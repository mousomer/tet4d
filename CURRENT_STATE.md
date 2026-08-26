# CURRENT_STATE (Restart Handoff)

Last updated: 2026-08-26
Worktree expectation: clean unless an active batch is in progress

## Purpose

This file is the compact restart handoff for staged, phase-dependent, or
multi-batch work. It is not workflow authority, a validation transcript, or a
history ledger. Detailed history is preserved in
`docs/history/current_state_archive_2026-07-30.md` and
`docs/history/DONE_SUMMARIES.md`.

## Active Focus

- Completed bounded follow-on: `codex/presentation-parameter-contract` starts
  from the locally accepted release-hardening stack at
  `7d9d3872180905e67874329f8046f336744a348e`. It implements a typed,
  uniquely-owned presentation-parameter registry, detached schema-1
  `PresentationProfile`, schema-3 settings reuse, and one bounded live app
  apply path over unchanged deterministic state. Focused, governance,
  sanitation, pinned Godot 4.7.1, full-repository, and agent-driven real-window
  checks pass. The acceptance record is
  `docs/plans/presentation_parameter_contract_acceptance.md`. This work does
  not reopen historical Stage 54E-4 or alter native/gameplay, replay/hash,
  basis, Hold, NEXT, Ghost-truth, or camera-pose authority.

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
  camera-rig separation — is COMPLETE / REVIEWED GREEN: left-drag and keyboard
  yaw/pitch mutate the one shared `L`; relative controls consume exact
  `B + Q(L.local_yaw)`; outer pan/zoom/Fit remain framing-only; gameplay roll
  is detached while generic roll remains; preset yaw/pitch and framing are
  decomposed; and every `L` mutation rerenders oriented geometry, bounds, and
  the fit reference. The fixed far-side mount uses one renderer-only outer `V`
  reflection across the active camera's vertical/depth plane; the camera and
  HUD remain outside it. Actual `Camera3D.unproject_position()` evidence proves
  resolver-selected Right is screen-right, while effective camera-space depth
  proves resolver-selected Forward recedes. Review correction accounts for
  residual continuous yaw between `L.local_yaw` and `Q(L.local_yaw)`: the
  strict all-yaw pitch interval is approximately
  `(-42.480 degrees, +86.240 degrees)`, and normal gameplay uses
  `[-40 degrees, +60 degrees]` with a `2.480-degree` lower margin. Final visual
  review identified and fixed an above-board active-spawn projection collapse
  that had initially looked like a stale Ghost cell; the investigation also
  hardened presentation-node teardown by synchronously detaching obsolete
  children before deferred destruction, but that hardening was not the root
  cause of the reported cube. It also restores face-connected cell adjacency
  inside each shared NEXT-thumbnail `W` group. Board spacing and grid/wireframe
  styling remain deferred visual-quality work tracked in `docs/BACKLOG.md` and
  GitHub Issues. Stage 54E-2d — lifecycle, authority, and contract
  reconciliation — is COMPLETE / REVIEWED GREEN on PR #72: it establishes
  fresh entry/restart/reset defaults, presentation-only Reset View, an internal
  basis-only reset, synchronous setup/menu/mode teardown, coherent re-entry,
  public roll removal with generic roll retained, and persistence/deterministic
  exclusion evidence. It performs no authority transfer or establishment.
  Aggregate Stage 54E-2 is COMPLETE / REVIEWED GREEN. Stage 54E-3 — setup/menu
  information architecture — is COMPLETE / REVIEWED GREEN. Stage 54E-3a
  declared the taxonomy as data; Stage 54E-3b renders it as progressive
  disclosure, removes the panel's duplicate visibility rules, and keeps
  disclosure out of canonical session setup, setup persistence, and native
  session state. Its distinct human product review is outstanding and belongs
  to integrated Stage 54F unless performed sooner; E3 remains COMPLETE /
  REVIEWED GREEN. A post-acceptance registry validation defect is FIXED:
  declarations are validated before mode expansion, so an empty mode set
  cannot disappear without a validation failure. Stage 54E-4a human view
  semantics and final technical findings are REVIEWED GREEN. Stage 54E-4b
  implements that contract and is COMPLETE / FOCUSED VISIBLE REVIEW ACCEPTED.
  The active contract in
  `docs/architecture/camera_gui_preset_semantics.md` treats current view as
  transient presentation-context state; exposes one composite Reset View and a
  framing-only Fit View; preserves view across same-context Restart/new game;
  establishes fresh canonical view after setup/menu/mode exit and re-entry;
  defines flat 2D plus mode-owned 3D/4D/replay semantics; assigns UI scale to
  accessibility reset ownership; resolves camera projection as transient; and
  treats named presets as actions with no continuous `Custom`/state-equality
  identity. This deliberately refines the then-accepted Stage 54E-2d restart
  lifecycle without rewriting its historical reviewed-green evidence. The
  implementation splits outer orientation from framing, removes continuous
  preset identity and dead `frame_board()`, preserves view across Restart/new
  same-context games, rebuilds canonical views on context re-entry, and routes
  UI-scale reset ownership to Accessibility without changing persistence ID or
  schema. The focused real-window review found and closed two player-facing
  affordance blockers: Reset View had no invocation path in Live 2D or Live 3D,
  and Live 3D help advertised `F` as Fit View while `F` is Rotate XZ. Live 2D
  and Live 3D now route the existing `reset` action (key `0`) to the same
  composite Reset View that Live 4D already used, and the Live 3D Camera help
  states its real double-click Fit affordance. Aggregate Stage 54E-4 is
  COMPLETE / REVIEWED GREEN.
