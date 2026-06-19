# Godot/C++ Migration Policy

This policy extends the reusable workspace governance in
`docs/governance/workspace_bundle/`.

## Scope

This policy applies only to Godot, GDExtension, native C++, and migration work.
It does not replace existing Python-centered governance.

## Architecture

Use the actual repository structure, but preserve these boundaries:

- Python implementation: current semantic oracle.
- Godot: product shell, UI, rendering, input, animation, diagnostics.
- C++/GDExtension/native code: provisional port of selected deterministic logic
  until parity is documented.
- Adapter layer: thin conversion boundary between Godot and deterministic
  logic.

## Memory safety

Native C++ and GDExtension memory-safety rules live in
`docs/governance/cpp_safety_policy.md`.

Migration work must keep deterministic rule logic independent from Godot where
practical and keep Godot-facing adapter code thin.

## No semantic duplication

GDScript must not implement or duplicate:

- topology rules
- legal movement
- collision
- gravity/drop behavior
- rotation
- scoring
- trace semantics
- replay correctness

GDScript may:

- present state
- animate state
- route input
- call adapter/core APIs
- display diagnostics
- manage menus and scenes

## Godot semantic boundary

Godot may display, animate, route, and request semantic state. Godot must not
independently compute topology, movement, collision, gravity, rotation, scoring,
trace correctness, or replay correctness.

The semantic-boundary validator scans Godot scripts for suspicious local rule
computation. Legitimate display/routing cases may use a narrow suppression with
a reason.

## No rewriting existing functions

Migration must reuse, map, or wrap existing Python semantics. Do not rewrite
Python functions as a side effect of porting.

Before adding C++/Godot logic, identify the existing Python authority:

- file
- function/class
- behavior
- tests/traces
- reuse/mapping plan

## No reinventing utilities

Before adding helpers, search for existing utilities. Follow
`docs/policies/POLICY_NO_REINVENTING_WHEEL.md`.

If adding a reusable helper, update the utility index.

Prefer existing libraries over new custom implementations for:

- test frameworks
- serialization/parsing
- schema validation
- secret scanning
- formatting/static analysis
- platform abstraction

Do not add a large dependency for trivial code.

## Comments

For C++ public APIs and stored Godot pointers, follow
`docs/governance/cpp_safety_policy.md`.

Comments in migration code must explain:

- intent
- invariants
- ownership
- coordinate conventions
- topology conventions
- boundary conversions
- non-obvious algorithm choices

Do not add comments that merely restate obvious code.

## Size limits

Use these budgets for native/Godot migration code and new governance examples:

- function target: 40 logical LOC
- function hard limit: 80 logical LOC
- `.cpp` target: 300 LOC
- `.cpp` hard limit: 500 LOC
- header target: 180 LOC
- header hard limit: 350 LOC
- folder target: 12 owned files
- folder hard limit: 20 owned files
- nesting target: 3 levels
- parameter target: 5 parameters

If a limit is exceeded, document why and add a follow-up note.

## Constants/config

No nontrivial magic numbers in source. Follow
`docs/governance/config_policy.md` and
`docs/policies/POLICY_NO_MAGIC_NUMBERS.md`.

Godot presentation-only constants may live in Godot theme/config resources.
Gameplay and topology constants must not be redefined independently in Godot.

## Tests

Every ported behavior needs parity evidence against Python.

Semantic parity requirements for native subsystems are defined in
`docs/architecture/parity_protocol.md`. C++/GDExtension code remains
provisional until parity evidence exists and the authority map records the
transfer.

Use the repo testing policy. Expected categories:

- Python tests for current oracle behavior
- golden traces or equivalent parity fixtures
- C++ unit tests for native deterministic logic
- Godot integration tests for adapter/UI behavior

A visual Godot demo is not a substitute for semantic parity.
