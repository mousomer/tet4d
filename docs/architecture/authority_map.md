# Authority Map

This map defines current semantics ownership, migration ownership, and product-
subsystem authority. It complements `config/project/policy_pack.json`,
`docs/WORKFLOW_CODEX.md`, `docs/ARCHITECTURE_CONTRACT.md`, relevant
`docs/rds/*`, `docs/architecture/parity_protocol.md`, and
`docs/plans/professional_godot_game_programme.md`; it does not replace them.

## Authority principle

Tet4D does not assign universal semantic authority to one implementation
language.

Authority is subsystem-specific.

Python remains reference authority for inherited Python behaviour that has not
been transferred or retired. New capabilities without a Python predecessor may
establish authority directly in native C++, Godot, or versioned declarative
data according to their owning contract.

Do not implement a new capability in Python solely to manufacture an oracle.

## Current authority matrix

| Subsystem | Current authority | Notes |
| --- | --- | --- |
| Inherited gameplay legality, piece transformations, gravity, drop/lock, clear, and scoring not explicitly transferred | Python reference implementation | Native live implementations remain parity-backed/provisional except where a future transfer record says otherwise. |
| Existing topology semantics and Play/Sandbox policy | Python topology implementation and canonical topology contracts | Native transport/query implementation does not by itself transfer topology semantics. |
| Existing replay, trace, and compatibility semantics | Python/reference contracts and versioned fixtures | Transfer may occur by bounded subsystem. |
| Existing locked-cell explosion semantics | Python headless model and golden traces | New physics beyond this model may establish separate native authority. |
| Accepted native bounded live-session execution | Native C++ implementation | Runtime implementation ownership is not automatically semantic authority; review and transfer bounded subsystems explicitly. |
| Native topology profile and resolver-query transport | Native C++ | Strict transport implementation ownership only. |
| Professional live-board setup admissibility and extent validation (`AE-0054`) | Versioned board-extent contract and native C++ | Established only for the live product envelope, bounded-profile admission, production-piece compatibility, canonical spawn viability, volume safety, and structured safe failure. It does not transfer topology seams or gameplay transitions. |
| Godot product shell, menus, setup interaction, input routing, rendering, camera, animation, HUD, guidance, accessibility, and diagnostics | Godot/GDScript | Godot must not duplicate inherited gameplay or topology rules. |
| New Godot 3D camera and 4D presentation state | Godot/GDScript | Includes camera orientation; the Stage 54C exact signed-axis basis; the Stage 54E-2a shared `SliceLocalOrientation`, centred point mapper, and anchor-only layout decomposition; basis-aware input routing; labels; guidance; and transition animation defined by `game_safe_4d_slice_basis.md` and `4d_presentation_interaction_architecture.md`. It excludes gameplay coordinates, legality, and deterministic identity. Renderer composition through the new local orientation remains gated to Stage 54E-2b. |
| Live one-piece next preview | Inherited deterministic queue owner for piece selection; Godot/GDScript for presentation | Native sessions expose the observational shape query defined by `next_piece_preview.md`. Godot owns the shared 2D/3D/4D thumbnail and HUD placement and must not infer queue order or mutate RNG. No authority transfer occurs. |
| Live authoritative ghost piece | Existing deterministic drop/collision owner for landing; Godot/GDScript for presentation | Native hard drop and the read-only query share `hard_drop_destination` as defined by `ghost_piece.md`. Godot owns visibility, settings, basis-aware projection, and styling only. No authority transfer or establishment occurs. |
| New deterministic core behaviour without a Python predecessor | Owning native C++ subsystem named by its contract | Examples may include Hold transitions, challenge predicates, and later shared geometric evaluation. |
| Challenge and campaign content | Versioned declarative data | Runtime implementations validate and execute the content but do not silently redefine it. |
| Challenge flow, hints, progress, and Explorer interaction | Godot/GDScript | Deterministic success predicates may be native. |

