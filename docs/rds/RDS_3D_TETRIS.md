# 3D Tetris RDS

Status: Active v0.4  
Author: Omer + Codex  
Date: 2026-02-12  
Target Runtime: Python 3.14 + `pygame-ce`

## 1. Scope

Define requirements for `(x, y, z)` gameplay mode implemented by:
- `/Users/omer/workspace/test-code/tet4d/front3d.py`
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_game.py`
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/game_nd.py`

## 2. Current Intentions

1. Deliver a readable, controllable 3D board with deterministic gameplay.
2. Keep gameplay actions separate from camera actions.
3. Keep all three projection modes usable in one session.

## 3. Board and Rules

1. Coordinate system: `(x, y, z)`.
2. Gravity axis: `y`.
3. Typical setup defaults: `6 x 18 x 6`.
4. Clear rule: full `x-z` layer at fixed `y`.

## 4. Piece Set

1. Default set: dedicated true 3D pieces.
2. Optional set: embedded 2D pieces (`2D->3D` lift).
3. Optional set: `random_cells_3d` (connected random cells).
4. Piece definitions are in `/Users/omer/workspace/test-code/tet4d/tetris_nd/pieces_nd.py`.
5. Setup menu must expose piece set source selection (`native_3d`, `embedded_2d`, `random_cells_3d`).

## 4.1 Lower-dimensional set embedding requirements (3D)

1. 2D coordinates `(x, y)` embed into 3D as `(x, y, 0)` by default.
2. Optional embedding plane selection is allowed (`xy`, `xz`, `yz`); default is `xy`.
3. After spawn, embedded pieces must support full 3D movement/rotation rules.
4. Embedding must preserve deterministic replay behavior under fixed seed.

## 4.2 Random-cell generator requirements (3D)

1. Generated coordinates must form a single connected component (6-neighborhood).
2. Default cell count is `5`, configurable range `4..8`.
3. Coordinates are normalized before spawn to maintain stable positioning.
4. Duplicate generated shapes in the same bag cycle should be avoided when feasible.

## 5. Controls

Gameplay (default small profile):
1. Move `x`: Left/Right
2. Move `z`: Up/Down
3. Soft drop: LShift/RShift
4. Hard drop: Space
5. Rotate `x-y`: Q/W
6. Rotate `x-z`: A/S
7. Rotate `y-z`: Z/X

Camera/view:
1. Yaw turn (animated 90°): J/L
2. Pitch turn (animated 90°): I/K
3. Zoom: `+` / `-`
4. Reset camera: `0`
5. Cycle projection: `P`

System:
1. Restart: `R`
2. Menu: `M`
3. Quit: `Esc`
4. Toggle grid: `G`

## 6. Rendering and UX

1. Projection modes: orthographic, perspective, and projective.
2. Grid can be toggled on/off.
3. When grid is off, a board shadow is still rendered.
4. Cleared layers should animate with a temporary ghost effect.
5. Default camera should fit the board view.

## 7. Scoring

Shared scoring table from general RDS:
1. 1 clear: `40`
2. 2 clears: `100`
3. 3 clears: `300`
4. 4+ clears: scaled bonus

## 8. Coding Best Practices (3D)

1. Keep 3D projection math in shared projection helpers.
2. Keep camera input handling separate from gameplay key handling.
3. Keep draw-time effects independent from rule state mutations.
4. Reuse helper pipelines for collecting faces, sorting, and drawing.

## 9. Testing Instructions (3D)

Minimum required coverage after 3D changes:
1. movement + rotation key routing,
2. deterministic replay path,
3. camera key smoke behavior,
4. layer clear logic.

Relevant tests:
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_game_nd.py`
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_pieces_nd.py`
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_gameplay_replay.py`

## 10. Acceptance Criteria

1. 3D mode is playable from menu to game-over.
2. `x-z` layer clearing works and scores correctly.
3. Camera controls do not interfere with gameplay controls.
4. Replay/smoke tests pass.
5. Embedded 2D and random-cell 3D sets are selectable and playable.
