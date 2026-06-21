# Topology Identifier Normalization Parity

## Scope

This document defines the Stage 20 topology identifier normalization parity
slice.

The slice is identifier-only. It compares canonical topology identifiers and
project labels through a deterministic fixture and exact string comparison.

It does not interpret topology mechanics and it does not transfer authority.

## Authority boundary

Python remains the semantic oracle.

Godot remains product shell, UI, presentation, and diagnostics.

C++/GDExtension remains provisional.

Passing this parity slice does not transfer authority.

## Inputs

Identifier-only fixture:
`tests/fixtures/parity/topology_identifier_normalization.json`

Parity harness:
`tools/parity/topology_identifier_normalization_parity.py`

Explicit exclusions:

- seam traversal
- neighbor lookup
- topology movement
- wrap/invert traversal semantics
- rotation
- gravity/drop
- collision
- lock/clear/gameplay loop
- board mutation
- rendering/projection/view/camera
- endgame physics

## Python oracle

The Python oracle is the local identifier-normalization helper inside
`tools/parity/topology_identifier_normalization_parity.py`.

It normalizes identifier strings by trimming whitespace, lower-casing,
canonicalizing separators, stripping an optional `topology_` prefix, and
mapping known aliases to canonical identifiers such as `plain_2d`,
`wrap_all_4d`, `invert_all_4d`, and `sphere_like_4d`.

## Native/provisional target

No safe native/provisional identifier-only route exists in this stage.

Default mode is advisory when the native/provisional route is unavailable.
Strict mode blocks that unavailability.

Do not claim native parity when the native route is unavailable.

## Package review

`docs/architecture/parity_evidence_package_review.md` reviews this slice as
identifier-only parity evidence with no native route yet. The review does not
change this slice's scope and does not transfer authority.

## Comparison rule

Exact equality of canonical topology identifier strings.

## Commands

Default/advisory:
`python tools/parity/topology_identifier_normalization_parity.py`

Strict:
`TET4D_STRICT_PARITY=1 python tools/parity/topology_identifier_normalization_parity.py`

Tests:
`python -m pytest -q tests/unit/migration/test_topology_identifier_normalization_parity.py`

## Acceptance criteria

- fixture is deterministic and identifier-only
- Python oracle computes canonical identifiers
- default mode is advisory if native/provisional output is unavailable
- strict mode fails on unavailability or mismatch
- no authority transfer is claimed
- routing is complete
