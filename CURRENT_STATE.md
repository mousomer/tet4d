# CURRENT_STATE (Restart Handoff)

Last updated: 2026-04-17  
Worktree expectation: clean unless an active batch is in progress

## Purpose

This file is the restart handoff for the current repo baseline. It is not a
historical ledger, a validation transcript, or a second workflow authority.
Historical rollout detail belongs in `docs/history/DONE_SUMMARIES.md`.

## Active Focus

- Primary product cleanup still routes through
  `docs/plans/topology_playground_current_authority.md` and
  `docs/BACKLOG.md`.
- Current topology-playground helper ownership is:
  `controls_panel_rows.py` for row inventory,
  `controls_panel_values.py` for display/value derivation,
  `controls_panel_actions.py` for explorer row mutations and seam-edit actions,
  and `controls_panel.py` for shell/input/launch orchestration plus thin
  compatibility re-exports.
- Governance after the policy-pack migration stays locked to:
  `config/project/policy_pack.json` for machine-readable policy,
  `docs/WORKFLOW_CODEX.md` for human workflow, and `CURRENT_STATE.md` for
  restart-only handoff.
- Generated ownership and source-of-truth inventories live in
  `docs/PROJECT_STRUCTURE.md`, not here.

## Current Authority

- For topology-playground architecture and active migration-state questions,
  start with `docs/plans/topology_playground_current_authority.md`.
- For topology-playground shell behavior, use
  `docs/plans/topology_playground_shell_redesign_spec.md`.
- For repo workflow, verification sequencing, and context-switch guidance, use
  `docs/WORKFLOW_CODEX.md`.
- For active open work and current change footprint, use `docs/BACKLOG.md`.
- For historical detail only, use `docs/history/DONE_SUMMARIES.md` and
  `docs/history/topology_playground/current_state_archive_2026-03-31.md`.

## Known Watchouts

- Do not reopen Stage 1 governance by reintroducing deleted split-authority
  files or a second machine-readable policy source.
- Do not let `tools/governance/validate_project_contracts.py` regain
  policy-shaped inventories that belong in `config/project/policy_pack.json`.
- Do not let `CURRENT_STATE.md` regrow batch ledgers, validation histories, or
  generated ownership snapshots.
- Do not let `controls_panel.py` re-absorb non-shell explorer mutation helpers;
  keep any retained compatibility re-exports thin and keep deferred
  playability ownership in `scene_preview_state.py`.
- Keep `docs/BACKLOG.md` as the open-work tracker and
  `docs/PROJECT_STRUCTURE.md` as the generated structure/source-of-truth
  inventory.

Sections with `BEGIN/END GENERATED:*` markers are maintained by
`tools/governance/generate_maintenance_docs.py`.

<!-- BEGIN GENERATED:current_state_metric_snapshot -->
## Current Metric Snapshot

From `python scripts/arch_metrics.py`:

- `deep_imports.engine_to_ui_non_api.count = 0`
- `deep_imports.engine_to_ai_non_api.count = 0`
- `deep_imports.ui_to_engine_non_api.count = 208` (allowed under current rule)
- `deep_imports.ai_to_engine_non_api.count = 27` (allowed under current rule)
- `engine_core_purity.violation_count = 0`
- `migration_debt_signals.pygame_imports_non_test.count = 0`
- `tech_debt.score = 4.73` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 2.18`
2. `code_balance = 1.31`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`.

Top 8 live Python hotspots by real LOC:

1. `tests/unit/engine/test_topology_lab_menu.py`: `3665` real LOC
2. `src/tet4d/ui/pygame/endgame_animation.py`: `2145` real LOC
3. `scripts/arch_metrics.py`: `1890` real LOC
4. `src/tet4d/engine/tutorial/setup_apply.py`: `1496` real LOC
5. `tools/governance/validate_project_contracts.py`: `1368` real LOC
6. `src/tet4d/ui/pygame/front4d_render.py`: `1313` real LOC
7. `src/tet4d/ui/pygame/render/gfx_game.py`: `1243` real LOC
8. `src/tet4d/ui/pygame/topology_lab/scene_state.py`: `1087` real LOC

Thin-wrapper budgets:

1. `cli/front.py: 819/840 real LOC (compatibility launcher wrapper)`
2. `cli/front2d.py: 15/24 real LOC (thin 2D launcher shim)`
3. `cli/front3d.py: 15/24 real LOC (thin 3D launcher shim)`
4. `cli/front4d.py: 15/24 real LOC (thin 4D launcher shim)`
5. `src/tet4d/engine/api.py: 91/160 real LOC (small engine compatibility facade)`
6. `src/tet4d/ui/pygame/front2d_game.py: 116/180 real LOC (2D orchestration entrypoint)`

Tutorial wording drift guard:

1. Lesson copy must not start with `Goal:` or `Action:`.
2. Tutorial overlay must keep `Do this:`, `Tip:`, and `USE:` tokens.
<!-- END GENERATED:current_state_drift_watch -->

## Restart Checklist

1. `git branch --show-current`
2. `git status --short`
3. Read:
   - `AGENTS.md`
   - `CURRENT_STATE.md`
   - `docs/WORKFLOW_CODEX.md`
   - `docs/BACKLOG.md`
   - `docs/PROJECT_STRUCTURE.md`
4. If the task is architecture-sensitive, capture fresh metrics:

```bash
python scripts/arch_metrics.py
```

5. Re-run the local gate before commit or handoff:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

## Next Steps

- Continue topology-playground cleanup from `docs/BACKLOG.md` without reopening
  the frozen shell contract.
- Continue cleanup pressure in `scene_state.py` and in the remaining
  shortcut/export/launch orchestration inside `controls_panel.py` without
  collapsing the new helper split back into one file.
- Keep governance edits pack-driven and update workflow/backlog/current-state
  docs together when boundary rules change.
