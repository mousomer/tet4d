# 4D Tetris RDS

Status: Active v0.7 (Verified 2026-02-19)  
Author: Omer + Codex  
Date: 2026-02-18  
Target Runtime: Python 3.11-3.14 + `pygame-ce`

## 1. Scope

Define requirements for `(x, y, z, w)` gameplay mode implemented by:
- `front4d.py`
- `tetris_nd/front4d_game.py`
- `tetris_nd/game_nd.py`

## 2. Current Intentions

1. Provide a playable 4D ruleset with practical visualization.
2. Render 4D state as multiple 3D `w`-layer boards.
3. Keep controls separated into gameplay, slicing, and view/camera groups.
4. Implement 4D automatic playbot logic as a configuration layer over shared ND playbot core (see `docs/rds/RDS_PLAYBOT.md`).

## 3. Board and Rules

1. Coordinate system: `(x, y, z, w)`.
2. Gravity axis: `y`.
3. Typical setup defaults: `6 x 18 x 6 x 4`.
4. Clear rule: full `x-z-w`hyperlayer at fixed`y`.
5. Lock and game-over semantics are shared with ND engine rules.
6. Setup exposes topology preset:
7. `bounded` (default),
8. `wrap_all` (`x`/`z`/`w` wrap; gravity `y` remains bounded),
9. `invert_all` (`x`/`z`/`w` wrap with mirrored non-gravity axis mapping).
10. Setup includes hidden-by-default advanced topology controls:
11. `topology_advanced` toggle and `topology_profile_index` selector.
12. Advanced profiles may apply per-edge inversion/wrap behavior including `w` edges.

## 4. Piece Set

1. Default set: dedicated true 4D piece bag.
2. Optional set: dedicated 4D six-cell piece bag.
3. Optional set: embedded 3D pieces (`3D->4D` lift).
4. Optional set: embedded 2D pieces (`2D->4D` lift).
5. Optional set: `random_cells_4d` (connected random cells).
6. Optional set: `debug_rectangles_4d` (simple hyper-rectangles for progression testing).
7. Current baseline 4D pieces are 5-cell forms with variation on all axes (`x,y,z,w`).
8. Definitions are in `tetris_nd/pieces_nd.py`.
9. Setup menu must expose piece set source selection (`native_4d`,`native_4d_6cell`,`embedded_3d`,`embedded_2d`,`random_cells_4d`,`debug_rectangles_4d`).
10. Setup menu must expose bot planner algorithm (`AUTO/HEURISTIC/GREEDY_LAYER`), planner profile (`FAST/BALANCED/DEEP/ULTRA`), and planner budget (ms).

## 4.1 Lower-dimensional set embedding requirements (4D)

1. 3D coordinates `(x, y, z)`embed into 4D as`(x, y, z, 0)` by default.
2. 2D coordinates `(x, y)`embed into 4D as`(x, y, 0, 0)` by default.
3. Optional embedding hyperplane selection is allowed; defaults are deterministic.
4. After spawn, embedded pieces must support full 4D movement/rotation rules.
5. Embedding must preserve deterministic replay behavior under fixed seed.

## 4.2 Random-cell generator requirements (4D)

1. Generated coordinates must form a single connected component (8-neighborhood in 4D axis-adjacent space).
2. Default cell count is `5`, configurable range`4..8`.
3. Coordinates are normalized before spawn to maintain stable positioning.
4. Duplicate generated shapes in the same bag cycle should be avoided when feasible.
5. Generated piece bounding boxes must fit board `x/z/w` dimensions at spawn.
6. Spawn-invalid random pieces must be rejected and regenerated.

## 4.3 Debug piece set requirements (4D)

1. Provide simple hyper-rectangles such as `2x1x1x1`,`2x2x1x1`,`3x1x1x1`.
2. Set is intended for fast hyperlayer-clear and scoring validation.
3. Debug set must remain deterministic under fixed seed.

## 5. Controls

Gameplay (default small profile):
1. Move `x`: Left/Right
2. Move `z`: Up/Down
3. Move `w`:`,`/`.`
4. Soft drop: LShift/RShift
5. Hard drop: Space
6. Rotate `x-y`: Q/W
7. Rotate `x-z`: A/S
8. Rotate `y-z`: Z/X
9. Rotate `x-w`: R/T
10. Rotate `y-w`: F/G
11. Rotate `z-w`: V/B

