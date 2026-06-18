# Testing Policy

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
