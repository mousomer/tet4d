# Explorer topology piece transport contract

Role: normative T1 piece-transport design
Status: design for review and native implementation; no runtime authority transfer
Version: `explorer-piece-transport/1` (prose contract, no generated schema)
Product authority: `docs/rds/RDS_EXPLORER_TOPOLOGIES.md`

## 1. Scope and normative relationships

**Normative:** This document answers the RDS §§5–7 whole-piece transport
question for one finite piece in a canonical v1 rectangular domain. It owns
the T1 design, subordinate to the RDS; it does not describe already implemented
native behavior. T2 implements and proves the 2D subset. Rank-independent
algebra here prepares T4, not permission to enable 3D/4D topology transport.

[Canonical topology v1](canonical_topology_contract.md) continues to own seam
interchange and identity. [Native transport](native_topology_transport.md)
owns the existing checked DTO boundary. The [Session 1 inventory](explorer_topology_t1_contract_inventory.md)
owns the implementation audit. The [authority map](authority_map.md) and
[transfer protocol](authority_transfer_protocol.md) remain unchanged. Ordinary
Play, historical Python results/goldens and Godot presentation are outside
this document's semantic replacement scope.

Labels used below: **Normative** states requirements; **Design decision**
selects semantics; **Implementation mapping** names reuse; **Deferred** names
unsupported extensions; **Unresolved** names outstanding work. Unqualified
rules, formulas and expected results in §§2–17 are normative for this design.
Session 3 dependencies in §18 do not supply missing movement rules.

| Layer | Design boundary | Evidence required before implementation acceptance |
| --- | --- | --- |
| Native query/core | Profile validation, indexed cells, proposals, inverse, atomic application and adjacency | Exact conformance and unchanged-cell parity |
| Checked native adapter | Strict values and versioned results | Invalid-type, field-path, stale/tampered candidate tests |
| Godot | Existing control mapping, requests, IDs in rendering and feedback | Isolation and adapter integration; human comprehension separately |
| Declarative data | Existing v1 profile meaning; separate piece state/version | Canonicalization, serialization and compatibility fixtures |
| Python | Historical cell/seam comparison and intentional divergences | Preserve legacy tests and goldens |

## 2. Mathematical definitions

Let `d` be the rank, `L=(L_0,...,L_(d-1))` the validated v1 extents and
`C_L = product_j {0,...,L_j-1}` the canonical cell-center sites. A location is
`(domain=0,c)` with `c in C_L`. Domain 0 is a constant in the piece contract,
not an added field in canonical topology v1. No other domain is accepted.
Let `B` be the exact canonical v1 profile payload, including `L`.

Let `G_d` be the signed permutation group acting on column vectors. All
arithmetic used to establish a result is exact integer/rational arithmetic;
overflow, unsupported rank/version and implementation resource exhaustion
must fail before mutation. Resource limits are admission failures, not evidence
that a structurally conformant profile or named space is mathematically invalid.

The semantic piece is

`P = (version, object_key, B, H, [(i,c_i,F_i)]_(i=0..n-1))`,

where `H=[(i,q_i)]` is immutable original polycube geometry and `F_i in G_d`.
`q_i` is a material coordinate; `F_i` maps material vectors into the current
canonical chart's axis basis at cell `i`. It is an active local orientation,
not the affine map from the original center to its current center. `c_i` and
`F_i` are independent state: deformation need not satisfy a global affine map.

A runtime envelope `S=(revision,P,initial_P,undo,trace)` is distinct from `P`.
`initial_P`, retained undo descriptors and diagnostic trace support lifecycle;
they are not hidden operands of translation/rotation. Proposal takes `P` and
an action only, plus the revision binding needed for later commit.

## 3. Canonical piece state

**Design decision:** Store original geometry once and current centers/frames
per ID. Do not store adjacency, a global orientation, a covering-space lift,
a pivot, or an operation log in `P`; those are derived or operation-specific.
Original geometry is necessary for the restricted rotation development (§9).
Translation alone would require only IDs, centers and frames.

| Field | Exact logical form and validation |
| --- | --- |
| `version` | Exact string `explorer-piece-transport/1` |
| `object_key` | Pair `(namespace,ordinal)`; namespace is 32 lowercase hexadecimal characters supplied by the session owner; ordinal is an integer in `[0,2^63-1]` |
| `B` | Canonical topology v1 payload, strictly validated; rank/board are taken from it, never conflicting copies |
| `H` | Nonempty original integer cells, distinct, face-connected by L1 distance 1; per-axis minimum 0; each coordinate in `[0,999999]`; sorted lexicographically, with IDs assigned `0..n-1` in that order |
| Current cells | Exactly one `(id,domain,c,frame)` for every ID in `H`; domain exactly integer 0; in-bounds `c`; distinct locations |
| `frame` | Two rank-length integer arrays `(permutation,signs)` as in §5; no translation field |

`n` cannot exceed board volume; never materialize the board to establish this.
These rest-geometry bounds use the existing maximum axis length; they do not
expand the v1 scalar envelope. Import validates rather than renormalizing or
reassigning an existing object's IDs. A malformed frame, missing/extra ID,
duplicate ID, invalid original geometry or duplicate source occupancy is
`invalid_piece_state`; a malformed profile is `invalid_profile`. No repair,
deduplication, coercion or partial admission occurs.

Canonical complete state orders fields as a logical record above, orders both
cell tables by ascending ID, and uses canonical `B`. For portable serialization,
encode the named records as compact UTF-8 JSON with lexicographically sorted
object keys, arrays in these orders, exact JSON integers and no insignificant
whitespace, as for v1. The logical keys are `version`, `object_key` (keys
`namespace`, `ordinal`), `profile`, `rest_cells` (rows `id`, `coordinate`), and
`cells` (rows `id`, `domain`, `coordinate`, `frame`; frame keys `permutation`,
`signs`). Unknown fields in this version fail. No machine schema is introduced
by this document; this specifies the future encoding, not a generated artifact.

Semantic equality is exact equality of every canonical field, including IDs,
original geometry, profile, instance identity and frames. It is independent of
incoming row order, labels discarded by v1 normalization, render order and
camera. It is not equality modulo translation, permutation of IDs, cell-shape
symmetry or frame symmetry. A digest may accelerate comparisons, but exact
canonical values are the commit authority; hash equality alone is insufficient.

## 4. Stable cell identity and adjacency semantics

The session owner supplies a namespace and monotonically allocates object
ordinals. Creation/replacement consumes a fresh ordinal; exhaustion rejects.
Loading a saved session preserves its namespace, objects and next ordinal;
importing a second colliding object key is rejected, never silently rekeyed.
An independently created session uses a distinct namespace. Namespace creation
is explicit external context, not randomness inside transport.

