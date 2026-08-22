# Stage 54F integrated acceptance screenshots

These frames are the durable before/after visual evidence for Stage 54F. They
were captured from Godot 4.7.1 real DisplayServer windows on Metal, using an
isolated copy of the accepted E5 baseline and an isolated copy of the Stage 54F
candidate. They are evidence for review, not pixel-diff test oracles.

## Baseline

| Frame | Finding |
| --- | --- |
| `before_live_2d_1600x960.png` | above-board spawn was visually unexplained |
| `before_live_3d_1600x960.png` | accepted 3D depth reference |
| `before_live_4d_1600x960.png` | fixed gutters, strong grid/frame, in-volume labels |
| `before_live_4d_wide_1600x960.png` | dense multi-row W layout before responsive clearance |
| `before_setup_invalid_1600x960.png` | collapsed error owner lacked redundant error treatment |
| `before_settings_focus_bottom_960x640.png` | off-screen focus did not move scroll from zero |

## Candidate

| Frame | Evidence |
| --- | --- |
| `after_live_2d_1600x960.png` | ordinary 2D, Ghost, NEXT, and collision-free spawn cue |
| `after_live_2d_large_ui_1600x960.png` | 2D hierarchy under Large UI scale |
| `after_live_3d_1600x960.png` | canonical 3D depth and subordinate grid |
| `after_live_3d_rotated_1600x960.png` | depth after representative outer-camera orbit |
| `after_live_4d_1600x960.png` | standard four-slice composition |
| `after_live_4d_occupied_1600x960.png` | dense locked cells, multi-W active/Ghost, label clearance |
| `after_live_4d_rotated_1600x960.png` | occupied 4D after camera orbit |
| `after_live_4d_wide_1600x960.png` | eight-slice responsive layout |
| `after_live_4d_compact_1600x960.png` | compact HUD density |
| `after_live_4d_detailed_1600x960.png` | detailed HUD density |
| `after_live_4d_high_contrast_1600x960.png` | High Contrast hierarchy |
| `after_live_4d_960x640.png` | requested small size, clamped to 960x660 |
| `after_live_4d_1180x760.png` | constrained window |
| `after_live_4d_1920x1080.png` | larger desktop window |
| `after_settings_960x640.png` | Settings at supported minimum |
| `after_settings_focus_bottom_960x640.png` | keyboard focus revealed the bottom reset action |
| `after_setup_invalid_1600x960.png` | ordinary invalid summary and collapsed error disclosure |
| `after_setup_invalid_hc_1600x960.png` | the same invalid state under High Contrast |

The complete checklist, environment, classification, and acceptance boundary
are in `docs/plans/stage_54f_integrated_visual_acceptance.md`.
