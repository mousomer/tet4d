# Parity Evidence Review and Third-Slice Selection

## Scope

This document reviews the first subsystem parity pilot and the Stage 18 trace
metadata identity/digest parity evidence, then selects the next smallest safe
slice.

It is process-only evidence. It does not transfer authority.

## Evidence review

- The first pilot proved the parity process with a fixed text fixture set,
  advisory default behavior, strict behavior, and no authority transfer.
- Stage 18 proved exact metadata identity and digest comparison for a
  metadata-only fixture, with a provisional native path and explicit
  exclusions.
- The review gap is the absence of a frozen third-slice candidate after both
  parity evidence mechanisms were compared.

## Harness routing decision

No new harness is created in Stage 19.

The Stage 18 trace metadata parity harness remains the only implemented
parity harness in this sequence.

This document selects the next slice and sets the implementation boundary for
the following stage. It does not add a native implementation or a third
parity harness.

## Chosen third-slice candidate

Chosen candidate: topology identifier normalization.

Implemented in `docs/architecture/topology_identifier_normalization_parity.md`.
Harness: `tools/migration/topology_identifier_normalization_parity.py`.
Fixture: `tests/fixtures/parity/topology_identifier_normalization.json`.

Stage 21 reviews the accumulated package in
`docs/architecture/parity_evidence_package_review.md`.

This is parity evidence only.

Why this candidate is the smallest safe next step:

- It is data-only and deterministic.
- It works on identifiers, not topology traversal or movement.
- It is exact-comparison friendly.
- It is migration/replay relevant.
- It is not renderer-owned.
- It is not topology-movement-owned.
- It is not gameplay-owned.

The candidate must remain identifier-only. It must not expand into seam
traversal, neighbor lookup, movement semantics, or topology gameplay
semantics.

Explicit exclusions:

## Rejected candidates

- trace schema/version normalization: too close to trace plumbing and less
  isolated from the existing Stage 18 metadata path.
- dimension label normalization: weaker evidence and closer to presentation
  or config labeling than replay semantics.
- coordinate/bounds normalization: too broad unless separately proven
  isolated and non-renderer-owned.

## Authority boundary

Python remains the semantic oracle.

Godot remains shell, presentation, and diagnostics.

C++/GDExtension remains provisional.

Candidate selection does not transfer authority.

## Stage 20 boundary

Stage 20 implementation may only implement topology identifier normalization.

It must not expand into:

- seam traversal
- neighbor lookup
- movement semantics
- rotation
- collision
- gravity/drop
- lock/clear/gameplay loop
- rendering/projection/view semantics
- endgame physics
- authority transfer records

## Routing

This document is routed from:

- `docs/architecture/parity_protocol.md`
- `docs/architecture/parity_pilot_audit_and_promotion_gates.md`
- `docs/architecture/authority_map.md`
- `docs/governance/README.md`
- `docs/governance/review_checklist.md`
- `docs/governance/drift_protection_map.md`
- `docs/DOCUMENTATION_MAP.md`
- `AGENTS.md`
- `native/AGENTS.md`

## Validation

Required validation for this slice:

- `git diff --check`
- `.venv/bin/python tools/governance/validate_project_contracts.py`
- `.venv/bin/python tools/governance/validate_drift_protection.py`
- `CODEX_MODE=1 ./scripts/verify.sh`
