# Explorer Topologies and Visual Topology Builder RDS

Role: rds
Status: active
Scope: Godot Explorer topology behavior, 2D/3D/4D presets, custom topology building, deterministic cell transport, validation, and acceptance
Canonical owner: this file for forward Explorer topology product semantics
Last verified: 2026-11-04
Revision: 2 — T1/T2 dependency and bounded authority-transfer redesign

## 1. Purpose and product decisions

The existing Godot Explorer is the primary environment for investigating polycubes and topological spaces in **2D, 3D, and 4D**. The topology builder is a **secondary** visual editing workspace, never a replacement Explorer, separate gameplay client, or independent style/input/movement system.

Players must be able to choose familiar presets directly inside Explorer; the builder is needed only to create or modify topologies. Explorer is a topology laboratory, not a rigid-body simulation: flat cubical presentations may expose a piece's deformation or apparent disconnection.

**Non-negotiable invariant:** A successful operation preserves every constituent cell's identity and count, maps every source cell to exactly one destination, and maps distinct source cells to distinct occupied destinations. Cells may not split, merge, duplicate, disappear, or collide.

## 2. Normative precedence and explicit authority milestones

### 2.1 Product requirements versus implemented semantic ownership

This RDS is authoritative for **forward Godot Explorer topology product behavior**, even where Python Explorer outputs, fixtures or legacy labels conflict. Duplicate destination occupancy must produce an atomic blocked result, **never** a successful `cellwise_deformation`. Do not weaken this rule to satisfy a historical golden.

This RDS does **not** itself transfer runtime authority. The existing `docs/architecture/authority_map.md` must remain truthful until an evidence-backed transfer or establishment record reaches its terminal state. Existing ordinary Play, gravity, lock/drop, scoring, traces, replay, and inherited scopes outside an explicitly transferred boundary are unaffected.

| Concern | Target owner | Boundary |
| --- | --- | --- |
| Forward Explorer product behavior | This RDS | Requirements and acceptance |
| Profile, construction, catalog and canonical identity data | Versioned language-neutral contracts | Declarative normalization, metadata, compatibility |
| Seam, cell, piece and frame transport; structural validation | Native C++ | Deterministic topology truth |
| Seam inspection and topology-aware adjacency | Native C++ | Read-only semantic queries |
| Explorer and secondary Builder, UI state, controls, camera, rendering | Godot | No independent topology solver |
| Old Python Topology Playground and goldens | Legacy reference/compatibility | No veto of explicitly superseded Explorer requirements |

### 2.2 Split transfer and establishment timeline

1. **Stage T1 prepares, but does not complete, authority transfer.** Define semantic owner boundaries, two-way transport and catalog contracts, the planned native APIs, deterministic fixture expectations, Python-oracle divergences, compatibility and fallback.
2. **Stage T2 must complete the bounded 2D Explorer native transport transfer before T2 can be accepted.** Native behavior must conform to this RDS, including conservation, injectivity, local-frame inverse and atomic rejection. Update the authority map and record status `transferred` under `docs/architecture/authority_transfer_protocol.md` only after required conformance and compatibility evidence.
3. **Stage T4 separately extends and transfers 3D/4D Explorer transport.** The 2D transfer does not implicitly change inherited 3D/4D or normal gameplay authority.
4. **Stage T6 establishes or transfers multi-domain topology semantics** according to their exact predecessor/owner. Do not manufacture Python oracle behavior solely to perform a nominal transfer.
5. **Stage T7 performs integrated acceptance and authority audit**; it is not the first occasion to complete prior required transfers.

Required transfer evidence includes current/candidate authority, exact observable scope, versioned conformance cases, existing Python comparison and intentionally superseded expectations, commands, known exclusions, compatibility, safe fallback/reversion, authority-map update and governance validation. Passing native code alone does not create authority.

**If the T2 transfer cannot be completed, T2 remains incomplete:** do not ship the new 2D Explorer with an implicitly authoritative, conflicting Python fallback.

### 2.3 Explicit approval of the Explorer RDS replan

The project owner explicitly permits this RDS to supersede conflicting
historical Python **Explorer requirements** as a normative product decision.
The authority-map's planned Explorer row is annotated with
`**Approved Explorer RDS replan: requirements only.**` for the narrowly scoped CI guard exemption.

