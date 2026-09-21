# Stage 56G responsive cockpit evidence

Stage 56G-R repairs the responsive acceptance claim while preserving one
shared `LiveCockpit` for Live 2D, 3D, and 4D. Apparent client width selects the
wide, standard, narrow, or small profile. Measured module minimums then flow
the existing `PIECE | VIEW | PIECE STATE` order across bounded rows; a capped
vertical scroller keeps the whole deck reachable without overlapping the
primary board. Header actions use ordered flow containers for the same reason.

## Why the first evidence was insufficient

The original Stage 56G matrix mounted the production scene under child
`SubViewport`s. That was useful structural coverage, but it did not reproduce
the shipped root-window `canvas_items` stretch behavior: the logical shell
could remain 1600×960 while a smaller window merely scaled it. The three
capture sizes consequently showed scaled versions of effectively one layout,
and the containment assertions checked modules inside an already-overflowing
deck rather than the deck inside the usable window. Those results are not used
as responsive acceptance.

## Production-equivalent matrix

Run the focused gate with a windowed DisplayServer:

```sh
/Applications/Godot.app/Contents/MacOS/Godot \
  --path godot/Tet4D.Godot \
  --script res://tests/run_responsive_acceptance.gd
```

The gate explicitly rejects headless execution. It drives the real root
window through six point sizes in every live dimension, then checks five
additional transitions while a live session is already active.

| Client size | Expected profile |
| ---: | --- |
| 1728×1080 | `wide` |
| 1440×900 | `standard` |
| 1200×800 | `standard` |
| 1000×720 | `narrow` |
| 860×640 | `narrow` |
| 720×600 | `small` |

Every case requires the live header, gameplay viewport, control deck, and all
visible header actions to remain inside the usable window. It also requires
board/deck separation, at least 55% window width and 30% window height for the
gameplay viewport, preserved module order and containment, grouped HOLD/NEXT,
and scrolling only when the deck's natural height genuinely exceeds its cap.

The headless suite retains deterministic source, structure, input, and state
coverage. Camera fitting now consumes per-slice content boxes rather than one
sparse collection AABB, so a multi-slice 4D board occupies the responsive
viewport without changing camera, basis, or gameplay ownership.

## Real-window visual review

The captures below were produced by Godot 4.7.2 through the macOS
DisplayServer and Metal on Apple M1 Pro. Sizes are client points; the PNGs use
the corresponding 2× Retina backing dimensions.

| Mode | Standard 1440×900 | Narrow 1000×720 | Small 720×600 |
| --- | --- | --- | --- |
| Live 2D | [capture](screenshots/stage_56g_responsive_cockpit/live_2d_standard.png) | [capture](screenshots/stage_56g_responsive_cockpit/live_2d_narrow.png) | [capture](screenshots/stage_56g_responsive_cockpit/live_2d_small.png) |
| Live 3D | [capture](screenshots/stage_56g_responsive_cockpit/live_3d_standard.png) | [capture](screenshots/stage_56g_responsive_cockpit/live_3d_narrow.png) | [capture](screenshots/stage_56g_responsive_cockpit/live_3d_small.png) |
| Live 4D | [capture](screenshots/stage_56g_responsive_cockpit/live_4d_standard.png) | [capture](screenshots/stage_56g_responsive_cockpit/live_4d_narrow.png) | [capture](screenshots/stage_56g_responsive_cockpit/live_4d_small.png) |

Visual inspection confirms that the standard layout uses two deck rows, the
narrow and small layouts flow to additional ordered rows, and vertical deck
scrolling exposes content that cannot fit simultaneously. Header actions wrap
inside the small shell. The primary board remains distinct and useful; 4D
slices keep monotonic left-to-right order and visible active-slice emphasis.

## Boundary result

The repair changes presentation geometry and evidence only. It does not add a
gameplay command, binding, camera/basis semantic, renderer owner, native
session mutation, queue/Hold model, deterministic-state change, or profile
persistence contract. Stage 56H remains the human long-play and key/action
legibility gate; Stage 56I and the final human A/B decision remain separate.