Cell identity is `(object_key,i)`. IDs are intrinsic to that instantiated
polycube's immutable `H`, not globally intrinsic to a catalog shape. Geometry
sorting may change presentation order but never identity. Retry restores
`initial_P`, including the same object/cell IDs. Serialization preserves them;
a fresh replacement with the same shape has a different object key.

| Relationship | Definition | Changes during transport? |
| --- | --- | --- |
| Piece membership | Same `object_key`, IDs in `H` | No |
| Original constituent adjacency | `||q_i-q_j||_1=1` | No; derive from `H` |
| Topology adjacency | A directed query `(i,axis,sign)` reaches canonical `c_j` under `B` | Yes |
| Visual adjacency | Rendered projections appear adjacent | Presentation only |

A neighbor query returns all `2d` labeled directed results in axis order,
negative then positive, including blocked edges, self-neighbors and distinct
directions with the same target. An occupied endpoint adds its stable cell ID;
a self-neighbor names the same ID, not another constituent. Do not deduplicate
edges into a simple graph. Original adjacency is not a requirement that current
cells remain topology-adjacent after a valid deformation.

## 5. Local-frame representation

For `(p,s)`, column `j` has entry `s_j` in row `p_j`:

`F e_j = s_j e_(p_j)`; equivalently `(F v)_(p_j)=s_j v_j`.

`p` is a permutation of `0..d-1`, `s_j in {-1,+1}`. This matches
`ExplorerTransportFrameTransform.apply_linear` and native
`TopologyFrameQueryTransform`: the array index is the **source axis**.
`I` has `p_j=j,s_j=+1`; `F^-1=F^T`, with inverse permutation and
`s_inv[p_j]=s_j`. Local orientation has no translation component.

A seam from source boundary `(a,epsilon)` to target `(b,eta)` has outward
source direction `epsilon e_a` and inward destination direction `-eta e_b`.
The seam's tangent signed permutation supplies the other columns. Define:

- `A`: the legacy coordinate-map linear extension, normal column `A e_a=-e_b`.
- `T`: transported physical-frame extension, normal column
  `T e_a=(-epsilon*eta)e_b`.
- `f(c)`: canonical destination, target normal coordinate `0` or `L_b-1`,
  tangent coordinates permuted, and a negative tangent coordinate mapped as
  `L_target-1-c_source`.

On the source boundary, both `A c+b_A` and `T c+b_T` equal `f(c)`, with
`b_A=f(c)-A c`, `b_T=f(c)-T c`. These offsets are constant over that boundary.
Agreement on boundary points does not determine the normal extension.
`T(epsilon e_a)=-eta e_b` fixes the correct physical normal transport.
Do not use `A` to update `F`, and do not add `b_T` to an orientation vector.

Interior step `a` has destination `c+a`, `T=I`, `b_T=a`; native's absent
interior frame DTO means this explicit identity, not undefined orientation.
Malformed/noninvertible tangent data is invalid transport, not an interior
identity. A missing seam is `unconnected_boundary`.

## 6. Composition, commands and holonomy

For material vector `v`, the old chart sees `F v`; after crossing the new
chart sees `T(F v)`. Therefore **`F'=T F`**, not `F T`. In array form,

`p_new[j]=p_T[p_F[j]]`, `s_new[j]=s_F[j]*s_T[p_F[j]]`.

Successive crossings give `T_k ... T_2 T_1 F`. Their affine extensions compose
as `(T_2 T_1, T_2 b_1+b_2)`; this expression describes the selected sequence,
not an arbitrary path-independent global chart. The reverse crossing has
`T_reverse=T^-1`, `b_reverse=-T^-1 b_T` on the paired boundary. Source and
destination chart bases are the fixed board axes, not camera axes.

For a 4×4 Möbius X− crossing:

```text
A = [-1  0]   T=M = [1  0]   b_A=b_T=(3,3) on x=0
    [ 0 -1]         [0 -1]
f(0,y)=(3,3-y), M(-e_x)=-e_x, M^2=I.
```

For Klein, X wrapping gives `T_x=I`, Y reversal gives
`T_y=K=diag(-1,+1)`: an X crossing followed by a Y crossing gives
`K I F=K F`; two Y crossings give `K K F=F`. E5 gives cell-by-cell coordinates.
Multiplication order matters even if these particular seam matrices commute.
With `Q=[[0,1],[-1,0]]` and old `F=Q`, `M Q=[[0,1],[1,0]]`, whereas
`Q M=[[0,-1],[-1,0]]`; the former alone sends each transported material basis
vector to its correct destination.

**Design decision:** A translation command is one canonical board vector
`a=delta e_axis`, `delta=±1`, used unchanged for every cell. It is not `F_i a`
and not an anchor-frame direction. Previous deformation affects current
centers and accumulated frames, but never secretly remaps the next key.
Rotations name an ordered canonical-axis plane and sign (§9).
Godot's existing `ControlFrameMapping.translation_command` / `rotation_command`
resolves camera-relative intent **before** this request. Canonical panel
buttons already supply semantic axes. Native receives no view, camera, slice,
projection or key-code data. Material/anchor-local input is outside version 1.

A closed coordinate path with changed `F_i` is a valid, distinct semantic
orientation (holonomy), even for an undecorated visually symmetric cell.
There is no quotient by frame symmetry. On a 4×3 Möbius strip, a singleton at
`(0,1),I` making four X+ steps returns to `(0,1),M`; this is not the original
state. Its four recorded inverses restore `I`.

## 7. Translation and result semantics

Given validated `P` and `a`, resolve every cell in ID order using the existing
single-cell rule: an in-bounds unit step is interior; otherwise inspect only
its exited face and apply the uniquely owned directed seam. Never recursively
step inward from the destination boundary or resolve other corner faces.

For each cell obtain `(c'_i,T_i,b_i)` and set `F'_i=T_i F_i`. Build the entire
candidate privately. Validate unchanged object/profile/rest data and ID set,
bounds, unique destination locations, and §8 inverse recovery before returning
a successful candidate. There is no gravity, locked-cell board or other-piece
occupancy in this single-piece Explorer contract. Such context requires a
separate extension, not a hidden dependency on a live Play session.

Classification uses correspondence and transported orientations, not an
unlabeled coordinate-set fit. Put `U_i=F'_i F_i^-1` and `t_i=c'_i-U_i c_i`.

| Condition, in order | Classification |
| --- | --- |
| Any validation/resolution/inverse failure | `blocked` |
| All `U_i=I` and all `t_i` equal | `plain_translation` (including zero displacement) |
| All `U_i=U` and all `t_i=t`, for one nonidentity signed permutation `U` | `rigid_transform` |
| Otherwise | `cellwise_deformation` |

