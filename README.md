# tet4d

Usage guide for the 2D/3D/4D Tetris project.

## What this is

This repository contains:
- Unified launcher (`front.py`)
- `2D Tetris` direct mode (`front2d.py`)
- `3D Tetris` direct mode (`front3d.py`)
- `4D Tetris` direct mode (`front4d.py`)

All modes share core logic under `tetris_nd/`, with mode-specific frontends and external keybindings JSON files.

## Requirements

- Python `3.11+` (target compatibility includes Python `3.14`)
- `pygame-ce` (installed via `requirements.txt`)

## Setup

```bash
cd /Users/omer/workspace/test-code/tet4d
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
# Unified launcher (recommended)
python /Users/omer/workspace/test-code/tet4d/front.py

# Direct 2D
python /Users/omer/workspace/test-code/tet4d/front2d.py

# Direct 3D
python /Users/omer/workspace/test-code/tet4d/front3d.py

# Direct 4D
python /Users/omer/workspace/test-code/tet4d/front4d.py
```

Unified launcher includes:
- Mode selection (`2D/3D/4D`)
- Keybindings setup menu (load/save/rebind/reset, profile cycle/create/delete)
- Audio settings (`master`, `sfx`, `mute`)
- Display settings (`fullscreen`, windowed size, apply/save/reset)

## Keybindings

Bindings are external JSON files:
- `/Users/omer/workspace/test-code/tet4d/keybindings/2d.json`
- `/Users/omer/workspace/test-code/tet4d/keybindings/3d.json`
- `/Users/omer/workspace/test-code/tet4d/keybindings/4d.json`

The active profile can be selected with:

```bash
export TETRIS_KEY_PROFILE=small
# or
export TETRIS_KEY_PROFILE=full
```

## Quality checks

```bash
# Lint
ruff check /Users/omer/workspace/test-code/tet4d

# Unit and gameplay replay tests
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3.11 -m pytest -q

# Python 3.14 compatibility compile check
python3.14 -m compileall -q /Users/omer/workspace/test-code/tet4d/front2d.py /Users/omer/workspace/test-code/tet4d/tetris_nd
```

## Documentation map

Documentation is unified into three sections:
1. Project structure and documentation:
   - `/Users/omer/workspace/test-code/tet4d/docs/PROJECT_STRUCTURE.md`
2. README usage (this file):
   - `/Users/omer/workspace/test-code/tet4d/README.md`
3. RDS files and Codex instructions:
   - `/Users/omer/workspace/test-code/tet4d/docs/RDS_AND_CODEX.md`
   - `/Users/omer/workspace/test-code/tet4d/docs/rds/`
