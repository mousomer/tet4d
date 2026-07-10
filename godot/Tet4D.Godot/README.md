# Tet4D Godot Front End

This Godot 4.6.3 project is the partial migration of Tet4D into a demo front
end and future product shell.

It currently supports:

- `Replay Demos` for exported gameplay, topology, and endgame traces
- `Live Plain 2D`
- `Live Plain 3D`
- `Live Plain 4D`

Python remains the fuller current playable/reference implementation. The
Topology Playground stays in the Python launcher, and this shell is not yet
feature-complete against the Python game.

## Quick Start

From the repo root:

```bash
./scripts/build_godot_tet4d_core.sh
godot --path godot/Tet4D.Godot
```

Headless tests:

```bash
godot --headless --path godot/Tet4D.Godot --script tests/run_tests.gd
```

## What The Shell Does

- Presents the main menu, replay browser, viewer, controls, settings, and diagnostics.
- Routes accepted plain live-mode inputs to the native bridge.
- Renders replay snapshots and live-session snapshots.
- Exposes controls/help and a demo/limitations summary for first-time users.

## Boundaries

- Python remains the rules reference implementation.
- Godot is the partial migration/demo front end and future product shell.
- Native C++ powers accepted plain live sessions plus geometry/query helpers.
- This shell does not own gameplay-rule authority, topology-rule authority, or replay-schema authority.

## Notes

- `Replay Demos` is the safest first stop if you want to inspect the project before playing.
- `Live Plain 2D` is the easiest first play mode.
- `Live Plain 3D` and `Live Plain 4D` are accepted playable shells, but they are still plain bounded modes rather than the full topology toolchain.
- Bundle assets under `res://assets/tet4d_bundle/` are copied inputs, not semantic authority.
