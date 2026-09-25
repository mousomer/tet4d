# Tet4D Open Work

Updated: 2026-09-25
Scope: active work, explicit deferrals, and near-term acceptance boundaries.

Completed chronology is recoverable from Git, merged PRs, CI, and
`docs/history/`. Programme sequencing and long-horizon intent live under
`docs/plans/`; this file does not duplicate either layer. Earlier detail is in
`docs/history/backlog_archive_2026-07-30.md`.

## Current Authority

- Product programme: `docs/plans/professional_godot_game_programme.md`
- Product behaviour: relevant `docs/rds/*`
- Architecture: `docs/ARCHITECTURE_CONTRACT.md` and
  `docs/architecture/authority_map.md`
- Authority transfer: `docs/architecture/authority_transfer_protocol.md`
- Topology/Explorer: `docs/architecture/topology_playground_current_authority.md`
- Human governance: `AGENTS.md` and the six owners under `docs/governance/`
- Machine governance: `config/project/policy_pack.json`

## Active Work

### Environment ownership

`bootstrap_env.sh` is the single owner of environment mutation and follows the
declared execution mode: installed mode builds a `.venv` belonging to this
checkout, source mode synchronises declared dependencies into the shared
toolchain and installs no project. Its fingerprint and mutation lock live beside
that environment, because a shared one is reachable from every worktree at once
while each worktree's verify lock guards only its own tree.

Bootstrap and every project-importing verification entry point consume `gov env`
for the resolver-selected interpreter, mode, and source binding. The obsolete shell
editable-install checker is retired: `gov doctor` certifies installed origin or source-mode checkout binding/distribution neutrality.

`verify_local.sh` owns nothing: it reports an unready environment and execs the
canonical gate. `--rebuild-venv` is gone with the venv it rebuilt, which also
retires the finding that inherited bootstrap had made that refusal permissive.

The inherited overlay serves bootstrap, certified selection, and execution mode;
two-worktree operation is certified without a `.venv` symlink farm. A checkout
predating the overlay needs its four shared-environment symlinks or `WORKSPACE_VENV`.

Source bootstrap validates installed dependency versions on cache hits and after
installation; its declaration digest never claims to describe shared contents.
Regression coverage repairs missing/incompatible dependencies without an
unneeded install when requirements are satisfied; `packaging>=24` is the example.

### Routing and scenario precedence

Scenario routing tiers cross-layer, constrained repair, subsystem work, then
generic wording; equal-tier maxima fail closed and matrix tests cover invariants.

### Governance-manifest quality calibration

Safety ceilings, including the machine-policy 80 KiB advisory and 96 KiB hard
ceiling, are provisional rather than experimentally optimal. Physical LOC is a
reviewability proxy, not a reason to compress normative authority. A
manifest/harness experiment must vary bytes, rules/authorities, depth,
concentration, and context burden; measure retrieval, selection,
reconstruction, isolated mutation, contradiction detection, and performance;
then set targets from quality degradation, never capacity alone.

Stage C1's non-authoritative instrumentation, frozen baseline, and historical
corpus result are complete; its PR118 identity evidence and limitations remain
in `docs/experiments/governance_manifest_quality_stage_c1.md`. C1 changed no
threshold, route, scenario, resolver, authority, or active surface. Production
post-mortems (`docs/experiments/governance_postmortem.md`) precede targeted
experiments. Candidates needing explicit approval: grouping human-turn segments
into engineering tasks (`task_group_id`); C1 encounters for `./gov` output,
injected instructions, and quoted Codex `exec` commands; and review of
phrase-sensitive fallback routing, observed for natural Stage 56G wording.

The postmortem correction classifies `CURRENT_STATE.md` and `docs/BACKLOG.md`
as edge-state files and records their distinct operational roles. Backlog is
conditional routed open-work authority; current-state is restart/staged-handoff
context. Raw size is descriptive rather than a task-quality penalty. Existing
LOC guards remain for their declared human-reviewability, structural-discipline,
or handoff-usability reasons. Follow-up calibration needs real task trajectories
with resolver and bounded-read evidence before making any claim about actual
agent-context pressure or changing those limits.

The PR118-baseline migration-bundle check separately reproduces stale generated metadata,
including the old `da6e2dd6...` policy digest. Regeneration also adds governance
config inputs and refreshes authority-document hashes, so that broader generated
artifact repair remains deferred from C1. The bundles' `codex_ci_lanes.json`
digest is likewise stale since iPadOS left hosted CI; that repair refreshes both.

### Work-type classification rollout

`docs/architecture/work_type_classification.md` owns the accepted ontology and rollout. Workspace-governance `0.2.0` / `v0.2-work-type-schema-1` implements the work-type vocabulary, explicit artifact-role schema, complete pack roles, obligation comparators, and Tet4D pack re-sync.
Stage G1 now provides the bounded, non-authoritative log-only observer: declared segment boundaries, repository-content write attribution, explicit/bootstrap/unclassified role provenance, observational compatibility, and basic telemetry. It neither blocks nor performs the Tet4D semantic role handoff.
Further governance work is deferred while real product trajectories exercise G1. The non-self-relaxation comparison, human-reviewed Tet4D role migration, stratified validation, and any separate Manifest change enabling blocking require a later evidence checkpoint and explicit approval.
`dispatch_paths` remains context metadata and never implies Manifest membership.

