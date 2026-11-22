# Dual-mode Godot UI redesign — implementation plan

Role: spec
Status: active
Source of truth: `docs/design/godot_visual_system.md` for current visual authority; `docs/plans/professional_godot_game_programme.md` for stage ordering
Supersedes: none
Prepared: 2026-11-22
Branch: `design/dual-mode-ui-redesign-2026-11-22`
Decision state: **candidate design / not approved product implementation**

## 1. Intent

Create a professionally designed Tet4D UI that can read as either a clean application or a distinctive puzzle game **without forking screens, controls, input contracts, gameplay or accessibility**.

- **Instrument / app-like:** calm, high-legibility, precise, flat-to-subtle surfaces, restrained accent, low chrome.
- **Vector Arcade / game-like:** recognisably geometric, more energetic framing and microfeedback, but no distracting bloom or proliferating cards.
- **Diagnostic:** existing examination-oriented theme retained unchanged for the redesign's initial implementation.

The existing persisted shell IDs remain `plain`, `tron` and `diagnostic`. The default remains `plain`. High Contrast and Reduced Motion remain independent preferences. No new setting or theme identity is authorized by this plan.

## 2. Existing architecture, not a greenfield UI

Repository inspection on 2026-11-22:

- `godot/Tet4D.Godot/config/shell_theme_palettes.json`: three shell palettes and semantic colour roles.
- `scripts/ui/style/shell_style_manager.gd`, `shell_style_roles.gd`, `shell_control_style_applier.gd`, `shell_design_tokens.gd`: existing style ownership and primitive tokens.
- `scripts/ui/live_cockpit.gd`, `replay_hud.gd`, `practice_explorer_panel.gd`, `presentation_designer.gd`, `responsive_panel_policy.gd`: real consumers; their local overrides must be inventoried, not blindly replaced.
- `config/shell_settings_registry.json` and `docs/architecture/built_in_style_catalog.md`: authoritative presentation parameters and saved/built-in presentation styles; not the same as the shell theme.
- `docs/plans/explorer_cockpit_unification.md`: Explorer control ownership and key mappings; keep its pending Phase 3 owner extraction independent.
- `docs/plans/typography_cleanup.md` and `docs/design/godot_visual_system.md`: existing typography and visual acceptance constraints.

**No parallel token registry, universal component rewrite, detached CSS-like shell, replacement designer, or new UI runtime.** Prefer ordinary Godot `Control` nodes, `Container`-based responsive layout, Theme type variations and thin reusable scenes. Use existing semantic labels instead of node-name styling heuristics where feasible.

## 3. Single rendering architecture

`InputMap / gameplay contract → semantic screen model → shared component structure → ShellStyleManager + role/token adapter → Instrument or Vector Arcade`.

The look can change while a session is running. Theme selection must never mutate game state, native state, replay hashes, input mapping, simulation timings, board geometry, viewport transforms or saved research measurements.

Keep separate concepts explicit:

1. **Shell theme**: menus, controls, typography, panels, focus, surface hierarchy; `plain` / `tron` / `diagnostic`.
2. **Board presentation profile / built-in style**: cells, lattice, cameras, opacity, background, animation parameters under their existing registries.
3. **Accessibility overrides**: High Contrast, UI scale, Reduced Motion, independent of theme and presentation profile.
4. **Game state**: untouched by any of the above.

The restyling adaptor maps one set of semantic component purposes to the existing role palette. Both looks use the same DOM-equivalent Godot scene/control tree. Avoid duplicated layout and input handlers.

## 4. Experience principles

1. **Board first**: largest unbroken visual region; shell cards and animations must never overpower the board, cut slices, occlude active cells or hide orientation.
2. **One primary action** per screen; clear direct entry into Play and Explorer; advanced settings are visible on demand, not surfaced by default.
3. **Recognition over recall**: label actions in ordinary language; show context-sensitive keycaps and modifiers from the real input contract, never hard-coded copies.
4. **Control categories stay distinct**: piece translation, piece rotation, view/camera transformation, slice changes, and session actions have separate labels/regions.
5. **Immediate truthful feedback**: pause, game over, invalid movement, topology seam result, changed settings, recording/assessment status; no colour-only states.
6. **Progressive disclosure**: standard cockpit displays next/hold/state/essential moves; Expanded shows additional controls; Diagnostic exposes advanced details.
7. **Responsive with no loss of reachability**: use owned layout policy, meaningful reflow, scroll as last resort; maintain existing minimum viewport contract.
8. **Accessibility is composed, not a fourth skin**: keyboard focus visible, logical Tab order, pointer equivalents, reduced movement, persistent text scale, contrast at all states.
9. **State stability**: styling may not recreate panels or reset selected tabs, focus, view state, in-progress Explorer targets, user profiles or paused state.
10. **Dimension parity**: a control has the same label, visual role and position policy in Live 2D, 3D and 4D; Explorer reuses the same vocabulary.

