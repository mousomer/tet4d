# Plan Report: Menu Graph Modularization + Launcher/Pause Runner Migration (2026-02-21)

Status: Planned (execution in this batch)  
Related backlog items: `BKL-P2-022` (new), `BKL-P2-009` (follow-up)  
Related RDS files: `docs/rds/RDS_MENU_STRUCTURE.md`

## 1. Objective

1. Remove hardcoded menu trees from launcher/pause runtime paths.
2. Introduce a config-defined menu graph with reusable runtime navigation/dispatch primitives.
3. Keep top-level IA unchanged while preparing `Play` branch capacity for future `Tutorials` and `Topology Lab` routes.

## 2. Comparison Against Existing RDS

Current `docs/rds/RDS_MENU_STRUCTURE.md` confirms top-level IA and parity, but launcher play-mode selection is still runtime-coded (`front.py`) rather than fully config-defined graph navigation.

Gap to close in this batch:
1. Promote menu structure from row/action arrays to an explicit graph (`menu_id -> title/items`).
2. Route launcher and pause through one generic menu runner + action registry.
3. Add machine lint/contract checks for graph reachability, handler coverage, and launcher/pause parity.

## 3. Planned Implementation Order

1. Extend menu config validation (`tetris_nd/menu_config.py`) to support `menus` graph while preserving legacy payload compatibility.
2. Add generic runtime primitives:
   - `tetris_nd/menu_runner.py` (`MenuRunner`, `ActionRegistry`)
3. Migrate launcher:
   - remove hardcoded play picker from `front.py`
   - use config-defined `Play` submenu/actions/routes
4. Migrate pause menu:
   - use `MenuRunner`/`ActionRegistry` while preserving decision semantics (`resume/restart/menu/quit`) and status behavior.
5. Add lint and hooks:
   - `tetris_nd/menu_graph_linter.py`
   - `tools/lint_menu_graph.py`
   - integrate in `tools/validate_project_contracts.py` and `scripts/ci_check.sh`.

## 4. Acceptance Criteria

1. Top-level launcher labels remain exactly: `Play`, `Continue`, `Settings`, `Controls`, `Help`, `Bot`, `Quit`.
2. No hardcoded play-mode picker remains in `front.py`.
3. `config/menu/structure.json` defines launcher/pause/play menu graph via `menus`.
4. Linter fails on unreachable menus, missing action handlers, and launcher/pause parity breaks.
5. Contract validation + targeted tests pass.
