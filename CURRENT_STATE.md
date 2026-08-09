# CURRENT_STATE (Restart Handoff)

Last updated: 2026-08-09
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
- PR #63 is merged on `master` at
  `c93dcc8cfa93857d514a14b925002efc4404b007`. Stages 54B-1 through 54D-2 are
  integrated: the topology-aware board-extent contract; editable validated
  setup; exact signed 4D basis; authoritative NEXT; and Ghost plus accepted
  presentation/control corrections.
- Stage 54E-1 is HUMAN ACCEPTED. Its accepted architecture contract is
  `docs/architecture/4d_presentation_interaction_architecture.md`: the
  combined-camera-yaw resolver is `DEFECTIVE`; Option A assigns shared
  slice-local orientation, anchor-only layout, and non-orienting normal
  Live-4D `V/P`; the F/R/Q and displayed-Forward/depth contracts are accepted.
  Normal-gameplay roll is removed in 54E-2 while reusable Explorer/free-
  inspection roll remains intended. Constrained pitch is accepted only where
  Pitch-depth preservation keeps Forward away from the viewer.
- Stage 54D-3 Hold is independently eligible. Stage 54E-2a is COMPLETE /
  REVIEWED GREEN: it established the first-class shared
  `SliceLocalOrientation`, explicit `B`, affine centred `G_D`, anchor-only
  layout decomposition, continuous `F(theta)`/`R(theta)`, and discrete `Q(q)`
  control projection distinction. Stage 54E-2b is COMPLETE / REVIEWED GREEN:
  it establishes `B -> G_D -> L -> anchor` renderer composition; one shared
  continuous `L`; aligned cells, active piece, Ghost, grids, and frames;
  anchor-only layout; oriented corner-derived fit bounds; and slice identity
  labels outside local physical rotation. Stage 54E-2c — interaction and
  camera-rig separation — is IMPLEMENTED / REVIEW PENDING: left-drag and
  keyboard yaw/pitch mutate the one shared `L`; relative controls consume
  exact `B + Q(L.local_yaw)`; outer pan/zoom/Fit remain framing-only; gameplay
  roll is detached while generic roll remains; preset yaw/pitch and framing
  are decomposed; and every `L` mutation rerenders oriented geometry, bounds,
  and the fit reference. The fixed far-side mount uses one renderer-only outer
  `V` reflection across the active camera's vertical/depth plane; the camera
  and HUD remain outside it. Actual `Camera3D.unproject_position()` evidence
  proves resolver-selected Right is screen-right, while effective camera-space
  depth proves resolver-selected Forward recedes. A review correction accounts
  for residual continuous yaw between
  `L.local_yaw` and `Q(L.local_yaw)`: the strict all-yaw pitch interval is
  approximately `(-42.480 degrees, +86.240 degrees)`, and normal gameplay uses
  `[-40 degrees, +60 degrees]` with a `2.480-degree` lower margin. Stage
  54E-2c final visual review identified and fixed an above-board active-spawn
  projection collapse that had initially looked like a stale Ghost cell; the
  investigation also hardened presentation-node teardown by synchronously
  detaching obsolete children before deferred destruction, but that hardening
  was not the root cause of the reported cube. It also restores face-connected
  cell adjacency inside each shared NEXT-thumbnail `W` group. Board spacing
  and grid/wireframe styling remain deferred visual-quality work tracked in
  `docs/BACKLOG.md` and GitHub Issues. Stage 54E-2d remains blocked until
  reviewed-green 54E-2c.
- Integrated professional playability/visual acceptance is now Stage 54F;
  professional gaming-experience and release hardening is Stage 54G.
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
- Stage 54B-2 must consume the established board-extent contract; Strip and
  Möbius constraints activate later through the same interface. Do not
  introduce topology-blind duplicate minima in Godot or adapters.
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
- Live 4D basis state is Godot presentation state only. Do not persist it,
  include it in snapshots/hashes, apply it to replay rendering, exchange Y,
  or duplicate native movement legality in GDScript.
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
- `tech_debt.score = 5.95` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 2.92`
2. `code_balance = 2.03`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`.

Top 8 live Python hotspots by real LOC:

1. `tools/governance/validate_project_contracts.py`: `4042` real LOC
2. `tests/unit/engine/test_topology_lab_menu.py`: `3804` real LOC
3. `tests/unit/render/test_locked_cell_explosion.py`: `3782` real LOC
4. `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`: `3194` real LOC
5. `tests/unit/governance/test_governance_validate_project_contracts.py`: `2427` real LOC
6. `src/tet4d/ui/pygame/locked_cell_explosion/board_view.py`: `3194` real LOC
7. `scripts/arch_metrics.py`: `1899` real LOC
8. `cli/front.py`: `804` real LOC

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

1. Review Stage 54E-2c — Interaction and camera-rig separation. Stage 54E-2d
   remains sequentially gated on reviewed-green 54E-2c, and Stage 54D-3 Hold
   remains independently eligible.
2. Keep piece/config-bundle import readers and unrelated settings recovery as
   bounded, format-specific deferrals rather than reopening generic governance
   work.
