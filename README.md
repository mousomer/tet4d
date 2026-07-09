# tet4d

Tet4D is a 2D/3D/4D Tetris project with two main ways to explore it:

- The Godot front end for replay demos and accepted plain 2D/3D/4D live play.
- The Python launcher for the broader project tools, including the Topology Playground.

![4D game mode](img.png)

## Start Here

For the best demo path, use the Godot front end.

```bash
./scripts/build_godot_tet4d_core.sh
godot --path godot/Tet4D.Godot
```

If you want the original Python launcher instead:

```bash
python front.py
```

## What You Can Do

- `Replay Demos`: inspect exported gameplay, topology, and endgame traces.
- `Live Plain 2D`: the easiest first play mode.
- `Live Plain 3D`: playable plain 3D with direct XY, XZ, and YZ rotations.
- `Live Plain 4D`: playable plain 4D in side-by-side W slices with camera controls.
- `Topology Playground`: available from the Python launcher, not the Godot shell.

## Demo Path

1. Launch `godot --path godot/Tet4D.Godot`.
2. Open `Replay Demos` and load a gameplay or topology case.
3. Return to `Main Menu` and play `Live Plain 2D`.
4. Try `Live Plain 3D` to understand direct plane rotations.
5. Open `Live Plain 4D` and use `Q / E` for W movement plus `Fit View` when needed.

## Controls Overview

- Replay: `Space` play/pause, arrows move frame/case, `1/2/3` switch trace family, `F` fit view.
- Live Plain 2D: `A/D` move, `W` or `X` rotate clockwise, `Z` rotate counter-clockwise, `S` soft drop, `Space` hard drop.
- Live Plain 3D: `A/D` move on X, `W/S` move on Z, `R/T`, `F/G`, `V/B` rotate planes, `Shift` soft drop, `Space` hard drop.
- Live Plain 4D: `A/D` move on X, `W/S` move on Z, `Q/E` move on W, `R/T`, `F/G`, `V/B`, `Y/U`, `H/J`, `N/M` rotate planes, `I/K/O/L`, `,/.`, wheel, and drag control the camera.
- Live shell system controls: `P` pause, `Backspace` reset, `Tab` switches mode, `Esc` backs out or quits.

The Godot shell also exposes a `Controls` screen and an `About / Demo Path` screen.

## Known Limitations

- Python remains the rules reference implementation.
- Godot is the product shell and playable front end.
- Native C++ currently powers accepted plain live sessions plus geometry/query helpers; it does not replace Python as the rules source.
- Topology Playground, broader topology editing, and Python-first development flows still live in the Python launcher.
- This repo is verified for development use; packaging and release polish are not the focus of the current demo milestone.

## Setup

Preferred bootstrap:

```bash
scripts/bootstrap_env.sh
source .venv/bin/activate
```

Manual setup:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
scripts/install_git_hooks.sh
```

## Run Commands

Python launcher:

```bash
python front.py
python front.py --frontend 2d
python front.py --frontend 3d
python front.py --frontend 4d
python cli/front.py --topology-playground
python cli/front.py --topology-playground 4
```

Godot front end:

```bash
./scripts/build_godot_tet4d_core.sh
godot --path godot/Tet4D.Godot
```

Godot tests:

```bash
godot --headless --path godot/Tet4D.Godot --script tests/run_tests.gd
```

Native core build and parity tests:

```bash
./scripts/test_godot_tet4d_core.sh
native/tet4d_core/build/tests/geometry_core_tests --geometry-parity
native/tet4d_core/build/tests/query_core_tests --query-parity
```

Python-golden gameplay parity checks:

```bash
.venv/bin/python tools/migration/compare_cpp_gameplay_trace.py --all-plain-2d
.venv/bin/python tools/migration/compare_cpp_gameplay_trace.py --all-plain-nd
```

Primary verification gate:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

## More Docs

- Documentation map:
  - `docs/CONFIGURATION_REFERENCE.md`
  - `docs/USER_SETTINGS_REFERENCE.md`
  - `docs/RELEASE_INSTALLERS.md`
- Godot shell notes: `godot/Tet4D.Godot/README.md`
- Workflow and contributor rules: `docs/WORKFLOW_CODEX.md`
- Product requirements: `docs/rds/`
- Current open work: `docs/BACKLOG.md`

## Developer References

- Packaging:
  - `packaging/scripts/build_macos.sh`
- Verification:
  - `scripts/ci_check.sh`
  - `tools/governance/scan_secrets.py`
  - `tools/governance/check_pygame_ce.py`
- Runtime config:
  - `config/gameplay/score_analyzer.json`
  - `config/project/io_paths.json`
  - `config/project/constants.json`
  - `config/project/policy/manifests/secret_scan.json`
