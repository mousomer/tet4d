# Godot/C++ Product and Migration Policy

This policy extends the reusable workspace governance in
`docs/governance/workspace_bundle/`.

## Scope

This policy applies to Godot, GDExtension, native C++, migration work, and new
Godot/native product capabilities.

It does not replace the owning RDS, architecture contract, subsystem authority
map, or professional product programme.

## Architecture

Use the actual repository structure and preserve these boundaries:

- inherited Python behaviour: reference authority until transferred or retired;
- Godot: product shell, UI, rendering, input routing, animation, diagnostics,
  accessibility, camera, view-basis presentation, Explorer interaction, and
  challenge/campaign presentation;
- C++/GDExtension/native code: parity-backed implementation of inherited
  deterministic logic and direct authority candidate for genuinely new
  deterministic subsystems;
- versioned declarative data: authority for challenge/campaign content and
  other named product data;
- adapter layer: thin conversion boundary between Godot and deterministic
  logic.

Implementation alone does not transfer inherited authority or establish new
authority. Both operations route through
`docs/architecture/authority_transfer_protocol.md` and
`docs/architecture/authority_map.md`.

## Inherited versus new behaviour

Before implementation, classify the feature.

### Inherited behaviour

Inherited behaviour already has an accepted reference implementation or
contract.

Requirements:

- identify the current reference owner;
- identify exact behaviour and exclusions;
- reuse or port without silent semantic change;
- provide parity or equivalent conformance evidence;
- complete authority transfer before claiming a new owner.

### New behaviour

New behaviour has no accepted predecessor.

Requirements:

- define it through an owning RDS, specification, or schema;
- name deterministic, presentation, and data owners separately;
- provide conformance tests and compatibility rules;
- establish authority explicitly;
- do not implement it in Python solely to manufacture an oracle.

## Godot product and presentation authority

Godot may own new product and presentation semantics, including:

- menus, setup interaction, and scenes;
- camera orientation and exact camera turns;
- 4D view/presentation basis and slice layout;
- basis-transition animation;
- HUD, guidance, hints, and accessibility presentation;
- Explorer interaction;
- challenge selection, progress, and campaign navigation;
- visual diagnostics.

Godot must not duplicate inherited deterministic semantics such as:

- topology rules;
- legal movement;
- collision;
- gravity/drop behaviour;
- piece rotation legality;
- scoring;
- trace semantics;
- replay correctness.

Godot may display, animate, route, request, and compose authoritative state.
Deterministic rules that must be shared across Play, Explore, and Challenge
belong in the named core authority rather than GDScript UI glue.

The semantic-boundary validator scans Godot scripts for suspicious local rule
computation. Legitimate presentation/routing cases may use a narrow suppression
with a reason.

## Native deterministic authority

Native C++ may implement:

- inherited deterministic behaviour under parity and transfer rules;
- genuinely new deterministic behaviour under establishment rules.

Potential new native subsystems include Hold transitions, challenge predicates,
shared geometric comparison, and future simulation behaviour beyond the
inherited Python model.

Keep deterministic core logic independent from Godot where practical and keep
the Godot-facing adapter thin.

## Memory safety

Native C++ and GDExtension memory-safety rules live in
`docs/governance/cpp_safety_policy.md`.

Native tooling CI-readiness rules live in
`docs/governance/native_tooling_ci_policy.md`.

## No rewriting inherited functions by convenience

Migration must reuse, map, or wrap inherited semantics. Do not rewrite Python
functions as a side effect of porting.

Before porting inherited behaviour, identify:

- current authority;
- file/function/class or normative contract;
- observable behaviour;
- tests/traces;
- reuse/mapping plan;
- transfer boundary.

For new behaviour, identify the normative contract and intended owner rather
than searching for a nonexistent Python implementation.

## No reinventing utilities

Before adding helpers, search for existing utilities. Follow
`docs/policies/POLICY_NO_REINVENTING_WHEEL.md`.

If adding a reusable helper, update the utility index.

Prefer existing libraries over new custom implementations for:

- test frameworks;
- serialization/parsing;
- schema validation;
- secret scanning;
- formatting/static analysis;
- platform abstraction.

Do not add a large dependency for trivial code.

## Comments

For C++ public APIs and stored Godot pointers, follow
`docs/governance/cpp_safety_policy.md`.

Comments in migration or new core code must explain:

- intent;
- invariants;
- authority boundary;
- ownership;
- coordinate conventions;
- topology conventions;
- boundary conversions;
- non-obvious algorithm choices.

Do not add comments that merely restate obvious code.

## Size limits

Use these budgets for native/Godot work and new governance examples:

- function target: 40 logical LOC;
- function hard limit: 80 logical LOC;
- `.cpp` target: 300 LOC;
- `.cpp` hard limit: 500 LOC;
- header target: 180 LOC;
- header hard limit: 350 LOC;
- folder target: 12 owned files;
- folder hard limit: 20 owned files;
- nesting target: 3 levels;
- parameter target: 5 parameters.

If a limit is exceeded, document why and add a follow-up note.

## Constants/config

No nontrivial magic numbers in source. Follow
`docs/governance/config_policy.md` and
`docs/policies/POLICY_NO_MAGIC_NUMBERS.md`.

Godot presentation-only constants may live in Godot theme/config resources.
Inherited gameplay/topology constants must not be redefined independently in
Godot. New deterministic constants belong to their normative contract and
core/data owner.

## Tests and authority evidence

Every inherited port needs parity or equivalent conformance evidence against
its accepted reference.

Every new deterministic subsystem needs conformance evidence against its
normative contract.

Expected categories include:

- Python tests/traces for inherited reference behaviour;
- golden traces or equivalent parity fixtures for inherited ports;
- C++ unit tests for native deterministic logic;
- schema/validator tests for declarative data;
- Godot integration tests for adapter and product behaviour;
- manual visual acceptance where presentation quality is part of the contract.

A visual Godot demo is not a substitute for inherited semantic parity or new
deterministic conformance evidence.
