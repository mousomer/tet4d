# Godot visual consolidation acceptance baseline

These captures are the durable human-review baseline for the Godot visual
system introduced by PR #39. They document the accepted foundation immediately
before consolidation and the candidate Instrument system at commit `7249900a`.

The `before_*` set covers the prior main menu, setup, settings, live 2D, live
3D, live 4D, and wide-W presentation. The `after_*` set covers equivalent
states plus High Contrast and a reproducible terminal game-over state.

The Pygame reference captures remain at the repository root:

- `img.png`: wide-W 4D gameplay;
- `img_1.png`: Topology Playground;
- `img_2.png`: 4D gameplay detail.

These images are review evidence, not pixel-perfect golden tests. The semantic
visual roles and composition rules remain authoritative in
`docs/design/godot_visual_system.md`.
