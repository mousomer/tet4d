# Project Structure And Documentation

This document is section `1` of the unified documentation layout.

## Top-level structure

```text
tet4d/
â”œâ”€â”€ cli/
â”‚   â”œâ”€â”€ front.py                # canonical unified launcher entrypoint
â”‚   â”œâ”€â”€ front2d.py              # canonical 2D entrypoint
â”‚   â”œâ”€â”€ front3d.py              # canonical 3D entrypoint
â”‚   â””â”€â”€ front4d.py              # canonical 4D entrypoint
â”œâ”€â”€ front.py                     # unified launcher (2D/3D/4D + settings)
â”œâ”€â”€ front2d.py                   # 2D game entrypoint
â”œâ”€â”€ front3d.py                   # 3D game entrypoint
â”œâ”€â”€ front4d.py                   # 4D game entrypoint
â”œâ”€â”€ requirements.txt             # runtime dependency list (pygame-ce)
â”œâ”€â”€ packaging/
â”‚   â”œâ”€â”€ pyinstaller/
â”‚   â”‚   â””â”€â”€ tet4d.spec          # canonical desktop bundle spec (embedded Python runtime)
â”‚   â””â”€â”€ scripts/
â”‚       â”œâ”€â”€ build_macos.sh      # local macOS desktop package build
â”‚       â”œâ”€â”€ build_linux.sh      # local Linux desktop package build
â”‚       â””â”€â”€ build_windows.ps1   # local Windows desktop package build
â”œâ”€â”€ config/
â”‚   â”œâ”€â”€ menu/
â”‚   â”‚   â”œâ”€â”€ defaults.json        # default menu/app settings (source-controlled)
â”‚   â”‚   â””â”€â”€ structure.json       # menu row/field definitions (source-controlled)
â”‚   â”œâ”€â”€ schema/
â”‚   â”‚   â”œâ”€â”€ menu_settings.schema.json  # canonical menu-settings schema
â”‚   â”‚   â”œâ”€â”€ save_state.schema.json     # canonical saved-state schema (planned runtime file)
â”‚   â”‚   â”œâ”€â”€ help_runtime_content.schema.json # runtime help content contract
â”‚   â”‚   â”œâ”€â”€ help_runtime_layout.schema.json  # runtime help layout contract
â”‚   â”‚   â”œâ”€â”€ tutorial_lessons.schema.json     # tutorial lesson data contract
â”‚   â”‚   â””â”€â”€ tutorial_plan.schema.json        # tutorial stage-plan data contract
â”‚   â”œâ”€â”€ tutorial/
â”‚   â”‚   â”œâ”€â”€ lessons.json         # tutorial packs/steps/gating definitions
â”‚   â”‚   â””â”€â”€ plan.json            # canonical tutorial stage order/coverage plan
â”‚   â”œâ”€â”€ gameplay/
â”‚   â”‚   â”œâ”€â”€ tuning.json          # speed/challenge/scoring/grid/rotation-kick tuning
â”‚   â”‚   â””â”€â”€ score_analyzer.json  # score-analyzer feature map and weights
â”‚   â”œâ”€â”€ help/
â”‚   â”‚   â”œâ”€â”€ topics.json          # help topic registry
â”‚   â”‚   â”œâ”€â”€ action_map.json      # action-to-topic mapping
â”‚   â”‚   â”œâ”€â”€ icon_map.json        # action-to-icon mapping for external SVG icon pack
â”‚   â”‚   â”œâ”€â”€ content/
â”‚   â”‚   â”‚   â””â”€â”€ runtime_help_content.json # runtime help content templates
â”‚   â”‚   â””â”€â”€ layout/
â”‚   â”‚       â””â”€â”€ runtime_help_layout.json # runtime help layout/media placement rules
â”‚   â”œâ”€â”€ topology/
â”‚   â”‚   â””â”€â”€ designer_presets.json # advanced boundary topology profile definitions
â”‚   â”œâ”€â”€ playbot/
â”‚   â”‚   â””â”€â”€ policy.json          # planner budgets/lookahead/controller defaults
â”‚   â”œâ”€â”€ project/
â”‚   â”‚   â”œâ”€â”€ canonical_maintenance.json  # machine-checked maintenance contract
â”‚   â”‚   â”œâ”€â”€ io_paths.json               # externalized repo-relative I/O path defaults
â”‚   â”‚   â”œâ”€â”€ constants.json              # externalized shared runtime constants
â”‚   â”‚   â”œâ”€â”€ folder_balance_budgets.json # leaf-folder fuzzy balance non-regression gate baselines
â”‚   â”‚   â”œâ”€â”€ tech_debt_budgets.json      # weighted tech-debt metric baseline + non-regression debt gate
â”‚   â”‚   â”œâ”€â”€ backlog_debt.json           # canonical machine-readable active debt backlog source
â”‚   â”‚   â””â”€â”€ secret_scan.json            # secret scanning policy and pattern set
â”‚   â””â”€â”€ audio/
â”‚       â””â”€â”€ sfx.json             # generated SFX event tone specs
â”œâ”€â”€ keybindings/
â”‚   â”œâ”€â”€ 2d.json                  # 2D key map
â”‚   â”œâ”€â”€ 3d.json                  # 3D key map
â”‚   â””â”€â”€ 4d.json                  # 4D key map
â”œâ”€â”€ state/
â”‚   â”œâ”€â”€ menu_settings.json       # user runtime overrides (generated)
â”‚   â””â”€â”€ analytics/               # optional runtime score-analyzer telemetry
â”œâ”€â”€ assets/
â”‚   â””â”€â”€ help/
â”‚       â”œâ”€â”€ manifest.json        # canonical help-asset index
â”‚       â””â”€â”€ icons/
â”‚           â””â”€â”€ transform/
â”‚               â””â”€â”€ svg/         # external transform icon pack (16/64, dark/light)
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ replay/
â”‚   â”‚   â”œâ”€â”€ manifest.json        # canonical replay fixture manifest
â”‚   â”‚   â””â”€â”€ golden/
â”‚   â”‚       â””â”€â”€ .gitkeep         # anchor for golden replay fixtures
â”‚   â””â”€â”€ unit/
â”‚       â””â”€â”€ engine/              # canonical engine/unit regression suites
â”œâ”€â”€ src/
â”‚   â””â”€â”€ tet4d/
â”‚       â”œâ”€â”€ __init__.py          # installable package root (src layout)
â”‚       â”œâ”€â”€ ui/                  # UI adapters (incremental separation; pygame adapters live here)
â”‚       â”œâ”€â”€ ai/                  # AI facades (playbot boundary seam over engine.api)
â”‚       â”œâ”€â”€ replay/              # replay data schema + pure playback helpers (no file I/O)
â”‚       â””â”€â”€ engine/              # shared engine + frontends (source of truth)
â”‚           â”œâ”€â”€ core/            # strict-purity deterministic logic extraction subtree
â”‚           â”œâ”€â”€ gameplay/        # non-core gameplay helpers/primitives (merged folder split sequence)
â”‚           â”œâ”€â”€ runtime/         # runtime/config/validation/analytics/assist-scoring/persistence helpers (merged folder split sequence)
â”‚           â”œâ”€â”€ tutorial/        # tutorial schema/content loader/state machine/gating logic
â”‚           â”œâ”€â”€ ui_logic/        # non-rendering menu/input helpers (merged folder split sequence)
â”‚           â”œâ”€â”€ board.py         # sparse ND board + plane clear logic
â”‚           â”œâ”€â”€ game2d.py        # 2D game rules/state
â”‚           â””â”€â”€ game_nd.py       # ND game rules/state (3D/4D)
â”‚       â”œâ”€â”€ topology.py          # bounded/wrap/invert topology rules and mapping helpers
â”‚       â”œâ”€â”€ topology_designer.py # advanced topology profile loader/resolver/export helpers
â”‚       â”œâ”€â”€ pieces2d.py          # classic tetromino set
â”‚       â”œâ”€â”€ pieces_nd.py         # 3D + 4D native piece sets
â”‚       â”œâ”€â”€ keybindings.py       # binding definitions + load/save
â”‚       â”œâ”€â”€ input/               # key dispatch/name formatting + default key maps helper subpackage
â”‚       â”œâ”€â”€ launch/              # launcher/setup/profile UI subpackage
â”‚       â”œâ”€â”€ menu/                # menu + keybindings-menu UI subpackage
â”‚       â”œâ”€â”€ render/              # rendering/panel/icon/font helper UI subpackage
â”‚       â”œâ”€â”€ runtime_ui/          # runtime audio/display/bootstrap + loop + pause/help UI helper subpackage
â”‚       â”‚   â””â”€â”€ tutorial_overlay.py # in-game tutorial instruction overlay renderer
â”‚       â”œâ”€â”€ score_analyzer.py    # board-health and placement-quality analyzer
â”‚       â”œâ”€â”€ runtime_config_validation.py # runtime-config schema validation helpers
â”‚       â”œâ”€â”€ front3d_game.py      # 3D gameplay frontend
â”‚       â”œâ”€â”€ front4d_game.py      # 4D gameplay frontend
â”‚       â”œâ”€â”€ projection3d.py      # shared projection/camera helpers
â”‚       â””â”€â”€ ...                  # additional package modules (see src/tet4d/)
â”œâ”€â”€ tools/
â”‚   â”œâ”€â”€ governance/
â”‚   â”‚   â”œâ”€â”€ validate_project_contracts.py  # canonical maintenance validator
â”‚   â”‚   â”œâ”€â”€ scan_secrets.py                # secret scanner (policy from config/project/policy/manifests/secret_scan.json)
â”‚   â”‚   â”œâ”€â”€ check_pygame_ce.py             # pygame-ce runtime compatibility check
â”‚   â”‚   â””â”€â”€ lint_menu_graph.py             # menu graph structural lint
â”‚   â”œâ”€â”€ stability/
â”‚   â”‚   â””â”€â”€ check_playbot_stability.py     # repeated dry-run stability checks
â”‚   â””â”€â”€ benchmarks/
â”‚       â”œâ”€â”€ bench_playbot.py               # planner benchmark + trend recording
â”‚       â”œâ”€â”€ analyze_playbot_policies.py    # offline playbot policy comparison
â”‚       â””â”€â”€ profile_4d_render.py           # renderer profiling helper
â”œâ”€â”€ .github/workflows/
â”‚   â”œâ”€â”€ ci.yml                   # push/PR CI matrix
â”‚   â”œâ”€â”€ stability-watch.yml      # scheduled dry-run + benchmark + policy analysis
â”‚   â””â”€â”€ release-packaging.yml    # installer build matrix + GitHub release asset publish
â”œâ”€â”€ .githooks/
â”‚   â””â”€â”€ pre-push                 # local push gate -> scripts/ci_check.sh
â””â”€â”€ docs/
    â”œâ”€â”€ BACKLOG.md               # canonical open TODO / technical debt tracker
    â”œâ”€â”€ history/
    â”‚   â””â”€â”€ DONE_SUMMARIES.md    # canonical historical DONE summary ledger
    â”œâ”€â”€ CHANGELOG.md             # consolidated change history notes
    â”œâ”€â”€ FEATURE_MAP.md          # user-facing shipped feature map
    â”œâ”€â”€ PROJECT_STRUCTURE.md     # this file
    ????????? USER_SETTINGS_REFERENCE.md  # generated compact view of user-tunable settings
    â”œâ”€â”€ RELEASE_CHECKLIST.md     # pre-release required verification list
    â”œâ”€â”€ RELEASE_INSTALLERS.md    # local/CI desktop packaging guide
    â”œâ”€â”€ RDS_AND_CODEX.md         # RDS index + Codex contributor instructions
    â”œâ”€â”€ SECURITY_AND_CONFIG_PLAN.md  # repo-level security/config externalization policy
    â”œâ”€â”€ help/
    â”‚   â””â”€â”€ HELP_INDEX.md        # canonical help-topic index
    â”œâ”€â”€ migrations/
    â”‚   â”œâ”€â”€ menu_settings.md     # menu-settings migration ledger
    â”‚   â””â”€â”€ save_state.md        # saved-state migration ledger
    â””â”€â”€ rds/
        â”œâ”€â”€ RDS_TETRIS_GENERAL.md
        â”œâ”€â”€ RDS_KEYBINDINGS.md
        â”œâ”€â”€ RDS_MENU_STRUCTURE.md
        â”œâ”€â”€ RDS_SCORE_ANALYZER.md
        â”œâ”€â”€ RDS_PACKAGING.md
        â”œâ”€â”€ RDS_FILE_FETCH_LIBRARY.md
        â”œâ”€â”€ RDS_2D_TETRIS.md
        â”œâ”€â”€ RDS_3D_TETRIS.md
        â””â”€â”€ RDS_4D_TETRIS.md
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
12. Audio/display/bootstrap runtime helpers are in `runtime_ui/audio.py` and
    `runtime_ui/app_runtime.py`.
13. Shared in-game loop orchestration helpers are in
    `runtime_ui/loop_runner_nd.py`.
14. Shared in-game pause flows (settings + keybindings + profiles + help) are in `runtime_ui/pause_menu.py`.
15. Launcher tutorial-pack selection is in the shared menu graph (`config/menu/structure.json`) and launched from `cli/front.py` action handlers.
16. In-game tutorial instruction overlay rendering is in `runtime_ui/tutorial_overlay.py`.
17. Shared in-game key helper grouping is in `render/control_helper.py`.
18. Help/explanation pages are in `runtime_ui/help_menu.py`; action icons for control visuals are rendered by `render/control_icons.py`.
19. Shared menu/help layout-zone allocation logic is in `engine/ui_logic/menu_layout.py`.
20. Shared menu/default/settings persistence and schema validation are in
    `engine/runtime/menu_settings_state.py`, `engine/runtime/menu_config.py`,
    `engine/runtime/settings_schema.py`,
    `engine/runtime/settings_sanitize.py`, and
    `engine/runtime/menu_structure_schema.py`.
21. Tests in `tests/unit/engine/` cover engine behavior and replay/smoke gameplay paths.
22. `config/menu/*` drives launcher/setup/pause menu structure and copy,
    launcher subtitles, launcher route-action mappings, setup hints, pause hints,
    and default values.
23. `config/help/topics.json` + `config/help/action_map.json` define help-topic registry and action-to-topic contracts; `config/help/content/runtime_help_content.json` is the canonical runtime help-copy content source formatted by `runtime_ui/help_menu.py`.
24. `config/help/layout/runtime_help_layout.json` defines runtime help layout/placement rules (including topic media mode and icon/image placement policy) consumed by `runtime_ui/help_menu.py`.
25. `config/help/icon_map.json` defines runtime action-to-icon mapping for external SVG transform icons.
26. Default keybinding maps/profile templates are config-backed in `config/keybindings/defaults.json` and loaded via runtime keybinding helpers.
27. `config/gameplay/*`,`config/playbot/*`, and`config/audio/*` drive runtime tuning defaults.
28. `config/project/io_paths.json` + `config/project/constants.json` feed safe runtime path/constants loading in `src/tet4d/engine/runtime/project_config.py`.
29. `config/project/policy/manifests/secret_scan.json` defines repository secret-scan policy used by `tools/governance/scan_secrets.py`.
30. `config/schema/*`and`docs/migrations/*` are canonical schema + migration ledgers for persisted data contracts.
31. `config/tutorial/lessons.json` is the canonical data source for tutorial lesson packs and deterministic step contracts.
32. `config/tutorial/plan.json` is the canonical data source for ordered tutorial stage coverage (single-button progression plan).
33. `config/project/policy/manifests/replay_manifest.json` tracks deterministic replay-contract expectations.
34. `docs/help/HELP_INDEX.md`,`config/help/content/runtime_help_content.json`,`config/help/layout/runtime_help_layout.json`, and`config/project/policy/manifests/help_assets_manifest.json` are canonical help-content/layout contracts.
35. `docs/history/DONE_SUMMARIES.md` is the single source for long historical DONE stage summaries.
36. `docs/RELEASE_CHECKLIST.md` defines pre-release required checks.
37. `state/menu_settings.json` stores user overrides and can be deleted to reset to config defaults.
38. `config/project/policy/manifests/canonical_maintenance.json` defines enforced doc/help/test/config consistency rules.
39. `tools/governance/validate_project_contracts.py` validates canonical maintenance contract and is run in CI.
40. `tools/governance/scan_secrets.py` executes the secret-scan policy and is wired into local CI.
41. `tools/stability/check_playbot_stability.py` runs repeated dry-run regression checks and is wired into local CI script.
42. `.github/workflows/stability-watch.yml` runs scheduled stability-watch and policy-analysis automation.
43. `.github/workflows/release-packaging.yml` builds desktop packages with embedded Python runtime for macOS/Linux/Windows.
44. `packaging/pyinstaller/tet4d.spec` is the canonical frozen-bundle build spec.
45. `packaging/scripts/*` are the local OS-specific packaging entrypoints.
46. `scripts/arch_metrics.py` emits top-level `tech_debt` and `stage_loc_logger`;
    active debt backlog input is read from `config/project/backlog_debt.json`,
    and `scripts/check_architecture_metric_budgets.sh` enforces configurable
    tech-debt gate modes (active default: `non_regression_baseline`) through
    `config/project/policy/manifests/tech_debt_budgets.json`.
47. Canonical piece-local transform math lives in
    `src/tet4d/engine/core/piece_transform.py` and is reused by gameplay,
    AI planning, tutorial setup, and rotation animation.
48. Canonical rotation-kick candidate generation and first-fit resolution live in
    `src/tet4d/engine/core/rotation_kicks.py` and are reused by gameplay via
    topology-aware legality checks.
49. `scripts/install_git_hooks.sh` sets `core.hooksPath=.githooks` and installs
    the pre-push local CI gate.
50. `docs/CONFIGURATION_REFERENCE.md` is the generated human-readable index of
    source-controlled config assets under `config/` (excluding schemas).
51. `docs/USER_SETTINGS_REFERENCE.md` is the generated compact view of
    persisted user-facing settings defaults and built-in keybinding profiles.
52. `tools/governance/generate_configuration_reference.py` regenerates and
    verifies both generated configuration docs during local verification and CI.

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
   - `docs/CONFIGURATION_REFERENCE.md`
   - `docs/USER_SETTINGS_REFERENCE.md`
   - `docs/GUIDELINES_RESEARCH.md`
   - `docs/RELEASE_INSTALLERS.md`
2. Usage README:
   - `README.md`
3. RDS and Codex instructions:
   - `docs/RDS_AND_CODEX.md`
   - `docs/rds/`
