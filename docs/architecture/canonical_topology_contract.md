# Canonical Topology Contract

Status: active contract

Schema: `tet4d.topology_contract` version `1`

Semantic authority: Python

## Scope and ownership

The contract is the deterministic interchange form for the modern Python
`ExplorerTopologyProfile` plus the board dimensions against which its boundary
maps are bijective. Python remains the semantic oracle. Native C++ currently
provides a provisional cell-step parity slice; Godot receives the contract as a
data document and must not calculate topology truth in GDScript.

The forgiving explorer-profile settings store remains a user persistence
boundary. It is not the strict migration contract and malformed stored input
must not be presented as contract evidence.

This deliberately cross-layer contract uses the following scope matrix:

| Layer | Why it changes | Allowed surface | Verification |
| --- | --- | --- | --- |
| Python engine | owns normalization, validation, serialization, and identity | `engine/topology_explorer` | contract, resolver, endgame tests |
| Native core | proves the minimal existing cell-step transport slice | query DTO/result only | native tests and Python comparison |
| GDExtension/Godot | carries frame results and the versioned document shape | thin dictionary/DTO adapter | exact pinned headless tests |
| Docs/schema | makes representation, invariants, ownership, and deferrals durable | this authority and JSON Schema | docs/governance checks |

Gameplay loops, topology editors, replay schemas, visual presentation, and
authority-transfer records are outside this change.

## Version 1 representation

- `dimension`: integer `2`, `3`, or `4`;
- `board_dimensions`: one positive integer per axis, included in identity;
- axes: `x`, `y`, `z`, `w` up to the selected dimension;
- sides: `-` and `+`;
- each gluing: an unordered pair of distinct boundaries and a signed
  permutation of their tangent axes;
- canonical seam IDs: `seam_000`, `seam_001`, ... after normalization;
- identity: lowercase SHA-256 of compact, key-sorted UTF-8 canonical JSON.

Normalization excludes disabled editor rows, user labels, input order, and the
chosen direction of an undirected seam. Reversing a seam also inverts its
transform. It then sorts seams by boundaries and transform and assigns the
canonical IDs. Canonicalizing an already canonical document is idempotent.

## Invariants

1. Dimensions, axes, sides, board sizes, tangent ranks, permutations, and signs
   are valid.
2. No active boundary belongs to more than one gluing.
3. Tangent extents are compatible under the signed permutation.
4. Every gluing materializes forward and inverse directed crossings.
5. Each crossing maps to an in-bounds canonical board coordinate, and crossing
   back restores the source coordinate.
6. Coordinate-frame and piece-frame transport use a signed axis permutation
   plus translation. Reflection and cross-axis orientation are preserved.
7. Serialization round-trips without semantic drift; equivalent descriptions
   normalize to the same payload and identity.
8. Unsupported schemas, versions, or malformed contracts fail strictly.

Legacy asymmetric per-side edge rules are not representable as an inverse
paired seam and are intentionally outside version 1. Sandbox cellwise seam
traversal and Play gravity/drop/lock policy also remain distinct; this contract
does not collapse those move classes.

## Consumer and migration map

| Stage | Consumer | Contract use | Explicit deferral |
| --- | --- | --- | --- |
| 53A | Python, fixtures, native query, Godot DTO | normalize, validate, identify, and prove cell/frame parity | gameplay ownership |
| 53B | Native topology transport | consume generic contract and implement wider transport parity | authority transfer without evidence |
| 53C | Topology-aware Godot gameplay | route native transport into live movement under Python goldens | Godot-owned rules |
| 53D | Topology diagnostics | expose seam, neighbor, frame, and failure evidence | editor workflow |
| 53E | Godot Topology Lab | edit and launch the exact canonical contract | silent fallback or reconstruction |
| Later | gameplay/endgame/explosion launch | share the same contract identity and transport | unified integration in 53A |

Before any authority transfer, the named subsystem still needs versioned
goldens, strict Python/native comparison, a thin Godot adapter, fallback and
rollback evidence, and a completed transfer record under the authority-transfer
protocol.
