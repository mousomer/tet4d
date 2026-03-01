# Consolidated Backlog

Generated: 2026-02-18  
Updated: 2026-03-01  
Scope: active open backlog, governance watchlist, and current change footprint.

## 1. Priority Verification Rules

1. `P1` = user-facing correctness, consistency, and discoverability gaps.
2. `P2` = maintainability and complexity risks that can cause regressions.
3. `P3` = optimization, tuning, and documentation hygiene.

## 2. Unified Change Set (Implemented Baseline)

Historical DONE summaries were deduplicated and moved to a single source:

- `docs/history/DONE_SUMMARIES.md`

Policy for updates:

1. New implementation detail belongs in `## 5. Change Footprint` for the active batch.
2. At batch close, summarize and append durable DONE history in `docs/history/DONE_SUMMARIES.md`.
3. Keep `docs/BACKLOG.md` focused on active open issues and near-term execution.

Historical anchor references:

- `[BKL-P3-001]` pre-push local CI gate checkpoint is closed and retained in historical DONE source.

## 3. Active Open Backlog / TODO (Unified RDS Gaps + Technical Debt)

1. `[BKL-P2-023]` Topology designer remains preset-file/export only; no interactive Topology Lab editor workflow.
2. `[BKL-P2-024]` Playbot lacks learning mode; current architecture supports heuristics/profiles but not an adaptive learning loop.
4. Canonical machine-readable debt source:
   `config/project/backlog_debt.json` (`active_debt_items`).
5. `TODO` Context router adoption: integrate `config/project/policy/manifests/context_router_manifest.json` into Codex tooling, surface in contributor docs, and add a verification hook if needed.
6. `TODO` Policy pack consolidation: wire `config/project/policy/pack.json` (`policy_pack`) into governance checks, keep `docs/policies/INDEX.md` in sync, and add validation hook to verify.sh when stable.

### Historical ID Lineage Policy

1. Backlog IDs must be unique in this file for unambiguous audit/search.
2. Legacy rerolled IDs use `-R2` suffix (for example `BKL-P2-010-R2`) when an original ID already exists in historical DONE ledgers.
3. Legacy/base references are retained in historical files; active/open tracking stays in this file.

### Operational Watchlist (Non-debt; recurring controls)

Cadence: weekly and after workflow/config changes.  
Trigger: any governance, CI-workflow, runtime-validation, or release-process drift.  
Done criteria: controls run cleanly and docs/contracts remain synchronized.

1. `WATCH` `[BKL-P3-002]` Scheduled stability + policy workflow watch:
   cadence remains weekly and after workflow/config changes for
   `.github/workflows/ci.yml`, `.github/workflows/stability-watch.yml`,
   `tools/stability/check_playbot_stability.py`, and
   `tools/benchmarks/analyze_playbot_policies.py`.
2. `WATCH` `[BKL-P3-003]` Runtime-config validation split watch:
   triggered only when playbot policy-surface growth exceeds maintainable scope
   in `src/tet4d/engine/runtime/runtime_config_validation_playbot.py`.
3. `WATCH` `[BKL-P3-006]` Desktop release hardening watch:
   cadence remains before each public release and is tracked through
   release-packaging workflow + release checklist/installers docs.
4. `WATCH` `[BKL-P3-007]` Module decomposition watch:
   large engine/runtime/ui module split pressure moved from active debt to watch
   after shared-settings and API dedup passes; monitor hotspot growth and
   continue staged LOC reduction.

## 4. Gap Mapping to RDS

1. `docs/rds/RDS_TETRIS_GENERAL.md`: CI/stability workflows and setup-menu dedup follow-up are closed; maintain drift watch only.
2. `docs/rds/RDS_PLAYBOT.md`: periodic retuning is operationalized; remaining open gap is learning-mode architecture (`BKL-P2-024`).
3. `docs/rds/RDS_MENU_STRUCTURE.md`: menu graph modularization is closed; remaining open gap is topology-lab interactivity (`BKL-P2-023`).
4. `docs/rds/RDS_FILE_FETCH_LIBRARY.md`: lifecycle/adaptive-fetch design baseline exists; implementation remains future-scoped.

## 5. Change Footprint (Current Batch)

Current sub-batch (2026-03-01): stage 814+ shared gameplay-settings dedup + API dispatch cleanup.

- Consolidated shared gameplay settings load/save/clamp logic into runtime state layer:
  - `src/tet4d/engine/runtime/menu_settings_state.py`
  - `src/tet4d/engine/runtime/settings_schema.py`
- Added engine API runtime adapters for shared gameplay settings access:
  - `src/tet4d/engine/api.py`
- Rewired runtime consumers to use shared helpers (removed duplicate speedup parsing/clamps):
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
  - `src/tet4d/ui/pygame/launch/launcher_settings.py`
