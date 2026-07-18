# Tet4D Godot Front End

This Godot 4.6.3 project is the partial migration of Tet4D into a demo front
end and future product shell.

It currently supports:

- `Replay Demos` under `Advanced / Diagnostics` for exported gameplay,
  topology, and endgame traces
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

- Presents the main menu, secondary advanced/diagnostics routes, replay browser,
  viewer, controls, and settings.
- Routes accepted plain live-mode inputs to the native bridge.
- Opens a mode-specific New Game setup flow with curated board, piece-set,
  randomness, seed, and starting-speed choices.
- Renders replay snapshots and live-session snapshots.
- Exposes controls/help and a demo/limitations summary for first-time users.
- Saves supported presentation preferences from the Settings screen and restores them at startup.

## Game Setup

Game-start configuration is gameplay setup, not shell settings. Choosing Play
2D, Play 3D, or Play 4D opens a setup screen with exact curated board
dimensions, production piece sets, Fixed Seed or True Random, a validated
decimal seed, and starting speed 1–10. Start Game constructs one strict native
bounded session from that canonical setup.

Restart Game keeps the same board, piece set, random mode, effective seed, and
starting speed, reproducing the initial piece sequence. True Random still
captures and displays an effective seed; New Random Game is shown only for that
mode and requests a new effective seed without changing the other setup
choices. Change Setup exits live play before another session is constructed.

The last validated setup per mode is stored separately in
`user://game_setup.json` using schema version 2. Existing Stage 49 preset-only
schema-version-1 files migrate safely. Missing, malformed, future, or invalid
mode entries fall back independently. The file stores the user's fixed seed,
not active/effective runtime seed or board state, score, pieces, cells, pause,
or game-over state, and it never writes `user://shell_settings.json`.

Production piece sets currently exposed are Classic Tetrominoes in 2D; True 3D
and Embedded 2D in 3D; and True 4D (5-cell), Embedded 3D, and Embedded 2D in
4D. Random-shape generators, debug rectangles, and the 6/7/8-cell 4D catalogs
remain deferred until they have native production and parity coverage.

The Wide W 4D preset uses an adaptive matrix of projected layer boards. Every
W layer is represented, all active-piece layers receive stronger outlines,
and Fit View frames the complete matrix. Godot does not currently expose XW or
ZW view-basis rotation, so identity/W layering remains the accepted live view.
Shift+mouse-wheel scrolls layer rows without sending gameplay commands; normal
mouse-wheel zoom remains unchanged, and Fit View restores the matrix overview.

## Shell Settings

The checked-in shell settings registry defines supported preferences and their
defaults. Validated user choices are saved as versioned JSON in Godot's writable
user-data directory at `user://shell_settings.json`; no repository or Python
configuration file is changed.

Missing or malformed settings recover to registry defaults with a concise
diagnostic. `Reset Settings to Defaults` restores and saves only shell
preferences. Onboarding can be disabled and re-enabled from Settings without
storing tutorial progress or gameplay state.

## Boundaries

- Python remains the rules reference implementation.
- Godot is the partial migration/demo front end and future product shell.
- Native C++ powers accepted plain live sessions plus geometry/query helpers.
- This shell does not own gameplay-rule authority, topology-rule authority, or replay-schema authority.

## Notes

- `Advanced / Diagnostics -> Replay Demos` retains the trace-inspection surface
  without presenting it as a primary play choice.
- `Live Plain 2D` is the easiest first play mode.
- `Live Plain 3D` and `Live Plain 4D` are accepted playable shells, but they are still plain bounded modes rather than the full topology toolchain.
- Bundle assets under `res://assets/tet4d_bundle/` are copied inputs, not semantic authority.
