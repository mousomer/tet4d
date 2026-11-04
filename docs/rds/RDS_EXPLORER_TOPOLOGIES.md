# Explorer Topologies and Visual Topology Builder RDS

Role: rds
Status: active
Scope: Godot Explorer topology behavior, 2D/3D/4D presets, custom topology building, deterministic cell transport, validation, and acceptance
Canonical owner: this file for forward Explorer topology product semantics
Last verified: 2026-11-04

## 1. Purpose and product decisions

The existing Godot Explorer is the primary environment for investigating polycubes and topological spaces in **2D, 3D, and 4D**. The topology builder is a **secondary** visual editing workspace, never a replacement Explorer, separate gameplay client, or independent style/input/movement system.

Players must be able to choose familiar presets directly inside Explorer; the builder is needed only to create or modify topologies. Explorer is a topology laboratory, not a rigid-body simulation: flat cubical presentations may expose a piece's deformation or apparent disconnection.

**Non-negotiable invariant:** A successful operation preserves every constituent cell's identity and count, maps every source cell to exactly one destination, and maps distinct source cells to distinct occupied destinations. Cells may not split, merge, duplicate, disappear, or collide.

## 2. Normative precedence and authority transition

This RDS takes precedence over conflicting **Python Explorer topology behavior and historical migration-oracle expectations as product requirements**. In particular, a Python `cellwise_deformation` outcome with duplicate destinations is **not** accepted Explorer behavior. Conformance must target this RDS, not reproduce a conflicting Python golden.

This RDS changes required behavior, **not the already-transferred status of code**. Until the repository authority-transfer protocol is satisfied, the existing authority map continues to describe current implementation ownership. The intended owners after bounded transfer are:
- Versioned declarative contracts: topology schema, preset definitions, identity, and canonical serialization requirements.
- Native C++ deterministic core: topology validation, seam resolution, cell/frame/piece transport, atomic commit decisions, inverse operations, and structured diagnostics.
- Godot/GDScript: Explorer and builder interaction, draft orchestration, camera, rendering, overlays, input routing, UX, and persistence adapter.
- Python: compatibility/reference implementation for still-inherited behavior, never a veto over requirements explicitly superseded here.

Authority transfer must name the inherited scope, new owner, deterministic conformance fixtures, former-oracle differences, compatibility rules, exclusions, fallback/reversion path, updated authority map, and a `transferred` record in `docs/architecture/authority_transfer_protocol.md`. Merely committing this RDS is **not** a transfer. Purely new deterministic multi-domain semantics may require authority establishment instead of pretending Python already owned them.

The existing v1 single-domain schema and Python golden traces remain historical/compatibility authority for their inherited scope until each bounded transfer is completed. No unreviewed change to normal Play, gravity/drop/lock, collision, scoring, replay, or release support is authorized.

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

## 7. Preset catalog and mathematical labels

Presets must be accessible without opening the builder, carry stable IDs, dimension, versioned definitions, construction/validation metadata, understandable descriptions and boundary correspondences. Editing a preset always forks a custom draft.

| Family | 2D | 3D | 4D |
| --- | --- | --- | --- |
| Bounded | Bounded | Bounded | Bounded |
| Partially periodic | Cylinder | One-/two-axis wrap | One-/two-/three-axis wrap |
| Fully periodic | Torus T² | 3-Torus T³ | 4-Torus T⁴ |
| Twisted | Möbius strip, Klein bottle | Twisted face identifications | Twisted hyperface identifications |
| Projective | RP² | RP³ | RP⁴ |
| Spherical | S² | S³ | S⁴ |
| Experimental/custom | Sphere-like transport; Custom | Sphere-like transport; Custom | Sphere-like transport; Custom |

A mathematical name is a correctness claim, not just a decorative label. Existing Python `sphere_like` presets are heuristics, not verified `S^n`. Existing `projective`/RP-like profiles must be verified before they are promoted to certified named spaces. Until verification, mark them accurately as experimental/approximate while permitting structurally valid exploration.

**Spherical construction target:** use the double of an n-ball, `S^n = B^n_+ union_(boundary) B^n_-`, represented by two n-cubic domains with corresponding complete boundary identifications. In 2D these are squares; in 3D cubes; in 4D tesseracts. Domain interiors are distinct. The structure must handle edges, corners and higher-codimension intersections consistently. The flat drawing is not a claim of a globally flat spherical metric.


### 7.1 Stage T2 — mandatory 2D preset catalog