This approval does not transfer native runtime authority, does not override
ordinary Play, and does not authorize an unrecorded topology transfer. The
validator must permit only the annotated **planned** Explorer row when it also
retains the RDS link, native C++ **candidate** status, the explicit no-transfer
statement and T2/T4 scoped authority-transfer gates. All other non-Python
semantic-oracle and supersession claims remain guarded.

T1 prepares contracts; T2 must complete a verified 2D Explorer-only transfer
before acceptance; T4 transfers 3D/4D separately. Multi-domain authority
follows its independent T6 establishment/transfer procedure.

### 2.4 Legacy compatibility and test discipline

Version-1 single-domain profiles and existing Python golden traces retain historical readability and meaning. Test expectations must be marked conforming, explicitly superseded, legacy compatibility, or unrelated; replace conflicting Explorer tests with conformance assertions rather than deleting coverage. Do not reassign old `sphere_2d`, `sphere_3d` or `sphere_4d` IDs to mathematically certified spheres. Do not copy the legacy Pygame Editor/Sandbox/Play UI as a second Godot Explorer.


## 3. Primary Explorer information architecture

- Main Menu -> Explorer enters the existing Godot Explorer; it must support 2D, 3D, and 4D.
- A visible topology selector on the existing primary Explorer panel offers the current preset and an immediately accessible preset gallery.
- `Edit Topology` opens the subordinate builder with a copy of the current preset or draft.
- `Return to Explorer` restores the existing view, piece, and control context where compatible.
- Presets are immutable; editing one creates a custom draft.
- Topology choice is not a separate Explorer application, a new top-level gameplay mode, or a duplicate `Editor / Sandbox / Play` shell.
- The existing Python Topology Playground remains a legacy/independent tool during migration; do not retrofit its frozen shell into Godot.

The Explorer retains gravity-free practice, single-piece initial object model, native catalogue, deliberate translation/rotation, Retry Object, Reset View, camera controls, 4D exact-basis and slice inspection, dynamically derived control help, and responsive cockpit layout. Ordinary Play remains independently governed and starts a fresh session.

## 4. Dimensions

### 4.1 2D first-class Explorer

2D is a full Explorer dimension and the recommended topology-learning starting point, not an optional debug mode. Reuse the live 2D board/piece renderer, piece catalogue and action routing. Support ±X/±Y translation, XY rotation, selectable four edges, crossing preview, seam highlights, path trace, and topology-aware adjacency. Topology selection and building in 2D must precede higher-dimensional builder acceptance.

### 4.2 3D

Retain the 3D renderer, camera, camera-relative movement and XY/XZ/YZ piece rotations. Add six selectable square boundary faces, face identifications, tangent-axis correspondence and transport, as well as topology-aware neighbors and seam visualization.

### 4.3 4D

Retain the 4D signed-basis/slice and presentation pipeline, camera-relative movement, ±X/±Y/±Z/±W translation and all six object-rotation planes. Add eight selectable cubical boundary hyperfaces, frame-aware 4D seam transport and a 3D hyperface inspector. Changing presentation basis or slice must not mutate topology or cells.

## 5. Cell identity, locations and occupancy

A piece is a finite, indexed collection `P = {p_1, ..., p_n}` of persistent cell identities. Its deterministic state includes each cell's canonical location, its local transported frame (where needed), and any transport/history information necessary for a well-defined inverse. Identity is not position; separate component cells remain one object even when rendered far apart.

A **cell location** is `(domain_id, integer_coordinate)`. Single-domain v1 may use an implicit domain. Multiple domains require explicit identifiers. A canonical occupied location is not a screen pixel, rendered ghost, boundary point or a duplicate visual representation in a covering view.

A face/edge/hyperface identification concerns the quotient's boundary geometry; it does **not** automatically merge distinct cell-center sites. In particular, ordinary torus wrapping must remain explorable without treating opposing seam-adjacent cell centers as coincident.

Occupancy uniqueness is checked against canonical cell locations. Projection overlap is not a collision; an actual duplicate occupied location is.

## 6. Deterministic movement contract

For a selected directed movement command and full current state, each participating cell must have **at most one** resolved destination. The command may fail if a required boundary is unconnected, the mapping is undefined or ambiguous, or another invariant fails.

