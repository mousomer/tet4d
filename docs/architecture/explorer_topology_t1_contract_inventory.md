# Explorer topology T1 contract inventory

Role: architecture audit and Session 2 decision input
Status: T1 Session 1 inventory; no runtime authority change
Baseline: `16d5151ec6d4d65f390fa2bf9f5ec96bf765fbc4`, inspected 2026-11-05
Product owner: `docs/rds/RDS_EXPLORER_TOPOLOGIES.md`, revision 2

## 1. Conclusion and evidence vocabulary

**Verified in code:** Tet4D already has the necessary single-domain seam model,
canonical v1 interchange, strict native transport decoder, provisional native
single-cell/frame resolver, bounded pose validator, geometry utilities, and
Godot Explorer/presentation pipeline. Reuse them. There is no native whole-piece
topology transaction, persistent constituent-cell/frame state, or mathematical
certification package. A loop over single-cell queries alone cannot supply those
guarantees.

**Required by RDS:** T1 must define these missing contracts before T2 implements
five functioning 2D presets and completes a bounded native transfer. This audit
completes the inventory input only; it does not complete T1's semantic/catalog
design, schema, certification fixtures, or conformance fixture specifications.

**Proposed:** extend the existing native query/transport family with an
identity-preserving piece proposal and atomic application contract. Keep the
Godot shell, geometry, profile representation and historical fixtures.

**Unresolved:** command/frame composition, sufficient inverse state, deformed
rotation, mathematical certification, and contract version boundaries are
Session 2 decisions (§12). Do not resolve them by accepting current outputs.

The four bold labels above apply throughout: **Verified in code** describes
the baseline; **Required by RDS** describes forward requirements; **Proposed**
is an implementation/transfer recommendation; **Unresolved** is not certified.
Source paths below are repository-relative. Line anchors describe this baseline.

## 2. Repository, routing and document ownership

**Verified in repository:** This inventory examines the RDS revision 2 and
repository implementation at the baseline commit recorded above. The task was
routed as a cross-layer `STRUCTURAL_CHANGE` / `staged_handoff` audit.
Representative `./gov explain` output is not the complete route set; the
inventory composes the following six applicable manifest routes:

| Route in `config/governance/project.json` | Consumed authority / layer | Evidence boundary |
| --- | --- | --- |
| `product_planning` | RDS, professional programme, backlog | Documentation and stage order |
| `topology_and_explorer` | Current Python topology authority, canonical/native contracts | Deterministic behavior inventory |
| `python_reference_engine` | Architecture contract, engine and direct tests | Reference behavior and compatibility |
| `native_deterministic_core` | `native/AGENTS.md`, authority protocol, query/transport/geometry | Provider implementation, not transferred semantics |
| `godot_product_shell` | `godot/AGENTS.md`, bounded Explorer, input/render consumers | Adapter and presentation integration |
| `governance_and_tooling` | Change/verification governance, authority validator | Documentation, handoff and authority assertions |

The audit inspected native and Godot behavior but changed documentation only;
inspection is not a runtime, mathematical-certification or authority-transfer
acceptance claim. Verification commands are in §9. Checkout state, CI results
and environment-specific policy-kit outcomes belong in the PR description,
not in this durable architecture reference.

Owner search covered the existing topology architecture and plans. The RDS
owns requirements, `canonical_topology_contract.md` owns v1 interchange,
`native_topology_transport.md` owns Stage 53B transport, and
`bounded_practice_explorer.md` owns the bounded MVP. The Stage 25
`docs/plans/topology_godot_core_port_plan.md` is historical planning, with a
broader gameplay migration and obsolete implementation-absence claims; the
piece-transform inventory is Python geometry reference. None owns the revised
T1 cross-runtime audit. This document owns findings and handoff only, and does
not repeat or replace those contracts.

## 3. Current authority and capability inventory

**Verified in code/authority map:** Python and canonical contracts retain
inherited topology and ordinary Play authority. Native query implementations
are provisional semantic ports; Stage 53B owns their checked transport only.
Godot owns the Explorer shell, controls, camera, exact basis, slices and
rendering. `authority_transfer_protocol.md` has zero active transfer records;
AE-0054 setup admission and AE-0055 Hold establish unrelated native scopes.
The planned Explorer row in `authority_map.md` does not transfer anything.

Path abbreviations used only in inventory tables: `E` =
`src/tet4d/engine/`; `N` = `native/tet4d_core/`; `G` =
`godot/Tet4D.Godot/`; `U` = `tests/unit/`. Symbols are actual baseline names.
“Inherited” means semantic ownership has not transferred, even when C++ runs it.

