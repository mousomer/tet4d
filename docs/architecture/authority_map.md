# Authority Map

This map clarifies migration ownership. It does not replace
`config/project/policy_pack.json`, `docs/WORKFLOW_CODEX.md`,
`docs/ARCHITECTURE_CONTRACT.md`, or relevant `docs/rds/*` product authorities.

## Current semantic authority

The existing Python implementation owns semantics for:

- topology
- legal movement
- rotation
- collision
- gravity/drop behavior
- trace semantics
- scoring
- replay correctness
- configuration defaults
- current gameplay behavior

These behaviors must not be rewritten during migration unless the task
explicitly requests a semantic change.

## Godot authority

Godot owns:

- UI shell
- menus
- scene composition
- input routing
- animation
- rendering
- camera/presentation
- inspector/probe panels
- product usability
- visual diagnostics

Godot does not own game-rule semantics.

## C++/GDExtension authority during migration

C++/GDExtension may own a ported subsystem only after:

1. The existing Python behavior is identified.
2. Existing Python utilities/functions are reused, wrapped, or mapped.
3. Golden traces, regression tests, or equivalent parity evidence exist.
4. The C++ implementation passes those parity checks.
5. This authority map or a narrower authority document records the transfer.

Until then, C++/GDExtension implementation is provisional.

Current accepted native authority is limited to already documented parity-backed
plain bounded gameplay surfaces in `docs/plans/godot_core_port_plan.md` and
`CURRENT_STATE.md`. Topology implementation remains deferred by
`docs/plans/topology_godot_core_port_plan.md`.
The first subsystem parity pilot is evidence only and does not change
authority.

## Authority transfer requires parity

A C++/GDExtension subsystem is provisional until it satisfies
`docs/architecture/parity_protocol.md`.

C++ existence, cleaner implementation, type safety, or successful Godot display
do not transfer semantic authority.

Authority transfer is subsystem-specific. One C++ subsystem passing parity does
not make the whole native port authoritative.

## Authority transfer

The existing Python implementation remains the current semantic oracle.

Authority may move away from Python only through
`docs/architecture/authority_transfer_protocol.md`.

Parity evidence alone does not transfer authority.

A document may not claim C++/GDExtension, Godot, or GDScript owns semantic
gameplay behavior unless a completed transfer record exists and this authority
map has been updated.

## Forbidden migration shortcuts

- Reimplementing Python semantics in GDScript.
- Rewriting Python logic while porting unless explicitly requested.
- Changing semantics to make C++ cleaner.
- Duplicating topology, movement, collision, gravity, scoring, or trace
  utilities.
- Treating visual plausibility as semantic correctness.
- Letting Godot UI behavior define game-rule semantics.