- Added regression coverage for shared gameplay settings persistence/clamp behavior:
  - `tests/unit/engine/test_keybindings.py`
- Backlog reprioritization:
  - moved decomposition pressure from active debt (`BKL-P2-027`) to operational
    watch (`BKL-P3-007`) in `config/project/backlog_debt.json` after this dedup
    tranche.
- Verification:
  - targeted suites passed (`test_keybindings.py`, `test_menu_policy.py`,
    `test_front3d_setup.py`, `test_pause_menu.py`,
    `test_display_resize_persistence.py`, `tests/test_leveling.py`)
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-01): pause hotkey parity + deterministic auto speed-up controls.

- Added dedicated pause hotkey default (`F10`) alongside `m`:
  - `config/keybindings/defaults.json`
  - `keybindings/2d.json`
  - `keybindings/3d.json`
  - `keybindings/4d.json`
- Added shared advanced gameplay defaults and settings row:
  - `config/menu/defaults.json` (`auto_speedup_enabled`, `lines_per_level`)
  - `config/menu/structure.json` (`gameplay_advanced` entry + category metrics update)
- Implemented settings hub advanced gameplay submenu and persistence wiring:
  - `src/tet4d/ui/pygame/launch/launcher_settings.py`
- Implemented deterministic speed-level helper:
  - `src/tet4d/engine/gameplay/leveling.py`
  - `tests/test_leveling.py`
- Applied speed-level progression in runtime loops (2D/3D/4D), with restart reset
  to session base speed and runtime gravity reconfiguration:
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
- Added engine API adapter for leveling helper to keep architecture boundary clean:
  - `src/tet4d/engine/api.py`
- Verification:
  - targeted pytest suites passed (76 tests)
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-01): stage 801-812 API/runtime dedup + debt-signal cleanup.

- Advanced stage metadata:
  - `scripts/arch_metrics.py` (`ARCH_STAGE=812`)
  - `config/project/policy/manifests/architecture_metrics.json` (`arch_stage=812`)
- Reduced repetitive wrapper/import boilerplate in `src/tet4d/engine/api.py`
  across:
  - runtime menu/settings/config/schema helpers
  - keybinding menu helper dispatch
  - frontend/render adapter dispatch
- Reduced duplicated helper logic in `src/tet4d/ui/pygame/keybindings.py`
  (key-list parsing, key tuple filtering, conflict-apply branch flow, profile
  creation delegation).
- Consolidated duplicated action/route collection loops in
  `src/tet4d/engine/runtime/menu_structure_schema.py`.
- Reworded canonical `BKL-P2-027` title in `config/project/backlog_debt.json`
  to classify it as structural maintenance debt (not bug backlog semantics),
  aligning tech-debt bug-pressure input with actual bug-class issues.
- Verification:
  - targeted suites passed (`test_keybindings.py`, `test_menu_policy.py`,
    `test_front4d_render.py`, `test_front3d_setup.py`,
    `test_validate_project_contracts.py`)
  - `CODEX_MODE=1 ./scripts/verify.sh` passed
  - `python scripts/arch_metrics.py` passed with debt score decrease:
    `9.81 -> 7.04`.

Current sub-batch (2026-03-01): stage 791-800 governance + LOC cleanup.

- Advanced stage metadata:
  - `scripts/arch_metrics.py` (`ARCH_STAGE=800`)
  - `config/project/policy/manifests/architecture_metrics.json` (`arch_stage=800`)
- Closed traceability debt in active backlog source:
  - removed `BKL-P2-029` from `config/project/backlog_debt.json`
  - disambiguated duplicated backlog IDs in historical summaries using `-R2` rollover IDs.
- Added project-contract enforcement for backlog-ID uniqueness:
  - `tools/governance/validate_project_contracts.py`
  - `tests/unit/engine/test_validate_project_contracts.py`
- Reduced runtime/UI wrapper/parser duplication (no behavior change):
  - `src/tet4d/engine/runtime/menu_settings_state.py`
  - `src/tet4d/engine/runtime/menu_structure_schema.py`
  - `src/tet4d/ui/pygame/keybindings.py`
  - `src/tet4d/engine/api.py`
- Documentation dedup/cleanup:
  - moved legacy DONE summaries from this file to `docs/history/DONE_SUMMARIES.md`
  - converted this file to active/open + current-batch scope only.
- Verification:
  - targeted policy/menu/keybinding/front4d/project-contract test suites passed
  - `CODEX_MODE=1 ./scripts/verify.sh` passed
  - `python scripts/arch_metrics.py` passed.

## 6. Source Inputs

1. `config/project/backlog_debt.json`
2. `scripts/arch_metrics.py`
3. `config/project/policy/manifests/tech_debt_budgets.json`
4. `docs/rds/*.md`
5. `docs/ARCHITECTURE_CONTRACT.md`
6. `CURRENT_STATE.md`
7. `docs/history/DONE_SUMMARIES.md`
