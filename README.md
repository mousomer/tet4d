# tet4d

Usage guide for the 2D/3D/4D Tetris project.

## What this is

This repository contains:
- Unified launcher wrapper (`front.py`)
- Direct mode launchers under `cli/` (`cli/front2d.py`, `cli/front3d.py`, `cli/front4d.py`)

Primary Python entrypoints live under `cli/` (`cli/front*.py`).
Root `front.py` is the compatibility wrapper entrypoint.
All modes share core logic under `src/tet4d/engine/`.

Boundary topology presets are available in setup menus:
- `bounded` (default)
- `wrap_all`
- `invert_all`

Gravity-axis wrapping is disabled by default.
Advanced topology designer controls are available per mode:
- `Topology advanced` (toggle)
- `Topology profile` (loaded from `config/topology/designer_presets.json`)

## Requirements

- Python `3.11+` (target compatibility includes `3.14`)
- `pygame-ce` (installed via `requirements.txt`)
- Do not install legacy `pygame` in the same environment
- CI validation matrix: Python `3.11`, `3.12`, `3.13`, `3.14`
- Desktop packaged bundles include embedded Python runtime (end users do not need system Python)

## Setup

```bash
cd .
scripts/bootstrap_env.sh
source .venv/bin/activate
```

Alternative manual setup:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install ruff pytest
```

`scripts/ci_check.sh` prefers `.venv/bin/python` when present and expects the repo to be installed in editable mode (`pip install -e .[dev]`) in that same environment.

## Dev setup (editable install)

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Development

- Canonical runtime source path is `src/tet4d/engine/`.
- `tet4d.engine.*` is the canonical import path for runtime/tests/tools.
- The repo expects an editable install for development and verification (`pip install -e ".[dev]"`).
- See `docs/MIGRATION_NOTES.md` for structure history and shim removal milestones.

## Run

```bash
# Unified launcher via compatibility wrapper (kept stable)
python front.py

# Unified wrapper selector (routes to main/2d/3d/4d; default is "main")
# `front` is an alias for `main` (same target)
python front.py --frontend 4d
python front.py --mode 2d

# Canonical direct entrypoints (primary scripts)
python cli/front.py

# Direct modes (canonical cli forms; root wrapper supports --frontend/--mode)
python cli/front2d.py
python cli/front3d.py
python cli/front4d.py
```

## Local desktop packaging (bundled runtime)

```bash
# macOS
bash packaging/scripts/build_macos.sh

# Linux
bash packaging/scripts/build_linux.sh
```

Windows (PowerShell):

```powershell
./packaging/scripts/build_windows.ps1
```

Build artifacts are written to `artifacts/installers/`.

## Key files

Menu config:
- `config/menu/structure.json`
- `config/menu/defaults.json`
- `config/help/topics.json`
- `config/help/action_map.json`
- `config/topology/designer_presets.json`

Runtime tuning:
- `config/gameplay/tuning.json`
- `config/gameplay/score_analyzer.json`
- `config/playbot/policy.json`
- `config/audio/sfx.json`

Project-wide path/constants/security policy:
- `config/project/io_paths.json`
- `config/project/constants.json`
- `config/project/secret_scan.json`

User state:
- `state/menu_settings.json`
- `state/topology/selected_profile.json` (advanced topology export)

Keybindings:
- `keybindings/2d.json`
- `keybindings/3d.json`
- `keybindings/4d.json`

Control guide renderer (legacy contract reference):
- `src/tet4d/ui/pygame/menu/menu_control_guides.py`
- `draw_translation_rotation_guides`

## Quality checks

```bash
ruff check .
ruff check --select C901 .
python3 tools/governance/validate_project_contracts.py
python3 tools/governance/scan_secrets.py
python3 tools/governance/check_pygame_ce.py
pytest -q
PYTHONPATH=. python3 tools/stability/check_playbot_stability.py --repeats 20 --seed-base 0
python3 tools/benchmarks/bench_playbot.py --assert --record-trend
scripts/ci_check.sh
```

## Documentation map

1. Project structure and documentation:
- `docs/PROJECT_STRUCTURE.md`
- `docs/FEATURE_MAP.md`
- `docs/GUIDELINES_RESEARCH.md`
- `docs/RELEASE_INSTALLERS.md`

2. Usage:
- `README.md`

3. RDS and Codex guidance:
- `docs/RDS_AND_CODEX.md`
- `docs/rds/`

## Canonical maintenance

- Contract source: `config/project/canonical_maintenance.json`
- Validator: `tools/governance/validate_project_contracts.py`
- Secret scanning policy/runtime scanner: `config/project/secret_scan.json` + `tools/governance/scan_secrets.py`

## Local pytest warning

- If you install `pytest` from local/offline wheels only, import can fail with `ModuleNotFoundError: No module named 'py'`.
- Workaround (offline/local wheel path): copy Homebrew shim file into the venv:
  - `cp /opt/homebrew/lib/python3.11/site-packages/py.py .venv/lib/python3.14/site-packages/py.py`
- Preferred path (when network is available): install `pytest` from PyPI into the active `.venv`.

## Test run TODO (short checklist)

1. Activate `.venv` and verify `pygame-ce` (not legacy `pygame`).
2. Ensure `ruff` and `pytest` import in `.venv`.
3. Run `scripts/ci_check.sh`.
4. If it fails, run the individual checks listed in `Quality checks` to isolate the failing stage.
