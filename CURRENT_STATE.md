# CURRENT_STATE (Restart Handoff)

Last updated: 2026-03-07  
Branch: `master`  
Worktree expectation: dirty until this architecture batch is committed

## Purpose

This file is the restart handoff for the current architecture baseline. It is
not a historical ledger. Long historical migration detail belongs in
`docs/history/DONE_SUMMARIES.md`.

## Current Architecture Snapshot

- `arch_stage`: `900`
- Canonical local gate: `CODEX_MODE=1 ./scripts/verify.sh`
- CI wrapper: `./scripts/ci_check.sh`
- Dependency direction:
  - `ui`, `ai`, `replay`, and `tools` may import engine modules directly
  - `engine` must not import `ui`, `ai`, `replay`, or `tools`
  - `engine/core` remains strict-pure

## Current Metric Snapshot

From `python scripts/arch_metrics.py` on 2026-03-07:

- `deep_imports.engine_to_ui_non_api.count = 0`
- `deep_imports.engine_to_ai_non_api.count = 0`
- `deep_imports.ui_to_engine_non_api.count = 117` (allowed under current rule)
- `deep_imports.ai_to_engine_non_api.count = 26` (allowed under current rule)
- `engine_core_purity.violation_count = 0`
- `migration_debt_signals.pygame_imports_non_test.count = 0`
- `tech_debt.score = 2.34` (`low`)

Dominant remaining pressure:

1. `code_balance = 1.07`
2. `delivery_size_pressure = 1.26`

## Canonical Ownership After This Batch

### Engine

- `src/tet4d/engine/core/piece_transform.py`
- `src/tet4d/engine/core/rotation_kicks.py`
- `src/tet4d/engine/gameplay/*`
- `src/tet4d/engine/gameplay/api.py`
- `src/tet4d/engine/runtime/*`
- `src/tet4d/engine/runtime/api.py`
- `src/tet4d/engine/tutorial/*`
- `src/tet4d/engine/tutorial/api.py`
- `src/tet4d/engine/api.py` (small compatibility facade for replay/tests/tutorial payload exports)

### UI

- `src/tet4d/ui/pygame/front2d_game.py`
- `src/tet4d/ui/pygame/front2d_setup.py`
- `src/tet4d/ui/pygame/front2d_loop.py`
- `src/tet4d/ui/pygame/front2d_runtime.py` (compatibility facade)
- `src/tet4d/ui/pygame/frontend_nd.py`
- `src/tet4d/ui/pygame/front3d_game.py`
- `src/tet4d/ui/pygame/front4d_game.py`
- `src/tet4d/ui/pygame/front3d_render.py`
- `src/tet4d/ui/pygame/front4d_render.py`
- `src/tet4d/ui/pygame/runtime_ui/*`
- `src/tet4d/ui/pygame/menu/*`
- `src/tet4d/ui/pygame/launch/*`
- `src/tet4d/ui/pygame/render/*`

### AI

- `src/tet4d/ai/playbot/*`

## What This Batch Changed

1. Folded 2D into the shared `src/tet4d/ui/pygame/` frontend structure and split
   ownership into `front2d_game.py` (orchestration), `front2d_setup.py`
   (setup/menu), `front2d_loop.py` (runtime loop), and `front2d_runtime.py`
   (compatibility facade for legacy imports/tests).
2. Moved engine-owned render/frontend adapters out of `src/tet4d/engine/` into
   UI ownership.
3. Removed all remaining reverse imports from `engine` into `ui` and `ai`.
4. Decomposed engine-owned convenience exports into
   `src/tet4d/engine/gameplay/api.py`, `src/tet4d/engine/runtime/api.py`, and
   `src/tet4d/engine/tutorial/api.py`, while keeping `src/tet4d/engine/api.py`
   as a thin compatibility facade.
5. Cut `menu_settings_state` -> UI keybinding side effects; live keybinding sync
   now happens in UI runtime/menu code.
6. Repointed AI planners/controllers/dry-run tooling to direct engine imports,
   eliminating `engine -> ai` wrapper pressure in `engine/api.py`.
7. Centralized shared rotation-with-kicks application through
   `resolve_rotated_piece(...)`, deleting duplicated first-fit application logic
   from 2D and ND gameplay states.
8. Zeroed the reverse-import metric budgets and aligned the boundary script with
   the current one-way rule.
9. Rewrote stale architecture docs so they describe the current architecture,
   not the old migration-only `engine.api` seam.
10. Moved remaining governance and render-benchmark callers off `engine.api` onto
    direct engine/UI owners, then reduced `src/tet4d/engine/api.py` to a small
    compatibility facade used mainly by replay and explicit compatibility tests.
11. Split the 2D runtime loop into `src/tet4d/ui/pygame/front2d_loop.py`, kept
    `front2d_runtime.py` as a compatibility surface only, and moved affected
    tests to patch the real owner module.
12. Extracted the duplicated setup-menu event/save loop into
    `src/tet4d/ui/pygame/menu/setup_menu_runner.py` and rewired both 2D and ND
    setup flows to use it.
13. Removed duplicated settings/default wrappers from
    `src/tet4d/ui/pygame/launch/launcher_settings.py` by extending
    `src/tet4d/engine/runtime/menu_settings_state.py` and reusing
    `src/tet4d/engine/runtime/settings_schema.py` window-size helpers.

## Validation Status

Validation completed during this batch:

- focused `ruff check`: passed
- focused pytest batches covering the 2D split, compatibility facade, and shared kick-resolution paths: passed
- `python scripts/arch_metrics.py`: passed with zero reverse imports
- `CODEX_MODE=1 ./scripts/verify.sh`: passed
- `CODEX_MODE=1 ./scripts/ci_check.sh`: passed

## Known Hotspots

These are not current correctness bugs; they are watch areas for future LOC and
ownership reduction.

1. `src/tet4d/ui/pygame/launch/launcher_settings.py`
2. `src/tet4d/ui/pygame/frontend_nd.py`
3. `src/tet4d/ui/pygame/front2d_loop.py`
4. `src/tet4d/engine/runtime/`
5. `src/tet4d/ui/pygame/launch/`

## Next High-Value Follow-Ups

1. Keep shrinking `src/tet4d/ui/pygame/front2d_loop.py`; the loop owner is now
   isolated, but it is still one of the larger 2D-specific modules.
2. Continue reducing duplication between `src/tet4d/ui/pygame/frontend_nd.py` and
   `src/tet4d/ui/pygame/launch/launcher_settings.py` now that the setup-menu loop
   and settings/default helpers are shared owners.
3. Keep trimming oversized UI/runtime owners in `src/tet4d/ui/pygame/launch/` and
   `src/tet4d/engine/runtime/` without reintroducing wrapper layers.
4. Keep docs, budgets, and package manifests synchronized whenever ownership changes.

## Restart Checklist

1. `git branch --show-current`
2. `git status --short`
3. Read:
   - `AGENTS.md`
   - `docs/RDS_AND_CODEX.md`
   - `docs/ARCHITECTURE_CONTRACT.md`
   - `CURRENT_STATE.md`
4. Capture fresh metrics:

```bash
python scripts/arch_metrics.py
```

5. Re-run the local gate before commit:

```bash
CODEX_MODE=1 ./scripts/verify.sh
./scripts/ci_check.sh
```
