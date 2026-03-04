# CURRENT_STATE (Restart Handoff)

Last updated: 2026-03-04
Branch: `codex/tutorials1`
Worktree expectation at handoff: clean (latest CI-compliance hardening batch committed + pushed)

## Purpose

This file is a restart-ready handoff for long-running architecture cleanup work.
Read this first in a new Codex thread before continuing staged refactors.

## Current Architecture Snapshot

- `arch_stage`: `890` (from `scripts/arch_metrics.py`)
- Verification pipeline:
  - canonical local/CI gate is `./scripts/verify.sh`
  - `./scripts/ci_check.sh` is a thin wrapper over `./scripts/verify.sh`
- Architecture gates (must remain green):
  - `ui_to_engine_non_api = 0`
  - `ai_to_engine_non_api = 0`
  - `engine_core_to_engine_non_core_imports = 0`
  - `engine_core_purity.violation_count = 0`

## Current Debt Metrics (from `python3 scripts/arch_metrics.py`)

- `tech_debt.score = 1.28` (`low`, below current baseline 15.06)
  - weighted components (current dominant drivers):
    - backlog priority pressure: `0.0` (no active P1/P2/P3 debt items in canonical debt source)
    - backlog bug pressure: `0.0`
    - delivery-size pressure: `0.92` (172 Python files, 32,243 LOC; weights: src=1.0, tests=0.35, tools/scripts=0.2)
    - code-balance pressure: `0.36` (gate-eligible leaf avg 0.97, runtime leaf watch)
    - menu/keybinding retention pressures: `0.0` (goals met)
  - active gate policy (`non_regression_baseline`, `score_epsilon=0.03`):
    - commits must not exceed baseline score + epsilon
    - debt status must not worsen versus baseline
    - use `strict_stage_decrease` only for designated refactor-only batches
- `pygame_imports_non_test = 3`
  - currently concentrated in:
    - `src/tet4d/engine/front3d_render.py`
    - `src/tet4d/engine/front4d_render.py`
    - `src/tet4d/engine/frontend_nd.py`
- `file_io_calls_non_test = 10`
  - concentrated in runtime storage helpers (acceptable placement debt):
    - `src/tet4d/engine/runtime/settings_schema.py`
    - `src/tet4d/engine/runtime/keybindings_storage.py`
    - `src/tet4d/engine/runtime/score_analyzer.py`
- `random_imports_non_test = 9`
- `time_imports_non_test = 0`
- Debt input source:
  - canonical JSON backlog debt source is now `config/project/backlog_debt.json`
    (`active_debt_items`) with no markdown fallback parsing.

## Folder Balance Snapshot (top-level `.py` per package)

- `src/tet4d/engine`: `6`
- `src/tet4d/engine/ui_logic`: `6`
- `src/tet4d/engine/runtime`: `12`
- `src/tet4d/engine/gameplay`: `11`
- `src/tet4d/ui/pygame`: `6`
- `src/tet4d/ui/pygame/menu`: `10`
- `src/tet4d/ui/pygame/launch`: `5`
- `src/tet4d/ui/pygame/input`: `6`
- `src/tet4d/ui/pygame/render`: `11`
- `src/tet4d/ui/pygame/runtime_ui`: `6`
- `src/tet4d/ai/playbot`: `9`
- `src/tet4d/replay`: `2`

### Balance Assessment

- Gate-eligible leafs remain non-regressed (runtime leaf fuzzy `0.78 / watch`, tests leaf `1.0 / balanced`).
- `engine` top-level and subpackages are healthy; runtime is the primary code-balance watch area.
- `ui/pygame` leaf packages stay balanced after prior relocations; remaining hotspot is logical size, not folder shape.
- `replay` remains `micro_feature_leaf` and balanced.

## Major Completed Milestones (Condensed)

- `src/` layout migration completed; old `tetris_nd` shim removed.
- Root entrypoints consolidated; single root wrapper `front.py`.
- Governance pipeline hardened:
  - `ci_check.sh` wraps `verify.sh`
  - policy, boundary, purity, and metric-budget checks are active
- Engine purity architecture established:
  - `src/tet4d/engine/core` with strict purity gate
  - architecture metrics + budgets enforced
- Boundary cleanup largely completed:
  - `ui -> engine` canonicalized through `engine.api`
  - `ai -> engine.api` enforced
- Large staged folder restructuring completed:
  - `engine/gameplay`
  - `engine/runtime`
  - `engine/ui_logic`
