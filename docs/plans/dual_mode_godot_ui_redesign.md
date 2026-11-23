# Unified Godot cockpit and graphical redesign — implementation plan

Role: spec
Status: active
Source of truth: this file for redesign planning and acceptance; `docs/plans/professional_godot_game_programme.md` for priority/stage order; `docs/design/godot_visual_system.md` for shell style; `docs/plans/gameboard_visual_language_design.md` for 3D/4D visual grammar; `docs/plans/explorer_cockpit_unification.md` for existing Explorer behavior and its staged extraction
Supersedes: previous design-only formulation of this plan, not semantic or rendering authority
Prepared: 2026-11-23
Branch: `design/dual-mode-ui-redesign-2026-11-22`
Decision: owner has **reopened the 2026-10-25 menu/cockpit layout lock for redesign** and required **one data-driven cockpit infrastructure across Play/Explorer and 2D/3D/4D**. No specific replacement layout or toolkit is approved. This PR is a planning proposal, not a shipped implementation.

## 1. Scope and non-negotiable boundaries

Goals: a board-first, legible, restrained visual language; professional app-like Instrument (`plain`) and geometric-game Vector Arcade (`tron`) appearances; and one shared, maintainable cockpit system. `diagnostic` and accessibility overrides remain supported. The three theme IDs, player presentation profiles and native gameplay contracts stay separate.

**The layout lock is deliberately reopened.** The owner decision dated 2026-11-23 authorizes *design exploration* of the Main Menu order/grouping, Live 2D/3D side rail, Live 4D split and smaller-window controls. It does **not** accept a new arrangement, release the old lock test automatically or authorize arbitrary modifications. Retain the 2026-10-25 layouts as the captured baseline until a replacement is separately reviewed. `godot/Tet4D.Godot/tests/test_locked_shell_layouts.gd` must be replaced or re-baselined **only in the same PR as an explicitly approved new layout**, with new behavioral assertions; never remove, skip or globally disable the regression.

**Style/layout is not gameboard semantics.** Board dimensions, cell coordinates, piece geometry, topology, collision, moves, scoring, 4D slice membership/order, basis, projection, per-slice transforms and adaptive matrix arrangement remain under their existing authorities. Changes to surrounding Control-panel allocation are now allowed, with Fit/camera responding through established contracts; new viewport rectangles may differ, but relative board mapping, state and renderer geometry cannot be silently rewritten.

**One cockpit infrastructure, not three code paths.** 2D, 3D and 4D use shared view/model, controls, input-to-command routing, responsive policy and layout composition, with mode/dimension-dependent **data** and capability declarations. This applies to both ordinary Play and Explorer. Native 2D/3D/4D gameplay implementations and authorized Explorer command handlers remain separate where their semantics differ; the unified requirement concerns the *presentation/interaction architecture*, not an artificial single native rules engine.

## 2. Existing code and ownership

- `godot/Tet4D.Godot/scripts/ui/live_cockpit.gd` already provides one `LiveCockpit` Control tree with Piece / View / Piece State slots and board stage. `cockpit_layout_policy.gd` (pure layout decisions), `cockpit_layout_coordinator.gd` (scheduling), `responsive_panel_policy.gd` (sizing), and `helper_fit_state.gd` (fitting) should be reused, not recreated per mode.
- `replay_hud.gd` owns shell composition, main menu and current presentation of the live cockpit. `live_piece_control_strip.gd` / `live_view_control_strip.gd` render mode-specific commands. `scripts/input/live_input_contract.gd` currently has `_live_2d_groups`, `_live_3d_groups`, `_live_4d_groups`, and `explorer_profile(dimension)`. These are the concrete existing per-dimension group builders to refactor toward **one declarative capability/command inventory** without changing the established bindings or command semantics. No duplicated lists or UI construction should remain in the consuming Control code.
- `docs/plans/explorer_cockpit_unification.md` already specifies one Explorer descriptor, one input-dispatch path, and a pending Phase 3 `ExplorerCockpit` owner extraction. Do not implement a rival Explorer panel or undo independent Explorer action IDs/held-repeat contracts. After Phase 3, an ExplorerCockpit may be a thin composition host **of the shared cockpit modules**, not a separate rendering, style, layout or key-hint infrastructure.
- `scripts/ui/style/shell_style_manager.gd`, `shell_control_style_applier.gd`, `shell_design_tokens.gd`, `config/shell_theme_palettes.json` own shell roles and styles.
- `scripts/ui/replay_visuals.gd` constructs 2D/3D live face, outline, board, ghost and lattice materials; `scripts/rendering/cell_renderer.gd` constructs cell geometry; `trace_scene_renderer.gd` applies the existing profile and invokes those materials. R2/R3 style changes go through these *existing material/color/outline consumers*, not a parallel board-theme registry.
- `config/shell_settings_registry.json` owns user-editable `display.board_detail`, active/locked/ghost opacity and grid/boundary presentation values; `PresentationProfile` composes validated values. Change a documented default only with profile compatibility, Designer, built-in style and regression review. Fixed per-face factors or material coefficients can remain renderer constants under `gameboard_visual_language_design.md`, rather than inventing user settings.
- `docs/plans/gameboard_visual_language_design.md` owns Live 3D and inherited Live 4D visual grammar; `docs/design/godot_visual_system.md` owns overall shell styling. Both are consulted/updated where their visual rules change; neither is displaced by this plan.
- `docs/architecture/configurable_plain_boards_and_4d_layout.md` and later accepted contracts own the adaptive slice matrix, not the concept SVGs.