This test needs no search over rigid motions and is invariant under row
reordering. Even one-cell orientation changes are visible to classification.
Different seam/interior outcomes are allowed; non-rigid appearance alone never
blocks. Coordinate coincidence of two **different IDs** always blocks as
`destination_collision`, even when each cell query succeeds.

Failure precedence is deterministic: checked decoding/version/rank errors;
profile structural validation; source-piece validation; action validation;
rotation development (if requested); per-cell resolution in ID order;
destination collisions (lexicographically first location, ascending IDs);
frame and inverse verification. Within a decoding record use the field order
in §§3/12, array index order, and report unknown keys lexicographically. Return
the first failing stage, with all per-cell diagnostics in ID order if retained.

| Stable reason | Meaning |
| --- | --- |
| `invalid_profile` / `invalid_piece_state` / `invalid_action` | Invalid semantic input; checked decoder also supplies its existing structured error |
| `unsupported_representation` | Unsupported version, domain, rank or action representation; T2 admits rank 2 only |
| `unconnected_boundary` | A selected translation exits a face without a seam |
| `ambiguous_destination` | More than one prescribed destination; conforming v1 cannot produce this, malformed boundary ownership fails profile validation first |
| `destination_collision` | At least two distinct IDs have the same proposed canonical location |
| `invalid_transport` | In-bounds/frame/transport contract broken after structural validation |
| `inverse_mismatch` | Reconstructed inverse fails exact cell, frame or endpoint recovery |
| `rotation_undefined` | §9 cannot establish its unique supported development/projection |
| `stale_candidate` / `candidate_mismatch` | §11 source binding changed / candidate differs from native recomputation |
| `resource_limit` | Checked arithmetic/resource/revision capacity exceeded; no partial result applied |

These names belong to this versioned piece contract; they do not rename the
existing low-level transport decoder's broad error codes. No failed result
contains an applicable destination or inverse descriptor. Tentative rows may
be diagnostics explicitly marked non-applicable.

## 8. Whole-piece inverse

A global opposite key is not the inverse definition. For a forward translation,
the inverse step for cell `i` is

`r_i=-T_i a`.

Interior gives `-a`. A crossing gives the outward direction of its **target**
face, hence the paired inverse seam. Re-query that step from `c'_i`, require
`c''_i=c_i`, `T_reverse=T_i^-1`, and `T_reverse F'_i=F_i`. Verify the whole
recovered state, not merely its unlabeled occupancy. This is a simultaneous
per-ID inverse operation, not a sequence of ordinary whole-piece keys.

**Design decision: snapshot-based, reconstructible descriptor.**

`D = (version="explorer-piece-inverse/1", source=P, forward_action=a)`.

For rotation, the action is the rotation action instead; §9 defines reversal.
The source includes the canonical profile and immutable original geometry.
Recompute its forward proposal to derive the target, all crossings, inverse
steps, pivot/development and frames. No separate crossing log is necessary.
This trades a bounded source snapshot for a simple, independently checkable
inverse; implementations may share immutable storage. It is not a claim of
minimum serialized byte count. Adding a second full target snapshot, reverse
step array or operation ID is unnecessary for semantics. Losing `D` loses the
ability to undo that operation; it does not disable subsequent translations.

Inverse execution:

1. Validate `D`, re-propose its forward action from its source, and require a
   successful forward result. This recomputation checks local reversibility
   directly; it must not recursively invoke the public inverse/proposal API.
2. Require current `P` to equal that computed target exactly. A different
   profile, instance, original geometry, center or frame yields `inverse_mismatch`.
3. Reconstruct every reverse result as above (or §9), compare to `D.source`,
   then create an ordinary revision-bound atomic candidate targeting that source.
4. Commit under §11. An inverse candidate's classification is computed by §7;
   its reversal plan is the original forward action from the recovered source
   (redo), not a recursively nested inverse descriptor.

Thus `Inverse(M_a(P),D_a)=P` exactly on the accepted endpoint. This is a
reversible **recorded operation**, not a claim that the unrecorded function
`P -> M_a(P)` is globally injective. Current frames alone need not determine
which step was taken. For a 1×1 torus, X+, X−, Y+, Y− all have the same endpoint
and frames; operation provenance cannot be recovered from that state.

No history stack is required for movement. An optional undo stack retains
these finite descriptors; undo pops only after successful commit. To reverse
several operations apply their descriptors in reverse order, re-proposing each
at the current revision. Intermediate incompatible state blocks; if exact
endpoint state is later restored, the descriptor may again be used in a new
proposal. This explicit value-based rule is different from reusing a stale
candidate. Descriptors serialize the source and action with exact values and
their own version; unknown versions fail without mutation.

Semantic state, revision and history have different equality rules:

| Observable | Forward then inverse |
| --- | --- |
| `P` | Exactly restored |
| Runtime revision | Increases once per accepted commit, never rewound |
| Undo stack | Optional forward push/inverse pop cancels the pair |
| Diagnostic trace | May retain ordered forward and inverse events; not part of `P` |

Trace entries use `(session namespace, committed revision)` as deterministic
identity, record action and stable correspondence, and may identify an inverse's
canceled descriptor. Timestamps/render state are not semantic operands. A
blocked proposal, inverse or commit appends nothing and changes no retained
trace/stack/revision. UI error feedback is outside that retained state.

### Distinct destinations do not imply a global inverse key

On legacy `sphere_2d`, 4×4, take `0:(0,1),I` and `1:(1,1),I`, original
horizontal domino `H=[(0,0),(1,0)]`, and X−. Cell 0 crosses X−→Y− with
`J=[[0,-1],[-1,0]]` to `(2,0),J`; cell 1 moves interior to `(0,1),I`.
Destinations are distinct; classification is `cellwise_deformation`.
`D=(source, X−)` reconstructs reverse steps `(0:Y−, 1:X+)`.

From `(2,0)`, Y− returns `(0,1)` and frame `J J=I`; X+ instead gives `(3,0)`.
For cell 1, X+ returns `(1,1)`; Y− instead gives `(0,0)`. Its other two
available steps also do not reach `(1,1)`. Thus no single global direction
recovers both. Every crossed seam is bijective, and this operation is reversible
with `D`; no new sphere certification follows from that fact.

## 9. Rotation and development rules

**Design decision:** Support exact quarter-turn rotations in a coherent
material development. Two deliberately bounded development modes suffice for
v1; neither searches arbitrary quotient paths nor uses a deformed bounding box
as an invented embedding. Rotation does not depend on previous move labels.

