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
  `controls_panel_routing.py` for navigation/pane/shortcut/enter routing,
  `controls_panel_commands.py` for save/export/experiment command execution,
  `controls_panel_launch.py` for play-preview launch preparation and runtime
  handoff,
  `controls_panel.py` for the public shell facade and only the remaining
  shell-entry compatibility seams,
  `scene_state.py` for the state shape plus pane/tool/workspace routing,
  `scene_state_canonical.py` for canonical runtime sync/write and fallback
  storage handling,
  and `scene_state_probe.py` for probe selectors, probe mutations, and
  probe-state synchronization.
- Current topology-playground preview/playability contract is:
  `scene_preview_state.py` treats explorer topology plus resolved board dims as
  the only preview/playability signature, restores same-signature cached
  playability results when available, and queues deferred rigid analysis only
  for valid states whose rigid result is still unknown.
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
- Do not let `controls_panel.py` re-absorb routing, command, launch, or
  non-shell explorer mutation helpers; keep any retained compatibility
  re-exports thin and keep deferred playability ownership in
  `scene_preview_state.py`.
- Do not let probe-only, sandbox-only, helper-only, or non-topological launch
  state drift into the preview/playability signature; only explorer topology
  plus resolved board dims should invalidate cached preview/playability
  results.
- Do not let `scene_state.py` re-absorb canonical sync/write glue or
  probe-state normalization now owned by `scene_state_canonical.py` and
  `scene_state_probe.py`, and do not drift boundary/glue selection or
  highlight-glue helpers back through that facade once callers import the
  focused owner modules directly.
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
- `deep_imports.ui_to_engine_non_api.count = 216` (allowed under current rule)
- `deep_imports.ai_to_engine_non_api.count = 27` (allowed under current rule)
- `engine_core_purity.violation_count = 0`
- `migration_debt_signals.pygame_imports_non_test.count = 0`
- `tech_debt.score = 4.76` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 2.21`
2. `code_balance = 1.31`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`.

Top 8 live Python hotspots by real LOC:

1. `tests/unit/engine/test_topology_lab_menu.py`: `3667` real LOC
2. `src/tet4d/ui/pygame/endgame_animation.py`: `2145` real LOC
3. `scripts/arch_metrics.py`: `1890` real LOC
4. `src/tet4d/engine/tutorial/setup_apply.py`: `1496` real LOC
5. `tools/governance/validate_project_contracts.py`: `1368` real LOC
6. `src/tet4d/ui/pygame/front4d_render.py`: `1313` real LOC
7. `src/tet4d/ui/pygame/render/gfx_game.py`: `1243` real LOC
8. `tools/governance/generate_configuration_reference.py`: `989` real LOC

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
- Continue trimming only the remaining real shell-entry seams in
  `controls_panel.py` and `scene_state.py` without collapsing the focused
  helper splits back into one file.
- Keep the hardened preview/playability contract explicit: same-signature
  refreshes restore cached results when available, invalid preview states do
  not queue pointless rigid scans, and play-preview launch only forces
  completion when a valid rigid result is still pending.
- Keep governance edits pack-driven and update workflow/backlog/current-state
  docs together when boundary rules change.