- Significant playbot physical relocation completed into `src/tet4d/ai/playbot`
  - ND planner stack migrated (`planner_nd`, `planner_nd_search`, `planner_nd_core`)
- UI migration continues; many engine compatibility shims already pruned.

## Latest Batch (Committed)

Completed:
- CI compliance hardening and reproducibility controls:
  - added `scripts/ci_preflight.sh` to run sanitation/policy gates + canonical CI pipeline locally
  - stabilized sanitation input handling for local context artifacts:
    - `.gitignore` excludes `context-*.instructions.md`
    - `scripts/check_git_sanitation_repo.sh` excludes `context-*.instructions.md`
  - added policy-manifest literal safety validation in
    `tools/governance/validate_project_contracts.py` to catch path-like string
    literals that can trip sanitation checks
  - tuned wheel-reuse rule scopes in
    `config/project/policy/manifests/wheel_reuse_rules.json` to lower
    false-positive pressure while retaining high-risk coverage
  - added governance test coverage:
    - `tests/unit/governance/test_governance_validate_project_contracts.py`
  - documented CI compliance runbook:
    - `docs/policies/CI_COMPLIANCE_RUNBOOK.md`
    - references synced in `docs/RDS_AND_CODEX.md` and `docs/policies/INDEX.md`
  - synced canonical maintenance contract for new script/doc paths:
    - `config/project/policy/manifests/canonical_maintenance.json`
- Integrated tutorial runtime execution end-to-end:
  - launcher tutorial selector + mode launch routing
  - deterministic per-step input gating
  - in-loop step progression from event + clear predicates
  - 2D/3D/4D tutorial overlay rendering with live key prompts
  - started/completed tutorial progress persistence
  - deterministic tutorial start conditions (2D/3D/4D):
    - curated asymmetric starter piece IDs,
    - starter piece fully visible with minimum gravity layer offset 2,
    - deterministic 1-2 seeded bottom challenge layers.
  - tutorial planning/structure are config-backed (non-Python):
    - `config/tutorial/lessons.json` (runtime structure)
    - `config/tutorial/plan.json` (ordered stage plan)
  - tutorial-step pause contract:
    - gravity/bot progression is paused while tutorial session is running
    - step progression waits on explicit required actions/predicates
  - tutorial setup presets now applied at runtime:
    - board presets (`2d_almost_line`, `3d_almost_layer`, `4d_almost_hyper_layer`)
    - camera presets (`tutorial_3d_default`, `tutorial_4d_default`)
  - pause menu tutorial-specific restart action was removed; tutorial control uses
    hotkeys (`F5/F6/F7/F8/F9`) while pause keeps generic run actions.
- launcher IA now exposes `Tutorials` at root-level; tutorial launch skips setup
  menus and uses persisted/default per-mode settings + deterministic lesson
  presets.
- CI status for latest hardening batch:
  - commit: `7631e36`
  - GitHub Actions run: `22676269281` (`CI`) passed on Python 3.11/3.12/3.13/3.14.
  - tutorial UX hardening:
    - menu/help steps now require Esc-return (`menu_back`) before progression
    - per-stage redo is available (`F7`) without resetting full lesson
    - target-drop stages now require clear predicates (no event-only pass)
    - tutorial overlay key-action rows are unified and bolded for clarity
    - tutorial step setup now enforces visible active-piece placement on every stage
    - tutorial movement/rotation/drop pacing is rate-limited by config-backed delays
    - runtime safety guard auto-redoes stage if no legal tutorial action remains
    - tutorial runtime re-enforces visible active-piece placement; impossible
      placement triggers tutorial restart
    - tutorial sessions clamp board dims to configured 2D/3D/4D minimums at launch
    - full-clear bonus stages now use deterministic single-piece board-clear presets:
      - 2D: `O` + `2d_almost_full_clear_o`
      - 3D: `O3` + `3d_almost_full_clear_o3`
      - 4D: `CROSS4` + `4d_almost_full_clear_cross4`
    - gameplay Esc key now routes to pause/menu return (not instant quit)
    - gameplay restart no longer restarts tutorial lesson progression
    - leaderboard session registration is disabled for tutorial runs
    - pause-menu restart now emits tutorial `restart` action (unblocks restart step)
    - tutorial hotkeys are unified across 2D/3D/4D:
      - `F5`: previous stage
      - `F6`: next stage
      - `F7`: redo stage
      - `F8`: exit tutorial to main menu
      - `F9`: restart tutorial lesson
    - tutorial `F9` restarts lesson session and reapplies deterministic step setup
    - tutorial completion now transitions cleanly to free-play by clearing tutorial
      session state in-loop (no forced menu return)
    - `Backspace` now mirrors `Esc` for menu-back navigation
    - visibility safety now redoes current step instead of full lesson restart
    - 3D/4D move+rotate stages now force asymmetric starters:
      - 3D: `SCREW3`
      - 4D: `SKEW4_A`
    - 3D/4D layer-clear target presets now use solvable deterministic hole patterns:
      - `3d_almost_layer_screw3`
      - `4d_almost_hyper_layer_skew4`
    - tutorial stage pacing increased via config-backed delay constants
    - tutorial stage flow is now segmented and ordered as:
      - translations -> piece rotations -> camera rotations (3D/4D) ->
        camera controls (`toggle_grid`, transparency) -> goals
    - tutorial system controls are guidance-only (no dedicated menu/help/restart
      interactive stages)
    - tutorial full-board-clean stages now require actual empty board state
      (`board_cleared`) before progression
