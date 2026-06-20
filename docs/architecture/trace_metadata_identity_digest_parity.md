# Trace Metadata Identity/Digest Parity

## Scope

This document records the Stage 18 parity evidence slice selected in
`docs/architecture/second_parity_slice_candidate_selection.md`.

The slice is data-only. It compares canonical trace metadata identity and
digest behavior between the Python oracle and the provisional native parity
path.

## Python oracle

The Python oracle is `tools/migration/trace_schema.py`.

It provides the canonical serialization and digest helpers used by this slice:

- `compact_canonical_json(payload)`
- `stable_hash(payload)`

The identity value is the compact canonical JSON string of the metadata
payload. The digest value is the SHA-256 hash of that canonical string via the
existing trace schema helper.

## Fixture

The committed fixture is `tests/fixtures/parity/trace_metadata_identity_digest.json`.

It is metadata only. It contains no movement events, board payloads, piece
positions, rotation state, collision state, renderer metadata, camera state,
or endgame data.

## Native/provisional path

The provisional native path is the migration test binary invoked through
`scripts/test_godot_tet4d_core.sh --trace-metadata-identity-digest`.

Its implementation lives in
`native/tet4d_core/tests/trace_metadata_identity_digest_tests.cpp`.

This path is provisional evidence only. It does not transfer authority.

## Comparison rule

Use exact comparison only:

- exact identity string equality
- exact digest equality

No tolerance mode is allowed.

## Default and strict behavior

- Default behavior is advisory when the native path is unavailable.
- `TET4D_STRICT_PARITY=1` makes native unavailability blocking.
- Any identity or digest mismatch is blocking in both modes when native output
  is available.

## Explicit exclusions

This slice must not include:

- coordinate/bounds normalization
- topology identifier normalization
- dimension label normalization
- topology movement
- seam traversal
- rotation
- gravity/drop
- collision
- lock/clear/gameplay loop
- rendering/projection/view/camera
- endgame physics

## Authority boundary

Python remains the semantic oracle.

Godot remains product shell, UI, and presentation.

C++/GDExtension remains provisional until parity evidence plus explicit
authority transfer.

This parity slice does not transfer authority.

## Routing

This implementation doc is routed from:

- `docs/architecture/parity_protocol.md`
- `docs/architecture/parity_pilot_audit_and_promotion_gates.md`
- `docs/architecture/second_parity_slice_candidate_selection.md`
- `docs/governance/README.md`
- `docs/governance/drift_protection_map.md`

## Validation

Required validation for this slice:

- `git diff --check`
- `.venv/bin/python tools/governance/validate_project_contracts.py`
- `.venv/bin/python tools/governance/validate_drift_protection.py`
- `CODEX_MODE=1 ./scripts/verify.sh`
