# Graphical language P1: board skin captures

These were captured through **normal startup** (`game_bootstrap.tscn` with the
player settings store) at a 1440×900 window, using
`godot/Tet4D.Godot/tests/run_graphical_language_capture.gd`. Each run plays the
same fixed-seed game (seed 1337) with the same scripted drops, so the before
and after images show identical game state.

| File | Settings file | Theme the player gets |
| --- | --- | --- |
| `live_*d_default.png` | window size + onboarding off only | `luminous` (new default) |
| `live_*d_plain.png` | same, plus `theme.name: plain` at schema 4 | `plain` (Instrument) |

No built-in style preset is applied: opacity, grid and enclosure values are
the registry defaults every new player receives. Compare against the concept
images in `docs/design/graphical_language/`. Cockpit layout and shell chrome
are unchanged here; they belong to P2 and P3.