Slice controls:
1. Slice `z`:`[`/`]`
2. Slice `w`:`;`/`'`

View controls:
1. Yaw turn (animated 90°): J/L
2. Pitch turn (animated 90°): O/U
3. Zoom: `+`/`-`
4. Reset view: `Backspace`
5. View `xw -/+`: `F5`/`F6`
6. View `zw -/+`: `F7`/`F8`

View-hyperplane extension (`xw` / `zw`) requirements:
1. Camera/view-only turns in the `xw` and `zw` planes are render-space only and must not mutate gameplay coordinates/state.
2. Turns are animated and deterministic (same duration/interpolation profile as other view turns).
3. Reset view also resets accumulated `xw` / `zw` view angles.
4. Key routing remains conflict-safe with gameplay `rotate_xw` / `rotate_zw`.
5. Dedicated camera actions:
6. `view_xw_neg`,
7. `view_xw_pos`,
8. `view_zw_neg`,
9. `view_zw_pos`.

System:
1. Restart: `Y`
2. Menu: `M`
3. Quit: `Esc`
4. Toggle grid: `C`

Slicing definition and purpose:
1. Slicing is a view filter that helps inspect specific `z`/`w` layers in dense 4D scenes.
2. Slicing is not a prerequisite for rotation; gameplay rotations must work regardless of active slice.
3. Slicing exists to improve readability and debugging, not to alter physics.
4. Plain-language summary: slice = "which layer you currently look at", not "which cells exist for collisions".

Viewer-consistent translation requirement:
1. Movement intents are interpreted in viewer space for `x/z` translation.
2. `Left/Right` always move screen-left/screen-right.
3. `Up`means away from the viewer,`Down` means closer to the viewer.
4. After yaw turns, `x/z` translation remaps to board axes to preserve viewer consistency.
5. `w`movement remains bound to`,`/`.` and is not viewer-remapped.

Rotation reliability requirements (4D `z-w`):
1. `rotate_zw` (`V/B`) must be conflict-free with view/system keys.
2. Rotation attempts must not get stuck due to input routing conflicts or stale state.
3. Repeated `V/B` input should either rotate or fail cleanly with no control deadlock.
4. Seam-straddling pieces in `invert_all` must remain translatable across `w` boundaries when destination occupancy is valid.

## 6. Rendering and UX

1. 4D state is shown as a grid of projected 3D boards (one per `w` layer).
2. Active slice indices are shown in the HUD.
3. Grid can be toggled on/off for all layer boards.
4. When grid is off, each layer board still renders a board shadow.
5. Hyperlayer clear animation uses transient ghost cells across affected layers.
6. Pitch turns must remain 90-degree relative view turns while preserving a non-flat 3D board perception.
7. Piece rotation uses a soft eased visual tween (`120-180 ms` target) instead of instant snap.
8. Rotation tween is render-only; 4D collision/lock/scoring remain deterministic and discrete in engine state.
9. Rapid chained rotations (including `V/B`) must retarget/queue without visual jitter or control deadlock.
10. Exploration mode must render the same rotation tween behavior as normal mode.
11. Overlay tween cells and active-piece cells must use the same topology mapping policy (bounded/wrap/invert parity).
12. Projection cache keys must include full layer-view context (`xw`,`zw`,`w_layer`, and total `W` size) to prevent stale cross-config cache reuse.
13. Per-layer zoom fit must be calculated after hyper-view transforms and `w`-layer centering so outer layers remain visible under `xw`/`zw` turns.

Implementation structure for view `xw` / `zw`:
1. Introduce a 4D camera orientation state in renderer/view layer (separate from gameplay state).
2. Apply 4D view-plane transforms before 3D layer projection; keep slicing semantics intact.
3. Preserve existing per-layer 3D yaw/pitch controls after 4D view-plane transform.
4. Keep view transforms independent from piece movement/rotation simulation logic.
5. Keep dry-run/headless paths unchanged (view-only code excluded).
6. Base transform sequence:
7. map `(x,y,z,w_layer)` to centered 4D world coords,
8. apply `xw` camera turn,
9. apply `zw` camera turn,
10. then apply existing 3D yaw/pitch projection path.

## 7. Scoring

