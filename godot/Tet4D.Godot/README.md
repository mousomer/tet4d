# Tet4D Godot Front End

This Godot 4.7.1 project is Tet4D's current bounded 2D/3D/4D
professional-core product shell.

It currently supports:

- `Replay Demos` under `Advanced / Diagnostics` for exported gameplay,
  topology, and endgame traces
- `Live Plain 2D`
- `Live Plain 3D`
- `Live Plain 4D`

Python remains reference authority for inherited, untransferred semantics and
retains the Topology Playground and later simulation/tooling surfaces. The
professional core does not require feature parity with those separate tools.

## Quick Start

From the repo root:

```bash
git submodule update --init --recursive
./scripts/build_godot_tet4d_core.sh
GODOT_BIN=/path/to/Godot
"$GODOT_BIN" --path godot/Tet4D.Godot
```

The executable must report
`4.7.1.stable.official.a13da4feb`. Official Linux and macOS archive URLs,
SHA-256 checksums, and executable paths are pinned in
`config/project/policy_pack.json`.

Canonical headless verification:

```bash
GODOT_BIN=/path/to/Godot ./scripts/verify_godot_4_7.sh
```

That command checks the exact engine and godot-cpp pins, extension API
compatibility, isolated import, all scripts/scenes/resources, the complete
Godot suite, GDExtension load, and bounded startup. Upgrade proposals must pin
an official stable patch and checksums, audit the official migration guide,
advance godot-cpp to a matching immutable API commit, perform a clean native
rebuild, and update the migration record and CI together.

## Release Export

The current supported product artifact is a macOS 13+ Universal 2 app and ZIP.
Install the exact matching Godot 4.7.1 export templates, then run from the
repository root:

```bash
GODOT_BIN=/path/to/Godot packaging/godot/build_macos.sh
```

The checked-in export preset selects the universal release GDExtension,
excludes the test tree, uses bundle identifier `io.github.mousomer.tet4d`, and
uses the repository's `0.7.5` candidate version. See
`docs/RELEASE_INSTALLERS.md` for artifact inspection, outside-tree launch,
platform limits, and the retained legacy Python installer path.

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
starting speed, reproducing the initial piece sequence and restoring the
default Live-4D presentation. Reset View restores only basis, shared slice
orientation, and fitted framing/projection; Fit View changes framing only.
True Random still
captures and displays an effective seed; New Random Game is shown only for that
mode and requests a new effective seed without changing the other setup
choices. Change Setup exits live play before another session is constructed.

The last validated setup per mode is stored separately in
`user://game_setup.json` using schema version 4. Existing schema versions 1–3
migrate safely. Missing, malformed, future, or invalid
mode entries fall back independently. The file stores the user's fixed seed,
not active/effective runtime seed or board state, score, pieces, cells, pause,
or game-over state. It also excludes basis, slice-local yaw/pitch, framing,
projection, fit, and reflection state, and it never writes
`user://shell_settings.json`.

Production piece sets currently exposed are Classic Tetrominoes in 2D; True 3D
and Embedded 2D in 3D; and True 4D (5-cell), Embedded 3D, and Embedded 2D in
4D. Random-shape generators, debug rectangles, and the 6/7/8-cell 4D catalogs
remain deferred until they have native production and parity coverage.

The Wide W 4D preset uses an adaptive matrix of projected layer boards. Every
current basis-derived layer is represented, all active-piece layers receive
stronger outlines, and Fit View frames the complete matrix. Exact `XW`, `ZW`,
and `ZX` 90-degree view rotations change presentation basis without changing
gameplay. Left drag changes shared slice orientation, right drag pans framing,
and the wheel zooms. Normal Live-4D gameplay exposes no roll control.

## Shell Settings

The checked-in shell settings registry defines supported preferences and their
defaults. Validated user choices are saved as versioned JSON in Godot's writable
user-data directory at `user://shell_settings.json`; no repository or Python
configuration file is changed.

Schema version 3 retains the Stage 51 Windowed/Fullscreen, remembered safe
window size, bounded UI scale, HUD density, board detail, camera sensitivity,
and vertical camera inversion settings, and adds High Contrast, Reduced
Motion, and Show Help and Control Hints. High Contrast composes with
Diagnostic, Instrument (`plain`), and Vector Arcade rather than replacing
theme identity.
Reduced Motion changes presentation smoothing and decorative emphasis only;
it does not change gameplay or replay timing. Instrument (`plain`) is the
calm, board-first default; Diagnostic and Vector Arcade remain selectable for
inspection and a more energetic presentation respectively.

Existing schema-version-1 and schema-version-2 shell settings migrate valid
preferences in memory while new fields use defaults. The legacy keyboard-hint
preference migrates to Show Help and Control Hints. Missing, malformed, future,
unknown, or invalid values recover safely and independently where possible.
`Reset Display Settings` remains display-only. `Reset Accessibility Settings`
restores only High Contrast, Reduced Motion, and help hints. Both preserve
replay, guided-onboarding, and separate game-setup choices. Neither shell file
stores tutorial progress or gameplay state. Game setup remains exclusively in
`user://game_setup.json`.

Visible focus, keyboard reachability, input isolation, and non-colour essential
state cues are always-on invariants rather than preferences. Key rebinding,
controller/touch support, screen-reader integration, speech/audio
accessibility, arbitrary colour settings, and topology remain deferred.

## Boundaries

- Python remains reference authority for inherited, untransferred semantics.
- Godot is the current bounded professional-core product shell.
- Native C++ powers accepted plain live sessions plus geometry/query helpers.
- This shell does not own gameplay-rule authority, topology-rule authority, or replay-schema authority.

## Notes

- `Advanced / Diagnostics -> Replay Demos` retains the trace-inspection surface
  without presenting it as a primary play choice.
- `Live Plain 2D` is the easiest first play mode.
- `Live Plain 3D` and `Live Plain 4D` are accepted playable shells, but they are still plain bounded modes rather than the full topology toolchain.
- Bundle assets under `res://assets/tet4d_bundle/` are copied inputs, not semantic authority.
