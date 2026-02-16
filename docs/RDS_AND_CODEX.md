# RDS Files And Codex Instructions

This document is section `3` of the unified documentation layout.

## RDS index

All requirement/design specs are in:
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_TETRIS_GENERAL.md`
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_KEYBINDINGS.md`
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_MENU_STRUCTURE.md`
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_2D_TETRIS.md`
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_3D_TETRIS.md`
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_4D_TETRIS.md`

Read order:
1. General RDS
2. Keybindings RDS
3. Menu structure RDS
4. Mode-specific RDS
5. This Codex instructions page

## Codex contributor workflow

1. Read the relevant RDS files before editing gameplay logic.
2. Keep keybindings external; do not hardcode mode keys in frontends.
3. Preserve deterministic behavior where seeds are used.
4. When refactoring frontends, keep behavior parity with existing tests.
5. Prefer small, composable helpers over large event/render functions.

## Coding best practices

1. Keep game rules in engine modules (`game2d.py`, `game_nd.py`) and keep rendering thin.
2. Reuse shared projection/menu/input helpers to avoid 3D/4D drift.
3. Avoid side effects during import (especially in keybinding/config modules).
4. Keep files ASCII unless there is a strong reason otherwise.
5. Name helper functions by intent (`_advance_gravity`, `_tick_clear_animation`, etc.).
6. Keep complexity in check; run `ruff --select C901` on changes.

## Testing instructions

Run after every gameplay or input change:

```bash
ruff check /Users/omer/workspace/test-code/tet4d
ruff check /Users/omer/workspace/test-code/tet4d --select C901
pytest -q
python3.14 -m compileall -q /Users/omer/workspace/test-code/tet4d/front2d.py /Users/omer/workspace/test-code/tet4d/tetris_nd
```

Minimum required coverage for gameplay-affecting changes:
1. Unit tests for engine correctness (move/rotate/lock/clear/scoring).
2. Replay determinism tests.
3. Per-mode smoke tests for key routing and system controls.
4. If controls changed, verify JSON keybinding load/save behavior.

## Done criteria for gameplay changes

1. RDS intent remains accurate or is updated in the same change.
2. Existing tests pass and new behavior has targeted tests.
3. No new C901 failures.
4. Usage docs remain valid (`README.md`, docs links, run commands).

## Simplification Opportunities (2026-02-16)

This section tracks high-value code simplification targets discovered from structure review and `ruff --select C901`.

### Current complexity hotspots

1. `/Users/omer/workspace/test-code/tet4d/front.py`
2. `_run_audio_settings_menu` and `_run_display_settings_menu` are large, stateful loops.
3. `run` mixes startup, menu event flow, and launch orchestration.
4. `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_controls.py`
5. `apply_menu_actions` is highly branched and handles many unrelated actions.
6. `/Users/omer/workspace/test-code/tet4d/tetris_nd/keybindings_menu.py`
7. `_run_menu_action` has dense branch-heavy control flow.
8. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_game.py`
9. `LoopContext4D.keydown_handler` combines system, slice, gameplay, and view dispatch.
10. `/Users/omer/workspace/test-code/tet4d/tetris_nd/keybindings.py`
11. `rebind_action_key` combines validation, conflict resolution, and state mutation.
12. `/Users/omer/workspace/test-code/tet4d/tetris_nd/pieces_nd.py`
13. `get_piece_shapes_nd` is branching across many set variants.

### Duplication hotspots

1. Camera/view turn animation logic is duplicated between:
2. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_game.py` (`Camera3D`)
3. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_game.py` (`LayerView3D`)
4. Large portions of projected rendering and clear-effect pipelines are parallel in 3D/4D frontends.
5. Launch/setup/display initialization patterns are repeated across:
6. `/Users/omer/workspace/test-code/tet4d/front.py`
7. `/Users/omer/workspace/test-code/tet4d/front2d.py`
8. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_game.py`
9. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_game.py`

### Recommended simplification backlog

1. Extract shared menu-state action dispatcher.
2. Move menu action handlers from `if/elif` ladders to table-driven handlers with small pure functions.
3. Target files: `menu_controls.py`, `keybindings_menu.py`, `front.py`.

4. Extract shared camera pose animator.
5. Create one reusable yaw/pitch animation component and reuse it in 3D and 4D views.
6. Target files: `front3d_game.py`, `front4d_game.py`, `view_controls.py`.

7. Extract shared ND movement dispatch pipeline.
8. Centralize system/slice/gameplay routing order and SFX triggers in one helper to avoid per-frontend drift.
9. Target files: `frontend_nd.py`, `front3d_game.py`, `front4d_game.py`.

10. Replace branching piece-set selector with registry maps.
11. Use per-dimension registry dictionaries for set id -> generator function.
12. Target file: `pieces_nd.py`.

13. Consolidate app boot and display/audio persistence glue.
14. Build one startup/session manager used by `front.py` and direct entrypoints.
15. Target files: `front.py`, `front2d.py`, `front3d_game.py`, `front4d_game.py`.

### Verification requirements for simplification PRs

1. No behavior changes without tests.
2. Add or update targeted tests before extraction/refactor.
3. Keep deterministic replay tests green.
4. Run:
5. `ruff check /Users/omer/workspace/test-code/tet4d`
6. `ruff check /Users/omer/workspace/test-code/tet4d --select C901`
7. `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3.11 -m pytest -q`
8. `python3.14 -m compileall -q /Users/omer/workspace/test-code/tet4d/front.py /Users/omer/workspace/test-code/tet4d/tetris_nd`
