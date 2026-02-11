# 2D Tetris RDS

Status: Active v0.3  
Author: Omer + Codex  
Date: 2026-02-10  
Target Runtime: Python 3.14 + `pygame-ce`

## 1. Scope

Define requirements for the classic `(x, y)` mode implemented by:
- `/Users/omer/workspace/test-code/tet4d/front2d.py`
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/game2d.py`

## 2. Current Intentions

1. Keep 2D mode as the baseline reference for gameplay correctness.
2. Keep rules simple and deterministic with seeded piece order.
3. Ensure no 3D/4D movement or rotation logic leaks into 2D gameplay.

## 3. Board and Rules

1. Coordinate system: `(x, y)`.
2. Gravity axis: `y`.
3. Setup range: width `6..16`, height `12..30`.
4. Clear rule: a line is removed only when all `x` cells at that `y` are filled.
5. `z`/`w` movement and rotation are disabled/ignored in 2D mode.

## 4. Piece Set

1. Classic tetromino bag (`I,O,T,S,Z,J,L`).
2. Piece blocks are relative to pivot coordinates.

## 5. Controls and UX

1. Movement: left/right.
2. Soft drop, hard drop, and `x-y` rotation only.
3. System controls: restart/menu/quit/toggle-grid.
4. Grid off mode must keep a visible board shadow.
5. Line clear should be animated.

## 6. Scoring

1. 1 line: `40`
2. 2 lines: `100`
3. 3 lines: `300`
4. 4 lines: `1200`

## 7. Coding Best Practices (2D)

1. Keep 2D actions mapped only through `KEYS_2D` and system keys.
2. Keep gravity and locking logic inside `GameState.step`/`lock_current_piece`.
3. Keep rendering-specific effects out of game-rule modules.

## 8. Testing Instructions (2D)

Minimum required tests for 2D gameplay changes:
1. line clear + shift-down behavior,
2. hard drop correctness,
3. deterministic replay consistency,
4. key routing smoke tests.

Relevant test files:
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_game2d.py`
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_board.py`
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_gameplay_replay.py`

## 9. Acceptance Criteria

1. 2D mode is playable start-to-finish.
2. Only `x` line fullness triggers clears.
3. ND-only keys do not alter state.
4. Tests pass under Python 3.14 compatibility checks.
