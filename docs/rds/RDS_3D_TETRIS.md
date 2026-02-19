# 3D Tetris RDS

Status: Active v0.7 (Verified 2026-02-19)  
Author: Omer + Codex  
Date: 2026-02-18  
Target Runtime: Python 3.11-3.14 + `pygame-ce`

## 1. Scope

Define requirements for `(x, y, z)` gameplay mode implemented by:
- `front3d.py`
- `tetris_nd/front3d_game.py`
- `tetris_nd/game_nd.py`

## 2. Current Intentions

1. Deliver a readable, controllable 3D board with deterministic gameplay.
2. Keep gameplay actions separate from camera actions.
3. Keep all three projection modes usable in one session.
4. Implement 3D automatic playbot logic as a thin adapter over shared ND playbot core (see `docs/rds/RDS_PLAYBOT.md`).

## 3. Board and Rules

1. Coordinate system: `(x, y, z)`.
2. Gravity axis: `y`.
3. Typical setup defaults: `6 x 18 x 6`.
4. Clear rule: full `x-z`layer at fixed`y`.
5. Setup exposes topology preset:
6. `bounded` (default),
7. `wrap_all` (`x`/`z` wrap; gravity `y` remains bounded),
8. `invert_all` (`x`/`z` wrap with mirrored non-gravity axis mapping).
9. Setup includes hidden-by-default advanced topology controls:
10. `topology_advanced` toggle and `topology_profile_index` selector.
11. Advanced profiles may apply per-edge inversion/wrap behavior by axis.

## 4. Piece Set

1. Default set: dedicated true 3D pieces.
2. Optional set: embedded 2D pieces (`2D->3D` lift).
3. Optional set: `random_cells_3d` (connected random cells).
4. Optional set: `debug_rectangles_3d` (simple cuboids for rapid layer-fill checks).
5. Piece definitions are in `tetris_nd/pieces_nd.py`.
6. Setup menu must expose piece set source selection (`native_3d`,`embedded_2d`,`random_cells_3d`,`debug_rectangles_3d`).
7. Setup menu must expose bot planner algorithm (`AUTO/HEURISTIC/GREEDY_LAYER`), planner profile (`FAST/BALANCED/DEEP/ULTRA`), and planner budget (ms).

## 4.1 Lower-dimensional set embedding requirements (3D)

1. 2D coordinates `(x, y)`embed into 3D as`(x, y, 0)` by default.
2. Optional embedding plane selection is allowed (`xy`,`xz`,`yz`); default is`xy`.
3. After spawn, embedded pieces must support full 3D movement/rotation rules.
4. Embedding must preserve deterministic replay behavior under fixed seed.

## 4.2 Random-cell generator requirements (3D)

1. Generated coordinates must form a single connected component (6-neighborhood).
2. Default cell count is `5`, configurable range`4..8`.
3. Coordinates are normalized before spawn to maintain stable positioning.
4. Duplicate generated shapes in the same bag cycle should be avoided when feasible.
5. Generated piece bounding boxes must fit board `x/z` dimensions at spawn.
6. Spawn-invalid random pieces must be rejected and regenerated.

## 4.3 Debug piece set requirements (3D)

1. Provide simple cuboids such as `2x1x1`,`2x2x1`,`3x1x1`.
2. Set is intended for fast plane-clear validation and scoring checks.
3. Debug set must remain deterministic under fixed seed.

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
3. Zoom: `+`/`-`
4. Reset camera: `0`
5. Cycle projection: `P`

System:
1. Restart: `Y`
2. Menu: `M`
3. Quit: `Esc`
4. Toggle grid: `C`

Viewer-consistent translation requirement:
1. Arrow and movement intents are interpreted in viewer space, not fixed board axes.
2. `Left/Right` always move the active piece screen-left/screen-right.
3. `Up` always means away from the viewer.
4. `Down` always means closer to the viewer.
5. After yaw turns, movement remaps to board axes so these viewer semantics stay consistent.

Slice semantics:
1. Slicing (when enabled in view tooling) is for inspecting depth layers only.
2. Rotations must work independently of slice selection.

## 6. Rendering and UX

1. Projection modes: orthographic, perspective, and projective.
2. Grid can be toggled on/off.
3. When grid is off, a board shadow is still rendered.
4. Cleared layers should animate with a temporary ghost effect.
5. Default camera should fit the board view.
6. Pitch turns must be 90-degree relative view turns that keep an oblique 3D perception (not flat 2D collapse).
7. Piece rotation uses a soft eased visual tween (`120-180 ms` target) instead of instant snap.
8. Rotation tween is render-only; rotation legality and gameplay state changes still occur atomically in rules code.
9. Interruption handling: repeated rotate input while tweening must retarget cleanly (no flicker/back-jump).

## 7. Scoring

Shared scoring table from general RDS:
1. 1 clear: `40`
2. 2 clears: `100`
3. 3 clears: `300`
4. 4+ clears: scaled bonus

## 7.1 Scoring verification requirements (3D)

1. Automated tests must verify score deltas for single and multi-layer clears.
2. Replay tests must assert deterministic score progression.

## 8. Coding Best Practices (3D)

1. Keep 3D projection math in shared projection helpers.
2. Keep camera input handling separate from gameplay key handling.
3. Keep draw-time effects independent from rule state mutations.
4. Reuse helper pipelines for collecting faces, sorting, and drawing.
5. Reuse shared ND playbot candidate/search/eval modules; keep 3D bot-specific code to profile/config only.

## 9. Testing Instructions (3D)

Minimum required coverage after 3D changes:
1. movement + rotation key routing,
2. deterministic replay path,
3. camera key smoke behavior,
4. layer clear logic,
5. scoring matrix checks,
6. random/debug piece spawn stability checks.

Relevant tests:
- `tetris_nd/tests/test_game_nd.py`
- `tetris_nd/tests/test_pieces_nd.py`
- `tetris_nd/tests/test_gameplay_replay.py`

## 10. Acceptance Criteria

1. 3D mode is playable from menu to game-over.
2. `x-z` layer clearing works and scores correctly.
3. Camera controls do not interfere with gameplay controls.
4. Replay/smoke tests pass.
5. Embedded 2D and random-cell 3D sets are selectable and playable.
6. Debug 3D piece set is selectable and supports fast layer-fill validation.
7. Random-cell set no longer causes premature game-over due to invalid spawn shapes.
