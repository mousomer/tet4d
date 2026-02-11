# 4D Tetris RDS

Status: Active v0.3  
Author: Omer + Codex  
Date: 2026-02-10  
Target Runtime: Python 3.14 + `pygame-ce`

## 1. Scope

Define requirements for `(x, y, z, w)` gameplay mode implemented by:
- `/Users/omer/workspace/test-code/tet4d/front4d.py`
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_game.py`
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/game_nd.py`

## 2. Current Intentions

1. Provide a playable 4D ruleset with practical visualization.
2. Render 4D state as multiple 3D `w`-layer boards.
3. Keep controls separated into gameplay, slicing, and view/camera groups.

## 3. Board and Rules

1. Coordinate system: `(x, y, z, w)`.
2. Gravity axis: `y`.
3. Typical setup defaults: `6 x 18 x 6 x 4`.
4. Clear rule: full `x-z-w` hyperlayer at fixed `y`.
5. Lock and game-over semantics are shared with ND engine rules.

## 4. Piece Set

1. Uses a dedicated true 4D piece bag.
2. Current 4D pieces are 5-cell forms with variation on all axes (`x,y,z,w`).
3. Definitions are in `/Users/omer/workspace/test-code/tet4d/tetris_nd/pieces_nd.py`.

## 5. Controls

Gameplay (default small profile):
1. Move `x`: Left/Right
2. Move `z`: Up/Down
3. Move `w`: `,` / `.`
4. Soft drop: LShift/RShift
5. Hard drop: Space
6. Rotate `x-y`: X/Z
7. Rotate `x-z`: 1/2
8. Rotate `y-z`: 3/4
9. Rotate `x-w`: 5/6
10. Rotate `y-w`: 7/8
11. Rotate `z-w`: 9/0

Slice controls:
1. Slice `z`: `[` / `]`
2. Slice `w`: `;` / `'`

View controls:
1. Yaw turn (animated 90°): J/L
2. Pitch turn (animated 90°): I/K
3. Zoom: `+` / `-`
4. Reset view: `0`

System:
1. Restart: `R`
2. Menu: `M`
3. Quit: `Esc`
4. Toggle grid: `G`

## 6. Rendering and UX

1. 4D state is shown as a grid of projected 3D boards (one per `w` layer).
2. Active slice indices are shown in the HUD.
3. Grid can be toggled on/off for all layer boards.
4. When grid is off, each layer board still renders a board shadow.
5. Hyperlayer clear animation uses transient ghost cells across affected layers.

## 7. Scoring

Shared scoring table from general RDS:
1. 1 clear: `40`
2. 2 clears: `100`
3. 3 clears: `300`
4. 4+ clears: scaled bonus

## 8. Coding Best Practices (4D)

1. Keep 4D rule transitions in ND engine modules, not renderer modules.
2. Keep 4D key routing explicit (game vs slice vs view).
3. Avoid copy/paste drift between 3D and 4D rendering helpers.
4. Keep per-layer draw code modular (`grid/shadow`, `cells`, `clear effect`).

## 9. Testing Instructions (4D)

Minimum required coverage after 4D changes:
1. deterministic replay path,
2. movement-vs-rotation key routing checks,
3. slice key behavior,
4. dedicated 4D piece-set invariants.

Relevant tests:
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_game_nd.py`
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_pieces_nd.py`
- `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_gameplay_replay.py`

## 10. Acceptance Criteria

1. 4D mode is playable from menu to game-over.
2. Hyperlayer clear behavior is correct for `x-z-w` at each `y`.
3. Dedicated 4D piece set is used and validated by tests.
4. Replay/smoke tests pass.