**T2 is a working single-domain Godot Explorer deliverable, not a complete surface-classification engine.** Its five core presets must be selectable in the main Explorer and execute real native topology transport. An informational gallery card cannot satisfy a runtime preset requirement.

| T2 entry | Existing Python preset candidate | Expected connected surface invariants | T2 status |
| --- | --- | --- | --- |
| Bounded rectangle / disk | `empty_2d` | Orientable; one boundary; Euler characteristic 1 | **Mandatory working** |
| Cylinder / annulus | `cylinder_2d` | Orientable; two boundaries; Euler characteristic 0 | **Mandatory working** |
| Torus `T²` | `torus_2d` | Orientable; closed; Euler characteristic 0 | **Mandatory working** |
| Möbius strip | `mobius_2d` | Non-orientable; one boundary; Euler characteristic 0 | **Mandatory working** |
| Klein bottle | `klein_2d` | Non-orientable; closed; Euler characteristic 0 | **Mandatory working** |
| Projective plane `RP²` | `projective_2d` | Non-orientable; closed; Euler characteristic 1 | **Verification-gated; experimental if not proved** |
| Sphere-like transport | legacy `sphere_2d` | Not certified as `S²` | **Experimental only; not a sphere** |

To label the projective preset **Projective plane**, prove that the actual square edge pairings, corner equivalence and discrete transport implement the claimed quotient: include vertex/edge/face identifications, orientability, Euler characteristic, two-way seam/frame transport and injectivity tests. If not verified by T2 completion, retain the structurally valid mapping under **Projective-like transport (experimental)**. Do not silently change historical IDs or block experimental exploration merely because it may deform a piece.

The current `sphere_2d` ID denotes the **old sphere-like heuristic**, not a verified sphere; retain that semantics for legacy imports. The genuine `S²` requires the two-domain ball-doubling construction of T6. Make that space discoverable as a *planned* catalog item, not an enabled T2 sphere preset.

For each mandatory working preset, test every seam direction, local-frame transport and inverse, boundary/corner cases, one-cell crossing, multi-cell crossing, valid deformation, and an invalid partial or colliding move that must reject **atomically**. Test connectivity across identified edges separately from visual Euclidean adjacency.

### 7.2 Full 2D surface-family catalog: planned, dependency-gated

The broader catalog shall reflect the classification of **compact connected surfaces** by orientability, genus and boundary count. These are planned mathematical *space classes*, not claims that a corresponding native transport profile exists in T2.

| Planned example/family | Surface class and Euler characteristic | Construction prerequisite |
| --- | --- | --- |
| Sphere `S²` | Orientable genus 0, closed; `χ=2` | Two-domain double of disk (T6) |
| Pair of pants | Orientable genus 0, three boundaries; `χ=-1` | Multi-patch / holes after T6 |
| Punctured torus | Orientable genus 1, one boundary; `χ=-1` | Verified boundary removal after T6 |
| Double torus | Orientable genus 2, closed; `χ=-2` | Connected-sum construction after T6 |
| Triple torus | Orientable genus 3, closed; `χ=-4` | Connected-sum construction after T6 |
| Dyck's surface | Non-orientable genus 3, closed; `χ=-1` | Verified crosscap construction after T6 |
| Orientable genus generator | Handles `g>=0`, boundaries `b>=0`; `χ=2-2g-b` | Canonical multi-patch genus/boundary generator |
| Non-orientable genus generator | Crosscaps `k>=1`, boundaries `b>=0`; `χ=2-k-b` | Canonical multi-patch crosscap/boundary generator |

The surface generator's parameter choice identifies a mathematical class; it does **not** by itself construct a valid cellular quotient or authorize simulated transport. Every generated cubical complex must separately pass native topology, corner-link, frame-inverse and one-to-one piece-transport validation. Unsupported generator parameters fail explicitly; the UI must not synthesize a plausible-looking, incorrectly labeled surface.

### 7.3 Higher-dimensional full catalog roadmap

Use the same registry architecture for **3D** planned examples: bounded 3-ball, solid torus, `T²×I`, `T³`, thickened Möbius strip, thickened Klein bottle, verified `RP³`, `S³`, `S²×I`, `S²×S¹`, selected lens spaces and the **ten closed flat 3-manifolds** (six orientable, four non-orientable).

For **4D**, plan bounded `D⁴`, periodic `S¹×D³`/`T²×D²`/`T³×I`/`T⁴`, Möbius/Klein × `I²`, verified `RP⁴`, `S⁴`, `S³×S¹`, `S²×T²`, `S²×S²`, Klein × `T²` and `RP²×T²`. `CP²` is long-term research, not an assumed supported cubical construction.

