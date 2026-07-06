# Project Structure And Documentation

This document describes the current canonical package layout and ownership model.

Sections with `BEGIN/END GENERATED:*` markers are maintained by
`tools/governance/generate_maintenance_docs.py`.

## Top-Level Layout

```text
tet4d/
|- cli/                         thin entrypoint shims
|- config/                      source-controlled runtime/config assets
|- docs/                        RDS, policies, handoff, and release docs
|- godot/                       Godot product-shell direction and replay spike
|- migration/                   checked-in migration traces plus generated engine-consumption bundle
|- native/                      C++ GDExtension skeleton and third-party native dependencies
|- packaging/                   PyInstaller spec and OS packaging scripts
|- scripts/                     local verification and architecture checks
|- unity/                       replay-only Unity spike project consuming copied migration bundle assets
|- src/tet4d/
|  |- ai/playbot/               playbot ownership
|  |- engine/                   reusable engine lower layer
|  |  |- core/                  pure deterministic helpers
|  |  |- gameplay/              gameplay rules and state
|  |  |- runtime/               config, persistence, validation, analytics
|  |  |- tutorial/              tutorial schema/content/runtime
|  |  `- ui_logic/              non-rendering engine-owned interaction helpers
|  |- replay/                   replay schema/playback helpers
|  `- ui/pygame/                pygame adapters and frontends
|- tests/                       top-level test tree
`- tools/                       governance, migration traces, stability, benchmark tooling
```

## Dependency Direction

The current rule is one-way:

1. `ui`, `ai`, `replay`, and `tools` may import engine modules directly.
2. `engine` must not import `ui`, `ai`, `replay`, or `tools`.
3. `engine/core` must remain pure.
4. `tet4d.engine.api` is a small compatibility surface for engine-owned helpers,
   not the only allowed import seam. Replay code and compatibility tests may use
   it; runtime UI/AI/tools should prefer direct canonical owners.

<!-- BEGIN GENERATED:project_structure_entry_points -->
## Canonical Entry Points

1. `cli/front.py`: unified launcher
2. `cli/front2d.py`: thin 2D shim
3. `cli/front3d.py`: thin 3D shim
4. `cli/front4d.py`: thin 4D shim
<!-- END GENERATED:project_structure_entry_points -->

<!-- BEGIN GENERATED:project_structure_runtime_owners -->
## Canonical Runtime Owners

### Engine

1. `src/tet4d/engine/api.py`: small compatibility facade used mainly by replay and explicit compatibility tests
2. `src/tet4d/engine/gameplay/api.py`: gameplay convenience exports
3. `src/tet4d/engine/runtime/api.py`: runtime/help/menu convenience exports
4. `src/tet4d/engine/tutorial/api.py`: tutorial convenience exports
5. `src/tet4d/engine/core/piece_transform.py`: canonical piece-local transform math
6. `src/tet4d/engine/core/rotation_kicks.py`: canonical kick candidate generation and shared resolution
7. `src/tet4d/engine/core/rules/lifecycle.py`: shared lock/spawn/drop lifecycle orchestration
8. `src/tet4d/engine/topology_explorer/`: explorer-only general gluing kernel, validation, mapping, and movement graph helpers
9. `src/tet4d/engine/gameplay/game2d.py`: 2D gameplay state/rules
10. `src/tet4d/engine/gameplay/game_nd.py`: 3D/4D gameplay state/rules
11. `src/tet4d/engine/gameplay/lock_flow.py`: shared lock-and-analysis orchestration
12. `src/tet4d/engine/runtime/menu_config.py`: menu/runtime config loading
13. `src/tet4d/engine/runtime/keybinding_store.py`: runtime-owned keybinding profile/path/json storage
14. `src/tet4d/engine/runtime/menu_settings_state.py`: stable persisted-settings facade over `runtime/menu_settings/`
15. `src/tet4d/engine/runtime/menu_structure_schema.py`: stable menu-structure parsing facade over `runtime/menu_structure/`
16. `src/tet4d/engine/runtime/score_analyzer.py`: stable score-analysis facade over `runtime/score_analysis/`
17. `src/tet4d/engine/tutorial/content.py`: tutorial content loader
18. `src/tet4d/engine/tutorial/runtime.py`: tutorial runtime session logic

### UI

1. `src/tet4d/ui/pygame/front2d_game.py`: 2D orchestration entry
2. `src/tet4d/ui/pygame/front2d_setup.py`: 2D setup/menu owner
3. `src/tet4d/ui/pygame/front2d_loop.py`: 2D runtime orchestration entrypoint
4. `src/tet4d/ui/pygame/front2d_session.py`: 2D session/state owner
5. `src/tet4d/ui/pygame/front2d_frame.py`: 2D per-frame/update owner
6. `src/tet4d/ui/pygame/front2d_results.py`: 2D results/leaderboard owner
7. `src/tet4d/ui/pygame/frontend_nd_setup.py`: shared ND setup/menu/config owner
8. `src/tet4d/ui/pygame/frontend_nd_state.py`: shared ND state-construction owner
9. `src/tet4d/ui/pygame/frontend_nd_input.py`: shared ND gameplay/input routing owner
10. `src/tet4d/ui/pygame/front3d_game.py`: 3D frontend
11. `src/tet4d/ui/pygame/front4d_game.py`: 4D frontend
12. `src/tet4d/ui/pygame/front3d_render.py`: 3D render adapter
13. `src/tet4d/ui/pygame/front4d_render.py`: 4D render adapter
14. `src/tet4d/ui/pygame/topology_lab`: explorer topology lab editor helpers
15. `src/tet4d/ui/pygame/runtime_ui`: bootstrap, pause/help, tutorial overlay, shared loop helpers
16. `src/tet4d/ui/pygame/launch`: launcher, settings, bot, leaderboard flows, including `settings_hub_model.py`, `settings_hub_actions.py`, and `launcher_settings.py`
17. `src/tet4d/ui/pygame/menu`: shared menu/keybinding adapters, including `setup_menu_runner.py`
18. `src/tet4d/ui/pygame/render`: render/layout/helper adapters

### AI

1. `src/tet4d/ai/playbot/controller.py`: playbot runtime controller
2. `src/tet4d/ai/playbot/planner_2d.py`: 2D planning
3. `src/tet4d/ai/playbot/planner_nd.py`: ND planning entry
4. `src/tet4d/ai/playbot/planner_nd_core.py`: shared ND candidate logic
5. `src/tet4d/ai/playbot/planner_nd_search.py`: ND search/budget logic
6. `src/tet4d/ai/playbot/dry_run.py`: stability/dry-run harness
<!-- END GENERATED:project_structure_runtime_owners -->

<!-- BEGIN GENERATED:project_structure_sources_of_truth -->
## Config And Docs Sources Of Truth

1. `config/project/policy_pack.json`: single machine-readable governance authority
2. `AGENTS.md`: thin dispatch for contributor and agent entry
3. `docs/WORKFLOW_CODEX.md`: human workflow explainer for repo process and verification
4. `CURRENT_STATE.md`: restart handoff only
5. `docs/rds/`: durable product requirements
6. `docs/plans/gameboard_visual_language_design.md`: Live 3D and future Live 4D gameboard visual-language authority
7. `docs/plans/topology_godot_core_port_plan.md`: Stage 25 topology Godot/C++ core-port planning authority
8. `docs/ARCHITECTURE_CONTRACT.md`: dependency contract
9. `docs/BACKLOG.md`: active backlog and current change footprint
10. `config/menu/structure.json`: launcher/pause/settings/help/menu graph and copy
11. `config/menu/defaults.json`: default persisted settings payload
12. `config/tutorial/lessons.json`: tutorial packs and board profiles
13. `config/gameplay/tuning.json`: scoring/kick/tuning defaults
14. `docs/CONFIGURATION_REFERENCE.md`: generated full config inventory
15. `docs/USER_SETTINGS_REFERENCE.md`: generated user-facing settings summary

### Stage 20 Topology Identifier Normalization Parity

1. `docs/architecture/topology_identifier_normalization_parity.md`: Stage 20 topology identifier normalization parity doc
2. `tools/parity/topology_identifier_normalization_parity.py`: Stage 20 parity harness

### Stage 21 Parity Evidence Package Review

1. `docs/architecture/parity_evidence_package_review.md`: Stage 21 package review of Stages 15, 18, and 20

### Stage 22 Trace Schema/Version Normalization Parity

1. `docs/architecture/trace_schema_version_normalization_parity.md`: Stage 22 trace schema/version normalization parity doc
2. `tools/parity/trace_schema_version_normalization_parity.py`: Stage 22 parity harness
<!-- END GENERATED:project_structure_sources_of_truth -->

## Placement Rules

1. Put pure deterministic logic in `src/tet4d/engine/core/`.
2. Put gameplay/runtime/tutorial logic in `src/tet4d/engine/`.
3. Put `pygame` frontends, rendering, audio, and menu adapters in `src/tet4d/ui/pygame/`.
4. Put playbot ownership in `src/tet4d/ai/playbot/`.
5. Keep CLI files as thin shims over package code.
6. Prefer reusing an existing canonical owner over adding wrappers.
7. Do not reintroduce reverse imports from engine into UI or AI.
8. Put migration replay/export tooling in `tools/migration/` and checked-in
   small topology, gameplay, and endgame replay artifacts in
   `migration/golden_traces/`; these artifacts are migration oracles, not
   gameplay or renderer authority.
9. Keep committed parity fixtures under `tests/fixtures/parity/` and route
   them through the matching parity harness docs rather than treating them as
   runtime assets.
10. Keep maintained parity harnesses under `tools/parity/` and
   `tests/unit/migration/`, while migration-only exporters and trace helpers
   remain under `tools/migration/`. Stage 18 parity work must follow
   `docs/architecture/second_parity_slice_candidate_selection.md` and
   `docs/architecture/trace_metadata_identity_digest_parity.md`; do not change
   parity routing outside the approved governance path.
11. Keep `migration/exported_bundle/` generated from
    `tools/migration/export_config_bundle.py`; it is a disposable engine-spike
    input package, not a config, trace, docs, or runtime authority.
11. Keep Unity replay code under `unity/Tet4D.Unity/` and load only the copied
    `Assets/StreamingAssets/tet4d_bundle/` payload at runtime; Unity is a
    replay/browser surface here, not a gameplay/topology/endgame semantic owner.
12. Keep Godot shell code under `godot/Tet4D.Godot/` and load only the copied
    `res://assets/tet4d_bundle/` payload for the current replay spike. Godot is
    the conditional primary product shell direction after Stage 7, with
    GDScript owning shell/UI/rendering and no gameplay/topology/endgame
    semantics until a native core passes trace parity.
13. Use `docs/plans/godot_core_port_plan.md` for the Stage 7 engine decision
    and Stage 8+ core-port order. The recommended future core path is C++
    GDExtension; do not add C++, C#, GDExtension, gameplay, topology, or
    endgame implementation as part of Stage 7 documentation work.
