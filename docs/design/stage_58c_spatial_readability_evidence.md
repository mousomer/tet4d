# Stage 58C spatial readability evidence

## Scope and baseline

Goal: a player reads the 3D/4D board fast enough to think about the move rather
than decode the display. Target hierarchy: active > settled > contextual > grid.
Scope is renderer presentation only. Grid modes keep their semantics and
topology, 58B layout and framing are unchanged, no gameplay, native, state,
hash, timing or replay path changes, and no setting or slider is added.

Baseline: `eda7b4ec` (PR #153 merge). Evidence environment: Godot
`4.7.2.stable.official.ed1daf0bf`, Linux, Vulkan Forward+ on Mesa lavapipe
under Xvfb, MSAA 4×, 1× pixel density. The 58B evidence used macOS Metal at
2×; absolute colours and antialiasing can differ there, while the role,
depth and slice orderings measured here do not depend on the platform.

## Method

`godot/Tet4D.Godot/tests/run_spatial_readability_capture.gd` renders fixed
board states through the production renderer, canonical outer views,
`TraceReplayApp._fit_view()` rules, light and environment:

```bash
xvfb-run -a Godot --rendering-driver vulkan --path godot/Tet4D.Godot \
  --script tests/run_spatial_readability_capture.gd -- /abs/out [scenes= styles= grids= sizes= colors= scale= masks=]
```

- 3D `[6,10,6]`: fresh, sparse, moderate, dense, active in front of a settled
  wall, active partly behind one (about 40% visible), and a floating piece
  overlapping a distant column in projection. 4D `[5,10,4,4]`: fresh, sparse,
  several populated slices, dense, sparse active slice between dense
  neighbours, a piece spanning two slices; `[5,10,4,7]`: seven slices.
- Purple active piece by default, also present among settled colours; a
  colour sweep covers palette colours 1-7. Ghosts are explicit fixture data.
- Fresh defaults plus all six styles, None/Border/Full, at the 58B 1280×720
  board regions (3D 906×580, 4D 970×444 pt), and the regions the live shell
  gives a 1728×1080 window (1036×660, 1085×463) and the 720×600 small profile
  (740×418, 1010×264).
- Five flat-material passes, keeping each material's draw-order state, give
  each cell's owned pixels and mean composite CIELAB, the active footprint, the
  light reaching it through all occluders and through lattice only, and
  lattice ink. ΔL* compares the active piece with same-colour settled cells.
  Depth slope regresses colour-normalised settled L* on camera depth
  normalised over the board box. Slice residuals average colour-normalised
  settled L* by distance from the active slice.

These are screen-space proxies supporting inspection, not perceptual truth.

## Baseline diagnosis

- Salience: 3D ΔL* 17-29 across styles; 4D −1 to 19, about 0 in the sparse
  4D scene for 5 of 7 styles. Blue was weakest (3D ΔL* 9.4-16.5, ΔE 12.6 in
  Python Reference; 4D 1.8-11.2). Material lightness gives active about twice
  settled, but ambient 1.85 plus sun 2.2 with linear tonemapping saturates the
  dominant channel of both, compressing the luminance ratio from about 8× to
  1.6-2.5×. Stage 23c's 4D-only material also darkened 4D active pieces, and
  the 4D view sees their darker back/left faces.
- Depth: settled L* slopes over board depth −9.9..+5.4 with no consistent
  sign; a piece floating three cells in front of a column read as resting on it.
- Occlusion: the behind scene shows 39-41% of the active piece in every style;
  every other scene shows at least 84% (dense, High Contrast, Full).
- 4D slices: per-style mean residual settled L* between −2.0 and +0.6 at every
  distance (single cases within ±4) and lattice ink equal within 10% per
  slice; only the active frame and label marked the active slice.
- Grid: Full has about twice Border's lattice ink. Full's front lines crossed
  an opaque active piece (4-10% of its light) but sat beneath translucent
  settled cells, inverting the hierarchy; Blueprint Technical, whose active
  opacity 0.88 already used the alpha path, lost 0-2%.

## Changes

| Step | Change | Files |
| --- | --- | --- |
| 58C.1 | Live 3D and 4D active pieces share one exterior material; the 4D-only darkened variant and its dead twin are removed | `scripts/ui/replay_visuals.gd`, `scripts/rendering/trace_scene_renderer.gd` |
| 58C.2 | Live 3D/4D settled cells take `lerp(1, 0.75, d)`, d = camera-space depth normalised over their board or slice box, as a colour scale; active never weighted | `scripts/presentation/spatial_readability.gd`, `scripts/rendering/cell_renderer.gd`, `trace_scene_renderer.gd`, `scripts/presentation/projection_layout.gd`, `board_presentation_model.gd` |
| 58C.4 | Live 4D settled cells and slice scaffold take `0.6 + 0.4·0.5^d`, d = distance to the nearest active slice; scaffold uses instance transparency | `spatial_readability.gd`, `trace_scene_renderer.gd`, `scripts/rendering/grid_renderer.gd` |
| 58C.5 | Active faces always use the depth-writing alpha path, so scaffold composites beneath them as it does beneath translucent settled cells | `replay_visuals.gd` |

Depth weights depend only on the camera direction in board space; they are
recomputed when that direction changes, never from frame time, and ignore zoom,
window size and camera distance. Slice weights are symmetric, take the minimum
over a spanning piece, and leave every slice at 1.0 without an active piece,
like the active frame. Weights are quantised to 1/128 so camera motion rewrites
a cell's materials only when its weight changes. Replays keep their baseline
presentation: their settled cells share one material per board, so
`recession_layers()` limits recession to live boards, whose cells own their
materials.

Rejected, one variable at a time, on a 42-case colour sweep: a uniform active
lift of 0.22 or 0.30 (blue ΔL* +8/+17 but bright hues lose chroma; at 0.30
active chroma falls below settled); an OKHSL active lightness floor of 0.62 or
0.55 (blue washes towards white-cyan and loses its identity); settled
darkening 0.55 (blue stays clipped, settled hue distinctness drops); ambient
energy 1.2 (blue unchanged, 4D worse). Rear depth weights 0.8 and 0.7 gave
mean slopes −6.9 and −9.2 L*; 0.75 gives −8.1 on that subset.

58C.3: no occlusion change. The behind scene is correct 3D occlusion (still
40-41% visible after 58C.5); showing hidden parts through cells would add new
visual language. The depth weight darkens the column behind the overlap
scene's floating piece, and the ghost remains its landing cue.

## Results

Light reaching the active piece under Full, minimum over scenes: before
0.90-0.98, after 0.97-0.99; Border and None 1.00. Full keeps about twice
Border's ink in every style.

| Board / style | ΔL* min (colour) / mean, before | after |
| --- | --- | --- |
| 3D default | 9.4 (blue) / 20.7 | 13.4 (blue) / 27.2 |
| 3D Python Reference | 10.8 (blue) / 20.1 | 14.3 (blue) / 26.6 |
| 3D Tron Grid Flow | 16.5 (blue) / 26.3 | 19.3 (blue) / 31.9 |
| 4D default | 1.8 (blue) / 16.0 | 15.9 (blue) / 35.2 |
| 4D Python Reference | 9.2 (blue) / 20.4 | 22.0 (blue) / 39.0 |
| 4D Tron Grid Flow | 11.2 (blue) / 23.1 | 22.8 (blue) / 40.3 |

| Style (Border) | 3D depth slope, before mean (range) | after | 4D slice residual d0 / d1 / d2, after |
| --- | --- | --- | --- |
| Default | 1.2 (−2.6..3.1) | −5.2 (−11.3..−1.5) | +5.2 / −0.1 / −4.9 |
| Python Reference | −4.6 (−9.3..−0.6) | −10.4 (−16.1..−5.2) | +5.4 / +0.0 / −5.1 |
| Arcade Neon | 1.7 (−1.9..5.1) | −4.9 (−10.8..−0.7) | +4.8 / +0.1 / −5.0 |
| Tron Grid Flow | −3.9 (−8.4..0.4) | −8.5 (−15.1..−2.6) | +4.6 / +0.2 / −4.7 |
| Blueprint Technical | −5.2 (−9.9..−0.6) | −10.4 (−16.9..−4.0) | +5.9 / −0.1 / −5.1 |
| High Contrast | 1.0 (−2.9..2.9) | −5.3 (−11.5..−2.0) | +5.0 / −0.0 / −4.9 |
| Tet4D Balanced | 2.5 (−1.3..5.4) | −4.4 (−10.4..−1.6) | +4.8 / +0.1 / −5.0 |

All 42 3D Border cases now have a negative depth slope. Baseline 4D residuals
were −2.0..+0.6 at every distance. Large and compact regions repeat the
orderings; slopes and slice spreads vary by up to 3 L* from pixel sampling,
while the weights themselves are resolution-independent by construction and
test.

Cost in this CPU-rendered container: re-weighting all 560 settled cells of a
dense `[5,10,4,7]` board takes about 9 ms, about 1.5% of that board's snapshot
rebuild, and the slice lookup adds about 4 ms; orbit steps average 1.2-1.4 ms
and reach 8-11 ms only when every weight changes at once. A 144-cell 3D board
takes 0.3 ms per step. Metal was not profiled.

## Python reference comparison (58C.6)

Python uses the same orthographic outer view and default locked opacity 0.75,
has no depth cue, and does not emphasise the active 4D layer. Its advantage is
figure/ground polarity: the active piece is opaque, painted after every
settled face so it is never hidden, and outlined 2 px white; settled faces form
one translucent layer with near-black 1 px outlines; each 4D layer has its own
framed panel. Godot gave both roles a similar light, sub-pixel outline and let
scaffold cross only the opaque active piece. 58C transfers the underlying
benefit, a consistent active > settled > scaffold ordering, through the
existing materials rather than Python's painter order or constants.

## Tests and verification

`tests/test_stage_58c_spatial_readability.gd` asserts active faces stay
lighter than same-colour settled faces for every palette colour, face and
theme; scaffold materials sort beneath active faces without writing depth;
depth and slice weight bounds, monotonicity, symmetry and placement/scale
invariance; rendered near/far and slice orderings; unchanged weights under
zoom, window size and camera distance; swapped weights from the opposite
side; scaffold following active slices without a rebuild; unchanged grid
topology; and a 4D replay under a camera whose settled colours, weights and
scaffold stay unchanged beside an active piece. Inverting either weight
function, restoring opaque active faces, or letting replays recede by slice
or depth fails it (5-23 findings each). Existing renderer tests now compare
settled colours at their presentation weight and require visually opaque
active faces on the alpha path.

Gates on `96aa5246`, the last code commit, in the Linux evidence container:

- `GODOT_BIN=<pinned 4.7.2> ./scripts/verify_godot_4_7.sh`: 84 of 85 replay
  scripts clean, no script errors or teardown leaks. The failure,
  `test_cockpit_density_control_hierarchy.gd` "must not mutate deterministic
  Live 4D state", fails identically alone on unmodified `eda7b4ec`: the app
  ticks 0.5 s gravity on real frame time (an idle session changed its hash
  after about 475 ms here), and this container spends longer than that in
  the Designer interactions between the test's two hash reads.
- The gate stops at that step, so its remaining steps ran separately:
  `tests/run_topology_transport_parity.gd` plus
  `tools/migration/compare_topology_transport.py` passed 59 shared cases, and
  headless boot (`--quit-after 5`) ran without script errors or leaks.
- `CODEX_MODE=1 ./scripts/verify.sh` on the branch head: governance fails only
  `native_cpp_tooling`, because the image's clang-format 18.1.3 flags the
  untouched `native/tet4d_core/include/tet4d_core/board_extent_contract.hpp`
  (also on `eda7b4ec`). With that binary hidden, so the check skips as on
  machines without clang-format, the full gate reports `verify: OK`.
- The 58C, renderer and live-presentation regression scripts pass at every
  renderer commit.

## Manual evidence

Agent inspection of the matrix contact sheets: inactive 4D slices read as
context while staying legible; the framed active slice and its piece lead;
rear 3D cells are slightly darker; Full lines no longer cross the active
piece; None remains understandable through the enclosure. Owner play
acceptance (58C.7) remains outstanding: dense 3D near-axis orbit, a piece in
the middle of a populated seven-slice board, and every style under Full.

## Remaining and deferred

- Dark active hues keep the smallest margin (3D blue ΔL* 13-19).
- Tron Grid Flow's background still shows through the board (style-owned).
- Cell outlines are about 0.5 px at 3D and 0.2-0.3 px at 4D pitch at 1×, so
  they cannot carry Python's outline polarity.
- Board framing and the 3D side rail remain 58D; W-label tracking Stage 59.