| Capability: exact module and symbol | Language / current semantic owner | Actual consumer, contract and tests | Reuse disposition / authority state |
| --- | --- | --- | --- |
| `E/topology_explorer/glue_model.py`: `BoundaryRef`, `BoundaryTransform.inverse`, `GluingDescriptor.canonical_geometry`, `ExplorerTopologyProfile`, `MoveStep` | Python / inherited topology | Resolver, canonical producer, presets; canonical v1; `U/engine/test_topology_domain_model.py`, `test_topology_explorer.py` | Retain model/meaning; adapt to native DTO, no transfer yet |
| `E/topology_explorer/glue_validate.py`: `validate_topology_structure`, `validate_topology_bijection` | Python / inherited topology | Resolver/preview/canonical producer; boundary ownership and extents; `U/engine/test_topology_explorer.py` | Retain reference; not a manifold classifier |
| `E/topology_explorer/canonical_contract.py`: `canonical_topology_payload`, `topology_contract_profile`, `topology_contract_identity`, `CanonicalTopologyContract` | Python / inherited v1 + declarative scalar contract | Migration fixtures and interchange; `U/engine/test_canonical_topology_contract.py` | Reuse unchanged; native normalized payload/SHA correspondence still needs design |
| `E/topology_explorer/transport_resolver.py`: `DirectedBoundarySeam`, `ExplorerTransportResolver.resolve_cell_step`, `resolve_piece_step`, `build_explorer_transport_resolver` | Python / inherited topology | Preview, sandbox, gameplay adapters; canonical v1; `U/engine/test_explorer_transport_resolver.py` | Reuse cell/frame reference; piece semantics need scoped replacement, not a second Python engine |
| `E/topology_explorer/movement_graph.py`: `neighbors_for_cell`, `build_movement_graph`, `movement_graph_rows` | Python / inherited topology | Preview/analysis; resolver-derived graph/cache; `U/engine/test_topology_explorer.py`, `test_topology_explorer_preview.py` | Retain reference and cache; avoid whole-board graph materialization for each native adjacency query |
| `E/gameplay/explorer_runtime_2d.py`: `move_piece_via_explorer_glue_2d`, `_piece_from_exact_cells`; ND equivalents in `explorer_runtime_nd.py` | Python / inherited Explorer/Play | `game2d.py`, `game_nd.py`; movement policy + placement; `U/engine/test_explorer_transport_parity.py` | Legacy/reference only; exact cell arrays can deform, but lose local frames |
| `E/core/rules/piece_placement.py`: `CandidatePiecePlacement`, `validate_candidate_piece_placement`, `commit_piece_if_legal` | Python / inherited placement | Gameplay and Explorer adapters; uniqueness/occupancy then commit; `U/engine/test_piece_placement.py` | Retain; transaction pattern to reuse, not a native cell-ID state contract |
| `E/runtime/topology_playground_sandbox.py`: `_move_sandbox_piece_explorer`, `move_sandbox_piece` | Python / inherited Pygame sandbox | Existing Playground; `topology_playground_current_authority.md`; `U/engine/test_topology_playground_sandbox.py` | Preserve UI/runtime; do not port shell or import its rigid-mode veto |
| `N/include/tet4d_core/query.hpp`: `TopologyQueryProfile`, `TopologyCellStepQueryResult`, `TopologyFrameQueryTransform`; `N/src/core/query.cpp`: `resolve_topology_cell_step_query`, `topology_neighbor_query` | C++ / inherited topology, implementation only | Checked transport and Godot axis-wrap query; `N/tests/query_core_tests.cpp`, `U/migration/test_cpp_query_parity.py` | Extend existing query family; all five profiles expressible; no native whole-piece topology API |
| `N/src/core/topology_transport.cpp`: `decode_topology_transport_profile`, `decode_topology_transport_query`, `topology_query_profile_from_transport`, `resolve_topology_transport_query` | C++ / Stage 53B implementation; Python semantics | GDExtension; `native_topology_transport.md`; `N/tests/topology_transport_tests.cpp`, `U/migration/test_topology_transport_parity.py` | Reuse strict decoder/error shape; extend for piece/frame requests |
| `N/src/core/geometry.cpp`: `canonicalize_blocks_nd`, `normalize_blocks_nd`, `translate_blocks_nd`, `rotate_blocks_nd`, `rotate_blocks_nd_around_pivot` | C++ / inherited geometry | Native sessions and Explorer bridge; `N/tests/geometry_core_tests.cpp`, `U/migration/test_cpp_geometry_parity.py` | Retain undeformed geometry; translation/normalization sort arrays, so do not infer cell IDs from output index |
| `N/src/core/query.cpp`: `piece_pose_legal_query`, `translated_piece_pose_legal_query`, `rotated_piece_pose_legal_query` | C++ / inherited placement | Explorer diagnostic + native callers; `N/tests/query_core_tests.cpp` | Reuse final canonical occupancy/bounds checks; no gravity/lock necessary; does not check identity/frame inverse |
| `N/src/godot/topology_transport_variant.cpp`: `topology_transport_value_from_variant`; `tet4d_core_api.cpp`: `topology_transport_profile`, `topology_transport_resolve_cell_step`, `topology_query_result_to_dictionary` | C++ / transport implementation | `G/scripts/native/tet4d_core_bridge.gd`; `G/tests/test_topology_transport_boundary.gd` | Extend thin checked boundary; do not put rules in Variant conversion |
| `G/scripts/presentation/practice_explorer.gd`: `begin`, `command`, `retry`, `replace_piece`, `snapshot`, `neighbors` | GDScript / Godot presentation, detached provisional native results | `trace_replay_app.gd`; bounded Explorer contract; `G/tests/test_practice_explorer.gd` | Extend adapter for 2D and native topology state/results; keep lifecycle/isolation |

## 4. Representation and identity gaps

**Verified in code:** `contracts/topology_contract_v1.json` supplies scalar
limits; `tools/codegen/generate_topology_contract.py` generates Python/C++
bindings and schema scalar limits. `config/schema/topology_contract.schema.json`
and `canonical_contract.py` define strict canonical interchange:

- Ranks 2–4; positive integer axis extents up to 1,000,000; product at most
  9,223,372,036,854,775,807. No booleans/floats/string integers.
- One implicit rectangular domain, boundaries `(dimension, axis, side)`,
  disjoint active pairs and signed tangent-axis permutations with compatible
  extents. Each pair implies both directed crossings and inverse mapping.
- Canonicalization discards disabled rows, labels, user seam IDs and order;
  reverses/inverts equivalent descriptions, sorts and assigns `seam_000` etc.
  Board extents participate in compact sorted JSON's SHA-256 identity.
- It does not encode cell state, persistent cell IDs, domains, holes/subfaces,
  arbitrary affine/continuous rotations, certification proofs, or asymmetric
  one-sided legacy edge rules. It supplies no whole-piece inverse guarantee.

`ExplorerTopologyPreset` in `presets.py` combines a historical preset ID and
profile with `group`, `mathematical_status`, `recommended_for`, `gravity_safe`
and `unsafe`. `quotient_clean`/`quotient_advanced` are metadata, not proofs.
There is no separate versioned space-class or construction identity, nor
independent availability/certification contract. A board-dependent canonical
digest already supplies a transport identity candidate; a preset ID does not.

