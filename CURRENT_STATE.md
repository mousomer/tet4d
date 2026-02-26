# CURRENT_STATE (Restart Handoff)

Last updated: 2026-02-26
Branch: `codex/foldersrestructuring`
Worktree expectation at handoff: dirty (local `AGENTS.md` edit)

## Purpose

This file is a restart-ready handoff for long-running architecture cleanup work.
Read this first in a new Codex thread before continuing staged refactors.

## Current Architecture Snapshot

- `arch_stage`: `520` (from `scripts/arch_metrics.py`)
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
- `src/tet4d/ui/pygame`: `8`
- `src/tet4d/ui/pygame/menu`: `10`
- `src/tet4d/ui/pygame/launch`: `7`
- `src/tet4d/ui/pygame/input`: `6`
- `src/tet4d/ui/pygame/loop`: `3`
- `src/tet4d/ui/pygame/render`: `9`
- `src/tet4d/ui/pygame/runtime_ui`: `6`
- `src/tet4d/ai/playbot`: `9`

### Balance Assessment

- `engine` top-level is now healthy.
- `engine/ui_logic` and `engine/gameplay` are healthy.
- `engine/runtime` is large but coherent (and leaf-gated at `watch` baseline).
- `ui/pygame/menu` and `ui/pygame/launch` are now balanced leaf subpackages.
- `ui/pygame/input` is now a balanced leaf package (`6` files, fuzzy `balanced`) after
  adding `keybindings_defaults`.
- `ui/pygame/loop` is a small but coherent new leaf package (`3` files, fuzzy `watch`)
  containing shared loop orchestration helpers (`game_loop_common`, `loop_runner_nd`).
- `ui/pygame/render` is now a balanced leaf package (`9` files, fuzzy `balanced`) after
  panel/control/gfx/grid/font helper relocation.
- `ui/pygame/runtime_ui` is now a balanced leaf package (`6` files, fuzzy `balanced`)
  after moving shared pause/help overlays alongside audio/display/app bootstrap helpers.
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

## Recent Batch Status (Stages 511-520)

Completed:
- Split runtime help assets into separate non-python content and layout files:
  - `config/help/content/runtime_help_content.json`
  - `config/help/layout/runtime_help_layout.json`
- Added dedicated runtime help schemas:
  - `config/schema/help_runtime_content.schema.json`
  - `config/schema/help_runtime_layout.schema.json`
- Refactored runtime loader/validation helper:
  - `src/tet4d/engine/help_text.py`
- Added engine API wrappers used by pygame runtime help UI:
  - `help_topic_block_lines_runtime`
  - `help_topic_compact_limit_runtime`
  - `help_topic_compact_overflow_line_runtime`
  - `help_value_template_runtime`
  - `help_action_group_heading_runtime`
  - `help_fallback_topic_runtime`
  - `help_layout_payload_runtime`
  - `help_topic_media_rule_runtime`
- Rewired `src/tet4d/ui/pygame/runtime_ui/help_menu.py` to load runtime help prose from
  `config/help/content/runtime_help_content.json` and layout/media placement rules from
  `config/help/layout/runtime_help_layout.json` (`context`, profile name, live
  bindings, piece-set labels, compact overflow counters, controls topic media mode).
- Added/extended runtime help loader tests:
  - `src/tet4d/engine/tests/test_help_text.py`
- Synced help contracts:
  - `config/project/canonical_maintenance.json`
  - `docs/help/HELP_INDEX.md`
  - `docs/PROJECT_STRUCTURE.md`
  - `docs/RDS_AND_CODEX.md`
- Added stage-level LOC logger output in `scripts/arch_metrics.py`:
  - `stage_loc_logger.arch_stage`
  - `stage_loc_logger.overall_python_loc`
  - `stage_loc_logger.overall_python_file_count`
  - `stage_loc_logger.overall_python_folder_count`
  - `stage_loc_logger.by_top_package_loc`

Balance note:
- Folder balance is unchanged by this batch (text externalization + helper wiring only).
- `src/tet4d/ui/pygame/runtime_ui` remains `6` Python files and `balanced`.
- Top-level `src/tet4d/ui/pygame` remains `8` Python files and `balanced`.
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
- `src/tet4d/ui/pygame/loop/` (small/coherent)
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
- `loop/` and `runtime_ui/` optional follow-up consolidation only when a cohesive helper pair is ready (avoid tiny leaf churn)

Pattern per family:
1. move implementation to subpackage
2. add compatibility shim at old path
3. canonicalize callers
4. zero-caller checkpoint
5. prune shim
6. checkpoint docs + metrics + verification

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
- Docs and architecture contract reflect the final canonical paths

### Estimated Remaining Effort

- Practical completion (high confidence, low churn): `~6-18` stages
- Maximal clean architecture (strict cleanup / deeper pruning): `~16-36` stages

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