For a successful move from source occupied locations `c_i` to `c'_i`:
1. **Functionality:** each source identity obtains exactly one destination.
2. **Injectivity:** `i != j => c'_i != c'_j`.
3. **Conservation:** source and destination contain the same number and identities of cells.
4. **Reversibility:** the specified inverse transport (including direction/frame/domain information) reconstructs the prior complete cell state.
5. **Atomicity:** candidate computation, uniqueness, inverse and validity checks run before any state mutation; commit succeeds entirely or changes nothing.
6. **Determinism:** equal topology, command and full source state yield the same result.

The inverse is relative to the transported local frame and recorded operation; pressing the opposite global camera-relative key need not be its inverse on a twisted seam.

**Permitted:** rigid moves, rotations/reflections, non-rigid cellwise deformation, cells crossing different seams, cells entering different domains, changed apparent adjacency, visually disconnected pieces, and orientation changes. No whole-piece Euclidean rigid transform is required.

**Blocked:** one-to-many or undefined cell destination for an attempted move, two cells at one canonical destination, disappearance, duplication, non-reversible or ambiguous transport, unsupported representation, or any partial move. Reject the whole operation and preserve the exact previous pose, frames, cell identities, trace and deterministic state.

A single cell can have multiple *available user commands* (± axes); that is not a one-to-many result for **one selected command**.

### 6.1 Result taxonomy

The deterministic native result contract shall distinguish:
- `plain_translation`: coherent identity-frame translation;
- `rigid_transform`: one coherent signed-permutation/translation transform;
- `cellwise_deformation`: successfully mapped, conserved, injective result not described by one rigid transform;
- `blocked`: atomic rejection with stable reason.

Stable reasons shall cover `unconnected_boundary`, `ambiguous_destination`, `destination_collision`, `invalid_transport`, `inverse_mismatch`, `rotation_undefined`, and `unsupported_representation`. Centralize names in one versioned contract.

**Required correction:** The current Python resolver's duplicate-target `CELLWISE_DEFORMATION` classification must be replaced with a blocked destination-collision outcome in the new authority and any adopted compatibility implementation. Historical goldens remain versioned; superseded behavioral tests get explicit replacement expectations rather than silent deletion.

### 6.2 Topology versus movement validity

A structurally valid topology is selectable even if a particular polycube move becomes non-rigid or must be blocked. Validity of individual pairings, mathematical recognition of a manifold, and ordinary rigid-Play admissibility are three separate judgments.

Explorer does **not** gate an entire topology based merely on non-orientability, curvature, gravity unsuitability, potential deformation, or a legacy `unsafe` flag. It **does** reject malformed or ambiguous transport definitions. It blocks individual invalid moves at execution time.

### 6.3 Local frames and rotation after deformation

Player input resolves through the existing control-frame mapping; local topology transport may permute or reverse directions independently of the camera. Cell-local frame and mapping history must survive movement, undo and serialization of an Explorer state.

Undeformed pieces retain the existing native rotation geometry. For a deformed piece, a rotation may execute only when a coherent local development/anchor and transport of **every** candidate cell are uniquely defined. Resolve the complete candidate, check functionality/injectivity/conservation/inverse, then commit atomically. If no unambiguous development exists, reject that rotation only; preserve valid translation and topology selection. Do not invent a global Euclidean frame or ban the topology.

### 6.4 Connectivity and overlap

Keep distinct: adjacency within a displayed domain, adjacency across the topology, and membership in the same original piece. A visually split piece need not be topologically disconnected. Optional neighbor overlays identify seam-based connections. Never collapse cell identities when multiple cells visually project to one point.

## 7. Stage T1 — Semantic and catalog foundation

**T1 purpose:** design the foundations demanded by T2's five real 2D presets and expanded catalog **before** native/Godot implementation. It is contract-and-transfer preparation, not a complete topology implementation or a separate research stage.

### 7.1 Separate the mathematical space, its construction, and the transport

The contract must distinguish:

```text
space_class_id  (topological type, e.g. torus T²)
   construction_id  (gluing recipe, version and parameters)
      profile_id  (fully normalized discrete transport and board)
```

Two gluing recipes can represent the same mathematical space. Two board discretizations of the same recipe can produce different cell-transport profiles. A name, topology proof, or visually similar seam pattern is not by itself a verified movement model.

Define identities, normalization, compatibility aliases, cross-references and ownership. Exclude display labels, input order and camera from transport identity. Preserve canonical v1 single-domain meaning. Reserve a **separately versioned** multi-domain extension rather than altering v1 profiles in place. T1 does not implement this extension.

### 7.2 Versioned catalog-data contract