Native `TopologyQueryProfile` contains rank/gluings, with shape supplied
separately. The transport DTO uses `contract_version/rank/dimensions/seams`
and preserves enabled rows/IDs; it is not canonical v1 JSON or a canonical
hashing API. `G/scripts/native/topology_contract_document.gd::load_payload`
only checks the document envelope, then copies it; it is not strict semantic
validation or native normalization. Do not promote it to that role.

**Required by RDS:** separate space class → construction recipe/version →
board-specific transport identity; independent availability and certification;
versioned result/reason vocabulary; persistent piece/cell/frame state and
certification fixtures. **Proposed:** keep v1 transport meaning and derive a
catalog correspondence to existing presets/digests; reserve separately
versioned domain extension for T6. **Unresolved:** exact new contract ownership,
normalization and alias rules are Session 2 work, not a schema in this audit.

## 5. Seven preset candidates

**Verified in code:** all definitions are in `E/topology_explorer/presets.py`.
For 2D every tangent permutation is `(0,)`; `+` below preserves the tangent,
`−` reverses it by `extent - 1 - coordinate`. Each pair has a generated reverse
direction through `transform.inverse()` in Python and `inverse_transform` in
native `query.cpp`; neither requires a separately authored inverse preset.

| Historical ID / definition | Exact paired edges and tangent sign | Claim and existing structural evidence | Extents, v1/native capability and specific T2 gap |
| --- | --- | --- | --- |
| `empty_2d` / `explorer_preset_sections_for_dimension` empty profile | None; all four edges bounded | Bounded rectangle/disk required by RDS; native `test_topology_queries` blocks bounded Y; canonical fixture `bounded_2d` | Any positive W,H within v1. Native empty profile works. Add 2D Explorer entry/catalog and cell-ID transaction + all wall/partial-block fixtures |
| `cylinder_2d` / `cylinder_profile_2d` → `axis_wrap_profile` | X− ↔ X+, `+`; Y bounded | Cylinder/annulus; `test_same_axis_wrap_transport_2d` checks X−→X+ and seam metadata | Any W,H. Generic native axis-wrap works. Add named catalog/construction evidence, both directions, bounded-Y transaction/inverse fixtures |
| `torus_2d` / `torus_profile_2d` | X− ↔ X+, `+`; Y− ↔ Y+, `+` | Torus; `test_torus_wrap_maps_across_x_boundary`, every-cell neighbor comparison, native X+/Y+ assertions; chart-split pair tested | Any W,H. Native two-wrap profile works. Add retained cell IDs/frames, seam-adjacent occupancy and corner/degenerate transaction evidence |
| `mobius_2d` / `mobius_strip_profile_2d` | X− ↔ X+, `−`; Y bounded | Möbius strip; `test_mobius_strip_flips_tangent_coordinate`, `test_orientation_reversal_transport_2d`; native reflected-2D parity case | Any W,H; reversal need not change a middle row. Generic reflected native seam works. Add persistent cell frames, mixed crossing/inverse and non-rigid/rotation tests |
| `klein_2d` / `klein_bottle_profile_2d` | X− ↔ X+, `+`; Y− ↔ Y+, `−` | Klein bottle; `test_klein_bottle_graph_keeps_four_neighbors_per_cell` checks `(3,0)→(0,0)` on X+ and `(1,2)→(2,0)` on Y+ for 4×3 | Any W,H. Generic native signed seams express/execute both pairs; no named whole-piece Klein acceptance. Add both seams/directions, corner/frame composition and atomic candidate evidence |
| `projective_2d` / `projective_plane_profile_2d` → `_opposite_projective_profile` | Both opposite-edge pairs, both `−` | Label “Projective Plane”; description says RP²-like. `test_projective_directed_crossings_roundtrip_entire_boundary` proves coordinates, not RP² | Any W,H structurally. v1/native signed seams suffice. Optional experimental transport only until edge/vertex, local links, χ/orientability/boundary proof; certification **Unresolved** |
| `sphere_2d` / `sphere_profile_2d` → `_sphere_like_profile` | X− ↔ Y−, `−`; X+ ↔ Y+, `−` | Label already “Sphere-Like Transport”, `transport_heuristic`; `test_sphere_like_transport_routes_cross_axis_seams_consistently` checks traversal/reverse | W=H required by tangent extents; 5×4 rejection tested. Generic native cross-axis resolver can execute compatible profile; no sphere proof. Optional heuristic only; collisions can block; genuine sphere stays T6 |

**Unresolved certification:** no inspected test constructs quotient vertices,
edge classes, local links, orientability and Euler/boundary evidence together.
The five core recipes correspond to the RDS's intended surfaces, but this
inventory does not promote them to certified catalog records. Tests above
prove discrete behavior, not mathematical recognition. For projective and
sphere-like candidates the mathematical name is explicitly unverified/heuristic.

All five core profiles fit v1 without semantic changes. Extent 1 is accepted
by v1, including self-neighbor steps on wrapped axes; transport degeneracy is
not proof that the underlying construction changes mathematical class. Define
small-board resource/availability rules and duplicate-neighbor presentation
separately from construction certification. No parity/native test found covers
all five named profiles, both directions and degenerate cases as one package.

### Continuous quotient analysis of the legacy `sphere_2d` construction

**Verified in code:** `presets.py::_sphere_like_pairs(2)` pairs X−
with Y− and X+ with Y+; `_sphere_like_profile` uses the reversing tangent
transform `_reverse_flip_transform(1)` for both pairs. This is a
*continuous-boundary-quotient analysis*, not a certification of the discrete
cell-center transport or of the preset's mathematical name.

Label the square vertices A=(0,0), B=(L,0), C=(L,L), D=(0,L).
Under the two reversed tangent identifications, the endpoint pairs are:

- X− ↔ Y−: A ~ B and D ~ A.
- X+ ↔ Y+: B ~ C and C ~ D.