1. Require all `F_i=F`. Choose anchor `h=0` (lowest stable ID) and derive
   `u_i=c_h+F(q_i-q_h)`. This is the only proposed material development.
2. If **every** active seam is an opposite-face, same-axis, tangent-identity
   wrap, define `pi(u)` by Euclidean modulo on wrapped axes and identity on
   unwrapped axes. Otherwise define `pi` as identity on the in-bounds chart
   only. This latter rule permits local rotations on Möbius/Klein/legacy
   profiles; it never attempts a rotation across a reversed/cross-axis seam.
3. Require `pi(u_i)=c_i` for every ID. If not, or frames differ, return
   `rotation_undefined`. No alternative path, shortest lift or alternate anchor
   is tried. Original geometry removes small-board shortest-path ties.
4. Compute the existing Euclidean pivot on the developed cells for the selected
   ordered plane `(a,b)`. With axis minima/maxima, if both spans have the same
   parity use their bounding midpoint. Otherwise choose the cell nearest the
   centroid **in that plane**, ties broken by full-coordinate lexicographic
   order. Compare integer squared distances of `n*u_i-sum(u)` to avoid floating
   ties. Store midpoint coordinates doubled as exact integers. This specifies
   the native pivot rule with explicitly canonicalized input order, without
   per-ID array-order ties. The existing helper uses first-in-array on ties;
   the new contract supplies lexicographic input order at each new request.
   It does not redefine historical unsorted-call outputs.
5. The sign `+1` is the existing native positive quarter turn:
   `(z_a,z_b)->(z_b,-z_a)`; sign `-1` is its inverse. Put `Q` for this signed
   permutation. Compute `v_i=Q(u_i-p)+p` in the plane (other axes unchanged),
   `c'_i=pi(v_i)` and `F'_i=Q F`. Other components of `p` may be zero because `Q` fixes them.
   The pivot rule makes lattice output exact;
   do not round an arbitrary fractional result or add wall kicks.
6. An undefined projection, including an out-of-bounds unwrapped coordinate,
   blocks as `rotation_undefined`. Check occupancy, state and inverse as for
   translation, then classify by §7. Pure-wrap projection transports frame `I`.

`u` is a chosen material embedding, not an assertion that every topology path
has identical development. For pure wraps, different deck translations exist;
the anchor and `H,F` choose exactly one. No lift is stored in `P`. A previous
seam split may rotate if this equality holds; mixed frames or an incompatible
original shape cannot. Even uniform frames are not alone a coherence proof.

The inverse descriptor reconstructs the **same** `u,p,Q,v` from its source.
After exact target matching, lift each target to its recorded/derived `v_i`,
apply `Q^-1(v_i-p)+p=u_i`, project to `c_i`, and restore orientation with
`Q^-1 F'_i=F_i`. Reusing the forward pivot is mandatory; do not recompute a
new pivot from wrapped target coordinates or promise that an opposite rotation
key always undoes the action. Projection may be many-to-one on the whole cover,
but ID correspondence, endpoint equality and the source-derived lift make this
particular operation invertible. Candidate injection is checked independently.

**Implementation mapping:** Keep `rotate_blocks_nd` for existing callers;
extend its internal pivot/per-coordinate operation or expose shared helpers so
the new indexed path retains IDs. `rotate_blocks_nd_around_pivot` supplies the
same algebra with a fixed pivot; do not zip sorted outputs with incoming IDs.
The explicit pivot is transient inverse data derived from `D.source`, never a
new gameplay pivot policy. §13 E7 specifies supported and rejected cases.

## 10. Corners and degenerate boards

A unit axis step exits at most one selected face, even at a corner. Destination
on another boundary ends the operation; no extra crossing is inferred. This
holds for torus, Klein and adjacent reversed identifications. A non-diagonal
step requires no vertex-link/manifold certification. A diagonal or simultaneous
multi-axis action has no ordered path in v1 and is `invalid_action`.

Ordered successive commands may disagree when reversed in order. That is
allowed; do not sort them or assert flat/path-independent development. On a
4×4 Klein profile from `(3,3),I`, X+ then Y+ yields `(3,0),K`, whereas Y+ then
X+ yields `(1,0),K`. Both paths have their own reverse descriptors. Corners after
a frame change still use the selected **board** axis, not an implicit local one.

Positive extent 1 and 2 are structurally legal. On extent 1 a wrapped step may
return the same coordinate with a changed frame; all direction labels remain.
On a 1×1 Möbius profile X± is a self-neighbor with frame `M`; Y± blocks.
On a 1×1 torus every direction is a self-neighbor with `I`, and only one cell
can occupy the domain. On a 2×2 torus both X directions may reach the same
neighbor; queries retain both edges and their inverse information. A second
ID at an occupied site is invalid, never an alternate representative of the
first. Pure-wrap rotations use `H` rather than shortest-neighbor guesses.

Transport invalidity and continuous corner ambiguity are separate. Multiple
seams owning the same face fail `invalid_profile` before a move; tangent extent
mismatch fails likewise. Arbitrary corner-path rotation on twisted/cross-axis
profiles is outside §9 and blocks `rotation_undefined`. Multi-domain and
higher-codimension path lifting are deferred to T6 or a separate version.

## 11. Candidate/commit lifecycle and Retry

**Design decision:** Use immutable value requests/results and exact source
comparison, with one monotonic runtime revision. No opaque native state handle
or secret candidate token is necessary. Candidate DTOs are untrusted values;
validation cannot be replaced by a `validated=true` boolean.

The runtime revision is an integer in `[0,2^63-1]`, scoped to the session
namespace, never reused in that session. Every accepted state/profile change,
replacement, Retry, forward or inverse commit increments it, even if `P` is
unchanged (extent-1 self-step). Loading/rebinding an existing live session
invalidates outstanding candidates by advancing revision; a fresh session has
a new namespace. Exhaustion fails with `resource_limit`, never wraps.

A request contains `(version, source_revision, P, action)`. A success candidate
contains the complete request, exact destination `P'`, classification,
per-ID resolution witness and reversal plan: a derived inverse descriptor for
a forward action, or the original source-bound forward action for redo after
an inverse. A blocked result
contains reason/error and diagnostics only. No mutable references are exposed.

| Stage | Validation | Mutation |
| --- | --- | --- |
| Propose | Strict decode; canonical profile/state/action; resolve all cells; bounds, IDs, injection, frame/inverse and classification | None, including trace |
| Apply | Require namespace/revision and exact source `P` match current; re-run native proposal; compare complete candidate to recomputed result | None until every check succeeds |
| Commit | Verify revision capacity; prepare complete new envelope, undo/trace updates and result; publish it as one replacement | One atomic swap of owned state |
| Reject | Stale binding gives `stale_candidate`; tampered result/witness gives `candidate_mismatch` | Exact no-op on the entire envelope |

