# Task Contract — Stage 54E-5 Gameplay Cockpit Consolidation

Status: COMPLETE / HUMAN PRODUCT REVIEW ACCEPTED (2026-08-21)

## Objective

Make ordinary Live 2D, Live 3D, and Live 4D present a coherent gameplay
cockpit in which the board is primary and the player can immediately identify
game state, NEXT, mode-appropriate gameplay guidance, view actions, and
session actions. This is information-architecture and player-affordance work,
not a gameplay, camera, movement, NEXT, Ghost, or broad visual redesign.

## Classification

- Primary task type: `godot_product_shell`.
- Workflow modifiers: none.
- Affected layers: Godot product shell and documentation.
- Required evidence: `documentation`, `godot`, `integration`, and
  `human_visual`.
- Full repository gate: required because the shared live/replay HUD and its
  product authorities change.

## Current Authority

- Godot owns live HUD layout, control presentation, input adaptation,
  guidance, accessibility, diagnostics, and camera/view presentation.
- `docs/architecture/camera_gui_preset_semantics.md` owns stateless named view
  actions, one composite Reset View, framing-only Fit View, mode canonical
  views, and view-preserving same-context Restart Game.
- `godot/Tet4D.Godot/scripts/input/live_input_contract.gd` owns public live
  action bindings and derives movement guidance from the app-supplied effective
  control-frame snapshot.
- `docs/architecture/next_piece_preview.md` owns the authoritative NEXT query,
  shared thumbnail, live-only placement, and replay exclusion.
- `docs/architecture/ghost_piece.md` owns authoritative Ghost presentation over
  the read-only landing query.
- `docs/architecture/godot_vector_arcade_cockpit_overhaul.md` owns the existing
  live/replay cockpit structure and is extended by the E5 decision record.

Authority effect: existing presentation owners are reused. No authority is
transferred or established.

## Cockpit Inventory Before Change

| Surface | Owner | Default live visibility | Interaction | Source / role | E5 finding |
| --- | --- | --- | --- | --- | --- |
| Replay/live/mode navigation buttons | `ReplayHud._build_layout()` | 2D/3D/4D | buttons | shell navigation | replay and alternate-mode chrome dominates ordinary play |
| `Show Quick Settings`, `Grid: On` | `ReplayHud._live_view_actions` | 2D/3D/4D | buttons | persisted HUD density and board-detail presentation | useful but visually promoted above gameplay/view recovery |
| `Bundle` / `TET4D` panel | `ReplayHud._top_status_panel` | 2D/3D/4D | passive | replay bundle status reused as product branding | redundant non-game information |
| `Live Session` summary | `ReplayHud.live_gameplay_summary_text()` | 2D/3D/4D | passive | native snapshot plus setup labels | truthful but overloaded with board, seed, piece set, score, queue, and feedback until it clips |
| running/paused/game-over badge | `ReplayHud._top_state_badge_label` | 2D/3D/4D | passive | live snapshot/state | essential and correctly prominent |
| `Restart Game` | `ReplayHud._restart_game_button` | game over only | button | existing reset signal / native session restart | semantic is correct but ordinary-play reachability is weak |
| `New Random Game` | `ReplayHud._new_random_game_button` | true-random setup only | button | session lifecycle | legitimate conditional session action |
| `Change Setup` | `ReplayHud._change_setup_button` | 2D/3D/4D | button | setup lifecycle | legitimate session action |
| `Authority` panel | `ReplayHud._authority_panel` | 2D/3D/4D | passive | implementation/ownership diagnostic | developer information promoted above gameplay |
| board and active/Ghost/locked cells | renderer plus `ReplayHud._game_area` | mode-owned | gameplay/camera pointer input | native snapshots and accepted Godot presentation owners | primary surface; unchanged |
| NEXT | `NextPiecePanel` in `_right_column` | 2D/3D/4D | passive | authoritative observational query | correct, readable, and retained before secondary guidance |
| `4D VIEW ROTATION` basis/axis panel | `ReplayHud._build_basis_panel()` | 4D only | exact view-action buttons | accepted signed-basis presentation and live input contract | legitimate 4D comprehension/action surface; action family wording needs clarification |
| grouped controls | `LiveInputContract.control_hint_groups()` rendered by `ReplayHud` | 2D/3D/4D | passive help | actual action contract plus effective control-frame snapshot | truthful; 2D is too dense and 4D repeats exact view actions already exposed as buttons |
| `INSPECTOR` session/status/view text | `ReplayHud._integrity_panel` | 2D/3D/4D | passive | native snapshot plus HUD formatting | duplicates top state and exposes engine/shell/topology/last-input diagnostics |
| bundle detail | `ReplayHud._bundle_detail_panel` | Detailed only | passive | replay bundle diagnostics | not ordinary live-game information |
| `VIEW` / `Camera` / `View Actions` | `ReplayHud._camera_panel` | 2D/3D/4D except Compact; menu hidden in 2D | stateless `MenuButton` plus passive status | camera preset action catalogue and numeric camera status | unreachable below long controls, empty/diagnostic in 2D, and menu needs explicit input ownership |
| diagnostics/events | `DiagnosticsPanel` / `EventListPanel` | replay only | passive | development diagnostics | already correctly hidden in live mode |
| Quick Settings panel | generated `SettingsPanel` | Detailed only | controls | persisted shell settings | valid progressive disclosure; remains secondary |
| hidden replay footer Reset/Fit/Reset Replay | `_bottom_panel` | replay only | buttons | replay/view/session signals | correct for replay, not a live affordance |
| onboarding | `LiveOnboardingPanel` | preference-controlled | dismiss button | accepted onboarding model | retained as optional guidance |

