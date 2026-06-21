# Parity Evidence Package Review

## Scope

This document reviews the parity evidence package after Stage 20.

Reviewed evidence:

- Stage 15: First subsystem parity pilot
- Stage 18: Trace metadata identity/digest parity
- Stage 20: Topology identifier normalization parity

This is a review and validation-governance checkpoint. It does not implement a
fourth parity slice.

## Authority boundary

Python remains the semantic oracle.

Native/C++ remains provisional.

Godot remains product shell/presentation.

This evidence package review does not transfer authority.

No authority-transfer record is created by this review.

## Evidence summary

### Stage 15 - first subsystem parity pilot

Evidence produced: a narrow `stable_hash_text(text)` pilot with a small fixed
text fixture set, a Python oracle helper, native/provisional output parsing,
and exact hash comparison.

Strengths: it proved the parity process shape: Python oracle output, native
case loading, missing/extra case detection, exact mismatch diagnostics,
advisory default behavior, and strict blocking behavior through
`TET4D_STRICT_PARITY`.

Limitations: it is process-only evidence for a tiny helper. It is not meaningful
gameplay or topology semantic evidence, and it is not a subsystem promotion.

Default/advisory behaviour: native bridge or toolchain unavailability is
advisory by default.

Strict/blocking behaviour: `TET4D_STRICT_PARITY=1` makes native unavailability
blocking. Hash mismatches are blocking when native output is available.

Routing status: routed through parity protocol, authority-transfer protocol,
promotion gates, governance README, and drift map.

Verdict: accepted as the first parity process pilot, not as transfer-ready
semantic evidence.

### Stage 18 - trace metadata identity/digest parity

Evidence produced: deterministic metadata-only fixture coverage for compact
canonical trace metadata identity and SHA-256 digest comparison between the
Python `trace_schema.py` oracle and a provisional native test surface.

Strengths: fixture is committed, small, data-only, trace/replay relevant, and
exact-comparison friendly. Native/provisional status is explicit, and mismatch
diagnostics name identity and digest failures separately.

Limitations: it covers trace metadata identity/digest only. It does not cover
trace events, parser behavior, replay behavior, topology mechanics, gameplay
mutation, or authority transfer.

Default/advisory behaviour: native path unavailability is advisory by default.

Strict/blocking behaviour: `TET4D_STRICT_PARITY=1` blocks native unavailability.
Identity and digest mismatches are blocking when native output is available.

Fixture status: deterministic, committed, metadata-only, and free of movement,
board, renderer, camera, and endgame state.

Native/provisional status: native output is produced by the provisional
`native/tet4d_core/tests/trace_metadata_identity_digest_tests.cpp` test surface.

Routing status: routed through parity protocol, promotion gates, candidate
selection, governance README, drift map, documentation map, project structure,
AGENTS, and native AGENTS.

Verdict: meaningful data-only parity evidence, but not transfer-ready by
itself.

### Stage 20 - topology identifier normalization parity

Evidence produced: deterministic identifier-only fixture coverage for topology
identifier normalization and exact canonical identifier equality.

Strengths: fixture is committed, deterministic, and identifier-only. It
preserves explicit exclusions for topology movement, seam traversal, neighbor
lookup, gameplay, rendering, and physics. Diagnostics identify missing native
cases and expected Python canonical identifiers.

Limitations: no safe native/provisional identifier-only output route exists
yet. The harness intentionally reports native/provisional output as unavailable
instead of claiming native parity.

Default/advisory behaviour: unavailable native/provisional output is advisory
by default.

Strict/blocking behaviour: `TET4D_STRICT_PARITY=1` blocks native/provisional
unavailability and mismatches.

Fixture status: deterministic, committed, identifier-only, and limited to
canonical string normalization.

Native/provisional status: unavailable by design until a safe identifier-only
native route exists.

Routing status: routed through parity protocol, promotion gates, Stage 19
review, authority map, governance README, drift map, documentation map, project
structure, AGENTS, and native AGENTS.

Verdict: useful Python-oracle and routing evidence for an identifier-only slice;
not native parity evidence and not transfer-ready.

