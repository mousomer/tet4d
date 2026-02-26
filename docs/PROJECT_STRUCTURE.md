# Project Structure And Documentation

This document is section `1` of the unified documentation layout.

## Top-level structure

```text
tet4d/
├── cli/
│   ├── front.py                # canonical unified launcher entrypoint
│   ├── front2d.py              # canonical 2D entrypoint
│   ├── front3d.py              # canonical 3D entrypoint
│   └── front4d.py              # canonical 4D entrypoint
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
├── src/
│   └── tet4d/
│       ├── __init__.py          # installable package root (src layout)
│       ├── ui/                  # UI adapters (incremental separation; pygame adapters live here)
│       ├── ai/                  # AI facades (playbot boundary seam over engine.api)
│       ├── replay/              # replay data schema + pure playback helpers (no file I/O)
│       └── engine/              # shared engine + frontends + tests (source of truth)
│           ├── core/            # strict-purity deterministic logic extraction subtree
│           ├── gameplay/        # non-core gameplay helpers/primitives (merged folder split sequence)
│           ├── runtime/         # runtime/config/validation/analytics/assist-scoring/persistence helpers (merged folder split sequence)
│           ├── ui_logic/        # non-rendering menu/input helpers (merged folder split sequence)
│           ├── board.py         # sparse ND board + plane clear logic
│           ├── game2d.py        # 2D game rules/state
│           └── game_nd.py       # ND game rules/state (3D/4D)
│       ├── topology.py          # bounded/wrap/invert topology rules and mapping helpers
│       ├── topology_designer.py # advanced topology profile loader/resolver/export helpers
│       ├── pieces2d.py          # classic tetromino set
│       ├── pieces_nd.py         # 3D + 4D native piece sets
│       ├── keybindings.py       # binding definitions + load/save
│       ├── input/               # key dispatch/name formatting + default key maps helper subpackage
│       ├── launch/              # launcher/setup/profile UI subpackage
│       ├── menu/                # menu + keybindings-menu UI subpackage
│       ├── render/              # rendering/panel/icon/font helper UI subpackage
│       ├── help_menu.py         # launcher/pause help and explanation UI
│       ├── score_analyzer.py    # board-health and placement-quality analyzer
│       ├── audio.py             # generated SFX + volume/mute runtime
│       ├── display.py           # shared fullscreen/windowed mode helpers
│       ├── runtime_config_validation.py # runtime-config schema validation helpers
│       ├── front3d_game.py      # 3D gameplay frontend
│       ├── front4d_game.py      # 4D gameplay frontend
│       ├── pause_menu.py        # shared in-game pause/settings/keybinding menu
│       ├── projection3d.py      # shared projection/camera helpers
│       ├── menu_model.py        # shared menu loop helpers (selection/confirm/clamp)
│       ├── menu_persistence.py  # shared menu settings persistence facade
│       └── tests/               # unit + replay/smoke tests
├── tools/
│   ├── governance/
│   │   ├── validate_project_contracts.py  # canonical maintenance validator
│   │   ├── scan_secrets.py                # secret scanner (policy from config/project/secret_scan.json)
│   │   ├── check_pygame_ce.py             # pygame-ce runtime compatibility check
│   │   └── lint_menu_graph.py             # menu graph structural lint
│   ├── stability/
│   │   └── check_playbot_stability.py     # repeated dry-run stability checks
│   └── benchmarks/
│       ├── bench_playbot.py               # planner benchmark + trend recording
│       ├── analyze_playbot_policies.py    # offline playbot policy comparison
│       └── profile_4d_render.py           # renderer profiling helper
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

1. `cli/front.py` is the canonical unified startup flow and settings hub.
2. `cli/front2d.py`,`cli/front3d.py`, and`cli/front4d.py` are the canonical direct mode entrypoints.
3. Root `front*.py` files are compatibility wrappers that delegate to `cli/`.
4. Core rule logic lives in `game2d.py`and`game_nd.py`.
5. Board occupancy and line/layer clearing logic lives in `board.py`.
6. Boundary topology mapping (`bounded`,`wrap_all`,`invert_all`) lives in `topology.py` and is consumed by `game2d.py`/`game_nd.py`.
7. Advanced topology profile loading/resolution/export is handled in `topology_designer.py` using `config/topology/designer_presets.json`.
8. Input binding definitions are centralized in `keybindings.py` and persisted as JSON.
9. Shared key-name formatting is centralized in `input/key_display.py`.
10. Shared keybinding editor model/scope helpers are in `menu/keybindings_menu_model.py`.
11. Shared keybinding editor UI is in `menu/keybindings_menu.py`.
12. Audio runtime helpers are in `audio.py`; display mode helpers are in`display.py`.
13. Shared in-game pause flows (settings + keybindings + profiles + help) are in `pause_menu.py`.
14. Shared in-game key helper grouping is in `render/control_helper.py`.
15. Help/explanation pages (including rendered arrow-diagram guides) are in `help_menu.py` and `menu/menu_control_guides.py`.
16. Shared menu/help layout-zone allocation logic is in `menu_layout.py`.
17. Shared menu utilities and persistence facades are in `menu_model.py`and`menu_persistence.py`.
18. Tests in `src/tet4d/engine/tests/` cover engine behavior and replay/smoke gameplay paths.
19. `config/menu/*` drives launcher/setup menu structure and default values.
20. `config/help/topics.json` + `config/help/action_map.json` define help-topic registry and action-to-topic contracts.
21. `config/help/icon_map.json` defines runtime action-to-icon mapping for external SVG transform icons.
22. Default keybinding maps/profile templates live in `input/keybindings_defaults.py`.
23. `config/gameplay/*`,`config/playbot/*`, and`config/audio/*` drive runtime tuning defaults.
24. `config/project/io_paths.json` + `config/project/constants.json` feed safe runtime path/constants loading in `src/tet4d/engine/runtime/project_config.py`.
25. `config/project/secret_scan.json` defines repository secret-scan policy used by `tools/governance/scan_secrets.py`.
26. `config/schema/*`and`docs/migrations/*` are canonical schema + migration ledgers for persisted data contracts.
27. `tests/replay/manifest.json` tracks deterministic replay-contract expectations.
28. `docs/help/HELP_INDEX.md`and`assets/help/manifest.json` are canonical help-content contracts.
29. `docs/RELEASE_CHECKLIST.md` defines pre-release required checks.
30. `state/menu_settings.json` stores user overrides and can be deleted to reset to config defaults.
31. `config/project/canonical_maintenance.json` defines enforced doc/help/test/config consistency rules.
32. `tools/governance/validate_project_contracts.py` validates canonical maintenance contract and is run in CI.
33. `tools/governance/scan_secrets.py` executes the secret-scan policy and is wired into local CI.
34. `tools/stability/check_playbot_stability.py` runs repeated dry-run regression checks and is wired into local CI script.
35. `.github/workflows/stability-watch.yml` runs scheduled stability-watch and policy-analysis automation.
36. `.github/workflows/release-packaging.yml` builds desktop packages with embedded Python runtime for macOS/Linux/Windows.
37. `packaging/pyinstaller/tet4d.spec` is the canonical frozen-bundle build spec.
38. `packaging/scripts/*` are the local OS-specific packaging entrypoints.

## Placement rubric

1. New pure deterministic logic slices (no pygame/I/O/time/logging) go in `src/tet4d/engine/core/`.
2. New runtime/gameplay modules that are not yet pure-core-ready go in `src/tet4d/engine/`.
3. New pygame/event-loop/render adapters go in `src/tet4d/ui/pygame/`; cluster subpackage families (for example `src/tet4d/ui/pygame/menu/`) once a prefix group grows.
4. New AI/playbot entry/facade modules go in `src/tet4d/ai/` and should depend on `src/tet4d/engine/api.py`.
5. New replay data schema/playback helpers go in `src/tet4d/replay/` (keep file I/O outside engine core).
6. New CLI-facing entry scripts go in `cli/`; keep root `front*.py` wrappers stable unless compatibility changes are intentional.
7. New repo tooling scripts go in `tools/governance/`, `tools/stability/`, or `tools/benchmarks/` by purpose.
8. Prefer `tet4d.engine.api` for tool imports; UI/render profiling tools may use `src/tet4d/ui/pygame/` adapter seams.
9. `scripts/check_architecture_boundaries.sh` enforces incremental import boundaries (with documented temporary baselines).
10. `scripts/check_engine_core_purity.sh` strictly enforces `src/tet4d/engine/core/` purity.
11. Use editable install (`pip install -e .`) for local imports; do not add runtime logic at repo root.

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