These named products require **validated construction operators** rather than independent hand-coded catalog rows: periodic axis wrap, tangent reversal, Cartesian product, doubling, antipodal quotient, boundary removal, connected sum, and generalized affine/group-action quotient. Not every platycosm or lens space fits the existing signed-permutation boundary model; third-/sixth-turn constructions require broader group actions and additional conformance. Do not advertise an unsupported mathematical label as executable.

**Catalog identities must be distinct:** `space_class_id` (mathematical homeomorphism type), `construction_id` (recipe and parameters) and `profile_id` (actual normalized discrete transport). Two transport profiles can represent the same space class yet give different movement. Preserve old preset/profile IDs and their semantics, particularly legacy `sphere_2d`.

### 7.4 Gallery, status and metadata contract for T2

Stage T2 supplies a compact **Explorer-local selector** and grouped **read-only gallery**, not the T3 visual editor or save browser. Group entries by:
- **Learn:** the five functioning core 2D spaces, projective status, and an accurate sphere/experimental explanation.
- **Families:** periodic versus twisted constructions and the planned orientable/non-orientable genus model.
- **Advanced:** existing valid experimental transports and explanatory mathematical status.
- **Saved:** reserved for the later T3 saved-profile lifecycle; do not claim it is implemented in T2.

Do not present a long 2D/3D/4D flat dropdown. Common **working** presets remain directly selectable in the main Explorer; an experimental preset is selectable only when structurally valid under the new transport invariant; a planned entry is informational **and not executable**.

Every catalog entry must independently record:
- dimension; stable ID; short mathematical name/description; family/group;
- `space_class_id`, `construction_id`, `profile_id` where applicable;
- schema version and exact seam/boundary correspondence;
- **availability**: `implemented`, `experimental`, or `planned`;
- **mathematical certification**: `verified`, `unverified`, or `heuristic`;
- orientability, boundary count, Euler characteristic and other invariants **only where established**;
- a versioned construction or conformance evidence reference for any verified claim.

`unknown` is preferable to a guessed invariant. A mathematical-status label is not a rigid-Play safety gate. Color is not the sole carrier of status or seam correspondence.

### 7.5 Stage T2 scope boundary and acceptance

**Included:** existing Godot Explorer extended to 2D; native single-domain cellwise transport; the five functioning core 2D presets; a verification-gated projective candidate; optional accurately labeled sphere-like experiment; immediate preset choice/grouped gallery; seam highlights, tangent orientation, crossing traces and topology-aware neighbors; exact blocked-movement reasons. Reuse existing input, renderer, camera and piece sources.

**Excluded:** the editable edge-pairing builder and save lifecycle (T3); 3D/4D active topology transport (T4); face/hyperface visual builder (T5); multi-domain spheres, holes, connected sums, genus generators, product operators and lens/platycosm realizations (T6 or subsequent dedicated stages). The catalog may describe them as planned, not enable them.

T2 cannot pass unless:
1. All **five required** 2D presets select and execute deterministic **native** transport; no decoration-only selections.
2. Successful polycube moves preserve identities, count, injectivity and frame-aware inverse; invalid one-to-many, many-to-one and partial cases reject atomically, without changing the active state.
3. At least one seam-spanning polycube genuinely deforms or appears disconnected while remaining a single identified piece; seam-aware adjacency is inspectable.
4. Every working mathematical label has matching quotient/corner and frame-transport evidence; unverified projective and sphere-like mappings remain accurately labeled, not prohibited for non-rigidity.
5. Native/Godot conformance and Python legacy-divergence expectations are explicit; old goldens are not silently rewritten.
6. Camera-relative 3D/4D movement, existing 4D basis/slice, controls, cockpit stability and separate ordinary Play behavior still pass regressions.
7. Human 2D Explorer review demonstrates discovery of the five core presets and predicted torus/Möbius edge crossings. T3's no-numeric-edit visual-construction test remains out of scope.

## 8. Topology model and canonical schema

Reuse version-1 single-domain topology contracts when expressive enough. Extend with a separately versioned **multi-domain** schema, not incompatible, silently changed v1 meanings.

The extended model requires domain IDs, rank, per-domain sizes, boundary references including domain, reversible gluing transforms, canonical signed tangent permutations, identity/normalization and strict validation. Each directed crossing must return a uniquely determined target coordinate/domain and updated local frame. Same-domain and cross-domain connections use one semantics owner.

