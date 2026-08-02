# Tet4D Open Work

Updated: 2026-08-02
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

## Active Work

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

### Short-term Python boundary governance

The remaining short-term sequence precedes the medium-term professional
playable 2D/3D/4D game programme:

1. **53D — explicit persistence and legacy recovery adapters.** Implemented on
   the active Stage 53D branch: persistence v1 is strict, unversioned legacy v0
   has a named evidence-backed adapter, and every migration, seam discard, or
   profile fallback is structured and observable. Integration remains pending.
2. **53E — repository-wide Python coercion and boundary audit.** Classify
   canonical and identity-bearing inputs, replay/state-hash inputs, public
   constructors, transport boundaries, persistence and human-input adapters,
   numerical internals, active runtime modules, migration tools, and dead or
   retirement-candidate paths.
3. **53F — targeted repository-wide hardening and governance.** Fix high-risk
   semantic coercions, retire dead code, add boundary-specific checks, prevent
   duplicated scalar policies, preserve legitimate parsing/formatting, and
   close short-term governance acceptance.

Repository-wide Python coercion hardening is a short-term governance objective,
but it must be driven by boundary classification rather than a mechanical ban
on conversion functions.

## Explicit Deferrals

- topology-aware Godot gameplay and diagnostics;
- Godot Topology Lab/editor;
- unified gameplay/endgame/explosion launch integration;
- control remapping, audio, tutorials, and unrelated cleanup;
- visual changes in the topology-contract PR;
- gameplay or toolchain changes in the governance PR.
- integration of the implemented Stage 53D persistence recovery policy;
- repository-wide coercion inventory (Stage 53E) and targeted fixes (Stage
  53F);
- topology-aware Godot gameplay and diagnostics, Godot Topology Lab/editor,
  and unified gameplay/endgame/explosion integration remain separate later
  migration slices.

## Governance Watchlist

- Keep one semantic objective per PR.
- Separate unrelated formatting and toolchain migrations from product behavior
  where practical.
- Require a scope matrix for deliberately cross-layer integration PRs.
- Never weaken tests to fit an implementation.
- Keep Python authority and transfer records aligned with actual ownership.
- Keep generated outputs tied to their source authority and generator.
- Record new warnings separately from known advisories.
- Keep all Tet4D GitHub writes on the verified owner identity for canonical
  `origin`, without publishing unrelated account or local identity details.

## Completion Boundary

Work is complete only when the stated acceptance criteria pass, authoritative
documentation is current, required checks are green, the PR state is reported,
and the tracked worktree is clean. Opening a branch or draft PR is not
completion.
