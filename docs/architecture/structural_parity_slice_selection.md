# Structural Parity Slice Selection

## Purpose

Stage 26 selects the next parity slice after the established
normalization/data-only parity foundation.

This stage selects a target only.
This stage does not implement a new parity harness.
This stage does not add fixtures.
This stage does not alter gameplay, topology, movement, trace events, Godot,
C++, or authority state.

Decision: select trace envelope validation for Stage 27.

## Current Parity Foundation

The maintained parity/evidence surfaces now live under `tools/parity/`.

| Stage | Surface | Harness path | Fixture path | Test path | Protected contract |
| --- | --- | --- | --- | --- | --- |
| 15 | First subsystem parity pilot | `tools/parity/first_subsystem_parity_pilot.py` | In-code fixture set: `""`, `tet4d`, `oracle-check`, `hash-bridge` | `tests/unit/migration/test_first_subsystem_parity_pilot.py` | Exact `stable_hash_text(text)` comparison between Python oracle and native/provisional output; process evidence only. |
| 18 | Trace metadata identity/digest parity | `tools/parity/trace_metadata_identity_digest_parity.py` | `tests/fixtures/parity/trace_metadata_identity_digest.json` | `tests/unit/migration/test_trace_metadata_identity_digest_parity.py` | Compact canonical trace metadata identity and digest equality. |
| 20 | Topology identifier normalization parity | `tools/parity/topology_identifier_normalization_parity.py` | `tests/fixtures/parity/topology_identifier_normalization.json` | `tests/unit/migration/test_topology_identifier_normalization_parity.py` | Canonical topology identifier normalization without topology mechanics. |
| 22 | Trace schema/version normalization parity | `tools/parity/trace_schema_version_normalization_parity.py` | `tests/fixtures/parity/trace_schema_version_normalization.json` | `tests/unit/migration/test_trace_schema_version_normalization_parity.py` | Trace schema/version metadata identity without interpreting trace events. |

These slices provide comparison scaffolding and narrow metadata/normalization
guardrails. They do not transfer authority and they do not prove gameplay,
topology traversal, movement, rendering, or native implementation parity.

## Candidate Selection Criteria

A valid next slice must be:

- structural rather than behavioural
- testable against existing Python/oracle outputs or fixtures
- isolated from movement/topology/gameplay mechanics
- independent of rendering/view/camera behaviour
- independent of Godot/native authority transfer
- small enough to review and revert
- useful as a guardrail for future trace consumers

A candidate must be rejected if it requires:

- interpreting trace events
- comparing board states
- comparing piece positions
- traversing topology
- validating movement legality
- simulating drop/collision/lock behaviour
- comparing rendered output
- adding native/provisional implementation
- changing golden fixture semantics

## Candidate Review

| Candidate | Classification | Reason |
| --- | --- | --- |
| trace envelope validation | selected | Structural, top-level, and useful for future trace consumers without inspecting gameplay events. |
| trace event validation | unsafe for now | Risks entering event meaning, ordering, and gameplay semantics. |
| board snapshot validation | unsafe for now | Touches board state semantics and would need a more explicit gameplay boundary. |
| piece position validation | unsafe for now | Touches movement and spatial semantics. |
| topology traversal validation | unsafe for now | Touches topology mechanics, neighbor lookup, and transport behaviour. |
| movement/drop validation | unsafe for now | Direct gameplay behaviour, including movement legality and drop/collision/lock results. |
| render/view/camera validation | out of scope | Product-shell/display concern, not semantic parity at this stage. |

## Selected Slice: Trace Envelope Validation

Stage 27 validates only the top-level trace envelope structure in
`docs/architecture/trace_envelope_validation_parity.md`.

Allowed Stage 27 scope:

- top-level trace object shape
- required metadata keys
- schema/version field presence
- identity/digest field presence
- fixture envelope structure
- stable validation result comparison
- clear pass/fail diagnostics for missing or malformed envelope fields

The selected slice must not inspect or validate the semantic contents of trace
events.

Allowed examples:

- trace is a JSON object
- trace has expected top-level metadata/envelope fields
- schema/version field exists and is normalized
- identity/digest fields exist where required by current trace contract
- events field exists only as a container shape, if required by current
  contract
- fixture envelope can be loaded and checked consistently

Forbidden examples:

- event sequence correctness
- event type semantics
- board cell correctness
- piece coordinate correctness
- movement legality
- drop/collision/lock results
- topology neighbor/seam behaviour
- rendered projection correctness
- camera/view correctness
- native/Godot comparison

## Stage 27 Proposed Deliverables

Stage 27 uses these final paths:

- `tools/parity/trace_envelope_validation_parity.py`
- `tests/fixtures/parity/trace_envelope_validation.json`
- `tests/unit/migration/test_trace_envelope_validation_parity.py`
- `docs/architecture/trace_envelope_validation_parity.md`

Stage 26 did not create these files.

## Stage 27 Guardrails

Stage 27 must preserve:

- Python remains semantic oracle.
- No authority transfer.
- No native/Godot implementation.
- No fake native/provisional output.
- Default harness mode should remain advisory if no native/provisional route
  exists.
- Strict mode should block if a required safe native/provisional route does not
  exist.
- No gameplay, topology, movement, trace-event, rendering, Godot
  scene/resource, config, or bundle regeneration work.

Stage 27 must not include:

- topology mechanics
- seams/neighbours
- movement
- drop/collision/lock
- board snapshots
- piece positions
- trace event semantic validation
- rendering/view/camera
- Godot implementation
- C++ implementation
- authority transfer

## Impact on Later Stages

The intended later sequence is:

```text
27. Implement trace envelope validation parity slice
28. Authority-transfer readiness review
```

Topology mechanics remain deferred.

Do not start seams, neighbours, movement, drop/collision, gameplay-loop parity,
or Godot-native semantic comparison until after an additional explicit
readiness review.

## Boundary Statement

This selection does not transfer authority from Python to Godot or C++.
This selection does not approve deletion of Python semantic code.
This selection does not authorize gameplay, topology, trace-event, movement,
rendering, Godot, or native-code changes.
This selection does not implement trace envelope validation.
This selection only authorizes Stage 27 to implement the selected slice within
the stated boundaries.
