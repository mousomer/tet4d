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
- CI validation matrix: Python `3.11`, `3.12`, `3.13`, `3.14`

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
- `Help` menu with explanation pages and arrow-diagram key guides
- Unified `Settings` submenu (`Audio` + `Display` + `Analytics`)
- Keybindings setup menu (load/save/save-as/rebind/reset, profile cycle/create/rename/delete)
  - Main keybinding sections: `General`, `2D`, `3D`, `4D`
- Unified `Bot Options` submenu with per-dimension bot settings
- Bot mode (`OFF`, `ASSIST`, `AUTO`, `STEP`)
- Bot speed (`1..10`)
- Bot algorithm (`AUTO`, `HEURISTIC`, `GREEDY_LAYER`)
- Bot planner profile (`FAST`, `BALANCED`, `DEEP`, `ULTRA`)
- Bot planning budget (ms cap per plan)
- Challenge mode setup (`challenge layers`: random-filled lower layers)
- Exploration mode setup (no gravity/locking; practice movement/rotation on minimal fitting boards)
- Dry-run verification in setup menus (`F7`) to validate playthrough/layer clears without rendering
- Session autosave (`Autosaved` status line in launcher): saves last mode, current setup values, and selected profile without confirmation

Mode setup menus (2D/3D/4D) only expose dimension-specific gameplay options.

## Menu config and defaults

Menu structure and default settings are externalized:
- `/Users/omer/workspace/test-code/tet4d/config/menu/structure.json`
- `/Users/omer/workspace/test-code/tet4d/config/menu/defaults.json`

Gameplay/bot/audio runtime tuning is also externalized:
- `/Users/omer/workspace/test-code/tet4d/config/gameplay/tuning.json`
- `/Users/omer/workspace/test-code/tet4d/config/playbot/policy.json`
- `/Users/omer/workspace/test-code/tet4d/config/audio/sfx.json`

`bot_budget_ms` defaults are sourced from:
- `/Users/omer/workspace/test-code/tet4d/config/playbot/policy.json`

User-specific overrides are persisted in:
- `/Users/omer/workspace/test-code/tet4d/state/menu_settings.json`

If `/Users/omer/workspace/test-code/tet4d/state/menu_settings.json` is removed, the app rebuilds runtime settings from `config/menu/defaults.json` (plus keybinding profile files), so defaults are not taken from hardcoded Python literals.

Reset paths:
- Settings -> Audio/Display -> `Reset defaults` (`F8`)
- Bot Options -> per-dimension -> `Reset defaults` (`F8`)
- Keybindings Setup -> `F6` reset bindings for active profile/dimension
- All reset actions require a second confirmation keypress.

Save behavior:
- `Autosave` is silent/no-confirm and updates session continuity state.
- Explicit `Save` buttons remain the manual durable commit action in settings and option menus.

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
- `F1`: open Help directly from gameplay
- `M`: open in-game pause menu (`Resume`, `Restart`, `Settings`, `Keybindings Setup`, profile actions, `Help`, `Back To Main Menu`, `Quit`)

In-game key helper:
- Keys are grouped into clear sections: `Translation`, `Rotation`, `Camera/View`, `Slice`, `System`.
- Keybinding rows and helper rows render compact per-action icons for translation/rotation.
- Legacy combined arrow-diagram renderer remains available and is still referenced by docs/contracts:
  - `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_control_guides.py` (`draw_translation_rotation_guides`)

3D/4D camera defaults:
- `H/J/K/L`: yaw `-15 / -90 / +90 / +15` (strict `hjkl` yaw layout)
- `U/O`: pitch `+90 / -90`
- Mouse: hold right button and drag to orbit, use wheel to zoom

Speed scaling by dimension:
- The same speed level is intentionally slower in higher dimensions (`4D` starts slower than `3D`, and `3D` slower than `2D`).

## Playbot Modes