- Key files:
  - `src/tet4d/engine/tutorial/runtime.py`
  - `src/tet4d/engine/tutorial/persistence.py`
  - `src/tet4d/ui/pygame/launch/tutorials_menu.py`
  - `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`
  - `cli/front.py`
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
  - `src/tet4d/engine/frontend_nd.py`
- Seeded interactive tutorial core (M0/M1 scaffolding) with config-backed
  lesson packs and deterministic runtime state machinery:
  - `config/tutorial/lessons.json`
  - `config/schema/tutorial_lessons.schema.json`
  - `src/tet4d/engine/tutorial/schema.py`
  - `src/tet4d/engine/tutorial/content.py`
  - `src/tet4d/engine/tutorial/gating.py`
  - `src/tet4d/engine/tutorial/conditions.py`
  - `src/tet4d/engine/tutorial/events.py`
  - `src/tet4d/engine/tutorial/manager.py`
- Exposed tutorial payload/lesson-id runtime accessors in:
  - `src/tet4d/engine/api.py`
- Added tutorial coverage:
  - `tests/unit/engine/test_tutorial_schema.py`
  - `tests/unit/engine/test_tutorial_manager.py`
  - `tests/unit/engine/test_tutorial_content.py`
- Synced canonical/RDS/project-structure docs:
  - `config/project/policy/manifests/canonical_maintenance.json`
  - `docs/rds/RDS_TETRIS_GENERAL.md`
  - `docs/PROJECT_STRUCTURE.md`
- Reduced runtime parser duplication by extracting shared menu-structure parsing
  helpers into:
  - `src/tet4d/engine/runtime/menu_structure_parse_helpers.py`
  - `src/tet4d/engine/runtime/menu_structure_graph.py`
  - `src/tet4d/engine/runtime/menu_structure_schema.py` now consumes shared helpers
    and no longer carries duplicate `ui_copy` parsing code paths or menu-graph
    traversal helpers.
- Reduced runtime-config validator concentration by extracting gameplay/audio
  payload validation into:
  - `src/tet4d/engine/runtime/runtime_config_validation_gameplay.py`
  - `src/tet4d/engine/runtime/runtime_config.py` now delegates gameplay/audio
    validation to the extracted module.
- Updated clear scoring to include config-backed layer-size weighting:
  - larger cleared layers now award higher base clear points via
    `sqrt(layer_size/reference_plane_cells)` with floor `1.0`
  - reference plane size is configured at
    `config/gameplay/tuning.json` (`clear_scoring.layer_size_weighting.reference_plane_cells`)
  - scoring integration points:
    - `src/tet4d/engine/gameplay/scoring_bonus.py`
    - `src/tet4d/engine/gameplay/game2d.py`
    - `src/tet4d/engine/gameplay/game_nd.py`
  - scoring coverage/docs updated:
    - `tests/unit/engine/test_scoring_bonus.py`
    - `config/help/content/runtime_help_content.json`
    - `docs/rds/RDS_TETRIS_GENERAL.md`
- Rebuilt release packaging matrix successfully for:
  - Linux, Windows, macOS x64, macOS ARM64.
