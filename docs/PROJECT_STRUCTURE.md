# Project Structure And Documentation

This document is section `1` of the unified documentation layout.

## Top-level structure

```text
tet4d/
├── front.py                     # unified launcher (2D/3D/4D + settings)
├── front2d.py                   # 2D game entrypoint
├── front3d.py                   # 3D game entrypoint
├── front4d.py                   # 4D game entrypoint
├── requirements.txt             # runtime dependency list (pygame-ce)
├── config/
│   ├── menu/
│   │   ├── defaults.json        # default menu/app settings (source-controlled)
│   │   └── structure.json       # menu row/field definitions (source-controlled)
│   ├── gameplay/
│   │   └── tuning.json          # speed/challenge/scoring/grid tuning
│   ├── playbot/
│   │   └── policy.json          # planner budgets/lookahead/controller defaults
│   └── audio/
│       └── sfx.json             # generated SFX event tone specs
├── keybindings/
│   ├── 2d.json                  # 2D key map
│   ├── 3d.json                  # 3D key map
│   └── 4d.json                  # 4D key map
├── state/
│   └── menu_settings.json       # user runtime overrides (generated)
├── tetris_nd/                   # shared engine + frontends + tests
│   ├── board.py                 # sparse ND board + plane clear logic
│   ├── game2d.py                # 2D game rules/state
│   ├── game_nd.py               # ND game rules/state (3D/4D)
│   ├── pieces2d.py              # classic tetromino set
│   ├── pieces_nd.py             # 3D + 4D native piece sets
│   ├── keybindings.py           # binding definitions + load/save
│   ├── keybindings_menu.py      # dedicated keybinding setup screen
│   ├── audio.py                 # generated SFX + volume/mute runtime
│   ├── display.py               # shared fullscreen/windowed mode helpers
│   ├── front3d_game.py          # 3D gameplay frontend
│   ├── front4d_game.py          # 4D gameplay frontend
│   ├── projection3d.py          # shared projection/camera helpers
│   └── tests/                   # unit + replay/smoke tests
└── docs/
    ├── PROJECT_STRUCTURE.md     # this file
    ├── RDS_AND_CODEX.md         # RDS index + Codex contributor instructions
    ├── archive/
    │   └── structure.txt        # original structure snapshot
    └── rds/
        ├── RDS_TETRIS_GENERAL.md
        ├── RDS_KEYBINDINGS.md
        ├── RDS_MENU_STRUCTURE.md
        ├── RDS_2D_TETRIS.md
        ├── RDS_3D_TETRIS.md
        └── RDS_4D_TETRIS.md
```

## Runtime architecture

1. `front.py` is the unified startup flow and settings hub.
2. `front2d.py`, `front3d.py`, and `front4d.py` remain direct mode entrypoints.
3. Core rule logic lives in `game2d.py` and `game_nd.py`.
4. Board occupancy and line/layer clearing logic lives in `board.py`.
5. Input binding definitions are centralized in `keybindings.py` and persisted as JSON.
6. Shared keybinding editor UI is in `keybindings_menu.py`.
7. Audio runtime helpers are in `audio.py`; display mode helpers are in `display.py`.
8. Tests in `tetris_nd/tests/` cover engine behavior and replay/smoke gameplay paths.
9. `config/menu/*` drives launcher/setup menu structure and default values.
10. `config/gameplay/*`, `config/playbot/*`, and `config/audio/*` drive runtime tuning defaults.
11. `state/menu_settings.json` stores user overrides and can be deleted to reset to config defaults.

## Unified documentation sections

1. Project structure and documentation:
   - `/Users/omer/workspace/test-code/tet4d/docs/PROJECT_STRUCTURE.md`
2. Usage README:
   - `/Users/omer/workspace/test-code/tet4d/README.md`
3. RDS and Codex instructions:
   - `/Users/omer/workspace/test-code/tet4d/docs/RDS_AND_CODEX.md`
   - `/Users/omer/workspace/test-code/tet4d/docs/rds/`