- `OFF`: normal manual gameplay.
- `ASSIST`: bot plans best landing and shows guidance stats; player still controls piece movement.
- `AUTO`: bot plays continuously. It uses planned lateral/rotation moves, starts descent with soft drops, and may hard-drop after a configured soft-drop threshold (default `4`) to keep pace with game speed.
- `STEP`: debug mode. Bot executes one action each time you press `F3`.
- Planner algorithm can be chosen explicitly: `AUTO` (dimension default), `HEURISTIC`, `GREEDY_LAYER`.
- Planner profile controls lookahead depth and fallback behavior (`FAST` = depth-1, `BALANCED`/`DEEP`/`ULTRA` = deeper lookahead in 2D/3D).
- Planner budget (ms) is an explicit per-plan time cap with adaptive fallback under load (candidate caps + best-so-far timeout fallback).
- Default planner budgets are board-size-aware (larger boards get higher default budgets).

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
- Runtime score analyzer tracks per-lock placement quality and board health:
  - side-panel summary lines: `Quality`, `Board health`, `Trend`
  - config: `/Users/omer/workspace/test-code/tet4d/config/gameplay/score_analyzer.json`
  - settings toggle: `Settings -> Analytics -> Score logging`
- Score-analyzer design (board-health and placement-quality feature vectors) is specified in:
  - `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_SCORE_ANALYZER.md`

## Quality checks

```bash
# Lint
ruff check /Users/omer/workspace/test-code/tet4d

# Validate canonical documentation/test/help contract
python3 /Users/omer/workspace/test-code/tet4d/tools/validate_project_contracts.py

# Unit and gameplay replay tests
pytest -q

# Repeated dry-run stability checks (2D/3D/4D debug sets)
PYTHONPATH=. python3 /Users/omer/workspace/test-code/tet4d/tools/check_playbot_stability.py --repeats 20 --seed-base 0

# Planner latency benchmark (used by CI harness)
python3 /Users/omer/workspace/test-code/tet4d/tools/bench_playbot.py --assert --record-trend

# Full local CI-equivalent check
/Users/omer/workspace/test-code/tet4d/scripts/ci_check.sh

# Optional offline policy snapshot for retuning reviews
python3 /Users/omer/workspace/test-code/tet4d/tools/analyze_playbot_policies.py --board-set all --runs 20 --output-json state/bench/policy_analysis.json --output-csv state/bench/policy_analysis.csv

# Python 3.14 compatibility compile check
python3.14 -m compileall -q /Users/omer/workspace/test-code/tet4d/front2d.py /Users/omer/workspace/test-code/tet4d/tetris_nd
```

## Documentation map

Documentation is unified into three sections:
1. Project structure and documentation:
   - `/Users/omer/workspace/test-code/tet4d/docs/PROJECT_STRUCTURE.md`
   - `/Users/omer/workspace/test-code/tet4d/docs/FEATURE_MAP.md`
   - `/Users/omer/workspace/test-code/tet4d/docs/GUIDELINES_RESEARCH.md`
2. README usage (this file):
   - `/Users/omer/workspace/test-code/tet4d/README.md`
3. RDS files and Codex instructions:
   - `/Users/omer/workspace/test-code/tet4d/docs/RDS_AND_CODEX.md`
   - `/Users/omer/workspace/test-code/tet4d/docs/rds/`

## Canonical maintenance rules

- Source of truth for automatic maintenance checks:
  - `/Users/omer/workspace/test-code/tet4d/config/project/canonical_maintenance.json`
- Contract validator (run locally and in CI):
  - `/Users/omer/workspace/test-code/tet4d/tools/validate_project_contracts.py`
- The contract currently enforces presence/content checks for:
  - README/docs/RDS/backlog/feature map,
  - help guide renderer + manifest,
  - core tests,
  - canonical runtime config files,
  - schema and migration ledgers,
  - replay manifest and golden fixture directory,
  - help index and help asset manifest,
  - release checklist,
  - scheduled stability-watch workflow (`.github/workflows/stability-watch.yml`).