### Camera and relative-control contract

Unify the Godot presentation contract for exact camera basis turns, slice
orientation, and Relative translation without changing native gameplay,
deterministic identity, or accepted 4D resolver behaviour. Issue #74 requires
2D screen-left/right and 3D screen-left/right plus Forward-away/Back-approach
to agree across resolver output, camera basis, direction helpers, and help.

Acceptance boundary:

- exact camera pairs are XZ `1/2`, XW `3/4`, and ZW `5/6`; the public and
  tutorial progression remains XW, ZW, XZ;
- `LiveInputContract` owns shared piece/camera rotation descriptors and 4D
  keeps the existing `B + Q(L.local_yaw)` resolver semantics; `O/L` preserve
  local-yaw decrement/increment without rotating the outer camera rig; and
- coordinate/framing changes are limited to the Stage 55B exact-basis fit
  contract and need independent mapper-oracle coverage.

Cockpit allocation, NEXT/HOLD redesign, grid/spacing polish, and issues
#69/#70 remain separate PR3–PR5 work. Stage 55 semantic export is available
only as reproducible, non-authoritative investigation tooling. Its compact
projection retains runtime provenance when generated wrappers are elided; it
is not a canonical design workflow and its generated captures remain untracked.

### Stage 56 cockpit completion

Complete the accepted cockpit direction through serial green stages. Stage
56A repaired the Live-4D orientation rosette as a passive consumer of the
existing `B + L + ControlFrameMapping` presentation snapshot. Stage 56B now
provides deterministic viewport-aware, activity-independent slice tiling and
records bounded repair 56B-R for settled HUD viewport ownership and manual-fit
preservation. Stage 56C now renders PIECE and VIEW as shared passive semantic
rows whose labels are injected from `LiveInputContract` across all densities.
Stage 56D extracts the Header, PrimaryBoardSurface, and three-module
ControlDeck allocation into the authority-free `LiveCockpit` shell. Stage 56E
has now migrated Live 3D with a larger primary board and dimension-filtered
PIECE/VIEW rows. Stage 56F has now migrated Live 2D and has implementation and
automated evidence complete; its regression evidence is independent of
machine-local onboarding preferences while preserving the profile-owned
guidance setting. Stage 56G-R now supplies one apparent-size responsive policy
across all live dimensions, real-window acceptance from 1728×1080 to 720×600,
active-resize coverage, bounded ordered deck flow, and repaired visual evidence.
Human playability, final polish, and the 190/200 human A/B choice remain gated as Stages 56H–56I.

### Three-product packaging gaps

Implement the missing package identities required by the authoritative
`product_platform_contract` without treating transitional jobs as support.

Acceptance boundary:

- The shared Godot tree now has explicit game and Designer bootstrap/profile
  selection; this establishes identity and startup separation only, not new
  platform support or a 0.9.0 release profile.
- Product-profile staging must reject the canonical Godot project and every
  resolved descendant as an export target; disposable staging remains outside
  the source tree and does not alter product identity or platform support.

- Godot game / Windows and Godot game / Linux need distinct distributable
  packages and acceptance; the existing Windows package is Designer only;
- Godot game / Android must replace the transitional Designer-identity tablet
  export with game identity and entry semantics (Godot game / iPadOS is
  deferred; see Release and platform); and
- Designer / macOS needs a genuinely distinct application identity and entry
  contract; renaming the current `Tet4D.app` game ZIP is insufficient.

The existing Python macOS/Windows/Linux packages, Godot game macOS package, and
Designer Windows package are implemented cells and remain separate evidence
from runtime acceptance or publication. Their release filename templates must
remain bound to their product's canonical `artifact_name_token`; the
transitional tablet consumers retain Designer naming only under their closed,
named status exception.

### 0.9.0 release-control boundary

The 0.9.0 release-control path may release an arbitrary validated subset of the
seven registered packaging consumers without changing the ten-cell product
target matrix. The expected first candidate is the Godot game macOS consumer
and the Designer Windows consumer, but that pair is not hard-coded: the manual
candidate workflow accepts registered `consumer_id` scope and records the exact
selected bytes in a v2 manifest before it creates a draft. A separate manual
publication workflow can publish only that inspected, byte-validated draft.

The initial full-matrix candidate remains blocked on Windows Designer package
identity acceptance. PCK validation now rejects out-of-file resource ranges and
truncated format-4 headers. This narrow blocker is tracked by the active task
record `docs/tasks/windows_designer_package_identity_validation.md`; it does
not authorize another candidate dispatch or alter release scope.