## 5. Visual direction

| Concern | Instrument (`plain`) | Vector Arcade (`tron`) | Shared invariant |
| --- | --- | --- | --- |
| Surface | quiet deep-blue/black, modest elevation | geometric framing, selective bright accents | one semantic panel scale |
| Accent | muted warm gold from existing palette | cyan from existing palette | emphasis communicates priority, not decoration |
| Typography | spacious, neutral and readable | same type family and hierarchy; perhaps stronger display weight | existing typography and UI-scale authority |
| Buttons | legible, minimal, distinct primary | restrained active/press treatment | same hit boxes, labels and focus |
| Board | diagrammatic, uncluttered | selective board-edge energy | active/locked/ghost/lattice hierarchy fixed |
| Motion | quick, discreet state transitions | selective, short feedback | Reduced Motion disables nonessential transitions |
| Error and pause | quiet but unmistakable status | visually stronger but still controlled | label plus shape + hue, same semantics |

Avoid new fonts and third-party icon packs until license, inclusion footprint and readability are reviewed. Preserve existing axis colour semantics and structural depth cues.

## 6. Screen information architecture

**Main menu.** One strong Play action; Explorer as the second first-class activity; dimension entry and setup close by. Settings, Designer, Replay, Help and Diagnostics form secondary grouped routes. Clear current/default mode. Do not create more top-level entry routes.

**Setup/settings.** Use one compact, predictable form grammar: left-aligned section labels, explanatory text adjacent to controls, stable footer actions, no nested cards per field. Validation sits next to its field. Theme preview changes only presentation and remains reversible.

**Live 2D/3D/4D.** Central board and orientation cues dominate. NEXT/HOLD and session state are peripheral but legible; current Piece and View controls share the same component grammar. Controls supporting Play remain available without launching settings. Use the existing width-driven responsive policy.

**Explorer.** Same shell and controls, but view manipulation and topology/space selection need discoverable labeling. Preserve `docs/plans/explorer_cockpit_unification.md` owner, existing View / Piece / Space grouping, and normal vs Explorer input separation.

**Designer, Replay, Help.** Shared app-like frame and tabs; technical detail is allowed in Designer and Replay, not duplicated in ordinary play. Advanced panes scroll within their content areas without hiding primary navigation.

Illustrative widescreen composition, **not** an instruction to create a new cockpit hierarchy:

`[Tet4D / Play / Explorer / Settings]                [Mode] [Pause]`
`[ Board and orientation: primary visual region     ][NEXT / HOLD]`
`[ Board and orientation continue                  ][State      ]`
`[ contextual Piece actions ] [ View actions ] [ Help/More  ]`

At narrow widths, the existing responsive policy reflows NEXT/HOLD and Piece/View below the board in a stable sequence. The board must not shrink to make decorative chrome fit.

## 7. Library evaluation, without premature adoption

Candidate findings and sources are captured in `docs/design/game_ui_best_practices_2026_11_22.md`.

**Shipping baseline: native Godot Theme + current Tet4D role/token owners.** The project already owns gameplay-specific roles that generic UI kits do not understand.

**Spike A, WoldUI v1.2.0:** isolated Godot 4.7.2 sample; inspect tokens → existing roles adapter, focus/navigation, state transitions, CanvasLayer restyling, footprint, editor reliability, licensing. Store metadata still marks an older listing unstable. Do not set its generated project Theme in the game or let it replace `ShellStyleManager` in the spike.

**Spike B, gohud v1.3.0:** isolated sample of at most one menu/form screen and one compact HUD region using Material/app and sci-fi/arcade looks. Test resizing, touch targets, gamepad/keyboard focus, contrast and component extensibility. Keep app-framework state and a second theme/preset owner out of the production architecture.

**Optional reference only:** Theme Assist's visual workflow and ThemeGen's generation approach. Neither is an approved runtime dependency.

