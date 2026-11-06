# Explorer topology catalog and certification contract

Role: normative T1 catalog, evidence and fixture design
Version: `explorer-topology-catalog/1`
Status: technical design; independent review and T1 reconciliation pending
Product owner: `docs/rds/RDS_EXPLORER_TOPOLOGIES.md`

## 1. Ownership and limits

This contract completes the catalog/evidence side of T1. The
[Session 2 piece contract](explorer_topology_piece_transport_contract.md) owns
movement, frames, inverses, rotation and transactions; this document does not
replace those rules. [Canonical v1](canonical_topology_contract.md) owns discrete
normalization. The [inventory](explorer_topology_t1_contract_inventory.md) owns
the code audit. [T2 preparation](explorer_topology_t2_transfer_preparation.md)
names the future native boundary; the authority map and active records do not
change. Normative means required design, not implemented runtime behavior.

The sole proposed catalog source is
`tests/fixtures/explorer_topology/catalog_v1.json`. Its seven records are
representative contract data, not an activated runtime catalog. A later reviewed
integration may relocate this owner; it must not create independently maintained
Python, C++ and Godot copies. Legacy Python presets remain historical code.

| Artifact | Schema / checker | What it establishes |
| --- | --- | --- |
| `catalog_v1.json` | `config/schema/explorer_topology_catalog_v1.schema.json` | Identity, metadata, cross-references and status admission |
| `quotients_v1.json` | `config/schema/explorer_topology_quotients_v1.schema.json` | Finite square-quotient proof specifications and recomputed combinatorics |
| `transport_v1.json` | `config/schema/explorer_topology_transport_fixtures_v1.schema.json` | Exact future test requests/outcomes, not native execution |
| `tools/migration/explorer_topology_contracts.py` | Existing bounded schema evaluator plus domain checks | Structural/schema, identity, evidence and fixture consistency |
| `tools/migration/square_quotient_evidence.py` | Independent continuous edge/germ incidence checker | Square quotient invariants; no movement API |

Schema validation and relational/domain checks are jointly mandatory, following
existing topology schema-plus-validator conventions. No new generic validator
framework or production binding is introduced. All new envelopes use integer
version 1, reject unknown fields and retain exact scalar types. Future versions
fail closed. Reuse the existing duplicate-key-rejecting JSON loader.

## 2. Three identities, and one catalog ID

A space class is a compact connected topological **2-manifold** type, with or
without boundary. IDs below are registered immutable semantic names, independent
of recipe, extent, display, input and camera. Genus is `g` for orientable types
and crosscap number `k` for nonorientable types. These definitions are targets;
they do not certify any construction-to-class association.

| `space_class_id` | Type | Orientable | Genus | Boundary count | Euler characteristic |
| --- | --- | --- | --- | --- | --- |
| `surface.disk` | Disk/rectangle | yes | g=0 | 1 | 1 |
| `surface.annulus` | Cylinder/annulus | yes | g=0 | 2 | 0 |
| `surface.torus` | Torus | yes | g=1 | 0 | 0 |
| `surface.mobius` | Möbius band | no | k=1 | 1 | 0 |
| `surface.klein` | Klein bottle | no | k=2 | 0 | 0 |
| `surface.projective` | RP² | no | k=1 | 0 | 1 |
| `surface.sphere` | S² | yes | g=0 | 0 | 2 |

**Construction identity is content-derived**, not a second registered recipe
name: `square-quotient-v1:sha256:<lowercase digest>`. The digested recipe has
exact fields `schema=tet4d.square_quotient`, `schema_version=1`, `dimension=2`,
`domain=unit_square`, `operator_version=1`, `parameters={}`, `gluings`.
The ordered four named edges and their parameterizations are fixed in §4.
Normalize gluings by invoking the existing canonical v1 producer on the recipe
at symbolic dimensions `(2,2)`, then take its canonical `gluings` array. The
recipe contains no board extents. Hash compact key-sorted UTF-8 JSON, exactly as
v1's serialization convention. The validator rejects a noncanonical stored recipe.

