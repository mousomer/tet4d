# Tet4D Open Work

Updated: 2026-08-01
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

### Native topology transport

Status: ordered next; implementation has not begun.

Objective:

- extend native C++ topology transport beyond the contract/parity surface;
- consume canonical topology contract v1;
- preserve exact parity with the Python topology oracle;
- avoid introducing topology-aware Godot gameplay in the same slice.

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

Subsequent order:

1. broader native topology transport;
2. topology-aware Godot gameplay;
3. Godot topology diagnostics;
4. Godot Topology Lab/editor;
5. unified gameplay, topology, endgame, and explosion launch integration.

These remain separate reviewable slices unless a later task contract explicitly
authorizes an integration PR.

## Explicit Deferrals

- topology-aware Godot gameplay and diagnostics;
- Godot Topology Lab/editor;
- unified gameplay/endgame/explosion launch integration;
- control remapping, audio, tutorials, and unrelated cleanup;
- visual changes in the topology-contract PR;
- gameplay or toolchain changes in the governance PR.

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
