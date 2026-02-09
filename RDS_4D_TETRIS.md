# 4D Tetris RDS

Status: Draft v0.1  
Author: Omer + Codex  
Date: 2026-02-08  
Target Runtime: Python 3.14 + `pygame-ce`

## 1. Scope

Define requirements for 4D gameplay mode using `(x, y, z, w)` coordinates.

## 2. Goals

1. Provide a playable 4D extension of Tetris rules.
2. Keep deterministic engine behavior despite added dimensional complexity.
3. Preserve usability through slice-based views and clear controls.

## 3. Board and Rules

1. Coordinate system: `(x, y, z, w)`.
2. Gravity axis: `y` (downward).
3. Default board size (MVP): `6 x 18 x 6 x 4`.
4. Spawn position: centered on `x,z,w`, negative entry on `y`.
5. Clear rule: clear full `x-z-w` hyperlayer at fixed `y`.

## 4. Piece Set

MVP:
1. Lift classic tetrominoes into 4D (extra axes initialized to `0`).
2. Allow movement and rotation through all required planes.

Post-MVP:
1. Evaluate dedicated 4D polycube/polytope set.

## 5. Actions

1. Move: `x-`, `x+`, `z-`, `z+`, `w-`, `w+`.
2. Soft drop: `y+`.
3. Hard drop: instant along `y` until lock.
4. Rotations (90-degree steps):
5. `x-y`, `x-z`, `x-w`, `y-z`, `y-w`, `z-w` (CW/CCW).

## 6. Collision and Lock

1. All non-gravity axes (`x,z,w`) must stay in bounds.
2. Gravity axis must remain below bottom bound.
3. Overlap with occupied cells is invalid for visible rows (`y >= 0`).
4. `y < 0` allowed pre-lock; lock above top triggers game-over.

## 7. View and UX Requirements

1. Primary gameplay view is slice-based:
2. 2D play surface displays `(x, y)` for selected `z,w`.
3. User can change active `z` and `w` slices.
4. Secondary visualization (optional): projected 3D hint for context.
5. HUD must show active slice indices and limits.

## 8. Controls (Default: Small Keyboard Profile)

1. Move `x`: Left/Right
2. Move `z`: Up/Down
3. Move `w`: , / .
4. Soft drop: Left Shift / Right Shift
5. Hard drop: Space
6. Rotate `x-y`: Up or X / Z
7. Rotate `x-z`: 1 / 2
8. Rotate `y-z`: 3 / 4
9. Rotate `x-w`: 5 / 6
10. Rotate `y-w`: 7 / 8
11. Rotate `z-w`: 9 / 0
12. Slice `z`: [ / ]
13. Slice `w`: ; / '
14. R: restart
15. M: menu
16. Esc: quit
17. Full-keyboard profile option:
18. Move `x`: Numpad 4 / 6
19. Move `z`: Numpad 8 / 2
20. Move `w`: Numpad 7 / 9
21. Soft drop: Numpad 5
22. Hard drop: Numpad 0

## 9. Scoring and Progression

1. Base scoring follows family table:
2. 1 clear: 40
3. 2 clears: 100
4. 3 clears: 300
5. 4+ clears: scaled bonus
6. Speed level (`1..10`) controls gravity interval.

## 10. Tests

1. 4D rotation invariants (4 steps return to original shape orientation).
2. Bounds/collision checks on `x,z,w`.
3. Hyperlayer clear and shift-down behavior.
4. Deterministic replay for scripted input sequence.

## 11. Acceptance Criteria

1. 4D mode is playable end-to-end from menu to game-over.
2. Hyperlayer clear logic is correct for `x-z-w` at each `y`.
3. Slice controls reliably inspect/navigate `z` and `w`.
4. Core 4D logic tests pass on Python 3.14.