This projection reuses v1's ordering, seam-direction inversion, disabled-row
removal and canonical seam IDs. It does not implement another profile
normalizer. Fixed-axis changes, signs, permutations, operator/domain versions
and domain arrangement distinguish recipes; homeomorphism does not identify
recipes. Axis relabeling is deliberately not syntactic equivalence. No
multi-domain recipe is representable here; T6 needs a different recipe schema
and ID prefix, not additional fields smuggled into version 1.

A **profile ID** is `topology-v1:sha256:<existing topology_contract_identity>`.
Its suffix is the unchanged SHA-256 of the exact canonical v1 profile payload,
including board extents. The prefix only names the existing namespace/version.
The stored profile must normalize to itself and match its construction's
normalized gluings. Catalog labels, availability and proof status cannot affect
this identity. Each sample entry binds one explicit board; runtime-selected
boards derive another ID using the same owner, not a cached sample ID.

A **catalog entry ID** preserves `empty_2d`, `cylinder_2d`, `torus_2d`,
`mobius_2d`, `klein_2d`, `projective_2d`, `sphere_2d`. These are stable historical
entry keys, not proof of their labels. Aliases must be globally unambiguous and
cannot shadow another entry. Display strings may evolve without identity drift.

`identity_examples` in the catalog supplies exact digest vectors: torus 4×4
versus 4×5 shares a construction but not a profile; equivalent reversed/reordered
seams retain both identities; changing cylinder tangent sign produces the
Möbius recipe/profile; X-wrap and Y-wrap cylinders have the same proposed class
but different construction and profile IDs. Both cylinder recipes are real
`axis_wrap_profile` instances. The sphere-like recipe and standard Klein recipe
also have distinct IDs despite their derived common class (§5).

## 3. Catalog status and evidence rules

Every entry contains label, dimension, family/order, description, class
association, complete recipe/construction ID, canonical profile/profile ID,
versions, availability, certification, derived/unknown invariants, diagram
inputs, aliases and evidence references. Boundary/diagram inputs reference the
recipe and exact seam IDs; do not maintain a second list of gluing signs.
`space_class_id=unknown` is allowed, with `association=unresolved`.
`association=proposed` identifies an intended claim; only `proved` means certified.

| Availability | Meaning and evidence |
| --- | --- |
| `planned` | Informational; no selection action; no supported runtime evidence claimed |
| `experimental` | Active only with structurally valid profile and complete native piece invariants; reviewed runtime conformance and checked adapter evidence required |
| `implemented` | Experimental conditions plus completed bounded transfer, five-core/product integration and human acceptance for the declared scope |

| Certification | Meaning and evidence |
| --- | --- |
| `unverified` | Named association/proof awaits complete independent review; calculations may already exist |
| `heuristic` | Historical name or transport heuristic is not a certified space association |
| `verified` | Exact recipe digest has complete incidence/link/orientation/boundary proof, matching class and independent accepted review |

The axes are independent: `planned+verified` is legitimate; executable
`experimental+unverified` is legitimate only after runtime gates. No entry in
this T1 data is active: all availability is `planned`; five core records and
projective are `unverified`; sphere-like is `heuristic`. Python support and native
single-cell parity cannot promote availability. `unsafe` and ordinary rigid-Play
suitability are not inputs to either enum.

Promotion requires a reviewed data change, never a label change. Planned to
experimental requires passing structural, piece/atomic/inverse, strict adapter
and isolation evidence for the exact profile/engine contract. Experimental to
implemented additionally requires the terminal scoped transfer and product
acceptance. Unverified or heuristic to verified requires the same complete
mathematical gate; a heuristic can only associate with the class actually proved.
A disproved intended label must be corrected, preserving its historical alias.

`evidence` rows name repository path, record ID, SHA-256 of that canonical record,
kind and review state. Cross-reference validation resolves the exact record,
checks its construction/profile binding and digest, and rejects missing/stale
proof. Review evidence must name a nonempty reviewer and immutable review
reference. Runtime evidence must additionally name source commit, command,
outcome, exact profile/contract scope, a confined repository artifact path and
its raw-byte SHA-256, plus the transport fixture file SHA-256. Missing/stale
runtime artifacts reject admission. Strings saying “passed” are not an
execution or human review. Independent acceptance remains a human gate even
when evidence metadata validates. This T1 package includes no accepted reviews.

