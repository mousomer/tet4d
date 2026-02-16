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

1. `/Users/omer/workspace/test-code/tet4d/tetris_nd/keybindings.py`
2. `rebind_action_key` combines validation, conflict resolution, and state mutation.
3. `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_settings_state.py`
4. `apply_saved_menu_settings` is still branch-heavy for mixed menu payload application.
5. Note: prior hotspots in `front.py`, `menu_controls.py`, `keybindings_menu.py`, `front4d_game.py`, and `pieces_nd.py` were reduced on 2026-02-16.

### Duplication hotspots

1. 3D and 4D projected rendering stacks remain intentionally parallel in:
2. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_game.py`
3. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_game.py`
4. Further unification is possible but should be weighed against readability/regression risk.

### Recommended simplification backlog

1. Completed: extract shared menu-state action dispatcher (2026-02-16).
2. Completed in:
3. `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_controls.py`
4. `/Users/omer/workspace/test-code/tet4d/tetris_nd/keybindings_menu.py`
5. Follow-up completed: same dispatcher/handler pattern applied to `/Users/omer/workspace/test-code/tet4d/front.py`.

6. Completed: extract shared camera pose animator (2026-02-16).
7. Completed in:
8. `/Users/omer/workspace/test-code/tet4d/tetris_nd/view_controls.py`
9. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_game.py`
10. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_game.py`

11. Completed: extract shared ND movement dispatch pipeline (2026-02-16).
12. Completed in:
13. `/Users/omer/workspace/test-code/tet4d/tetris_nd/frontend_nd.py`
14. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_game.py`
15. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_game.py`

16. Completed: replace branching piece-set selector with registry maps (2026-02-16).
17. Completed in:
18. `/Users/omer/workspace/test-code/tet4d/tetris_nd/pieces_nd.py`

19. Completed: consolidate app boot and display/audio persistence glue (2026-02-16).
20. Completed in:
21. `/Users/omer/workspace/test-code/tet4d/tetris_nd/app_runtime.py`
22. `/Users/omer/workspace/test-code/tet4d/front.py`
23. `/Users/omer/workspace/test-code/tet4d/front2d.py`
24. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_game.py`
25. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_game.py`

### Verification requirements for simplification PRs

1. No behavior changes without tests.
2. Add or update targeted tests before extraction/refactor.
3. Keep deterministic replay tests green.
4. Run:
5. `ruff check /Users/omer/workspace/test-code/tet4d`
6. `ruff check /Users/omer/workspace/test-code/tet4d --select C901`
7. `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3.11 -m pytest -q`
8. `python3.14 -m compileall -q /Users/omer/workspace/test-code/tet4d/front.py /Users/omer/workspace/test-code/tet4d/tetris_nd`
