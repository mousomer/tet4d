# Trace Schema/Version Normalization Parity

## Scope

This document defines the Stage 22 trace schema/version normalization parity
slice.

The slice is trace schema/version metadata-only. It compares canonical schema
version, trace kind, trace family, compatibility label, schema identifier, and
schema identity strings through a deterministic fixture and exact comparison.

It does not interpret trace events and it does not transfer authority.

## Authority boundary

Python remains the semantic oracle.

Native/C++ remains provisional.

Godot remains product shell/presentation.

Passing this parity slice does not transfer authority.

## Inputs

Schema/version metadata-only fixture:
`tests/fixtures/parity/trace_schema_version_normalization.json`

Parity harness:
`tools/migration/trace_schema_version_normalization_parity.py`

Explicit exclusions:

- trace events
- board snapshots
- piece positions
- topology movement
- seam traversal
- neighbor lookup
- rotation
- drop/collision
- lock/clear/gameplay loop
- rendering/projection/view semantics
- endgame physics

## Python oracle

The Python oracle is the local schema/version normalization helper inside
`tools/migration/trace_schema_version_normalization_parity.py`.

It normalizes schema version values to canonical integer version `1`, maps trace
kind and trace family labels to canonical strings, normalizes compatibility
labels, and emits a canonical `trace_schema_v1` schema ID plus exact schema
identity string.

## Native/provisional target

No safe native/provisional route exists for schema/version metadata-only
comparison in this stage.

Default mode is advisory when the native/provisional route is unavailable.
Strict mode `TET4D_STRICT_PARITY=1` blocks that unavailability.

Do not claim native parity when the native path is unavailable.

## Comparison rule

Exact equality of normalized schema/version identity.

## Commands

Default/advisory:
`python tools/migration/trace_schema_version_normalization_parity.py`

Strict:
`TET4D_STRICT_PARITY=1 python tools/migration/trace_schema_version_normalization_parity.py`

Tests:
`python -m pytest -q tests/unit/migration/test_trace_schema_version_normalization_parity.py`

## Acceptance criteria

- fixture is deterministic and schema/version metadata-only
- Python oracle computes canonical schema/version identity
- default mode is advisory if native/provisional unavailable
- strict mode fails on unavailability or mismatch
- no authority transfer is claimed
- routing is complete
