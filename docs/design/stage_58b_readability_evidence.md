# Stage 58B readability evidence

## Scope and baseline

Approved widened scope: reclaim gameplay area from the existing cockpit, select
4D tiling by usable scale, make spacing canonical, and render at displayed pixel
resolution. Depth/contrast hierarchy belongs to 58C; W-label tracking belongs to
Stage 59. No lattice topology, Border/Full semantics, inherited native gameplay,
Stage 57 input/restart behavior or Designer A/B adoption logic changes.

Baseline: `eaa3b303` (accepted 58A), with current master `5b0e30db` already an
ancestor. Remote master was checked again during implementation and still named
`5b0e30db`. Pinned runtime: Godot `4.7.2.stable.official.ed1daf0bf`, macOS Apple M1
Pro, Metal Forward+, Retina scale 2.

## Controlled graphical measurements

Both baseline and final use the production replay shell, fixed native seed 1337,
canonical board shapes, deterministic native movement/hard-drop population,
onboarding hidden, default fitted view, Border, a 1280×720-point client area and
2560×1440 backing pixels. Cell pitch is the projected length of one normalized
world-Y unit, converted from render pixels to logical points. It measures pitch,
not the visible 0.9-unit cell face or a Python pixel-parity target.

| Board | Before viewport, pt | After viewport, pt | Before pitch, pt | After pitch, pt | Pitch gain |
| --- | --- | --- | --- | --- | --- |
| 3D `[6,10,6]` | 750×490 | 906×580 | 27.785 | 34.785 | 25.2% |
| 4D `[5,10,4,4]` | 898×266 | 970×444 | 15.017 | 23.230 | 54.7% |
| 4D `[5,10,4,7]` | 898×266 | 970×444 | 7.672 | 13.793 | 79.8% |

The 3D region grows from 39.9% to 57.0% of the window; the 4D region from 25.9%
to 46.7%. The seven-slice layout changes from 4 columns / 2 rows to 7 / 1 at
this viewport. Tall viewports still select multiple rows when those yield more
usable scale. The scorer includes canonical camera projection and the same
per-slice label/spawn clearance as Fit, rather than an arbitrary row penalty.

## Incremental attribution

Allocation changes precede scoring, spacing and resolution changes. A separate
allocation-only graphical probe restores the baseline camera and layout scorer
while keeping the new cockpit allocation.

| Board | Allocation only pitch, pt | Final pitch, pt | Additional mechanism |
| --- | --- | --- | --- |
| 3D `[6,10,6]` | 32.888 | 34.785 | Fit clearance 1.10 → 1.04 |
| 4D `[5,10,4,4]` | 23.230 | 23.230 | No default geometry change |
| 4D `[5,10,4,7]` | 12.806 | 13.793 | Scale-first tiling 4×2 → 7×1 |

The complete 3D spawn silhouette remains fitted. These controlled figures
separate allocation gains from the subsequent framing and scoring changes.

Default canonical spacing equals the previous 1.0 spacing. Removing the legacy
multiplier changes styles that previously moved slices, and has no effect on
default geometry. The render-resolution change does not change logical pitch,
viewport allocation, camera target or slice positions.

## Style and resolution matrix

Fresh defaults plus all six catalog styles were rendered for each board above,
Border and Full, default and the probe's oblique/refit view: 63 captures. All
styles have identical logical viewport sizes, default pitch, fitted camera size,
and slice anchors within each board/view. All 63 default and oblique/refitted board footprints are
unclipped (measured clip fraction 0). Rotated W-label behavior remains the separate Stage 59 finding.

At scale 2, 3D renders 1812×1160 pixels for 906×580 points; 4D renders 1940×888
pixels for 970×444 points. A texture-backed gameplay surface sizes its
SubViewport from the actual viewport stretch and canvas transform. Four-sample
3D MSAA complements native pixel density. No line-width or topology changes
substitute for resolution. A preliminary graphical pass caught that
CanvasItem.get_screen_transform alone omitted root stretch; the final mechanism
explicitly composes the viewport stretch transform with the canvas transform.

## Verification and manual review

