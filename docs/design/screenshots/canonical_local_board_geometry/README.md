# Canonical Local Board Geometry Screenshots

Agent-driven Godot 4.7.1 real-window evidence for Stage 54F-1. Frames were
captured from the production `res://scenes/trace_replay.tscn` path with native
fixed-seed sessions, except the explicitly labelled controlled diagnostic.
They are 3456 x 2073 Retina viewport captures from a requested 1600 x 960 real
window on Metal Forward+.

| Frame | Evidence |
| --- | --- |
| `2d_default_6x6.png` | Default 2D remains immediately planar with full local one-cell depth. |
| `2d_asymmetric_4x7.png` | Asymmetric 2D centring, grid, boundary, active/Ghost/locked readability. |
| `2d_narrow_4x6.png` | Minimum valid 2D board remains coherent. |
| `3d_default_6x10x6.png` | Default 3D volume consumes canonical cells, face grid, floor, and boundary. |
| `3d_asymmetric_4x7x5.png` | Unequal 3D axes retain correct centring and subdivisions. |
| `3d_narrow_4x6x2.png` | Minimum valid Z extent remains a readable volume. |
| `4d_standard_5x10x4x4.png` | Standard four-slice product composition. |
| `4d_asymmetric_4x7x3x2.png` | Asymmetric local volume repeated across two slices. |
| `4d_w1_4x7x2x1.png` | W=1 uses one canonical local volume without fake local/slice-axis merging. |
| `4d_multislice_4x7x2x6.png` | Six identical local geometries remain separately arranged by slice-set layout. |
| `4d_basis_xw_visible_wyz.png` | XW turn derives local `[W,Y,Z] = [2,7,3]` and `-X` slices. |
| `4d_signed_basis_visible_zy_negx.png` | ZX- turn visibly reports `+Z,+Y,-X`; sign changes orientation, not extent. |
| `controlled_structural_convergence_4x7x1.png` | Real-window direct comparison of 2D adaptation, direct 3D local geometry, and one-slice 4D local geometry after suppressing labels/active-frame differences; capture reported `structural_equal=true`. |
| `stage_54f1r/2d_fractional_endgame.png` | Stage 54F-1R production `endgame_2d_classic` at half-frame interpolation: four distinct non-origin fractional particles and visible motion trails over unchanged board geometry. |
| `stage_54f1r/3d_fractional_endgame.png` | Stage 54F-1R production `endgame_3d_classic` at half-frame interpolation: four distinct non-origin fractional particles, visible motion trails, and the particle-derived boundary-event marker. |

The complete environment, observations, automated evidence, and acceptance
boundary are in
`docs/plans/canonical_local_board_presentation_geometry_acceptance.md`.
These frames are review artifacts rather than pixel-diff golden tests or
independent human sign-off. The two `stage_54f1r` frames are the focused
agent-driven correction pass; the capture reported four distinct non-origin
particles and four moving trails in each mode, plus one event marker in 3D.