- Stage 54E-5 gameplay cockpit consolidation is COMPLETE / HUMAN PRODUCT
  REVIEW ACCEPTED on `codex/54e-5-cockpit-consolidation`. Ordinary live play
  is board-first, keeps NEXT prominent, separates View, Display, and Session
  actions, derives progressively richer 2D/3D/4D guidance from the shared live
  input contract, and hides replay/developer diagnostics without removing
  their existing routes. View Actions remain stateless and own input while
  open. Focused, keybinding, sanitation, pinned Godot 4.7.1, and full
  repository gates pass; normal, smaller, and larger real-window review is
  accepted. No gameplay, view lifecycle, control-frame, NEXT, Ghost,
  deterministic, native, topology, or persistence authority changed.
- Pre-54F issue #74 is COMPLETE / REVIEWED GREEN, and the 3D/4D NEXT
  correction is COMPLETE / HUMAN VISIBLE REVIEW ACCEPTED.
- Stage 54F integrated professional playability/visual acceptance is
  COMPLETE / HUMAN INTEGRATED PLAYABILITY ACCEPTED on
  `codex/54f-integrated-playability-visual-acceptance`. The candidate closes
  #69 responsive slice spacing, #70 board hierarchy, 4D label collisions,
  setup-error presentation, small-window Settings reachability, 2D spawn-entry
  grammar, and concrete setting naming/applicability defects. Focused tests and
  agent-driven Godot 4.7.1 real-window evidence cover 2D, 3D, occupied/rotated/
  wide-W 4D, High Contrast, and 1600x960, 1180x760, and OS-clamped 960x660
  windows; the pinned Godot 4.7.1 and full repository gates pass. No
  deterministic gameplay, view, movement, NEXT, Ghost, native, topology, or
  persistence authority changed. Human integrated review accepted 2D, 3D, and
  4D on 2026-08-23. It recorded slightly weaker standard-mode Live-4D gamebox
  legibility than equivalent 2D/3D boards as non-blocking Stage 54G polish;
  the usable current presentation and strong High Contrast alternative keep it
  outside the 54F correctness and architecture gates.
- Stage 54D-3 Hold is COMPLETE / DETERMINISTIC AUTHORITY ESTABLISHED / HUMAN
  VISIBLE ACCEPTED under `AE-0055` on
  `codex/54d-3-authoritative-hold`. Native live sessions own the one-slot
  identity, lifecycle legality, queue/RNG and canonical-spawn consequences,
  snapshots, and hashes. Godot dispatches one non-repeat `C` action and renders
  empty, populated, and unavailable HOLD state through the accepted NEXT
  thumbnail model/renderer. Transition-table, production-registry,
  deterministic replay/value-restore, GDExtension conformance, input/modal,
  responsive cockpit, pinned Godot 4.7.1, and full repository evidence are
  green. The fixed trace/replay schema and historical fixture results are
  unchanged. No Stage 54G polish was absorbed.
- Stage 54G is COMPLETE / FINAL MANUAL RELEASE ACCEPTANCE PASSED on
  `codex/54g-release-hardening`. The current candidate is the Godot 4.7.1
  macOS 13+ Universal 2 app/ZIP at runtime HEAD
  `fcaa450a57a43f6e1c931ceb35b98cdf2b0ccfbc`. Exact export-template pinning,
  release native build, metadata/signature/artifact inspection, two-user
  outside-tree smoke, persisted/invalid-state launches, and agent real-window
  2D/3D/4D/Hold/Settings/replay-browser evidence are recorded in
  `docs/plans/stage_54g_release_acceptance.md`. Linux and Windows are
  development-configured only, and Python/PyInstaller packaging is retained
  legacy. The first independent matrix found one Live-4D blocker after Main
  Menu / Advanced / Replay Demos / Viewer navigation. Viewer now returns
  through the app lifecycle owner and rebuilds canonical live presentation
  without resetting native gameplay. All-mode/replay regression, pinned Godot,
  full verification, rebuilt packaging, outside-tree smoke, and actual-app
  reproduction pass. No deterministic authority or accepted Fit/Reset,
  gameplay, Hold, NEXT, Ghost, replay, controls, or camera semantics changed.
  The independent final blocker re-acceptance passed for running and paused
  Live 4D, shared Live 2D/3D return, replay, immediate board visibility,
  retained gameplay/HOLD/NEXT/Ghost state, restored input ownership, and clean
  runtime logs. The bounded 4D polish decision remains disposition B.
  `PROFESSIONAL_CORE_GAME_READY` is `YES`, and the Stage 54 Professional Core
  Game programme is complete. No further Stage 54 implementation slice is
  required; later product and distribution work begins under a new programme
  or stage. The accepted package is ad-hoc signed and not notarized, so this
  product gate does not claim frictionless public macOS distribution.
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

1. `tools/governance/validate_project_contracts.py`: `4083` real LOC
2. `tests/unit/engine/test_topology_lab_menu.py`: `3804` real LOC
3. `tests/unit/render/test_locked_cell_explosion.py`: `3782` real LOC
4. `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`: `3194` real LOC
5. `tests/unit/governance/test_governance_validate_project_contracts.py`: `2457` real LOC
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

1. Stop Stage 54. Future product implementation begins as a separately
   contracted programme or stage; do not extend 54G or create Stage 54H.
2. Keep the Standard Live-4D legibility and live pause-badge findings as
   non-blocking post-release polish; do not reopen the already-passed matrix.
3. Keep piece/config-bundle import readers and unrelated settings recovery as
   bounded, format-specific deferrals rather than reopening generic governance
   work.
