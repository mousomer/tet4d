# Stage 56B Slice-Tiling Evidence

Status: focused-green on 2026-09-07. This is presentation evidence, not a new
gameplay or layout-authority transfer.

## Deterministic reference measurements

The candidate oracle used a `1600×960` board viewport and the stable local
orientation envelope `[8, 16, 5]`. Every result is row-major, inside the
viewport, non-overlapping, and independent of active slice and occupancy.

| Slice count | Selected grid | Projected scale | Unused viewport area |
| ---: | ---: | ---: | ---: |
| 5 | 3×2 | 22.248823 | 750153.128 |
| 6 | 3×2 | 22.248823 | 750153.128 |
| 7 | 4×2 | 22.248823 | 457979.421 |
| 8 | 4×2 | 22.248823 | 457979.421 |

The reference tile envelope is `9.433981×18.574175`, with horizontal gap
`4.245291` and vertical gap `6`. Candidate scoring maximizes projected scale,
then applies the explicit two-row and balanced-final-row preferences. Those
preferences intentionally reject a superficially larger but fragmented row
when the expected Live-4D count can form a coherent two-row scan.

## Real cockpit A/B

The runtime captures used the actual settled HUD game area, `1576×604`. The
temporary comparison variants altered candidate selection or partial-row
alignment only; none of those overrides exists in production code.

| Comparison | Selected result | Comparison result | Decision |
| --- | --- | --- | --- |
| 6 slices | 3×2, scale `12.754280`, unused `668469.609` | 4+2, scale `13.347328`, unused `545011.156` | Keep 3×2: balanced scan wins the declared final-row preference. |
| 7 slices | 4+3 left, scale `12.754280`, unused `563090.202` | 4+3 centered, scale `12.477088`, unused `571540.384` | Keep left: stable columns and a measurably larger oblique fit. |
| 8 slices | 4×2, scale `12.211690`, unused `579631.049` | 5+3, scale `12.754280`, unused `457710.767` | Keep 4×2: two complete rows avoid the old imbalanced tail. |

### Captures

Six slices: [selected 3×2](screenshots/stage_56b_slice_tiling/new_6_3x2.png)
and [rejected 4+2](screenshots/stage_56b_slice_tiling/compare_6_4plus2.png).

Seven slices: [selected left-aligned 4+3](screenshots/stage_56b_slice_tiling/new_7_4plus3_left.png)
and [centered comparison](screenshots/stage_56b_slice_tiling/compare_7_4plus3_centered.png).

Eight slices: [selected 4×2](screenshots/stage_56b_slice_tiling/new_8_4x2.png)
and [rejected 5+3](screenshots/stage_56b_slice_tiling/old_8_5plus3.png).

## Bounded integration repair 56B-R

The stretched render SubViewport briefly reported `120×2` during startup. If
that transient size became the layout input, eight slices selected an `8×1`
grid and no later event invalidated the cached layout. `ReplayHud` now exposes
the stable game-area size and emits geometry changes; `TraceReplayApp` routes
that size to `TraceSceneRenderer`, which invalidates only Live-4D presentation
fit and layout. Focused runtime evidence verifies that the renderer consumes
the HUD viewport and resolves the required count-derived grids after startup.
Routing is idempotent for repeated equal sizes, and a genuine later geometry
change preserves a player's manual framing instead of silently reapplying Fit.
