# 2D Tetris RDS

Status: Active v0.6 (Verified 2026-02-18)  
Author: Omer + Codex  
Date: 2026-02-18  
Target Runtime: Python 3.11-3.14 + `pygame-ce`

## 1. Scope

Define requirements for the classic `(x, y)` mode implemented by:
- `front2d.py`
- `tetris_nd/game2d.py`

## 2. Current Intentions

1. Keep 2D mode as the baseline reference for gameplay correctness.
2. Keep rules simple and deterministic with seeded piece order.
3. Ensure no 3D/4D movement or rotation logic leaks into 2D gameplay.

## 3. Board and Rules

1. Coordinate system: `(x, y)`.
2. Gravity axis: `y`.
3. Setup range: width `6..16`, height`12..30`.
4. Clear rule: a line is removed only when all `x`cells at that`y` are filled.
5. `z`/`w` movement and rotation are disabled/ignored in 2D mode.

## 4. Piece Set

1. Default set: classic tetromino bag (`I,O,T,S,Z,J,L`).
2. Optional set: `random_cells_2d` (connected random cells).
3. Optional set: `debug_rectangles_2d` (simple large rectangular blocks for progression checks).
4. `random_cells_2d`defaults to`4`cells per piece and supports configurable range`3..6`.
5. Piece blocks are relative to pivot coordinates.
6. Setup menu must expose piece set selection (`classic`,`random_cells_2d`,`debug_rectangles_2d`).

## 4.1 Random-cell generator requirements (2D)

1. Generated coordinates must form a single connected component (4-neighborhood).
2. Piece coordinates must be normalized so spawn origin is deterministic.
3. Duplicate coordinate generation must be rejected and regenerated.
4. With a fixed RNG seed, generated sequence must be deterministic.
5. Generated piece bounding boxes must fit configured board width at spawn.
6. Shapes that cannot spawn on the current board must be rejected from bag generation.

## 4.2 Debug piece set requirements (2D)

1. Provide rectangular blocks such as `1x2`,`1x3`,`2x2`,`2x3`.
2. Set is intended for fast line-fill verification and progression debugging.
3. Debug set must remain deterministic under fixed seed.

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

## 6.1 Scoring verification requirements (2D)

1. Automated tests must verify score deltas for 1/2/3/4-line clears.
2. Replay tests must assert score progression remains deterministic.

## 7. Coding Best Practices (2D)

1. Keep 2D actions mapped only through `KEYS_2D` and system keys.
2. Keep gravity and locking logic inside `GameState.step`/`lock_current_piece`.
3. Keep rendering-specific effects out of game-rule modules.

## 8. Testing Instructions (2D)

Minimum required tests for 2D gameplay changes:
1. line clear + shift-down behavior,
2. hard drop correctness,
3. deterministic replay consistency,
4. key routing smoke tests,
5. scoring matrix checks,
6. random/debug piece spawn stability checks.

Relevant test files:
- `tetris_nd/tests/test_game2d.py`
- `tetris_nd/tests/test_board.py`
- `tetris_nd/tests/test_gameplay_replay.py`

## 9. Acceptance Criteria

1. 2D mode is playable start-to-finish.
2. Only `x` line fullness triggers clears.
3. ND-only keys do not alter state.
4. Tests pass under Python 3.14 compatibility checks.
5. Random-cell 2D piece set is selectable and playable without crashes.
6. Debug 2D piece set is selectable and supports easy line-fill validation.
7. Random-cell set no longer causes premature game-over due to invalid spawn shapes.
