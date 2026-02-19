# Changelog

## 2026-02-19

### Added
1. Local environment bootstrap script:
   - `scripts/bootstrap_env.sh`
   - creates/updates `.venv` and installs runtime + local quality tools (`pygame-ce`, `ruff`, `pytest`).
2. Canonical contract regex rules support in:
   - `tools/validate_project_contracts.py`
   - manifest fields: `must_match_regex` and `must_not_match_regex`.
3. Control UI helper parity/caching regression tests:
   - `tetris_nd/tests/test_control_ui_helpers.py`
4. Repository secret scanning policy and scanner:
   - `config/project/secret_scan.json`
   - `tools/scan_secrets.py`
5. Shared project config/path loader for safe repo-relative resolution:
   - `tetris_nd/project_config.py`
6. Security/config governance document:
   - `docs/SECURITY_AND_CONFIG_PLAN.md`
7. Advanced topology profile definitions:
   - `config/topology/designer_presets.json`
8. Topology designer resolver/export helpers:
   - `tetris_nd/topology_designer.py`
9. Topology designer test coverage:
   - `tetris_nd/tests/test_topology_designer.py`
10. 4D render profiling tool:
    - `tools/profile_4d_render.py`
11. Gap-closure execution plan artifact:
    - `docs/plans/PLAN_4D_RENDER_GAPS_2026-02-19.md`
12. Dead-code/dedup cleanup planning artifact:
    - `docs/plans/PLAN_UNREFERENCED_HELPERS_AND_CODE_REDUCTION_2026-02-19.md`

### Changed
1. `scripts/ci_check.sh` is now hermetic for lint/test tools:
   - removed global command fallback for `ruff`/`pytest`,
   - requires those modules in the selected `PYTHON_BIN`.
2. Project contract rules now assert the ci runner behavior and block stale pass-count snapshots in docs.
3. Control icon rendering now uses cached pre-rendered surfaces keyed by `(action,width,height)`:
   - `tetris_nd/control_icons.py`
4. Dimensional helper control rows were refactored to shared row-spec builders with unchanged output contracts:
   - `tetris_nd/control_helper.py`
5. Shared cross-screen text/gradient helpers extracted to:
   - `tetris_nd/ui_utils.py`
6. Keybindings UI flow split into dedicated input/view helpers:
   - `tetris_nd/keybindings_menu_input.py`
   - `tetris_nd/keybindings_menu_view.py`
7. Shared ND setup->runtime launcher orchestration extracted to:
   - `tetris_nd/launcher_nd_runner.py`
8. Playbot lookahead scaffolding now uses shared helper logic:
   - `tetris_nd/playbot/lookahead_common.py`
9. Runtime playbot-policy validation refactored from monolith paths into section validators:
   - `tetris_nd/runtime_config_validation.py`
10. Pause/settings menu rows are now externally configured and validated:
   - `config/menu/structure.json`
   - `tetris_nd/menu_config.py`
   - `tetris_nd/pause_menu.py`
11. Local CI now runs secret scanning before lint/tests:
    - `scripts/ci_check.sh` calls `tools/scan_secrets.py`.
12. Runtime path consumers now use shared safe path resolution from `tetris_nd/project_config.py`:
    - `tetris_nd/keybindings.py`
    - `tetris_nd/menu_settings_state.py`
    - `tetris_nd/runtime_config.py`
    - `tetris_nd/score_analyzer.py`
13. Selected hardcoded constants were externalized to `config/project/constants.json` and consumed by:
    - `tetris_nd/gfx_game.py`
    - `tetris_nd/front3d_render.py`
    - `tetris_nd/front4d_render.py`
    - `tetris_nd/text_render_cache.py`
    - `tetris_nd/ui_utils.py`
14. Shared projected-grid rendering now includes cache-keyed lattice segment caching for static camera states:
    - `tetris_nd/projection3d.py`
    - `tetris_nd/grid_mode_render.py`
15. Gradient background drawing in projection renderer now uses shared cached gradient path:
    - `tetris_nd/projection3d.py` -> `tetris_nd/ui_utils.py`.
16. Pause-menu action handling was simplified to a compact action-code dispatcher:
    - reduced duplicated per-action handlers in `tetris_nd/pause_menu.py`.
17. Shared projection cache-key builders were added and reused in 3D/4D renderers:
    - `tetris_nd/projection3d.py`
    - `tetris_nd/front3d_render.py`
    - `tetris_nd/front4d_render.py`