Thus all four corner vertices have one equivalence class. In the standard
polygonal quotient cell count this gives `V=1, E=2, F=1` and
`χ=V−E+F=0`. Both glued edge pairs agree with the oriented square's
boundary traversal, so the candidate is non-orientable. **If the
vertex-link/manifold checks pass**, the standard compact connected
closed-surface classification identifies this quotient as a *Klein bottle*,
not `S²`. The prior sphere-like label is therefore not supported by this
continuous gluing calculation.

Using tangent sign `+` on both adjacent-edge pairs instead yields three
vertex classes and `χ=2`, consistent with the usual one-square
sphere construction. This is an **investigation comparison only**:
changing a legacy sign would change historical profile/transport semantics
and is not authorized by this audit. The RDS's T6 two-domain ball-double
remains the intended certified sphere delivery. A mathematical sphere need
not in general require two domains; that is the project's chosen T6
construction and versioning boundary.

**Unresolved:** independently verify vertex links and orientation under the
canonical continuous construction, and keep those proof objects distinct from
discrete seam inverses, cell-center occupancy and polycube movement. Add
certification fixtures in Session 2; neither preset-name metadata nor the
4×4 collision witness proves a homeomorphism type.

## 6. Python divergences and transaction findings

**Verified in code:** `transport_resolver.py::ExplorerTransportResolver.resolve_piece_step`
(baseline line 637) computes every `CellStepResult` before returning a
`PieceStepResult`. Any blocked cell blocks the piece. The function's
duplicate-destination branch (baseline lines 662–669) instead returns
`CELLWISE_DEFORMATION` with the duplicate coordinate tuple. For example, an
executed read-only probe of `sphere_profile_2d()`, board 4×4, cells
`((0,3),(1,0))`, command X− returned
`cellwise_deformation`, `((0,0),(0,0))`. This is a valid seam profile with an
invalid particular movement, not evidence that all sphere-like moves fail.

| Existing behavior / exact evidence | Required by RDS | Classification and proposed disposition |
| --- | --- | --- |
| Resolver duplicate-target branch above; `PieceStepResult.__post_init__` checks rank/kind/cell-step count, not destination uniqueness or moved/source count equality | `blocked`, `destination_collision`; preserve complete prior state | Intentionally superseded for new Explorer. No direct duplicate-target resolver regression was found in inspected tests; add one with explicit old/new comparison, rather than inventing a conflicting golden |
| Sandbox `_move_sandbox_piece_explorer` rejects `len(set(moved_cells)) != len(moved_cells)`; `piece_placement.py::validate_candidate_piece_placement` rejects duplicate locations | Same invariant at native proposal boundary, consistently reported | Valid safeguards unchanged; reuse their regression intent. Resolver success must not depend on a later UI consumer catching collapse |
| 2D gameplay under `CELLWISE_FREE`: `explorer_runtime_2d.py::move_piece_via_explorer_glue_2d` passes the duplicate `moved_cells` to `_piece_from_exact_cells`, constructing a temporary `PieceShape2D` with coincident blocks; `game2d.py::_try_commit_candidate_piece` routes through `commit_piece_if_legal` to `piece_placement.py::validate_candidate_piece_placement`, which rejects duplicate occupancy | Return a blocked `destination_collision` **before** constructing a candidate shape or exposing successful transport; leave whole state unchanged | Legacy gameplay's later rejection is effective for commit but does not repair the resolver's success classification. T2 fixtures must check resolver, gameplay-consumer/compatibility, and native proposal boundaries separately |
| `test_torus_chart_split_piece_step_stays_rigidly_coherent` expects deformation with `(0,0),(0,1)` → `(0,3),(0,0)` | Valid one-to-one apparent split allowed | Valid unchanged behavior; taxonomy/coherence terminology needs clarification, not a rigid-only filter |
| `test_sandbox_forced_rigid_mode_blocks_cellwise_projective_cases_across_dimensions`; runtime `RIGID` policy rejects non-coherent deformation | Valid deformations remain permitted in forward Explorer | Legacy compatibility test; retain Pygame/Play expectation, add separate native RDS conformance |
| `topology_playability_signal.py` keeps `validity=valid` even when `rigid_playability=blocked`, but scans deformation to choose rigid policy | Structural validity, catalog certification and per-command legality independent | Existing separation is useful. Do not use `unsafe`, gravity safety or rigid scan as catalog-wide Explorer rejection |
| Python cell resolver returns identity+translation frames for interior movement; native `query.cpp::resolve_topology_cell_step_query` (baseline line 387) returns target with absent frames; current topology parity cases cover seam crossings and a blocked boundary, not successful interior frames | Full composed local-frame state must be well-defined for every successful action | Additional coverage/contract required; define absent-frame semantics without silently changing the legacy DTO |
| Python `frame_transform` uses normal sign −1; `piece_frame_transform` uses exit/entry sign relation; Möbius X crossing gives coordinate signs (−1,−1), piece signs (+1,−1) | Frame meaning and inverse defined explicitly | Additional coverage/contract required; choosing the coordinate map as a persistent physical frame would be unjustified |
| `TestStage35TopologySemantics` permits Explorer Y seam but blocks Play drop; `play_move_intents.py` classifies those intents separately | Explorer isolated from gravity/drop/lock | Valid unchanged; do not route new Explorer through gameplay drop legality |

**Verified state/atomicity answers:**

- Python `ActivePiece2D` stores shape/position/rotation; `ActivePieceND` stores
  shape/position/relative blocks. Sandbox stores origin/local blocks. These can
  represent arbitrary separated cell coordinates, but have no persistent cell
  IDs or independently accumulated local frames. `cell_steps` records one
  proposal's correspondence; rebuilding exact cells discards its frames.
- Native `CoordND` arrays and `TopologyCellStepQueryResult` likewise have no
  constituent identity or persistent frame accumulator. A single affine
  `TopologyFrameQueryTransform` cannot represent different cell-local frames.