Define a **declarative schema**, independent of Godot gallery code, containing:

- Stable preset ID, dimension, label, family, explanation and ordering.
- `space_class_id`, recipe/version/parameters, `construction_id`, actual `profile_id` and relevant schema version where applicable.
- **Availability**: `implemented` (active and conformant); `experimental` (active only if structurally valid and runtime one-to-one); `planned` (informational only).
- **Mathematical certification**, independently: `verified`, `unverified`, `heuristic`.
- Established invariants such as orientability, boundary-component count, Euler characteristic, with evidence and explicit `unknown` where undecided.
- Boundary-correspondence information, legacy aliases, diagram inputs, and traceable conformance/certification evidence.

These categories must not collapse into an `unsafe` switch. Experimental does not mean rigidly playable; planned must not appear to work. T1 defines schema and a small representative fixture catalog, not every future space or UI card.

### 7.3 Structural transport validity versus mathematical certification

**Transport validation** establishes valid axes/ranks/extents, compatible tangent signed permutations, uniquely owned and reversible seam pairs, valid in-bounds destinations, deterministic local frames and strict canonicalization. It does **not** require every conceivable piece move to succeed; a many-to-one candidate collision is rejected at execution time without invalidating the underlying topology.

**Mathematical certification** establishes what quotient space a construction represents. For a claimed 2D surface, evidence must address edge and vertex equivalence classes, Euler characteristic of the quotient cell complex, orientability, boundary components and the manifold/local-link condition. Validating one-cell seam bijections alone cannot prove `RP²`, `S²`, or an arbitrary manifold.

T1 defines the independent certification fixture format and promotion rules, not a universal manifold classifier. If certification is missing, keep the topology exploratory with truthful metadata rather than fabricating mathematical facts.

### 7.4 Native API, atomicity and inspectability contracts

T1 must specify the input, result/error, identity and state-transition contracts for:

```text
validate_profile(profile, board)                -> normalized profile / errors
query_boundary_pair(profile, boundary)          -> correspondence / none
query_neighbor(profile, cell, direction)         -> target + frame / blocked
query_seam_preview(profile, cell, direction)     -> correspondence + orientation
propose_piece_action(profile, piece, action)     -> candidate / blocked
apply_validated_action(piece, candidate)         -> new state / atomic no-op
query_topology_adjacency(profile, piece)         -> neighbor relationships
```

These are conceptual operations, not mandated names for C++ functions. Native owns all topology calculations. Godot receives a thin, checked result adapter; it must not independently compute validity or corresponding destination cells.

A piece has persistent cell IDs and canonical occupied **cell-center** positions, with domain identity (implicit for v1), transported local frames and enough inverse-operation information to recover exact state. A quotient's identified boundary points are **not automatically the same occupied cell centers**. Projected visual overlap is not collision.

For one selected movement, each cell has at most one destination; on success, destinations are injective, original cell IDs/count are preserved, and the defined frame-aware inverse restores state. All candidate cells are resolved/validated before an **atomic** commit. A blocked result preserves everything, including positions, frames, trace and history. The API distinguishes `plain_translation`, `rigid_transform`, valid `cellwise_deformation`, and `blocked` with stable reasons including `ambiguous_destination`, `destination_collision`, `unconnected_boundary`, `inverse_mismatch` and `rotation_undefined`.

These result names must live in a single versioned contract, not duplicated among GDScript and native adapters.

### 7.5 T1 deterministic fixture and transfer package

Define expected behavior for each **mandatory T2** candidate:

| Candidate | Essential positive/negative fixture |
| --- | --- |
| Bounded rectangle | Missing seam blocks entire piece |
| Cylinder / annulus | X crossing wraps; Y boundary remains blocking |
| Torus | Two reversible periodic directions; seam-adjacent cell centers remain distinct |
| Möbius strip | Tangent reversal, correct transported frame and inverse |
| Klein bottle | Periodic and orientation-reversing pairs interact consistently |

Across the fixtures require single and multi-cell movement, a valid non-rigid/decomposed display, one-to-many ambiguity, many-to-one occupancy, partly blocked move, small/degenerate extents, boundary intersections, inverse operation with changed frame, and deterministic cell identity. Provide a mathematical certification **plan** for the existing projective candidate, including the square's quotient edge/vertex structure, orientability, boundary count and `χ=1`. Do not certify its name without evidence; do not treat old sphere-like transport as proof of a sphere.