14. Keep native core code under `native/tet4d_core/`, with the official
    `godot-cpp` dependency isolated as `native/third_party/godot-cpp`. Stage 8
    is native integration proof; Stage 9 adds only the plain bounded 2D
    `gameplay_plain_2d_short` parity slice; Stage 10 adds canonical snapshot
    and `state_hash` parity for that same short trace; Stage 11 broadens
    plain bounded 2D parity to rotation, hard-drop lock, and line-clear golden
    traces. Stage 12 adds a narrow live plain bounded 2D shell where Godot
    routes input and renders C++ snapshots while native code owns gameplay
    state transitions. Stage 13 polishes only that accepted live 2D slice.
    Stage 14 adds `docs/plans/plain_nd_core_parity_plan.md` as the planning
    gate for plain bounded 3D/4D native parity. Stage 15 adds a sidecar
    plain-ND trace scaffold under `native/tet4d_core/` plus
    `docs/plans/plain_nd_core_parity_contract.md`; it exports only parity
    traces for `gameplay_plain_3d_short` and `gameplay_plain_4d_short`.
    Stage 16 adds `docs/plans/plain_nd_coverage_expansion_plan.md` as the
    next coverage-planning authority for rotation, clear/scoring, and
    spawn-blocked game-over before any broader ND implementation. Stage 17
    adds those Python-oracle golden traces under `migration/golden_traces/`
    while native C++ parity remains scoped to implemented cases. Stage 18 adds
    trace metadata identity/digest parity only for the metadata-only slice in
    `docs/architecture/trace_metadata_identity_digest_parity.md`. Stage 19
    adds native clear/scoring
    parity only for `gameplay_plain_3d_plane_clear_short` and
    `gameplay_plain_4d_plane_clear_short`. Stage 20 adds native
    spawn-blocked game-over parity only for
    `gameplay_plain_3d_spawn_blocked_game_over` and
    `gameplay_plain_4d_spawn_blocked_game_over`; live 3D/4D, topology,
    endgame, Python runtime, C#, Steam, or console
    implementation is not authorized here. Stage 21 adds
    `docs/plans/live_plain_nd_godot_prototype_plan.md` as the planning-only
    authority for live plain ND work: Stage 22 prototypes live plain 3D first,
    Stage 23 adds live plain 4D, Godot reuses the existing trace coordinate
    mapper/renderer, and C++ remains gameplay authority. Stage 22 adds only
    that live plain 3D prototype through a
    native `PlainNDSession` facade plus Godot command routing/HUD. Stage 23
    adds the narrow Live Plain 4D prototype through the same native
    `PlainNDSession` owner, separate `live_4d_*` bridge methods, side-by-side W
    slices through the existing mapper/renderer, Q/E W movement, six direct
    rotation plane pairs, and `LIVE 4D · C++ CORE` HUD state; topology,
    endgame, Python runtime, C#, Steam, or console implementation remains
    deferred. Stage 22d adds
    `docs/plans/gameboard_visual_language_design.md` as the design-only
    authority for Live 3D and future Live 4D board readability. Stage 22e must
    implement that grammar through the existing mapper/renderer path, the
    structural Godot shell layout, and focused presentation/projection
    ownership. Stage 22f must manually accept Live 3D readability using
    `docs/plans/godot_live_3d_manual_acceptance.md`. The initial Stage 22f
    inspection failed, so Stage 22g corrects only the Live 3D visual
    observations: above-board canonical camera/default Fit View, visible camera
    diagnostics, compact bundle status with inspector detail, stronger active
    cells versus locked cells, and an active origin/orientation marker.
    Stage 22f manual Live 3D visual acceptance passed after Stage 22g
    corrections. Stage 23 Live Plain 4D Godot Prototype is implemented
    narrowly while preserving Live 2D, Live 3D, Replay, topology, endgame, and
    golden traces. Stage 23b corrects manual Live 4D acceptance defects in
    Godot shell/rendering only: larger backed W labels, Space captured as live
    hard-drop before UI accept handling, and restrained Live 4D active-cell
    brightness. Stage 23c further corrects Live 4D view/readability in Godot
    presentation/input only: `W SLICE n/N` headers, W-header fit bounds,
    canonical fitted Live 4D entry/reset, Fit View recovery, and safe camera
    keys that do not overlap gameplay. Stage 23 Live Plain 4D Godot Prototype
    passed manual GUI acceptance after Stage 23b/23c/23d corrections. Live 4D
    is accepted as a narrow plain bounded prototype. Stage 24 Live ND polish
    and hardening is implemented as Godot shell lifecycle/input hardening:
    returning from Replay resumes the selected Live 2D/3D/4D session without
    resetting native state, pauses non-selected live modes, and preserves
    pre-UI Space and Live 4D camera/zoom capture. Topology and endgame remain
    deferred. Manual Stage 24 acceptance is required before Stage 25 topology
    planning.

<!-- BEGIN GENERATED:project_structure_verification_contract -->
## Verification Contract

Run:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

Authoritative enforcement is backed by:

1. `scripts/check_editable_install.sh`
2. `scripts/check_architecture_boundaries.sh`
3. `scripts/check_engine_core_purity.sh`
4. `scripts/arch_metrics.py`
5. `tools/governance/architecture_metric_budget.py`
<!-- END GENERATED:project_structure_verification_contract -->

<!-- BEGIN GENERATED:project_structure_symbol_index -->
## Public Symbol Skim

This routing aid lists compact top-level public symbols from configured source files.
It is a public symbol skim for navigation, not full API documentation, and it does not try to list every symbol.