- Candidate calculation is already pure in Python resolver and native queries.
  Python `commit_piece_if_legal` validates before assignment; sandbox computes
  and rejects before writing origin/blocks; Godot `command` assigns `cells`
  only after native pose validation. No incremental earlier-cell mutation was
  found on these paths. The missing guarantee is full state/trace/frame atomicity,
  not evidence of a currently observed partial mutation.
- Native `piece_pose_legal_query` checks duplicate integer coordinates,
  canonical bounds and occupied cells; it neither merges opposing boundary
  columns nor requires connectivity. Canonical profile normalization does not
  canonicalize occupied coordinates modulo `extent - 1`. A torus's X=0 and
  X=W−1 remain distinct sites when W>1; wrap occurs on exiting, not occupying,
  an edge cell. Boundary-point quotient certification must remain separate.
- Inverse seam tests choose the target boundary's **outward** step. Its
  `entry_step` points inward and is not the reverse command. Tests restore
  coordinates; no inspected persistent piece state checks accumulated frames
  and operation inverse after a sequence of mixed crossings.
- Godot Retry restores its `_initial` coordinate array, not a mathematical
  inverse. There is no Explorer transport Undo/history API. **Unresolved:**
  whether transported frames alone suffice for each supported command or
  an inverse descriptor/history is necessary. RDS allows necessary history;
  opposite camera-relative keys are not an inverse contract.

## 7. Native API reuse and extension map

**Verified in code** mappings, with **Proposed** extensions:

| RDS conceptual operation | Existing provider | Classification / architectural action |
| --- | --- | --- |
| `validate_profile` | `decode_topology_transport_profile`; Python canonical producer/parser; shared generated scalars | Implemented requiring extension: strict DTO validity exists; canonical normalization/identity and mathematical certification are different operations. Reuse decoder and define canonical correspondence |
| `query_boundary_pair` | Private native `glue_for_source_boundary`; Python public `seam_for_boundary` | Native implementation available only through unsuitable private abstraction. Expose a checked read-only correspondence result from existing lookup, not another seam engine |
| `query_neighbor` | `resolve_topology_cell_step_query`, checked `topology_transport_resolve_cell_step` | Implemented requiring frame/result extension for persistent state; reuse exact cell destination machinery |
| `query_seam_preview` | Single-cell result already carries seam ID, boundaries, entry step and both frame maps | Implemented requiring extension: source/target correspondence can reuse this result; preview-specific endpoint/orientation payload needs a contract, no Godot recomputation |
| `propose_piece_action` | Python `resolve_piece_step`; native geometry + pose validator only | Available only in Python for seam-aware piece classification, with incompatible collision semantics. Missing native identity/frame-aware transaction: compose native cell resolver and validation in core query family |
| `apply_validated_action` | Python atomic placement; Godot detached coordinate assignment | Available only through unsuitable abstractions. Define native validated candidate/state binding and commit/no-op semantics; no new gameplay session or per-cell Godot commit loop |
| `query_topology_adjacency` | Native `topology_neighbor_query` returns ordered ±axis steps; Python `neighbors_for_cell` | Implemented requiring extension: expose generic checked profile query and map results to persistent piece IDs/relationships. Decide self/duplicate edge representation; avoid a second graph engine |

**Required by RDS / proposed flow:**

```text
Godot semantic action + existing camera/control-frame mapping
    ↓ checked GDExtension request (profile identity, full piece state, action)
existing native profile validation + canonical correspondence
    ↓ existing cell resolver / undeformed geometry, candidate only
identity + count + functionality + destination uniqueness + frame/inverse checks
    ↓ blocked(reason), or validated candidate bound to source/profile revision
native atomic application → complete new piece state (or exact no-op)
    ↓ thin result adapter
Godot cells/overlays/feedback; camera, basis, slice and draft remain separate
```

**Unresolved:** stateful native handle versus immutable value-state application,
candidate invalidation and deterministic revision/identity binding, per-cell
inverse descriptors, and state serialization. Do not let stale preview results
commit after topology/piece changes. No current native API satisfies the full
diagram merely because it returns a legal pose.

## 8. Godot integration and rendering reuse

**Verified in code:** `G/scenes/game_bootstrap.tscn` uses
`G/scripts/app/trace_replay_app.gd`. Main-menu Explorer/E routes to
`_start_practice`; `_practice_action` and `_refresh_practice_snapshot` reuse
the live viewer. `_start_practice` currently chooses only Live 3D/4D;
`practice_explorer.gd::begin` rejects rank 2. The panel has only dimension_3/4
buttons. Its native catalogue path is `live_nd_production_piece_catalog`;
native `plain_piece_catalog.cpp` already has production 2D geometry, but a
matching 2D Explorer catalogue adapter is still needed.

| Existing owner / actual call path | Reusable behavior | T2/later integration gap |
| --- | --- | --- |
| `trace_replay_app.gd::_live_3d_command`, `_live_4d_command` → `_practice_action`; `ControlFrameMapping.translation_command` / `rotation_command` | Camera-relative keyboard intents; canonical panel buttons; view/semantic separation | `_live_2d_command` currently goes straight to gameplay; add practice routing and action-name adaptation: existing 2D mapping emits `move_left/right`, practice parser expects `move_x_neg/pos`; do not create a new control frame |
| `G/scripts/input/live_input_contract.gd::practice_piece_control_groups`, `practice_view_control_groups`; `live_piece_control_strip.gd::configure` | Shared semantic descriptors, live bindings and dynamic labels | Extend applicability for 2D topology actions; keep exact modifiers and node/tab/scroll stability |
| `practice_explorer.gd::command` → bridge geometry → `native_piece_pose_diagnostic` | Candidate-before-assignment and bounded rejection | Replace bounded coordinate-only route for new 2D topology actions with native whole-piece proposal/application; keep 3D/4D bounded baseline |
| `practice_explorer.gd::neighbors` → `query_topology_axis_wrap_cell_step(..., [], ...)` | Native neighbor routing | Empty wrapped-axis list is bounded-only; use generic checked topology query for selected profile |
| `practice_explorer.gd::retry`, app `_reset_view`, `SliceBasis4D.free_inspection`, `_practice_action` slice branch | Retry independent of view; all six basis planes; separate slice/camera state | Retry must include IDs/frames/inverse state; keep reset/basis/slice isolation. Higher-dimensional transport is T4 |
| `G/scripts/rendering/trace_scene_renderer.gd` active-cell loop; `board_presentation_model.gd`; `local_board_presentation_geometry.gd` | Per-coordinate cell rendering and existing 2D/3D/4D projection/geometry | No whole-piece rigid mesh requirement found. Add stable IDs, frame/trace/seam overlays; current node basis is shared presentation basis, not a transported per-cell frame |

