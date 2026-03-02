# CURRENT_STATE (Restart Handoff)

Last updated: 2026-03-01
Branch: `codex/loc-slim-batch`
Worktree expectation at handoff: dirty (policy additions + doc refresh pending commit)

## Purpose

This file is a restart-ready handoff for long-running architecture cleanup work.
Read this first in a new Codex thread before continuing staged refactors.

## Current Architecture Snapshot

- `arch_stage`: `836` (from `scripts/arch_metrics.py`)
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

## Latest Local Batch (Unreleased)

Completed:
- Added leaderboard persistence and display flow:
  - storage: `state/analytics/leaderboard.json`
  - launcher + pause menu entrypoint action: `leaderboard`
  - runtime submission on 2D/3D/4D session end.
- Added restart-path leaderboard session capture so scores are persisted when runs are restarted.
- Added scoring explanation blocks to runtime help content (base clear points,
  multi-layer bonus, board-clear bonus, multiplier, leaderboard semantics).
- Updated 3D/4D control helper group ordering so camera actions are prioritized
  and panel priority remains: score summary -> Translation -> Rotation -> Camera/View -> System -> low-priority data.

Verification:
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

### Track A (highest value): Delivery-Size Pressure Reduction

Goal: shave LOC without behavior change in runtime/UI hotspots.

Planned moves:
- Factor `src/tet4d/ui/pygame/keybindings.py` into smaller helpers (profile/IO/rebind) with shims and zero-caller prune.
- Slice `src/tet4d/engine/runtime/menu_settings_state.py` into read/write/sanitize helpers; keep storage layout stable.
- Trim duplicated runtime API wrapper boilerplate in `src/tet4d/engine/api.py`.
- Keep menu/help content in config assets; avoid large Python literals.

Execution pattern:
1. Extract to subpackage.
2. Add compatibility shim.
3. Canonicalize callers.
4. Zero-caller audit.
5. Prune shim.
6. Update docs/metrics; ensure `tech_debt.score` ≤ baseline.

### Track B: Playbot relocation audit-only (low priority)

- Periodic audit for stray `engine/playbot/*.py` (none currently; no action staged).

### Track C: Runtime side-effect extraction (selective)

- Audit `read_text`/`write_text`/`open(` in `src/tet4d/engine/**` and reroute misplaced I/O into runtime helpers only when outside runtime-owned storage modules.

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
