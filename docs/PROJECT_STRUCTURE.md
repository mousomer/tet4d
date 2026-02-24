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
├── packaging/
│   ├── pyinstaller/
│   │   └── tet4d.spec          # canonical desktop bundle spec (embedded Python runtime)
│   └── scripts/
│       ├── build_macos.sh      # local macOS desktop package build
│       ├── build_linux.sh      # local Linux desktop package build
│       └── build_windows.ps1   # local Windows desktop package build
├── config/
│   ├── menu/
│   │   ├── defaults.json        # default menu/app settings (source-controlled)
│   │   └── structure.json       # menu row/field definitions (source-controlled)
│   ├── schema/
│   │   ├── menu_settings.schema.json  # canonical menu-settings schema
│   │   └── save_state.schema.json     # canonical saved-state schema (planned runtime file)
│   ├── gameplay/
│   │   ├── tuning.json          # speed/challenge/scoring/grid tuning
│   │   └── score_analyzer.json  # score-analyzer feature map and weights
│   ├── help/
│   │   ├── topics.json          # help topic registry
│   │   ├── action_map.json      # action-to-topic mapping
│   │   └── icon_map.json        # action-to-icon mapping for external SVG icon pack
│   ├── topology/
│   │   └── designer_presets.json # advanced boundary topology profile definitions
│   ├── playbot/
│   │   └── policy.json          # planner budgets/lookahead/controller defaults
│   ├── project/
│   │   ├── canonical_maintenance.json  # machine-checked maintenance contract
│   │   ├── io_paths.json               # externalized repo-relative I/O path defaults
│   │   ├── constants.json              # externalized shared runtime constants
│   │   └── secret_scan.json            # secret scanning policy and pattern set
│   └── audio/
│       └── sfx.json             # generated SFX event tone specs
├── keybindings/
│   ├── 2d.json                  # 2D key map
│   ├── 3d.json                  # 3D key map
│   └── 4d.json                  # 4D key map
├── state/
│   ├── menu_settings.json       # user runtime overrides (generated)
│   └── analytics/               # optional runtime score-analyzer telemetry
├── assets/
│   └── help/
│       ├── manifest.json        # canonical help-asset index
│       └── icons/
│           └── transform/
│               └── svg/         # external transform icon pack (16/64, dark/light)
├── tests/
│   └── replay/
│       ├── manifest.json        # canonical replay fixture manifest
│       └── golden/
│           └── .gitkeep         # anchor for golden replay fixtures
├── tet4d/                       # root shim package forwarding to src/tet4d for local imports
├── tetris_nd/                   # legacy compatibility shim forwarding to tet4d.engine
├── src/tet4d/engine/            # shared engine + frontends + tests (source of truth)
│   ├── board.py                 # sparse ND board + plane clear logic
│   ├── game2d.py                # 2D game rules/state
│   ├── game_nd.py               # ND game rules/state (3D/4D)
│   ├── topology.py              # bounded/wrap/invert topology rules and mapping helpers
│   ├── topology_designer.py     # advanced topology profile loader/resolver/export helpers
│   ├── pieces2d.py              # classic tetromino set
│   ├── pieces_nd.py             # 3D + 4D native piece sets
│   ├── keybindings.py           # binding definitions + load/save
│   ├── keybindings_menu.py      # dedicated keybinding setup screen
│   ├── keybindings_menu_model.py # scope/row model helpers for keybinding UI
│   ├── key_display.py           # shared key-name formatting and display helpers
│   ├── font_profiles.py         # shared per-mode font profiles and font factory
│   ├── control_helper.py        # grouped in-game key-helper rendering
│   ├── help_menu.py             # launcher/pause help and explanation UI
│   ├── menu_control_guides.py   # rendered translation/rotation arrow diagrams
│   ├── score_analyzer.py        # board-health and placement-quality analyzer
│   ├── audio.py                 # generated SFX + volume/mute runtime
│   ├── display.py               # shared fullscreen/windowed mode helpers
│   ├── runtime_config_validation.py # runtime-config schema validation helpers
│   ├── front3d_game.py          # 3D gameplay frontend
│   ├── front4d_game.py          # 4D gameplay frontend
│   ├── pause_menu.py            # shared in-game pause/settings/keybinding menu
│   ├── projection3d.py          # shared projection/camera helpers
│   ├── menu_model.py            # shared menu loop helpers (selection/confirm/clamp)
│   ├── menu_persistence.py      # shared menu settings persistence facade
│   └── tests/                   # unit + replay/smoke tests
├── tools/
│   ├── bench_playbot.py         # planner benchmark + trend recording
│   ├── check_playbot_stability.py  # repeated dry-run stability checks
│   ├── validate_project_contracts.py  # validates canonical maintenance contract
│   └── scan_secrets.py          # secret scanner (policy from config/project/secret_scan.json)
├── .github/workflows/
│   ├── ci.yml                   # push/PR CI matrix
│   ├── stability-watch.yml      # scheduled dry-run + benchmark + policy analysis
│   └── release-packaging.yml    # desktop package build matrix + artifact upload
└── docs/
    ├── BACKLOG.md               # canonical open TODO / technical debt tracker
    ├── CHANGELOG.md             # consolidated change history notes
    ├── FEATURE_MAP.md          # user-facing shipped feature map
    ├── PROJECT_STRUCTURE.md     # this file
    ├── RELEASE_CHECKLIST.md     # pre-release required verification list
    ├── RELEASE_INSTALLERS.md    # local/CI desktop packaging guide
    ├── RDS_AND_CODEX.md         # RDS index + Codex contributor instructions
    ├── SECURITY_AND_CONFIG_PLAN.md  # repo-level security/config externalization policy
    ├── help/
    │   └── HELP_INDEX.md        # canonical help-topic index
    ├── migrations/
    │   ├── menu_settings.md     # menu-settings migration ledger
    │   └── save_state.md        # saved-state migration ledger
    └── rds/
        ├── RDS_TETRIS_GENERAL.md
        ├── RDS_KEYBINDINGS.md
        ├── RDS_MENU_STRUCTURE.md
        ├── RDS_SCORE_ANALYZER.md
        ├── RDS_PACKAGING.md
        ├── RDS_FILE_FETCH_LIBRARY.md
        ├── RDS_2D_TETRIS.md
        ├── RDS_3D_TETRIS.md
        └── RDS_4D_TETRIS.md
