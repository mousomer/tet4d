# Testing Policy

This policy extends the reusable workspace governance in
`docs/governance/workspace_bundle/`.

## Python oracle tests

Current Python behavior must remain covered by existing tests where available.
When a behavior becomes migration-critical, add or identify tests/traces that
define it.

## Golden parity

A ported subsystem is not authoritative until parity evidence exists.

Parity evidence may include:

- golden traces generated from Python
- regression fixtures
- deterministic replay comparisons
- equivalent input/output test cases

## C++ / Python parity tests

Native C++ behavior that corresponds to existing Python semantics requires
parity evidence before it can be treated as authoritative.

Required for parity claims:

- identified Python oracle behavior
- deterministic inputs
- expected Python output
- comparison command or documented comparison process
- regression coverage for known edge cases
- authority-map update when ownership changes

Visual Godot tests are not substitutes for parity tests.

## C++ tests

Native deterministic logic requires unit tests.

Tests must cover:

- normal cases
- boundary cases
- invalid inputs
- regression cases
- parity with Python where applicable

## Godot tests

Godot tests verify:

- adapter call wiring
- scene/UI behavior
- input routing
- display of state
- diagnostics
- no duplicated semantic rule logic in scripts

Godot visual inspection is useful but not sufficient for semantic correctness.

## Bug fixes

Every bug fix requires a regression test or a documented reason why a test
cannot yet be added.