Ghost has no separate ordinary-play cockpit label. Its visibility preference is
already owned by Quick Settings/Settings and its rendered cells remain the
player-facing surface; E5 does not add a duplicate status.

## Allowed Systems and Paths

- shared Godot live/replay HUD composition and its layout snapshot;
- existing live control-contract presentation helpers, without changing
  bindings or command semantics;
- app-level input suppression while a cockpit popup owns interaction;
- focused Godot HUD/layout/input tests; and
- existing cockpit architecture, programme, backlog, and restart handoff.

## Required Changes

1. Replace live replay/developer chrome with clear `View` and `Session` action
   families while preserving replay layout when replay is active.
2. Keep Running/Paused/Game Over, score, clears, active piece, and speed in a
   concise live summary; leave NEXT to the authoritative thumbnail panel.
3. Hide live bundle/authority/session-diagnostic panels and preserve detailed
   observability through existing replay/Advanced Diagnostics surfaces.
4. Keep 2D minimal, show legitimate 3D camera guidance and stateless View
   Actions, and retain 4D movement/view distinction plus useful axis/slice cues.
5. Present Fit View, Reset View, and Restart Game as distinct reachable actions
   backed by their existing signals; do not invent universal key labels.
6. Remove conceptual duplicates from the ordinary cockpit by deriving a
   cockpit subset from the full shared input contract rather than creating a
   new binding table.
7. Make the View Actions popup explicitly own keyboard interaction while open
   so unhandled input cannot dispatch gameplay, then restore live capture when
   it closes.
8. Preserve the supported minimum, scrollable inspector, board dominance,
   NEXT placement, and replay behavior.

## Forbidden Changes

- deterministic gameplay, native sessions, queue/RNG, scoring, topology,
  movement/rotation/drop legality, replay/trace schemas, or persistence;
- control-frame resolution or any HUD-local yaw/quadrant resolver;
- camera/view/Reset/Fit/Restart semantics or persistent preset identity;
- NEXT geometry, queue data path, W grouping/placement, or normalization;
- Ghost landing/collision semantics or renderer authority;
- Hold, #69, #70, 4D volume redesign, board art, Settings-screen overflow,
  setup error colour, or other Stage 54F work; and
- push or pull-request creation.

## Acceptance Criteria

1. The board remains the dominant live surface and NEXT remains visible,
   readable, authoritative, and before secondary inspector content.
2. 2D exposes no named View Actions, camera diagnostics, 3D/4D orientation, or
   slice concepts.