- Tutorial/runtime control UX alignment pass (2026-03-03):
  - helper panel taxonomy enforced as `Main > Translation > Rotation > Camera > Stats`
    with 2D camera panel now exposing grid + transparency controls
  - side panel now renders locked-cell transparency percentage meter bar in
    2D/3D/4D
  - tutorial runtime now enforces config-backed step transition delay (`>=1s`),
    transparency target-range progression (`20%-80%`, per-step randomized target),
    and global soft-drop allowance
  - 4D movement steps now require double action count; ND tutorial setup now
    validates repeated move feasibility before spawning starter piece
  - pause menu `Restart Tutorial` action removed from menu graph (stage redo/restart
    remains available via tutorial hotkeys)

Verification:
- `.venv/bin/ruff check cli/front.py cli/front2d.py src/tet4d/engine/tutorial src/tet4d/ui/pygame/front3d_game.py src/tet4d/ui/pygame/front4d_game.py src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py` passed.
- `.venv/bin/pytest -q tests/unit/engine/test_front_launcher_routes.py tests/unit/engine/test_nd_routing.py tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_tutorial_schema.py tests/unit/engine/test_tutorial_manager.py tests/unit/engine/test_tutorial_content.py` passed (`30 passed`).
- `.venv/bin/pytest -q tests/unit/engine/test_game2d.py tests/unit/engine/test_game_nd.py tests/unit/engine/test_front3d_setup.py tests/unit/engine/test_menu_policy.py tests/unit/engine/test_pause_menu.py` passed (`95 passed`).
- `.venv/bin/ruff check src/tet4d/engine/tutorial tests/unit/engine/test_tutorial_schema.py tests/unit/engine/test_tutorial_manager.py tests/unit/engine/test_tutorial_content.py` passed.
- `.venv/bin/pytest -q tests/unit/engine/test_tutorial_schema.py tests/unit/engine/test_tutorial_manager.py tests/unit/engine/test_tutorial_content.py` passed (`10 passed`).
- `.venv/bin/python tools/governance/validate_project_contracts.py` passed.
- `.venv/bin/pytest -q tests/unit/engine/test_menu_policy.py tests/unit/engine/test_runtime_config.py tests/unit/engine/test_project_config.py` passed (`33 passed`).
- `CODEX_MODE=1 ./scripts/verify.sh` passed.

## Recent Batch Status (Stages 756-790)

Completed:
- Externalized launcher/settings/keybindings/bot/setup UI copy into
  `config/menu/structure.json` (`ui_copy`) and validated it in
  `src/tet4d/engine/runtime/menu_structure_schema.py`.
- Added runtime config accessors for the new copy contract in
  `src/tet4d/engine/runtime/menu_config.py` and `src/tet4d/engine/api.py`.
- Rewired launcher/settings/keybindings/bot/setup rendering modules to consume
  config-backed copy instead of Python literals:
  - `cli/front.py`
  - `src/tet4d/ui/pygame/launch/launcher_settings.py`
  - `src/tet4d/ui/pygame/menu/keybindings_menu_view.py`
  - `src/tet4d/ui/pygame/launch/bot_options_menu.py`
  - `src/tet4d/engine/frontend_nd.py`
  - `src/tet4d/ui/pygame/render/gfx_game.py`
- Expanded menu-policy coverage for config-driven UI copy in
  `tests/unit/engine/test_menu_policy.py`.
- Closed debt item `BKL-P1-008` in canonical backlog debt source
  (`config/project/backlog_debt.json`) after eliminating remaining hardcoded
  launcher/settings/keybindings/bot/setup copy.
- Externalized launcher subtitle copy and route-action mappings to
  `config/menu/structure.json` (`launcher_subtitles`, `launcher_route_actions`).
- Externalized ND setup hint copy to `config/menu/structure.json`
  (`setup_hints`) for `2d/3d/4d`, removed hardcoded setup hint lines in
  `frontend_nd.py`, and enforced schema-level hint presence for every mode.
- Externalized pause subtitle/hint copy to `config/menu/structure.json`
  (`pause_copy`) and wired pause runtime to consume it via `engine.api`.
- Wired launcher route dispatch in `cli/front.py` so `tutorials` and
  `topology_lab` execute implemented actions (`help` and `settings`) instead of
  no-op "not implemented" status paths.
- Removed legacy duplicated `launcher_menu` structure from
  `config/menu/structure.json`; launcher action rows are derived from
  `menus.launcher_root` graph items.
- Extended runtime validation in
  `src/tet4d/engine/runtime/menu_structure_schema.py` to enforce:
  - launcher route mappings exist for every reachable route item,
  - route mapping keys are valid launcher routes,
  - mapped target actions are valid reachable launcher actions.
