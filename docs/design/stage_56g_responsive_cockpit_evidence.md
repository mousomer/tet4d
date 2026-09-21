# Stage 56G responsive cockpit evidence

Stage 56G makes the existing shared `LiveCockpit` responsive without creating
dimension-specific layouts. The policy is presentation-only: available width
selects one of four deterministic profiles, and the profile adjusts deck
height, spacing, and the three existing module shares. Module identity and
order remain `PIECE | VIEW | PIECE STATE` in 2D, 3D, and 4D.

## Automated matrix

`test_stage_56g_responsive_cockpit.gd` renders the production scene inside
real per-case `SubViewport`s. This avoids the fixed 1600×960 headless root that
previously made a resized child `Control` look responsive without changing its
actual viewport.

| Case | Viewport | Profile | Required result |
| --- | ---: | --- | --- |
| Wide desktop | 1920×1080 | `wide` | Full 42/33/25 deck allocation. |
| Standard desktop/laptop | 1440×900 | `standard` | Full deck with standard height and spacing. |
| Narrow window | 960×640 | `narrow` | Tighter spacing and bounded deck height. |
| Small supported viewport | 634×624 | `small` | Compact deck at the declared shell floor. |

Every case enters Live 2D, Live 3D, and Live 4D and verifies a nonzero legible
game viewport, board/deck separation, module containment and ordering, and a
visible HOLD/NEXT row contained by PIECE STATE. The same gate retains the
existing source-boundary and deterministic-state checks.

The single `AdaptiveLayerLayout` allocator is also exercised at four board
areas for 6, 7, and 8 slices. Every result is repeated for deterministic
equality, keeps at most two rows, contains all tile rectangles, and has no tile
overlap. The reference 1600×960 choices remain 6→3×2, 7→4×2, and 8→4×2.

The existing `test_live_4d_orientation_rosette.gd` remains the authoritative
state-consumption acceptance. It covers XZ, XW, and ZW exact turns, continuous
yaw and pitch, passive redraw, and Reset View against the app-owned
presentation snapshot while proving native state/hash isolation. Stage 56G
does not introduce another orientation model.

## Real-window visual review

The captures below were produced by Godot 4.7.2 through the macOS DisplayServer
and Metal on Apple M1 Pro. Standard and narrow captures cover representative
desktop widths. The 634-pixel capture is an additional constrained-height
stress case; exact 634×624 supported-floor geometry is covered by the automated
matrix above.

| Mode | Standard | Narrow | Constrained stress |
| --- | --- | --- | --- |
| Live 2D | [1440×864](screenshots/stage_56g_responsive_cockpit/live_2d_standard.png) | [960×576](screenshots/stage_56g_responsive_cockpit/live_2d_narrow.png) | [634×380](screenshots/stage_56g_responsive_cockpit/live_2d_small.png) |
| Live 3D | [1440×864](screenshots/stage_56g_responsive_cockpit/live_3d_standard.png) | [960×576](screenshots/stage_56g_responsive_cockpit/live_3d_narrow.png) | [634×380](screenshots/stage_56g_responsive_cockpit/live_3d_small.png) |
| Live 4D | [1440×864](screenshots/stage_56g_responsive_cockpit/live_4d_standard.png) | [960×576](screenshots/stage_56g_responsive_cockpit/live_4d_narrow.png) | [634×380](screenshots/stage_56g_responsive_cockpit/live_4d_small.png) |

Visual inspection found the primary game surface dominant at standard and
narrow widths, all three semantic modules reachable, HOLD/NEXT visually
adjacent, and no board/deck or module overlap. The 3D and 4D orientation
rosettes remain visible at the lower left. The 4D W slices retain monotonic
left-to-right order and legible active-slice emphasis. Even the below-floor
height stress retains the structural hierarchy without wrapping the deck into
a second cockpit framework. Key-chip weight and long-play scan comfort remain
Stage 56H concerns rather than geometry repairs.

## Boundary result

No gameplay command, binding, camera/basis semantic, renderer owner, native
session, queue/Hold model, deterministic state, or profile persistence contract
changes in Stage 56G. The layout is stable enough for Stage 56H to focus on
playability and control-deck presentation rather than another structural
layout redesign.