Application compares at one serialized mutation boundary (single owner or
lock); it cannot check revision, release ownership, and commit after another
writer. Recomputed profile normalization eliminates user seam-label/order
influence. Compare canonical witnesses, not presentation strings. If an adapter
returns an incomplete DTO or a trace allocation fails, publish nothing.
Proposals do not consume revisions, allocate object IDs or append history.

An inverse proposal uses the current revision plus `D` and follows §8. A
candidate generated before an intermediate move is stale even if a later
inverse returns identical `P` (ABA). A descriptor can generate a **new** inverse
proposal when its endpoint matches. Cosmetic profile metadata and camera changes
are not semantic mutations; different canonical profile content or rebinding
must invalidate candidates. A profile edit reverted later still advances revision.

Retry atomically restores the saved complete `initial_P`, preserves its IDs,
restores the initial undo/trace baseline and advances revision. It never restores
an old revision. If profile selection changed, the session must first establish
an explicit compatible new baseline or reject Retry with `invalid_piece_state`;
it must not silently switch profile or repair frames. Reset View touches no
native envelope. Replacing a piece creates a fresh object key and baseline.

## 12. Native request/result and checked adapter boundary

**Implementation mapping:** Extend the existing query/transport family with
piece DTOs and pure proposal/application operations; the following are logical
contracts, not a requirement for a second API namespace or solver.

| Existing owner/symbol | Extension or reuse |
| --- | --- |
| `native/tet4d_core/include/tet4d_core/query.hpp`: `TopologyQueryProfile`, `MoveStepQuery`, `TopologyCellStepQueryResult`, `TopologyFrameQueryTransform` | Reuse validated profile, unit actions, frame and directed-step outputs; add indexed piece/state/candidate values alongside them |
| `native/tet4d_core/src/core/query.cpp`: `resolve_topology_cell_step_query`, private `inverse_transform`, `frame_transform_for_crossing`, `topology_neighbor_query` | Same per-cell/seam math; expose shared directed-seam inspection as needed; add accumulated frames, per-ID validation and inverse orchestration |
| `piece_pose_legal_query` in that file | Reuse canonical bounds/duplicate occupancy checks after indexed candidate construction; never substitute it for identity or inverse verification |
| `native/tet4d_core/src/core/geometry.cpp`: `rotate_blocks_nd`, `rotate_blocks_nd_around_pivot`, `translate_blocks_nd`, `canonicalize_blocks_nd`, `normalize_blocks_nd` | Reuse exact geometry/pivot internals; sorting/normalization are coordinate utilities, never ID allocators after creation |
| `native/tet4d_core/src/core/topology_transport.cpp`: `decode_topology_transport_profile`, `decode_topology_transport_query`, `topology_query_profile_from_transport`, `resolve_topology_transport_query` | Extend strict value decoding for new versioned piece requests/results; canonicalize by unchanged v1 rules before identity/binding |
| `native/tet4d_core/src/godot/topology_transport_variant.cpp`: `topology_transport_value_from_variant` | Classify Variant types before extraction; no permissive `int()` reconstruction |
| `native/tet4d_core/src/godot/tet4d_core_api.cpp`: `topology_transport_profile`, `topology_transport_resolve_cell_step`, `topology_query_result_to_dictionary` | Thin checked entry/result conversion for piece operations, no second validity decision |
| `godot/Tet4D.Godot/scripts/presentation/practice_explorer.gd`: `command`, `retry`, `replace_piece`, `snapshot`, `neighbors`; `scripts/native/tet4d_core_bridge.gd` | Route detached Explorer state/action to native; display result and stable IDs; retain camera and live-Play isolation |

Logical action encoding is a tagged record: `translate(axis,delta)` or
`rotate(axis_a,axis_b,quarter_turn)`; axes are exact integers in range,
`axis_a != axis_b`, signs exactly ±1. No batch turns, diagonal vectors or
implicit local-axis mode. Inverse is a separate tagged request carrying `D`.
Action JSON uses `kind` equal to `translate` or `rotate` and the exact keys
shown in parentheses above; inverse request `kind=inverse` carries `descriptor`.
Field order for decoding: envelope version, revision, piece fields (§3), action
tag then action parameters in this order. Inverse decodes its version, source,
then forward action. References are owned immutable values, not borrowed pointers
into Godot arrays; nullable fields are allowed only where explicitly blocked.

A per-cell witness names ID, source/target, selected step or rotation development,
canonical directed seam boundaries (or interior), `T`, and `F'`. Translation
witnesses include `r_i`; rotation witnesses include `u_i,v_i`, doubled pivot and
`Q`. Canonical seam IDs come from normalized `B`. Witness rows are sorted by ID;
checks represented are source validity, conservation, bounds, injection and exact
inverse. These are deterministic evidence fields, not client-granted authority.

Conceptual `validate_profile` uses strict transport validation and unchanged
canonical v1 normalization/identity. `query_boundary_pair` returns its directed
pair and tangent correspondence or none. `query_neighbor` and
`query_seam_preview` reuse the same resolver and distinguish `A` from `T`;
previewing one cell does not promise whole-piece validity.
`query_topology_adjacency` joins labeled native neighbor targets to the piece's
injective occupancy index (§4), without a second graph solver or full-board scan.
`propose_piece_action` and `apply_validated_action` follow §§7–11. Native C++
canonicalization must match Python v1 payload/SHA fixtures; the current transport
DTO is not itself canonical JSON and may not be hashed as if it were.

Reuse the existing validation structure `code,path,expected,actual,message`.
Booleans, floats, numeric strings, invalid enum values, duplicate IDs, wrong
ranks, repeated permutation entries and nonunit signs fail before construction.
The new piece import must not copy the legacy snapshot adapter's float-to-int
conversion. Unknown fields/versions fail; arrays cannot hide missing cells.
Godot can render/explain native outcomes but cannot independently veto, repair,
reclassify or approve transport. Missing provider means unavailable/atomic
failure, never fallback to conflicting historical Python piece behavior.

## 13. Exact worked examples

Notation: `i:c/F` gives every current center and frame; domain is always 0.
`I`, `M=diag(1,-1)`, `K=diag(-1,1)`, `J=[[0,-1],[-1,0]]`,
`Q=[[0,1],[-1,0]]`. All examples use namespace `00000000000000000000000000000001`
and ordinal equal to the example number (subexamples use separate sessions).
`H` entries are in ID order. Profile definitions are the existing presets in
`src/tet4d/engine/topology_explorer/presets.py`; E3 explicitly uses only Y wrap.
Every displayed output retains version, object key, `B`, `H` and IDs unchanged.
Thus the header plus rows denotes complete `P`, not just a coordinate set.
`D(P,a)` is exactly §8's source-plus-action descriptor; listed reverse steps
are derived evidence, not a different descriptor format. No blocked example
has a committed candidate or inverse. Revisions advance only on application.