## Cross-slice findings

Default/advisory consistency: all three slices treat native/provisional
unavailability as advisory by default.

Strict/blocking consistency: all three slices use `TET4D_STRICT_PARITY=1` to
make native/provisional unavailability blocking.

Fixture quality: Stage 18 and Stage 20 use small deterministic committed JSON
fixtures. Stage 15 uses a small deterministic in-code text fixture set.

Failure diagnostics: diagnostics are actionable for missing cases, unexpected
cases, and exact mismatch values. Stage 20 additionally states that no safe
native/provisional route exists.

Native/provisional evidence: Stage 18 has the strongest native/provisional
surface. Stage 15 has pilot native/provisional coverage. Stage 20 has no native
route yet and correctly reports that gap.

Authority boundary: no slice transfers authority. Python remains the semantic
oracle, Godot remains product shell/presentation, and native/C++ remains
provisional.

Routing completeness: active parity evidence is routed through architecture,
governance, project maps, and AGENTS files.

Remaining gaps:

- no dedicated `tools/parity/` route yet
- no native/provisional route for Stage 20 topology identifier normalization
- no authority-transfer readiness for any subsystem
- no structural parity slice has been selected

## Parity tooling route decision

Current route: parity harnesses remain under `tools/migration/`.

Decision: keep `tools/migration/` for now.

Reason: the current harnesses are still migration evidence for the Godot/native
port. They have not become a reusable parity subsystem independent of migration.

Create `tools/parity/` when there are at least four maintained parity harnesses,
or when parity harnesses are used outside the Godot/native migration path.

Do not move files before that trigger is met.

Stage 24 update: `docs/architecture/parity_tooling_package_review.md`
supersedes this Stage 21 route decision after Stage 22 added the fourth
maintained parity harness. Stage 24 approves a future isolated Stage 25
`tools/parity/` routing/refactor, but still does not move files or transfer
authority.

## Next-stage recommendation

Recommended next stage: select and implement one additional data-only parity
slice only after this review is accepted.

Candidate: trace schema/version normalization.

Implemented by:
`docs/architecture/trace_schema_version_normalization_parity.md`.

Harness: `tools/migration/trace_schema_version_normalization_parity.py`.

Fixture: `tests/fixtures/parity/trace_schema_version_normalization.json`.

This is parity evidence only. It remains schema/version metadata-only and does
not transfer authority.

Reason: it is data-only, trace/replay relevant, exact-comparison friendly, not
topology mechanics, not renderer-owned, and not gameplay mutation.

Allowed scope:

- schema version field normalization
- trace metadata/schema labels
- deterministic fixture-based exact comparison
- Python-oracle output and provisional native comparison only if a safe route
  exists

Forbidden scope:

- topology movement
- seam traversal
- neighbor lookup
- rotation
- gravity/drop
- collision
- lock/clear/gameplay loop
- rendering/projection/view/camera
- endgame physics

Candidate options considered:

- trace schema/version normalization: recommended
- dimension label normalization: acceptable fallback if schema/version is
  exhausted
- topology category/family classification: defer unless it can be proven
  identifier-only and non-mechanical
- coordinate/bounds normalization: defer until ownership is proven isolated and
  non-renderer-owned

## Authority-transfer readiness

Ready for authority transfer: no.

Reason: the package contains useful parity evidence, but no subsystem has full
promotion coverage, fallback routing, known exclusions, authority-map update,
and a completed transfer record.

Candidate transfer record created: no.

Transferred authority: no.

Next evidence needed:

- at least one subsystem-sized parity package with Python oracle, committed
  fixtures, native/provisional output, comparison command, strict/default
  behavior, known exclusions, fallback path, and passing validation
- explicit authority-transfer record with `transferred` status
- authority map update after the transfer record is complete

## Explicit forbidden areas

The next implementation must not include:

- topology movement
- seam traversal
- neighbor lookup
- rotation
- gravity/drop
- collision
- lock/clear/gameplay loop
- rendering/projection/view/camera
- endgame physics