The renderer explicitly notes exported cells lack stable IDs and therefore
does not invent interpolated paths (`trace_scene_renderer.gd:302`). It can draw
separated cells now; shared membership/identity and correspondence are missing.
The practice adapter copies position/color arrays and sorts through native
geometry; `selected_cell` is an index, not an identity. No duplicate inherited
seam solver or polycube rotation implementation was found in the scoped Godot
path: it delegates to native. Control-frame math and slice projection are
Godot presentation authority, not duplication to remove.

**Required by RDS:** topology selection, seam highlight/preview, identity/trace
and adjacency overlays, blocked explanation, and explicit incompatible-pose
recovery. These integrations are absent from bounded practice. Preserve native
gameplay hash/queue/RNG isolation; Play still creates a fresh bounded session.
Builder drafts/editor Undo are T3+, not a reason to redesign the existing UI.

## 9. Tests, fixtures and comparison boundaries

**Verified in code:** representative assertions were read, not inferred from
filenames. Paths below use §3 abbreviations. Actions classify future coverage;
none authorizes deleting/rebaselining a historical fixture.

| Requirement | Existing test / fixture owner | Current expectation | RDS expectation | Action |
| --- | --- | --- | --- | --- |
| Profile normalization/identity | `U/engine/test_canonical_topology_contract.py::test_equivalent_order_direction_ids_and_disabled_rows_normalize_identically`, board-dim identity test; `tests/fixtures/parity/canonical_topology_contract_v1.json` | Equivalent seam descriptions same payload/hash; board changes identity | Preserve v1; catalog identities separate | Valid unchanged; add cross-language identity/catalog correspondence |
| Strict scalar acceptance | `U/engine/test_topology_contract_validation.py`; `N/tests/topology_contract_foundation_tests.cpp`; `U/migration/test_cpp_topology_contract_foundation.py` | Reject coercible scalar values; generated fingerprint agreement | Same strict boundary | Valid unchanged; retain generator check |
| Gluing/extents/inverses | `U/engine/test_topology_explorer.py::test_validation_rejects_duplicate_boundary_ownership`; `test_contract_rejects_non_bijective_cross_axis_dimensions` in canonical tests; resolver projective full-boundary roundtrip | Structural pairing, inverse coordinates, extents | Same plus separate certification | Valid unchanged; add edge/vertex/link certification fixtures |
| Cell seams and reversal | `U/engine/test_explorer_transport_resolver.py` wrap/Möbius/cross-axis/reverse tests; `N/tests/query_core_tests.cpp`; `U/migration/test_cpp_query_parity.py::test_cpp_topology_queries_match_python_resolver` | Exact targets, boundaries and seam frames for selected cases | All five presets, all directed edges/corners, accumulated piece frames | Needs additional coverage; preserve selected-case parity |
| Rigid/non-rigid classification | Resolver torus chart split and projective rigid pair; `U/engine/test_explorer_piece_transport.py`; `test_explorer_transport_parity.py` | Translation, rigid map, cellwise deformation; some “rigidly coherent” splits | Injective deformation allowed | Valid unchanged examples; investigate taxonomy/coherence versus persistent frame |
| Duplicate destinations | Native `test_legality_queries`; `U/migration/test_cpp_query_parity.py` case `bounded_2d_duplicate`; Python placement validator | Duplicate pose illegal, but topology resolver classifies collision as deformation | Block at proposal with collision reason | Add direct topology regression using §6 witness; preserve bounded legality and historical resolver comparison |
| Atomic rejection | `U/engine/test_piece_placement.py::test_shared_commit_is_atomic_when_candidate_collides`; `test_explorer_transport_parity.py::test_atomic_seam_move_matches_explorer_sandbox_and_gameplay_2d` and ND; Godot model wall rejection | Pose/current_piece unchanged on rejected candidate | IDs, frames, history/trace/revision unchanged too | Needs additional coverage: partial-cell block, inverse failure, stale candidate and all state fields |
| Rigid mode / Play isolation | Sandbox forced-rigid projective and torus tests; resolver `TestStage35TopologySemantics`; `U/engine/test_unsafe_topology_correctness.py` | Legacy rigid policy and Y drop distinction | Native Explorer permits valid non-rigid; Play unchanged | Legacy compatibility; supersede only Explorer veto, preserve drop/Play tests |
| Checked GDExtension | `G/tests/fixtures/topology_transport_v1.json`; `G/tests/test_topology_transport_boundary.gd`; `U/migration/test_topology_transport_parity.py`; `N/tests/topology_transport_tests.cpp` | Reject boolean/float/string integers, bad rank/permutation/dims; exact error code/path and selected targets | Same checks plus piece state/result transport | Valid unchanged; extend alongside new contract, not via permissive document wrapper |
| Godot interaction/camera | `G/tests/test_practice_explorer.gd::_model_contract`, `_check_view_and_replacement`, `_check_y_view_controls`, `_check_layout_stability`; `test_control_frame_mapping.gd` | 3D/4D native movement/rotation, bounded no-op, inverse/four-turn, camera-relative dispatch, retry, slices, hash/queue and layout isolation | Preserve and add 2D/selected topology + identity/frame integration | Needs additional coverage; existing relative oracle reuses adapter and is not independent topology proof |
| Historical transport/gameplay | `tools/migration/export_topology_trace.py`, `trace_cases.py`; `migration/golden_traces/topology/` and `gameplay/`; `U/migration/test_topology_trace_export.py` | Historical Python labels, traces, Sandbox/Play behavior | Historical readability + explicit new-contract comparison mode | Legacy compatibility; do not rewrite goldens or reinterpret old sphere IDs |
| Inverse identity, split/merge ambiguity, deformation rotation and certification | No full native piece-state/certification package in inspected providers/tests | Not established by single-cell or geometry parity | Full transaction inverse; one-to-many/many-to-one blocked; rotation either well-defined or rejected | Missing evidence/contracts; Session 2 must specify fixtures before T2 implementation |

