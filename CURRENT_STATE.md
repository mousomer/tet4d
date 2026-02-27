# CURRENT_STATE (Restart Handoff)

Last updated: 2026-02-27
Branch: `codex/foldersrestructuring`
Worktree expectation at handoff: dirty (local `AGENTS.md` edit)

## Purpose

This file is a restart-ready handoff for long-running architecture cleanup work.
Read this first in a new Codex thread before continuing staged refactors.

## Current Architecture Snapshot

- `arch_stage`: `535` (from `scripts/arch_metrics.py`)
- Verification pipeline:
  - canonical local/CI gate is `./scripts/verify.sh`
  - `./scripts/ci_check.sh` is a thin wrapper over `./scripts/verify.sh`
- Architecture gates (must remain green):
  - `ui_to_engine_non_api = 0`
  - `ai_to_engine_non_api = 0`
  - `engine_core_to_engine_non_core_imports = 0`
  - `engine_core_purity.violation_count = 0`

## Current Debt Metrics (from `python3 scripts/arch_metrics.py`)

- `tech_debt.score = 5.37` (`low`)
  - weighted components:
    - backlog priority pressure (`P1/P2/P3` weighted open backlog load)
    - backlog bug/regression pressure (keyword-classified open backlog issues)
    - CI gate pressure (architecture budget overages + folder-balance gate violations)
    - code-balance pressure (`1 - leaf_fuzzy_weighted_balance_score_avg`)
    - keybinding-retention pressure (runtime binding inventory vs keybindings menu scope rendering; weighted higher than menu simplification)
    - menu-simplification pressure (launcher/pause/settings-hub complexity vs split-policy targets)
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
    - `src/tet4d/engine/runtime/score_analyzer_storage.py`
- `random_imports_non_test = 9`
- `time_imports_non_test = 0`

## Folder Balance Snapshot (top-level `.py` per package)

- `src/tet4d/engine`: `5`
- `src/tet4d/engine/ui_logic`: `6`
- `src/tet4d/engine/runtime`: `22`
- `src/tet4d/engine/gameplay`: `11`
- `src/tet4d/ui/pygame`: `8`
- `src/tet4d/ui/pygame/menu`: `10`
- `src/tet4d/ui/pygame/launch`: `7`
- `src/tet4d/ui/pygame/input`: `6`
- `src/tet4d/ui/pygame/render`: `9`
- `src/tet4d/ui/pygame/runtime_ui`: `8`
- `src/tet4d/ai/playbot`: `9`

### Balance Assessment

- `engine` top-level is now healthy.
- `engine/ui_logic` and `engine/gameplay` are healthy.
- `engine/runtime` is large but coherent (and leaf-gated at `watch` baseline).
- `ui/pygame/menu` and `ui/pygame/launch` are now balanced leaf subpackages.
- `ui/pygame/input` is now a balanced leaf package (`6` files, fuzzy `balanced`) after
  adding `keybindings_defaults`.
- `ui/pygame/render` is now a balanced leaf package (`9` files, fuzzy `balanced`) after
  panel/control/gfx/grid/font helper relocation.
- `ui/pygame/runtime_ui` is now a balanced leaf package (`8` files, fuzzy `balanced`)
  after consolidating shared loop orchestration helpers (`game_loop_common`,
  `loop_runner_nd`) with pause/help/audio/display/app bootstrap runtime UI helpers.
- `ui/pygame` top-level remains balanced and dropped further to `8` files after the
  `runtime_ui` help/pause move batch.

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

## Recent Batch Status (Stages 531-535)

Completed:
- Added repo-managed pre-push local CI gate:
  - `.githooks/pre-push`
  - `scripts/install_git_hooks.sh`
  - `scripts/bootstrap_env.sh` now installs hooks path (`core.hooksPath=.githooks`)
- Added rotated-view viewer-relative routing regression coverage in:
  - `tests/unit/engine/test_nd_routing.py`
  - coverage includes 3D yaw-based remapping, 4D `move_w_*` precedence, and axis-override precedence.
- Closed backlog items:
  - `BKL-P3-001` (pre-push local CI gate)
  - `BKL-P1-003` (viewer-relative movement regression verification)
  - `BKL-P1-002` (overlay-transparency control)
- Added overlay-transparency controls:
  - display default/persistence via `config/menu/defaults.json` + settings hub row
    (`Overlay transparency`, default `70%`).
  - in-game camera-key adjustment actions (`overlay_alpha_dec/inc`) in 3D/4D.
  - side-panel transparency bar + render-path split so alpha applies to active overlays
    only (active-piece cells remain opaque).
- Consolidated canonical tests under top-level `tests/unit/engine/`:
  - moved Python suites from legacy `src/tet4d/engine/tests/`.
  - updated folder-balance tracked leaf + class overrides and metrics source roots.
  - synchronized docs/contracts/backlog references and closed `BKL-P2-012`.
- Consolidated runtime loop helpers into `runtime_ui`:
  - moved `ui/pygame/loop/game_loop_common.py` and `ui/pygame/loop/loop_runner_nd.py`
    to `ui/pygame/runtime_ui/`.
  - canonicalized `cli/front2d.py`, `front3d_game.py`, and `front4d_game.py` imports
    to `tet4d.ui.pygame.runtime_ui.*`.
  - removed the tiny `ui/pygame/loop` Python leaf from folder-balance reporting.

Balance note:
- Folder-balance tracked leaf gates remain non-regressed:
  - `src/tet4d/engine/runtime`: `0.71 / watch`
  - `tests/unit/engine`: `1.0 / balanced`
- Tech-debt dropped vs stage-530 baseline:
  - `32.42 -> 5.37`
  - `moderate -> low`

## Open Issues / Operational Notes

- Some verification runs can fail transiently (historically score-snapshot determinism / benchmark spikes).
  - Policy: rerun once if failure matches known flaky pattern and no code changed.
- GitHub CI should be checked if local green diverges again, but recent governance fixes addressed the prior CI drift.

## Short-Term Plan (Next 10-20 stages)

### Track A (highest value): Rebalance `src/tet4d/ui/pygame`

Goal: reduce folder sprawl in `ui/pygame` by introducing a small number of coherent subpackages.

Recommended subpackages (incremental, not all at once):
- `src/tet4d/ui/pygame/menu/` (balanced)
- `src/tet4d/ui/pygame/input/` (balanced)
- `src/tet4d/ui/pygame/render/` (balanced)
- `src/tet4d/ui/pygame/runtime_ui/` (balanced)
- `src/tet4d/ui/pygame/launch/` (balanced)

Recommended next family moves (same staged pattern):
- `ui_utils` extraction decision (keep top-level utility, or pair it with another draw/layout helper if a coherent subpackage is justified)
- `projection3d` / `front3d_game` / `front4d_game` watch (defer until a renderer/viewer feature batch)
- `keybindings.py` decomposition planning (split internal sections before any package move)
- maintain split runtime help assets as the source of truth:
  - `config/help/content/runtime_help_content.json` (content)
  - `config/help/layout/runtime_help_layout.json` (layout/media placement rules)
  - no new hardcoded topic prose/layout rules in Python

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

- Practical completion (high confidence, low churn): `~6-18` stages
- Maximal clean architecture (strict cleanup / deeper pruning): `~16-36` stages

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