### E1 — bounded wall rejection, and cylinder's bounded axis

Bounded 4×4; `H=[(0,0),(1,0)]`; source `0:(0,1)/I, 1:(1,1)/I`; X−.
Cell 0 hits unconnected X−; cell 1 tentatively reaches `(0,1)/I`.
Result `blocked/unconnected_boundary`; complete retained state equals source,
including revision/trace/undo. No inverse exists for the rejected operation.

Cylinder 4×4 companion fixture: same `H`, source
`0:(1,0)/I,1:(2,0)/I`, Y−; both hit bounded Y−, same rejection. For its positive
wrap fixture use `H=[(0,0),(0,1)]`, `0:(0,1)/I,1:(0,2)/I`, X−:
outputs `0:(3,1)/I,1:(3,2)/I`, both `T=I,b=(3,0)`;
`plain_translation`, `D(P,X−)`, both inverse X+ restore the source exactly.

### E2 — simple torus wrap

Torus 4×4; `H=[(0,0),(0,1)]`; `0:(0,1)/I,1:(0,2)/I`; X−.
Both cross X−→X+, `T=I,b=(3,0)`.
Complete proposed rows `0:(3,1)/I,1:(3,2)/I`.
`plain_translation`, no blocked reason; `D(P,X−)` derives X+ for both.
Reverse crossing gives `(0,1), (0,2)` and `I,I`, exact `P`.

### E3 — torus chart split

Y-wrap-only 4×4, matching
`test_torus_chart_split_piece_step_stays_rigidly_coherent` in
`tests/unit/engine/test_explorer_transport_resolver.py`;
`H=[(0,0),(0,1)]`; `0:(0,0)/I,1:(0,1)/I`; Y−.
Cell 0 crosses to `(0,3)`, `T=I,b=(0,3)`;
cell 1 is interior to `(0,0)`, `T=I,b=(0,-1)`.
Complete output `0:(0,3)/I,1:(0,0)/I`; `cellwise_deformation`, no block.
`D(P,Y−)` derives Y+ for both: 0 crosses back and 1 moves interior,
recovering exact `P`. The same calculation holds on the full torus; original
adjacency and seam adjacency survive despite rectangular visual separation.

### E4 — Möbius reversal

Möbius 4×4; `H=[(0,0),(0,1)]`; `0:(0,1)/I,1:(0,2)/I`; X−.
Both cross X−→X+, `A=-I`, `T=M`, `b_A=b_T=(3,3)`.
Output `0:(3,2)/M,1:(3,1)/M`; `rigid_transform`, no block.
`D(P,X−)` derives X+ for both; the reverse seam uses `M` and
`b_T=(-3,3)`, giving `0:(0,1)/(MM)=I,1:(0,2)/I`.
Using `A` for local frames would incorrectly flip X as well.

### E5 — Klein sequential crossings

Klein 4×4; `H=[(0,0),(0,1)]`; source `0:(3,2)/I,1:(3,3)/I`.
(The ID order follows the original geometry, not the next crossing order.)

| Operation | Cell 0 resolution | Cell 1 resolution | Complete output / classification |
| --- | --- | --- | --- |
| X+ | X+→X−, `I, b=(-3,0)` | Same | `0:(0,2)/I,1:(0,3)/I`; `plain_translation` |
| Y+ | Interior, `I,b=(0,1)` | Y+→Y−, `K,b=(3,-3)` | `0:(0,3)/I,1:(3,0)/K`; `cellwise_deformation` |

No blocked reasons. `D1=(P0,X+)`, `D2=(P1,Y+)`.
D2 derives Y− for both: 0 interior→`(0,2)/I`, 1 reverse seam→`(0,3)/(KK)=I`.
D1 then derives X− for both, restoring `(3,2)/I,(3,3)/I` and complete `P0`.
Cell 1's accumulated frame is `K I I=K`; reversing the sequence gives
`I K K I=I`. A subsequent Y-reversing crossing multiplies on the left again.

### E6 — invalid sphere-like collapse

Legacy sphere-like 4×4; `H=[(0,0),(1,0)]` (source geometry need not be a rigid image
of `H`; no reachability claim is made); source `0:(0,3)/I,1:(1,0)/I`; X−.
Cell 0 crosses X−→Y−: `J,b=(3,0)`, tentative `(0,0)/J`.
Cell 1 is interior: `I,b=(-1,0)`, tentative `(0,0)/I`.
Two IDs occupy the same domain/site. Result `blocked/destination_collision`;
there is no complete applicable proposed state, and the complete retained state
is source. No frame, ID, trace, undo or revision change. Historical Python
`cellwise_deformation` remains a legacy comparison, explicitly superseded here.
The connected-source counterexample in §8 is the successful companion case.

### E7 — supported and undefined rotations

Each uses plane `(x,y)`, frames shown below, and `D(P,rotation)` on success.

| Case, profile/board and `H` | Source and action | Development, pivot and per-ID resolution | Complete output and classification |
| --- | --- | --- | --- |
| Ordinary bounded 4×4; `H=[(0,0),(0,1),(1,0)]` | `0:(1,1)/I,1:(1,2)/I,2:(2,1)/I`; +1 | `u=c`; midpoint `p=(1.5,1.5)`; `Q` sends IDs to `(1,2),(2,2),(1,1)` | `0:(1,2)/Q,1:(2,2)/Q,2:(1,1)/Q`; `rigid_transform` |
| Torus seam split 4×4; `H=[(0,0),(0,1)]` | `0:(0,3)/I,1:(0,0)/I`; +1 | `u_0=(0,3),u_1=(0,4)`; nearest-centroid tie gives `p=(0,3)`; `v_0=(0,3),v_1=(1,3)` | `0:(0,3)/Q,1:(1,3)/Q`; `cellwise_deformation` in canonical chart |
| Möbius after E4; same board/H | `0:(3,2)/M,1:(3,1)/M`; −1 | `u=c`; tie gives `p=(3,1)`; `Q^-1` gives `(2,1),(3,1)`; both stay in chart | `0:(2,1)/(Q^-1 M),1:(3,1)/(Q^-1 M)` with `Q^-1 M=[[0,1],[1,0]]`; `rigid_transform` |
| Mixed Möbius 4×4; `H=[(0,0),(1,0)]` | `0:(3,2)/M,1:(0,1)/I`; +1 | Source comes from `(0,1)/I,(1,1)/I` moving X−; unequal frames fail before choosing a pivot | `blocked/rotation_undefined`; complete source unchanged; no inverse |