18. Dead projected-grid drawing helpers were removed from `tetris_nd/projection3d.py` after cached-segment path adoption.
19. Score-analyzer validation/update code was consolidated and deduplicated in `tetris_nd/score_analyzer.py`.
20. Added setup-selectable topology presets (`bounded`,`wrap_all`,`invert_all`) for 2D/3D/4D gameplay, with gravity-axis wrapping disabled by default.
21. Menu defaults/structure and persisted settings now include `topology_mode` per dimension.
22. Added deterministic engine-side topology handling for wrapped and inverted edge modes in 2D/ND gameplay paths.
23. Small-profile rotation defaults were replanned to keyboard-pair ladder:
    - 2D: `Q/W`
    - 3D: `Q/W`, `A/S`, `Z/X`
    - 4D: `Q/W`, `A/S`, `Z/X`, `R/T`, `F/G`, `V/B`.
24. Default system bindings were deconflicted from the new 4D small rotation ladder:
    - restart moved to `Y`,
    - toggle-grid moved to `C`.
25. Setup flows now support hidden advanced topology controls per dimension:
    - `topology_advanced`
    - `topology_profile_index`
26. 2D/3D/4D config builders now support profile-driven per-axis/per-edge topology rules.
27. Topology engine now supports explicit edge-rule payloads (per-axis neg/pos behavior) while preserving deterministic mapping.
28. Additional animation timing constants were externalized to `config/project/constants.json` with code-level fallbacks:
    - rotation tween duration,
    - 2D clear effect duration,
    - 3D/4D clear effect durations.
29. Menu schema/defaults were expanded for topology designer fields:
    - `config/menu/defaults.json`
    - `config/menu/structure.json`
    - `config/schema/menu_settings.schema.json`
30. Safe project I/O path config now includes topology export target:
    - `config/project/io_paths.json`
    - `tetris_nd/project_config.py`
31. Rotation-animation overlay rendering now routes through topology-aware mapping (bounded/wrap/invert parity) in:
    - `tetris_nd/gfx_game.py`
    - `tetris_nd/front3d_render.py`
    - `tetris_nd/front4d_render.py`
    - `tetris_nd/topology.py`
32. Invert-boundary seam movement was stabilized for seam-straddling ND pieces via deterministic piece-level fallback mapping in:
    - `tetris_nd/topology.py`
    with regression tests:
    - `tetris_nd/tests/test_topology.py`
    - `tetris_nd/tests/test_game_nd.py`
33. 4D camera/view hyperplane turns (`xw`/`zw`) implemented as render-only animated view controls in:
    - `tetris_nd/front4d_render.py`
    - `tetris_nd/front4d_game.py`
34. 4D keybinding camera actions extended and wired:
    - `view_xw_neg/view_xw_pos/view_zw_neg/view_zw_pos`
    - defaults in `tetris_nd/keybindings_defaults.py`
    - shipped bindings in `keybindings/4d.json` and profile files.
35. 4D camera/view helper grouping updated to expose new view-plane controls:
    - `tetris_nd/control_helper.py`
    - `tetris_nd/keybindings_catalog.py`
36. Added test coverage for the new 4D view-plane features:
    - `tetris_nd/tests/test_front4d_render.py`
    - `tetris_nd/tests/test_nd_routing.py`
    - `tetris_nd/tests/test_gameplay_replay.py`
    - `tetris_nd/tests/test_control_ui_helpers.py`
    - `tetris_nd/tests/test_keybindings.py`
37. 4D projection cache keys now include total `W` size in render extras to prevent stale cross-config lattice/helper cache reuse:
    - `tetris_nd/front4d_render.py`
38. 4D per-layer zoom fit now runs through hyper-view transforms (`xw`/`zw` + centered `w` layer) to keep outer layers visible:
    - `tetris_nd/front4d_render.py`
39. Added 4D render regressions for cache-key separation and hyper-view zoom bounds:
    - `tetris_nd/tests/test_front4d_render.py`
40. Added projection-lattice cache observability helpers for test/profiling validation:
    - `tetris_nd/projection3d.py`
41. Added black-box 4D frame-cache regression for cross-config `W`-size separation:
    - `tetris_nd/tests/test_front4d_render.py`
42. Profiler/benchmark output paths are now restricted to project-root-local destinations:
    - `tools/profile_4d_render.py`
    - `tools/bench_playbot.py`
    - `tools/analyze_playbot_policies.py`
