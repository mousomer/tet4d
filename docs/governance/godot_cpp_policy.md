# Godot/C++ Migration Policy

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

For C++/native code:

- No raw owning pointers.
- No naked `new` or `delete`.
- Prefer values and RAII.
- Use `std::unique_ptr` or `std::shared_ptr` only when ownership requires it.
- Avoid pointer arithmetic.
- Avoid C-style casts.
- No unsafe casts without written justification.
- No global mutable state unless explicitly justified.
- No detached threads.
- Public APIs must document ownership, nullability, lifetime, preconditions,
  and failure modes.

For Godot-facing native code:

- Keep Godot object lifetime rules at the boundary.
- Use Godot reference types appropriately where applicable.
- Stored Godot object pointers are non-owning unless explicitly documented.
- Any stored Godot pointer must document owner, lifetime, nullability, and
  invalidation condition.

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

Comments must explain:

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

Use the repo testing policy. Expected categories:

- Python tests for current oracle behavior
- golden traces or equivalent parity fixtures
- C++ unit tests for native deterministic logic
- Godot integration tests for adapter/UI behavior

A visual Godot demo is not a substitute for semantic parity.
