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

### Changed
1. `General` scope behavior in keybindings menu now treats shared/system actions as cross-dimension operations.
2. Keybinding scope order config updated to include `general` (`config/menu/structure.json`).
3. Help/workflow text and RDS/docs references updated to describe `General/2D/3D/4D` keybinding sections.
4. Local CI script now enforces contract validation before test execution.
5. 4D dry-run validation hardening: deterministic debug fallback path and stronger default budget floor for debug-set dry runs.
6. Unified settings menu now includes `Analytics` category with persisted `Score logging` toggle.
7. `tetris_nd/launcher_settings.py` simplified to a single active unified-settings flow (legacy dead paths removed).
8. Help/control rendering for narrow windows improved:
   - `tetris_nd/help_menu.py` now stacks GIF guides on narrow layouts.
   - `tetris_nd/control_helper.py` now renders bounded key/action columns to avoid overlap.
9. Menu settings category docs now include `Analytics` in `config/menu/structure.json`.

### Documentation
1. Updated backlog and RDS references for the keybindings scope split.
2. Added/updated usage and feature map entries to reflect the new keybinding menu structure.
3. Added canonical-maintenance rule documentation in README, feature map, backlog, and RDS guidance.
4. Updated project-structure/docs index to include canonical schema/migration/replay/help/release artifacts.
5. Updated analyzer/menu RDS status and backlog mappings to reflect phase-2 completion and current open follow-up items.
