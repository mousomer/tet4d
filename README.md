# tet4d

Usage guide for the 2D/3D/4D Tetris project.

## What this is

This repository contains:
- Unified launcher (`front.py`)
- `2D Tetris` direct mode (`front2d.py`)
- `3D Tetris` direct mode (`front3d.py`)
- `4D Tetris` direct mode (`front4d.py`)

All modes share core logic under `tetris_nd/`.

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

`scripts/ci_check.sh` prefers `.venv/bin/python` when present and expects `ruff` + `pytest` to be installed in that same environment.

## Run

```bash
# Unified launcher (recommended)
python front.py

# Direct modes
python front2d.py
python front3d.py
python front4d.py
```

## Key files

Menu config:
- `config/menu/structure.json`
- `config/menu/defaults.json`
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
- `tetris_nd/menu_control_guides.py`
- `draw_translation_rotation_guides`

## Quality checks

```bash
ruff check .
ruff check --select C901 .
python3 tools/validate_project_contracts.py
python3 tools/scan_secrets.py
python3 tools/check_pygame_ce.py
pytest -q
PYTHONPATH=. python3 tools/check_playbot_stability.py --repeats 20 --seed-base 0
python3 tools/bench_playbot.py --assert --record-trend
scripts/ci_check.sh
```

## Documentation map

1. Project structure and documentation:
- `docs/PROJECT_STRUCTURE.md`
- `docs/FEATURE_MAP.md`
- `docs/GUIDELINES_RESEARCH.md`

2. Usage:
- `README.md`

3. RDS and Codex guidance:
- `docs/RDS_AND_CODEX.md`
- `docs/rds/`

## Canonical maintenance

- Contract source: `config/project/canonical_maintenance.json`
- Validator: `tools/validate_project_contracts.py`
- Secret scanning policy/runtime scanner: `config/project/secret_scan.json` + `tools/scan_secrets.py`

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