Focused deterministic and integration checks cover candidate scale maximization,
wide/tall viewport decisions, style-invariant anchors and gaps, legacy profile
loading without geometric effects, logical allocation, and backing-pixel
resolution changes. Existing grid/style topology, native state, bounds fitting,
responsive cockpit, Designer, input and restart tests remain required.

Interactive agent review passed for 3D and 4D: movement, piece rotation, hard
drop, score updates, direct Restart Game, camera rotation and Fit View, unclipped
spawn silhouettes, and access to the scrollable rail/deck controls. The compact
rail wraps operation labels without horizontal overflow. Cell/lattice edges are
visibly sharper than the baseline; appearance hierarchy remains 58C work.
Review used an isolated production game bootstrap and real UI/keyboard events;
this records agent inspection, not a claim of user sign-off.

Verification passed:

- `CODEX_MODE=1 ./scripts/verify.sh` — normal repository gate.
- `GODOT_BIN=/Applications/Godot.app/Contents/MacOS/Godot ./scripts/verify_godot_4_7.sh`
  — all 84 replay test scripts, 59 shared topology transport parity cases and boot.

The first final Godot run exposed assertions for superseded spacing-control,
side-by-side preview, fully visible legend and logical/pixel equality contracts.
Those tests now enforce the approved layout/resolution contracts while retaining
state preservation, containment, non-overlap and clipping checks. Focused tests
and the complete rerun pass. Screenshots, probe JSON
and complete gate logs are retained under `/private/tmp/tet4d-58b/evidence/`.
The final graphical matrix is `style-matrix-rotated/records.json`; comparative
records are `baseline-graphical/records.json` and `allocation-only/records.json`.
Scale/framing is frozen after this stage; remaining depth and contrast defects
continue in 58C and rotated W-label tracking remains Stage 59.

## Publication verification (2026-10-14)

Implementation is committed at `21b361c4`, following the reference-size legend
and responsive menu corrections (`3ad116c3`, `43dda6a0`). PR #153 includes these
changes together with the earlier cockpit, lattice and Stage 57 work.

The remote run on `21b361c4` stopped in baseline planning because the ready PR
still carried active handoff metadata. Product lanes were skipped, not passed.
Finalization clears the handoff state in accordance with its existing lifecycle
contract. The normal pre-push verifier and required remote lanes must pass
before merge; the master push run supplies post-merge CI evidence. Current
remote results are linked from [PR #153](https://github.com/mousomer/tet4d/pull/153).

This publication step does not change scale, geometry, styling or gameplay.
Owner visual acceptance remains distinct from the recorded agent inspection.

The first publication rerun passed every other selected product lane but the
Godot replay suite exceeded its 900-second aggregate budget after reaching
script 78/84, with no reported assertion failure. Publication gives this suite
a separate bounded 1800-second budget, retaining all tests and the 900-second
watchdog for other Godot steps. A fresh complete run is required; the timed-out
run is not acceptance evidence.

## Amendment: drawn-board allocation (2026-10-25)

The 2D/3D side rail now grows into width the right-anchored board leaves
unused, so NEXT/HOLD names and the 3D MOVE row stop trimming and wrapping.
That narrows the gameplay viewport rect without changing the board the player
sees: the board is fitted by its height and anchored beside the rail. The
viewport-rect share was a proxy for that board and no longer tracks it, so the
58B allocation contract now measures the drawn board.

- Measure: the fitted content's projected span at the orthographic scale,
  in logical points (`CameraRig.drawn_content_size`).
- Share at 1280×720: 3D 0.194 and 4D 0.340 of the window, against floors of
  0.18 and 0.32. The earlier 55%/35% floors were viewport-rect shares.
- Preserved: the drawn board is identical across all six styles even when a
  style's fonts resize the rail and so the viewport rect (3D measured 320×558
  points with viewports of 655, 736 and 752 points width).
- Not narrowed: the Live 3D fit must stay height-limited
  (`CameraRig.fitted_height_limited`); a rail that cut into the board would
  make it width-limited and shrink what is drawn.

Pitch is unchanged: the viewport height (580 points at 1280×720 for 3D) and the
fit are unchanged, and only the empty width beside the board moved to the rail.
`tests/test_stage_58b_readability.gd` carries these assertions.
