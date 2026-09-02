# CURRENT_STATE (Restart Handoff)

Last updated: 2026-09-02
Working state: re-governance PR 3 on `codex/regovernance-lock-surface`, based
on merged PR 2 commit `a5d30db61c8821a71e94cb9ed430fe491ebd8ccc`

## Purpose

This file contains only the compact state needed to resume staged or
phase-dependent work. It is not workflow authority, a CI diary, a completed
stage archive, a task-contract ledger, or a future programme.

## Active Focus

- Current objective: close the final audit by deriving validator provenance
  from the real enforcement graph, enforcing canonical policy bytes and size,
  broadening lifecycle checks, and classifying topology authority as
  architecture without changing its semantics.
- Current blocker: none known for this governance-only cut.
- Established baseline: PR 2 merged green, master was clean at the SHA above,
  and this fresh branch was created from that exact commit. No frozen or
  unrelated feature branch is part of the change.
- Product and release execution chronology is intentionally excluded. Resume
  such work only from its owning RDS, release documentation, open backlog, and
  a newly approved task scope.

## Current Authority

- Machine governance and task routing: `config/project/policy_pack.json`
- Contributor dispatch: `AGENTS.md`
- Canonical human governance: the six owner files under `docs/governance/`
- Product behaviour: relevant `docs/rds/*`
- Architecture boundaries: `docs/ARCHITECTURE_CONTRACT.md`
- Subsystem ownership: `docs/architecture/authority_map.md`
- Open work and explicit deferrals: `docs/BACKLOG.md`
- Generated repository inventory: `docs/PROJECT_STRUCTURE.md`

## Next Acceptance Boundary

1. PR 3 is ready only when the active surface is at most 2,500 lines, the
   canonical policy pack is at most 1,000 lines and 80,000 bytes, the backlog is
   at most 250, exactly six owners and all routes remain valid, lifecycle and
   actual-enforcement provenance regressions fail adversarially, and focused
   plus full-repository checks are green.
2. Stop after PR 3. The frozen Windows/iPad release work remains separate.

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
- `tech_debt.score = 5.94` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 2.92`
2. `code_balance = 2.03`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`.

Top 8 live Python hotspots by real LOC:

1. `tests/unit/engine/test_topology_lab_menu.py`: `3804` real LOC
2. `tests/unit/render/test_locked_cell_explosion.py`: `3782` real LOC
3. `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`: `3194` real LOC
4. `tools/governance/validate_project_contracts.py`: `2676` real LOC
5. `src/tet4d/ui/pygame/front4d_render.py`: `2153` real LOC
6. `scripts/arch_metrics.py`: `1899` real LOC
7. `src/tet4d/ui/pygame/locked_cell_explosion/board_view.py`: `1883` real LOC
8. `src/tet4d/ui/pygame/endgame_animation.py`: `1869` real LOC

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

1. Confirm the branch and worktree before editing.
2. Read `AGENTS.md`, this handoff, and only the authorities routed for the
   current task.
3. Recompute the migration coverage and size boundaries if the baseline moved.
4. Run focused governance checks, generated-document checks, sanitation,
   `git diff --check`, and the full gate before completion.
