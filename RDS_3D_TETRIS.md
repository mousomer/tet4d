# 3D Tetris RDS

Status: Draft v0.2  
Author: Omer + Codex  
Date: 2026-02-08  
Target Runtime: Python 3.14 + `pygame-ce`

## 1. Scope

Define requirements for 3D gameplay mode using `(x, y, z)` coordinates.

## 2. Goals

1. Deliver a clear and playable 3D Tetris experience.
2. Keep deterministic rules and stable controls.
3. Maintain separation between gameplay controls and camera controls.

## 3. Board and Rules

1. Coordinate system: `(x, y, z)`.
2. Gravity axis: `y` (downward).
3. Default board size (MVP): `6 x 18 x 6`.
4. Spawn position: centered on `x,z`, negative entry on `y`.
5. Clear rule: clear full `x-z` layer at fixed `y`.
6. default camera: projective transform. Enable orthographic projection and perspective projection.

## 4. Piece Set

MVP:
1. Reuse classic 7 tetrominoes lifted into 3D (`z=0` initialization).
2. Support movement and rotation in 3D space.

Post-MVP:
1. Evaluate true 3D tetracube set.

## 5. Actions

1. Move: `x-`, `x+`, `z-`, `z+`.
2. Soft drop: `y+`.
3. Hard drop: instant drop and lock.
4. Rotations (90-degree):
5. `x-y`, `x-z`, `y-z` (CW/CCW).

## 6. Collision and Lock

1. `x` and `z` must stay in bounds.
2. `y` may be negative before lock, but not below board bottom.
3. Occupied-cell overlap is invalid when `y >= 0`.
4. Lock piece when gravity step fails.
5. Trigger game-over if any locked cell remains above top.

## 7. Controls (Default)

1. Move `x`: Left/Right
2. Move `z`: Up/Down
3. Soft drop: Left Shift / Right Shift
4. Hard drop: Space
5. Rotate `x-y`: Q / W
6. Rotate `x-z`: A / S
7. Rotate `y-z`: Z / X
8. Restart: R
9. Menu: M
10. Quit: Esc
11. Full-keyboard profile option:
12. Move `x`: Numpad 4 / 6
13. Move `z`: Numpad 8 / 2
14. Soft drop: Numpad 5
15. Hard drop: Numpad 0

## 8. Camera Controls

1. Orbit yaw: J/L
2. Orbit pitch: I/K
3. Zoom: +/- 
4. Reset camera: 0
5. Cycle projection mode: P
6. Camera keys must not conflict with core movement keys.

## 9. Rendering and UX

1. Use software 3D projection with `pygame-ce`.
2. Draw cells as projected cubes/quads with depth ordering.
3. HUD includes:
4. Score
5. Cleared layers
6. Speed level
7. Controls summary
8. Game-over instructions

## 10. Scoring and Progression

1. 1 clear: 40
2. 2 clears: 100
3. 3 clears: 300
4. 4+ clears: scaled bonus
5. Speed level (`1..10`) controls gravity interval.

## 11. Tests

1. 3D rotation invariants.
2. Bounds/collision behavior.
3. Hard drop and lock correctness.
4. Layer clear and shift-down correctness.
5. Deterministic replay test from fixed seed.

## 12. Acceptance Criteria

1. Mode is fully playable from menu to game-over.
2. `x-z` layer clear logic works as specified.
3. Camera controls function without breaking gameplay control mapping.
4. 3D logic tests pass on Python 3.14.
