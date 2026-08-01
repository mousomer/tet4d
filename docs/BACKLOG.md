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

### Canonical topology contract

Objective: define the versioned topology representation shared by Python,
fixtures/traces, native C++, Godot transport, topology exploration, and
endgame/explosion consumers.

Acceptance:

- existing Python semantics remain the oracle;
- normalization, validation, serialization, identity, invariants, and
  representative 2D/3D/4D parity are explicit and tested;
- no complete topology-aware Godot game loop or editor is introduced;
- any behavior-changing semantic decision is surfaced for review.

## Explicit Deferrals

- native topology transport beyond the contract/parity slice;
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

## Completion Boundary

Work is complete only when the stated acceptance criteria pass, authoritative
documentation is current, required checks are green, the PR state is reported,
and the tracked worktree is clean. Opening a branch or draft PR is not
completion.
