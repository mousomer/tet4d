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
