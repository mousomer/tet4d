# Tet4D Open Work

Updated: 2026-08-03
Scope: active work, explicit deferrals, and acceptance boundaries only.

Completed detail is preserved in `docs/history/backlog_archive_2026-07-30.md`,
`docs/history/current_state_archive_2026-07-30.md`, and
`docs/history/DONE_SUMMARIES.md`.

## Current Authority

- Product behavior: relevant `docs/rds/*`
- Architecture boundaries: `docs/ARCHITECTURE_CONTRACT.md`
- Topology semantics:
  `docs/plans/topology_playground_current_authority.md`
- Godot/native ownership: `docs/architecture/authority_map.md`
- Documentation routing: `docs/DOCUMENTATION_MAP.md`
- Workflow and change classes: `docs/WORKFLOW_CODEX.md`
- Machine governance: `config/project/policy_pack.json`

## Tracking Boundaries

This backlog tracks strategic programmes, migrations, and deferrals whose
resolution depends on an authority decision or product evidence. GitHub issues
are for independently actionable, user-visible or reproducible bugs and their
collaboration lifecycle. The movement-cache item below remains here because it
depends on a future C++ graph-authority and representation decision.

## Completed Foundations

### Shared topology contract foundation

Status: merged and verified on `master` at `af01bbd6`.

Objective:

- make `contracts/topology_contract_v1.json` the shared scalar authority;
- generate deterministic Python, C++, and canonical-schema bindings;
- reject scalar coercion at the canonical Python boundary;
- preserve existing valid canonical identities;
- unblock native topology transport without implementing it.

Explicit boundary:

- no persistence migration or forgiving-adapter rewrite;
- no broad constructor or resolver hardening;
- no native topology transport behavior;
- no topology-aware gameplay or UI;
- Python remains the semantic oracle.

### Native topology transport

Status: merged and verified on `master` at `fe867627`.

Objective:

- transport strict version-1 topology profiles and resolver queries through
  native C++ and the Godot `Variant` boundary;
- consume the generated canonical topology contract constants;
- preserve exact acceptance parity with the Python topology oracle;
- retain deterministic structured errors without scalar coercion.

Acceptance boundaries:

- Python remains authoritative;
- representative bounded, wrapped, reflected, cross-axis, inverse,
  coordinate-frame, and piece-frame cases remain parity-backed;
- board extents and contract identity remain explicit;
- legacy asymmetric per-side rules receive no silent support;
- no complete Godot topology game loop;
- no Godot Topology Lab;
- no unified gameplay/endgame/explosion integration;
- no unrelated visual, toolchain, governance, packaging, or release work.

Native topology transport accepts only values that satisfy the shared topology
contract and the runtime query contract. It does not coerce malformed scalar
values into valid topology data.

Stage 53B transports and validates topology data but does not transfer semantic
authority from Python to C++.

## Active Work

### Professional playable 2D/3D/4D game programme

Stage 53E is complete and merged at `22938485`. Stage 53F, including its
corrective follow-up, is merged and verified on `master` at `91b901f3`. Its
strict replay, trace/hash, configuration, movement-cache, topology-store, and
validation-ownership work is complete; the cache-performance deferral below is
not incomplete correctness. The short-term Python boundary-governance programme
is closed.

The primary objective is a professional playable 2D/3D/4D game: stable
gameplay, Godot integration, clear controls, UI/UX, tutorials and onboarding,
topology gameplay, endgame/explosion presentation, and user-visible
performance. Plan product slices through the relevant RDS and authority-map
owners; do not reopen generic boundary-governance stages.

Stage 54A, Godot cockpit control coherence and visual-affordance correction,
is implemented locally and pending human visual acceptance. It establishes one
Godot control/helper authority; Ctrl-only soft drop; left-drag rotation,
right-drag translation, and wheel zoom; cockpit-panel ownership for Quick
Settings and grid visibility; clearer passive helper tags; rear-face W labels;
and restrained active-slice framing. Control remapping, controller support,
tutorials, topology gameplay, audio, and broader menu work remain later
product slices.

## Explicit Deferrals

- topology-aware Godot gameplay and diagnostics;
- Godot Topology Lab/editor;
- unified gameplay/endgame/explosion launch integration;
- control remapping, audio, tutorials, and unrelated cleanup;
- visual changes in the topology-contract PR;
- gameplay or toolchain changes in the governance PR;
- piece-record and migration/config-bundle import readers identified by the
  Stage 53E audit, pending owning-format evidence and focused acceptance tests;
- unrelated settings recovery identified by Stage 53E, pending individual
  stored-schema review and named migration-adapter evidence;
- Stage 53E retirement candidates that retain active callers, policy/RDS or
  benchmark roles, or released compatibility obligations;
- topology-aware Godot gameplay and diagnostics, Godot Topology Lab/editor,
  and unified gameplay/endgame/explosion integration remain separate later
  migration slices.

### Python movement-graph persistent-cache performance

Status: deferred pending a C++ movement-graph authority and representation
decision, or user-facing latency evidence.

Stage 53F correctness is complete: strict cache validation treats malformed or
incompatible data as a derived-data miss, rebuilds from authoritative topology,
and keeps normal cache acceptance bounded without constructing the full graph.
The diagnostic 20³ benchmark measured direct construction at approximately
`.054` seconds and a cold strict JSON cache read at approximately `.318`
seconds. The cache therefore makes no cold-start performance claim.

This affects setup and topology transitions only; it has no steady-state
movement, rendering, collision, determinism, or frame-rate impact. A redesign
is deferred because C++ graph authority and representation would change the
cost model, ownership, layout, serialization, cache strategy, and possible
asynchronous work. Revisit when that authority/representation is designed, or
when realistic normal game-start or topology-switching latency exceeds the
accepted product budget on representative hardware.

## Governance Watchlist

- Keep one semantic objective per PR.
- Separate unrelated formatting and toolchain migrations from product behavior
  where practical.
- Require a scope matrix for deliberately cross-layer integration PRs.
- Never weaken tests to fit an implementation.
- Keep Python authority and transfer records aligned with actual ownership.
- Keep invalid topology-profile storage non-saveable through ordinary update
  paths; read-only fallback is not mutation authority.
- Keep generated outputs tied to their source authority and generator.
- Record new warnings separately from known advisories.
- Keep all Tet4D GitHub writes on the verified owner identity for canonical
  `origin`, without publishing unrelated account or local identity details.

## Completion Boundary

Work is complete only when the stated acceptance criteria pass, authoritative
documentation is current, required checks are green, the PR state is reported,
and the tracked worktree is clean. Opening a branch or draft PR is not
completion.
