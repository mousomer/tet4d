# Project Structure And Documentation

This document describes the current canonical package layout and ownership model.

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

## Canonical Entry Points

1. [cli/front.py](/C:/Users/omer/Documents/workspace/repos/tet4d/cli/front.py): unified launcher
2. [cli/front2d.py](/C:/Users/omer/Documents/workspace/repos/tet4d/cli/front2d.py): thin 2D shim
3. [cli/front3d.py](/C:/Users/omer/Documents/workspace/repos/tet4d/cli/front3d.py): thin 3D shim
4. [cli/front4d.py](/C:/Users/omer/Documents/workspace/repos/tet4d/cli/front4d.py): thin 4D shim

## Canonical Runtime Owners

### Engine

1. [api.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/engine/api.py): small compatibility facade used mainly by replay and explicit compatibility tests
2. [api.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/engine/gameplay/api.py): gameplay convenience exports
3. [api.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/engine/runtime/api.py): runtime/help/menu convenience exports
4. [api.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/engine/tutorial/api.py): tutorial convenience exports
5. [piece_transform.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/engine/core/piece_transform.py): canonical piece-local transform math
6. [rotation_kicks.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/engine/core/rotation_kicks.py): canonical kick candidate generation and shared resolution
7. [game2d.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/engine/gameplay/game2d.py): 2D gameplay state/rules
8. [game_nd.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/engine/gameplay/game_nd.py): 3D/4D gameplay state/rules
9. [menu_config.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/engine/runtime/menu_config.py): menu/runtime config loading
10. [menu_settings_state.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/engine/runtime/menu_settings_state.py): persisted settings state
11. [content.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/engine/tutorial/content.py): tutorial content loader
12. [runtime.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/engine/tutorial/runtime.py): tutorial runtime session logic

### UI

1. [front2d_game.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/front2d_game.py): 2D orchestration entry
2. [front2d_setup.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/front2d_setup.py): 2D setup/menu owner
3. [front2d_loop.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/front2d_loop.py): 2D runtime loop owner
4. [front2d_runtime.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/front2d_runtime.py): 2D runtime compatibility facade for legacy imports/tests
5. [frontend_nd.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/frontend_nd.py): shared ND setup/menu/input helpers
6. [front3d_game.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/front3d_game.py): 3D frontend
7. [front4d_game.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/front4d_game.py): 4D frontend
8. [front3d_render.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/front3d_render.py): 3D render adapter
9. [front4d_render.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/front4d_render.py): 4D render adapter
10. [runtime_ui/](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/runtime_ui): bootstrap, pause/help, tutorial overlay, shared loop helpers
11. [launch/](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/launch): launcher, settings, bot, leaderboard flows
12. [menu/](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/menu): shared menu/keybinding adapters, including `setup_menu_runner.py`
13. [render/](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ui/pygame/render): render/layout/helper adapters

### AI

1. [controller.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ai/playbot/controller.py): playbot runtime controller
2. [planner_2d.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ai/playbot/planner_2d.py): 2D planning
3. [planner_nd.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ai/playbot/planner_nd.py): ND planning entry
4. [planner_nd_core.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ai/playbot/planner_nd_core.py): shared ND candidate logic
5. [planner_nd_search.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ai/playbot/planner_nd_search.py): ND search/budget logic
6. [dry_run.py](/C:/Users/omer/Documents/workspace/repos/tet4d/src/tet4d/ai/playbot/dry_run.py): stability/dry-run harness

## Config And Docs Sources Of Truth

1. [config/menu/structure.json](/C:/Users/omer/Documents/workspace/repos/tet4d/config/menu/structure.json): launcher/pause/settings/help/menu graph and copy
2. [config/menu/defaults.json](/C:/Users/omer/Documents/workspace/repos/tet4d/config/menu/defaults.json): default persisted settings payload
3. [config/tutorial/lessons.json](/C:/Users/omer/Documents/workspace/repos/tet4d/config/tutorial/lessons.json): tutorial packs and board profiles
4. [config/gameplay/tuning.json](/C:/Users/omer/Documents/workspace/repos/tet4d/config/gameplay/tuning.json): scoring/kick/tuning defaults
5. [docs/CONFIGURATION_REFERENCE.md](/C:/Users/omer/Documents/workspace/repos/tet4d/docs/CONFIGURATION_REFERENCE.md): generated full config inventory
6. [docs/USER_SETTINGS_REFERENCE.md](/C:/Users/omer/Documents/workspace/repos/tet4d/docs/USER_SETTINGS_REFERENCE.md): generated user-facing settings summary
7. [docs/ARCHITECTURE_CONTRACT.md](/C:/Users/omer/Documents/workspace/repos/tet4d/docs/ARCHITECTURE_CONTRACT.md): dependency contract
8. [CURRENT_STATE.md](/C:/Users/omer/Documents/workspace/repos/tet4d/CURRENT_STATE.md): restart handoff
9. [docs/BACKLOG.md](/C:/Users/omer/Documents/workspace/repos/tet4d/docs/BACKLOG.md): active backlog and current change footprint

## Placement Rules

1. Put pure deterministic logic in `src/tet4d/engine/core/`.
2. Put gameplay/runtime/tutorial logic in `src/tet4d/engine/`.
3. Put `pygame` frontends, rendering, audio, and menu adapters in `src/tet4d/ui/pygame/`.
4. Put playbot ownership in `src/tet4d/ai/playbot/`.
5. Keep CLI files as thin shims over package code.
6. Prefer reusing an existing canonical owner over adding wrappers.
7. Do not reintroduce reverse imports from engine into UI or AI.

## Verification Contract

Run:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

Authoritative enforcement is backed by:

1. [scripts/check_architecture_boundaries.sh](/C:/Users/omer/Documents/workspace/repos/tet4d/scripts/check_architecture_boundaries.sh)
2. [scripts/check_engine_core_purity.sh](/C:/Users/omer/Documents/workspace/repos/tet4d/scripts/check_engine_core_purity.sh)
3. [scripts/arch_metrics.py](/C:/Users/omer/Documents/workspace/repos/tet4d/scripts/arch_metrics.py)
4. [tools/governance/architecture_metric_budget.py](/C:/Users/omer/Documents/workspace/repos/tet4d/tools/governance/architecture_metric_budget.py)