Comparison rubric: 30% ownership/fit, 20% usability/accessibility, 20% Godot/platform/CI compatibility, 15% binary/package and runtime cost, 15% maintenance/licensing. Require documented evidence for every category, not marketing counts. **Never install WoldUI and gohud simultaneously into product UI.** A third-party component may be adopted only when it solves a measured problem better than existing native Controls and does not create competing theme authority.

## 8. Work packages (separate, reviewable PRs)

**R0 — visual and interaction baseline.**
Capture current main menu, settings, setup, Live 2D/3D/4D, Explorer 2D/3D/4D, Replay and Designer. Annotate board occupancy, clutter, reading order, focus path, contrast failures, label duplication, truncation and help discoverability. Preserve current screenshots/acceptance evidence; do not rewrite older evidence.

**R1 — library spikes and design tokens.**
Isolated prototypes of native-only, WoldUI and gohud. Resolve package license/version and Godot compatibility. Inventory duplicate token constants and style overrides before any refactor. Present two representative screen designs built over the same component tree. Choose native-only or one narrow adapter through a recorded decision.

**R2 — application shell.**
Reskin menu, setup, settings, status dialogs, tabs and help using shared semantic controls. Main menu and onboarding novice clarity first. No change to entry routing.

**R3 — game cockpit.**
Apply the two skins to shared Live and Explorer HUD components after respecting Explorer Phase 3 ownership. Repair visual hierarchy, NEXT/HOLD grouping, board fit, visible controls, and focus only. Reuse (do not fork) responsive and keybinding contracts.

**R4 — detail polish.**
Add selectively: active-selection cues, legible focus, reversible transitions, reduced-motion handling, pressed/hover/status feedback. No global animation that consumes gameplay input or obscures geometry.

**R5 — acceptance and integration.**
Run focused Godot UI/theme tests and unchanged complete verification gate, produce per-theme screenshot matrix, do human novice review and macOS/Windows desktop visual review as available. No automatic merge based on snapshot differences alone.

Every package lists its owning files, observed baseline, change-scope diff, executable tests, unexecuted checks and human acceptance status. Do not combine whole-app refactor, toolkit install, Explorer functional changes or native geometry fixes into one PR.

## 9. Acceptance criteria

- **No gameplay regressions:** input-to-command semantics, camera-relative motion, basis/view controls, topology rules, replay identity and deterministic native state unchanged; regression checks cover all dimensions.
- **Contrast:** target WCAG 2.2 AA-like 4.5:1 for normal UI text, 3:1 for large text and functional non-text indicators, including normal/hover/focus/disabled as applicable. Record exception rationale, not false certification.
- **Keyboard and controllers:** visible focus, predictable order, no keyboard/gameplay leakage from text fields or dialogs, labelled alternatives for every essential visible control.
- **Readable at scale:** default and enlarged UI scale; no clipped control labels or hidden primary actions at existing 680x520 minimum and supported sizes (960x640, 1280x800, 1600x960, 1920x1080). Tablet portrait/landscape are additional evaluation targets, not an expansion of released-platform support.
- **Touch readiness:** interactive targets at least 44 logical px where tablet usage is supported by the local layout, with adequate separation; measure actual active bounds, not apparent icon size.
- **Session continuity:** switching `plain` ⇄ `tron` changes appearance only; no loss of tab, viewport, focus intent, Explorer object, pause state or Designer parameters.
- **Two distinct identities:** reviewers can identify which skin is active without reading a title, yet the interaction map is identical.
- **Player comprehension:** uncoached users can locate Play/Explorer, identify which actions move the piece versus the view, find NEXT/HOLD and pause, and explain the current 4D slice/axis cues. Record actual task completion and wrong-action counts; do not claim improvement without comparative sessions.
- **Performance and packaging:** measure frame time, memory, shader stutter, editor import and package size against baseline; reject unexplained regressions. Run actual target builds before claiming platform acceptance.
- **Design review:** humans approve both screenshots and direct keyboard/pointer interaction. The existing visual system remains authority until a separate explicit authority update is accepted.

## 10. Explicit exclusions

No third-party dependency is added by this planning branch. No change to releases, project settings, telemetry, research consent, cloud identity, data capture, geometry, piece simulation, topology transport, cameras, input defaults, built-in presentation style catalog, or existing theme IDs. These require their own owning contracts and review.

## 11. Design handoff boundary

This branch establishes scope, decision criteria and research, not an accepted UI implementation. The next bounded engineering action is R0 capture + R1 isolated comparative prototypes. Library adoption, default appearance changes, layout rewrite and merge remain separate owner/reviewer decisions.
