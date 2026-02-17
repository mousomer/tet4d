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
- Playbot mode selection in per-mode setup menus (`OFF`, `ASSIST`, `AUTO`, `STEP`)
- Playbot speed control in setup menus (`1..10`)
- Challenge mode setup (`challenge layers`: random-filled lower layers)
- Dry-run verification in setup menus (`F7`) to validate playthrough/layer clears without rendering

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

In-game utility keys:
- `G`: cycle grid mode (`OFF -> EDGE -> FULL -> HELPER`)
- `F2`: cycle playbot mode
- `F3`: trigger one bot step (useful in `STEP` mode)

3D/4D camera defaults:
- `H/J/K/L`: yaw `-15 / -90 / +90 / +15` (strict `hjkl` yaw layout)
- `U/O`: pitch `+90 / -90`
- Mouse: hold right button and drag to orbit, use wheel to zoom

Speed scaling by dimension:
- The same speed level is intentionally slower in higher dimensions (`4D` starts slower than `3D`, and `3D` slower than `2D`).

## Playbot Modes

- `OFF`: normal manual gameplay.
- `ASSIST`: bot plans best landing and shows guidance stats; player still controls piece movement.
- `AUTO`: bot plays continuously. It uses planned lateral/rotation moves plus **soft-drop only** (no hard-drop), and its action cadence matches the configured game speed level.
- `STEP`: debug mode. Bot executes one action each time you press `F3`.

Bot behavior details:
- Bot starts planning rotations/moves only after the active piece is fully visible (below spawn/top area), so rotations are visible to the player.
- 4D bot planning uses cached orientation expansion and a faster drop-settle evaluation path.

## What Is "Slice" (3D/4D views)

- A slice is a **view filter**, not a physics change.
- In 4D, board cells exist across `z` and `w` axes; slicing chooses which `z` or `w` layer to focus on visually.
- Piece collisions, gravity, and rotations still run on the full board state even when a slice is active.
- Use slices to inspect dense scenes and debug layer interactions.

## Scoring Rules

- Every locked piece gives a base score.
- Clearing layers gives larger bonus score.
- Final awarded points are multiplied by a difficulty factor.
- Easier assists lower score gain:
  - stronger bot assistance (`ASSIST/AUTO/STEP`)
  - more informative grid modes (`EDGE/FULL/HELPER`)
  - slower speed levels

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