This operational readiness does not close any missing target cell. Godot game
Windows/Linux/Android/iPadOS and Designer macOS remain separate package and
acceptance work. The transitional Designer Android artifact and transitional
Designer iPadOS artifact remain technical evidence under their machine
identifiers; they do not become supported Designer platforms or game packages.

## Accepted Next Product Boundaries

- Stage 54F-6 default style selection/polish must consume reviewed human Design
  Laboratory evidence. See
  `docs/plans/design_evaluation_laboratory_acceptance.md`.
- Topology, Explorer, challenge, and simulation work must begin as a new
  approved stage under the relevant plan and architecture owners.
- Path-sensitive CI Slice C may map evidence to explicit lanes only after
  duplicate push/PR execution is measured and removed; retain a conservative
  full-gate fallback.

## Explicit Deferrals

### Workspace governance extraction

- v0.1 retains `config/project/policy_pack.json` as authority for unmigrated
  Tet4D-specific facts. Future extraction should migrate one bounded fact family
  at a time with generated/validated compatibility output.
- General prompt classification, runtime execution graphs, cross-repository
  orchestration, migration engines, and planner/runner redesign remain deferred.
- Round 2 hardens bootstrap diagnostics, canonical-owner coverage, field-use
  mutation evidence, and executable contradiction fixtures. Generic generated
  documents and the Godot-namespaced full-gate pointer remain deferred.
- The v0.1 integrity repair makes project routes canonical and retains legacy
  routes only as a parity-validated facade. Do not extract another policy family
  until the repaired contract receives independent review.
- The vendored v0.1 pack is internally checked here. Canonical extraction is
  blocked until authority names the external package/repository and release identity; Tet4D manifests cannot derive either from mutable Git remotes.

### Release and platform

- Clean-machine Windows and iPadOS runtime acceptance remain real-platform
  evidence, not claims inferred from macOS or package structure.
- The hosted CI platform lane exists for macOS only. `platform_windows`,
  `platform_linux`, `platform_android`, and `platform_ipados` are declared
  manual in `config/project/codex_ci_lanes.json`: a change to those packaging
  paths reports outstanding platform evidence instead of borrowing another
  platform's job. Adding those hosted lanes needs their own scope and runner
  contract.
- All iPadOS work waits for the notarized macOS game release: the Godot
  game/iPadOS target, its godot-cpp static-link composition and simulator
  architecture compatibility, and hosted iPadOS CI evidence. The release
  workflow's transitional Designer iPadOS job still builds on explicit scope.
  Restoring the hosted lane restores its CI job, routing tests, and gate wiring.
- Developer ID signing/notarization and broader distribution are separate
  release prerequisites.

### Product and presentation

- First-class topology games, complete Godot Topology Lab/Explorer, the general
  challenge/campaign runner, and unified gameplay-to-simulation flow remain in
  `docs/plans/`.
- Multi-piece next preview, configurable preview depth, ghost style/opacity,
  multiple/buffered Hold, gamepad, audio, and broad remapping require separate
  product slices.
- Non-blocking polish remains for Live-4D volume legibility, the pause badge,
  narrow-window clipping, replay-list keyboard access, very-small windows,
  HiDPI defaults, and window size/position persistence.

### Migration and compatibility

- Piece-record and migration/config-bundle readers require owning-format
  evidence and focused acceptance tests.
- Settings recovery requires stored-schema review and named adapter evidence.
- Stage 53E candidates with active callers, product/policy roles, benchmark
  roles, or released compatibility obligations remain retained.
- `codex/explosion-architecture-inventory` remains a manual-review candidate
  under a separate authorized task because it may contain unique changes.

### Engineering debt

- `TD-0001`: Godot presentation/trace constant advisories. Trigger: before
  strict config-authority mode.
- `TD-0002`: duplicate bridge/native trace-export helper-name advisories.
  Trigger: before strict utility-reuse mode.
- `TD-0004`: reproducible clang-format, clang-tidy, and
  `compile_commands.json`. Trigger: before strict native tooling in CI.
- Python movement-graph persistent caching remains deferred until a native
  representation decision or representative latency evidence; current
  diagnostics show no cold-start benefit.
- `docs/history/DONE_SUMMARIES.md` compaction is a separate history-hygiene
  batch.

## Governance Watchlist

- Define governance-pack `VERSION` versus revision semantics for schema
  compatibility changes, including required-field additions. Trigger: before
  the next compatibility-significant schema change.
- Keep one semantic objective per PR and use scope matrices for cross-layer
  integration.
- Never weaken tests, deterministic identity, replay/schema compatibility,
  sanitation, or explicit deferrals.
- Keep authority records aligned with actual ownership; do not manufacture
  Python mirrors for new authority.
- Keep generated outputs tied to their source and generator.
- Keep invalid topology-profile storage non-saveable through ordinary updates.
- Record new warnings separately from known advisories.

## Completion Boundary

Work is complete only when acceptance passes, authorities are current, required
checks are green, publication state is reported, and the worktree is clean. A
branch or draft PR alone is not completion.
