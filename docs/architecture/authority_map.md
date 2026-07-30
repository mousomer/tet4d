# Authority Map

This map defines current migration ownership. It complements
`config/project/policy_pack.json`, `docs/WORKFLOW_CODEX.md`,
`docs/ARCHITECTURE_CONTRACT.md`, and relevant `docs/rds/*`; it does not replace
them.

## Current semantic authority

The existing Python implementation remains the semantic oracle for:

- topology and legal movement;
- rotation, collision, gravity, and drop/lock behaviour;
- scoring and gameplay state transitions;
- trace and replay semantics;
- configuration defaults and current product behaviour.

Do not rewrite those semantics during migration unless the task explicitly
requests a product change through the relevant RDS and tests.

## Godot product-shell authority

Godot is the product-shell direction and owns UI shell, menus, scenes, input
routing, animation, rendering, camera/presentation, inspector/probe panels,
visual diagnostics, and product usability.

Godot and GDScript do not own game-rule semantics. They consume Python traces,
native adapter APIs, or another documented authoritative core API. Visual
plausibility is not semantic evidence.

## Native C++ / GDExtension status

Native code contains parity-backed implementations and query/session surfaces,
including accepted plain bounded gameplay and later deterministic geometry and
legality/topology diagnostic slices. Their implementation responsibilities are
documented in current plans, tests, and `CURRENT_STATE.md` when phase context is
needed.

Those implementations remain provisional semantic ports. No active transfer
record currently moves semantic authority from Python. A native subsystem
receives authority only when:

1. the Python owner and observable behaviour are identified;
2. versioned golden traces, fixtures, or equivalent regression evidence exist;
3. the native implementation passes the documented parity comparison;
4. the Godot adapter does not duplicate the semantics;
5. `docs/architecture/authority_transfer_protocol.md` contains a completed
   subsystem-specific transfer record; and
6. this map records that transfer.

`docs/architecture/parity_protocol.md` defines parity evidence. Parity evidence
alone, successful native execution, type safety, or successful Godot display
does not transfer authority. One transferred subsystem would not make the
whole native port authoritative.

## Migration routing

Use durable work categories rather than loading every completed slice:

- parity implementation: parity protocol plus the selected subsystem document,
  harness, fixtures, and tests;
- parity evidence review: promotion gates, evidence package, and affected
  comparisons;
- authority transfer: authority-transfer protocol, evidence, fallback, and this
  map;
- native migration: relevant plan, native dispatch, safety/tooling policy, and
  parity evidence;
- Godot product shell: Godot dispatch and relevant product/presentation
  authority;
- topology migration: current topology authority, topology port plan, Python
  oracle/runtime, and tests.

`docs/DOCUMENTATION_MAP.md` and `docs/governance/README.md` index current and
historical parity documents without making completed stages universal context.

## Forbidden migration shortcuts

- Reimplementing semantic truth in GDScript or adapter glue.
- Rewriting Python logic for port convenience without an explicit semantic
  change request.
- Duplicating topology, movement, collision, gravity, scoring, or trace
  utilities.
- Treating parity evidence as authority transfer.
- Expanding a parity slice beyond its documented scope or exclusions.
- Letting Godot presentation define game-rule semantics.
