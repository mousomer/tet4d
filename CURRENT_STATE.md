# CURRENT_STATE (Restart Handoff)

Last updated: 2026-02-26
Branch: `codex/foldersrestructuring`
Worktree expectation at handoff: dirty (local `AGENTS.md` edit + uncommitted Stage 431-450 batch)

## Purpose

This file is a restart-ready handoff for long-running architecture cleanup work.
Read this first in a new Codex thread before continuing staged refactors.

## Current Architecture Snapshot

- `arch_stage`: `450` (from `scripts/arch_metrics.py`)
- Verification pipeline:
  - canonical local/CI gate is `./scripts/verify.sh`
  - `./scripts/ci_check.sh` is a thin wrapper over `./scripts/verify.sh`
- Architecture gates (must remain green):
  - `ui_to_engine_non_api = 0`
  - `ai_to_engine_non_api = 0`
  - `engine_core_to_engine_non_core_imports = 0`
  - `engine_core_purity.violation_count = 0`

## Current Debt Metrics (from `python3 scripts/arch_metrics.py`)

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
- `src/tet4d/ui/pygame`: `24`
- `src/tet4d/ui/pygame/menu`: `10`
- `src/tet4d/ui/pygame/launch`: `7`
- `src/tet4d/ui/pygame/input`: `5`
- `src/tet4d/ai/playbot`: `9`

### Balance Assessment

- `engine` top-level is now healthy.
- `engine/ui_logic` and `engine/gameplay` are healthy.
- `engine/runtime` is large but coherent (and leaf-gated at `watch` baseline).
- `ui/pygame/menu` and `ui/pygame/launch` are now balanced leaf subpackages.
- `ui/pygame/input` is now a balanced leaf package (`5` files, fuzzy `balanced`) after
  the mouse/view helper moves.
- `ui/pygame` remains the current structural hotspot, but it dropped from `26` to `24`
  top-level Python files and improved again within the non-leaf `skewed` band.

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

## Recent Batch Status (Stages 431-450)

Completed:
- Extended `src/tet4d/ui/pygame/input/` with camera/view input helpers:
  - `ui/pygame/camera_mouse.py` -> `ui/pygame/input/camera_mouse.py`
  - `ui/pygame/view_controls.py` -> `ui/pygame/input/view_controls.py`
- Canonicalized callers across UI frontends, engine render/front helpers, and engine
  tests to `tet4d.ui.pygame.input.camera_mouse` / `tet4d.ui.pygame.input.view_controls`.
- Pruned zero-caller top-level `ui/pygame/camera_mouse.py` and
  `ui/pygame/view_controls.py` shims after caller canonicalization.
- Updated staged architecture/backlog checkpoint history and handoff notes for the new
  canonical `ui/pygame/input/*` paths.

Balance note:
- `src/tet4d/ui/pygame/input` is now balanced at `5` Python files (`234` LOC total),
  fuzzy score `1.0` (`balanced`) due margin-expanded target plateau.
- Top-level `src/tet4d/ui/pygame` dropped from `26` to `24` Python files and improved to
  fuzzy score `0.58` (`skewed`, still the primary structural hotspot).
- Leaf folder-balance gate remains non-regressed:
  - `src/tet4d/engine/runtime`: `0.71 / watch`
  - `src/tet4d/engine/tests`: `1.0 / balanced`

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
- `src/tet4d/ui/pygame/render/`
- `src/tet4d/ui/pygame/launch/` (balanced)

Recommended next family moves (same staged pattern):
- `keybindings_defaults` (pairs naturally with `input/key_dispatch.py` + `input/key_display.py`)
- `game_loop_common` (candidate for `input/` or a future `loop/` subpackage, depending on caller review)
- `panel_utils` / `ui_utils` family (likely better grouped under a future `render/` or `layout/` subpackage)

Pattern per family:
1. move implementation to subpackage
2. add compatibility shim at old path
3. canonicalize callers
4. zero-caller checkpoint
5. prune shim
6. checkpoint docs + metrics + verification

### Track B: Continue playbot physical relocation cleanup

Goal: finish remaining `engine/playbot` physical ownership debt.

Do:
- audit `src/tet4d/engine/playbot/*` remaining files
- move low-risk stragglers to `src/tet4d/ai/playbot/`
- keep `ai_to_engine_non_api = 0` by extending `engine.api` wrappers if needed

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
- Docs and architecture contract reflect the final canonical paths

### Estimated Remaining Effort

- Practical completion (high confidence, low churn): `~20-35` stages
- Maximal clean architecture (strict cleanup / deeper pruning): `~30-55` stages

### Estimated LOC Impact

- Next ~10 stages: roughly `-50` to `+50` LOC net (API prep adds, shim pruning removes)
- Near-maximal completion: roughly `-200` to `-600` LOC net (shim retirement dominates)

## Test Structure Preference (Planned Future Refactor)

Preference recorded:
- move toward a single top-level test root `./tests/`
- organize by sub-test tasks/domains (unit/integration/runtime/ui/etc.)

Status:
- not started (tests remain in `src/tet4d/engine/tests/` and other existing locations)

Recommended approach:
- dedicated staged migration (do not mix with architecture module moves)
- migrate one test family/domain at a time
- update pytest discovery and path-based tooling incrementally

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