For the three successes, inverse uses the source-derived `v,p` and the
opposite `Q`, **not** a new wrapped-bounds pivot. Bounded recovery is
`(1,1)/I,(1,2)/I,(2,1)/I`; torus recovery projects `(0,3),(0,4)` to
`(0,3)/I,(0,0)/I`; Möbius recovery is `(3,2)/M,(3,1)/M`. All exact `P` fields
are restored. On that Möbius source, +1 instead needs `(4,1)` and blocks
`rotation_undefined`; this limits the command, not the topology's availability.

### E8 — stale and mismatched candidates

Torus 4×4; `H=[(0,0)]`; source `0:(0,0)/I`, revision 10; propose X+.
Candidate is `0:(1,0)/I`, `plain_translation`, inverse `D(P,X+)` (reverse X−).
Before apply, commit Y+, giving actual `0:(0,1)/I`, revision 11. Applying the
old candidate yields `blocked/stale_candidate`, retaining exactly that actual
state/revision/trace. No new inverse/trace event is emitted for the rejection.
Undoing Y+ restores `(0,0)/I` at revision 12; the candidate is still stale.
Changing canonical profile content or rebinding its revision has the same
failure even if coordinates match. Altering a fresh candidate's frame instead
produces `candidate_mismatch` after native recomputation.

### E9 — extent-one wrap

Torus 1×3; `H=[(0,0),(0,1)]`; `0:(0,0)/I,1:(0,1)/I`; X+.
Both cross X+→X− to their own source center; `T=I,b=(0,0)`.
Complete output equals source; `plain_translation` with zero displacement.
`D(P,X+)` derives X− for each, recovering exactly the same `P`. A successful
commit still increments revision; an inverse commit increments it again.
X± neighbor edges target self; they do not merge IDs 0 and 1. Y+ from cell 0
reaches cell 1. On a 1×1 board only a singleton is admissible; two IDs at
`(0,0)` fail source validation, not successful transport.

### E10 — repeated forward/inverse mixed-seam sequence

Klein 4×4, same object/H/source as E5. Apply X+, Y+, X−, Y+ in order:

| State | Cell 0 | Cell 1 | Incoming per-cell `T`, reason and classification |
| --- | --- | --- | --- |
| P0 | `(3,2)/I` | `(3,3)/I` | Initial |
| P1 | `(0,2)/I` | `(0,3)/I` | `I,I`; none; `plain_translation` |
| P2 | `(0,3)/I` | `(3,0)/K` | `I,K`; none; `cellwise_deformation` |
| P3 | `(3,3)/I` | `(2,0)/K` | `I,I`; none; `cellwise_deformation` (wrap/interior offsets differ) |
| P4 | `(0,0)/K` | `(2,1)/K` | `K,I`; none; `cellwise_deformation` |

Descriptors are `D1=(P0,X+)`, `D2=(P1,Y+)`, `D3=(P2,X−)`, `D4=(P3,Y+)`.
D4: Y− for both, cell 0 crosses with `K`, cell 1 is interior → P3.
D3: X+ for both, cell 0 crosses with `I`, cell 1 is interior → P2.
D2: Y− for both, cell 0 interior, cell 1 crosses with `K` → P1.
D1: X− for both, both cross with `I` → P0. All original geometry, IDs and
frames are exact. Revision is `r+8`, stack cancels to its baseline, and diagnostic
trace may contain eight committed events. A blocked intervening action would
change none of these and would not prevent the next valid inverse.

## 14. Invariants, proofs and adversarial review obligations

For translation, unique source face ownership supplies functionality. Signed
permutations are invertible; paired tangent maps plus compatible extents recover
coordinates, while the physical normal rule makes `T_reverse=T^-1`. The
reverse command is the target outward direction. Per-ID inversion therefore
recovers centers and frames; the whole-piece collision check separately supplies
injective occupancy. Conservation follows from building one row for each and
only each original ID. None of these facts follows merely from a set of centers.

For supported rotation, the explicit material development, deterministic pivot
and signed `Q` give one candidate. The descriptor identifies its lift even when
projection loses information; `Q^-1 Q=I` restores developed centers and frames.
Checking projected occupancy and exact endpoint matching completes the proof
for the accepted operation. Transaction serialization and final swap supply
atomicity, independently of the mathematical proofs.

| Adversarial challenge | Required result / containment |
| --- | --- |
| Distinct destinations but no single reverse key | §8 connected sphere-like domino; use per-ID `-T_i a`, never one global key |
| Recover coordinates but not frames | §6 center-row Möbius holonomy; complete-state comparison fails until frames recover |
| Individually legal but invalid whole piece | E6 blocks collision before any commit |
| Destination alone loses operation information | 1×1 torus has four indistinguishable coordinate/frame outcomes; retain `D` |
| Development depends on path | §9 uses only `H`, uniform `F`, fixed anchor and specified projection; other cases block |
| Corner order disagrees | §10 Klein order witness; preserve command sequence, no simultaneous diagonal resolution |
| Degenerate extents confuse identity | E9 plus 1×1 Möbius frame change; keep IDs and labeled self-edges |
| Stale state/profile/ABA candidate | E8 exact source plus monotonic revision; no reuse after Retry |
| Blocked action changes trace | Propose is pure, reject is whole-envelope no-op; include failure after trace-preparation allocation |
| Equivalent profiles yield different outcomes | Normalize `B`, canonical seam IDs/directed boundaries; exclude authored labels/order, compare normalized witnesses |
| Cell order changes classification/pivot | ID-ordered construction; `U_i,t_i` equality; lexicographic coordinate pivot tie-break |
| Godot view changes semantic result | No presentation fields in request; identical semantic request must compare exactly |
| Tampered inverse snapshot or witness | Recompute forward, exact endpoint match, then inverse; malformed values reject |
| Rotation maps two lifts onto one site | Unique projected occupancy required despite invertible `Q` |

This is an adversarial design review, not evidence that unimplemented native
piece conformance tests have passed. The required executable cases follow.

## 15. Explicitly unsupported operations

- Material-local/per-cell-local movement keys, diagonal steps, multi-step
  atomic macros, arbitrary continuous rotations or fractional-angle rotations.
- Rotation with unequal cell frames, failure of the original-geometry
  development equality, or crossing reversed/cross-axis seams during rotation.
  Translation remains available where its own candidate passes.
- Arbitrary cover/path search, alternate anchor selection, path-independent
  rotation on twisted corners, and inferred universal manifold charts.