- Added new menu policy coverage in `tests/unit/engine/test_menu_policy.py` for:
  - route mapping completeness and action validity,
  - launcher subtitles config presence.
- Closed debt items in canonical backlog source:
  - `BKL-P1-009`
  - `BKL-P2-025`
  - `BKL-P2-026`
  - `BKL-P3-008`
- Advanced stage metadata to `arch_stage=790`.
- Refreshed tech-debt baseline to stage `755` / score `15.06`.

Balance note:
- Folder-balance tracked leaf gates remain non-regressed:
  - `src/tet4d/engine/runtime`: `0.82 / watch`
  - `tests/unit/engine`: `1.0 / balanced`
- Replay leaf remains `1.0 / balanced` under the micro profile.
- Tech debt decreased in this batch (`2.19 -> 2.18`).

## Recent Batch Status (Stages 791-800)

Completed:
- Removed backlog-ID ambiguity in `docs/BACKLOG.md` by disambiguating reused IDs
  with `-R2` suffixes and dropping active `BKL-P2-029` from canonical debt source
  (`config/project/backlog_debt.json`).
- Added project-contract enforcement for backlog-ID uniqueness in
  `tools/governance/validate_project_contracts.py`.
- Added regression coverage for backlog-ID uniqueness enforcement:
  `tests/unit/engine/test_validate_project_contracts.py`.
- Reduced duplicated settings-state save/sanitize code in
  `src/tet4d/engine/runtime/menu_settings_state.py`.
- Reduced duplicated menu-structure parsing paths in
  `src/tet4d/engine/runtime/menu_structure_schema.py`:
  - shared mode-string list parser
  - table-driven `ui_copy` section parsing
  - shared string-list parsing for pause/setup/settings-label sections
- Simplified keybinding I/O context handling in
  `src/tet4d/ui/pygame/keybindings.py` by removing unused context flags and
  collapsing dimension-group mapping.
- Reduced wrapper boilerplate in `src/tet4d/engine/api.py` with grouped helper
  dispatchers for keybindings/menu/help/frontend delegates.
- Documentation dedup/cleanup: historical DONE summaries were moved out of
  `docs/BACKLOG.md` into `docs/history/DONE_SUMMARIES.md`; backlog now tracks
  active open items + current batch footprint only.
- Advanced stage metadata to `arch_stage=800`.

Verification checkpoint:
- `CODEX_MODE=1 ./scripts/verify.sh` passed.
- Targeted policy/menu/keybinding/front4d/project-contract test suites passed.
- `python scripts/arch_metrics.py` passed with non-regressed debt status.

## Recent Batch Status (Stages 801-812)

Completed:
- Reduced repetitive wrapper/import boilerplate in
  `src/tet4d/engine/api.py` across runtime settings/menu, keybinding menu
  helpers, frontend/render delegators, and config/schema wrappers while
  preserving existing public API function signatures.
- Added shared call/getattr helper dispatch paths in `engine/api.py` for:
  - runtime modules (`menu_config`, `menu_settings_state`, `runtime_config`,
    `project_config`, `settings_schema`)
  - UI adapters (`keybindings`, keybindings menu helpers, front3d/front4d
    adapters, front3d/front4d render helpers).
- Reduced small duplicated helper logic in
  `src/tet4d/ui/pygame/keybindings.py` (key-list parsing, tuple filtering,
  conflict-apply flow, profile creation delegation).
- Consolidated duplicate action/route item-collection loops in
  `src/tet4d/engine/runtime/menu_structure_schema.py`.
- Reclassified `BKL-P2-027` wording in canonical debt source to reflect
  structural maintenance debt rather than bug backlog semantics.
- Advanced stage metadata to `arch_stage=812`.

Verification checkpoint:
- Targeted suites passed:
  - `test_keybindings.py`
  - `test_menu_policy.py`
  - `test_front4d_render.py`
  - `test_front3d_setup.py`
  - `test_validate_project_contracts.py`
- `python scripts/arch_metrics.py` reports non-regressed gates and
  lower debt score (`9.81 -> 7.04`).
- `CODEX_MODE=1 ./scripts/verify.sh` passed for the post-stage-812 checkpoint.

## Recent Batch Status (Stages 813-826)

Completed:
- Added deterministic gameplay speed-up and scoring support plus restart
  stabilization coverage in the stage-813 commit/tag checkpoint.