- `cli/front.py`: `MainMenuState`, `run()`, `main(argv=...)`
- `cli/front2d.py`: `main(argv=...)`
- `cli/front3d.py`: `main(argv=...)`
- `cli/front4d.py`: `main(argv=...)`
- `src/tet4d/ai/playbot/controller.py`: `PlayBotController`
- `src/tet4d/ai/playbot/dry_run.py`: `run_dry_run_2d(cfg, *, max_pieces=..., seed=..., ...)`, `run_dry_run_nd(cfg, *, max_pieces=..., seed=..., ...)`
- `src/tet4d/ai/playbot/lookahead_common.py`: `choose_best_with_followup(*, candidates, base_candidate, score_of, cleared_of, ...)`
- `src/tet4d/ai/playbot/planner_2d.py`: `BotPlan2D`, `plan_best_2d_move(state, *, profile=..., budget_ms=..., algorithm=...)`
- `src/tet4d/ai/playbot/planner_nd.py`: `BotPlanND`, `plan_best_nd_move(state, *, profile=..., budget_ms=..., algorithm=...)`
- `src/tet4d/ai/playbot/planner_nd_core.py`: `build_column_levels(cells, *, lateral_axes, gravity_axis)`, `drop_piece_fast(piece, *, dims, gravity_axis, lateral_axes, ...)`, `column_key(coord, lateral_axes)`, `iter_lateral_columns(dims, lateral_axes)`, `top_by_column(cells, lateral_axes, gravity_axis)`, `column_height_and_holes(column, top, cells, *, dims, ...)`, `height_roughness(heights, *, dims, lateral_axes)`, `height_features(cells, dims, gravity_axis)`, `evaluate_nd_board(cells, dims, gravity_axis, cleared, game_over)`, `simulate_lock_board(state, piece)`, `level_completion_score(cells, *, dims, gravity_axis)`, `hole_count(cells, *, dims, gravity_axis)`, ...
- `src/tet4d/ai/playbot/planner_nd_search.py`: `enumerate_orientations(start_blocks, ndim, gravity_axis)`, `SearchPlanND`, `plan_best_nd_with_budget(state, *, profile, planning_budget_ms, algorithm)`
- `src/tet4d/ai/playbot/types.py`: `playbot_adaptive_candidate_cap_for_ndim(ndim)`, `playbot_adaptive_fallback_enabled()`, `playbot_adaptive_lookahead_min_budget_ms(ndim)`, `playbot_auto_algorithm_policy_for_ndim(ndim)`, `playbot_board_size_scaling_policy_for_ndim(ndim)`, `playbot_budget_table_for_ndim(ndim)`, `playbot_clamp_policy()`, `playbot_deadline_safety_ms()`, `playbot_learning_mode_policy()`, `playbot_lookahead_depth(ndim, profile)`, `playbot_lookahead_top_k(ndim, profile, depth)`, `BotMode`, ...
- `src/tet4d/engine/api.py`: `new_game_state_2d(config, *, board=..., rng=..., seed=...)`, `new_game_state_nd(config, *, board=..., rng=..., seed=...)`, `new_rng(seed=...)`, `step_2d(state, action=...)`, `step_nd(state)`, `step(state, action=...)`, `board_cells(state)`, `current_piece_cells(state, *, include_above=...)`, `is_game_over(state)`
- `src/tet4d/engine/core/model/board.py`: `BoardND`
- `src/tet4d/engine/core/model/game2d_types.py`: `Action`, `GameConfig2DLike`, `ActivePiece2DLike`, `BoardCells2DLike`, `GameState2DLike`
- `src/tet4d/engine/core/model/game2d_views.py`: `GameConfig2DCoreView`, `GameState2DCoreView`
- `src/tet4d/engine/core/model/game_nd_views.py`: `GameConfigNDCoreView`, `GameStateNDCoreView`
- `src/tet4d/engine/core/piece_transform.py`: `block_axis_bounds(blocks)`, `canonicalize_blocks_nd(blocks)`, `canonicalize_blocks_2d(blocks)`, `normalize_blocks_2d(blocks)`, `normalize_blocks_nd(blocks)`, `rotate_point_2d(x, y, quarter_turns=..., *, steps_cw=...)`, `rotation_pivot_2d(blocks)`, `rotate_blocks_2d(blocks, quarter_turns=..., *, steps_cw=...)`, `rotate_point_nd(point, axis_a, axis_b, quarter_turns=..., ...)`, `rotate_blocks_nd(blocks, axis_a, axis_b, quarter_turns=..., ...)`, `rotate_blocks_nd_continuous(blocks, axis_a, axis_b, angle_radians)`, `rotation_planes_nd(ndim, gravity_axis)`, ...
- `src/tet4d/engine/core/rng/engine_rng.py`: `EngineRNG(seed=...)`, `coerce_random(*, rng=..., seed=...)`, `normalize_rng_mode(mode)`
- `src/tet4d/engine/core/rules/board_rules.py`: `full_levels(dims, cells, gravity_axis)`, `clear_planes(dims, cells, gravity_axis)`
- `src/tet4d/engine/core/rules/gravity_2d.py`: `apply_gravity_tick_2d(state)`
- `src/tet4d/engine/core/rules/lifecycle.py`: `lock_and_respawn(state)`, `advance_or_lock_and_respawn(state, *, try_advance)`, `run_hard_drop(state, *, try_advance)`
- `src/tet4d/engine/core/rules/locking.py`: `LockScoreResult`, `apply_lock_and_score(*, board, visible_piece_cells, color_id, ...)`
- `src/tet4d/engine/core/rules/piece_placement.py`: `CandidatePiecePlacement`, `build_candidate_piece_placement(piece, cells)`, `validate_candidate_piece_placement(candidate, board_cells, *, ignore_cells=..., ...)`, `commit_piece_placement(state, candidate, *, attribute=...)`
- `src/tet4d/engine/core/rules/scoring.py`: `score_for_clear(cleared_count)`
- `src/tet4d/engine/core/rules/state_queries.py`: `board_cells(state)`, `current_piece_cells(state, *, include_above=...)`, `is_game_over(state)`, `can_piece_exist_2d(state, piece, *, ignore_cells=...)`
- `src/tet4d/engine/core/step/reducer.py`: `apply_action_2d(state, action)`, `step_2d(state, action)`, `step_nd(state)`
- `src/tet4d/engine/gameplay/api.py`: `gravity_interval_ms_gameplay(speed_level, *, dimension)`, `map_overlay_cells_gameplay(*args, **kwargs)`, `topology_mode_from_index_runtime(index)`, `topology_mode_label_runtime(mode)`, `topology_mode_options_runtime()`, `topology_designer_profiles_runtime(dimension)`, `topology_designer_profile_label_runtime(dimension, index)`, `topology_designer_resolve_runtime(*, dimension, gravity_axis, topology_mode, ...)`, `topology_designer_export_runtime(*, dimension, gravity_axis, topology_mode, ...)`, `piece_set_2d_options_gameplay()`, `piece_set_2d_label_gameplay(piece_set_id)`, `piece_set_label_gameplay(piece_set_id)`, ...
- `src/tet4d/engine/gameplay/challenge_mode.py`: `apply_challenge_prefill_2d(state, *, layers, fill_ratio=...)`, `apply_challenge_prefill_nd(state, *, layers, fill_ratio=...)`
- `src/tet4d/engine/gameplay/exploration_mode.py`: `minimal_exploration_dims_2d(piece_set_id, *, random_cell_count=...)`, `minimal_exploration_dims_nd(ndim, piece_set_id, *, random_cell_count=...)`
- `src/tet4d/engine/gameplay/explorer_movement_policy.py`: `normalize_explorer_movement_policy(value)`, `explorer_movement_policy_from_rigid_play_enabled(rigid_play_enabled)`
- `src/tet4d/engine/gameplay/explorer_piece_transport.py`: `ExplorerPieceMoveOutcome`, `classify_explorer_piece_move(source_cells, moved_cells)`
- `src/tet4d/engine/gameplay/explorer_runtime_2d.py`: `move_piece_via_explorer_glue_2d(piece, *, transport, dx, dy, ...)`, `piece_cells_in_bounds_2d(piece, *, dims)`, `can_piece_exist_explorer_2d(board_cells, piece, *, dims, ignore_cells=...)`
- `src/tet4d/engine/gameplay/explorer_runtime_nd.py`: `ExplorerPieceMoveResultND`, `move_piece_via_explorer_glue_with_frame(piece, *, transport, axis, delta, ...)`, `move_piece_via_explorer_glue(piece, *, transport, axis, delta, ...)`, `piece_cells_in_bounds(piece, *, dims)`, `can_piece_exist_explorer(board, piece, *, dims, ignore_cells=...)`
- `src/tet4d/engine/gameplay/game2d.py`: `GameConfig`, `GameState`
- `src/tet4d/engine/gameplay/game_nd.py`: `GameConfigND`, `GameStateND`
- `src/tet4d/engine/gameplay/leveling.py`: `compute_speed_level(*, start_level, lines_cleared, enabled, ...)`
- `src/tet4d/engine/gameplay/lock_flow.py`: `LockFlowResult`, `visible_locked_cells(mapped_cells, *, gravity_axis)`, `has_cells_above_gravity(mapped_cells, *, gravity_axis)`, `apply_lock_flow(*, board, board_pre, dims, gravity_axis, ...)`
- `src/tet4d/engine/gameplay/pieces2d.py`: `PieceShape2D`, `get_standard_tetrominoes()`, `normalize_piece_set_2d(piece_set)`, `piece_set_2d_label(piece_set)`, `get_random_pieces_2d(rng, cell_count=..., bag_size=...)`, `get_debug_rectangles_2d(board_dims=...)`, `get_piece_bag_2d(piece_set=..., *, rng=..., random_cell_count=..., ...)`, `ActivePiece2D`
- `src/tet4d/engine/gameplay/pieces_nd.py`: `piece_set_options_for_dimension(ndim)`, `piece_set_label(piece_set_id)`, `normalize_piece_set_4d(piece_set_4d)`, `normalize_piece_set_for_dimension(ndim, piece_set_id)`, `lift_2d_blocks_to_nd(blocks_2d, ndim)`, `get_debug_rectangles_nd(ndim, board_dims=...)`, `PieceShapeND`, `get_piece_shapes_nd(ndim, *, piece_set_id=..., piece_set_4d=..., ...)`, `get_standard_pieces_nd(ndim, piece_set_4d=...)`, `ActivePieceND`
- `src/tet4d/engine/gameplay/pieces_shared.py`: `scaled_span(axis_size, ratio, min_size, max_cap=...)`
- `src/tet4d/engine/gameplay/play_move_intents.py`: `is_drop_intent(intent)`, `crosses_gravity_seam(step_result, *, gravity_axis)`
- `src/tet4d/engine/gameplay/rotation_anim.py`: `RigidPieceOverlay2D`, `PieceRenderStateND`, `PieceRotationAnimator2D`, `PieceRotationAnimatorND`
- `src/tet4d/engine/gameplay/scoring_bonus.py`: `plane_cell_count_for_dims(dims, *, gravity_axis)`, `score_with_clear_bonuses(*, raw_base_points, cleared_count, ...)`
- `src/tet4d/engine/gameplay/speed_curve.py`: `gravity_interval_ms(speed_level, *, dimension)`
- `src/tet4d/engine/gameplay/topology.py`: `normalize_topology_mode(mode)`, `topology_mode_from_index(index)`, `topology_mode_index_from_id(mode)`, `topology_mode_label(mode)`, `normalize_edge_behavior(value)`, `default_edge_rules_for_mode(axis_count, gravity_axis, *, mode, ...)`, `TopologyPolicy`, `map_piece_cells(policy, coords, *, allow_above_gravity)`, `map_overlay_cells(policy, coords, *, allow_above_gravity)`
- `src/tet4d/engine/gameplay/topology_designer.py`: `TopologyDesignerProfile`, `TopologyProfileState`, `normalize_topology_gameplay_mode(mode)`, `topology_gameplay_mode_label(mode)`, `validate_topology_profile_state(*, gameplay_mode, dimension, gravity_axis, ...)`, `designer_profiles_for_dimension(dimension, gameplay_mode=...)`, `designer_profile_label_for_index(dimension, index, gameplay_mode=...)`, `profile_state_from_preset(*, dimension, gravity_axis, gameplay_mode, ...)`, `default_topology_profile_state(*, dimension, gravity_axis, gameplay_mode)`, `topology_profile_state_from_payload(*, dimension, gravity_axis, gameplay_mode, payload)`, `topology_profile_state_payload(profile)`, `export_topology_profile_state(*, profile, gravity_axis)`, ...
- `src/tet4d/engine/help_text.py`: `HelpTextValidationError`, `help_content_registry()`, `help_layout_registry()`, `help_action_layout_registry()`, `help_topic_block_lines(topic_id, *, compact)`, `help_topic_compact_limit(topic_id)`, `help_topic_compact_overflow_line(topic_id)`, `help_value_template(name, *, default=...)`, `help_action_group_heading(group)`, `help_fallback_topic()`, `help_layout_payload()`, `help_action_layout_payload()`, ...
- `src/tet4d/engine/runtime/api.py`: `topology_lab_menu_payload_runtime()`, `bot_options_rows_runtime()`, `bot_defaults_by_mode_runtime()`, `ui_copy_section_runtime(section)`, `active_key_profile_runtime()`, `runtime_binding_groups_for_dimension_runtime(dimension)`, `profile_tiny_runtime()`
- `src/tet4d/engine/runtime/endgame_presets.py`: `normalize_endgame_preset_id(value, *, default=...)`, `normalize_endgame_boundary_response(value, *, default=...)`, `normalize_endgame_particle_collisions(value, *, default=...)`, `resolve_endgame_interaction_axes(*, boundary_response=..., particle_collisions=..., ...)`
- `src/tet4d/engine/runtime/help_topics.py`: `HelpTopicsValidationError`, `help_topics_registry()`, `help_action_topic_registry()`, `normalize_help_context(context_label)`, `help_topics_for_context(*, dimension, context_label)`
- `src/tet4d/engine/runtime/keybinding_runtime_state.py`: `normalize_rebind_conflict_mode(mode)`, `cycle_rebind_conflict_mode(mode, step=...)`, `KeybindingRuntimeState(*, defaults_payload=..., active_profile=...)`
- `src/tet4d/engine/runtime/keybinding_store.py`: `validate_keybinding_defaults_payload(payload)`, `validate_keybinding_file_payload(payload, *, expected_dimension=..., ...)`, `load_keybinding_defaults_payload()`, `normalize_builtin_profile(raw)`, `normalize_profile_name(raw)`, `active_key_profile_from_env()`, `selected_profile_name(profile, active_profile)`, `safe_resolve_keybinding_path(path)`, `default_keybinding_file_path(dimension)`, `profile_keybinding_file_path(dimension, profile)`, `keybinding_file_path_for_profile(dimension, *, profile=..., active_profile=...)`, `resolve_keybinding_io_path(dimension, *, file_path, profile, active_profile)`, ...
- `src/tet4d/engine/runtime/leaderboard.py`: `leaderboard_payload(*, path=...)`, `leaderboard_top_entries(*, limit=..., path=...)`, `leaderboard_entry_rank(*, dimension, score, lines_cleared, ...)`, `leaderboard_entry_would_enter(*, dimension, score, lines_cleared, ...)`, `record_leaderboard_entry(*, dimension, score, lines_cleared, ...)`
- `src/tet4d/engine/runtime/menu_config.py`: `default_settings_payload()`, `explorer_default_board_dims(dimension)`, `authored_menu_graph()`, `menu_graph()`, `launcher_menu_id()`, `pause_menu_id()`, `settings_menu_id()`, `keybindings_menu_id()`, `authored_menu_definition(menu_id)`, `authored_menu_items(menu_id)`, `runtime_menu_id_for_item(item_id)`, `resolve_runtime_menu_id(menu_id, *, item_id=..., fallback_menu_id=...)`, ...
- `src/tet4d/engine/runtime/menu_field_spec.py`: `FieldOption`, `FieldSpec`
- `src/tet4d/engine/runtime/menu_runtime_graph.py`: `MenuCompileResult`, `detect_redundant_single_option_menus(menus, *, source_label)`, `compile_runtime_menu_graph(authored_menus, *, authored_entrypoints)`, `validate_runtime_menu_graph(runtime_menus, *, runtime_entrypoints)`
- `src/tet4d/engine/runtime/menu_settings/sections.py`: `clamp_kick_level_index(value, *, default=...)`, `normalize_mode_key(mode_key)`, `normalize_rotation_animation_mode(value, *, default=...)`, `coerce_shared_gameplay_settings(raw, *, defaults=...)`, `display_settings_for_payload(payload, *, default_payload, defaults)`, `audio_settings_for_payload(payload, *, default_payload)`, `analytics_settings_for_payload(payload, *, default_payload)`, `global_game_seed_from_payload(payload, *, default)`, `mode_shared_gameplay_settings_from_payload(payload, *, mode_key, defaults)`
- `src/tet4d/engine/runtime/menu_settings/store.py`: `normalize_active_profile_name(raw, *, default)`, `settings_mapping(payload)`, `mode_settings_mapping(settings, mode_key)`, `iter_all_mode_settings(payload)`, `mode_settings_view(settings, mode_key)`, `default_settings_payload_for_runtime(base_default_payload, *, defaults)`, `load_payload(state_file, *, base_default_payload, defaults)`, `save_payload(state_file, payload)`, `sanitize_and_save_payload(state_file, payload, *, base_default_payload, ...)`, `save_payload_section(state_file, section_name, updates, ...)`, `apply_mode_settings_to_state(state, mode_settings)`
- `src/tet4d/engine/runtime/menu_settings_state.py`: `apply_saved_menu_settings(state, dimension, include_profile=...)`, `save_menu_settings(state, dimension)`, `load_menu_settings(state, dimension, include_profile=...)`, `reset_menu_settings_to_defaults(state, dimension)`, `load_app_settings_payload()`, `save_app_settings_payload(payload)`, `get_display_settings()`, `default_display_settings()`, `get_overlay_transparency()`, `get_analytics_settings()`, `default_analytics_settings()`, `save_display_settings(*, fullscreen=..., windowed_size=..., ...)`, ...
- `src/tet4d/engine/runtime/menu_structure/graph.py`: `collect_reachable_menu_ids(menus, *, start_menu_id)`, `collect_actions_for_menu_ids(menus, *, menu_ids)`, `collect_route_ids_for_menu_ids(menus, *, menu_ids)`
- `src/tet4d/engine/runtime/menu_structure/menu_parse.py`: `parse_menu_item(raw, *, path)`, `parse_menus(raw)`, `parse_menu_entrypoints(payload, *, menus)`, `parse_launcher_subtitles(payload)`, `parse_launcher_route_actions(payload)`, `parse_branding(payload)`
- `src/tet4d/engine/runtime/menu_structure/parse_helpers.py`: `parse_string_list(raw, *, path)`, `parse_mode_string_lists(raw_obj, *, base_path)`, `parse_copy_fields(raw, *, base_path, string_fields, list_fields=...)`, `parse_ui_copy(payload)`
- `src/tet4d/engine/runtime/menu_structure/policy.py`: `validate_launcher_route_actions(*, launcher_route_actions, launcher_route_ids, ...)`, `enforce_menu_entrypoint_parity(validated)`, `enforce_settings_split_policy(validated)`
- `src/tet4d/engine/runtime/menu_structure/settings_parse.py`: `parse_pause_copy(payload)`, `parse_setup_fields(payload)`, `parse_setup_hints(payload)`, `parse_settings_option_labels(payload)`, `parse_settings_category_docs(payload)`, `parse_settings_split_rules(payload)`, `parse_settings_category_metrics(payload, docs)`, `resolve_field_max(raw_max, piece_set_max, topology_profile_max, ...)`
- `src/tet4d/engine/runtime/menu_structure_schema.py`: `validate_structure_payload(payload)`
- `src/tet4d/engine/runtime/project_config.py`: `io_paths_payload()`, `constants_payload()`, `ui_theme_payload()`, `project_root_path()`, `state_dir_relative()`, `state_dir_path(*, root_dir=...)`, `sanitize_state_relative_path(raw, *, default_relative)`, `resolve_state_relative_path(raw, *, default_relative, root_dir=...)`, `menu_settings_file_relative()`, `menu_settings_file_path(*, root_dir=...)`, `keybindings_dir_relative()`, `keybindings_dir_path()`, ...
- `src/tet4d/engine/runtime/runtime_config.py`: `gameplay_tuning_payload()`, `speed_curve_for_dimension(dimension)`, `challenge_prefill_ratio(dimension)`, `assist_bot_factor(mode_name)`, `assist_grid_factor(mode_name)`, `kick_level_names()`, `kick_default_level()`, `normalize_kick_level_name(level_name)`, `kick_level_index_from_id(level_name)`, `assist_kick_factor(level_name)`, `rotation_kick_candidate_offsets(level_name)`, `assist_speed_formula()`, ...
- `src/tet4d/engine/runtime/runtime_config_validation_gameplay.py`: `validate_audio_sfx_payload(payload)`, `validate_gameplay_tuning_payload(payload)`
- `src/tet4d/engine/runtime/runtime_config_validation_playbot.py`: `validate_playbot_policy_payload(payload)`
- `src/tet4d/engine/runtime/score_analysis/store.py`: `default_config(config_path)`, `load_json_object_or_default(path, default)`, `atomic_write_summary_json(path, payload)`, `append_json_line(path, payload)`, `load_summary(path, *, new_summary_fn, validate_summary_fn)`
- `src/tet4d/engine/runtime/score_analysis/validate.py`: `validate_score_analysis_event(event)`, `validate_score_analysis_summary(summary)`
- `src/tet4d/engine/runtime/score_analyzer.py`: `new_analysis_session_id()`, `reload_score_analyzer_config()`, `reset_score_analyzer_runtime_state()`, `set_score_analyzer_logging_enabled(enabled)`, `score_analyzer_logging_enabled()`, `analyze_lock_event(*, board_pre, board_post, dims, gravity_axis, ...)`, `score_analysis_summary_snapshot()`, `record_score_analysis_event(event)`, `hud_analysis_lines(event)`
- `src/tet4d/engine/runtime/score_analyzer_features.py`: `board_health_features(cells_map, *, dims, gravity_axis, near_threshold=..., ...)`, `placement_features(*, board_pre, board_post, board_pre_features, ...)`, `weighted_score(features, score_obj)`
- `src/tet4d/engine/runtime/settings_sanitize.py`: `ensure_default_settings_payload(payload, *, defaults)`, `merge_loaded_payload(payload, loaded)`, `sanitize_payload(payload, *, default_payload, defaults)`, `display_settings_from_payload(payload, *, default_payload, defaults)`, `audio_settings_from_payload(payload, *, default_payload)`, `analytics_settings_from_payload(payload, *, default_payload)`
- `src/tet4d/engine/runtime/settings_schema.py`: `RuntimeSettingDefaults`, `as_non_empty_string(value, *, path)`, `require_object(value, *, path)`, `require_list(value, *, path)`, `require_bool(value, *, path)`, `require_int(value, *, path, min_value=..., max_value=...)`, `require_number(value, *, path, min_value=..., max_value=...)`, `validate_setting_storage_metadata(parsed, *, semantic_type, item_type, path)`, `string_tuple(raw_values, *, path, normalize_lower=...)`, `mode_key_for_dimension(dimension)`, `clamp_overlay_transparency(value, *, default=...)`, `clamp_game_seed(value, *, default=...)`, ...
- `src/tet4d/engine/runtime/topology_cache.py`: `topology_cache_key(profile, *, dims)`, `topology_cache_dir_path(*, root_dir=...)`, `topology_cache_file_path(profile, *, dims, root_dir=...)`, `read_topology_cache_entry(profile, *, dims, cache_version=..., root_dir=...)`, `write_topology_cache_entry(profile, *, dims, entry, cache_version=..., ...)`, `merge_topology_cache_entry(profile, *, dims, cache_version=..., root_dir=..., ...)`, `read_cached_graph_rows(profile, *, dims, cache_version=..., root_dir=...)`, `write_cached_graph_rows(profile, *, dims, graph_rows, cache_version=..., ...)`, `read_cached_playability_analysis(profile, *, dims, root_dir=...)`, `write_cached_playability_analysis(profile, *, dims, analysis, root_dir=...)`, `topology_cache_usage(*, root_dir=...)`, `clear_topology_cache(*, root_dir=...)`
- `src/tet4d/engine/runtime/topology_explorer_audit.py`: `ExplorerInteractionAuditEvent`, `ExplorerInteractionAuditSpan`, `ExplorerInteractionAudit`, `current_audit_action(state)`, `record_interaction_handler(state, action, **metadata)`, `record_interaction_phase(state, phase, *, action=..., **metadata)`, `record_active_interaction_phase(phase, **metadata)`, `latest_span_for_phase(state, *, action, phase)`
- `src/tet4d/engine/runtime/topology_explorer_bridge.py`: `explorer_profile_from_legacy_profile(profile)`, `explorer_profile_from_edge_rules(*, dimension, topology_mode, edge_rules)`, `export_explorer_preview_from_legacy_profile(profile, *, dims, source)`
- `src/tet4d/engine/runtime/topology_explorer_experiments.py`: `compile_parallel_explorer_experiments(current_profile, *, dims, source=...)`, `export_parallel_explorer_experiments(current_profile, *, dims, source=..., root_dir=..., ...)`
- `src/tet4d/engine/runtime/topology_explorer_preview.py`: `preview_dims_for_dimension(dimension)`, `recommended_explorer_probe_coord(profile, *, dims)`, `explorer_probe_options(profile, *, dims, coord, frame_permutation=..., ...)`, `advance_explorer_probe(profile, *, dims, coord, step_label, ...)`, `basis_arrow_payload(profile)`, `compile_explorer_topology_preview(profile, *, dims, source=..., root_dir=..., ...)`, `export_explorer_topology_preview(profile, *, dims, source=..., root_dir=..., ...)`
- `src/tet4d/engine/runtime/topology_explorer_runtime.py`: `resolve_direct_explorer_launch_profile(*, dimension, gravity_axis, topology_mode, ...)`, `load_runtime_explorer_topology_profile(dimension)`, `export_stored_explorer_topology_preview(dimension, *, source=...)`, `compile_runtime_explorer_experiments(profile, *, dims, source=...)`, `export_runtime_explorer_experiments(profile, *, dims, source=..., batch_payload=...)`
- `src/tet4d/engine/runtime/topology_explorer_store.py`: `load_explorer_topology_profiles_payload(root_dir=...)`, `load_explorer_topology_profile(dimension, *, root_dir=...)`, `save_explorer_topology_profile(profile, *, root_dir=...)`
- `src/tet4d/engine/runtime/topology_playability_signal.py`: `derive_topology_playability_analysis(state, *, preview=..., preview_error=..., ...)`, `topology_is_rigid_playable(profile, *, dims, resolver=...)`, `resolve_rigid_play_enabled(profile, *, dims, rigid_play_mode=..., analysis=..., ...)`, `update_topology_playability_analysis(state, *, preview=..., preview_error=..., ...)`
- `src/tet4d/engine/runtime/topology_playground_launch.py`: `build_gameplay_config_from_topology_playground_state(state, exploration_mode=...)`
- `src/tet4d/engine/runtime/topology_playground_sandbox.py`: `SandboxShape`, `SandboxMoveOutcome`, `sandbox_shapes_for_state(state)`, `ensure_piece_sandbox_state(state)`, `sandbox_shape(state)`, `spawn_sandbox_piece(state)`, `sandbox_cells(state)`, `rotate_blocks_for_action(dimension, blocks, *, action)`, `sandbox_validity(state)`, `rotate_sandbox_piece_action(state, action)`, `move_sandbox_piece(state, step_label)`, `rotate_sandbox_piece(state)`, ...
- `src/tet4d/engine/runtime/topology_playground_state.py`: `TopologyPlaygroundLaunchSettings`, `TopologyPlaygroundGluingDraft`, `TopologyPlaygroundTopologyConfig`, `TopologyPlaygroundProbeState`, `TopologyPlaygroundSandboxPieceState`, `TopologyPlaygroundGravityMode`, `TopologyPlaygroundTransportPolicy`, `TopologyPlaygroundMovementSummary`, `TopologyPlaygroundPlayabilityAnalysis`, `TopologyPlaygroundPresetSelection`, `TopologyPlaygroundPresetMetadata`, `TopologyPlaygroundCanonicalOwnershipState`, ...
- `src/tet4d/engine/runtime/topology_profile_store.py`: `load_topology_profiles_payload(root_dir=...)`, `load_topology_profile(gameplay_mode, dimension, *, root_dir=...)`, `save_topology_profile(profile, *, root_dir=...)`, `topology_profile_note(gameplay_mode)`
- `src/tet4d/engine/topology_explorer/glue_map.py`: `BoundaryTraversal`, `map_boundary_exit(profile, *, dims, coord, step)`, `move_cell(profile, *, dims, coord, step)`
- `src/tet4d/engine/topology_explorer/glue_model.py`: `normalize_dimension(dimension)`, `axis_name(axis)`, `normalize_side(side)`, `BoundaryRef`, `boundary_label(boundary)`, `tangent_axes_for_boundary(boundary)`, `BoundaryTransform`, `GluingDescriptor`, `ExplorerTopologyProfile`, `MoveStep`, `movement_steps_for_dimension(dimension)`, `coord_in_bounds(coord, dims)`
- `src/tet4d/engine/topology_explorer/glue_validate.py`: `validate_topology_structure(profile)`, `validate_topology_bijection(profile, *, dims)`, `validate_explorer_topology_profile(profile, *, dims)`
- `src/tet4d/engine/topology_explorer/movement_graph.py`: `MovementEdge`, `movement_graph_rows(profile, *, dims)`, `movement_graph_from_rows(rows)`, `serialize_movement_graph_rows(rows)`, `deserialize_movement_graph_rows(payload, *, dimension)`, `neighbors_for_cell(profile, *, dims, coord)`, `build_movement_graph(profile, *, dims)`
- `src/tet4d/engine/topology_explorer/presets.py`: `pair_boundaries(*, dimension, source_axis, source_side, target_axis, ...)`, `axis_wrap_profile(*, dimension, wrapped_axes)`, `torus_profile_2d()`, `cylinder_profile_2d()`, `mobius_strip_profile_2d()`, `klein_bottle_profile_2d()`, `projective_plane_profile_2d()`, `sphere_profile_2d()`, `ExplorerTopologyPreset`, `ExplorerTopologyPresetSection`, `full_wrap_profile_3d()`, `twisted_y_profile_3d()`, ...
- `src/tet4d/engine/topology_explorer/transport_resolver.py`: `ExplorerTransportFrameTransform`, `DirectedBoundarySeam`, `CellStepResult`, `PieceStepResult`, `ExplorerTransportResolver`, `build_explorer_transport_resolver(profile, dims)`
- `src/tet4d/engine/tutorial/api.py`: `tutorial_lessons_payload_runtime()`, `tutorial_plan_payload_runtime()`, `tutorial_lesson_ids_runtime()`, `tutorial_board_dims_runtime(mode)`, `tutorial_runtime_create_session_runtime(*, lesson_id, mode)`, `tutorial_runtime_action_allowed_runtime(session, action_id)`, `tutorial_runtime_is_running_runtime(session)`, `tutorial_runtime_observe_action_runtime(session, action_id)`, `tutorial_runtime_sync_and_advance_runtime(session, *, lines_cleared, overlay_transparency=..., ...)`, `tutorial_runtime_overlay_payload_runtime(session)`, `tutorial_runtime_required_action_runtime(session)`, `tutorial_runtime_allowed_actions_runtime(session)`, ...
- `src/tet4d/engine/tutorial/conditions.py`: `evaluate_completion(condition, *, events_seen, predicate_values=..., ...)`
- `src/tet4d/engine/tutorial/content.py`: `tutorial_lessons_file_path()`, `tutorial_plan_file_path()`, `load_tutorial_payload()`, `load_tutorial_plan_payload()`, `tutorial_payload_dict()`, `tutorial_plan_payload_dict()`, `tutorial_lesson_map()`, `tutorial_lesson_ids()`, `tutorial_board_dims_for_mode(mode)`, `clear_tutorial_content_cache()`
- `src/tet4d/engine/tutorial/events.py`: `TutorialEvent`, `sanitize_event_name(name)`, `build_event(*, sequence, name, payload=...)`
- `src/tet4d/engine/tutorial/gating.py`: `sanitize_action_id(action_id)`, `TutorialInputGate`, `gate_for_step(step)`
- `src/tet4d/engine/tutorial/manager.py`: `TutorialSnapshot`, `TutorialManager(lessons)`
- `src/tet4d/engine/tutorial/persistence.py`: `load_tutorial_progress()`, `save_tutorial_progress(payload)`, `mark_tutorial_lesson_started(lesson_id)`, `mark_tutorial_lesson_completed(lesson_id)`
- `src/tet4d/engine/tutorial/runtime.py`: `TutorialRuntimeSession`, `create_tutorial_runtime_session(*, lesson_id, mode)`, `tutorial_progress_snapshot()`
- `src/tet4d/engine/tutorial/schema.py`: `TutorialStepUI`, `TutorialStepGating`, `TutorialStepSetup`, `TutorialCompletionCondition`, `TutorialStep`, `TutorialLesson`, `TutorialBoardProfiles`, `TutorialPayload`, `parse_tutorial_payload(payload)`, `build_tutorial_lesson_map(payload)`, `tutorial_payload_to_dict(payload)`
- `src/tet4d/engine/tutorial/setup_apply.py`: `apply_tutorial_step_setup_2d(state, cfg, setup, *, lesson_id, step_id)`, `apply_tutorial_step_setup_nd(state, cfg, setup, *, lesson_id, step_id)`, `ensure_tutorial_piece_visibility_2d(state, cfg, *, min_visible_layer=...)`, `ensure_tutorial_piece_visibility_nd(state, cfg, *, min_visible_layer=...)`
- `src/tet4d/engine/ui_logic/keybindings_catalog.py`: `keybinding_catalog_payload()`, `binding_scope_order()`, `binding_scope_menu_sections()`, `binding_group_docs()`, `binding_group_label(group)`, `binding_group_description(group)`, `binding_action_ids()`, `binding_action_contracts()`, `binding_action_description(action)`, `binding_reference_runtime_order()`, `binding_reference_live_order()`, `binding_reference_group_heading(group)`, ...
- `src/tet4d/engine/ui_logic/menu_graph_linter.py`: `MenuGraphIssue`, `lint_menu_graph()`
- `src/tet4d/engine/ui_logic/menu_layout.py`: `LayoutRect`, `MenuLayoutZones`, `compute_menu_layout_zones(*, width, height, outer_pad, header_height, ...)`
- `src/tet4d/engine/ui_logic/view_modes.py`: `GridMode`, `ShadowMode`, `cycle_grid_mode(mode)`, `grid_mode_label(mode)`, `shadow_mode_label(mode)`
- `src/tet4d/replay/__init__.py`: `play_replay_2d(script)`, `play_replay_nd_ticks(script)`, `record_replay_2d(*, config, seed, actions)`, `record_replay_nd_ticks(*, config, seed, ticks)`
- `src/tet4d/replay/format.py`: `ReplayFormatError`, `ReplayEvent2D`, `ReplayScript2D`, `ReplayTickScriptND`
- `src/tet4d/shared/nd_coords.py`: `coord_from_column(column, lateral_axes, gravity_axis, gravity_value, ...)`
- `src/tet4d/ui/pygame/__init__.py`: `run_2d()`, `run_3d()`, `run_4d()`
- `src/tet4d/ui/pygame/endgame_animation.py`: `EndgamePresetConfig`, `EndgameAnimationTuning`, `load_endgame_animation_tuning()`, `EndgameRenderContext`, `SnapshotCell`, `EndgameSnapshot`, `EndgameCellSplit`, `ShellFragment`, `EndgameShellArtifact`, `EndgameGridBreakMark`, `EndgameShatterState`, `EndgameAnimationState`, ...
- `src/tet4d/ui/pygame/endgame_shell_effects.py`: `EndgameBoundaryImpact`, `EndgameShellTimeline`, `EndgameEscapeEvent`, `EndgameBoardShard`, `EndgameImpactDrawState`, `EndgameShardDrawState`, `EscapeProxyState`, `EscapeStreakState`, `ImpactFlashState`, `ResidueCrackState`, `EscapeEventFrame`, `EndgameShellSoundEvent`, ...
- `src/tet4d/ui/pygame/front2d_game.py`: `run()`, `main(argv=...)`
- `src/tet4d/ui/pygame/front2d_input.py`: `system_decision_for_key(key)`, `gameplay_action_for_key_2d(state, key)`, `overlay_action_for_key_2d(key)`, `apply_2d_gameplay_action(state, action)`, `dispatch_2d_gameplay_action(state, key)`, `handle_game_keydown(event, state, _cfg, *, allow_gameplay=..., ...)`
- `src/tet4d/ui/pygame/front2d_loop.py`: `run_game_loop(screen, cfg, fonts, display_settings, ...)`
- `src/tet4d/ui/pygame/front2d_session.py`: `create_initial_state(cfg)`, `LoopContext2D`
- `src/tet4d/ui/pygame/front2d_setup.py`: `GameSettings`, `MenuState`, `menu_fields(settings)`, `piece_set_index_to_id(index)`, `random_mode_index_to_id(index)`, `load_speedup_settings_for_mode(mode_key)`, `load_animation_settings_for_mode(mode_key)`, `kick_level_name(index)`, `load_overlay_transparency_for_runtime_2d()`, `menu_value_formatter(field, value)`, `config_from_settings(settings, *, explorer_topology_profile_override=...)`, `build_play_menu_config(settings)`, ...
- `src/tet4d/ui/pygame/front2d_tutorial.py`: `tutorial_create_session_2d(*, lesson_id)`, `tutorial_board_dims_2d()`, `tutorial_action_allowed(loop, action_id)`, `tutorial_observe_action(loop, action_id)`, `enforce_tutorial_runtime_safety_2d(loop)`, `apply_pending_tutorial_setup(loop)`, `handle_tutorial_hotkey(loop, key)`, `handle_overlay_hotkey(loop, key)`, `open_help_screen(screen, fonts, loop)`, `restart_tutorial_if_running_2d(loop)`, `pause_tutorial_restart_2d(loop)`, `pause_tutorial_skip_2d(loop)`, ...
- `src/tet4d/ui/pygame/front3d_game.py`: `handle_camera_key(key, camera, *, on_overlay_alpha_dec=..., ...)`, `handle_game_keydown(event, state, camera=..., _cfg=..., ...)`, `LoopContext3D`, `run_game_loop(screen, cfg, fonts, *, bot_mode=..., ...)`, `run()`
- `src/tet4d/ui/pygame/front3d_render.py`: `BoardPresentation3D`, `init_fonts()`, `ProjectionMode3D`, `projection_label(mode)`, `ClearAnimation3D`, `Camera3D`, `color_for_cell_3d(cell_id)`, `draw_game_frame(screen, state, camera, fonts, grid_mode, ...)`, `suggested_window_size(cfg)`
- `src/tet4d/ui/pygame/front4d_game.py`: `LoopContext4D`, `run_game_loop(screen, cfg, fonts, *, bot_mode=..., ...)`, `suggested_window_size(cfg)`, `run()`
- `src/tet4d/ui/pygame/front4d_render.py`: `LayerPresentation4D`, `LayerView3D`, `ClearAnimation4D`, `RenderBasis4D`, `FrozenAnimationPresentation4D`, `movement_axis_overrides_for_view(view, dims4)`, `viewer_axes_for_view(view, dims4)`, `draw_game_frame(screen, state, view, fonts, grid_mode, ...)`, `handle_view_key(key, view, *, on_overlay_alpha_dec=..., ...)`, `spawn_clear_animation_if_needed(state, last_lines_cleared)`
- `src/tet4d/ui/pygame/frontend_nd_input.py`: `system_key_action(key)`, `gameplay_action_for_key(key, cfg)`, `apply_nd_gameplay_action(state, action)`, `can_apply_nd_gameplay_action_with_view(state, action, *, yaw_deg_for_view_movement=..., ...)`, `apply_nd_gameplay_action_with_view(state, action, *, yaw_deg_for_view_movement=..., ...)`, `route_nd_keydown(key, state, *, yaw_deg_for_view_movement=..., ...)`, `handle_game_keydown(event, state)`
- `src/tet4d/ui/pygame/frontend_nd_setup.py`: `init_fonts()`, `draw_gradient_background(surface, top_color, bottom_color)`, `GameSettingsND`, `MenuState`, `menu_fields_for_settings(settings, dimension)`, `draw_menu(screen, fonts, state, dimension, *, menu_fields=...)`, `run_menu(screen, fonts, dimension)`, `build_config(settings, dimension, ...)`, `build_play_menu_config(settings, dimension)`, `gravity_interval_ms_from_config(cfg)`, `piece_set_4d_label(piece_set_id)`
- `src/tet4d/ui/pygame/frontend_nd_state.py`: `create_initial_state(cfg)`
- `src/tet4d/ui/pygame/input/camera_mouse.py`: `MouseOrbitState`, `clamp_pitch_deg(pitch_deg, *, max_abs_pitch=...)`, `mouse_wheel_delta(event)`, `apply_mouse_orbit_event(event, state, *, yaw_deg, pitch_deg)`
- `src/tet4d/ui/pygame/input/key_dispatch.py`: `match_bound_action(key, bindings, ordered_actions)`, `dispatch_bound_action(key, bindings, handlers)`
- `src/tet4d/ui/pygame/input/key_display.py`: `display_key_name(key)`, `format_key_tuple(keys)`
- `src/tet4d/ui/pygame/input/view_controls.py`: `YawPitchTurnAnimator`, `viewer_relative_move_axis_delta(yaw_deg, intent)`, `wrapped_pitch_target(yaw_deg, pitch_deg, delta_deg, *, max_abs_pitch=...)`
- `src/tet4d/ui/pygame/keybindings.py`: `default_game_bindings_for_profile(profile)`, `default_camera_bindings_for_profile(profile)`, `default_explorer_bindings_for_profile(profile)`, `default_system_bindings_for_profile(profile)`, `active_key_profile()`, `profile_keybinding_file_path(dimension, profile)`, `keybinding_file_path_for_profile(dimension, profile=...)`, `key_matches(bindings, action, key)`, `reset_keybindings_to_profile_defaults(profile=...)`, `runtime_binding_groups_for_dimension(dimension)`, `binding_actions_for_dimension(dimension)`, `rebind_action_key(dimension, group, action, key, *, conflict_mode=...)`, ...
- `src/tet4d/ui/pygame/launch/bot_options_menu.py`: `run_bot_options_menu(screen, fonts, *, start_dimension)`
- `src/tet4d/ui/pygame/launch/launcher_menu_view.py`: `draw_main_menu(screen, fonts, *, menu_title, items, ...)`
- `src/tet4d/ui/pygame/launch/launcher_nd_runner.py`: `run_nd_mode_launcher(*, display_settings, fonts, setup_caption, ...)`
- `src/tet4d/ui/pygame/launch/launcher_play.py`: `setup_caption_for_dimension(dimension)`, `game_caption_for_dimension(dimension)`, `LaunchResult`, `launch_2d(screen, fonts_2d, display_settings, ...)`, `launch_3d(screen, fonts_nd, display_settings, ...)`, `launch_4d(screen, fonts_nd, display_settings, ...)`
- `src/tet4d/ui/pygame/launch/launcher_profile_menu.py`: `profile_action_id(profile)`, `profile_label(profile)`, `expand_settings_profile_rows(items)`, `is_profile_prev_key(key)`, `is_profile_next_key(key)`
- `src/tet4d/ui/pygame/launch/launcher_runtime_helpers.py`: `handle_launcher_route(route_id, *, route_actions, state, action_registry)`, `handle_missing_action(action_id, *, state)`, `play_move_sfx()`, `play_confirm_sfx()`, `handle_launcher_profile_cycle_key(menu_id, key, *, menu_ids, state, ...)`
- `src/tet4d/ui/pygame/launch/launcher_settings.py`: `run_settings_hub_menu(screen, fonts, *, audio_settings, display_settings, ...)`
- `src/tet4d/ui/pygame/launch/leaderboard_menu.py`: `run_leaderboard_menu(screen, fonts)`, `prompt_leaderboard_player_name(screen, fonts, *, rank, draw_background=..., ...)`, `maybe_record_leaderboard_session(screen, fonts, *, dimension, score, ...)`
- `src/tet4d/ui/pygame/launch/settings_hub_model.py`: `SettingsHubResult`, `settings_page_items(page_id)`, `selectable_indexes_for_items(items)`, `selectable_index_by_item_id_for_items(items)`, `settings_title_for_page(page_id)`, `current_settings_page_id(state)`, `current_settings_page_items(state)`, `current_page_selectable_indexes(state)`, `rotation_animation_mode_label(value)`, `build_unified_settings_state(*, audio_settings, display_settings, ...)`
- `src/tet4d/ui/pygame/launch/topology_lab_menu.py`: `run_explorer_playground(screen, fonts, *, launch=..., dimension=..., ...)`
- `src/tet4d/ui/pygame/locked_cell_explosion/audio.py`: `aggregate_audio_events(raw_events, *, elapsed_ms, sound_enabled, state)`
- `src/tet4d/ui/pygame/locked_cell_explosion/board_view.py`: `draw_native_board_view(surface, *, rect, fonts, controller, ...)`
- `src/tet4d/ui/pygame/locked_cell_explosion/controller.py`: `LockedCellExplosionController`, `build_locked_cell_explosion(config)`
- `src/tet4d/ui/pygame/locked_cell_explosion/defaults_store.py`: `clamp_endgame_live_cell_fraction(value)`, `ExplosionDefaults`, `default_explosion_defaults()`, `coerce_explosion_defaults(raw, *, defaults=...)`, `serialize_explosion_defaults(defaults)`, `mode_explosion_defaults(mode_key)`, `save_mode_explosion_defaults(mode_key, defaults)`
- `src/tet4d/ui/pygame/locked_cell_explosion/endgame_preview.py`: `PreviewSourceCell`, `ShellPreviewEscapingCellState`, `EndgamePreviewCache`, `EndgamePreviewFrame`, `default_shell_preview_time_scale(tuning=...)`, `shell_preview_phase_for_elapsed(elapsed_ms, tuning=...)`, `shell_preview_timeline_progress(elapsed_ms, *, phase, tuning=...)`, `scaled_shell_preview_elapsed(state, dt_ms, tuning=...)`, `preview_source_cell_map(cache)`, `reset_shell_preview_state(state)`, `advance_shell_preview_elapsed(state, dt_ms)`, `ensure_shell_preview_cache(state, *, source_cells, board_dims)`, ...
- `src/tet4d/ui/pygame/locked_cell_explosion/model.py`: `normalize_boundary_response(value, *, default=...)`, `normalize_particle_collisions(value, *, default=...)`, `normalize_mass_mode(value, *, default=...)`, `normalize_diagnostics_mode(value, *, default=...)`, `normalize_speed_preset(value, *, default=...)`, `speed_scale_for_preset(value, *, default=...)`, `clamp_trace_retention_ms(value)`, `clamp_mass_value(value)`, `normalize_mass_range(min_value, max_value)`, `clamp_collision_elasticity(value)`, `trail_sample_budget_for_lifetime_ms(value)`, `ExplosionSeedCell`, ...
- `src/tet4d/ui/pygame/locked_cell_explosion/render.py`: `project_particle_for_render(particle, *, dimension, board_dims, render_context)`, `render_particles(particles, *, dimension, board_dims, render_context)`
- `src/tet4d/ui/pygame/locked_cell_explosion/simulation.py`: `total_kinetic_energy_for_particles(particles)`, `velocity_norm_sq_sum_for_particles(particles, *, weighted_by_mass=...)`, `kinetic_energy_formula_text_for_particles(particles, *, max_terms=...)`, `weighted_speed_sq_sum_text_for_particles(particles)`, `assign_particle_masses(particles, *, random_seed, mass_mode, base_mass, ...)`, `build_simulation(config)`, `step_simulation(state, *, adapter, dt_ms, time_scale)`, `build_endgame_state(*, locked_cells, board_shape, dimension, ...)`, `step_endgame_state(state, *, dt_ms, topology=..., time_scale=...)`
- `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`: `StandaloneExplosionSurfaceState`, `build_standalone_explosion_surface_state(*, dimension=...)`, `launcher_row_keys()`, `save_standalone_explosion_defaults(state)`, `build_standalone_explosion_config(state)`, `build_explorer_explosion_surface_state(*, dimension, board_dims, explorer_profile, ...)`, `restart_standalone_explosion(state)`, `run_standalone_explosion_launcher(screen, fonts, *, initial_state=...)`, `run_standalone_explosion_launcher_action(state, session, fonts, *, persist_session_status)`
- `src/tet4d/ui/pygame/locked_cell_explosion/topology.py`: `ExplosionSeam`, `ExplosionTopologyAdapter`, `build_explosion_topology_adapter(topology)`
- `src/tet4d/ui/pygame/menu/keybindings_menu.py`: `KeybindingsMenuState`, `run_keybindings_menu(screen, fonts, dimension=..., *, scope=...)`
- `src/tet4d/ui/pygame/menu/keybindings_menu_input.py`: `process_menu_events(state, binding_rows, *, run_menu_action, ...)`
- `src/tet4d/ui/pygame/menu/keybindings_menu_model.py`: `BindingRow`, `RenderedRow`, `scope_label(scope)`, `scope_dimensions(scope)`, `scope_from_dimension(dimension)`, `rows_for_scope(scope)`, `binding_title(row, scope)`, `binding_keys(row)`, `scope_file_hint(scope)`, `resolve_initial_scope(dimension, scope)`, `scope_description(scope)`
- `src/tet4d/ui/pygame/menu/keybindings_menu_view.py`: `draw_section_menu(surface, fonts, state, *, section_menu, ...)`, `draw_binding_menu(surface, fonts, state, *, rendered_rows, ...)`
- `src/tet4d/ui/pygame/menu/menu_controls.py`: `RebindCapture`, `NumericTextAppend`, `MenuAction`, `gather_menu_actions(state=..., _dimension=...)`, `apply_menu_actions(state, actions, fields, dimension, ...)`
- `src/tet4d/ui/pygame/menu/menu_keybinding_shortcuts.py`: `menu_binding_action_for_key(key, load_action, save_action)`, `apply_menu_binding_action(action, load_action, save_action, dimension, state)`, `menu_binding_status_color(is_error)`
- `src/tet4d/ui/pygame/menu/menu_navigation_keys.py`: `normalize_menu_navigation_key(key)`
- `src/tet4d/ui/pygame/menu/menu_runner.py`: `ActionRegistry()`, `MenuPointerTarget`, `MenuRunner(*, menus, start_menu_id, action_registry, ...)`
- `src/tet4d/ui/pygame/menu/numeric_text_input.py`: `numeric_digits_only(text, *, max_length, sanitize_text)`, `append_numeric_text(*, current_buffer, incoming_text, replace_on_type, ...)`, `parse_numeric_text(text, *, max_length, sanitize_text)`
- `src/tet4d/ui/pygame/menu/setup_menu_runner.py`: `run_setup_menu_loop(*, screen, state, dimension, fields_for_state, ...)`
- `src/tet4d/ui/pygame/projection3d.py`: `ProjectedLinePrimitive`, `ProjectedLineFragment`, `ProjectedFacePrimitive`, `shade_color(color, factor)`, `color_for_cell(cell_id, color_map, default=...)`, `draw_gradient_background(surface, top_color, bottom_color)`, `raw_to_world(raw, dims)`, `transform_point(world, yaw_deg, pitch_deg)`, `normalize_angle_deg(angle_deg)`, `shortest_angle_delta_deg(start_deg, target_deg)`, `smoothstep01(t)`, `interpolate_angle_deg(start_deg, target_deg, t)`, ...
- `src/tet4d/ui/pygame/render/active_piece_projection_guides.py`: `BoundaryProjectionSegment2D`, `projection_guide_enabled(grid_mode)`, `boundary_targets_for_mode(*, dims, gravity_axis, grid_mode)`, `build_boundary_projection_segments_2d(*, cells, dims, gravity_axis, grid_mode, color)`, `draw_boundary_projection_segments_2d(surface, *, segments, board_offset, cell_size, ...)`, `build_boundary_projection_face_primitives(*, cells, dims, gravity_axis, grid_mode, ...)`, `draw_boundary_projection_faces(surface, *, faces, fill_alpha=..., outline_alpha=...)`
- `src/tet4d/ui/pygame/render/board_boundary.py`: `BoardBoundaryPlane`, `board_boundary_coordinate(*, dims, axis, side)`, `board_boundary_limits(dims)`, `board_boundary_planes(dims)`
- `src/tet4d/ui/pygame/render/control_helper.py`: `control_groups_for_dimension(dimension, *, include_exploration=..., ...)`, `draw_grouped_control_helper(surface, *, groups, rect, panel_font, hint_font)`
- `src/tet4d/ui/pygame/render/control_icons.py`: `action_icon_action(action)`, `draw_action_icon(surface, *, rect, action)`
- `src/tet4d/ui/pygame/render/font_profiles.py`: `GfxFonts`, `init_fonts(profile=...)`
- `src/tet4d/ui/pygame/render/front3d_cell_render.py`: `split_faces_for_cells(cells, *, build_faces_fn, color_for_cell_fn)`, `draw_sorted_faces(surface, faces)`, `draw_translucent_faces(surface, faces, *, fill_alpha, outline_alpha)`, `overlay_opacity_scale(overlay_transparency)`, `draw_cells(surface, *, cells, build_faces_fn, color_for_cell_fn, ...)`
- `src/tet4d/ui/pygame/render/front3d_projection_helpers.py`: `ProjectionParams3D`, `transform_raw_point(raw, dims, params)`, `project_point(trans, params, center_px)`, `project_raw_point(raw, dims, params, center_px)`, `depth_denominator_for_depth(depth, params)`, `draw_board_grid(surface, dims, params, board_rect, ...)`, `build_cell_faces(*, cell, color, params, center_px, ...)`, `build_cell_face_primitives(*, cell, color, params, center_px, ...)`, `fit_orthographic_zoom_for_rect(*, dims, yaw_deg, pitch_deg, rect, ...)`
- `src/tet4d/ui/pygame/render/gfx_game.py`: `color_for_cell(cell_id)`, `ClearEffect2D`, `init_fonts()`, `draw_gradient_background(surface, top_color, bottom_color)`, `draw_button_with_arrow(surface, center, size, direction, label, ...)`, `draw_menu(screen, fonts, settings, selected_index, ...)`, `compute_game_layout(screen, cfg)`, `draw_board(surface, state, board_offset, grid_mode=..., ...)`, `draw_side_panel(surface, state, panel_offset, fonts, grid_mode=..., ...)`, `gravity_interval_ms_from_config(cfg)`, `draw_game_frame(screen, cfg, state, fonts, grid_mode=..., ...)`
- `src/tet4d/ui/pygame/render/gfx_panel_2d.py`: `draw_side_panel_2d(surface, state, panel_offset, fonts, ...)`
- `src/tet4d/ui/pygame/render/grid_mode_render.py`: `build_projected_grid_primitives(*, dims, grid_mode, project_raw, transform_raw, ...)`, `draw_projected_line_buckets(*, surface, fragments, frame_color=..., ...)`, `draw_projected_grid_mode(*, surface, dims, grid_mode, draw_full_grid, ...)`
- `src/tet4d/ui/pygame/render/panel_utils.py`: `draw_game_over_banner(surface, *, rect, fonts, subtitle=...)`, `draw_unified_game_side_panel(surface, *, panel_rect, fonts, title, ...)`
- `src/tet4d/ui/pygame/render/projected_occlusion.py`: `SegmentOcclusionPolicy`, `OccludedSegmentBuckets`, `default_segment_occlusion_policy()`, `resolve_board_line_occlusion(board_segments, piece_faces, *, policy=...)`
- `src/tet4d/ui/pygame/render/text_render_cache.py`: `render_text_cached(*, font, text, color, antialias=...)`
- `src/tet4d/ui/pygame/render/w_movement_animation.py`: `layer_transition_scale_for_distance(layer_distance)`
- `src/tet4d/ui/pygame/runtime_ui/app_runtime.py`: `RuntimeSettings`, `DisplaySettings`, `normalize_display_settings(settings)`, `apply_display_mode(settings, *, preferred_windowed_size=...)`, `load_audio_settings_from_store()`, `load_display_settings_from_store()`, `initialize_runtime(*, sync_audio_state=...)`, `open_display(display_settings, *, caption=..., ...)`, `capture_windowed_display_settings(display_settings, *, min_width=..., min_height=...)`, `capture_windowed_display_settings_from_event(display_settings, *, event, min_width=..., ...)`
- `src/tet4d/ui/pygame/runtime_ui/audio.py`: `AudioSettings`, `AudioEngine()`, `initialize_audio(settings=...)`, `set_audio_settings(*, master_volume, sfx_volume, mute)`, `play_sfx(event_name)`
- `src/tet4d/ui/pygame/runtime_ui/help_menu.py`: `paginate_help_lines(lines, rows_per_page)`, `is_compact_help_view(*, width, height)`, `help_topic_action_rows(*, topic_id, dimension, include_all)`, `help_topic_action_lines(*, topic_id, dimension, include_all=...)`, `run_help_menu(screen, fonts, *, dimension=..., context_label=..., ...)`
- `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`: `process_game_events(keydown_handler, on_restart, on_toggle_grid, ...)`, `run_nd_loop(*, screen, fonts, loop, gravity_interval_from_config, ...)`
- `src/tet4d/ui/pygame/runtime_ui/panel_drag.py`: `helper_panel_rect_for_surface(*, surface_size, offset, side_panel, margin)`, `PanelDragMixin`
- `src/tet4d/ui/pygame/runtime_ui/pause_menu.py`: `run_pause_menu(screen, fonts, *, dimension, on_tutorial_restart=..., ...)`
- `src/tet4d/ui/pygame/runtime_ui/tutorial_loop_common.py`: `tutorial_action_delay_ms(action_id)`, `tutorial_overlay_start_from_setup(payload)`, `tutorial_gated_mouse_orbit_event(event, *, mouse_orbit, yaw_deg, pitch_deg, ...)`, `running_tutorial_session(loop, *, tutorial_is_running)`, `redo_tutorial_stage(loop, session, *, redo_stage, apply_pending_setup)`, `tutorial_required_action_blocked(session, *, required_action_runtime, ...)`, `tutorial_allowed_actions_blocked(session, *, allowed_actions_runtime, ...)`, `maintain_tutorial_runtime_safety(loop, *, min_visible_layer, running_tutorial_session, ...)`, `handle_tutorial_hotkey(*, key, session, previous_stage, next_stage, ...)`, `restart_loop_runtime_state(loop, *, create_initial_state, ...)`, `refresh_score_multiplier_state(loop, *, off_mode, combined_score_multiplier)`, `tutorial_sync(loop, *, lines_cleared, grid_mode_off, ...)`
- `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`: `tutorial_panel_last_rect(dimension)`, `draw_tutorial_overlay(screen, fonts, *, dimension, tutorial_session, ...)`
- `src/tet4d/ui/pygame/topology_lab/__main__.py`: `main()`
- `src/tet4d/ui/pygame/topology_lab/app.py`: `ExplorerPlaygroundLaunch`, `mode_settings_snapshot_for_dimension(dimension)`, `build_explorer_playground_settings(*, dimension, source_settings=...)`, `build_explorer_playground_launch(*, dimension, explorer_profile=..., ...)`, `build_explorer_playground_config(*, dimension, explorer_profile, ...)`
- `src/tet4d/ui/pygame/topology_lab/arrow_overlay.py`: `draw_glue_arrows(surface, fonts, *, cards_by_label, basis_arrows, ...)`
- `src/tet4d/ui/pygame/topology_lab/boundary_picker.py`: `pick_target(targets, pos)`, `update_hover_target(state, target)`, `apply_boundary_pick(state, boundary_index)`, `apply_boundary_edit_pick(state, boundary_index)`, `apply_glue_pick(state, glue_id)`
- `src/tet4d/ui/pygame/topology_lab/camera_controls.py`: `CameraAvailability`, `scene_camera_availability(dimension)`, `ensure_scene_camera(dimension, camera)`, `ensure_mouse_orbit_state(orbit)`, `handle_scene_camera_key(dimension, key, camera)`, `step_scene_camera(camera, dt_ms)`, `handle_scene_camera_mouse_event(dimension, event, camera, orbit)`
- `src/tet4d/ui/pygame/topology_lab/common.py`: `ExplorerGlueDraft`, `TopologyLabHitTarget`, `boundaries_for_dimension(dimension)`, `permutation_options_for_dimension(dimension)`, `default_draft_for_dimension(dimension)`, `axis_color(axis)`, `boundary_fill_color(boundary)`, `transform_preview_label(source, target, transform)`
- `src/tet4d/ui/pygame/topology_lab/controls_panel.py`: `compile_explorer_topology_preview(*args, **kwargs)`
- `src/tet4d/ui/pygame/topology_lab/controls_panel_commands.py`: `save_profile(state, *, save_explorer_topology_profile, ...)`, `run_export(state, *, export_explorer_topology_preview, ...)`, `run_experiments(state, *, compile_runtime_explorer_experiments, ...)`
- `src/tet4d/ui/pygame/topology_lab/controls_panel_launch.py`: `launch_play_preview(state, screen, fonts_nd, ...)`
- `src/tet4d/ui/pygame/topology_lab/controls_panel_routing.py`: `set_active_pane_from_target(state, target)`, `handle_navigation_key(state, nav_key, selectable, *, adjust_active_row, ...)`, `handle_shortcut_key(state, key, *, mod=..., apply_probe_step, ...)`, `handle_enter_key(state, selectable, *, adjust_active_row, ...)`
- `src/tet4d/ui/pygame/topology_lab/copy.py`: `display_title_for_state(state)`, `topology_note_text(state)`
- `src/tet4d/ui/pygame/topology_lab/entrypoint.py`: `parse_topology_playground_dimension(raw_value)`, `run_direct_topology_playground(dimension)`
- `src/tet4d/ui/pygame/topology_lab/explorer_tools.py`: `cycle_tool(state, step)`, `draw_tool_ribbon(surface, fonts, *, area, active_workspace)`
- `src/tet4d/ui/pygame/topology_lab/explosion.py`: `clear_scene_explosion(state)`, `consume_pending_scene_explosion_launch(state)`, `scene_explosion_particles(state)`, `start_sandbox_explosion(state)`, `step_scene_explosion(state, *, dt_ms, play_sfx)`
- `src/tet4d/ui/pygame/topology_lab/piece_sandbox.py`: `sandbox_shapes_for_state(state)`, `ensure_piece_sandbox(state)`, `spawn_sandbox_piece(state)`, `sandbox_shape(state)`, `sandbox_cells(state)`, `rotate_sandbox_piece_action(state, profile, action)`, `sandbox_validity(state, profile)`, `move_sandbox_piece(state, profile, step_label)`, `rotate_sandbox_piece(state, profile)`, `cycle_sandbox_piece(state, step)`, `reset_sandbox_piece(state)`, `sandbox_lines(state, profile)`
- `src/tet4d/ui/pygame/topology_lab/play_launch.py`: `launch_playground_state_gameplay(playground_state, screen, fonts_nd, ...)`
- `src/tet4d/ui/pygame/topology_lab/preview.py`: `build_preview_lines(preview, *, dimension)`, `draw_preview_panel(surface, fonts, *, area, title, lines)`, `draw_probe_controls(surface, fonts, *, area, step_options, ...)`
- `src/tet4d/ui/pygame/topology_lab/projection_scene.py`: `projection_pairs_for_dimension(dimension)`, `projection_label(axes)`, `projection_hidden_axes(dimension, axes)`, `projection_hidden_label(dimension, axes, selected_coord, *, slab_radius=...)`, `draw_projection_scene(surface, fonts, *, dimension, area, ...)`
- `src/tet4d/ui/pygame/topology_lab/scene2d.py`: `draw_probe_path_glyphs(surface, *, centers, cell_size)`, `draw_probe_neighbor_glyphs(surface, *, centers, cell_size)`, `draw_probe_center_glyph(surface, *, center, cell_size)`, `draw_scene(surface, fonts, *, area, boundaries, ...)`
- `src/tet4d/ui/pygame/topology_lab/scene3d.py`: `draw_scene(surface, fonts, *, area, boundaries, ...)`
- `src/tet4d/ui/pygame/topology_lab/scene4d.py`: `draw_scene(surface, fonts, *, area, boundaries, ...)`
- `src/tet4d/ui/pygame/topology_lab/scene_preview_state.py`: `clear_explorer_scene_state(state)`, `preview_signature_for_state(state)`, `refresh_explorer_scene_state(state)`, `advance_pending_explorer_playability_analysis(state)`, `ensure_explorer_playability_analysis(state)`
- `src/tet4d/ui/pygame/topology_lab/scene_state.py`: `ExplorerPlaygroundSettings`, `ExplorerPreviewCompileSignature`, `ExplorerPreviewCompileArtifacts`, `ExplorerPlayabilityArtifacts`, `TopologyPlaygroundState`, `canonical_tool_name(tool)`, `active_workspace_name(state)`, `current_editor_tool(state)`, `tool_is_edit(tool)`, `tool_is_probe(tool)`, `tool_is_sandbox(tool)`, `uses_general_explorer_editor(state)`, ...
- `src/tet4d/ui/pygame/topology_lab/scene_state_canonical.py`: `sync_shell_state_from_canonical(state)`, `canonical_playground_state(state)`, `current_explorer_profile(state)`, `current_explorer_draft(state)`, `current_play_settings(state)`, `current_dirty(state)`, `sync_canonical_playground_state(state)`, `set_dirty(state, dirty)`, `replace_play_settings(state, settings)`, `replace_explorer_profile(state, explorer_profile)`, `replace_explorer_draft(state, explorer_draft)`, `update_explorer_draft(state, *, slot_index=..., source_index=..., ...)`, ...
- `src/tet4d/ui/pygame/topology_lab/scene_state_probe.py`: `current_highlighted_glue_id(state)`, `current_probe_coord(state)`, `current_probe_trace(state)`, `probe_trace_visible(state)`, `probe_neighbors_visible(state)`, `current_probe_path(state)`, `current_probe_frame(state)`, `replace_probe_state(state, *, coord, trace, path, ...)`, `set_probe_trace_visible(state, enabled)`, `set_probe_neighbors_visible(state, enabled)`, `set_highlighted_glue_id(state, glue_id)`, `playground_dims_for_state(state)`, ...
- `src/tet4d/ui/pygame/topology_lab/shell_layout.py`: `TopologyLabTopBarLayout`, `TopologyLabFooterLayout`, `TopologyLabShellLayout`, `TopologyLabRowTextBudgets`, `topology_lab_row_text_budgets(*, menu_w, row_rect_width)`, `build_topology_lab_shell_layout(*, width, height, general_editor, scene_pane_active, ...)`
- `src/tet4d/ui/pygame/topology_lab/state_ownership.py`: `TopologyLabEditorOwnershipState`, `TopologyLabInspectorOwnershipState`, `TopologyLabSandboxOwnershipState`, `TopologyLabPlayOwnershipState`, `TopologyLabDerivedCacheOwnershipState`, `TopologyLabOwnershipSnapshot`, `ownership_snapshot(state)`, `current_sandbox_focus_coord(state)`, `current_sandbox_focus_trace(state)`, `current_sandbox_focus_path(state)`, `current_sandbox_focus_frame(state)`, `replace_sandbox_focus_state(state, *, coord, trace, path, ...)`, ...
- `src/tet4d/ui/pygame/topology_lab/transform_editor.py`: `draw_transform_editor(surface, fonts, *, area, editable=..., ...)`, `draw_action_buttons(surface, fonts, *, area, actions=...)`
- `src/tet4d/ui/pygame/ui_utils.py`: `button_bg()`, `button_active()`, `button_text()`, `button_border()`, `panel_bg()`, `panel_border()`, `fit_text(font, text, max_width)`, `text_fits(font, text, max_width)`, `wrap_text_lines(font, text, max_width)`, `wrapped_row_height(font, line_count, *, min_padding=..., ...)`, `wrapped_label_value_layout(font, *, label, value, total_width=..., ...)`, `SliderRowLayout`, ...
<!-- END GENERATED:project_structure_symbol_index -->