## 3. Unified cockpit contract (required for implementation)

Use **one dimension-parameterized cockpit specification**, consumed by all visible controls and layout decisions.

`CockpitContext` (conceptual contract, not a new authoritative settings schema) contains:
- `dimension`: 2 / 3 / 4;
- `activity`: Play or Explorer, with active-mode lifecycle and session state;
- `capabilities`: available piece translations, rotation planes, camera/view turns, slice actions, Hold/NEXT/drop where supported, and optional topology/Explorer tools, **derived from existing input/product contracts**;
- `bindings`: current action IDs, translated via the shared binding-label formatter; never duplicate hard-coded key labels;
- `state`: existing score/progress, NEXT/HOLD, warnings, selected view/slice, action availability; no fabricated values;
- `display`: density, viewport/apparent size, UI scale, accessibility and shell theme.

**Single shared pipeline:** product/input contracts and snapshots → context/capability adapter → stable command descriptors + modules (Piece, View, State, optional Explorer controls) → one responsive layout policy → one styled Godot Control tree → existing command dispatch owners.

A capability is present or absent in a descriptor. Do not implement `build_2d_cockpit`, `build_3d_cockpit`, `build_4d_cockpit`, copies of `_input`/help rows, one layout algorithm per dimension, or a separate Explorer skin. Do not hide a second dispatch table in a renderer. Local branching inside the semantic adapter may interpret dimension-specific native snapshots but must not fork UI orchestration. Shared behavior such as focus ownership, pause, resize, modal isolation, selected tabs, tooltips, theme switching and control rebind display exists once.

Dimension-specific *parameters* can select available groups, axis/plane inventory, label content, allowed actions, density and desired layout weights. Layout should respond primarily to **available size and actual measured content**, not simply `if dimension == 4` then swap to a different cockpit implementation. A design can have distinct 2D/3D/4D compositions produced by the same layout engine.

Explorer: extend context through the **existing `LiveInputContract.explorer_profile(dimension)`** and approved Explorer controls; do not invent a second `ExplorerContract` module just for this redesign. Its native state/commands remain separate from Play. Reuse the same modules, sizing/fit engine, semantic roles, status and key-hint generation; Phase 3 host extraction is a dependency for final integration. Coordinate owner boundaries rather than duplicating its plan.

### Architectural acceptance

1. Exactly one shared UI component/semantic-control implementation per common cockpit function; every common module uses the same code in 2D/3D/4D.
2. A dimension switch changes context and capabilities, **not implementation class or a collection of competing UIs**. Common module node identity and current UI state persist where appropriate; no stale bindings/handlers from the previous dimension.
3. New applicable capabilities can be exposed by changing a descriptor and adding an underlying handler where necessary, without duplicating the HUD.
4. Play and Explorer use the same responsive/layout infrastructure, with Explorer-specific extensions and separately authorized command semantics.
5. Input focus, held/repeat state, keyboard/menu precedence, pause and resize are governed once and checked across dimension/activity transitions.
6. Visual styles and High Contrast/Reduced Motion are orthogonal to both dimension and activity.

## 4. Board-first visual language