3. 3D exposes truthful relative movement, piece rotation, camera gestures,
   stateless View Actions, and distinct recovery/session actions.
4. 4D exposes ordinary/W movement, piece rotation, exact re-slice actions,
   slice orientation/framing, and meaningful axis/slice cues without raw `B/L`
   or implementation terminology.
5. Reset View, Fit View, and Restart Game are distinct, visible, reachable, and
   retain their accepted semantics.
6. View Actions visibly read as actions and never expose selected/`Custom`
   identity after manual manipulation.
7. Cockpit movement labels continue to consume the effective translation
   snapshot and displayed bindings resolve through `LiveInputContract`.
8. Ordinary live mode hides bundle, authority, raw engine/shell/topology,
   numeric camera, and last-input diagnostics; existing diagnostic routes
   remain available.
9. Opening View Actions suppresses gameplay dispatch until the popup closes.
10. Compact/Standard/Detailed density retains critical state, gives Standard
    the intended ordinary cockpit, and keeps detailed settings secondary.
11. Supported default, smaller, and larger layouts keep essential actions and
    NEXT reachable without structural overlap; replay shared infrastructure is
    not regressed.
12. Focused Godot checks, pinned Godot verification, sanitation,
    documentation/governance checks, and the full gate pass.
13. Real-window 2D/3D/4D review accepts first-five-seconds hierarchy,
    dimensional progression, semantic distinctions, truthfulness, and
    supported-size composition.

## Automated Verification

- focused cockpit mode-visibility, grouping, action, responsive-layout, and
  popup-input-ownership tests;
- existing live input, control-frame, NEXT, Ghost, replay-layout, and menu
  routing tests affected by the shared HUD;
- `./scripts/check_keybinding_contract.sh`;
- `git diff --check`;
- `./scripts/check_git_sanitation_repo.sh`;
- routed governance/documentation checks;
- `GODOT_BIN=/Applications/Godot.app/Contents/MacOS/Godot
  ./scripts/verify_godot_4_7.sh`;
- `CODEX_MODE=1 ./scripts/verify.sh`.

## Manual Verification

- Capture before/after real-window evidence at the supported normal desktop
  size for Live 2D, Live 3D, and Live 4D.
- Exercise View Actions then manual view manipulation, Fit View, Reset View,
  Restart Game, pause, Change Setup, Main Menu, Quick Settings, and popup input
  ownership.
- Resize to the supported smaller window and a larger desktop window; sanity
  check replay when shared HUD structure changes.
- Do not infer human-visible acceptance from headless tests.

Acceptance record (2026-08-21): pinned Godot 4.7.1 real-window review accepted
Live 2D, Live 3D, and Live 4D at the normal desktop size, plus 960 x 640 and
1728 x 1000 window requests. The review exercised stateless named View Actions
followed by manual camera manipulation, Fit View, Reset View, Restart Game,
Change Setup, Main Menu, Quick Settings, and the View Actions popup. It
confirmed board-first hierarchy; prominent authoritative NEXT; intentionally
increasing 2D/3D/4D complexity; distinct View, Display, and Session families;
truthful relative guidance; and the absence of replay/developer diagnostics in
ordinary play. The popup was visibly inspected and executable dispatch tests
proved that gameplay input remains suppressed until it closes. Replay's
shared layout, diagnostics, NEXT/status, and view controls were regression-
checked by the focused executable suite. No E5 blocker remained.

## Documentation Updates

- extend the existing cockpit architecture with the E5 hierarchy and
  progressive-disclosure decisions;
- expand the E5 programme section and update `docs/BACKLOG.md`;
- update this task contract before implementation; and
- update `CURRENT_STATE.md` with final verified/reviewed status.

## Explicit Deferrals

- Stage 54D-3 Hold;
- Stage 54F #69 spacing, #70 grid/wireframe/active hierarchy, 4D volume
  readability, broad polish, Settings overflow, and setup-error colour;
- display-setting applicability/name findings carried from E4a unless a direct
  cockpit regression makes a minimal shared correction unavoidable; and
- replay-specific redesign beyond regression safety for shared components.