<!-- BEGIN GENERATED:project_structure_likely_test_files -->
## Likely Test Files

These heuristic links are likely test files for configured sources.
They are routing hints only, using tiered exact, prefix, then controlled fallback matching.
Match labels are shown inline as `(exact)`, `(prefix)`, or `(fallback)`.

- `cli/front.py`: `tests/unit/engine/test_front_launcher_routes.py` (prefix)
- `cli/front2d.py`: `tests/unit/engine/test_front2d_setup.py` (prefix)
- `cli/front3d.py`: `tests/unit/engine/test_front3d_setup.py` (prefix)
- `src/tet4d/engine/core/model/board.py`: `tests/unit/engine/test_board.py` (exact)
- `src/tet4d/engine/core/model/game_nd_views.py`: `tests/unit/engine/test_game_nd.py` (fallback)
- `src/tet4d/engine/core/piece_transform.py`: `tests/unit/engine/test_piece_transform.py` (exact)
- `src/tet4d/engine/core/rotation_kicks.py`: `tests/unit/engine/test_rotation_kicks.py` (exact)
- `src/tet4d/engine/core/rules/lifecycle.py`: `tests/unit/engine/test_lifecycle_rules.py` (prefix)
- `src/tet4d/engine/core/rules/piece_placement.py`: `tests/unit/engine/test_piece_placement.py` (exact)
- `src/tet4d/engine/gameplay/challenge_mode.py`: `tests/unit/engine/test_challenge_mode.py` (exact)
- `src/tet4d/engine/gameplay/explorer_piece_transport.py`: `tests/unit/engine/test_explorer_piece_transport.py` (exact)
- `src/tet4d/engine/gameplay/game2d.py`: `tests/unit/engine/test_game2d.py` (exact)
- `src/tet4d/engine/gameplay/game_nd.py`: `tests/unit/engine/test_game_nd.py` (exact)
- `src/tet4d/engine/gameplay/leveling.py`: `tests/test_leveling.py` (exact)
- `src/tet4d/engine/gameplay/pieces_nd.py`: `tests/unit/engine/test_pieces_nd.py` (exact)
- `src/tet4d/engine/gameplay/rotation_anim.py`: `tests/unit/engine/test_rotation_anim.py` (exact)
- `src/tet4d/engine/gameplay/scoring_bonus.py`: `tests/unit/engine/test_scoring_bonus.py` (exact)
- `src/tet4d/engine/gameplay/speed_curve.py`: `tests/unit/engine/test_speed_curve.py` (exact)
- `src/tet4d/engine/gameplay/topology.py`: `tests/unit/engine/test_topology.py` (exact)
- `src/tet4d/engine/gameplay/topology_designer.py`: `tests/unit/engine/test_topology_designer.py` (exact)
- `src/tet4d/engine/help_text.py`: `tests/unit/engine/test_help_text.py` (exact)
- `src/tet4d/engine/runtime/help_topics.py`: `tests/unit/engine/test_help_topics.py` (exact)
- `src/tet4d/engine/runtime/leaderboard.py`: `tests/unit/engine/test_leaderboard.py` (exact)
- `src/tet4d/engine/runtime/project_config.py`: `tests/unit/engine/test_project_config.py` (exact)
- `src/tet4d/engine/runtime/runtime_config.py`: `tests/unit/engine/test_runtime_config.py` (exact)
- `src/tet4d/engine/runtime/score_analyzer.py`: `tests/unit/engine/test_score_analyzer.py` (exact)
- `src/tet4d/engine/runtime/score_analyzer_features.py`: `tests/unit/engine/test_score_analyzer.py` (fallback)
- `src/tet4d/engine/runtime/topology_explorer_experiments.py`: `tests/unit/engine/test_topology_explorer_experiments.py` (exact)
- `src/tet4d/engine/runtime/topology_explorer_preview.py`: `tests/unit/engine/test_topology_explorer_preview.py` (exact)
- `src/tet4d/engine/runtime/topology_explorer_runtime.py`: `tests/unit/engine/test_topology_explorer_runtime.py` (exact)
- `src/tet4d/engine/runtime/topology_explorer_store.py`: `tests/unit/engine/test_topology_explorer_store.py` (exact)
- `src/tet4d/engine/runtime/topology_playability_signal.py`: `tests/unit/engine/test_topology_playability_signal.py` (exact)
- `src/tet4d/engine/runtime/topology_playground_launch.py`: `tests/unit/engine/test_topology_playground_launch.py` (exact)
- `src/tet4d/engine/runtime/topology_playground_sandbox.py`: `tests/unit/engine/test_topology_playground_sandbox.py` (exact)
- `src/tet4d/engine/runtime/topology_playground_state.py`: `tests/unit/engine/test_topology_playground_state.py` (exact)
- `src/tet4d/engine/runtime/topology_profile_store.py`: `tests/unit/engine/test_topology_profile_store.py` (exact)
- `src/tet4d/engine/topology_explorer/transport_resolver.py`: `tests/unit/engine/test_explorer_transport_resolver.py` (fallback)
- `src/tet4d/engine/tutorial/setup_apply.py`: `tests/unit/engine/test_tutorial_setup_apply.py` (fallback)
- `src/tet4d/engine/ui_logic/menu_layout.py`: `tests/unit/engine/test_menu_layout.py` (exact)
- `src/tet4d/ui/pygame/endgame_animation.py`: `tests/unit/engine/test_endgame_animation.py` (exact)
- `src/tet4d/ui/pygame/front2d_setup.py`: `tests/unit/engine/test_front2d_setup.py` (exact)
- `src/tet4d/ui/pygame/front4d_render.py`: `tests/unit/engine/test_front4d_render.py` (exact)
- `src/tet4d/ui/pygame/input/camera_mouse.py`: `tests/unit/engine/test_camera_mouse.py` (exact)
- `src/tet4d/ui/pygame/input/view_controls.py`: `tests/unit/engine/test_view_controls.py` (exact)
- `src/tet4d/ui/pygame/keybindings.py`: `tests/unit/engine/test_keybindings.py` (exact)
- `src/tet4d/ui/pygame/launch/launcher_settings.py`: `tests/unit/engine/test_launcher_settings_layout.py` (prefix)
- `src/tet4d/ui/pygame/launch/leaderboard_menu.py`: `tests/unit/engine/test_leaderboard_menu.py` (exact)
- `src/tet4d/ui/pygame/launch/topology_lab_menu.py`: `tests/unit/engine/test_topology_lab_menu.py` (exact)
- `src/tet4d/ui/pygame/menu/keybindings_menu.py`: `tests/unit/engine/test_keybindings_menu_model.py` (prefix)
- `src/tet4d/ui/pygame/menu/keybindings_menu_model.py`: `tests/unit/engine/test_keybindings_menu_model.py` (exact)
- `src/tet4d/ui/pygame/menu/menu_navigation_keys.py`: `tests/unit/engine/test_menu_navigation_keys.py` (exact)
- `src/tet4d/ui/pygame/menu/menu_runner.py`: `tests/unit/engine/test_menu_runner.py` (exact)
- `src/tet4d/ui/pygame/menu/numeric_text_input.py`: `tests/unit/engine/test_numeric_text_input.py` (exact)
- `src/tet4d/ui/pygame/render/active_piece_projection_guides.py`: `tests/unit/render/test_active_piece_projection_guides.py` (exact)
- `src/tet4d/ui/pygame/render/front3d_projection_helpers.py`: `tests/unit/render/test_projection_guide_animation.py` (fallback), `tests/unit/render/test_active_piece_projection_guides.py` (fallback)
- `src/tet4d/ui/pygame/render/gfx_game.py`: `tests/unit/engine/test_gfx_game_rotation_render.py` (prefix)
- `src/tet4d/ui/pygame/render/panel_utils.py`: `tests/unit/engine/test_panel_utils.py` (exact)
- `src/tet4d/ui/pygame/render/projected_occlusion.py`: `tests/unit/engine/test_projected_piece_occlusion.py` (fallback)
- `src/tet4d/ui/pygame/render/w_movement_animation.py`: `tests/unit/render/test_projection_guide_animation.py` (fallback)
- `src/tet4d/ui/pygame/runtime_ui/help_menu.py`: `tests/unit/engine/test_help_menu.py` (exact)
- `src/tet4d/ui/pygame/runtime_ui/pause_menu.py`: `tests/unit/engine/test_pause_menu.py` (exact)
- `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`: `tests/unit/engine/test_tutorial_overlay.py` (exact)
- `src/tet4d/ui/pygame/topology_lab/camera_controls.py`: `tests/unit/engine/test_tutorial_mouse_camera_controls.py` (fallback)
- `src/tet4d/ui/pygame/topology_lab/interaction_audit.py`: `tests/unit/engine/test_topology_lab_interaction_audit.py` (fallback)
- `src/tet4d/ui/pygame/topology_lab/piece_sandbox.py`: `tests/unit/topology_lab/test_topology_lab_projection_sandbox.py` (fallback)
- `src/tet4d/ui/pygame/topology_lab/projection_scene.py`: `tests/unit/topology_lab/test_topology_lab_projection_sandbox.py` (fallback)
- `src/tet4d/ui/pygame/topology_lab/scene_preview_state.py`: `tests/unit/topology_lab/test_topology_lab_preview_latency.py` (fallback)

### Stage 20 Topology Identifier Normalization Parity Test Files

1. `tests/fixtures/parity/topology_identifier_normalization.json`: identifier-only Stage 20 fixture
2. `tests/unit/migration/test_topology_identifier_normalization_parity.py`: Stage 20 parity tests

### Stage 22 Trace Schema/Version Normalization Parity Test Files

1. `tests/fixtures/parity/trace_schema_version_normalization.json`: schema/version metadata-only Stage 22 fixture
2. `tests/unit/migration/test_trace_schema_version_normalization_parity.py`: Stage 22 parity tests
<!-- END GENERATED:project_structure_likely_test_files -->