- Consolidated shared gameplay settings access (random mode, topology advanced,
  auto speed-up, lines-per-level) into runtime state/config helpers:
  - `src/tet4d/engine/runtime/menu_settings_state.py`
  - `src/tet4d/engine/runtime/settings_schema.py`
- Rewired runtime consumers to shared helpers and removed duplicated speedup
  parsing/clamping paths:
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
  - `src/tet4d/ui/pygame/launch/launcher_settings.py`
- Reduced dynamic dispatch duplication in `src/tet4d/engine/api.py` via generic
  module call/get helpers and centralized partial dispatchers.
- Extended regression coverage:
  - `tests/unit/engine/test_keybindings.py`
  - `tests/unit/engine/test_pause_menu.py`
  - `tests/unit/engine/test_display_resize_persistence.py`
- Reprioritized decomposition debt from active P2 backlog to operational watch:
  - removed `BKL-P2-027` from active debt list
  - added watch item `BKL-P3-007` in `config/project/backlog_debt.json`.
- Advanced stage metadata:
  - `scripts/arch_metrics.py` (`ARCH_STAGE=826`)
  - `config/project/policy/manifests/architecture_metrics.json` (`arch_stage=826`)

Verification checkpoint:
- targeted suites passed (71 tests in focused batch).
- `CODEX_MODE=1 ./scripts/verify.sh` passed.
- `python scripts/arch_metrics.py` passed with lower debt score (`7.18 -> 5.17`).

## Recent Batch Status (Stages 827-834)

Completed:
- Added shared numeric text-input helpers for menu number entry:
  - `src/tet4d/ui/pygame/menu/numeric_text_input.py`
- Reused numeric text-input helpers in settings flow:
  - `src/tet4d/ui/pygame/launch/launcher_settings.py`