The canonicalizer must exclude irrelevant edit ordering and user labels; equivalent descriptions must share identity under documented rules. Domain-label renaming equivalence must be explicitly specified (not guessed). Strict invalid-input behavior must survive adapters and saved-profile migrations.

Schema extension must distinguish mathematical quotient points from discrete occupied cell centers and must prevent contradictory corner/edge crossings. Unsupported multi-domain profiles must not silently fall back to bounded topology.

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

## 12. Verification and non-regression

Automated verification is required in native, Godot, schema/governance, and historical Python compatibility lanes as applicable. New behavior is tested **against this RDS**, not an artificial Python predecessor. Each fixture names the accepted contract, complete input/command/frame, expected result, and whether old parity is intentionally superseded.

Required deterministic invariants: functionality, injectivity, conservation, cell identity, reversibility including local frame, atomic failure, deterministic identity and serialization, no camera-dependent topology truth.

Required negative cases: one-to-many ambiguity, many-to-one occupancy, partially blocked piece, inconsistent inverse, invalid seam/corner/domain, undefined deformed-piece rotation, frame-dependent reversals. Required positive cases: torus wrapping without false collisions, orientation reversal, cross-axis gluing, simultaneous different seam crossings, valid deformation, apparent disconnection with seam adjacency, multi-domain crossing.

Required topology coverage: bounded/cylinder/T²/Möbius/Klein/RP²/S²; 3D periodic/twist/RP³/S³; 4D periodic/twist/RP⁴/S⁴. Mathematical-name claims require independent construction evidence. Generate reproducible small-board profile and piece property tests, including degenerate dimensions and edge/corner interactions.

Godot tests must cover 2D/3D/4D entry, presets, builder draft/undo/apply/cancel, persistence, responsive/fullscreen presentation, camera-relative 3D/4D movement, all view/basis/slice invariants, native-Godot result agreement, and normal Play isolation. Human novice acceptance must verify that users can build a 2D torus and Möbius strip, predict a seam crossing, understand visual disconnection, and select 3D faces/4D hyperfaces without guessing.

Run routed checks and the canonical full gate `CODEX_MODE=1 ./scripts/verify.sh` for implementation changes. A docs-only RDS commit can be reviewed without claiming any runtime or human acceptance.

## 13. Staged implementation and completion gates

| Stage | Deliverable | Acceptance |
| --- | --- | --- |
| T1 | Normative contract, precedence reconciliation and bounded transfer plan | No ambiguous target authority; explicit old/new behavior differences; native conformance fixtures designed |
| T2 | **2D Explorer with fuller classified preset catalog** (see §§7.1–7.5) | Five functioning core 2D spaces, projective certification gate, separately labeled sphere-like experiment, grouped catalog with dependency-gated future examples, injective/invertible native transport, human 2D comprehension review; no T3 builder or T6 multi-domain features |
| T3 | Visual 2D builder and profile persistence | Novice torus/Möbius/Klein construction without numeric permutation editing |
| T4 | 3D/4D Explorer topology transport | Shared native semantics, signed frames, camera-relative and 4D basis regressions |
| T5 | Visual 3D/4D face/hyperface builder | Full supported signed transformations through visual manipulation |
| T6 | Multi-domain schema, native transport and S²/S³/S⁴ | Mathematically justified sphere models and versioned round-trip |
| T7 | Learnability/visual acceptance and authority completion | Novice observations, full evidence, updated authority map and completed transfer records |

A stage must not claim a later stage's semantics or acceptance. Ordinary topological **games** and a full Pygame-shell migration remain separate product work; this RDS concerns Explorer and its secondary builder.

## 14. Explicit non-goals

No universal rigid playability requirement, automatic gravity/drop/lock behavior for custom topologies, continuous differential geometry, smooth embedded sphere rendering, arbitrary continuous seam rotations, certification of all custom manifolds, separate Godot topology engine, Python oracle reinvention, backend/login, research telemetry, release-matrix expansion, or unrelated UI redesign.

## 15. Final acceptance

Explorer is complete only when: 2D/3D/4D all select and traverse supported topologies; presets are immediate; builder is secondary and visual at each dimension; successful moves preserve one-to-one cell identity and are reversible; both split/merge cases are blocked; deformation/disconnection are permitted; domain-aware sphere constructions are correctly represented; full native and Godot gates, human learnability checks, compatibility migration and formal authority transfer are completed.

**Final invariant: Geometry may deform. Constituent cells may not split, merge, disappear, or multiply.**
