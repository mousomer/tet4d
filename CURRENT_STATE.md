# CURRENT_STATE (Restart Handoff)

Last updated: 2026-08-01
Worktree expectation: clean unless an active batch is in progress

## Purpose

This file is the compact restart handoff for staged, phase-dependent, or
multi-batch work. It is not workflow authority, a validation transcript, or a
history ledger. Detailed history is preserved in
`docs/history/current_state_archive_2026-07-30.md` and
`docs/history/DONE_SUMMARIES.md`.

## Active Focus

- The accepted Godot foundation is merged on `master` at `eb584e4f`. It
  includes configurable bounded setup, display/accessibility infrastructure,
  settings hardening, Godot 4.7.1, pinned native dependencies, blocking
  Godot/native/parity CI, and Ruff 0.16 migration.
- Python remains the semantic oracle. No topology, replay, endgame/explosion,
  or broader gameplay authority transferred to Godot or native C++.
- Governance trajectory simplification is merged on `master` at `f7e519b0`.
  Active routing now uses the stable constitution, task contract, change
  classes, and completion report; completed stage detail remains historical.
- Godot visual consolidation was human accepted and merged at `6e06e00a`.
  Its viewport-control and persistence recovery was manually accepted and
  merged at `6bedb75a`. Camera-relative grid rectangles occupy the three rear
  faces of every volumetric section while the three front faces remain clear;
  the recovered shell keeps Ctrl-only soft drop, direct mouse orbit/pan/zoom,
  persistent windowed state, readable W-slice labels, and restrained slice
  framing.
- Canonical topology contract version 1 is merged on `master` at `86906eb8`.
  It makes the existing paired-seam Python semantics strict, normalized,
  versioned, and identity-bearing, and extends the provisional native query
  parity surface with frame transport and board-extent validation. The merge
  does not transfer Python topology authority to native C++ or Godot; Godot
  carries only the documented DTO, adapter, parity, and query-facing surfaces.
- Broader native topology transport based on canonical topology contract v1 is
  the next ordered technical objective. That separate parity-backed slice has
  not begun and must not transfer Python authority.
- Godot topology gameplay, the Godot Topology Lab, and unified Godot
  gameplay/endgame/topology/explosion integration have not begun.

## Current Authority

- Contributor workflow and change-class routing: `docs/WORKFLOW_CODEX.md`
- Governance router and reusable contracts: `docs/governance/README.md`
- Machine-readable policy: `config/project/policy_pack.json`
- Product behavior: relevant `docs/rds/*`
- Architecture boundaries: `docs/ARCHITECTURE_CONTRACT.md`
- Migration ownership: `docs/architecture/authority_map.md`
- Documentation routing: `docs/DOCUMENTATION_MAP.md`
- Open work and deferrals: `docs/BACKLOG.md`
- Generated structure inventory: `docs/PROJECT_STRUCTURE.md`

## Known Watchouts

- Broader native topology transport must consume canonical contract v1 and
  remain parity-backed against the Python oracle.
- Do not move Python semantic authority through implementation convenience or
  visual plausibility; use the authority-transfer protocol.
- Do not let completed stage narratives return to universal agent prompts,
  review checklists, or active drift rules. Route historical evidence through
  the parity protocol, documentation map, and `docs/history/`.
- Keep `CURRENT_STATE.md` restart-only and `docs/BACKLOG.md` open-work-only.

Sections with `BEGIN/END GENERATED:*` markers are maintained by
`tools/governance/generate_maintenance_docs.py`.

<!-- BEGIN GENERATED:current_state_metric_snapshot -->
## Current Metric Snapshot

From `python scripts/arch_metrics.py`:

- `deep_imports.engine_to_ui_non_api.count = 0`
- `deep_imports.engine_to_ai_non_api.count = 0`
- `deep_imports.ui_to_engine_non_api.count = 290` (allowed under current rule)
- `deep_imports.ai_to_engine_non_api.count = 28` (allowed under current rule)
- `engine_core_purity.violation_count = 0`
- `migration_debt_signals.pygame_imports_non_test.count = 0`
- `tech_debt.score = 5.72` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 2.81`
2. `code_balance = 1.91`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`.

Top 8 live Python hotspots by real LOC:

1. `tests/unit/engine/test_topology_lab_menu.py`: `3804` real LOC
2. `tests/unit/render/test_locked_cell_explosion.py`: `3782` real LOC
3. `tools/governance/validate_project_contracts.py`: `3692` real LOC
4. `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`: `3194` real LOC
5. `tests/unit/governance/test_governance_validate_project_contracts.py`: `2183` real LOC
6. `src/tet4d/ui/pygame/front4d_render.py`: `2153` real LOC
7. `scripts/arch_metrics.py`: `1899` real LOC
8. `src/tet4d/ui/pygame/locked_cell_explosion/board_view.py`: `1883` real LOC

Thin-wrapper budgets:

1. `cli/front.py: 804/840 real LOC (compatibility launcher wrapper)`
2. `cli/front2d.py: 15/24 real LOC (thin 2D launcher shim)`
3. `cli/front3d.py: 15/24 real LOC (thin 3D launcher shim)`
4. `cli/front4d.py: 15/24 real LOC (thin 4D launcher shim)`
5. `src/tet4d/engine/api.py: 140/160 real LOC (small engine compatibility facade)`
6. `src/tet4d/ui/pygame/front2d_game.py: 116/180 real LOC (2D orchestration entrypoint)`

Tutorial wording drift guard:

1. Lesson copy must not start with `Goal:` or `Action:`.
2. Tutorial overlay must keep `Do this:`, `Tip:`, and `USE:` tokens.
<!-- END GENERATED:current_state_drift_watch -->

## Restart Checklist

1. Run `git branch --show-current` and `git status --short`.
2. Read `AGENTS.md`, this handoff, `docs/BACKLOG.md`, and the authorities
   routed for the active task.
3. Confirm the task contract, branch, acceptance criteria, and forbidden scope.
4. Run focused checks while iterating.
5. Before completion, run:

```bash
git diff --check
./scripts/check_git_sanitation_repo.sh
CODEX_MODE=1 ./scripts/verify.sh
```

## Next Steps

- Broader native topology transport based on canonical topology contract v1,
  implemented as a separate parity-backed slice without transferring Python
  authority. No implementation branch or PR for this objective currently
  exists.