Document intended Python-old versus new-RDS behavior, coverage disposition, native query/commit owner, compatibility fallback, comparison procedure and bounded transfer record requirements.

### 7.6 T1 acceptance and explicit exclusions

T1 passes only when:
1. Three identity types and a versioned catalog/status schema are normatively defined.
2. Strict transport validity and separate space certification are specified, with verifiable evidence requirements.
3. Whole-piece native move/query/result semantics, adjacency and seam-inspection contracts are specified.
4. Five core 2D preset fixtures plus negative injectivity/atomicity fixtures are written and routed to native/Godot owners.
5. The 2D-only Python-to-native semantic transfer is scoped with exclusions, compatibility, conformance, fallback and authority-map migration plan.
6. Single-domain v1 compatibility and forward multi-domain versioning rules are clear.
7. Required governance/document/schema checks pass.

**T1 does not implement:** Godot 2D Explorer, gallery, visual editor, saved custom profiles, native authority transfer, a sphere, connected sum, complete surface generator or multi-domain runtime.

## 8. Stage T2 — Mandatory 2D catalog and expanded preset roadmap

### 8.1 Five functioning core spaces

T2's **required** implemented presets, not merely future catalog names:

| Space | Existing Python candidate ID | Expected mathematical data | T2 |
| --- | --- | --- | --- |
| Bounded rectangle / disk | `empty_2d` | Orientable; 1 boundary; `χ=1` | Working |
| Cylinder / annulus | `cylinder_2d` | Orientable; 2 boundaries; `χ=0` | Working |
| Torus `T²` | `torus_2d` | Orientable, closed; `χ=0` | Working |
| Möbius strip | `mobius_2d` | Non-orientable; 1 boundary; `χ=0` | Working |
| Klein bottle | `klein_2d` | Non-orientable, closed; `χ=0` | Working |
| Projective plane `RP²` | `projective_2d` | Non-orientable, closed; `χ=1` | Verification-gated optional certification |
| Sphere-like transport | legacy `sphere_2d` | **Not** a verified sphere | Optional experimental |

T2 must verify the five core mathematical constructions and their **actual discrete seam/frame behavior**, not infer correctness from labels. Projective `RP²` may be called that only after rigorous edge/vertex, manifold and Euler-characteristic certification of the current construction. Otherwise call it **Projective-like transport (experimental)**. The old `sphere_2d` ID continues to denote heuristic transport, not `S²`. A genuine sphere is *planned* in T6 and must not appear as selectable in T2.

### 8.2 Catalog navigation and semantics

A visible preset selector remains inside the **existing** Godot Explorer, with a compact grouped, read-only gallery. Main working presets are directly selectable without opening a secondary editor.

- **Learn:** five core surfaces and accurate projective/sphere-like explanations.
- **Families:** periodic, twisted and planned surface-class families.
- **Advanced:** conformant experimental profiles, proofs/unknown properties and seam information.
- **Saved:** future T3 custom-topology persistence, not a working T2 feature.

An entry has independent `availability` and `certification` states as defined in T1. `planned` is informational. `experimental` may run only when structurally valid and runtime one-to-one, regardless of rigidity. Unknown mathematics is displayed as unknown. Visible seam colors require redundant symbols/labels.

T2 adds 2D to the current Explorer, with native 2D transport, seam highlight/preview, optional cell identity/trace, topology-aware adjacency, blocked-movement explanation, and existing renderer/input/cockpit conventions. This is **not** a new topology game or Pygame editor port.

### 8.3 T2 completion includes 2D native authority transfer

All five mandatory presets must execute native **whole-piece** cell transport, with functionality, injectivity, conservation, transported-frame inverse, atomic rejection, valid non-rigid deformation and correct seam-aware neighbors. Every crossing direction and relevant corner/degenerate board case requires deterministic tests.

T2 must document old Python golden divergences; a duplicate destination must block even if Python historically called it deformation. Complete the **2D Explorer transport** transfer record with status `transferred` and an authority-map update after the conformance and compatibility gates. Until then T2 is incomplete, irrespective of visual quality.

Retain bounded 3D/4D camera-relative, exact-basis/slice and ordinary Play isolation regressions. Human T2 review must show novice discovery of the five presets, prediction of torus/Möbius crossing and recognition of a single piece after visually separated cell movement.

**Not T2:** edge-pairing builder or saved profiles (T3), 3D/4D topology runtime (T4), face/hyperface builder (T5), multi-domain spheres or surface/product construction generators (T6 or later).