The canonical JSON fixture is owned by Python canonical-contract tests;
native query parity inputs are constructed in `query_core_tests.cpp`, not
automatically read from that JSON. The transport-v1 JSON is shared by Python
and Godot boundary tests; `tools/migration/compare_topology_transport.py`
compares exported boundary acceptance/errors, not a whole-piece engine.
Generated bundle/asset trace copies are not primary golden owners.

Real commands, from repository scripts (not CMake/ctest):

```sh
./scripts/test_godot_tet4d_core.sh
./scripts/verify_focus.sh --docs --pytest tests/unit/engine/test_canonical_topology_contract.py tests/unit/engine/test_topology_explorer.py tests/unit/engine/test_explorer_transport_resolver.py tests/unit/engine/test_explorer_transport_parity.py tests/unit/engine/test_piece_placement.py tests/unit/migration/test_cpp_query_parity.py tests/unit/migration/test_cpp_geometry_parity.py tests/unit/migration/test_topology_transport_parity.py
./scripts/build_godot_tet4d_core.sh
./scripts/verify_godot_4_7.sh
git diff --check
CODEX_MODE=1 ./scripts/verify.sh
```

The native script builds/runs core, geometry, query, scalar-foundation,
transport and board-extent tests. Build before migration parity tests: those
pytest tests skip if binaries are absent. Build the GDExtension with the named
build script before the pinned Godot wrapper runs boundary export/comparison
and product tests against the extension in its managed
copy; focused Explorer runner is `tests/run_practice_explorer.gd` with the
resolved Godot executable. The full repository gate runs governance, Python
tests, stability, compile and benchmark checks; it does not itself establish
all Godot/native or human acceptance. Exact outcomes belong to this PR's
verification record; commands listed here are not claimed as passed.

## 10. Candidate T2 authority transfer (prose only)

**Proposed:** one coherent transfer of **deterministic single-domain 2D
Explorer topology transport and queries**. Seam interpretation, cell frames,
piece proposals and invariants must share a normative contract and lifecycle;
splitting them into individually promoted pieces risks a period with two truth
owners for one command. No second transfer is justified by the current API
inventory. Reassess if Session 2 identifies an independent semantic predecessor;
do not include gameplay or higher dimensions to simplify record keeping.

| Protocol field / concern | Candidate description; not an active AT record |
| --- | --- |
| Current authority | Python `glue_model`, `glue_validate`, `transport_resolver`, movement graph and Explorer adapters under inherited canonical v1; forward differences governed by Explorer RDS |
| Candidate authority | Native deterministic core query/transport family; declarative contracts retain data identity; Godot retains presentation |
| Exact behavior | 2D Explorer profile/seam interpretation, signed local-frame/cell transport, whole-piece proposal/application, conservation/functionality/injectivity/inverse/atomicity, classification and stable blocked reasons, read-only boundary/preview/adjacency queries. Include only defined Explorer rotation/development behavior, not general gameplay rotation authority |
| Reference implementation | Existing Python cells/seams and versioned v1 contract for unchanged behavior; RDS §§5–8 plus Session 2 normative contracts for intentional differences. Preserve both reference inputs and expected new outputs |
| Normative differences | Duplicate-target deformation becomes collision-blocked; no legacy rigid-Play catalog veto; persistent cell IDs/frames and inverse checks; undefined deformed rotation rejected locally. No claim of blind Python parity on these cases |
| Conformance fixtures | Five-core normal/seam/both-direction/corner/degenerate cases; seam-adjacent occupancy, mixed cell frames, valid deformation, partial block, duplicate target, ambiguity, inverse mismatch, rotation and repeat/apply/Retry tests. Each names profile/board, source IDs/locations/frames, command, exact output or reason, inverse and comparison mode. Session 2 must write full specifications; none is fabricated here |
| Compatibility | Keep v1 schema/digests, historical preset meanings, goldens, traces/replays and independent Pygame/Play paths. New Explorer state/result/catalog version boundaries explicit. Keep generic native 3D/4D query compatibility; additions must not silently change all-rank outputs |
| Exclusions | Ordinary 2D Play, gravity, soft/hard drop, lock/clear, score, queue/RNG, gameplay replay/hash; Python Playground UI; inherited 3D/4D topology (T4); multi-domain/generators/spheres (T6+); Godot camera, basis, slice, rendering and builder draft |
| Comparison/verification | Run existing native tests, focused Python parity/legacy fixtures, generator/schema/docs/authority validators, pinned Godot boundary + Explorer isolation tests, full repository gate. Add a specified exact RDS-conformance comparison for changed outputs; no such runnable piece harness exists yet. Terminal transfer needs concrete fixture paths, commands/results and human T2 review, not this proposed list |
| Fallback/reversion | Before promotion, preserve bounded MVP and disable unavailable 2D feature on provider failure. After promotion, safe-fail exact no-op for malformed/unsupported requests; no silent switch to conflicting Python cellwise behavior. Roll back bounded transfer record/map/feature together to prior bounded-only product; retain versioned data readers and old traces |
| Required map/record update | At T2 acceptance, narrow the inherited topology row by exact 2D Explorer exclusion, add terminal AT reference and precise native row, preserve Play/3D/4D rows and presentation owner. Record substantive protocol fields and status `transferred` only after evidence; keep all active tables unchanged now |

