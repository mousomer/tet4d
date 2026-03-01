# CURRENT_STATE (Restart Handoff)

Last updated: 2026-03-01
Branch: `codex/foldersrestructuring`
Worktree expectation at handoff: dirty (policy additions + doc refresh pending commit)

## Purpose

This file is a restart-ready handoff for long-running architecture cleanup work.
Read this first in a new Codex thread before continuing staged refactors.

## Current Architecture Snapshot

- `arch_stage`: `715` (from `scripts/arch_metrics.py`)
- Verification pipeline:
  - canonical local/CI gate is `./scripts/verify.sh`
  - `./scripts/ci_check.sh` is a thin wrapper over `./scripts/verify.sh`
- Architecture gates (must remain green):
  - `ui_to_engine_non_api = 0`
  - `ai_to_engine_non_api = 0`
  - `engine_core_to_engine_non_core_imports = 0`
  - `engine_core_purity.violation_count = 0`

## Current Debt Metrics (from `python3 scripts/arch_metrics.py`)

- `tech_debt.score = 24.21` (`low`, equal to strict baseline 24.21)
  - weighted components (current dominant drivers):
    - backlog priority pressure: `19.38` (weights dominated by open P1/P2 items)
    - backlog bug pressure: `2.64`
    - delivery-size pressure: `2.07` (163 Python files, 30,210 LOC; weights: src=1.0, tests=0.35, tools/scripts=0.2)
    - code-balance pressure: `0.12` (gate-eligible leaf avg 0.99, runtime leaf balanced)
    - menu/keybinding retention pressures: `0.0` (goals met)
  - strict gate policy:
    - same-stage commits must not exceed baseline score/status
    - stage-advance batches must strictly decrease score versus baseline stage
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

- Gate-eligible leafs remain balanced (runtime leaf fuzzy 0.99, tests leaf 1.0).
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

## Recent Batch Status (Stages 696-715)

Completed:
- Added runtime schema/sanitization extraction modules:
  - `src/tet4d/engine/runtime/settings_schema.py`
  - `src/tet4d/engine/runtime/settings_sanitize.py`
  - `src/tet4d/engine/runtime/menu_structure_schema.py`
- Refactored runtime configuration and menu-state loading to use schema/sanitizer
  helpers, reducing duplicated validation logic in:
  - `src/tet4d/engine/runtime/menu_config.py`
  - `src/tet4d/engine/runtime/menu_settings_state.py`
- Pruned thin or duplicate helper files after caller canonicalization:
  - `src/tet4d/engine/runtime/menu_persistence.py`
  - `src/tet4d/engine/runtime/runtime_config_validation_shared.py`
  - `src/tet4d/engine/runtime/json_storage.py`
  - `src/tet4d/ui/pygame/menu/menu_model.py`
  - `src/tet4d/engine/core/model/types.py`
- Advanced stage metadata to `arch_stage=715`.
- Verified stage debt decrease (`2.19 -> 2.18`) with tracked folder gates non-regressed.
- Post-stage incremental LOC cleanup on `codex/loc-slim-batch` (same stage baseline):
  - externalized ND piece-set literals to `config/gameplay/piece_sets_nd.json`
  - externalized keybinding defaults to `config/keybindings/defaults.json`
  - centralized random-mode labels through `config/menu/structure.json` option labels
  - deduplicated launcher settings/default-loader paths and keybinding declaration/header duplicates
  - maintained strict same-stage gate (`tech_debt.score = 24.21`, `low`) under `CODEX_MODE=1 ./scripts/verify.sh`

Balance note:
- Folder-balance tracked leaf gates remain non-regressed:
  - `src/tet4d/engine/runtime`: `0.86 / balanced`
  - `tests/unit/engine`: `1.0 / balanced`
- Replay leaf remains `1.0 / balanced` under the micro profile.
- Tech debt decreased in this batch (`2.19 -> 2.18`).

## Open Issues / Operational Notes

- Tech-debt gate is tight (baseline 24.21); any LOC/file growth without relief risks failing the soft gate.
- Verification flakiness (metrics determinism/benchmarks) remains rare; rerun once if failure occurs with no code change.
- GitHub CI must stay aligned; local verify is authoritative pre-push.

## Active Plan (Policy-Integrated)

Batch objective:
- continue staged architecture cleanup while preserving strict non-regression
  gates and reducing `tech_debt.score` at each stage-advance checkpoint; stay net-LOC-neutral or negative unless shipping a feature.

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