## Inherited Python reference authority

Python remains reference authority only for existing behaviour that:

1. originated in the Python implementation;
2. remains intended product behaviour;
3. has not received a completed authority transfer;
4. has not been explicitly retired.

This bounded claim does not mean:

- every new feature must first exist in Python;
- every Godot feature requires Python parity;
- Python owns new presentation semantics;
- the future Explorer or challenge campaign must be mirrored in Python;
- new native systems require an artificial Python predecessor.

## Godot product and presentation authority

Godot is the product-shell direction and owns:

- menus, scenes, and setup interaction;
- input routing and control presentation;
- animation and rendering;
- 3D camera orientation;
- 4D presentation/view basis;
- shared 4D slice-local orientation;
- centred slice-local point mapping plus anchor-only slice layout;
- slice labels and basis-transition presentation;
- HUD, guidance, hints, and campaign navigation;
- accessibility and product usability;
- Explorer shell and interaction;
- visual diagnostics.

Godot may consume inherited or native deterministic core state. It must not
reimplement inherited gameplay, topology, scoring, or replay semantics in
presentation glue.

## Native C++ / GDExtension status

Native code contains parity-backed implementations and query/session surfaces,
including accepted plain bounded gameplay and deterministic geometry and
legality/topology diagnostic slices. Stage 53B owns strict implementation of
the native topology profile and resolver-query transport boundary described in
`native_topology_transport.md`; this is transport implementation ownership, not
topology semantic authority.

For inherited behaviour, native authority changes only through an explicit
transfer record.

For genuinely new deterministic behaviour, native authority may be established
directly through the authority-establishment rules in
`docs/architecture/authority_transfer_protocol.md`.

## Existing-behaviour transfer

An inherited subsystem receives transferred authority only when:

1. the current Python/reference owner and observable behaviour are identified;
2. versioned traces, fixtures, or equivalent conformance evidence exist;
3. the candidate implementation passes the documented comparison under
   `docs/architecture/parity_protocol.md`;
4. Godot or adapter code does not duplicate the semantics;
5. fallback/reversion is documented;
6. an explicit transfer record has status `transferred`;
7. this map records the change;
8. governance validation passes.

Parity evidence alone, successful native execution, type safety, or successful
Godot display does not transfer authority.

## New-behaviour establishment

A capability with no prior authority does not require a fictional transfer from
Python.

Its authority is established when:

1. a normative RDS, specification, schema, or versioned contract exists;
2. the implementation and data owners are named;
3. semantic and presentation boundaries are explicit;
4. deterministic conformance tests exist where applicable;
5. persistence and compatibility rules are documented where applicable;
6. no competing truth implementation remains;
7. an establishment record has status `established`;
8. this map records the owner.

## Migration and product routing

Use durable work categories rather than loading every completed slice:

- inherited parity implementation: `docs/architecture/parity_protocol.md` plus
  the selected subsystem contract, fixtures, and tests;
- parity evidence review: promotion gates and affected comparisons;
- inherited authority transfer: transfer protocol, evidence, fallback, and this
  map;
- new authority establishment: normative contract, owner, conformance evidence,
  establishment record, and this map;
- Godot product work: professional programme plus the owning product and visual
  authorities;
- topology migration: current topology authority, canonical contracts,
  Python-reference runtime, native transport/query surfaces, and tests.

## Forbidden shortcuts

- Reimplementing inherited semantic truth in GDScript or adapter glue.
- Rewriting Python behaviour for port convenience without an explicit product
  change.
- Duplicating topology, movement, collision, gravity, scoring, replay, or trace
  utilities.
- Treating parity evidence as authority transfer.
- Claiming universal Python authority over a feature that has no Python
  predecessor.
- Creating a Python mirror solely to satisfy an obsolete oracle requirement.
- Establishing new native authority without a normative contract and tests.
- Letting Godot presentation define inherited game-rule semantics.