```

## Runtime architecture

1. `front.py` is the unified startup flow and settings hub.
2. `front2d.py`,`front3d.py`, and`front4d.py` remain direct mode entrypoints.
3. Core rule logic lives in `game2d.py`and`game_nd.py`.
4. Board occupancy and line/layer clearing logic lives in `board.py`.
5. Boundary topology mapping (`bounded`,`wrap_all`,`invert_all`) lives in `topology.py` and is consumed by `game2d.py`/`game_nd.py`.
6. Advanced topology profile loading/resolution/export is handled in `topology_designer.py` using `config/topology/designer_presets.json`.
7. Input binding definitions are centralized in `keybindings.py` and persisted as JSON.
8. Shared key-name formatting is centralized in `key_display.py`.
9. Shared keybinding editor model/scope helpers are in `keybindings_menu_model.py`.
10. Shared keybinding editor UI is in `keybindings_menu.py`.
11. Audio runtime helpers are in `audio.py`; display mode helpers are in`display.py`.
12. Shared in-game pause flows (settings + keybindings + profiles + help) are in `pause_menu.py`.
13. Shared in-game key helper grouping is in `control_helper.py`.
14. Help/explanation pages (including rendered arrow-diagram guides) are in `help_menu.py`and`menu_control_guides.py`.
15. Shared menu/help layout-zone allocation logic is in `menu_layout.py`.
16. Shared menu utilities and persistence facades are in `menu_model.py`and`menu_persistence.py`.
17. Tests in `src/tet4d/engine/tests/` cover engine behavior and replay/smoke gameplay paths.
18. `config/menu/*` drives launcher/setup menu structure and default values.
19. `config/help/topics.json` + `config/help/action_map.json` define help-topic registry and action-to-topic contracts.
20. `config/help/icon_map.json` defines runtime action-to-icon mapping for external SVG transform icons.
21. `config/gameplay/*`,`config/playbot/*`, and`config/audio/*` drive runtime tuning defaults.
22. `config/project/io_paths.json` + `config/project/constants.json` feed safe runtime path/constants loading in `src/tet4d/engine/project_config.py`.
23. `config/project/secret_scan.json` defines repository secret-scan policy used by `tools/scan_secrets.py`.
24. `config/schema/*`and`docs/migrations/*` are canonical schema + migration ledgers for persisted data contracts.
25. `tests/replay/manifest.json` tracks deterministic replay-contract expectations.
26. `docs/help/HELP_INDEX.md`and`assets/help/manifest.json` are canonical help-content contracts.
27. `docs/RELEASE_CHECKLIST.md` defines pre-release required checks.
28. `state/menu_settings.json` stores user overrides and can be deleted to reset to config defaults.
29. `config/project/canonical_maintenance.json` defines enforced doc/help/test/config consistency rules.
30. `tools/validate_project_contracts.py` validates canonical maintenance contract and is run in CI.
31. `tools/scan_secrets.py` executes the secret-scan policy and is wired into local CI.
32. `tools/check_playbot_stability.py` runs repeated dry-run regression checks and is wired into local CI script.
33. `.github/workflows/stability-watch.yml` runs scheduled stability-watch and policy-analysis automation.
34. `.github/workflows/release-packaging.yml` builds desktop packages with embedded Python runtime for macOS/Linux/Windows.
35. `packaging/pyinstaller/tet4d.spec` is the canonical frozen-bundle build spec.
36. `packaging/scripts/*` are the local OS-specific packaging entrypoints.

## Unified documentation sections

1. Project structure and documentation:
   - `docs/PROJECT_STRUCTURE.md`
- `docs/FEATURE_MAP.md`
- `docs/GUIDELINES_RESEARCH.md`
- `docs/RELEASE_INSTALLERS.md`
2. Usage README:
   - `README.md`
3. RDS and Codex instructions:
   - `docs/RDS_AND_CODEX.md`
- `docs/rds/`
