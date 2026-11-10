# CURRENT_STATE (Restart Handoff)

Harness repair consumes distribution 1.4.0 / runtime 0.7.0. Candidate and
immutable kit gates, source/skill integrity, guarded direct adoption and manual
owner migrations are retained in durable private receipts. Tet4D's current
native verifier and committed project rules are preserved in the reviewed
binding. The owner selected harness repairs and existing offline checks;
the private fleet audit owns fresh scoped outcomes and remaining gaps.
Protected data, historical releases/evidence, product authority and deferred
telemetry gates remain intact. The plan is
`docs/plans/policy_kit_logging_and_meta_testing_repairs.md`.
The Stage 56H unified baseline is committed at `0cb30958`.
## Purpose

This file contains only the compact state needed to resume staged or
phase-dependent work. It is not workflow authority, a CI diary, a completed
stage archive, a task-contract ledger, or a future programme.
## Active Focus

Explorer T2A implements the native bounded/cylinder/torus translation candidate and permanent preservation suite described in `docs/architecture/explorer_topology_t2a_native_transport.md`. T1 PRs #172–#176 are the accepted baseline; remaining Correction 4B P2 findings stay deferred. T2B Godot integration is in progress on `codex/t2b-godot-2d-topology-explorer`; its interface and acceptance are recorded in `docs/architecture/explorer_topology_t2b_godot.md`. T2C rotations/twisted profiles and complete T2 acceptance remain separate. Runtime authority has not transferred. See `docs/BACKLOG.md` and `docs/architecture/explorer_topology_t2_transfer_preparation.md`. T2B now includes the PR #179 fullscreen safe-area correction. On 2026-11-10 the owner reported cylinder and torus working; detailed scenario and fullscreen acceptance remain open.
Bounded MVP novice acceptance remains pending in `docs/plans/bounded_practice_explorer.md`; unified VIEW helpers and compact Settings/Designer menus remain the baseline.

Machine-readable handoff state. `status` is `active` only on a feature branch
or draft PR and must name that branch; it is `none` on the default branch and
on any non-draft PR targeting it. `tools/governance/validate_handoff_lifecycle.py`
enforces this.

<!-- BEGIN HANDOFF:state -->
```json
{
  "schema_version": 1,
  "status": "none",
  "branch": null,
  "pull_request": null
}
```
<!-- END HANDOFF:state -->

<!-- BEGIN HANDOFF:notes -->
No active handoff.
<!-- END HANDOFF:notes -->

## Current Authority

- Workspace/project routing: `.governance/workspace.json` and
  `config/governance/project.json`
- Unmigrated machine governance and route compatibility facade:
  `config/project/policy_pack.json`
- Contributor dispatch: `AGENTS.md`
- Canonical human governance: the six owner files under `docs/governance/`
- Product behaviour: relevant `docs/rds/*`
- Architecture boundaries: `docs/ARCHITECTURE_CONTRACT.md`
- Subsystem ownership: `docs/architecture/authority_map.md`
- Open work and explicit deferrals: `docs/BACKLOG.md`
- Stage 56 task contract: `docs/tasks/live_4d_cockpit_convergence.md`
- Generated repository inventory: `docs/PROJECT_STRUCTURE.md`

## Next Acceptance Boundary

Next: bounded Designer text-size review; replay toolbar assessment stays separate.
Repair accepted; publication/master CI is tracked on PR #162. 58B scale stays frozen.
Stage 58C.7 is owner-accepted with documented tradeoffs; see
`docs/history/stage_58c_owner_acceptance_2026_11_02.md`. Stage 58D stays separate.
The Stage 56H human playability checkpoint retains its task contract at
`docs/tasks/live_4d_cockpit_convergence.md`; Stage 56I polish and the 190/200
A/B decision remain separate. Governance distribution 1.4.0 / runtime 0.7.0 is active;
its rollout and proof limits are recorded in
`docs/plans/all_repository_governance_rollout.md` and the private fleet audit.
P1b/P1c/P6 continuation and separate comparison/blocking gates remain required.
The implemented repair contract is recorded in
`docs/plans/policy_kit_logging_and_meta_testing_repairs.md`; fresh successor
evidence is separate from the retained historical records. Unrecoverable Git metadata, unresolved product contracts, sanitation limits
and census gaps remain separate acceptance boundaries. IQA product execution stays held at its model-download boundary; RMBG
verification follows its reviewed temporary-input repair.
The human session includes direct Play and `2`/`3`/`4` entry, `C` Change Setup,
and frozen-setup Restart/Play Again under
`docs/architecture/editable_board_setup_and_persistence.md`.
Shell readability uses 24/22 px text, a Main Menu that scales to fit (scrolling
only below its floor), and visible launch Play. Scale: menus 1280×720 pt, tighter axis, 0.75–2×; live/replay 1280×800 pt, 1–2×.
Include resizing, navigation, and guide layout in human acceptance.
The correction on `claude/stage-56h-gameplay-ergonomics` from `0cb30958`
requires actual-region fitting, styled legends, orthogonal grid modes, and
session-only Designer panel Move/Resize with native-hash isolation. Human
playability remains the acceptance boundary after automated geometry gates.
Preserve synchronous fitting when valid visible geometry already exists,
including Reset View and Designer comparison loading. Human playability remains
separate from automated geometry and local Metal screenshot inspection.
Durable open work and release-matrix deferrals remain in `docs/BACKLOG.md`.

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
- `tech_debt.score = 6.02` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 3.11`
2. `code_balance = 1.91`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`.

Top 8 live Python hotspots by real LOC:

1. `tests/unit/engine/test_topology_lab_menu.py`: `3804` real LOC
2. `tests/unit/render/test_locked_cell_explosion.py`: `3782` real LOC
3. `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`: `3194` real LOC
4. `tools/governance/validate_project_contracts.py`: `2754` real LOC
5. `src/tet4d/ui/pygame/front4d_render.py`: `2153` real LOC
6. `tools/workspace_governance/validators/core.py`: `2104` real LOC
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

1. Confirm the branch and worktree before editing.
2. Read `AGENTS.md`, this handoff, and only the authorities routed for the
   current task.
3. Recompute the migration coverage and size boundaries if the baseline moved.
4. Run focused governance checks, generated-document checks, sanitation,
   `git diff --check`, and the full gate before completion.
