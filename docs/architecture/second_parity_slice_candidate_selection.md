# Second Parity Slice Candidate Selection

## Decision

Chosen candidate: trace metadata identity/digest.

Decision status: selected.

Stage 18 implementation allowed: yes, limited to the selected candidate.

## Reason for selection

Why this candidate is small:

- It is data-only and deterministic.
- It can use existing trace-schema hashing and identity concepts.
- It does not require board mutation, topology traversal, renderer state,
  camera state, or Godot scene changes.

Why this candidate is useful:

- Trace identity and digest checks protect replay and migration integrity.
- They verify that Python-oracle trace metadata can be represented exactly by a
  provisional native surface before any larger semantic subsystem is attempted.

Why higher-ranked candidates were accepted/rejected:

- coordinate/bounds normalization: rejected for Stage 18 because existing
  helpers are embedded in trace export and gameplay snapshot payload assembly;
  selecting them now risks expanding into coordinate ownership, board state, or
  topology-sensitive output.
- trace metadata identity/digest: accepted because it is isolated,
  JSON-serializable, exact-comparison friendly, and migration-relevant.
- topology identifier normalization: not selected because topology identifiers
  are closer to topology-mode routing and may invite seam or movement
  interpretation.
- dimension label normalization: not selected because it is weaker evidence and
  closer to presentation/config labeling than trace integrity.

## Authority boundary

Python remains the semantic oracle.

Native/C++ remains provisional.

Godot remains product shell, UI, rendering, presentation, diagnostics, and
input routing.

Candidate selection does not transfer authority.

Passing a future second-slice parity check will still not transfer authority.

## Candidate specification

Subsystem: trace metadata identity/digest.

Python oracle source: `tools/migration/trace_schema.py`, specifically
canonical JSON, compact canonical JSON, and stable hash behavior for a small
metadata-only payload.

Native/provisional target: a future native/Godot-facing bridge may expose the
same metadata identity and digest values, but Stage 17 creates no native API and
no harness.

Fixture shape:

```json
{
  "candidate": "trace_metadata_identity_digest",
  "cases": [
    {
      "trace_id": "plain_2d_spawn_001",
      "mode": "2d",
      "topology": "plain",
      "schema_version": 1,
      "trace_version": 1,
      "expected_identity": "trace_metadata_identity_digest:plain_2d_spawn_001:2d:plain:1:1",
      "expected_digest": "python-oracle-stable-hash"
    }
  ]
}
```

Comparison rule: exact string equality for identity and exact digest equality.
No tolerance mode is allowed.

Default mode: advisory only when the native bridge/toolchain is unavailable.

Strict mode: `TET4D_STRICT_PARITY=1` makes native unavailability and any
identity/digest mismatch blocking.

Failure reporting: missing cases, unexpected cases, identity mismatches, and
digest mismatches must name the case id and show expected and actual values.

## Explicit exclusions

This slice must not include:

- topology movement
- rotation
- drop/collision
- lock/clear/gameplay loop
- rendering/projection/view semantics
- endgame physics

It also must not add board mutation, topology seam traversal, Godot scene
changes, generated bundle changes, or authority-transfer records.

## Promotion-gate compliance

How this candidate satisfies:

- deterministic fixture: metadata-only JSON payload with stable sorted-key
  digesting.
- Python oracle identified: `tools/migration/trace_schema.py`.
- native/provisional target identified: future native/Godot-facing metadata
  identity/digest bridge.
- exact/tolerance comparison specified: exact identity and digest equality only.
- default advisory behaviour specified: unavailable native bridge remains
  advisory by default.
- strict failure behaviour specified: `TET4D_STRICT_PARITY=1` makes
  unavailability and mismatches fail.
- no authority transfer: selection and future passing evidence remain
  process/evidence only.
- routing required: Stage 18 must update parity protocol, this selection doc,
  governance router, drift map, review checklist, AGENTS routing, and native
  AGENTS routing as needed.
- validators/tests required: project-contract and drift-protection validators
  must cover the second-slice routing surface.

## Stage 18 implementation boundaries

Allowed in Stage 18:

- add one small metadata-only fixture set for
  `trace_metadata_identity_digest`
- add a Python-oracle comparison helper that uses `tools/migration/trace_schema.py`
- add a provisional native/Godot-facing output path for the same metadata-only
  identity and digest values
- add exact comparison and actionable failure reporting
- add tests and routing for the new harness

Forbidden in Stage 18:

- implementing any candidate other than trace metadata identity/digest
- adding topology movement, rotation, drop/collision, lock/clear/gameplay loop,
  rendering/projection/view, or endgame physics parity
- changing gameplay, topology, trace export, rendering, config, or Godot scene
  semantics
- claiming authority transfer or marking a transfer record as `transferred`

Required validation in Stage 18:

- project-contract and drift-protection validators for the new routing
- governance tests for missing routing and authority claims
- focused second-slice parity tests
- `CODEX_MODE=1 ./scripts/verify.sh`

## Routing checklist

Stage 18 must update or verify:

- `docs/architecture/parity_protocol.md`
- `docs/architecture/parity_pilot_audit_and_promotion_gates.md`
- `docs/architecture/second_parity_slice_candidate_selection.md`
- `docs/architecture/authority_transfer_protocol.md`
- `docs/architecture/authority_map.md`
- `docs/plans/godot_core_port_plan.md`
- `docs/plans/topology_godot_core_port_plan.md`
- `docs/plans/live_plain_nd_godot_prototype_plan.md`
- `docs/governance/README.md`
- `docs/governance/review_checklist.md`
- `docs/governance/drift_protection_map.md`
- `docs/governance/codex_policy.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/PROJECT_STRUCTURE.md`
- `AGENTS.md`
- `native/AGENTS.md`
- `tools/governance/validate_project_contracts.py`
- `tools/governance/validate_drift_protection.py`
- `tests/unit/governance/test_governance_validate_project_contracts.py`
- `tests/unit/governance/test_validate_drift_protection.py`