The owner-accepted aesthetic moodboards are in `docs/design/accepted_gameplay_ui_direction.md`. They show **prominent individual cells**, crisp outlines, restrained blue/charcoal shell, quiet grid, muted locked fills and distinct active/ghost states. They do **not** specify cell coordinates, a 4D projection, a slice count or a prescribed panel layout.

- **2D:** style the existing flat board's cell contours and visual density; no dimensional geometry changes.
- **3D:** style exterior voxel faces, depth-readable locked cells and active outlines; preserve canonical projection and the existing renderer.
- **4D:** style the existing **set of 3D slices** with the same 3D voxel grammar. No replacement slice mapping, nested cube or independent panel-per-slice dashboard. W counts/layout remain computed by the existing presentation authority.

The 2D and 3D visual moodboards were accepted for appearance; 4D is an illustration of shared volume styling only. Real engine screenshots and state-correctness checks decide implementation acceptance.

Shell theme: Instrument `plain` = calm surface with disciplined hierarchy; Vector Arcade `tron` = restrained game character. Both use **the same Control tree and component behavior**. The board's presentation is controlled by its established palette/profile/renderer roles; avoid an extra theme-to-gameboard appearance authority. Status must not rely on color alone.

## 5. Screen and layout redesign decision space

**The old lock is open for redesign, but no replacement layout is selected.** Baseline: Main Menu single list and original ordering, Live 2D/3D board+side rail, Live 4D split with bottom legend, and small-window NEXT/HOLD-first behavior. Those are test-protected historical results until replacement acceptance.

Candidates include a simpler Main Menu hierarchy with direct Play/Explorer prominence, relocated controls, compact side/bottom regions, and adaptive grouping. These are **design alternatives**, not approved interaction or menu routing changes. The accepted replacement may change placement and menu ordering without changing command semantics.

When evaluated, the new layout must:
- maximize *actual, legible* board area rather than unused background; never crop the underlying game geometry;
- keep NEXT/HOLD, pause, critical state and applicable move/view controls accessible;
- preserve an identical capability-to-control mapping across dimensions, with missing capabilities omitted/disabled based on descriptors;
- retain keyboard, mouse and approved touch access, visible focus, readable keycaps, logical reading order, scroll/fit recovery and window-minimum behavior;
- never change the existing adaptive 4D *internal slice layout* merely because outer panel positions change;
- retain the existing Main Menu routes and dispatch targets even if order/grouping is intentionally redesigned.

The schematic SVGs are **aesthetic references only**, not accepted screen layouts, UI measurements or semantic fixtures. No layout may be implemented solely because it appears in an SVG.

## 6. Programme placement and design ownership