- Implemented interactive Topology Lab workflow with config-backed layout/content:
  - `config/topology/lab_menu.json`
  - `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
- Wired launcher Topology Lab action + runtime status integration:
  - `cli/front.py`
- Simplified launcher routing contract: Topology Lab is now a direct `Play` action
  (no route-special-case dispatch path required):
  - `config/menu/structure.json`
  - `src/tet4d/engine/ui_logic/menu_action_contracts.py`
  - `tests/unit/engine/test_menu_policy.py`
- Added engine API adapters for topology mode/profile resolution and export:
  - `src/tet4d/engine/api.py`
- Added regression coverage for topology lab and launcher routing:
  - `tests/unit/engine/test_topology_lab_menu.py`
  - `tests/unit/engine/test_front_launcher_routes.py`
  - `tests/unit/engine/test_numeric_text_input.py`
- Synced canonical maintenance manifest for new topology config asset:
  - `config/project/policy/manifests/canonical_maintenance.json`
- Closed active debt item `BKL-P2-023` (interactive topology-lab gap) in:
  - `config/project/backlog_debt.json`
- Advanced stage metadata:
  - `scripts/arch_metrics.py` (`ARCH_STAGE=834`)
  - `config/project/policy/manifests/architecture_metrics.json` (`arch_stage=834`)

Verification checkpoint:
- `CODEX_MODE=1 ./scripts/verify.sh` passed.
- targeted menu/front/topology suites passed.
- `python scripts/arch_metrics.py` passed with lower debt score (`5.17 -> 3.29`).

## Recent Batch Status (Stage 835)

Completed:
- Added playbot `LEARN` mode with deterministic adaptive profile tuning:
  - `src/tet4d/ai/playbot/types.py`
  - `src/tet4d/ai/playbot/controller.py`
- Added learning policy keys and runtime validation/accessors:
  - `config/playbot/policy.json`
  - `src/tet4d/engine/runtime/runtime_config_validation_playbot.py`
  - `src/tet4d/engine/runtime/runtime_config.py`
  - `src/tet4d/engine/runtime/settings_schema.py`
  - `config/gameplay/tuning.json`
- Added regression coverage for learning mode/profile adaptation and policy load:
  - `tests/unit/engine/test_playbot.py`
  - `tests/unit/engine/test_runtime_config.py`
- Closed final active debt item in canonical source:
  - removed `BKL-P2-024` from `config/project/backlog_debt.json`
  - added watch item `BKL-P3-009` for post-launch learning tuning/stability.
- Advanced stage metadata:
  - `scripts/arch_metrics.py` (`ARCH_STAGE=835`)
  - `config/project/policy/manifests/architecture_metrics.json` (`arch_stage=835`)

Verification checkpoint:
- `CODEX_MODE=1 ./scripts/verify.sh` passed.
- `python scripts/arch_metrics.py` passed with debt score decrease (`3.29 -> 1.28`).

## Recent Batch Status (Stage 836)

Completed:
- Added context-router manifest contract validation:
  - `tools/governance/validate_project_contracts.py`
- Added regression coverage for context-router manifest validation:
  - `tests/unit/engine/test_validate_project_contracts.py`
- Closed stale backlog TODO entries by converting them to enforced contracts:
  - context-router manifest validation
  - policy-pack contract coverage already validated through project contracts.
- Advanced stage metadata:
  - `scripts/arch_metrics.py` (`ARCH_STAGE=836`)
  - `config/project/policy/manifests/architecture_metrics.json` (`arch_stage=836`)

Verification checkpoint:
- `CODEX_MODE=1 ./scripts/verify.sh` passed.
- `python scripts/arch_metrics.py` passed (`tech_debt.score = 1.28`, non-regressed gates).

## Open Issues / Operational Notes

- Tech-debt gate is now non-regression by baseline with epsilon (`15.06 + 0.03`);
  large LOC/file growth still raises debt pressure and can fail budgets.
- Verification flakiness (metrics determinism/benchmarks) remains rare; rerun once if failure occurs with no code change.
- GitHub CI must stay aligned; local verify is authoritative pre-push.

## Active Plan (Policy-Integrated)

Batch objective:
- continue staged architecture cleanup while preserving non-regression debt
  gates; with active debt closed, prioritize LOC/decomposition reduction and
  stability/tuning watchlist execution.

Policy maintenance requirements in every batch:
1. Run policy guardrails at batch start and batch end for:
   - no reinventing the wheel
   - string sanitation
   - no magic numbers
   - formatting/line-length
2. Run a policy checkpoint every 5 stages in long sequential runs.
3. Require documented exception notes + targeted tests for any policy exception.
4. Default verification in quiet mode; use verbose only when debugging failures.

Placement in stage sequence:
1. Baseline metrics/policy check.
2. Staged refactor implementation (move/canonicalize/prune).
3. Periodic policy checkpoint (every 5 stages).
4. Stage-advance checkpoint (`verify`, metrics, budget checks).
5. Final policy + contract sync before commit.

## Short-Term Plan (Next 10-20 stages)

### Track A (highest value): CI Compliance Maintenance

Goal: keep CI deterministic and fast to triage.

Planned moves:
- Keep `scripts/ci_preflight.sh` as required pre-push local gate in daily flow.
- Keep policy manifests/doc indices synchronized (`project_policy.json`, `policy_registry.json`, `docs/policies/INDEX.md`).
- Keep sanitation-safe policy literals and avoid committing local context artifacts.
- If CI fails, triage in runbook order (`docs/policies/CI_COMPLIANCE_RUNBOOK.md`) and patch minimally.

Execution pattern:
1. Reproduce with `./scripts/ci_preflight.sh`.
2. Fix root cause in smallest scope possible.
3. Re-run `CODEX_MODE=1 ./scripts/verify.sh`.
4. Push and confirm matrix green.

### Track B: Tutorial Stability Closure

Goal: eliminate remaining tutorial flow edge-cases without changing core game rules.

Planned moves:
- Harden 4D W-axis progression reliability and stage-completion predicates.
- Ensure transparent, deterministic stage transition pacing across 2D/3D/4D.
- Keep keybinding-driven prompts always consistent with live bindings.

Acceptance:
1. Tutorial runs complete in 2D/3D/4D without deadlocks across replayed smoke runs.
2. Restart/redo/previous/next controls remain deterministic.
3. No tutorial-specific regressions in `verify` test suite.

### Track C: Delivery-Size Pressure Reduction

Goal: reduce LOC and simplify structure with no behavior change.

Planned moves:
- Factor `src/tet4d/ui/pygame/keybindings.py` into smaller helpers (profile/IO/rebind) with shims and zero-caller prune.
- Slice `src/tet4d/engine/runtime/menu_settings_state.py` into read/write/sanitize helpers while keeping storage stable.
- Trim duplicate runtime API wrapper boilerplate in `src/tet4d/engine/api.py`.
- Keep menu/help/tutorial content in config assets instead of Python literals.

Execution pattern:
1. Extract.
2. Add compatibility shim.
3. Canonicalize callers.
4. Zero-caller audit.
5. Prune shim.
6. Re-check tech-debt score trend.

### Track D: Runtime side-effect extraction (selective)

- Audit `read_text`/`write_text`/`open(` in `src/tet4d/engine/**` and reroute misplaced I/O into runtime helpers only when outside runtime-owned storage modules.

### Track E: Interactive Tutorials (authoritative replacement plan)

Objective:

1. Ship a step-driven in-game tutorial system for 2D/3D/4D.
2. Teach movement, rotation, camera, and line/layer/hyper-layer completion.
3. Keep tutorials scriptable/data-driven and resilient to UI/input refactors.

Core constraints:

1. Deterministic progression on explicit conditions only.
2. Lesson content/flow is data; code only implements generic engine/conditions.
3. Per-step input gating (`allow`/`deny`) enforced at input dispatch.
4. Always skippable/restartable; never softlock users.
5. Mode-agnostic core: mode differences live in content packs.

Milestone sequence:

1. M0: schema + canonical action/clearing definitions.
2. M1: tutorial engine (`TutorialManager`, conditions, gating, persistence).
3. M2: overlay UI + highlights + progress + skip/restart controls.
4. M3: Pack A (2D) end-to-end.
5. M4: Pack B (3D) end-to-end.
6. M5: Pack C (4D) end-to-end.
7. M6: replay harness + static validation + tutorial event log export.

Release gate:

1. 2D/3D/4D packs pass deterministic replay tests.
2. Every step has explicit completion conditions and gating.
3. Skip/restart always recover to known state.

Reference:

1. Full canonical tutorial plan is in `docs/BACKLOG.md` section
   `4.1 Interactive Tutorials Plan (BKL-P3-013)`.

## Long-Term Plan (Maximal Clean Architecture)

### Definition of Done (strict target)

- All boundary metrics remain zero:
  - `ui_to_engine_non_api`
  - `ai_to_engine_non_api`
  - `engine_core_to_engine_non_core_imports`
  - `engine_core_purity.violation_count`
- `ui/pygame` split into manageable subpackages with coherent ownership
- Remaining compatibility shims are minimal or removed
- `engine/playbot` compatibility package/surfaces retired after zero-caller audits
- File I/O is centralized under `engine/runtime` (or explicitly accepted if runtime-owned)
- keybinding-retention metric remains aligned (`pressure = 0.0`, no missing/unexpected bindings)
- menu-simplification metric remains at least `manageable` (`simplification_score >= 0.65`)
- Docs and architecture contract reflect the final canonical paths

### Estimated Remaining Effort

- Practical completion (high confidence, low churn): `~6-16` stages
- Maximal clean architecture (strict cleanup / deeper pruning): `~14-30` stages

### Estimated LOC Impact

- Next ~10 stages: roughly `-50` to `+50` LOC net (API prep adds, shim pruning removes)
- Near-maximal completion: roughly `-200` to `-600` LOC net (shim retirement dominates)

## Test Structure Preference

Preference recorded:
- move toward a single top-level test root `./tests/`
- organize by sub-test tasks/domains (unit/integration/runtime/ui/etc.)

Status:
- stage-534 checkpoint completed for canonical engine suites:
  - engine unit/regression tests now live in `tests/unit/engine/`.
  - replay fixtures remain in `tests/replay/`.

Recommended approach:
- keep future test-family additions in top-level `tests/` subfolders.
- avoid reintroducing canonical Python tests under `src/tet4d/engine/tests/`.

## Restart Checklist (for a new Codex thread)

1. Confirm branch and cleanliness:
   - `git branch --show-current`
   - `git status --short`
2. Read:
   - `AGENTS.md`
   - `docs/RDS_AND_CODEX.md`
   - `docs/ARCHITECTURE_CONTRACT.md`
   - this file (`CURRENT_STATE.md`)
3. Capture fresh metrics:
   - `python3 scripts/arch_metrics.py`
4. Choose one family and execute staged sequence:
   - move -> canonicalize -> zero-caller -> prune -> checkpoint
5. Validate at checkpoint:
   - `./scripts/check_git_sanitation.sh`
   - `./scripts/check_policy_compliance.sh`
   - `CODEX_MODE=1 ./scripts/verify.sh`
   - `./scripts/ci_check.sh`

## Current Source of Truth References

- Architecture contract: `docs/ARCHITECTURE_CONTRACT.md`
- RDS + Codex workflow: `docs/RDS_AND_CODEX.md`
- Backlog: `docs/BACKLOG.md`
- Canonical maintenance contract: `config/project/policy/manifests/canonical_maintenance.json`