Invalid combinations include verified with unknown/mismatched class, pending
proof or unknown invariants; implemented without transfer/product evidence;
experimental without conformant runtime evidence; planned with selectable=true;
and any active status with a malformed profile. Invalid records fail catalog
admission. A consumer may show a nonselectable unavailable diagnostic; it must
not coerce status. Planned legacy projective/sphere entries retain clearly
qualified labels; proposed invariants display as **derived, review pending**.

## 4. Continuous quotient evidence procedure

The proof format is `square-quotient-evidence/1`. It binds the exact recipe/digest,
domain, face, oriented edge inventory, pairings, expected edge/vertex classes,
vertex links, boundary cycles, orientation, Euler characteristic, compactness,
connectedness, derived class, independent review and limitations. It concerns
continuous **polygon vertices**, not occupied lattice cell centers.

Use A=(0,0), B=(1,0), C=(1,1), D=(0,1). Natural edge parameterizations:
X−:A→D, X+:B→C, Y−:A→B, Y+:D→C. Counterclockwise boundary traversal is
Y−+, X++, Y+−, X−−. In this order the edge directions relative to their natural
parameters are `o=(+,+,-,-)`. A positive tangent pairing matches endpoints
in order; a negative pairing swaps them.

For a finite polygonal complex the deterministic proof procedure is:

1. Check each face is a disk with an ordered closed boundary word; each edge
   occurrence is unpaired or has exactly one distinct reciprocal mate. Check
   endpoints, invertible linear edge parameter maps and consistent incidence.
2. Union endpoints induced by paired edges; compute equivalence classes without
   identifying interiors of unpaired edges. Count one quotient edge per pair
   and one per unpaired occurrence, and one face per disk.
3. At every original corner create an interval arc with two nodes: the two
   incident **edge endpoint germs**. Pair corresponding germs along seam maps.
   For each quotient vertex assemble the resulting link **multigraph**, keeping
   loop arcs and parallel arcs. Require connectedness and either all degrees 2
   (circle/interior) or exactly two degrees 1 with all others 2
   (interval/boundary). Disconnected circles, branching and isolated germs fail.
4. Unpaired edge occurrences form the boundary graph on quotient vertices.
   Require degree 2 at its vertices (loop contributes 2); traverse each edge
   exactly once to obtain boundary cycles. Count components after vertex unions,
   never by counting original edges. Link endpoints must match these boundary germs.
5. Assign face orientations `f in {±1}`. For every paired edge enforce
   `f_source*o_source = -sign*f_target*o_target`. Solve the signed constraints
   by graph propagation; contradiction means nonorientable. For a single face
   any pair with `o_source*sign*o_target=+1` gives the explicit contradiction.
   Physical cell-frame determinants are not this orientation test.
6. Check quotient connectedness; finite disks plus closed edge homeomorphisms
   give compact Hausdorff quotient in this finite setup. Compute `chi=V-E+F`.
   Only after the incidence, edge-neighborhood and link tests establish a surface
   use `chi=2-2g-b` (orientable) or `chi=2-k-b` (nonorientable).
   Require integer `g>=0` or `k>=1` and compatibility with the claimed class.

A counterexample to chi-only admission is a sphere and torus joined at one
vertex: chi is `2+0-1=1`, like RP², but the joined vertex has two disjoint
circle links and is not a surface point. The disconnected-link regression
rejects precisely this local obstruction without adding a general wedge solver.

The checker implements only one unit square and its disjoint paired edges.
It neither accepts arbitrary cell complexes nor resolves cell movement. General
finite polygon checking above is a specification, not a promised universal
classifier. Malformed incidence is rejected; missing links/orientation/provenance
or unsupported decomposition leaves certification unknown. A failed link is an
explicit obstruction, not an invitation to infer class from chi.

