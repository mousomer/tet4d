# Project Structure And Documentation

This document is section `1` of the unified documentation layout.

## Top-level structure

```text
tet4d/
├── front2d.py                   # 2D game entrypoint
├── front3d.py                   # 3D game entrypoint
├── front4d.py                   # 4D game entrypoint
├── requirements.txt             # runtime dependency list (pygame-ce)
├── keybindings/
│   ├── 2d.json                  # 2D key map
│   ├── 3d.json                  # 3D key map
│   └── 4d.json                  # 4D key map
├── tetris_nd/                   # shared engine + frontends + tests
│   ├── board.py                 # sparse ND board + plane clear logic
│   ├── game2d.py                # 2D game rules/state
│   ├── game_nd.py               # ND game rules/state (3D/4D)
│   ├── pieces2d.py              # classic tetromino set
│   ├── pieces_nd.py             # 3D + 4D native piece sets
│   ├── keybindings.py           # binding definitions + load/save
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
        ├── RDS_2D_TETRIS.md
        ├── RDS_3D_TETRIS.md
        └── RDS_4D_TETRIS.md
```

## Runtime architecture

1. `front2d.py`, `front3d.py`, and `front4d.py` are startup scripts.
2. These scripts launch mode-specific frontends in `tetris_nd/`.
3. Core rule logic lives in `game2d.py` and `game_nd.py`.
4. Board occupancy and line/layer clearing logic lives in `board.py`.
5. Input binding definitions are centralized in `keybindings.py` and persisted as JSON.
6. Tests in `tetris_nd/tests/` cover engine behavior and replay/smoke gameplay paths.

## Unified documentation sections

1. Project structure and documentation:
   - `/Users/omer/workspace/test-code/tet4d/docs/PROJECT_STRUCTURE.md`
2. Usage README:
   - `/Users/omer/workspace/test-code/tet4d/README.md`
3. RDS and Codex instructions:
   - `/Users/omer/workspace/test-code/tet4d/docs/RDS_AND_CODEX.md`
   - `/Users/omer/workspace/test-code/tet4d/docs/rds/`