Placed in **Phase III `9.1 Professional UI review and correction**, **P2** of `docs/plans/professional_godot_game_programme.md`; after the established Stage 57 control legibility/restart work and alongside relevant Stage 58C/59 readability acceptance. This is **not a new numbered Stage** and does not reopen `PROFESSIONAL_CORE_GAME_READY`. Priority against active P0/P1 work remains programme-owned.

This user instruction is the required **product decision to reopen** the 2026-10-25 layout lock for design. Replacement layout acceptance, baseline migration and implementation PR approval are separate decisions. Preserve legacy evidence and compare old/new results.

Authority split: this plan = redesign programme/work packages and shared cockpit architecture target; `professional_godot_game_programme.md` = product stage order; `gameboard_visual_language_design.md` = 3D/4D visual grammar; `godot_visual_system.md` = overall shell; `explorer_cockpit_unification.md` = Explorer capabilities/dispatch/Phase 3 lifecycle; existing RDS, renderer and geometry owners = gameboard and command semantics. No new competing authority.

## 7. Toolkit decision

**Default: current native Godot Control/Theme and existing Tet4D tokens.** Toolkit comparisons are **optional**, not the next mandatory work package. WoldUI/gohud could be isolated reference spikes **only if R4 finds a reproducible deficiency** in the native implementation, with license/version/CI and single-theme-owner assessment. Neither is approved to install; both may not independently control the live UI. Research inventory: `docs/design/game_ui_best_practices_2026_11_22.md`.

## 8. Execution packages and gates

- **R0 — baseline and capability inventory:** baseline captures for 2D/3D/4D Play and Explorer, Main Menu, Designer, Replay at supported sizes; record `test_locked_shell_layouts.gd` and Explorer/typography locks, actual Control owners and input→command matrix. Record native snapshot/replay hashes and Designer/presentation fingerprints/fixtures where available.
- **R2 — 2D/3D appearance:** refine existing `ReplayVisuals` materials, palette roles, outline/face parameters under the gameboard visual owner. Maintain the current layout lock and exact gameplay/renderer geometry.
- **R3 — 4D appearance:** apply those same material/outline conventions to existing 3D slices via current consumers, without touching slice placement, coordinate mapping or basis. Maintain layout lock.
- **R4A — unified cockpit infrastructure:** consolidate modules, dimension/activity capability descriptors, lifecycle, key-hint generation, layout-policy ownership and state adapters. Respect and integrate the existing Explorer Phase 3 extraction. This is a **behavior-preserving refactor**; keep baseline shell/Explorer/input tests and node-state continuity checks.
- **R4B — approved responsive layout redesign:** evaluate real screenshots and usability measures, obtain owner acceptance for specific new Main Menu/2D/3D/4D compositions, then apply them via **one shared responsive policy**. In the same PR, update `test_locked_shell_layouts.gd` and dependent typography/Explorer checks with explicit old→new expected rectangles, focus, menu order and accessibility evidence; do not weaken coverage or rewrite unrelated fixtures. Until this PR lands, old layout lock stays enforced.
- **R5 — surface/accessibility polish:** restrained motion, focus/selection/error feedback, contrast/scale, theme and presentation coherence; no new gameplay actions.
- **R6 — full acceptance:** focused tests and unchanged full verifier, platform screenshots, human novice/expert review, distinct Instrument/Vector Arcade themes over the **same** common cockpit and geometry.

**Optional R1** toolkit spike only after a documented native-control limitation at R4. No blanket library migration.

## 9. Verification and invariants

1. **Semantics remain identical.** For identical initial state, seed and command sequence, assert the same native snapshot, state/replay hashes and 2D/3D/4D positions before/after appearance, layout and activity changes; use existing accepted native/parity fixtures. Presentation-only state must not enter deterministic session identity.
2. **Projection/4D geometry remain identical.** Pin basis-derived slice membership, ordered layer identities, cell-local positions and adaptive layout outputs for the same allocated board viewport. A revised shell may change *outer* viewport rectangles, so do not confuse responsive Fit changes with a semantic geometry regression.
3. **Profile/Designer identity:** compare presentation snapshot and Designer fingerprints, detached profile resolution and A/B state under pure cockpit restyling. Intentionally changed visual constants require visual baseline review, not silent fixture regeneration.
4. **Unified cockpit:** test dimension and Play↔Explorer switching across every shared module, active controls/disabled state, binding labels, press/release/repeat, focus/modal capture, onboarding, pause, lifecycle and state preservation. Assert no duplicated presenters or mode-specific copies for common actions.
5. **Layout acceptance:** run existing `godot/Tet4D.Godot/tests/test_locked_shell_layouts.gd` unchanged through R4A; R4B replaces exact old-layout expectations only with owner-approved alternatives, then keeps all control-reachability, no-clipping, focus, window, menu-route and board-preservation checks. Include 700×480, 680×520, 960×640, 1280×720, 1440×900, 1600×960 and 1920×1080 where supported.
6. **Accessibility:** target 4.5:1 normal text, 3:1 large text and non-text functional controls (WCAG-like pragmatic goals), High Contrast, Reduced Motion and coherent scaling; capture actual contrast, do not claim full WCAG certification.
7. **Usability:** compare novice comprehension of movement vs view, 3D depth, 4D signed slices, NEXT/HOLD, Play/Explorer entry and escape/return; measure misclicks, task completion, clipped controls and time-to-first-success against R0.
8. **Performance:** measure frame time, memory, imported assets and package footprint; preserve known platform-support matrix. Human GUI/target-platform review and CI remain merge gates. Docs/SVGs are not runtime evidence.

## 10. Explicit non-goals and handoff

No new piece/gameplay logic, topology changes, board semantic rules, 4D coordinate mapping, renderer replacement, camera math, persistence schema, telemetry, participant data or study protocol. No third-party dependency installation by this planning PR. No duplicated 2D/3D/4D cockpit controllers disguised as theming. Existing Play/Explorer command semantics are unchanged unless separately authorized.

This PR records approved **design goals and the intentional reopening of the layout lock**, not acceptance of a new layout or of implemented code. The next bounded action is R0, followed by R2/R3 and R4A. Design alternatives and implementation follow separately.