43. Removed definition-only unreferenced helpers from:
    - `tetris_nd/frontend_nd.py`
    - `tetris_nd/menu_keybinding_shortcuts.py`
    - `tetris_nd/menu_model.py`
    - `tetris_nd/project_config.py`
    - `tetris_nd/score_analyzer.py`

### Documentation
1. Setup flow in `README.md` now uses `scripts/bootstrap_env.sh` as canonical quick start.
2. `docs/BACKLOG.md`, `docs/GUIDELINES_RESEARCH.md`, and `docs/RDS_AND_CODEX.md` updated to mark the P2/P3 guardrail items closed.
3. `docs/rds/RDS_TETRIS_GENERAL.md` updated with bootstrap script and closure notes.
4. `docs/FEATURE_MAP.md` updated to document helper icon caching behavior.
5. Backlog and RDS status entries now mark the simplification batch as completed and verified (`ruff`, `C901`, `pytest`).
6. Added and linked repository-level security/config policy docs and config files in README + docs indexes.
7. RDS + feature docs updated for advanced topology-designer behavior, hidden-menu gating, and deterministic profile export path.
8. Backlog updated to close boundary-warping designer and animation-constant externalization follow-ups.
9. Added planning documentation for future 4D view/camera hyperplane rotations (`xw`/`zw`) in backlog and RDS/keybinding specs.
10. Updated RDS/backlog/feature-map docs to mark 4D `xw/zw` view-plane turns as implemented and tested.
11. Added explicit 4D testing requirements for full local CI and render profiling in:
    - `docs/rds/RDS_4D_TETRIS.md`
12. Normalized open `P3` backlog entries to structured ID/cadence/trigger/done format in:
    - `docs/BACKLOG.md`
13. Canonical maintenance contract now validates backlog structure markers/regex for active `P3` entries in:
    - `config/project/canonical_maintenance.json`
14. Added active backlog/RDS follow-up for help and menu IA restructuring (`BKL-P2-006`) in:
    - `docs/BACKLOG.md`
    - `docs/rds/RDS_MENU_STRUCTURE.md`
15. Added active backlog follow-up for unreferenced-helper cleanup and setup-menu deduplication (`BKL-P2-007`) in:
    - `docs/BACKLOG.md`
    - `docs/plans/PLAN_UNREFERENCED_HELPERS_AND_CODE_REDUCTION_2026-02-19.md`
16. Updated `BKL-P2-007` scope after cleanup completion:
    - unreferenced-helper removal marked complete,
    - remaining scope narrowed to setup-menu render/value deduplication.
17. Added sourced help/menu restructuring report and phased execution plan:
    - `docs/plans/PLAN_HELP_AND_MENU_RESTRUCTURE_2026-02-19.md`
18. Updated `docs/rds/RDS_MENU_STRUCTURE.md` research basis with ARIA APG, Microsoft menu/flyout guidance, Material menu guidance, and content-structure references.
19. Expanded `BKL-P2-006` with concrete execution milestones and linked plan artifact in `docs/BACKLOG.md`.
20. Refreshed `docs/GUIDELINES_RESEARCH.md` to reflect current open gaps and current web-guideline source set.

## 2026-02-18

### Added
1. Main keybindings section menu now separates `General` bindings from dimension-specific sections (`2D`,`3D`,`4D`).
2. Canonical maintenance contract file:
   - `config/project/canonical_maintenance.json`
3. Contract validator script and regression test:
   - `tools/validate_project_contracts.py`
- `tetris_nd/tests/test_project_contracts.py`
4. Canonical maintenance artifacts connected and source-controlled:
   - `config/schema/menu_settings.schema.json`
- `config/schema/save_state.schema.json`
- `docs/migrations/menu_settings.md`
- `docs/migrations/save_state.md`
- `tests/replay/manifest.json`
- `docs/help/HELP_INDEX.md`
- `assets/help/manifest.json`
- `docs/RELEASE_CHECKLIST.md`
5. Playbot repeated stability checker:
   - `tools/check_playbot_stability.py`
- wired into `scripts/ci_check.sh`
6. Score-analyzer protocol/persistence tests:
   - `tetris_nd/tests/test_score_analyzer.py` expanded with event/summary validation and file-write checks.
7. Scheduled stability-watch workflow:
   - `.github/workflows/stability-watch.yml`
8. Keybinding/menu decomposition helpers:
   - `tetris_nd/key_display.py`
- `tetris_nd/keybindings_menu_model.py`
9. Menu split-policy regression tests:
   - `tetris_nd/tests/test_menu_policy.py`