### 8.4 Planned complete 2D compact-surface families

Use classification by **orientability, genus/crosscaps and number of boundary components**. The fixed examples and generators are **not mandatory T2 runtime features**.

| Planned example | Class / invariant | Additional construction |
| --- | --- | --- |
| Genuine sphere `S²` | Orientable genus 0, closed; `χ=2` | Double of disk; T6 |
| Pair of pants | Orientable genus 0, 3 boundaries; `χ=-1` | Multi-patch boundary construction |
| Punctured torus | Orientable genus 1, 1 boundary; `χ=-1` | Verified boundary removal |
| Double torus | Orientable genus 2, closed; `χ=-2` | Connected sum |
| Triple torus | Orientable genus 3, closed; `χ=-4` | Generalized connected sum |
| Dyck's surface | Non-orientable genus 3, closed; `χ=-1` | Crosscap construction |
| Orientable surface generator | `g>=0, b>=0; χ=2-2g-b` | Verified handles/boundaries |
| Non-orientable generator | `k>=1, b>=0; χ=2-k-b` | Verified crosscaps/boundaries |

A genus or boundary parameter describes a mathematical space class, **not** automatically a valid, usable discrete transport profile. Generators must produce a certified cubical construction and separately pass native transport/corner/inverse/conservation tests. Out-of-envelope configurations remain unavailable.

### 8.5 Planned 3D and 4D catalog families

**3D:** bounded 3-ball, solid torus `S¹×D²`, thickened torus `T²×I`, `T³`, thickened Möbius/Klein, twisted and cross-axis faces, verified `RP³`, `S³`, `S²×I`, `S²×S¹`, selected lens spaces and eventually the **ten closed flat 3-manifolds** (six orientable, four non-orientable).

**4D:** bounded `D⁴`, partial wraps `S¹×D³`, `T²×D²`, `T³×I`, full `T⁴`, Möbius/Klein × `I²`, verified `RP⁴`, `S⁴`, `S³×S¹`, `S²×T²`, `S²×S²`, Klein × `T²` and `RP²×T²`. `CP²` is research-only.

Prefer versioned and verified **construction operators** over many bespoke hard-coded rows: axis wrap, reversal, Cartesian product, ball-double, antipodal quotient, connected sum, boundary removal, and generalized affine/group action. Third- and sixth-turn flat 3-manifolds cannot be promised using only existing cubical signed-permutation seam maps. Later stages must identify extended mathematical/transport machinery rather than fake a named quotient.

### 8.6 Multi-domain sphere construction boundary (T6)

Genuine `S^n` may be represented as the double of an n-ball: glue the entire boundaries of **two** n-cubic domains (square for n=2, cube for n=3, tesseract for n=4). Domain interiors remain separate. The flat cubical drawing is not a globally flat smooth metric on a sphere.

T6 requires a separately versioned domain-aware schema, stable domain and boundary IDs, consistent higher-codimension intersections, canonical quotient identity and unambiguous crossing/inverse of both domain and local frames. The quotient's shared boundary points are not automatically merged cell-center occupancy. A piece may span domains; an ambiguous or colliding particular movement blocks atomically. v1 profiles and heuristic IDs remain compatible. The visual `Add Domain` editor is introduced alongside this capability, not simulated inside v1.


## 9. Main Explorer topology presentation

Reuse the Godot renderer, colors/style registry, piece display, camera and control helper. Add subordinate, optional visual layers:
- matched boundary highlight with redundant color **and** symbol/label;
- destination ghost/crossing preview with source and target correspondence;
- path trace, visibly marking crossings and domain changes;
- per-cell identity tracing;
- topology-aware neighbor overlay, distinct from the base piece;
- local tangent-frame/orientation arrows;
- ghost neighbor-domain previews, which must never count as additional cells.

A topology selection updates actual transport, not just a scene color or name. Ordinary movement success does not flood the cockpit with diagnostics. Rejected operations use bounded, readable feedback with a concrete reason.

Rendering a 4D slice or rotating an inspection camera cannot change topology truth. 4D hidden hyperfaces must remain selectable through a labeled browser or auxiliary 3D inspector.

## 10. Secondary Custom Topology Builder

### 10.1 Layout and ownership

