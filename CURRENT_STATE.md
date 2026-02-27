# CURRENT_STATE (Restart Handoff)

Last updated: 2026-02-27
Branch: `codex/foldersrestructuring`
Worktree expectation at handoff: dirty (local `AGENTS.md` edit)

## Purpose

This file is a restart-ready handoff for long-running architecture cleanup work.
Read this first in a new Codex thread before continuing staged refactors.

## Current Architecture Snapshot

- `arch_stage`: `695` (from `scripts/arch_metrics.py`)
- Verification pipeline:
  - canonical local/CI gate is `./scripts/verify.sh`
  - `./scripts/ci_check.sh` is a thin wrapper over `./scripts/verify.sh`
- Architecture gates (must remain green):
  - `ui_to_engine_non_api = 0`
  - `ai_to_engine_non_api = 0`
  - `engine_core_to_engine_non_core_imports = 0`
  - `engine_core_purity.violation_count = 0`

## Current Debt Metrics (from `python3 scripts/arch_metrics.py`)

- `tech_debt.score = 2.19` (`low`)
  - weighted components (current dominant drivers):
    - backlog priority pressure (`+0.00`, no active open backlog debt items)
    - code-balance pressure (`+0.12`, runtime leaf dropped to `0.87` fuzzy while still `balanced`)
    - delivery-size pressure (`+2.07`; increases with weighted LOC/file growth)
  - delivery-size calibration:
    - `loc_unit = 10600`, `file_unit = 64` (keeps size pressure monotonic while
      preserving stronger weighting for correctness/CI/boundary signals)
  - collection note:
    - keybinding-retention now runs in headless environments via a metrics-only pygame stub fallback, preventing false `unavailable` pressure in CI/local non-graphics contexts
  - strict gate policy:
    - same-stage commits: must not regress baseline score/status
    - stage-advance batches: must strictly decrease score versus baseline stage
- `pygame_imports_non_test = 3`
  - currently concentrated in:
    - `src/tet4d/engine/front3d_render.py`
    - `src/tet4d/engine/front4d_render.py`
    - `src/tet4d/engine/frontend_nd.py`
- `file_io_calls_non_test = 10`
  - concentrated in runtime storage helpers (acceptable placement debt):
    - `src/tet4d/engine/runtime/json_storage.py`
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

- `engine` top-level is now healthy.
- `engine/core/step` and `engine/core/rng` now use a micro-leaf balance profile and
  score `balanced`, reducing technical debt pressure without changing gate scope.
- `engine/ui_logic` and `engine/gameplay` are healthy.
- `engine/runtime` remains gate-eligible and balanced (`0.87` fuzzy), but is now
  the primary code-balance watch hotspot after wrapper pruning.
- `ui/pygame/menu` and `ui/pygame/launch` are balanced after launcher wrapper pruning.
- `ui/pygame/input` is now a balanced leaf package (`6` files, fuzzy `balanced`) after
  adding `keybindings_defaults`.
- `ui/pygame/render` is now a balanced leaf package (`11` files, fuzzy `balanced`) after
  panel/control/gfx/grid/font helper relocation.
- `ui/pygame/runtime_ui` remains balanced at `6` files after consolidating
  `display` and shared event-loop logic into canonical runtime modules.
- `ui/pygame` top-level remains balanced at `6` files after removing thin 3D/4D launch wrappers.
- `replay` remains `micro_feature_leaf` and balanced at `2` files.

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

## Recent Batch Status (Stages 676-695)

Completed:
- Completed help/menu/runtime wrapper pruning and canonicalized callers to
  stable engine-api/runtime entry points.
- Moved replay helpers into `src/tet4d/replay/__init__.py` and pruned
  thin replay wrapper modules.
- Consolidated runtime UI display and event-loop helpers into:
  - `src/tet4d/ui/pygame/runtime_ui/app_runtime.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
- Removed obsolete wrapper modules:
  - `src/tet4d/ui/pygame/front3d.py`
  - `src/tet4d/ui/pygame/front4d.py`
  - `src/tet4d/ui/pygame/launch/front3d_setup.py`
  - `src/tet4d/ui/pygame/launch/profile_4d.py`
  - `src/tet4d/ui/pygame/runtime_ui/display.py`
  - `src/tet4d/ui/pygame/runtime_ui/game_loop_common.py`
  - `src/tet4d/engine/runtime/assist_scoring.py`
  - `src/tet4d/engine/runtime/runtime_helpers.py`
  - `src/tet4d/engine/runtime/runtime_config_validation_audio.py`
  - `src/tet4d/engine/runtime/runtime_config_validation_gameplay.py`
  - `src/tet4d/replay/playback.py`
  - `src/tet4d/replay/record.py`
- Advanced stage metadata to `arch_stage=695`.
- Verified strict stage-advance debt decrease (`2.31 -> 2.19`) and refreshed strict
  tech-debt baseline at stage `695`.

Balance note:
- Folder-balance tracked leaf gates remain non-regressed:
  - `src/tet4d/engine/runtime`: `0.87 / balanced`
  - `tests/unit/engine`: `1.0 / balanced`
- Replay leaf remains `1.0 / balanced` under the micro profile.
- Tech debt decreased in this batch (`2.31 -> 2.19`) and baseline was refreshed at stage `695`.

## Open Issues / Operational Notes

- Some verification runs can fail transiently (historically score-snapshot determinism / benchmark spikes).
  - Policy: rerun once if failure matches known flaky pattern and no code changed.
- GitHub CI should be checked if local green diverges again, but recent governance fixes addressed the prior CI drift.

## Short-Term Plan (Next 10-20 stages)

### Track A (highest value): Continue Delivery-Size Pressure Reduction

Goal: reduce Python LOC in large runtime/UI modules without changing behavior.

Recommended next family moves:
- split `src/tet4d/ui/pygame/keybindings.py` into profile/IO/rebind helpers.
- split `src/tet4d/engine/runtime/menu_settings_state.py` into read/write/sanitize slices.
- trim duplicated runtime API wrapper boilerplate in `src/tet4d/engine/api.py` where safe.
- preserve config/help/menu assets as source-of-truth; avoid reintroducing large Python literals.

Pattern per family:
1. move implementation to subpackage
2. add compatibility shim at old path
3. canonicalize callers
4. zero-caller checkpoint
5. prune shim
6. checkpoint docs + metrics + verification
7. for each stage-batch checkpoint, ensure `tech_debt.score` decreases versus prior
   baseline stage before refreshing `config/project/tech_debt_budgets.json`

### Track B: Playbot relocation audit-only (deprioritized)

Goal: confirm no real `engine/playbot` Python module stragglers remain.

Current note:
- latest audit found no `*.py` files under `src/tet4d/engine/playbot/` (only local
  `__pycache__` artifacts), so no staged relocation work is currently queued.

### Track C: Runtime side-effect extraction (selective)

Goal: ensure any remaining file I/O outside `engine/runtime` is routed to runtime helpers.

Do:
- grep for `read_text`, `write_text`, `open(` in `src/tet4d/engine/**/*.py`
- only extract misplaced I/O (do not churn runtime-owned storage helpers)

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
- Canonical maintenance contract: `config/project/canonical_maintenance.json`
