# Trace Envelope Validation Parity

## Purpose

This document defines the Stage 27 trace envelope validation parity slice.

This parity slice validates the trace envelope only. It checks the top-level
trace object and the envelope fields that let future trace consumers identify,
load, and route a trace before any semantic interpretation begins.

It is structural rather than behavioural.

## Authority boundary

Python remains the semantic oracle.

Native/C++ remains provisional.

Godot remains product shell/presentation.

Passing this parity slice does not transfer authority from Python to Godot or
C++.

## Inputs

Trace envelope validation fixture:
`tests/fixtures/parity/trace_envelope_validation.json`

Parity harness:
`tools/parity/trace_envelope_validation_parity.py`

Tests:
`tests/unit/migration/test_trace_envelope_validation_parity.py`

## Validated envelope fields

The Stage 27 harness validates only:

- trace is a JSON object
- `trace_type` exists and is a non-empty string
- `trace_version` exists and is an integer
- `case_id` exists and is a non-empty string
- `dimension` exists and is an integer
- `generator` exists and is an object
- `generator.name` exists and is a non-empty string
- `generator.schema_version` exists and is an integer
- `frames` exists and is an array
- `final` exists and is an object
- `final.state_hash` exists and is a non-empty string

`frames` is validated only as a container. The harness does not inspect frame
contents or event payloads.

`final.state_hash` is treated as the current envelope digest field for this
slice. The harness checks presence and string shape only; it does not recompute
or interpret the digest.

## Explicit exclusions

This parity slice validates the trace envelope only.
It does not validate trace event semantics.
It does not validate board states, piece positions, topology traversal,
movement, drop/collision/lock, rendering, or camera/view behaviour.
It does not transfer authority from Python to Godot or C++.

Additional exclusions:

- event sequence correctness
- event type meaning
- board cell correctness
- piece coordinate correctness
- movement legality
- topology neighbor/seam behaviour
- gameplay-loop outcomes
- rendered projection correctness
- native/Godot comparison

## Python oracle

The Python oracle is the local structural validator inside
`tools/parity/trace_envelope_validation_parity.py`.

The fixture records valid and invalid envelope examples plus expected
diagnostics. The oracle recomputes diagnostics and compares them with the
fixture expectations.

## Native/provisional target

No safe native/provisional route exists for trace envelope validation in this
stage.

Default mode is advisory when the native/provisional route is unavailable.
Strict mode `TET4D_STRICT_PARITY=1` blocks that unavailability.

Do not claim native parity when the native/provisional path is unavailable.

## Comparison rule

Exact equality of envelope validation results and diagnostics.

## Commands

Default/advisory:
`python tools/parity/trace_envelope_validation_parity.py`

Strict:
`TET4D_STRICT_PARITY=1 python tools/parity/trace_envelope_validation_parity.py`

Tests:
`python -m pytest -q tests/unit/migration/test_trace_envelope_validation_parity.py`

## Acceptance criteria

- fixture is deterministic and envelope-only
- valid envelope examples pass
- invalid envelope examples fail with stable diagnostics
- event payload semantics are not inspected
- default mode is advisory if native/provisional unavailable
- strict mode fails on unavailability or mismatch
- no authority transfer is claimed
- routing is complete