**Verified in code:** `tools/governance/validate_authority_transfer.py` parses
the active tables, validates required fields/statuses, checks terminal map
mentions and scans dangerous claims. It does not execute comparison commands
or prove fixture semantics. Placeholder nonterminal rows are also rejected.
That supports a prose candidate here until Session 2/T2 evidence is concrete.

## 11. Ranked risk register

Each row states **Verified in code** evidence and **Proposed** containment;
unresolved semantics remain decisions rather than implemented behavior.

| Rank / risk | Evidence and consequence | Containment / stage / blocking boundary |
| --- | --- | --- |
| 1 — B/C: no identity/frame-aware reversible transaction | Resolver collision witness (§6), coordinate-only active pieces, sorted native translation, per-step frames discarded. A legal coordinate set alone cannot prove conserved correspondence or exact inverse state | T1 Session 2 defines indexed cell state, frame composition, action/inverse and candidate binding; T2 implements whole-piece validation. Blocks T1 contract completion and T2 acceptance, not this inventory |
| 2 — D: rotation after deformation | Exact-cell Python reconstruction and native bounds/centroid-based pivot operate on Euclidean coordinates; no local-development contract | Define unique anchor/development and inverse or `rotation_undefined`; retain undeformed geometry. T1 decision/T2 implementation blocker for permitted deformed rotations; never ban the entire topology |
| 3 — A: discrete bijection mistaken for quotient proof | Preset mathematical flags and seam roundtrips; no vertex/link/χ proof package | Separate certification from runtime availability. T1 specifies evidence, T2 certifies five core recipes; optional projective/sphere names remain gated. Core certification blocks T2, genuine sphere stays T6 |
| 4 — E: runtime implementation confused with transfer | Native resolver/Godot use exists, active transfer table empty; older port plan makes broader ownership claims | Use current map/RDS/protocol, one narrow prose candidate now; terminal T2 record after comparison. Blocks T2 acceptance; no guard modifications |
| 5 — F: shared v1/query behavior changed across dimensions | One native decoder/query family serves rank 2–4; canonical IDs and historical traces shared | Add explicit Explorer state/result contract boundary and legacy comparison modes. Do not rebase goldens or repurpose sphere IDs. T1 compatibility design, T2 regression blocker; T4 separate |
| 6 — H: visible split loses membership/trace | Renderer already draws independent cells, but snapshot has only position/color and a shared presentation basis; no stable-ID animation | Extend snapshot/overlay contract over native cell IDs; do not make rendering a rigid-body validator. T1 interface/T2 integration and human comprehension gate |
| 7 — G: second engine/API introduced unnecessarily | Existing generic resolver, signed frames, pose checks, strict Variant boundary and control descriptors | Extend those owners; expose private seam lookup/query as needed, no Godot topology math or parallel core. T1 design review/T2 implementation containment |
| 8 — integration/admission confusion | Practice rank 2 rejected; live setup admission AE-0054 bounded-only, no matching 2D practice catalogue path | Keep detached Explorer state separate from live Play admission/session transitions; reuse 2D rendering/catalog source through an explicit adapter. T1 interface decision/T2 integration blocker; do not broaden AE-0054 |

## 12. Session 2 decisions and required inputs

These are **Unresolved** design tasks for the next agent, ordered by dependency;
they are not questions requiring the owner to choose implementation guesses.

1. **Identity, frames and command inverse.** Specify persistent IDs independent
   of geometry sorting, complete cell state, coordinate-map versus piece-frame
   meaning, composition order, and whether commands are global, anchor-local or
   per-cell-local after input mapping. Define the inverse and any necessary
   history without assuming independent cell steps form a reversible action.
   Inputs: resolver lifting/inverse code, native `query.cpp`, geometry sorting,
   §6 collision and torus split witnesses, RDS §§5–6. Include repeat sequences
   across Möbius/Klein seams with different cell frames and extent-1 cases.
2. **Rotation and corner semantics.** Specify coherent local development,
   anchor/pivot selection, ambiguous paths/higher-codimension crossings and
   exact failure behavior. Preserve existing undeformed native rotation;
   reject only the undefined command. Inputs: native geometry pivot helpers,
   reverse outward-step tests, mixed-crossing candidates. Resolve which
   topology/extent/action combinations are representable before promising them.
3. **Three identities and certification.** Specify versioned catalog/recipe
   correspondence to unchanged v1 digests/aliases; independent availability,
   certification and unknown invariants. Write edge/vertex equivalence and
   local-link/χ/orientability/boundary fixture specifications for the five core
   constructions. Investigate projective separately. Check §5's legacy
   `sphere_2d` corner equivalences (`χ=0` with reversed tangent signs) and
   vertex links against a `+`-sign sphere construction; keep the historical
   sphere-like profile heuristic regardless of the proof outcome.
   Inputs: exact §5 definitions, canonical normalization/scalar limits, RDS §7.
   Do not certify by preset metadata or merge boundary vertices with occupancy.
4. **Native request/state/result contract.** Decide immutable values versus
   state handle, validated-candidate lifetime/source binding, strict decoding,
   stable result/reason vocabulary, full-state Retry/Undo/serialization and
   adjacency self/duplicate edges. Map extensions to §7 existing providers;
   name deterministic/data/presentation owners and explicit version envelopes.
   Inputs: checked transport errors, null interior frames, Godot snapshots and
   2D action/catalog/admission adapters. No new schema until these are settled.
5. **Fixture and transfer package.** Turn RDS §7.5 and §10's candidate into
   precise five-core positive/negative fixture specifications, old/new
   comparison classifications and rollback steps. Retain legacy goldens and
   separately assert revised conformance. Decide concrete harness/fixture paths
   and authority-map edits before creating a substantive active record at T2.

Session 2 exits with reviewed semantic/catalog/API and fixture specifications,
remaining mathematical unknowns explicit, and the candidate transfer complete
enough to implement. It does not start T2, transfer 3D/4D, change gameplay,
invent a surface generator or bypass the authority guard.