The surface-classification premise is the standard compact connected surface
theorem; see Jeff Erickson's [Surface Classification](https://jeffe.cs.illinois.edu/teaching/comptop/2017/chapters/07-surface-classification.pdf)
and [Surface Maps](https://jeffe.cs.illinois.edu/teaching/comptop/2023/notes/19-surface-maps.html).
Our fixed-square calculations below are separate derivations, not claims that
those references certify these executable profiles.

## 5. Seven presets and the comparison construction

Write `ab+/-` for pairing edges a,b with natural tangent sign. Every row has one
face. The proof JSON contains exact link degree/corner witnesses and boundary
cycles; all await independent review, so none promotes catalog certification.

| Recipe | Edge classes (unpaired edges remain singleton) | Vertex classes | chi | Orientable / boundary | Local links / derived class |
| --- | --- | --- | --- | --- | --- |
| Bounded | X−; X+; Y−; Y+ | A; B; C; D | 1 | yes / 1 | Four interval links; disk |
| Cylinder: X−X+ + | {X−,X+}; Y−; Y+ | AB; CD | 0 | yes / 2 | Two interval links; annulus |
| Torus: X−X+ +, Y−Y+ + | {X−,X+}; {Y−,Y+} | ABCD | 0 | yes / 0 | One four-arc circle; torus |
| Möbius: X−X+ − | {X−,X+}; Y−; Y+ | AC; BD | 0 | no / 1 | Two interval links; Möbius band |
| Klein: X−X+ +, Y−Y+ − | {X−,X+}; {Y−,Y+} | ABCD | 0 | no / 0 | One four-arc circle; Klein bottle |
| Projective: X−X+ −, Y−Y+ − | {X−,X+}; {Y−,Y+} | AC; BD | 1 | no / 0 | Two two-arc circles; RP² |
| Legacy sphere-like: X−Y− −, X+Y+ − | {X−,Y−}; {X+,Y+} | ABCD | 0 | no / 0 | One four-arc circle; Klein bottle, not S² |
| Comparison only: X−Y− +, X+Y+ + | {X−,Y−}; {X+,Y+} | A; BD; C | 2 | yes / 0 | Two one-arc circles and one two-arc circle; sphere |

Projective endpoint derivation: X reversal identifies A~C and D~B; Y reversal
identifies A~C and B~D, adding no further vertex union. Each resulting link is
a connected two-edge multigraph with degree 2, not disconnected intervals.
One face/2 edges/2 vertices gives chi=1. Each reversed opposite-edge pairing
violates the one-face orientation equation. This supports RP², pending review.

Sphere-like derivation: X−Y− reversal identifies A~B, D~A; X+Y+ reversal
identifies B~C, C~D. All corners coincide. Their link is one connected cycle,
not two touching circles. Both pairs preserve the counterclockwise boundary
orientation, obstructing orientability. Thus this exact continuous quotient
satisfies the Klein-bottle classification conditions; the **catalog remains
heuristic pending independent review**, and the ID/transport remain unchanged.
Positive adjacent pairings instead leave A and C separate, identify only B~D,
and have orientable circle links and chi=2. This is investigation evidence only.
T6's two-domain ball-double sphere is Tet4D's chosen delivery architecture, not
a theorem that a sphere requires two domains.

The square's connectedness and compactness are immediate; edge interiors have
disk or half-disk neighborhoods. The remaining substantive checks are the
explicit link graphs and orientation constraints, not discrete step inverses.
Independent review must verify the recipe-to-preset mapping and every proof
witness before promotion; T2 separately proves runtime/profile conformance.

## 6. Transport fixture contract

`transport_v1.json` is a specification, version `explorer-transport-fixtures/1`.
It references Session 2's exact contract/version and provides shared complete
states, explicit positive cases, failure mutations, ordered sequences and a
finite boundary enumeration specification. Reference expansion is lossless
substitution, not a movement solver. It never calls Python piece movement to
invent expected new behavior.

A complete state has profile ID/board, object namespace/ordinal, immutable
rest geometry, all persistent IDs/domain-0 centers/source-indexed frames,
revision and initial/undo/trace baseline. A case references this entire source,
semantic action, exact per-ID destinations/frames, result/reason and complete
candidate. Candidate state is the source with **only** the explicitly listed
cell rows replaced, revision advanced on apply, and documented undo/trace
updates. Its inverse descriptor is exactly Session 2's source plus action;
expected inverse is the exact source semantic piece, revision advanced again,
undo canceled and optional diagnostic trace retained. No coordinate-set-only
comparison is sufficient. Blocked cases specify no candidate and whole-envelope
byte/value equality. Decoder failures are distinct from semantic rejection.

In ordered sequences, the first state supplies object identity, original
geometry and baseline. Later named states are pose templates: their cells/profile/
rest geometry must match the preceding candidate, while their standalone object
key/revision/baseline are not substituted. Every step binds the live incremented
revision and retains its own source descriptor. In E8 the intervening Y+ move
is committed before attempting the prepared candidate; its inverse produces the
specified later revision without reviving that candidate.

Mutations follow the existing transport fixture convention: base-case ID,
exact JSON path, replacement value, operation phase, reason/error path and
no-op assertions. Request mutations occur before proposal; candidate/current
mutations occur after proposal; descriptor mutations occur before inverse;
provider mutations are explicit test-only fault injection. Revision exhaustion
sets both request/current revision before proposal when `synchronize_current_revision`
is true. The unknown-field case alone adds its final path component. Invalid values belong in requests, not in successful state
records. `$float` retains a deliberate Variant float as in existing fixtures.
Malformed duplicate-boundary input is `invalid_profile`, not a reachable
`ambiguous_destination`; the latter is tested by an explicitly fault-injected
provider result and must never be advertised as a conforming v1 profile.

E1–E10 are carried forward, including E8 prepare/intervene/apply and E10 exact
intermediate states. Cylinder companions, all seam directions, non-square
boards, extent-one/two and strict/adversarial cases complete the five-core matrix.
The enumerated cell query family specifies every cell/direction on
1×1, 1×2, 2×1, 2×2, 4×4 and 4×5 for the five core recipes; cross-axis legacy
profiles use square boards only. Eight 2D signed frames exercise composition.
Exact formulas for these finite family expectations come from the piece
contract's per-cell rule and are recorded in the fixture, not guessed by a runner.

Evidence fields separately mark `specified`, historical Python comparison,
independent mathematical calculation, native `not_run` and Godot `not_run`.
The local checker validates fixtures, IDs, frames, correspondence, collision
expectations, sequence references and identity digests. The focused
`tools/migration/explorer_rotation_contract_evidence.py` checks exact stable-ID
pivot/development, quarter-turn projection and collision witnesses and §7's
periodic affine classification. Tests independently exercise fresh opposite
requests and four-turn identities; reviewed fixture outputs are not generated
by this helper. These are T1 mathematical checks, not a production piece engine
or execution of the native movement/commit contract. E3, E7 torus and E10's
third step use periodic coherence; E7 Möbius uses the ID-0 pivot and separately
blocks the negative request. E7's 2×3 torus I3 rejects projected collision
before classification. Runtime result fields remain `not_run`. Future runner names/commands in the transfer
package are labeled proposed and are not tests claimed to exist.

## 7. Adversarial containment and review gate

| Challenge | Concrete containment / regression |
| --- | --- |
| Distinct recipes collapse to one ID | Hash exact canonical recipe; X/Y cylinders and standard/adjacent Klein recipes remain distinct |
| Equivalent seam syntax changes profile | Existing canonicalizer; reverse/order/disabled-label mutation test |
| Board size or tangent sign omitted | Exact identity vectors for torus sizes and cylinder/Möbius |
| Plausible name or seam inverse proves wrong surface | Legacy sphere-like proof has chi=0; catalog stays heuristic |
| Correct chi but singular link | Link checker test with disconnected degree-2 cycles rejects; no class without connected links |
| Cell-frame reflection used as orientability | Boundary-orientation equation; cylinder/torus versus Möbius/Klein tests |
| Boundary edges counted before unions | Cylinder has two loops, Möbius one two-edge cycle |
| Projective name dictates result | Explicit AC/BD, link and chi=1 witness; independent review pending |
| Collision invalidates whole profile | E6 is movement rejection; profile remains structurally admitted |
| Experimental bypasses invariants | Same native conformance gate as implemented for all piece invariants |
| Planned looks usable or verified looks implemented | selectable/status checks; all seven samples nonselectable |
| Conflicting profile versions / stale evidence | Exact version, digest, construction/profile and record-reference checks |
| T6 reinterprets v1 | Closed single-square recipe schema and distinct future prefix required |

Technical design delivery is not T1 acceptance. Independent adversarial review
of Sessions 2 and 3, reconciliation of any findings, and explicit T1 acceptance
are next. No production UI/native transport, authority transfer, historical
rebaseline or premature mathematical status promotion is authorized here.
