# Unified Godot cockpit and graphical redesign — implementation plan

Role: spec
Status: active
Source of truth: this file for redesign planning and acceptance; `docs/plans/professional_godot_game_programme.md` for priority/stage order; `docs/design/godot_visual_system.md` for shell style; `docs/plans/gameboard_visual_language_design.md` for 3D/4D visual grammar; `docs/plans/explorer_cockpit_unification.md` for existing Explorer behavior and its staged extraction
Supersedes: previous design-only formulation of this plan, not semantic or rendering authority
Prepared: 2026-11-23
Branch: `design/dual-mode-ui-redesign-2026-11-22`
Decision: owner has **reopened the 2026-10-25 menu/cockpit layout lock for redesign** and required **one shared cockpit infrastructure across Play/Explorer and 2D/3D/4D**. No specific replacement layout or toolkit is approved. This PR is a planning proposal, not a shipped implementation.

Decision provenance: **Tet4D project conversation, 2026-11-23** — owner explicitly stated that the design lock is being reopened and subsequently required that cockpit functionality/behavior use one infrastructure, with 2D/3D/4D differences expressed by parameters rather than separate UI code. This is recorded as a dated addendum in `docs/design/ui_cockpit_result_lock_2026_10_27.md` and in [PR #199](https://github.com/mousomer/tet4d/pull/199). There is no external permalink to the original chat in this repository; the PR and addendum are the durable design-decision record.

## 1. Scope and non-negotiable boundaries

Goals: a board-first, legible, restrained visual language; professional app-like Instrument (`plain`) and geometric-game Vector Arcade (`tron`) appearances; and one shared, maintainable cockpit system. `diagnostic` and accessibility overrides remain supported. The three theme IDs, player presentation profiles and native gameplay contracts stay separate.

**The layout lock is deliberately reopened.** The owner decision dated 2026-11-23 authorizes *design exploration* of the Main Menu order/grouping, Live 2D/3D side rail, Live 4D split and smaller-window controls. It does **not** accept a new arrangement, release the old lock test automatically or authorize arbitrary modifications. Retain the 2026-10-25 layouts as the captured baseline until a replacement is separately reviewed. `godot/Tet4D.Godot/tests/test_locked_shell_layouts.gd` must be replaced or re-baselined **only in the same PR as an explicitly approved new layout**, with new behavioral assertions; never remove, skip or globally disable the regression.

**Style/layout is not gameboard semantics.** Board dimensions, cell coordinates, piece geometry, topology, collision, moves, scoring, 4D slice membership/order, basis, projection, per-slice transforms and adaptive matrix arrangement remain under their existing authorities. Changes to surrounding Control-panel allocation are now allowed, with Fit/camera responding through established contracts; new viewport rectangles may differ, but relative board mapping, state and renderer geometry cannot be silently rewritten.

**One cockpit infrastructure, not three code paths.** 2D, 3D and 4D use shared view/model, controls, input-to-command routing, responsive policy and layout composition, with mode/dimension-dependent **data** and capability declarations. This applies to both ordinary Play and Explorer. Native 2D/3D/4D gameplay implementations and authorized Explorer command handlers remain separate where their semantics differ; the unified requirement concerns the *presentation/interaction architecture*, not an artificial single native rules engine.

## 2. Existing code and ownership

- `godot/Tet4D.Godot/scripts/ui/live_cockpit.gd` already provides one `LiveCockpit` Control tree with Piece / View / Piece State slots and board stage. `cockpit_layout_policy.gd` (pure layout decisions), `cockpit_layout_coordinator.gd` (scheduling), `responsive_panel_policy.gd` (sizing), and `helper_fit_state.gd` (fitting) should be reused, not recreated per mode.
- `replay_hud.gd` owns shell composition, main menu and current presentation of the live cockpit. `live_piece_control_strip.gd` / `live_view_control_strip.gd` render commands. `scripts/input/live_input_contract.gd` already supplies `_live_2d_groups`, `_live_3d_groups`, `_live_4d_groups`, and `explorer_profile(dimension)` as data builders. **R0 must count actual duplication and branching before a refactor is specified**. Review evidence suggests only a small number of dimension branches in the UI tree: the most likely improvement is factoring identical Hold, Session, Navigation and Drop descriptors in the input contract, while leaving legitimately different movement/rotation inventories as parameters. No new adapter or hierarchy is justified without an observed limitation.
- `docs/plans/explorer_cockpit_unification.md` already specifies one Explorer descriptor, one input-dispatch path, and a pending Phase 3 `ExplorerCockpit` owner extraction. Do not implement a rival Explorer panel or undo independent Explorer action IDs/held-repeat contracts. After Phase 3, an ExplorerCockpit may be a thin composition host **of the shared cockpit modules**, not a separate rendering, style, layout or key-hint infrastructure.
- `scripts/ui/style/shell_style_manager.gd`, `shell_control_style_applier.gd`, `shell_design_tokens.gd`, `config/shell_theme_palettes.json` own shell roles and styles.
- `scripts/ui/replay_visuals.gd` constructs 2D/3D live face, outline, board, ghost and lattice materials; `scripts/rendering/cell_renderer.gd` constructs cell geometry; `trace_scene_renderer.gd` applies the existing profile and invokes those materials. R2/R3 style changes go through these *existing material/color/outline consumers*, not a parallel board-theme registry.
- `config/shell_settings_registry.json` owns user-editable `display.board_detail`, active/locked/ghost opacity and grid/boundary presentation values; `PresentationProfile` composes validated values. Change a documented default only with profile compatibility, Designer, built-in style and regression review. Fixed per-face factors or material coefficients can remain renderer constants under `gameboard_visual_language_design.md`, rather than inventing user settings.
- `docs/plans/gameboard_visual_language_design.md` owns Live 3D and inherited Live 4D visual grammar; `docs/design/godot_visual_system.md` owns overall shell styling. Both are consulted/updated where their visual rules change; neither is displaced by this plan.
- `docs/architecture/configurable_plain_boards_and_4d_layout.md` and later accepted contracts own the adaptive slice matrix, not the concept SVGs.

## 3. Unified cockpit contract (required for implementation)

Use **one cockpit infrastructure** that consumes existing dimension/activity data. **Start with existing `LiveCockpit`, `LiveInputContract` and `CockpitLayoutPolicy`; do not introduce a framework until R0 demonstrates a specific deficiency.**

The following context fields describe the information the shared UI already needs; **this is a checklist, not a requirement to create a `CockpitContext` class, configuration schema or capability-adapter layer**:
- `dimension`: 2 / 3 / 4;
- `activity`: Play or Explorer, with active-mode lifecycle and session state;
- `capabilities`: available piece translations, rotation planes, camera/view turns, slice actions, Hold/NEXT/drop where supported, and optional topology/Explorer tools, **derived from existing input/product contracts**;
- `bindings`: current action IDs, translated via the shared binding-label formatter; never duplicate hard-coded key labels;
- `state`: existing score/progress, NEXT/HOLD, warnings, selected view/slice, action availability; no fabricated values;
- `display`: density, viewport/apparent size, UI scale, accessibility and shell theme.

**Shared data flow:** existing `LiveInputContract` group data and native/Explorer snapshots → existing Piece, View, State and optional Explorer modules → existing `CockpitLayoutPolicy` / `LiveCockpit` structure → authorized command handlers. Extract shared Hold/Session/Navigation/Drop data only where R0 demonstrates repetition. Preserve legitimate dimension-specific movement/rotation descriptors and activity-specific dispatch behavior.

Capability availability should come from existing command-group descriptors. Do not implement `build_2d_cockpit`, `build_3d_cockpit`, `build_4d_cockpit`, copies of `_input`/help rows, one layout algorithm per dimension, or a separate Explorer skin. Existing Play and Explorer dispatchers remain distinct because they have different semantics; only the *common UI presentation infrastructure* must be singular. Dimension-specific snapshot interpretation is legitimate. Shared focus, resize, modal handling, appearance and binding-label formatting should reuse existing owners.

Dimension-specific *parameters* can select available groups, axis/plane inventory, label content, allowed actions, density and desired layout weights. Layout should respond primarily to **available size and actual measured content**, not simply `if dimension == 4` then swap to a different cockpit implementation. A design can have distinct 2D/3D/4D compositions produced by the same layout engine.

Explorer: consume the existing `LiveInputContract.explorer_profile(dimension)` and approved Explorer controls; do not invent a second `ExplorerContract` module. Its commands, dispatch and held-key lifecycle remain separately governed. **Integrate Explorer Phase 3 first**, on its own reviewed/merged branch. Only afterward rebase the R4A implementation branch on the integrated Phase 3 result and factor common presentation/layout components. R0 and R2/R3 appearance work may proceed separately, without editing Phase 3's overlapping `live_cockpit.gd`, `replay_hud.gd` or `practice_explorer_panel.gd`. A renamed/composed Explorer host must not fork the rendering or responsive system.

### Architectural acceptance

1. Each shared cockpit function uses the same existing presenter/script and semantic role in 2D/3D/4D; the only differences in common action groups are descriptor contents, availability and binding values. No parallel implementation tree is added.
2. A dimension switch may **rebuild control nodes**, as Explorer's existing 2026-11-16 contract and tests do. Preserve external UI behavior, active context, appropriate user-visible state and correct event registration; **no stale bindings, handlers, or duplicate connections**. Do not mandate persistent node identity or change lifecycle behavior in R4A.
3. New applicable capabilities can be exposed by changing a descriptor and adding an underlying handler where necessary, without duplicating the HUD.
4. Play and Explorer use the same responsive/layout infrastructure, with Explorer-specific extensions and separately authorized command semantics.
5. Shared focus/resize/menu presentation policies are reused; Play and Explorer retain their authorized separate input and held-repeat owners. Check event ownership, pause, modal priority and resize transitions in every dimension/activity.
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

Decision evidence: owner instruction in the **2026-11-23 Tet4D project conversation**, followed by the single-cockpit requirement in that same conversation; recorded in the dated lock addendum and PR #199. The permission reopens design exploration, **not** the locked runtime baseline. Replacement layout acceptance, baseline migration and implementation PR approval are separate decisions. Preserve legacy evidence and compare old/new results.

Authority split: this plan = redesign programme/work packages and shared cockpit architecture target; `professional_godot_game_programme.md` = product stage order; `gameboard_visual_language_design.md` = 3D/4D visual grammar; `godot_visual_system.md` = overall shell; `explorer_cockpit_unification.md` = Explorer capabilities/dispatch/Phase 3 lifecycle; existing RDS, renderer and geometry owners = gameboard and command semantics. No new competing authority.

## 7. Toolkit decision

**Default: current native Godot Control/Theme and existing Tet4D tokens.** Toolkit comparisons are **optional**, not the next mandatory work package. WoldUI/gohud could be isolated reference spikes **only if R4 finds a reproducible deficiency** in the native implementation, with license/version/CI and single-theme-owner assessment. Neither is approved to install; both may not independently control the live UI. Research inventory: `docs/design/game_ui_best_practices_2026_11_22.md`.

## 8. Execution packages and gates

- **R0 — baseline and duplication audit:** capture 2D/3D/4D Play and Explorer, Main Menu, Designer, Replay at supported sizes; record shell/Explorer/typography locks, Control owners and input→command matrix. **Count dimension-conditional branches and truly duplicated group definitions**, starting at the three `LiveInputContract` builders. Mark each item `shared identical`, `shared with parameter`, or `semantically distinct` and measure the minimum necessary source change. Record native/replay hashes and Designer/profile fingerprints where available. No speculative `CockpitContext`/adapter new classes.
- **R2 — 2D/3D appearance:** refine existing `ReplayVisuals` materials, palette roles, outline/face parameters under the gameboard visual owner. Maintain the current layout lock and exact gameplay/renderer geometry.
- **R3 — 4D appearance:** apply those same material/outline conventions to existing 3D slices via current consumers, without touching slice placement, coordinate mapping or basis. Maintain layout lock.
- **Dependency — Explorer Phase 3 first:** deliver/merge the existing ExplorerCockpit structure-owner extraction on its owning branch with unchanged current rectangles, observable controls and input behavior. Do not run a competing R4A edit of the same files in parallel.
- **R4A — minimum shared-cockpit refactor after Phase 3:** start from R0's duplication table. Factor common input-contract group data (e.g. Hold, Session, Navigation and Drop) only where repeated, retain dimension-specific movement/rotation commands where meaningful, and reuse the already-shared `LiveCockpit` tree and policies. Add no new context class or adapter unless the audit proves it necessary. **Behavior-preserving:** preserve Explorer's helper-deck rebuild and node lifecycle, current shell lock and tests; check no stale handlers after changes.
- **R4B — approved responsive layout redesign:** evaluate real screenshots and usability measures, obtain owner acceptance for specific new Main Menu/2D/3D/4D compositions, then apply them via **one shared responsive policy**. In the same PR, update `test_locked_shell_layouts.gd` and dependent typography/Explorer checks with explicit old→new expected rectangles, focus, menu order and accessibility evidence; do not weaken coverage or rewrite unrelated fixtures. Until this PR lands, old layout lock stays enforced.
- **R5 — surface/accessibility polish:** restrained motion, focus/selection/error feedback, contrast/scale, theme and presentation coherence; no new gameplay actions.
- **R6 — full acceptance:** focused tests and unchanged full verifier, platform screenshots, human novice/expert review, distinct Instrument/Vector Arcade themes over the **same** common cockpit and geometry.

**Optional R1** toolkit spike only after a documented native-control limitation at R4. No blanket library migration.

## 9. Verification and invariants

1. **Semantics remain identical.** For identical initial state, seed and command sequence, assert the same native snapshot, state/replay hashes and 2D/3D/4D positions before/after appearance, layout and activity changes; use existing accepted native/parity fixtures. Presentation-only state must not enter deterministic session identity.
2. **Projection/4D geometry remain identical.** Pin basis-derived slice membership, ordered layer identities, cell-local positions and adaptive layout outputs for the same allocated board viewport. A revised shell may change *outer* viewport rectangles, so do not confuse responsive Fit changes with a semantic geometry regression.
3. **Profile/Designer identity:** compare presentation snapshot and Designer fingerprints, detached profile resolution and A/B state under pure cockpit restyling. Intentionally changed visual constants require visual baseline review, not silent fixture regeneration.
4. **Unified cockpit (testable):** in each 2D/3D/4D Live and Explorer state, inspect the active common module's `get_script().resource_path` and semantic role/relative control path; assert that the same shared scripts implement corresponding modules. Ensure **exactly one visible presenter per common role at a time**, and after dimension/activity transitions check current command IDs, binding labels, handler connection count/one-dispatch behavior, press/release/held repeat, focus/modal capture and pause. Node instances **may be reconstructed**; no test may require identity persistence where the existing Explorer implementation rebuilds them.
5. **Layout acceptance:** run existing `godot/Tet4D.Godot/tests/test_locked_shell_layouts.gd` unchanged through R4A; R4B replaces exact old-layout expectations only with owner-approved alternatives, then keeps all control-reachability, no-clipping, focus, window, menu-route and board-preservation checks. Include 700×480, 680×520, 960×640, 1280×720, 1440×900, 1600×960 and 1920×1080 where supported.
6. **Accessibility:** target 4.5:1 normal text, 3:1 large text and non-text functional controls (WCAG-like pragmatic goals), High Contrast, Reduced Motion and coherent scaling; capture actual contrast, do not claim full WCAG certification.
7. **Usability:** compare novice comprehension of movement vs view, 3D depth, 4D signed slices, NEXT/HOLD, Play/Explorer entry and escape/return; measure misclicks, task completion, clipped controls and time-to-first-success against R0.
8. **Performance:** measure frame time, memory, imported assets and package footprint; preserve known platform-support matrix. Human GUI/target-platform review and CI remain merge gates. Docs/SVGs are not runtime evidence.

## 10. Explicit non-goals and handoff

No new piece/gameplay logic, topology changes, board semantic rules, 4D coordinate mapping, renderer replacement, camera math, persistence schema, telemetry, participant data or study protocol. No third-party dependency installation by this planning PR. No duplicated 2D/3D/4D cockpit controllers disguised as theming. Existing Play/Explorer command semantics are unchanged unless separately authorized.

This PR records approved **design goals and the intentional reopening of the layout lock**, not acceptance of a new layout or of implemented code. The next bounded action is R0, then R2/R3 styling and **Explorer Phase 3 integration before R4A**. Design alternatives and implementation follow separately.
