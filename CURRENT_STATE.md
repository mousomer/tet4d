# CURRENT_STATE (Restart Handoff)

Last updated: 2026-08-05
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
- Governance trajectory simplification is merged on `master` at `f7e519b0`.
  Active routing now uses the stable constitution, task contract, change
  classes, and completion report; completed stage detail remains historical.
- Godot visual consolidation was human accepted and merged at `6e06e00a`.
  Its viewport-control and persistence recovery was manually accepted and
  merged at `6bedb75a`.
- Canonical topology contract version 1 is merged on `master` at `86906eb8`.
  Shared topology-contract foundations are merged at `af01bbd6`, and Stage 53B
  native topology transport is merged at `fe867627` with strict profile/query
  transport and 59 shared Python/Godot-native acceptance fixtures.
- Stage 53C strict Python topology constructors are merged at `36972384`.
  Stage 53D topology persistence and legacy recovery is merged at `c7243828`.
  Stage 53E is merged at `22938485`. Stage 53F is merged and verified on
  `master` at `91b901f3`. The short-term Python boundary-governance programme
  is closed.
- Stage 54A is human accepted and merged on `master` at `bcf41519`.
- The active product authority is
  `docs/plans/professional_godot_game_programme.md`. Its first gate is a fully
  playable, professionally presented 4D Godot game that is ready for later
  topology, Explorer, challenge, and simulation extensions.
- The next implementation slice is Stage 54B-1: a shared topology-aware
  board-extent contract implementing the complete bounded-board rule. Stage
  54B-2 then adds direct Godot X/Y/Z/W setup, validation, and persistence.
- Stage 54C adds game-safe 4D slice-basis quarter-turns and focused instruction.
- Stage 54D provides the modern gameplay baseline in three ordered slices:
  next-piece preview, ghost piece, and Hold.
- Weak live 3D/4D grid visibility is known non-blocking visual debt. It is
  deferred to the Stage 54E visible-GUI playability review and does not block
  Stage 54B, Stage 54C, or Stage 54D.
- Godot topology gameplay, the Godot Topology Lab, the full Explorer, the
  challenge campaign, and unified gameplay/endgame/topology/explosion
  integration remain later programme phases.

## Current Authority

- Professional product programme and phase gates:
  `docs/plans/professional_godot_game_programme.md`
- Contributor workflow and change-class routing: `docs/WORKFLOW_CODEX.md`
- Governance router and reusable contracts: `docs/governance/README.md`
- Machine-readable policy: `config/project/policy_pack.json`
- Product behaviour: relevant `docs/rds/*`
- Architecture boundaries: `docs/ARCHITECTURE_CONTRACT.md`
- Subsystem authority and migration ownership:
  `docs/architecture/authority_map.md`
- Authority transfer and new-authority establishment:
  `docs/architecture/authority_transfer_protocol.md`
- Documentation routing: `docs/DOCUMENTATION_MAP.md`
- Open work and deferrals: `docs/BACKLOG.md`
- Generated structure inventory: `docs/PROJECT_STRUCTURE.md`

## Known Watchouts

- Python is reference authority only for inherited, untransferred behaviour.
  It is not the mandatory origin or universal oracle for new Godot/native
  product capabilities.
- Existing inherited behaviour moves through the authority-transfer protocol.
  New behaviour without a predecessor uses authority establishment with an
  owning contract, named owner, conformance evidence, and authority-map entry.
- Stage 54B must accept topology as an explicit board-validation input while
  implementing the bounded rule now; Strip and Möbius constraints activate
  later through the same interface. Do not introduce topology-blind duplicate
  minima in Godot or adapters.
- Stage 54D-1 presents inherited next-piece state. Stage 54D-2 presents an
  authoritative landing query. Stage 54D-3 introduces new Hold state and must
  complete an `AE-####` establishment record during implementation, not before
  concrete contract and evidence exist.
- Native topology transport accepts only values that satisfy the shared
  topology contract and runtime query contract. It does not coerce malformed
  scalar values into valid topology data.
- Stage 53B transports and validates topology data but does not transfer
  inherited topology semantics from Python/reference contracts to C++.
- Lenient persistence or human-input recovery must stay in named source
  adapters rather than topology domain constructors.
- Invalid topology movement caches are derived-data misses: discard and
  rebuild them from the authoritative profile and dimensions; never repair
  them into semantic state. Its separate C++-dependent setup-latency deferral
  remains in `docs/BACKLOG.md`.
- `state/topology/profiles.json` is a distinct version-1 edge-rule workspace
  format. Invalid existing storage may provide read-only defaults but must
  block ordinary save; destructive replacement requires an explicit recovery
  operation.
- Do not create a Python mirror solely to satisfy an obsolete universal-oracle
  claim.
- Do not let completed stage narratives return to universal agent prompts,
  review checklists, or active drift rules.
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
- `tech_debt.score = 6.04` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 2.90`
2. `code_balance = 2.15`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`.

Top 8 live Python hotspots by real LOC:

1. `tools/governance/validate_project_contracts.py`: `3941` real LOC
2. `tests/unit/engine/test_topology_lab_menu.py`: `3804` real LOC
3. `tests/unit/render/test_locked_cell_explosion.py`: `3782` real LOC
4. `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`: `3194` real LOC
5. `tests/unit/governance/test_governance_validate_project_contracts.py`: `2378` real LOC
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

1. Implement Stage 54B-1 — Shared Topology-Aware Board-Extent Contract.
2. Keep piece/config-bundle import readers and unrelated settings recovery as
   bounded, format-specific deferrals rather than reopening generic governance
   work.
