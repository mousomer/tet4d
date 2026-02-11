# Tetris Family RDS (General)

Status: Active v0.3  
Author: Omer + Codex  
Date: 2026-02-10  
Target Runtime: Python 3.14 + `pygame-ce`

## 1. Purpose

Define shared requirements for the 2D, 3D, and 4D game modes in this repository.

Mode-specific requirements are defined in:
1. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_2D_TETRIS.md`
2. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_3D_TETRIS.md`
3. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_4D_TETRIS.md`

## 2. Current Project Intentions

1. Keep one shared deterministic gameplay core with mode-specific frontends.
2. Keep controls configurable via external JSON files (`keybindings/2d.json`, `3d.json`, `4d.json`).
3. Maintain playable and testable 2D, 3D, and 4D experiences with the same quality bar.
4. Preserve Python 3.14 compatibility while staying runnable on local Python 3.11+.

## 3. Shared Rules and Axis Conventions

1. Axis `0` = `x` (horizontal), axis `1` = `y` (gravity/downward).
2. 3D adds axis `2` = `z`, 4D adds axis `3` = `w`.
3. Gravity acts on axis `y` in all modes.
4. `y < 0` is allowed before lock; locking above top triggers game over.
5. Board storage is sparse (`coord -> cell_id`).

## 4. Shared UX Requirements

1. Menu/setup screen before starting each mode.
2. In-game panel with score, cleared lines/layers, speed, controls, and game-over state.
3. Toggleable grid in all modes.
4. When grid is off, a board shadow/silhouette must still provide spatial context.
5. Layer/line clear feedback should be animated.

## 5. Controls and Keybinding Requirements

1. Keybindings must be loaded from external JSON files.
2. Small and full keyboard profiles are supported.
3. System actions (`quit`, `menu`, `restart`, `toggle_grid`) are shared and discoverable.
4. 2D must ignore ND-only movement/rotation keys.

## 6. Technical Requirements

1. Dependency package is `pygame-ce`; imports remain `import pygame`.
2. Main scripts:
3. `front2d.py`
4. `front3d.py`
5. `front4d.py`
6. Game loops must be frame-rate independent for gravity.

## 7. Engineering Best Practices

1. Keep gameplay rules in engine modules (`game2d.py`, `game_nd.py`).
2. Keep rendering and camera/view logic in frontend modules.
3. Prefer small helper functions to avoid deeply nested loops and handlers.
4. Share projection/math helpers to avoid 3D/4D behavior drift.
5. Avoid hidden side effects at import-time.
6. Keep deterministic paths stable (seeded RNG, reproducible replay scripts).

## 8. Testing Instructions

Required checks for behavior changes:

```bash
ruff check /Users/omer/workspace/test-code/tet4d
ruff check /Users/omer/workspace/test-code/tet4d --select C901
pytest -q
python3.14 -m compileall -q /Users/omer/workspace/test-code/tet4d/front2d.py /Users/omer/workspace/test-code/tet4d/tetris_nd
```

Expected test categories:
1. Unit tests for board, pieces, and game state transitions.
2. Replay determinism tests for 2D/3D/4D.
3. Smoke tests for key routing and system controls per mode.

## 9. Acceptance Criteria (Family)

1. All three modes launch and play from menu to game-over without crash.
2. Clear and scoring logic match the mode RDS files.
3. Keybindings remain external and loadable.
4. Test and lint suites pass.