10. Exploration mode for `2D/3D/4D` setup flows:
   - no gravity/locking/clears,
   - minimal fitting board dimensions per selected piece set,
   - hard-drop repurposed to piece cycling for movement/rotation practice.
11. Gameplay help shortcut:
   - default `F1` system action opens Help directly during gameplay.
12. Per-action control icon renderer:
   - `tetris_nd/control_icons.py` used in keybinding rows and in-game helper rows.
13. Explicit pygame provider compatibility guard:
   - `tools/check_pygame_ce.py`verifies`pygame-ce`install and rejects legacy`pygame` shadowing.

### Changed
1. `General` scope behavior in keybindings menu now treats shared/system actions as cross-dimension operations.
2. Keybinding scope order config updated to include `general` (`config/menu/structure.json`).
3. Help/workflow text and RDS/docs references updated to describe `General/2D/3D/4D` keybinding sections.
4. Local CI script now enforces contract validation before test execution.
5. 4D dry-run validation hardening: deterministic debug fallback path and stronger default budget floor for debug-set dry runs.
6. Unified settings menu now includes `Analytics`category with persisted`Score logging` toggle.
7. `tetris_nd/launcher_settings.py` simplified to a single active unified-settings flow (legacy dead paths removed).
8. Help/control rendering for narrow windows improved:
   - `tetris_nd/help_menu.py` now stacks control-guide panels on narrow layouts.
   - `tetris_nd/control_helper.py` now renders bounded key/action columns to avoid overlap.
9. Menu settings category docs now include `Analytics`in`config/menu/structure.json`.
10. Control-guide rendering switched from animated GIF playback to simple arrow diagrams (rendered in-code).
11. Side-panel hierarchy updated so low-priority diagnostics (bot/analyzer lines) render in the lowest section.
12. Runtime config module decomposed: validation logic extracted to `tetris_nd/runtime_config_validation.py`.
13. Added configurable settings IA split policy in `config/menu/structure.json` (`settings_split_rules`).
14. Stability watch uses a longer 4D dry-run window (`max_pieces=40`) in`tools/check_playbot_stability.py`.
15. Keybinding stack simplification:
   - removed dead legacy control-line generation in `tetris_nd/keybindings.py`,
   - unified key-name rendering through `tetris_nd/key_display.py`,
   - reduced duplication in `tetris_nd/keybindings_menu.py` via shared model helpers.
16. Control-guide renderer naming normalized to `menu_control_guides.py`(with compatibility shim in`menu_gif_guides.py`).
17. Settings IA split policy is now enforced at config-load time using `settings_category_metrics`+`settings_split_rules`in`tetris_nd/menu_config.py`.
18. Help menu expanded with a dedicated menu-parity/settings-policy page.
19. Launcher settings subtitle and layout checks now validate top-level category policy from config.
20. Removed oversized combined guide panels from launcher/settings/pause/keybindings screens to prevent text/guide overlap.
21. 4D helper grid rendering now uses layer-local marks only (helper lines appear only on occupied W-layer boards).
22. Help menu was rebuilt into a fuller multi-page reference covering all modes, keys, features, settings, slicing, workflows, and troubleshooting.
23. Complexity hotspots were refactored to pass `C901` checks:
   - `front2d.py` (`run_game_loop`)
   - `tetris_nd/control_icons.py` (`draw_action_icon`)
   - `tetris_nd/loop_runner_nd.py` (`run_nd_loop`)
24. Local CI script now includes:
   - explicit `pygame-ce` compatibility check,
   - explicit complexity gate (`ruff --select C901`),
   - `.venv`-preferred Python selection with optional module/command fallback for lint/test runners.
25. RDS runtime headers were normalized to Python `3.11-3.14`+`pygame-ce` in 2D/3D/4D and Keybindings RDS files.
26. Backlog/guideline docs were synchronized to remove stale fixed pass-count snapshots and to track active maintenance items.

### Documentation
1. Updated backlog and RDS references for the keybindings scope split.
2. Added/updated usage and feature map entries to reflect the new keybinding menu structure.
3. Added canonical-maintenance rule documentation in README, feature map, backlog, and RDS guidance.
4. Updated project-structure/docs index to include canonical schema/migration/replay/help/release artifacts.
5. Updated analyzer/menu RDS status and backlog mappings to reflect phase-2 completion and current open follow-up items.
6. Backlog and RDS gap sections updated to reflect closure of all previously open gap items.
7. Help index and asset manifest updated to document arrow-diagram renderer as the primary guide source.
8. README/help docs updated for exploration mode, `F1` gameplay help access, and icon-based control guidance.