Enter through `Edit Topology`; `Return to Explorer` restores context. The builder has a compact header, a boundary/domain browser, a **dominant central visual workspace**, and a contextual connection inspector. Technical diagnostics and raw permutations are secondary advanced controls.

Godot owns only the draft/edit/UI workflow; semantic validation and transport use native APIs. Do not create a second movement engine, renderer style, or keybinding vocabulary.

### 10.2 Primary six-step workflow

1. Choose the first edge/face/hyperface.
2. Choose the second, possibly in another domain.
3. See paired highlighting, corresponding corners/axes and a default compatible mapping.
4. Manipulate orientation (flip/rotate) visually.
5. Preview one sample-cell crossing **in both directions**, showing orientation and target.
6. Apply the connection to the draft, then apply the validated topology to Explorer.

Selecting/previewing is **not** a committed mutation. Incomplete drafts remain editable. Applying a topology is atomic; Cancel preserves the active topology. Undo/Redo covers connection edits, domain edits, deletes, and transform edits.

### 10.3 2D boundary editor

Expose four edges ±X/±Y around the actual rectangular domain. Click-to-pair; show endpoint correspondence and arrows. The two tangent mappings (preserve/reverse) are represented directly. Novice construction of cylinder, torus, Möbius strip and Klein bottle requires no numeric transform entry.

### 10.4 3D face editor

Expose six square faces ±X/±Y/±Z; pair by direct selection or labeled list. Show the source and target face side-by-side, corresponding corners, two tangent axes, and an animated sample marker. Rotation/reflection controls cover the eight signed square orientations without presenting an eight-item matrix menu by default.

### 10.5 4D hyperface editor

Expose eight cubical hyperfaces ±X/±Y/±Z/±W. Provide both an existing 4D projected/sliced view and a coordinated independently rotatable **3D hyperface inspection** view. Users visually specify the 48 signed permutations of three tangent axes via rotate/reflect operations. Viewing a cube from another angle must **not** alter the mapping; transform editing is explicit. Both views share one canonical boundary selection.

### 10.6 Multi-domain editor

Provide an advanced `Add Domain` operation and a domain browser. Cross-domain pair labels include both domain ID and signed boundary, e.g. `A:+X <-> B:-Y`. `Sphere construction` may initialize the two-domain boundary gluing template. Domain deletion is explicit and undoable, with affected connections identified.

### 10.7 Validation and user feedback

Check structural validity (axes, ranks, extents, bijection/inverse, no conflicting boundary ownership, deterministic crossing, domain reference, serialization). Explain errors geometrically: e.g. `These faces have incompatible sizes`, with exact technical diagnostics optionally expandable.

Do **not** require a rigidly playable profile to apply an otherwise valid topology. Mathematical classification requires separate proof/tests; a valid seam set is not automatically a named manifold.

## 11. Input, readability, and lifecycle

Existing Explorer movement, rotation, view, camera/slice, piece selector, retry, reset, input bindings, helper-keycap and reflow policies remain the default. Builder-specific actions (select, connect, align, reflect, test, apply, undo/redo, back) use visible semantic action descriptors and keyboard alternatives to precision clicking. Input focus must isolate text and edit actions from game movement.

Panels and text resize for readability, then scroll below the readability floor. Test 1280x720, 1280x800, narrow windows and fullscreen. Normal movement/preview must not rebuild control nodes or change selected tab, control state, scrollbar position, board allocation or camera.

Keep four separate state owners: canonical topology, deterministic piece/cell transport, presentation view, and uncommitted builder draft. Switching topology preserves view and valid piece state; incompatible poses require explicit recovery rather than silent reset. Retry/Undo restore exact cell identities, locations and local frames. Explorer does not mutate native gameplay RNG, score, queue, lock, gravity or hashes; Play starts under its separate admissibility contract.

Save/load/duplicate/rename/delete/export/import custom topology definitions using versioned canonical data. Preserve v1 readability and historical traces. Do not store transient camera state inside the semantic topology identity.

## 12. Stage-sensitive evidence and non-regression

**T1:** schema/catalog and ID correspondence checks; transport-versus-certification contract reviews; five 2D positive and negative fixture **specifications**; complete bounded authority-transfer design including Python divergences and rollback. T1 does not claim implementation tests passed or an authority transfer.

**T2:** native deterministic tests for all five real presets (normal, seam, corner, degenerate, inverse-frame, multi-cell deformation, one-to-many, many-to-one, partial-block), native/Godot contract parity, preset gallery and UX, historical compatibility distinctions, human 2D comprehension review, regression of 3D/4D camera-relative controls, 4D basis/slices, responsive panels and normal Play, **and terminal 2D authority-transfer record**.