Shared scoring table from general RDS:
1. 1 clear: `40`
2. 2 clears: `100`
3. 3 clears: `300`
4. 4+ clears: scaled bonus

## 7.1 Scoring verification requirements (4D)

1. Automated tests must verify score deltas for single and multi-hyperlayer clears.
2. Replay tests must assert deterministic score progression.

## 8. Coding Best Practices (4D)

1. Keep 4D rule transitions in ND engine modules, not renderer modules.
2. Keep 4D key routing explicit (game vs slice vs view).
3. Avoid copy/paste drift between 3D and 4D rendering helpers.
4. Keep per-layer draw code modular (`grid/shadow`,`cells`,`clear effect`).
5. Keep 4D bot implementation thin; do not duplicate ND planner/search/candidate code.

## 9. Testing Instructions (4D)

Minimum required coverage after 4D changes:
1. deterministic replay path,
2. movement-vs-rotation key routing checks,
3. slice key behavior,
4. dedicated 4D piece-set invariants,
5. scoring matrix checks,
6. random/debug piece spawn stability checks,
7. repeated `V/B` rotation reliability checks,
8. invert-topology seam traversal regression for `w` moves on seam-straddling pieces,
9. rotation-overlay topology parity checks in exploration mode and normal mode,
10. view `xw` / `zw` key-routing and animation behavior,
11. replay determinism invariance under view-only `xw` / `zw` turns.
12. projection cache-key separation when only total `W` size changes (same xyz/layer/view angles).
13. hyper-view zoom-fit regression checks for outer `w` layers.
14. full local gate via `scripts/ci_check.sh` for renderer-affecting batches.
15. profile report via `tools/profile_4d_render.py` after projection/cache/zoom changes, with mitigation required if sparse overhead exceeds `15%` or `2.0 ms/frame`.

Relevant tests:
- `tetris_nd/tests/test_game_nd.py`
- `tetris_nd/tests/test_pieces_nd.py`
- `tetris_nd/tests/test_gameplay_replay.py`

## 10. Acceptance Criteria

1. 4D mode is playable from menu to game-over.
2. Hyperlayer clear behavior is correct for `x-z-w`at each`y`.
3. Dedicated 4D piece set is used and validated by tests.
4. Replay/smoke tests pass.
5. Embedded 2D/3D and random-cell 4D sets are selectable and playable.
6. Debug 4D piece set is selectable and supports fast hyperlayer-fill validation.
7. `V/B` rotations are stable and not consumed by unrelated actions.
8. Random-cell set no longer causes premature game-over due to invalid spawn shapes.
9. View `xw` / `zw` turns are camera-only and never alter gameplay outcomes.
10. Changing total `W` size does not reuse stale projected grid/helper caches.
11. Outer `w` layers remain in-bounds under hyper-view turns (`xw`/`zw`).

## 11. Implementation Status (2026-02-19)

Implemented in code:
1. 4D mode renders all `w`layers as multiple projected 3D boards in`tetris_nd/front4d_game.py`.
2. Grid toggle supports full projected lattice rendering per layer; grid-off draws board shadow silhouettes.
3. 4D clear animation uses ghost-cell fade overlays across affected layers.
4. `rotate_zw` (`V/B`) is conflict-safe with view/system defaults and protected from camera key override during rebinding.
5. Random 4D spawn stability improved by spawn-fit filtering and centered spawn placement in `tetris_nd/game_nd.py`.
6. Debug 4D rectangle piece set is selectable and tested.
7. Scoring matrix and random-piece stability checks are covered in `tetris_nd/tests/test_game_nd.py`.
8. Camera/view hyperplane turns for `xw` and `zw` are implemented in 4D renderer/view layer (`tetris_nd/front4d_render.py`).
9. Dedicated keybinding camera actions for these turns are implemented and conflict-safe by default:
10. `view_xw_neg/view_xw_pos/view_zw_neg/view_zw_pos`.
11. 4D projection cache keys include total `W` size, avoiding stale lattice/helper cache reuse across config changes.
12. 4D per-layer zoom fitting is hyper-view aware (accounts for `xw`/`zw` + centered `w` layer transform).
13. Black-box render-cache regression coverage exists for cross-config `W`-size changes (`tetris_nd/tests/test_front4d_render.py`).
14. 4D render profiling tooling exists and is part of projection/cache change validation (`tools/profile_4d_render.py`).
