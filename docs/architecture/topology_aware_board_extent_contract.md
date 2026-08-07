# Topology-Aware Board-Extent Contract

Status: Stage 54B-1 implementation authority

## Purpose and source of truth

`contracts/board_extent_contract_v1.json` is the versioned declarative source
of truth for **professional live-board setup admissibility**. Its generator,
`tools/codegen/generate_board_extent_contract.py`, validates the source and
creates the checked-in Python, C++, Godot, and JSON-schema bindings. The
contract is owned as data by that JSON document and as deterministic runtime
behaviour by `native/tet4d_core/board_extent_contract`.

This is a new, narrow subsystem. It does not transfer topology semantics or
the existing gameplay loop from Python.

## Contract envelope

| Mode | Axis order | Inclusive ranges | Canonical default | Native cells |
| --- | --- | --- | --- | ---: |
| `live_2d` | X, Y | X 4–16; Y 6–30 | 6 × 6 | 480 |
| `live_3d` | X, Y, Z | X 4–10; Y 6–24; Z 2–10 | 6 × 10 × 6 | 2,400 |
| `live_4d` | X, Y, Z, W | X 4–12; Y 6–24; Z 2–8; W 1–12 | 5 × 10 × 4 × 4 | 27,648 |

The Stage 49 4D W envelope remains 1–12. Axis bounds are intentionally
separate from the selected piece set: a W=1 board is admissible for a 4D set
only when every piece in that set has a canonical spawn. For example,
`embedded_3d` and `embedded_2d` fit W=1, while `standard_4d_5` is rejected
there with `spawn_not_viable`. The envelope applies only to Godot professional
live play. It does not
narrow general Python `GameConfig`, `GameConfigND`, Explorer, tutorial, or
migration dimensions.

## Validation request and result

The strict native request contains `contract_version`, `mode`, `board_shape`,
`piece_set_id`, and the Stage 53B `topology_profile`. A successful result
contains `ok: true`, a normalized `validated_setup`, and an empty `errors`
array. A rejected result contains `ok: false`, no validated setup, and ordered
errors with stable `code`, `path`, `expected`, `actual`, and `message` fields.

The supported error vocabulary is:

- `unsupported_contract_version`, `invalid_field_type`, `unsupported_mode`,
  `rank_mismatch`;
- `axis_below_minimum`, `axis_above_maximum`, `native_volume_overflow`,
  `native_volume_limit_exceeded`;
- `topology_dimensions_mismatch`, `unsupported_topology_rule`;
- `unsupported_piece_set`, `piece_dimension_mismatch`, `spawn_not_viable`.

Codes and paths are programmatic identity. Messages are diagnostic text and may
improve without changing the contract.

## Topology, pieces, and spawning

Topology is explicit: its rank and dimensions must exactly match the requested
board. Phase I accepts only the bounded representation, a strict topology
profile with no seams. Strip, Möbius, and seam-safety rules are intentionally
unsupported now and reject with `unsupported_topology_rule`; Stage 55A adds
them through this same request boundary.

The native `plain_piece_catalog` is shared by validation and live sessions.
Supported sets are `classic` (2D), `native_3d`/`embedded_2d` (3D), and
`standard_4d_5`/`embedded_3d`/`embedded_2d` (4D). Every production piece is
checked with the same pure canonical centring and entry logic used by gameplay
before a session is built. This validation has no RNG, score, bag, or live
state mutation. Thus 4D admission is tuple-based: bounds admit the board
shape, then the selected production piece set decides whether that shape is
actually playable.

Native volume multiplication uses a checked division-before-multiplication
guard, distinct from topology scalar validity and the product cell budget.

## Safe failure and consumers

The failure policy is invariant:

```text
invalid setup -> structured error -> no session construction -> no setup mutation
```

There is no fallback to standard dimensions. Parameterized native construction
is available only through `create_validated`, which returns an explicit failure
for an invalid request; the generated no-argument/default-mode constructors
remain canonical-only. Godot uses the checked configure methods.

Godot consumes generated defaults and emits an explicit bounded profile, then
calls `validate_live_board_setup` and `live_*_configure_checked`. GDScript owns
the setup interaction and presets but not professional extent, piece, spawn,
or topology admissibility. Existing persistence schemas 1 and 2 remain source
adapters: recovery produces a canonical candidate which is validated before
native construction. This stage adds no arbitrary-shape persistence format and
the validator never performs semantic repair.

## Scope and extension point

Excluded behaviour includes topology seam semantics, movement, rotation,
collision, gravity, locking, clearing, scoring, randomization, replay, trace,
hashing, custom-axis UI, and renderer changes. Existing valid gameplay hashes
and trace schemas remain unchanged.

Stage 55A may add topology-specific board rules by extending the selected
topology rule branch after rank and dimension agreement; it must not replace
this contract or reintroduce consumer-owned minima.
