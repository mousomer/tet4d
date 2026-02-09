# 2D Tetris RDS

Status: Draft v0.1  
Author: Omer + Codex  
Date: 2026-02-08  
Target Runtime: Python 3.14 + `pygame-ce`

## 1. Scope

Define requirements for classic 2D gameplay mode.

## 2. Goals

1. Deliver stable, responsive classic Tetris loop.
2. Keep logic deterministic and easily testable (seeded piece order).
3. Serve as the simplest reference implementation for higher dimensions.

## 3. Board and Rules

1. Coordinate system: `(x, y)`.
2. Gravity axis: `y` (downward).
3. Default board size: `10 x 20` (setup menu allows `6..16 x 12..30`).
4. Spawn position: centered `x`, negative `y` entry.
5. Clear rule: clear full row (`x` complete) at a given `y`.
6. Only horizontal `x` rows are considered for clears in 2D mode.
7. No `z`/`w` movement or rotation exists in 2D mode.

## 4. Piece Set

1. MVP uses the classic 7 tetrominoes (`I,O,T,S,Z,J,L`).
2. Pieces are represented by relative block offsets around a pivot.

## 5. Actions

1. Move left/right.
2. Soft drop.
3. Hard drop.
4. Rotate clockwise/counter-clockwise in `x-y` plane.

## 6. Collision and Lock

1. Valid piece cells must stay in horizontal bounds (`x`).
2. Cells may be above top (`y < 0`) before lock.
3. Cells may not overlap occupied board cells at `y >= 0`.
4. Lock when gravity movement fails.
5. Game over if any locked block remains above top.

## 7. Scoring and Progression

1. 1 line: 40
2. 2 lines: 100
3. 3 lines: 300
4. 4 lines: 1200
5. Speed level (`1..10`) maps to gravity interval.

## 8. Controls (Default)

1. Left/Right: move
2. Down: soft drop
3. Space: hard drop
4. Up or X: rotate CW
5. Z: rotate CCW
6. R: restart
7. M: menu
8. Esc: quit
9. Full-keyboard profile option:
10. Move `x`: Numpad 4 / 6
11. Soft drop: Numpad 5
12. Hard drop: Numpad 0

## 9. Rendering and UX

1. Top-down grid rendering.
2. Distinct color per piece type.
3. Side panel:
4. score
5. lines
6. speed
7. controls
8. game-over prompt

## 10. Tests

1. Piece rotation correctness in 2D.
2. Boundary and collision checks.
3. Hard drop placement correctness.
4. Line clear and shift-down behavior.

## 11. Acceptance Criteria

1. Mode starts from menu and reaches playable loop.
2. Full row clears and scoring work as specified.
3. Game-over state is reached correctly.
4. Tests for 2D core logic pass on Python 3.14.