- Multiple domains, holes/subfaces, one-sided asymmetric seams or changing v1
  transport to accommodate them. No T6 machinery is hidden here.
- Concurrent pieces, obstacles/locked-cell gameplay, gravity/drop/lock, wall
  kicks, score, queue/RNG or ordinary Play/replay changes.
- T2 activation or authority transfer of rank 3/4; rank-independent formulas
  alone are insufficient evidence.
- Silent coordinate-only import into persistent framed state, inverse without
  its source descriptor, or accepting a candidate as proof because it decodes.

## 16. Compatibility, certification and versioning

Canonical topology v1 retains its exact schema, ID/digest normalization, scalar
limits, seam meanings and historical readers. Piece state, inverse and candidate
requests/results are separately versioned. Changed action/frame/inverse meaning
requires a new piece-contract version, never reinterpretation of existing saves.
Legacy coordinate-only traces remain legacy; do not synthesize lost frames or
stable identities and claim exact old-state recovery. An explicit new object
creation may use old geometry as input with fresh IDs and identity frames.

Keep five independent judgments: (1) structural transport validity;
(2) this movement's validity; (3) continuous quotient certification;
(4) ordinary rigid Play admissibility; (5) catalog availability. No mathematical
label, `unsafe` flag, orientability guess or renderer can change §7's result.
A structurally valid profile can have rejected moves and unverified mathematics.

The five T2 constructions remain bounded rectangle, cylinder, torus, Möbius
strip and Klein bottle. Existing `sphere_2d` retains adjacent reversed pairs
X−↔Y− and X+↔Y+. Its continuous polygon corner identifications have one vertex
class and `V-E+F=1-2+1=0`; this is not a sphere certification and not a reason
to change transport. Session 3 must verify vertex links and orientability before
any closed-surface classification. The projective-like candidate requires its
own proof; neither preset name nor discrete inverse proves RP². Construction
metadata/evidence is separate from executable `B` and does not enter action
semantics. No legacy preset identity or golden changes here.

Historical duplicate-target success is an explicitly superseded Explorer
expectation (E6); historical Python retains compatibility coverage. Existing
cell coordinate/frame maps are reusable parity evidence. New accumulated state,
inverse, collision rejection and rotation scope require RDS-conformance tests,
not a new Python engine to manufacture an oracle. Before T2 transfer, the
bounded MVP remains the safe fallback. After promotion, unavailable native
transport fails closed; rollback disables the feature and reverts its scoped
map/record together, without changing legacy meanings.

## 17. Conformance fixture requirements

**Normative future evidence:** Convert §§8/13 into manually reviewed, versioned
fixtures only after semantic review. Suggested future owner
`tests/fixtures/explorer_piece_transport_v1.json` is a **proposed new file**, not
an existing artifact. Do not generate it from Python `resolve_piece_step`.
Extend `native/tet4d_core/tests/query_core_tests.cpp` and
`topology_transport_tests.cpp`, the existing checked Godot boundary tests, and
`tests/unit/migration/test_topology_transport_parity.py`'s explicit comparison
modes. No piece harness or fixture is claimed to exist in this session.

Each fixture records canonical profile/board, version/object/H, every ID/center/
frame, revision, selected action, exact per-cell witness, complete target or
stable blocked reason, descriptor source/action, inverse target, retained-state
assertions, comparison disposition, and contract example/section. Never compare
only sorted occupied coordinates. Add roundtrip serialization of `P,D`, strict
malformed inputs, unknown versions and source-rest tampering.

| Family | Required deterministic cases |
| --- | --- |
| Bounded | E1/E7; every wall and partial-cell failure; undeformed native pivot parity |
| Cylinder | E1 companion wrap and bounded-Y; both X directions, both bounded directions |
| Torus | E2/E3/E7/E9; all directions, corners, extent 1/2, repeated inverse and seam-adjacent distinct occupancy |
| Möbius | E4/E7; both seam directions, mixed interior/seam, center-row holonomy, 1×1 frame self-step |
| Klein | E5/E10; both seam directions, corner order witness, uniform and mixed frames |
| Legacy optional profiles | E6 and §8; projective both reversed pairs; separate metadata/certification assertions |
| Lifecycle | E8; Retry, replacement, profile rebind, ABA, tampered candidate, inverse after changed frame, revision exhaustion and allocation failure |
| Determinism | Reordered cell arrays and equivalent seam order/direction/labels; repeat same input; camera/slice changes leave native result unchanged |
| Strict boundary | Boolean/float/string integers, bad dimension/domain/ID/permutation/sign, duplicate source occupancy, malformed descriptor, unsupported rank |

For each core seam, enumerate all boundary coordinates on small boards
(1×1, 1×2, 2×1, 2×2, 4×4) and both directions; verify reverse center and frame,
then combine cells to test injection/atomicity. This is finite conformance,
not a universal mathematical manifold classifier. Enumerate signed-frame inputs
in 2D to catch multiplication order, including noncommuting examples in §6.
Parity outputs for unchanged low-level behavior remain distinct from new piece
conformance. A passing historical test cannot certify the unimplemented engine.

## 18. Open issues and Session 3 handoff

**Unresolved outside this movement scope:** Catalog schema and
`space_class_id -> construction_id -> profile_id` relationships, aliases,
availability/certification promotion and the independent continuous quotient
fixture format remain Session 3 work. No such choice is needed to execute an
accepted request: it carries normalized `B` directly. Session 3 must preserve
that distinction and the canonical v1 identity algorithm.

Session 3 inputs/outputs:

1. Bind the five core recipes and historical aliases to exact normalized
   transport profiles/boards, independently of display labels and certification.
2. Define proof fixtures for edges, vertices, local links, orientation, boundary
   components and Euler characteristic. Recheck sphere-like `chi=0` without
   altering its pairings or asserting Klein certification before all checks.
   Investigate projective-like construction without forcing its label's `chi=1`.
3. Carry §§13/17's exact five-core transport and negative examples into the T1
   conformance package; add certification cases separately. Record intentional
   Python divergences and compatibility, not rewritten historical goldens.
4. Complete the inventory §10 bounded 2D transfer preparation using this native
   mapping, exact exclusions, comparison modes and rollback. T2 still needs
   implemented native/adapter conformance, Godot integration and human review
   before any terminal transfer record or map promotion. T4/T6 remain separate.

There is no unresolved choice inside the supported movement/rotation rules:
accepted operations have one candidate and a defined recorded inverse; all
other operations reject deterministically. Semantic review, Session 3's broader
T1 deliverables, T2 implementation and acceptance are still required. Stop at
this design boundary; this document does not authorize T2 implementation.
