# Changelog

## 2026-02-18

### Added
1. Main keybindings section menu now separates `General` bindings from dimension-specific sections (`2D`, `3D`, `4D`).
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

### Changed
1. `General` scope behavior in keybindings menu now treats shared/system actions as cross-dimension operations.
2. Keybinding scope order config updated to include `general` (`config/menu/structure.json`).
3. Help/workflow text and RDS/docs references updated to describe `General/2D/3D/4D` keybinding sections.
4. Local CI script now enforces contract validation before test execution.
5. 4D dry-run validation hardening: deterministic debug fallback path and stronger default budget floor for debug-set dry runs.
6. Unified settings menu now includes `Analytics` category with persisted `Score logging` toggle.
7. `tetris_nd/launcher_settings.py` simplified to a single active unified-settings flow (legacy dead paths removed).
8. Help/control rendering for narrow windows improved:
   - `tetris_nd/help_menu.py` now stacks control-guide panels on narrow layouts.
   - `tetris_nd/control_helper.py` now renders bounded key/action columns to avoid overlap.
9. Menu settings category docs now include `Analytics` in `config/menu/structure.json`.
10. Control-guide rendering switched from animated GIF playback to simple arrow diagrams (rendered in-code).
11. Side-panel hierarchy updated so low-priority diagnostics (bot/analyzer lines) render in the lowest section.
12. Runtime config module decomposed: validation logic extracted to `tetris_nd/runtime_config_validation.py`.
13. Added configurable settings IA split policy in `config/menu/structure.json` (`settings_split_rules`).
14. Stability watch uses a longer 4D dry-run window (`max_pieces=40`) in `tools/check_playbot_stability.py`.
15. Keybinding stack simplification:
   - removed dead legacy control-line generation in `tetris_nd/keybindings.py`,
   - unified key-name rendering through `tetris_nd/key_display.py`,
   - reduced duplication in `tetris_nd/keybindings_menu.py` via shared model helpers.
16. Control-guide renderer naming normalized to `menu_control_guides.py` (with compatibility shim in `menu_gif_guides.py`).
17. Settings IA split policy is now enforced at config-load time using `settings_category_metrics` + `settings_split_rules` in `tetris_nd/menu_config.py`.
18. Help menu expanded with a dedicated menu-parity/settings-policy page.
19. Launcher settings subtitle and layout checks now validate top-level category policy from config.
20. Removed oversized combined guide panels from launcher/settings/pause/keybindings screens to prevent text/guide overlap.
21. 4D helper grid rendering now uses layer-local marks only (helper lines appear only on occupied W-layer boards).
22. Help menu was rebuilt into a fuller multi-page reference covering all modes, keys, features, settings, slicing, workflows, and troubleshooting.

### Documentation
1. Updated backlog and RDS references for the keybindings scope split.
2. Added/updated usage and feature map entries to reflect the new keybinding menu structure.
3. Added canonical-maintenance rule documentation in README, feature map, backlog, and RDS guidance.
4. Updated project-structure/docs index to include canonical schema/migration/replay/help/release artifacts.
5. Updated analyzer/menu RDS status and backlog mappings to reflect phase-2 completion and current open follow-up items.
6. Backlog and RDS gap sections updated to reflect closure of all previously open gap items.
7. Help index and asset manifest updated to document arrow-diagram renderer as the primary guide source.
8. README/help docs updated for exploration mode, `F1` gameplay help access, and icon-based control guidance.
