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
- Machine governance: `config/governance/project.json` (routes, execution
  profiles and scenarios) and `config/project/policy_pack.json` (unmigrated
  facts)

## Active Work

### Godot editor diagnostic follow-up

Recheck the isolated macOS ObjectDB profiler snapshot-storage advisory when the
pinned engine or temporary-path strategy changes; see the Godot 4.7.2 audit.

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
context. Raw size is descriptive rather than a task-quality penalty. The
backlog has no size limit: it is measured and reported, and items leave it when
completed or obsolete. `CURRENT_STATE.md` keeps its 150-line handoff-usability
guard. Claims about actual agent-context pressure still need real task
trajectories with resolver and bounded-read evidence.

The PR118-baseline migration-bundle check separately reproduces stale generated metadata,
including the old `da6e2dd6...` policy digest. Regeneration also adds governance
config inputs and refreshes authority-document hashes, so that broader generated
artifact repair remains deferred from C1. The bundles' `codex_ci_lanes.json`
digest is likewise stale since iPadOS left hosted CI; that repair refreshes both.

### Governance pack, telemetry and work-type rollout

**Status (2026-09-25): paused for product work.** The approved work is the
bounded pre-56H repair (routing default, handoff and authority text), then
Stage 56H as the first instrumented coding task, with P1a telemetry enabled on
the working machine and the raw agent transcripts retained. A task-scoped
post-mortem of 56H informs the owner's decision on whether P1b, P1c and P6
continue. P2–P5 are dormant until the owner explicitly reactivates them. The
items below are not executable backlog work: listing them here grants no agent
permission to start them.

Authorities: `docs/architecture/work_type_classification.md` (work-type ontology, G1) and `docs/architecture/workspace_governance_v0_1.md` (pack ownership; its "Planned: portable agent telemetry" section, accepted 2026-09-25, owns P1). Done: pack `0.2.0` work-type schema; pack `0.3.0` / `v0.3-role-resolution-1` role resolution, project role-declaration checks, pack bootstrap roots and write-compatibility table, and the project `role_bootstrap` declaration; the G1 log-only observer (record schema 2) judging writes by the treatment captured at segment start.
**P0** (planning, recorded in those authorities): the pack records generic agent activity and experiments interpret it; capture is passive; per-run labels never live in `project.json`; snapshots are evidence, not attribution; raw-transcript retention is separable from telemetry retention. **P1a** (done in pack `0.4.0` / `v0.4-telemetry-core-4`): the pack's Tet4D literals are gone and guarded against, and the frozen project-independent observation envelope has immutable observation identities, source and persistence times, command phases, and opt-in first-hand `gov` observations with workspace-keyed private identities. **P1b**: capture sources that all emit the one observation model and differ only in source and provenance: first a Codex transcript importer moved out of the C1 experiment without its policy lookups, then a Claude transcript/session importer and a filesystem-snapshot source. Claude hooks are not assumed; add them only if a real consumer needs evidence unavailable in transcripts. Snapshots establish observed state changes, not reads or attributed writes. **P1c**: generic reconstruction of segments, read/write timelines and invocation results, correlating observations only on explicit evidence with a recorded confidence and never merging them by resemblance.
**P2**: consolidate `scripts/resolve_bootstrap_python.sh` into the pack. **P3**: move project values into `project.json` (canonical owner set, the toolchain commands behind `verification.full`, routing requirements and workflow modifiers) and register the work-type decision as a routed authority. **P4**: unify `governance_surface.document_roles`, `governance_surface.file_classifications` and artifact roles within the human-reviewed Tet4D role migration, which must also classify `CURRENT_STATE.md`, `docs/CONFIGURATION_REFERENCE.md` and the work-type decision. **P5**: move the governance-surface mechanism into the pack and its limits into `project.json`. **P6**: move C1 calibration, the G1 outcome and postmortem analysis onto the telemetry interface as outside consumers. P3 and P5 extract policy families, so each waits on the independent review required under Explicit Deferrals.
Still deferred behind an evidence checkpoint and explicit approval: the non-self-relaxation comparison, stratified validation, and any separate Manifest change enabling blocking. `dispatch_paths` remains context metadata and never implies Manifest membership.

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

Task contract: `docs/tasks/live_4d_cockpit_convergence.md`. Stage 56H is the
next acceptance boundary.

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
Stage 56H-R1.1 now routes ordinary Game bootstrap, player-facing quick entry,
and Tab 2D→3D→4D through validated configured sessions, while preserving the
explicit replay/fixture seam. R1.2 now prevents held blocked soft drops from
starving the normal native gravity tick/lock across Live 2D/3D/4D. R2.1 now
pauses ordinary Live 2D/3D/4D play on focus loss without auto-resume; R2.2 is
next, while R2.3/R2.4 remain unstarted. Stage 56H is a gameplay/product acceptance checkpoint,
not a release gate; Stage 56I polish, the 190/200 A/B choice, and cockpit
refinement continue after it.

### Three-product packaging gaps

The missing `product_platform_contract` package identities are future release work
under the platform priority below; transitional jobs are not support.

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
  export with game identity and entry semantics (Godot game / iPadOS is a
  long-term option; see Release and platform); and
- Designer / macOS (deferred) needs a genuinely distinct application identity
  and entry contract; renaming the current `Tet4D.app` game ZIP is insufficient.

The existing Python macOS/Windows/Linux packages, Godot game macOS package, and
Designer Windows package are implemented cells and remain separate evidence
from runtime acceptance or publication. Their release filename templates must
remain bound to their product's canonical `artifact_name_token`; the
transitional tablet consumers retain Designer naming only under their closed,
named status exception.

### Platform priority and release control

- Near term: Stage 56H, then continued product and design work (see Stage 56).
- Future release priority, once release work is justified: Windows, Linux, then
  Android tablets, in strategic order with overlap allowed; this starts no
  packaging, porting, monetization, or storefront work.
- Deferred: macOS public distribution, then iPadOS, until distribution nears.

`v0.9.0` was published on 2026-09-04 from `3d06bb96` with all seven registered
consumers, after the Windows Designer package identity repair. Release control
may release any validated subset of those consumers without changing the
ten-cell product target matrix: the manual candidate workflow records the
selected bytes in a v2 manifest before it creates a draft, and a separate
manual workflow publishes only that inspected, byte-validated draft.

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
- iPadOS is a long-term option, not an immediate goal: the Godot game/iPadOS
  target (godot-cpp static-link composition, simulator architecture), Design
  Laboratory iPadOS acceptance, hosted CI evidence, and release scope. Packaging
  code, its unit tests, and the manual release job remain so it can resume;
  resuming restores the hosted CI job, routing tests, and gate wiring.
- macOS public distribution waits until commercialization nears: Developer ID
  enrollment, signing, notarization, stapling, Apple release automation, and
  App Store/provisioning. macOS stays a development, playtest, and CI platform.

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
