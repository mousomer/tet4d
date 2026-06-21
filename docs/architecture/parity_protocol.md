# Parity Protocol

## Scope

This protocol defines how C++/GDExtension implementations prove equivalence
with the current Python implementation.

It does not make C++ authoritative. Python remains the semantic oracle until
parity evidence is committed and `docs/architecture/authority_map.md` records
the authority transfer.

## Definition of parity

Parity means that, for a defined subsystem, the C++/GDExtension
implementation produces the same observable semantic results as the Python
implementation for the same versioned inputs, configuration, topology, seed
data, and initial state.

Visual similarity is not parity. A Godot scene appearing correct is not
parity.

## Parity versus authority transfer

Parity evidence is necessary but not sufficient for authority transfer.

A candidate implementation that passes parity checks remains provisional until
`docs/architecture/authority_transfer_protocol.md` contains a completed
transfer record and the authority map is updated.

## Python oracle

The Python implementation is the oracle for:

- topology transitions
- legal movement
- rotation
- collision
- gravity/drop behavior
- line/cell clearing semantics
- scoring, if implemented
- trace semantics
- replay correctness
- deterministic configuration defaults

## Golden evidence

Golden evidence may include:

- Python-generated traces
- deterministic input/output fixtures
- replay comparison fixtures
- serialized board/topology states
- seed-based deterministic simulation outputs
- regression cases derived from known bugs

Each fixture must record or identify:

- subsystem
- Python source/version or commit
- configuration source
- input state
- expected output
- comparison mode
- tolerance, if any
- reason the fixture exists

## Comparison modes

Use exact comparison for:

- integer coordinates
- topology labels
- cell occupancy
- legal/illegal move decisions
- discrete state transitions
- trace event ordering
- scoring integers

Use tolerance comparison only for:

- projection math
- floating-point diagnostics
- animation-independent numeric output

Tolerances must be documented per fixture or subsystem. Do not use broad
global tolerances to hide semantic differences.

## Disagreement rule

If Python and C++ disagree:

1. Treat Python as correct by default.
2. Check whether the fixture is stale or malformed.
3. Check whether the Python behavior is known-bug-compatible.
4. Do not adjust C++ merely to pass a visual test.
5. Do not change Python semantics unless the task explicitly requests a
   semantic change.
6. Record the decision if authority or expected behavior changes.

## Subsystem promotion

A C++ subsystem may become authoritative only after:

1. Python owner behavior is identified.
2. Golden evidence exists.
3. C++ implementation passes parity checks.
4. Regression tests are committed.
5. Godot adapter, if relevant, calls the C++ path rather than duplicating
   semantics.
6. `docs/architecture/authority_map.md` is updated.
7. Any old duplicate/provisional path is explicitly deprecated, removed, or
   retained as oracle fallback.

## Fixture location

Use the repository's existing fixture layout:

- `migration/golden_traces/` for committed Python-oracle migration traces.
- `tests/replay/golden/` for replay test fixtures.
- `migration/exported_bundle/traces/` for exported bundle copies, not primary
  authority.

Do not add large generated fixtures without review.

## Naming

Fixture names should include:

```text
<subsystem>__<scenario>__<purpose>.<ext>
```

Examples:

```text
topology__x_wrap_edge__legal_transition.json
rotation__2d_rigid_l_shape__orientation_cycle.json
gravity__y_boundary_no_fallthrough__regression.json
trace__basic_drop_lock__event_order.json
```

Existing migration trace case IDs may keep their current names when they are
already referenced by `tools/migration/trace_cases.py` or
`tools/migration/compare_cpp_gameplay_trace.py`.

## Review rule

Any PR or task that claims C++ parity must state:

- Python authority used
- fixtures used
- comparison command
- result
- known exclusions
- authority-map update, if any

## First subsystem parity pilot

The repository's first parity pilot is a narrow evidence-only trial for
`stable_hash_text(text)`.

It uses a fixed text fixture set, a Python oracle helper, and the existing
native/Godot-facing bridge to compare exact text-hash outputs. The pilot
proves the parity process, not subsystem promotion, and it does not transfer
authority.

Pilot authority and routing live in
`docs/architecture/first_subsystem_parity_pilot.md`.

Future parity slices must also satisfy
`docs/architecture/parity_pilot_audit_and_promotion_gates.md` before a second
parity slice is added.

Stage 17 selected the only Stage 18 implementation candidate in
`docs/architecture/second_parity_slice_candidate_selection.md`. Stage 18 may
implement only that selected trace metadata identity/digest slice. Candidate
selection does not transfer authority. This is the selected second parity
slice boundary.

Second parity slice selection: trace metadata identity/digest.
Candidate selection does not transfer authority.

Stage 18 trace metadata identity/digest parity evidence and implementation
details live in
`docs/architecture/trace_metadata_identity_digest_parity.md`.

Stage 19 evidence review and third-slice selection live in
`docs/architecture/parity_evidence_review_and_third_slice_selection.md`.
That review compares the first pilot and Stage 18 evidence, then selects the
next safe slice without transferring authority.

Stage 20 implementation lives in
`docs/architecture/topology_identifier_normalization_parity.md`.
That topology identifier normalization slice is identifier-only, remains
provisional, and does not transfer authority.

Stage 20 harness and fixture:
`tools/parity/topology_identifier_normalization_parity.py` and
`tests/fixtures/parity/topology_identifier_normalization.json`.

Stage 20 must not expand into topology movement, seam traversal, neighbor
lookup, rotation, collision, gravity/drop, lock/clear/gameplay loop,
rendering/projection/view/camera, or endgame physics.

Stage 21 parity evidence package review lives in
`docs/architecture/parity_evidence_package_review.md`.
That review summarizes Stages 15, 18, and 20, records the then-current
`tools/migration/` route, recommends trace schema/version normalization as the
next data-only candidate, and does not transfer authority.

Stage 22 implementation lives in
`docs/architecture/trace_schema_version_normalization_parity.md`.
Stage 22 implements only trace schema/version normalization and does not
transfer authority.

Stage 22 harness and fixture:
`tools/parity/trace_schema_version_normalization_parity.py` and
`tests/fixtures/parity/trace_schema_version_normalization.json`.

Stage 24 package review lives in
`docs/architecture/parity_tooling_package_review.md`.
It records the package-routing decision only. Stage 25 applies the approved
isolated routing/refactor that moves the maintained parity harnesses into
`tools/parity/` without adding parity logic, changing fixtures, or transferring
authority.

Stage 26 structural parity slice selection lives in
`docs/architecture/structural_parity_slice_selection.md`.
It selects trace envelope validation as the Stage 27 target only. Stage 26
does not implement a harness, add fixtures, inspect trace events, or transfer
authority.

Parity evidence and promotion-gate acceptance remain evidence only. They do not
transfer authority without
`docs/architecture/authority_transfer_protocol.md` and an authority-map update.
