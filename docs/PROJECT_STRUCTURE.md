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
|- packaging/                   PyInstaller spec and OS packaging scripts
|- scripts/                     local verification and architecture checks
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
`- tools/                       governance, stability, benchmark tooling
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

1. `config/menu/structure.json`: launcher/pause/settings/help/menu graph and copy
2. `config/menu/defaults.json`: default persisted settings payload
3. `config/tutorial/lessons.json`: tutorial packs and board profiles
4. `config/gameplay/tuning.json`: scoring/kick/tuning defaults
5. `docs/CONFIGURATION_REFERENCE.md`: generated full config inventory
6. `docs/USER_SETTINGS_REFERENCE.md`: generated user-facing settings summary
7. `docs/ARCHITECTURE_CONTRACT.md`: dependency contract
8. `CURRENT_STATE.md`: restart handoff
9. `docs/BACKLOG.md`: active backlog and current change footprint
<!-- END GENERATED:project_structure_sources_of_truth -->

## Placement Rules

1. Put pure deterministic logic in `src/tet4d/engine/core/`.
2. Put gameplay/runtime/tutorial logic in `src/tet4d/engine/`.
3. Put `pygame` frontends, rendering, audio, and menu adapters in `src/tet4d/ui/pygame/`.
4. Put playbot ownership in `src/tet4d/ai/playbot/`.
5. Keep CLI files as thin shims over package code.
6. Prefer reusing an existing canonical owner over adding wrappers.
7. Do not reintroduce reverse imports from engine into UI or AI.

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
