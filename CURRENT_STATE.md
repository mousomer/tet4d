# CURRENT_STATE (Restart Handoff)

Last updated: 2026-03-20  
Branch: `true-animations`  
Worktree expectation: dirty only when an active batch is in progress

## Purpose

This file is the restart handoff for the current architecture baseline. It is
not a historical ledger. Long historical migration detail belongs in
`docs/history/DONE_SUMMARIES.md`.

## Current Authority

- For topology-playground architecture and migration-state questions, consult
  `docs/plans/topology_playground_current_authority.md` first.
- Older topology-playground manifests, stage plans, and audits remain useful
  background, but they are historical unless a future task explicitly
  reactivates them.
- If archived topology-playground manifests conflict with the current-authority
  file, follow the current-authority file.
- If a newer task instruction severely conflicts with the current-authority
  file or with current code reality, ask first and then update the manifest
  layer in the same batch if the direction changes.

## Active Batch Note

- Shared rotation animation mode is now a first-class shared gameplay setting rather than a hidden fallback.
- Advanced gameplay now exposes the mode selector directly, and `2D`/`3D`/`4D` runtime loop construction all load the persisted mode through `menu_settings_state.mode_rotation_animation_mode(...)`.
- Active `2D` animation overlays now clip seam-straddling cell boxes into topology-aware fragments, so rigid rotation and deliberate/cellwise tween paths both show partial geometry in each affected wrapped destination cell instead of one unsplit quad.
- Topology Playground Editor unification Stage 2 is now live for the migrated shell: the visible top-level workspace model is `Editor` / `Sandbox` / `Play`, Editor keeps its own remembered tool state, movement in Editor always updates the safe probe/selection target, and topology mutation stays behind explicit Editor-tool actions.
- Explorer Playground workspace stabilization follow-up (2026-03-20): Editor probe/dot and trace now stay live even while the Edit tool is active, Editor trace is an explicit on/off control, Sandbox focus/anchor now tracks a visible piece cell so `3D`/`4D` piece rendering survives entry and movement even when neighbor overlay is off, and the migrated shell now shows an explicit external right-side helper keyed to minimal movement/rotation guidance plus short workspace context.
- Manifest reconciliation and current-authority refresh (2026-03-20): `docs/plans/topology_playground_current_authority.md` is now the single current topology-playground architecture authority, while older topology-playground manifests/plans/audits are explicitly marked historical or supporting background.

Sections with `BEGIN/END GENERATED:*` markers are maintained by
`tools/governance/generate_maintenance_docs.py`.

<!-- BEGIN GENERATED:current_state_architecture_snapshot -->
## Current Architecture Snapshot

- `arch_stage`: `900`
- Canonical local gate: `CODEX_MODE=1 ./scripts/verify.sh`
- CI wrapper: `./scripts/ci_check.sh`
- Full local gate runs are serialized by `scripts/verify.sh`, use an isolated per-run state root via `TET4D_STATE_ROOT` when no explicit override is provided, and include the CI sanitation/policy checks (`scripts/check_policy_compliance.sh`, `scripts/check_policy_compliance_repo.sh`, `scripts/check_git_sanitation_repo.sh`) so local verification matches GitHub policy enforcement.
- Dependency direction:
  - `ui`, `ai`, `replay`, and `tools` may import engine modules directly
  - `engine` must not import `ui`, `ai`, `replay`, or `tools`
  - `engine/core` remains strict-pure
<!-- END GENERATED:current_state_architecture_snapshot -->

<!-- BEGIN GENERATED:current_state_metric_snapshot -->
## Current Metric Snapshot

From `python scripts/arch_metrics.py`:

- `deep_imports.engine_to_ui_non_api.count = 0`
- `deep_imports.engine_to_ai_non_api.count = 0`
- `deep_imports.ui_to_engine_non_api.count = 174` (allowed under current rule)
- `deep_imports.ai_to_engine_non_api.count = 27` (allowed under current rule)
- `engine_core_purity.violation_count = 0`
- `migration_debt_signals.pygame_imports_non_test.count = 0`
- `tech_debt.score = 2.97` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 1.89`
2. `code_balance = 1.07`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_canonical_ownership -->
## Canonical Ownership After This Batch

### Engine

- `src/tet4d/engine/core/piece_transform.py`
- `src/tet4d/engine/core/rotation_kicks.py`
- `src/tet4d/engine/core/rules/lifecycle.py`
- `src/tet4d/engine/topology_explorer/*`
- `src/tet4d/engine/gameplay/*`
- `src/tet4d/engine/gameplay/api.py`
- `src/tet4d/engine/runtime/*`
- `src/tet4d/engine/runtime/api.py`
- `src/tet4d/engine/tutorial/*`
- `src/tet4d/engine/tutorial/api.py`
- `src/tet4d/engine/api.py (small compatibility facade for replay/tests/tutorial payload exports)`

### UI

- `src/tet4d/ui/pygame/front2d_game.py`
- `src/tet4d/ui/pygame/front2d_setup.py`
- `src/tet4d/ui/pygame/front2d_loop.py`
- `src/tet4d/ui/pygame/front2d_session.py`
- `src/tet4d/ui/pygame/front2d_frame.py`
- `src/tet4d/ui/pygame/front2d_results.py`
- `src/tet4d/ui/pygame/frontend_nd_setup.py`
- `src/tet4d/ui/pygame/frontend_nd_state.py`
- `src/tet4d/ui/pygame/frontend_nd_input.py`
- `src/tet4d/ui/pygame/front3d_game.py`
- `src/tet4d/ui/pygame/front4d_game.py`
- `src/tet4d/ui/pygame/front3d_render.py`
- `src/tet4d/ui/pygame/front4d_render.py`
- `src/tet4d/ui/pygame/topology_lab/*`
- `src/tet4d/ui/pygame/runtime_ui/*`
- `src/tet4d/ui/pygame/menu/*`
- `src/tet4d/ui/pygame/launch/* (with settings_hub_model.py owning settings model/layout, settings_hub_actions.py owning settings mutations/text-entry, and launcher_settings.py owning orchestration/view)`
- `src/tet4d/ui/pygame/render/*`

### AI

- `src/tet4d/ai/playbot/*`
<!-- END GENERATED:current_state_canonical_ownership -->

## Transform Ownership Note

- The requested piece-transform extraction plan is already complete in code.
- Canonical owner: `src/tet4d/engine/core/piece_transform.py`.
- Retrospective plan/inventory docs now exist at:
  - `docs/plans/piece_transform_extraction.md`
  - `docs/plans/piece_transform_inventory.md`
- Current `HEAD` has already progressed beyond the original extraction-stage
  non-goal and now uses center-of-piece block rotation semantics.

## Explorer Playground Status

- The same-screen Explorer Playground product goal remains complete on `codex/toplogy-dirty`.
- Stage 1 of the canonical-state migration is now live: `src/tet4d/engine/runtime/topology_playground_state.py` now defines the engine/runtime-owned playground state contract.
- Stage 2 is now live for the migrated explorer path: explorer scene refresh, topology preview compilation, and explorer-side selection/probe highlighting now consume that canonical state through additive bridge helpers in `src/tet4d/ui/pygame/topology_lab/scene_state.py`, `src/tet4d/ui/pygame/topology_lab/controls_panel.py`, `src/tet4d/ui/pygame/topology_lab/boundary_picker.py`, and `src/tet4d/ui/pygame/launch/topology_lab_menu.py`.
- Retained UI-local shell fields in `src/tet4d/ui/pygame/topology_lab/scene_state.py` remain additive compatibility paths for non-migrated analysis/edit flows; Stage 3 completion here is limited to the core explorer gluing workflow, not every retained panel consumer.
- Stage 3 is live for the core direct explorer-entry topology edit flow: from the explorer scene, the user can select a source boundary, select a compatible target boundary, create or reselect a gluing draft, inspect the selected seam, edit its normalized transform in the linked side panel, and apply the glue without leaving the shell. Explorer-side boundary picks, seam picks, and glue-slot inspection now synchronize the canonical playground selection and draft state immediately.
- Stage 5 sandbox migration is now live through engine/runtime-owned playground state: `src/tet4d/engine/runtime/topology_playground_sandbox.py` now owns sandbox piece spawning, movement, rotation, and seam-cross preview against the active canonical playground topology, while `src/tet4d/ui/pygame/topology_lab/piece_sandbox.py` is reduced to a thin shell adapter instead of a detached state owner.
- Stage 6 demotion cleanup is now live: the launcher's ordinary custom-topology action now enters the unified Explorer Playground shell through `run_explorer_playground(...)`, so the detached lab route is no longer required for ordinary topology editing.
- Stage 7 is now live: the graphical explorer is the primary editor, while the former line+dots row/panel surface is explicitly demoted to `Analysis View` as a secondary view.
- Projection-first visualization follow-up (2026-03-13): for `3D` and `4D`, the Explorer Playground primary scene now uses synchronized 2D coordinate-plane projections (`xy/xz/yz` in `3D`; `xy/xz/xw/yz/yw/zw` in `4D`) with explicit hidden-coordinate slice labels and cross-panel cell selection, replacing the older free-camera shell sketches as the default user-facing inspector/sandbox view.
- Compact explorer-board defaults follow-up (2026-03-13): `build_explorer_playground_settings(...)` now starts untouched explorer launches on `8`-bounded board sizes in `2D/3D/4D`, keeping initial topology-lab boards under `9` on every axis while still preserving explicitly user-chosen board dimensions from launcher/setup flows.
- Semantics-correctness stabilization follow-up (2026-03-13): explorer/sandbox/gameplay now share one explicit `CELLWISE_FREE` vs `RIGID` movement-policy split on the active transport paths, the shared resolver distinguishes boundary point-maps from piece-frame transport, chart-split torus wraps remain rigidly coherent instead of being mislabeled as non-rigid, and the ND legality-preview/input path now uses the same policy-aware whole-piece transport semantics as live gameplay.
- Ownership + mode-boundary cleanup follow-up (2026-03-13): `src/tet4d/engine/runtime/topology_playground_state.py` now exposes explicit canonical/editor/inspector/sandbox/derived ownership views, `src/tet4d/ui/pygame/topology_lab/state_ownership.py` records the UI-side transient bucket split, and the live menu path now keeps sandbox projection focus/path/frame separate from inspector probe state for scene overlays, footer controls, and workspace diagnostics. `docs/history/topology_playground/topology_playground_ownership_audit.md` remains a useful transitional ownership snapshot, but `docs/plans/topology_playground_current_authority.md` is now the current architecture authority.
- Topology playground restructure Stage 1 follow-up (2026-03-20): the canonical playground state and migrated shell now treat `editor` / `sandbox` / `play` as the internal top-level workspaces, with legacy `Inspect` / `Edit` preserved only as editor-scoped compatibility tool labels. Sandbox neighbor-search is now explicit runtime/menu state instead of hidden ND behavior, and helper/status scaffolding is keyed to those canonical workspaces.
- Topology playground Editor unification Stage 2 follow-up (2026-03-20): the primary workspace ribbon now exposes `Editor` / `Sandbox` / `Play`, Explorer entry defaults to `Editor`, Editor keeps a remembered internal tool (`Probe` or `Edit`), probe movement and projection-cell selection stay safe in either Editor tool, and the action bar/helper copy now treat `Inspect` / `Edit` only as Editor-internal behaviors.
- Workspace regression stabilization follow-up (2026-03-20): Editor no longer loses the probe substrate when `Edit` is active, trace visibility is explicit and non-destructive, Sandbox movement/projection framing now keeps the visible piece tied to an actual rendered sandbox cell instead of a stale origin/focus slice, and the scene shell now keeps a visible external right-side helper with concise movement/rotation guidance instead of burying that guidance below the workspace.
- Explorer clarification follow-up (2026-03-21): the live guidance now states explicitly that the legacy Inspect dot is the Editor probe/dot, its movement and trace must stay consistent across seams in `2D` / `3D` / `4D`, trace visibility must be controlled by an explicit Explorer-panel button, Sandbox must show a piece by default in `2D` / `3D` / `4D`, neighbor markers must appear as small dots only when `neighbor search` is enabled, menu items must stay fully visible, and the translation/rotation helper panel must remain visible outside the main Explorer viewport.
- Explorer stabilization implementation pass (2026-03-21): the live shell now renders Editor trace and Sandbox piece state as projected overlays across `3D` / `4D` panels instead of hiding them behind exact hidden-axis slice matches, Sandbox neighbor-search now renders small marker dots without reusing the Editor trace line path, Editor probe movement no longer carries seam-rotated local controls forward after traversal so repeated movement stays canonical, and the current explorer/menu shell gives the controls column and outer helper panel more stable room while keeping the helper visually outside the main scene/editor panel on the tested layout.
- Explorer shell follow-up (2026-03-21): the `Trace` / `Neighbor` toggle now lives in the explorer panel header instead of the external helper, the helper stays keys-only outside the explorer panel, sandbox neighbor mode now renders real reachable neighbor dots in `2D` / `3D` / `4D` instead of reusing the focus path, and the `3D` / `4D` projection scenes now use the same filled sandbox-cell display logic as `2D`.
- Sandbox ND render correction (2026-03-21): sandbox projection scenes no longer draw the old whole-piece move-preview overlay in `3D` / `4D`, so Sandbox now shows only filled piece cells plus optional neighbor dots. With `Neighbor` off, the extra ND dots disappear entirely instead of merely shrinking.
- Sandbox ND visibility follow-up (2026-03-21): `3D` / `4D` projection panels no longer cap visible sandbox neighbor markers to the last few projected cells, and ND sandbox piece fills now use a larger outlined cell footprint so they read as real boxes instead of center dots. In sandbox mode, the selected ND cell keeps its outline but no longer paints a center dot over the box.
- Sandbox ND box-footprint adjustment (2026-03-21): the ND sandbox cell fill now uses a near-full-cell inset and tighter corners, so projected sandbox cells in `3D` / `4D` read as clear boxes even on smaller panel cell sizes instead of rounded dot-like blobs.
- The `Analysis View` pane now limits itself to board/preset settings, save/export, experiment-pack actions, and read-only seam context; row-based source/target/tangent/apply/remove controls no longer act as a parallel editor for the migrated explorer path.
- Menu ambiguity cleanup pass 1 remains the live baseline on that migrated path: `Explorer Preset` in `Analysis View` is the only visible preset selector, the transform editor shows the active preset as a read-only display, `Save`/`Export`/`Experiments`/`Back` no longer duplicate in the workspace action bar, analysis seam-context rows are non-selectable status displays, the `Normal Game` branch is labeled as legacy compatibility, and the footer movement grid distinguishes inspector-local traversal from sandbox piece movement.
- Mode/action simplification pass 2 follow-up is now live on the migrated explorer path: the scene-first workspace no longer exposes `Edit` / `Inspect` as peer top-level modes. Instead, `Editor` owns both safe probe/select flow and explicit edit flow, `Sandbox` owns piece experimentation, and `Play` owns launch/preview only.
- Legacy-consumer retirement follow-up (2026-03-12): the migrated probe/highlight path now writes canonical playground probe state through `src/tet4d/ui/pygame/topology_lab/scene_state.py` helpers, `src/tet4d/ui/pygame/topology_lab/controls_panel.py` delegates normal-mode rows and resolved-profile export to `src/tet4d/ui/pygame/topology_lab/legacy_panel_support.py`, and the unused `run_topology_lab_menu(...)` alias has been removed after caller audit found no remaining `src/` callers.
- Compatibility-debt retirement pass 2 is now live on the migrated explorer path: `src/tet4d/ui/pygame/topology_lab/scene_state.py` no longer relies on retained shell snapshots for probe-unavailable fallback, the direct play-launch path no longer re-syncs stale dirty shell fields before launch, and canonical runtime probe/play state remains authoritative on the explorer path.
- Remaining compatibility debt after this pass: retained shell snapshot fields in `src/tet4d/ui/pygame/topology_lab/scene_state.py` are still kept only as non-explorer compatibility mirrors, while normal-mode legacy rows and resolved-profile export remain intentionally isolated in `src/tet4d/ui/pygame/topology_lab/legacy_panel_support.py`.
- Stage 8 is now live: the shell's `Play This Topology` action launches directly from the current in-memory playground draft state, with no secondary conversion menu on the migrated path.
- The migrated play-launch path now bypasses the older shell-snapshot `build_explorer_playground_config(...)` helper and instead routes through `src/tet4d/engine/runtime/topology_playground_launch.py` plus `src/tet4d/ui/pygame/topology_lab/play_launch.py`, so gameplay launch now reads the canonical `TopologyPlaygroundState` directly.
- Stage 9 is now live: ordinary play menus and launcher settings surfaces are now preset-only for topology, keeping safe preset launches plus `Play Last Custom Topology` and `Open Explorer Playground` without reintroducing full topology editing into launcher UI.
- Explorer experiment packs are now live inside that shell: the current draft and preset family compile into a shared comparison/export batch, and the playground surfaces a recommended next topology to try.
- Latency reduction pass 1 is now live for the migrated explorer path: dimension changes no longer re-enter a cached post-sync refresh pass, Piece Set and Speed skip scene refresh when the preview signature is unchanged, Export Explorer Preview reuses the live preview payload when signatures match, and Build Experiment Pack now compiles once then exports that same batch. Representative 4D timings improved from the audit baselines 402.8 ms -> 2.1 ms for preview export and 10.31 s -> 5185.7 ms for experiment-pack generation.
- Explorer piece transport now keeps active-piece frame semantics explicit: `src/tet4d/engine/gameplay/explorer_piece_transport.py` classifies explorer moves as `plain_translation`, `rigid_transform`, or `cellwise_deformation`, while the 2D/ND explorer runtimes preserve frame metadata for ordinary translation, apply explicit rigid frame transforms for coherent seam moves, and block unsafe non-rigid seam deformation instead of silently rebasing the piece.

- Unsafe-topology correctness fix pass 1 (2026-03-12): preview/probe remains the cellwise topology surface and gameplay remains the rigid-piece transport surface, but sandbox now shares gameplay's transport classifier so both accept `plain_translation` and `rigid_transform` while still blocking `cellwise_deformation`. Non-bijective unsafe preset / board-size pairings now surface explicitly as `unsupported for current board dimensions ...` during preview/runtime validation instead of degrading into partial connectivity.
- Topology playability signaling pass 1 (2026-03-12): the canonical playground state now owns a runtime-derived playability analysis that distinguishes `valid` vs `invalid`, `cellwise explorable` vs `not explorable`, and `rigid-playable` vs `not rigid-playable` from current validation plus rigid transport behavior. Analysis View and the workspace status/preview panel surface that same signal directly above `Play This Topology`, so confusing cases such as valid-but-explorer-only `Projective` and invalid-dimension `Sphere` now explain themselves in-shell.
- Play-launch topology propagation + unsafe launch fix (2026-03-12, refined 2026-03-14): `Play This Topology` still refreshes launch-critical preview validity before deciding whether to block or launch, but it no longer treats stale dirty shell fields as an explorer-path source of truth. Launch now uses the canonical `TopologyPlaygroundState` already held by the migrated explorer path instead of re-importing drifted shell snapshots.
- Play-launch gameplay/runtime correction (2026-03-14): direct playground launch now enters ordinary gameplay controls/gravity/locking again instead of the free-exploration runtime, while 2D/ND gameplay still keeps explorer seam transport active whenever the launched topology carries an explorer profile.
- Live-path play regression follow-up (2026-03-20): focused launch-path tests now pin the broader non-trivial `Y`-seam contract on real gameplay state. Stage 1's traced bottom-boundary continuation coverage remains useful scaffolding, but it is now explicitly recorded as partial rather than a full Play drop/lock solution.
- Play drop/lock semantics fix (2026-03-20): `2D` and `ND` runtime now treat deliberate translation, gravity tick, soft drop, and hard drop as separate gameplay intents. Play groundedness/lock is based on one legal gravity/drop step under the Play drop policy, gravity-axis seam traversal no longer counts as generic fall continuation, sideways/topological entry into legal bottom-layer space still works, and hard drop now matches repeated drop legality on the live playground launch path.
- Play coverage hardening follow-up (2026-03-20): focused launch-path regressions now also pin `twisted_y_3d`, `twisted_y_4d`, a custom cross-axis `Y` seam, and one rotation-near-seam case through reusable invariant helpers for grounded/drop, hard-drop parity, and translation-vs-drop legality. Targeted ND input routing and playbot checks now also assert that soft drop stays on the explicit drop path while non-drop movement keeps using the deliberate translation path.
- GitHub Actions runtime follow-up (2026-03-20): workflow warnings about deprecated Node 20 JavaScript actions are now addressed by moving repo workflows from `actions/checkout@v4` / `actions/setup-python@v5` to the Node 24-compatible `v5` / `v6` lines before GitHub's June 2026 runner default switch.
- Actual-play spawn follow-up (2026-03-14): launched explorer-topology games no longer invalidate the opening piece while it is still above the gravity axis; standard spawn works again, and explorer seam transport takes over once the piece enters the board.
- Dimension-cycle sandbox follow-up (2026-03-14): changing Explorer Playground dimensions now clears stale sandbox transients from the previous dimension before canonical-state rebuild, so retained sandbox origin/local-block payloads no longer crash the migrated explorer shell during dimension changes.
- The ND launcher no longer treats Explorer Playground status messages as app-exit flags; `src/tet4d/ui/pygame/launch/launcher_nd_runner.py` now returns to the launcher menu after the playground closes unless the launcher callback itself explicitly requests exit.
- Startup optimization pass 1 is now live for the audited explorer-entry route: explicit Explorer launches skip the stored explorer-profile refresh, launch validation and default probe placement no longer build extra movement graphs, and representative first-frame readiness improved from `137.5/555.5/6890.3 ms` to `64.6/215.9/2326.1 ms` for `2D/3D/4D` launches while startup movement-graph builds fell from `4` to `1`.
- Remaining startup hotspot after that pass: the one required preview compile inside `_refresh_explorer_scene_state(...)`, especially in `4D`; the new playability signal now piggybacks on that canonical refresh using the live preview plus a lightweight rigid-transport scan, while the heavier experiment-pack analysis still remains deferred.

Stage 4 live playground settings remain available on the current explorer-entry shell: the playground exposes the dimension selector, board-axis size editors, and explorer preset selector, and those changes now refresh the migrated explorer scene through the engine/runtime-owned canonical state while retained UI-local shell fields remain compatibility debt for later cleanup.
- In one shell, the player can change presets, adjust board size, move and rotate the sandbox piece, glue/edit seams, and launch play from the current draft.
- Old configuration panels are intentionally still present for later-stage consolidation; this batch does not remove them.
- The remaining explorer topology work now includes the rest of the retained consumer migration plus later structural consolidation:
  1. migrate the remaining retained analysis/edit-panel consumers from `src/tet4d/ui/pygame/topology_lab/scene_state.py` onto `src/tet4d/engine/runtime/topology_playground_state.py`
  2. further structural decomposition of `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
  3. migration of additional retained panel responsibilities into the canonical playground state

## What This Batch Changed

1. Folded 2D into the shared `src/tet4d/ui/pygame/` frontend structure and split
   ownership into `front2d_game.py` (orchestration), `front2d_setup.py`
   (setup/menu), `front2d_loop.py` (runtime orchestration), `front2d_session.py`
   (session/state), `front2d_frame.py` (per-frame/update), and
   `front2d_results.py` (results/leaderboard flow).
2. Moved engine-owned render/frontend adapters out of `src/tet4d/engine/` into
   UI ownership.
3. Removed all remaining reverse imports from `engine` into `ui` and `ai`.
4. Decomposed engine-owned convenience exports into
   `src/tet4d/engine/gameplay/api.py`, `src/tet4d/engine/runtime/api.py`, and
   `src/tet4d/engine/tutorial/api.py`, while keeping `src/tet4d/engine/api.py`
   as a thin compatibility facade.
5. Cut `menu_settings_state` -> UI keybinding side effects; live keybinding sync
   now happens in UI runtime/menu code.
6. Repointed AI planners/controllers/dry-run tooling to direct engine imports,
   eliminating `engine -> ai` wrapper pressure in `engine/api.py`.
7. Centralized shared rotation-with-kicks application through
   `resolve_rotated_piece(...)`, deleting duplicated first-fit application logic
   from 2D and ND gameplay states.
8. Zeroed the reverse-import metric budgets and aligned the boundary script with
   the current one-way rule.
9. Rewrote stale architecture docs so they describe the current architecture,
   not the old migration-only `engine.api` seam.
10. Moved remaining governance and render-benchmark callers off `engine.api` onto
    direct engine/UI owners, then reduced `src/tet4d/engine/api.py` to a small
    compatibility facade used mainly by replay and explicit compatibility tests.
11. Finished the 2D runtime decomposition by splitting `front2d_loop.py` into
    orchestration, session/state, frame/update, and results owners, then
    deleted `front2d_runtime.py` after migrating affected callers/tests.
12. Extracted the duplicated setup-menu event/save loop into
    `src/tet4d/ui/pygame/menu/setup_menu_runner.py` and rewired both 2D and ND
    setup flows to use it.
13. Removed duplicated settings/default wrappers from
    `src/tet4d/ui/pygame/launch/launcher_settings.py` by extending
    `src/tet4d/engine/runtime/menu_settings_state.py` and reusing
    `src/tet4d/engine/runtime/settings_schema.py` window-size helpers.
14. Finished ND frontend decomposition by splitting shared ND ownership into
    `frontend_nd_setup.py` (setup/menu/config), `frontend_nd_state.py`
    (state creation), and `frontend_nd_input.py` (gameplay/input routing), then
    deleted `frontend_nd.py`.
15. Finished settings-hub decomposition by splitting shared settings ownership
    into `settings_hub_model.py` (model/layout/defaults),
    `settings_hub_actions.py` (mutation/text-entry/save/reset), and
    `launcher_settings.py` (orchestration/view), then deleted
    `settings_hub_state.py`.
16. Split oversized engine-runtime helpers into stable facades plus smaller
    internal owners:
    - `menu_settings_state.py` over `runtime/menu_settings/`
    - `menu_structure_schema.py` over `runtime/menu_structure/`
    - `score_analyzer.py` over `runtime/score_analysis/`
17. Applied a correctness hotfix batch after the restructure: the settings hub
    now seeds analytics from persisted runtime state,
    `score_analysis_summary_snapshot()` returns detached copies, and the unused
    `dispatch_nd_gameplay_key()` helper was deleted from
    `frontend_nd_input.py`.
18. Hardened local verification against recurring Windows state collisions by
    adding a serialized `verify.sh` lock, a per-run `TET4D_STATE_ROOT` sandbox
    for full-gate runs, and env-aware pytest temp roots for Codex/local test
    helpers.
19. Converted `CURRENT_STATE.md` and `docs/PROJECT_STRUCTURE.md` to mixed
    manual/generated maintenance docs and added
    `tools/governance/generate_maintenance_docs.py` plus verify-time drift
    checks for the generated sections.
20. Added `docs/plans/cleanup_master_plan.md` as the canonical cleanup ledger and used code, not manifests, as the stage-status authority for the remaining dedup program.
21. Narrowed `src/tet4d/engine/api.py` by deleting raw piece-transform re-exports; replay/tests now consume stable engine contracts there while transform tests import the canonical kernel directly.
22. Extracted shared gameplay orchestration into `src/tet4d/engine/gameplay/lock_flow.py` (lock-analysis / score-bookkeeping) and `src/tet4d/engine/core/rules/lifecycle.py` (lock-and-respawn / hard-drop flow), then rewired `game2d.py`, `game_nd.py`, `core/rules/gravity_2d.py`, and `core/step/reducer.py` to consume those shared owners.
23. Moved keybinding path/profile/json ownership into `src/tet4d/engine/runtime/keybinding_store.py`; `src/tet4d/ui/pygame/keybindings.py` now owns runtime maps and rebinding behavior only.
24. Unified the install contract on editable install from `pyproject.toml`, removed `requirements.txt`, added `scripts/check_editable_install.sh`, and wired that smoke check into `scripts/verify.sh`.
25. Further thinned `src/tet4d/engine/runtime/menu_structure_schema.py` by moving menu graph parsing into `runtime/menu_structure/menu_parse.py` and settings/payload parsing into `runtime/menu_structure/settings_parse.py`, keeping `menu_structure_schema.py` as the stable validation facade only.
26. Reduced the fixed 4D tutorial board profile to `8 x 20 x 7 x 6` and the fixed 4D exploration board profile to `8 x 9 x 7 x 6`.
27. Unified tutorial instruction copy around one plain-language `Do this:` line, one optional `Tip:` line, and simpler `USE:` input prompts, with clearer layman wording across the 4D lesson pack.
28. Added larger dedicated 4D piece-set options (`True 4D (7-cell)` and `True 4D (8-cell)`) plus regression coverage for the new 4D bag families.
29. Added machine-checked drift protection via `config/project/policy/manifests/drift_protection.json`, `tools/governance/check_drift_protection.py`, a generated `Live Drift Watch` section in `CURRENT_STATE.md`, and verify-time enforcement of thin-wrapper LOC budgets plus tutorial copy taxonomy.
30. Fixed recurring GitHub CI parity drift by restoring the executable bit on `scripts/check_editable_install.sh` and teaching `scripts/check_git_sanitation_repo.sh` to fail if any direct-run shell entrypoint in the repo loses `100755` mode in git metadata.
31. Split Topology Lab topology ownership by gameplay mode (`normal` vs `explorer`) for 3D/4D, with engine-owned validation rejecting wrapped `Y` boundaries in Normal Game while Explorer Mode persists separate topology profiles and allows bidirectional vertical traversal.
32. Added explorer-only `move_up` / `move_down` keybinding groups and routing for 2D/3D/4D exploration, removed stale `move_y_*` gameplay naming from live help/control mappings, and hid 3D/4D topology-profile setup rows so advanced topology now flows through the mode-aware Topology Lab store.
33. Added a new engine-only explorer topology kernel under `src/tet4d/engine/topology_explorer/` covering general boundary gluing descriptors, signed-permutation transform validation, move-through-boundary mapping, movement-graph compilation, and basic quotient-topology presets without switching the live runtime/UI to the new model yet.
34. Added Stage 2 runtime-owned explorer topology integration: `topology_explorer_store.py` now owns JSON save/load for general explorer gluing profiles, `topology_explorer_bridge.py` converts the representable subset of legacy explorer edge-rule profiles into the new gluing model for preview/export, `topology_explorer_preview.py` compiles and exports movement-graph previews, and Topology Lab export now emits that explorer preview when the current explorer profile is representable as a true paired-boundary gluing.
35. Added `scripts/verify_focus.sh` as the documented fast-path staged local validation helper for focused lint/tests and maintenance-doc checks while keeping `./scripts/verify.sh` as the required pre-commit/pre-push gate.
36. Replaced the legacy edge-rule editor path for Explorer 2D, Explorer 3D, and Explorer 4D inside Topology Lab with direct general-gluing editors backed by `src/tet4d/engine/runtime/topology_explorer_store.py`, engine-owned explorer presets, and live sidebar previews compiled from the explorer movement graph; Normal Game remains on the legacy lab path in this phase.
37. Added engine-owned unsafe `Projective` / `Sphere` explorer preset families for 2D/3D/4D and surfaced them in Topology Lab with explicit `[unsafe]` labeling while keeping validation canonical in `src/tet4d/engine/topology_explorer/glue_validate.py`.
38. Routed live Explorer 2D gameplay/runtime through the general gluing engine by adding `src/tet4d/engine/gameplay/explorer_runtime_2d.py`, teaching `src/tet4d/engine/gameplay/game2d.py` to use `explorer_topology_profile` for explorer movement/collision/hard-drop behavior, and updating `src/tet4d/ui/pygame/front2d_setup.py` so explorer setup resolves the stored gluing profile through the runtime-owned explorer profile model.
39. Expanded explorer preview diagnostics so `src/tet4d/engine/runtime/topology_explorer_preview.py` now exports engine-owned tangent-basis arrow mappings for each gluing, and `src/tet4d/ui/pygame/launch/topology_lab_menu.py` renders those signed basis transforms in the live lab sidebar directly from the preview payload.
40. Relaxed the newer thin-wrapper drift budgets for `cli/front.py`, `src/tet4d/engine/api.py`, and `src/tet4d/ui/pygame/front2d_game.py`, and documented a contributor-process rule preferring medium-sized localized patches over ultra-narrow patch fragmentation while keeping the core architecture/purity gates unchanged.
40a. Clarified contributor edit-method selection so `apply_patch` is reserved for localized code edits with fresh context, while broad drifting maintenance-doc rewrites use one deterministic scripted rewrite instead of repeated patch retries.
40b. Hardened contributor write-safety and verification process rules: source-file rewrites now forbid multiline PowerShell `-replace` and BOM-producing writes, require a touched-file hygiene pass after non-patch rewrites, and explicitly ban parallel `verify.sh` / `ci_check.sh` runs.
40c. Tightened edit-method escalation so dirty/generated maintenance files skip patch-first behavior, and one rejected `apply_patch` attempt on a file is now the maximum before switching to a deterministic rewrite path.
41. Replaced the explorer Topology Lab's text-only right-hand sidebar with a scene-first graphical playground built from `src/tet4d/ui/pygame/topology_lab/scene3d.py`, `scene4d.py`, `transform_editor.py`, `preview.py`, and `arrow_overlay.py`, so explorer 2D/3D/4D topology editing now starts from the graphical explorer shell rather than from a detached editor panel.
42. Added engine-backed probe traversal support to the explorer lab via `advance_explorer_probe(...)` and `explorer_probe_options(...)` in `src/tet4d/engine/runtime/topology_explorer_preview.py`, and surfaced those controls in the same graphical explorer shell so seam edits, arrows, diagnostics, and movement feedback update in one coherent scene-first playground.
43. Completed the missing scene-first topology-lab owners under `src/tet4d/ui/pygame/topology_lab/` (`scene_state.py`, `explorer_tools.py`, `boundary_picker.py`, `scene2d.py`, `piece_sandbox.py`) and reduced `src/tet4d/ui/pygame/launch/topology_lab_menu.py` to orchestration over those owners.
44. Made seam arrows directly clickable in the explorer scene, added explicit probe path state plus reset behavior, and rendered scene-visible probe trace/sandbox status for Explorer 2D/3D/4D.
45. Added explorer-only sandbox and play-preview regression coverage, including direct Explorer 2D/3D/4D launch-from-draft checks and a sandbox guard that reports non-rigid seam-crossing failures explicitly instead of silently corrupting piece motion.
46. Added `src/tet4d/engine/runtime/topology_explorer_runtime.py` as the runtime-owned resolver/export facade for explorer setup and legacy-profile preview export, and migrated `front2d_setup.py`, `frontend_nd_setup.py`, and Topology Lab export to that runtime owner so the UI no longer imports the legacy edge-rule bridge directly.
47. Unified live Explorer launch with the same scene-first topology playground shell, so Explorer 2D/3D/4D now enter `run_explorer_playground(...)` directly and use bound explorer movement inside the probe/sandbox tools instead of a separate detached explorer frontend.
48. Added `src/tet4d/ui/pygame/topology_lab/app.py` as the canonical explorer-playground launch owner, so Explorer Mode, Topology Lab, and play-preview now share one launch/config assembly path and differ only by entry context instead of by separate shell setup logic.
49. Removed topology-editor rows from the outer Explorer setup menus and made Explorer launch/export resolve the stored explorer gluing profile by default, so topology editing now lives in the unified scene-first playground shell rather than in detached setup-menu toggles.
50. Added runtime-owned Explorer experiment packs under `src/tet4d/engine/runtime/topology_explorer_experiments.py` plus a new `state/topology/explorer_experiments.json` export path, then wired the playground controls/action ribbon to build that pack from the current draft, compare it against the dimension's preset family, and show an in-shell recommended next topology.
51. Added shared atomic candidate-placement validation in `src/tet4d/engine/core/rules/piece_placement.py` and rewired `game2d.py`, `game_nd.py`, explorer runtime collision helpers, and topology-playground sandbox rotation so full-piece moves/rotations are validated and committed atomically across seam-aware runtime paths.

## Validation Status

Validation completed during this batch:

- focused cleanup slices covering `engine.api`, keybinding storage migration, and shared gameplay lifecycle/lock-flow helpers: passed
- focused `ruff check`: passed
- focused pytest batches covering the 2D split, compatibility facade, and shared kick-resolution paths: passed
- focused explorer-topology kernel tests (`test_topology_explorer.py`): passed
- focused 2D explorer runtime/setup tests (`test_game2d.py`, `test_front2d_setup.py`): passed
- focused atomic piece-placement and explorer seam parity regressions (`test_piece_placement.py`, `test_game2d.py`, `test_game_nd.py`, `test_explorer_transport_parity.py`, `test_topology_playground_sandbox.py`): passed
- focused topology-playground ownership regressions (`test_topology_playground_state.py`, `test_topology_lab_state_ownership.py`, `test_topology_lab_menu.py`, `test_topology_lab_sandbox.py`): passed
- focused explorer experiment pack checks (`test_project_config.py`, `test_topology_explorer_experiments.py`, `test_topology_lab_experiments.py`, `test_topology_explorer_preview.py`): passed
- `python scripts/arch_metrics.py`: passed with zero reverse imports
- `CODEX_MODE=1 ./scripts/verify.sh`: passed
- `CODEX_MODE=1 ./scripts/ci_check.sh`: passed

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy/manifests/drift_protection.json`.

Top 8 live Python hotspots by real LOC:

1. `tests/unit/engine/test_topology_lab_menu.py`: `2847` real LOC
2. `src/tet4d/ui/pygame/topology_lab/controls_panel.py`: `1926` real LOC
3. `scripts/arch_metrics.py`: `1869` real LOC
4. `src/tet4d/engine/tutorial/setup_apply.py`: `1496` real LOC
5. `src/tet4d/ui/pygame/launch/topology_lab_menu.py`: `1370` real LOC
6. `tools/governance/validate_project_contracts.py`: `1177` real LOC
7. `src/tet4d/ui/pygame/topology_lab/projection_scene.py`: `1039` real LOC
8. `tools/governance/generate_configuration_reference.py`: `982` real LOC

Thin-wrapper budgets:

1. `cli/front.py: 781/840 real LOC (compatibility launcher wrapper)`
2. `cli/front2d.py: 15/24 real LOC (thin 2D launcher shim)`
3. `cli/front3d.py: 15/24 real LOC (thin 3D launcher shim)`
4. `cli/front4d.py: 15/24 real LOC (thin 4D launcher shim)`
5. `src/tet4d/engine/api.py: 91/160 real LOC (small engine compatibility facade)`
6. `src/tet4d/ui/pygame/front2d_game.py: 116/180 real LOC (2D orchestration entrypoint)`

Tutorial wording drift guard:

1. Lesson copy must not start with `Goal:` or `Action:`.
2. Tutorial overlay must keep `Do this:`, `Tip:`, and `USE:` tokens.
<!-- END GENERATED:current_state_drift_watch -->

## Next High-Value Follow-Ups

1. Keep trimming the runtime-engine facades (`menu_structure_schema.py`,
   `score_analyzer.py`, `menu_settings_state.py`) only if hotspot growth returns.
2. Watch `settings_hub_model.py` and `settings_hub_actions.py` for another split
   only if new feature work pushes them back into mixed responsibility.
3. Keep docs, budgets, generated references, and package manifests synchronized
   whenever ownership changes.
4. If more 2D/ND gameplay orchestration duplication remains after `lock_flow.py` and `core/rules/lifecycle.py`, extract only the next shared owner that produces net deletion.
5. Keep `engine.api` narrow and do not reintroduce raw transform or upper-layer
   convenience exports there.
6. Continue explorer topology by polishing the scene-first graphical explorer shell (especially richer 3D/4D picking/visualization), then delete the remaining legacy bridge once non-advanced explorer setup/export no longer depend on edge-rule conversion.

## Restart Checklist

1. `git branch --show-current`
2. `git status --short`
3. Read:
   - `AGENTS.md`
   - `docs/RDS_AND_CODEX.md`
   - `docs/ARCHITECTURE_CONTRACT.md`
   - `CURRENT_STATE.md`
4. Capture fresh metrics:

```bash
python scripts/arch_metrics.py
```

5. Re-run the local gate before commit:

```bash
CODEX_MODE=1 ./scripts/verify.sh
./scripts/ci_check.sh
```