**T3:** 2D visual pairing, orientation preview, draft Apply/Cancel, Undo/Redo, persistence/import compatibility and novice builder tests.

**T4:** 3D/4D signed-frame native transport conformance, Godot input/camera/basis/slice regression, exact scoped authority-transfer record for newly owned dimensions.

**T5:** 3D square face and 4D cubic hyperface visual editing, correspondence-inverse and view-versus-mapping isolation, input-focus and layout acceptance.

**T6:** multi-domain schema versioning, canonical import/round-trip, two-domain sphere certification, corner and higher-codimension consistency, cross-domain inverse/identity, and authority establishment/transfer appropriate to the new scope.

**T7:** integrated topology pedagogy and visual acceptance, regression and authority-record audit. T7 is **not** a substitute for mandatory earlier transfer milestones.

Every conformance fixture names the normative contract, input profile/board, precise source cell IDs/locations/frames, command, expected destinations or failure, inverse, status and comparison mode. Do not waive an old golden silently. Require actual routed tests and the project full gate `CODEX_MODE=1 ./scripts/verify.sh` for implementation changes. A docs-only RDS commit proves no runtime or human acceptance.

## 13. Revised implementation and authority gates

| Stage | Deliverable | Completion gate |
| --- | --- | --- |
| **T1** | **Semantic/catalog foundation and native 2D transfer preparation** | Three identities, versioned catalog and status metadata, mathematical certification, piece transport/query API, five 2D conformance fixture specifications, legacy-difference and compatibility/rollback plan. No transfer yet. |
| **T2** | **2D Explorer, five working core presets, grouped catalog** | Native one-to-one piece transport and seam queries, mathematical-name honesty, Godot integration, human 2D review, **2D Explorer native authority transfer completed and recorded**. |
| T3 | 2D visual edge builder and custom-profile save/load | Torus/Möbius/Klein visually constructed, stable draft/undo/apply and persistence. |
| T4 | 3D/4D Explorer native topology transport | Shared signed-frame semantics, camera/basis non-regression and **separate completed 3D/4D transfer**. |
| T5 | Visual 3D/4D topology builder | All supported 3D face and 4D hyperface signed tangent mappings visually editable and tested. |
| T6 | Multi-domain and verified `S²/S³/S⁴` | Versioned domain schema, certified spherical doubles, cross-domain conformance, appropriate native authority establishment/transfer. |
| T7 | Integrated learnability/quality and authority audit | User comprehension, visual stability, deterministic regressions and review of **already completed** scoped authority records. |
| Later | Genus/crosscap/product generators, all ten 3D flat manifolds, lens and advanced 4D spaces | Independent operator contracts, proof, resource envelope, native implementation and human acceptance; not a T2/T7 blocker. |

**Dependency order:** T1 specifies reusable semantics and evidence; T2 *implements* and transfers 2D; T3 consumes 2D; T4 extends/transfers 3D/4D; T5 consumes those dimensions; T6 extends to domains; T7 integrates. No general Python-oracle veto and no premature global native transfer.

A stage may not claim a later stage's deliverable. First-class topological **games**, ordinary Play policies and an entire Python Topology Playground port remain separate work.


## 14. Explicit non-goals

No universal rigid playability requirement, automatic gravity/drop/lock behavior for custom topologies, continuous differential geometry, smooth embedded sphere rendering, arbitrary continuous seam rotations, certification of all custom manifolds, separate Godot topology engine, Python oracle reinvention, backend/login, research telemetry, release-matrix expansion, or unrelated UI redesign.

## 15. Final acceptance

T1 contract preparation, T2 bounded native transfer, T4 dimensional transfer and T6 multi-domain authority must each be accepted at their own gate. T7 cannot defer them.

Explorer is complete only when: 2D/3D/4D all select and traverse supported topologies; presets are immediate; builder is secondary and visual at each dimension; successful moves preserve one-to-one cell identity and are reversible; both split/merge cases are blocked; deformation/disconnection are permitted; domain-aware sphere constructions are correctly represented; full native and Godot gates, human learnability checks, compatibility migration and formal authority transfer are completed.

**Final invariant: Geometry may deform. Constituent cells may not split, merge, disappear, or multiply.**
