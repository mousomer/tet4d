# Explorer 2D surface runtime

Role: spec
Status: active implementation contract
Source of truth: this file for the 2D probe amendment and retained spherical double;
`explorer_topology_piece_transport_contract.md` for single-domain transport/rotation
Supersedes: none

## Scope and acceptance

Owner authorization: implement Möbius, Klein bottle, projective plane and genuine
sphere profiles in the existing 2D Explorer. Inherited single-domain transport
remains a candidate until the formal transfer protocol completes. The genuinely
new closed disk-double mechanics establish native ownership under `AE-0056`;
mathematical certification and human acceptance remain separate. Godot owns selectors, feedback and chart presentation. Play,
legacy Python profiles, hashes, replay and 3D/4D topology are unchanged.

Single-domain presets reuse canonical v1 paired seams: Möbius reverses the X
pair's tangent; Klein wraps X and reverses Y; projective reverses both pairs.
The existing decoder and cell-step resolver own coordinates and frame transforms.
No mathematical certification status is promoted by runtime availability.
Projective selection is explicitly experimental pending independent proof review.
Outside the three §2.5 surfaces, presets permit only the coherent-development quarter turns in the T1 piece
contract §9; mixed frames, off-chart twisted rotations and collisions reject
atomically. Recorded inverse descriptors distinguish translation from rotation.

## Topology-first selected profiles

RDS §2.5 controls Klein bottle, RP² and the normal Sphere selection. Native C++
reuses canonical v1 boundary descriptors and the existing cell-step resolver.
The bridge selects `sphere_adjacent_positive`: X− ↔ Y− + and X+ ↔ Y+ +.
It uses one square chart; no new domain system is introduced. Existing v1
cross-axis lattice transport requires equal edge lengths: nonsquare boards
report a technical representation limit and retain state, rather than
substitute another quotient. Select a square board to explore this Sphere. The existing
`sphere_double_2d` path remains compatibility-only and is absent from the normal
selector; the older `sphere_2d` catalog identity is also unchanged.

These three constructions use ordinary `explorer-piece-transport/1` state (the
former `explorer-piece-probes/1` mode is removed). Under RDS §2.5's free-cellwise amendment every cell receives the same
canonical board-axis translation. Frames accumulate across seams but never
remap subsequent translation; deformation and changed adjacency are allowed.
Recorded Undo validates provenance and restores its exact owned source snapshot.
Commit still revalidates candidates,
revisions, dimensions, frames and resource limits. No persistent session reader
or gameplay contract changes.

Acceptance is existing square-quotient analysis plus actual Godot selected-profile
checks of all four signed boundaries and tangent coordinates. Piece preservation
and comprehensive inverse recovery are not acceptance tests for this fix.
The following disk-double specification documents the retained compatibility
path only; its acceptance obligations do not gate the normal Sphere.

## Versioned spherical double

New semantic version `explorer-piece-domains/2` represents only the closed preset
`sphere_double_2d`, never a reinterpretation of historical `sphere_2d` or canonical
v1 profiles. There are exactly two identical rectangular disk domains, 0 and 1.
Each domain has a bounded canonical v1 chart. Every entire signed boundary is
glued to the same signed boundary of the other domain, preserving its tangent
coordinate. An outward normal step changes domain, retains the boundary cell
coordinate, reflects the normal component of the physical frame and preserves
the tangent component. Interior steps reuse the existing bounded resolver.
A selected unit axis step crosses at most one boundary, including corners.
The transported reverse direction is `-T a`; the domain is part of every
occupancy key, source/candidate equality and witness. Coincident coordinates in
different domains are distinct cells. Capacity is twice the chart volume.
Rotations walk across domains like translations; only overlap refuses them. Retry restores domains and frames exactly.

The continuous construction is two disks identified pointwise along their whole
boundary: each boundary link glues two half-disks to a disk, including the square
corners. The quotient is orientable, closed and has Euler characteristic 2
(two faces, four paired edges, four paired vertices). This specifies S² rather
than a smooth embedded mesh or a globally flat metric. Independent mathematical
review remains separate from these implementation/conformance claims.

## Presentation and compatibility

The bridge returns owned canonical cells, domains, frames, IDs, chart dimensions,
version and separate native-computed display cells. Single-domain rendering stays
unchanged. The spherical double renders chart A and chart B side by side with
one empty column between them; the bridge computes the display offset. The
Explorer snapshot labels both charts and explains that matching boundaries join.
Movement requests remain chart-axis requests; rendering never determines legality.
Switching profiles preserves compatible coordinates. A selection made after
seam-frame/domain traversal atomically admits the stored Retry baseline in the
destination topology and displays that recovery; it does not require a separate
Retry click. Failed destination admission preserves the source runtime. Replacement starts a fresh object in domain A.
Invalid requests and failed profile changes preserve the entire runtime envelope.
Legacy profile serialization stays v1; no persisted session reader is introduced.

## Evidence and remaining gates

Native tests cover all signed seam crossings, per-cell frames, transported
inverses, corners, extent 1/2, collision rejection, domain occupancy, malformed
versions/domains, Retry, stale/tampered candidates, coherent rotation identities
and deterministic action sequences. Godot tests cover selector availability,
bridge result ownership, display charts, neighbor queries, replacement/Retry,
Play isolation and rejected profile changes. Run the native harness, build the
extension, focused Explorer tests, pinned Godot gate and full repository gate.
Human chart/seam comprehension, independent proof review, external state DTO
serialization and inherited authority transfer remain open. `AE-0056` establishes
only the new closed disk-double mechanics. This slice implements
the bounded S² construction; T6's general multi-domain schema and S³/S⁴ remain open.

## Owner review sheet (pending)

Launch the built game with `godot --path godot/Tet4D.Godot
res://scenes/game_bootstrap.tscn`, using the pinned Godot 4.7.2 executable.
From Main Menu press E, choose 2D, then Space → Topology. Review windowed
1280×720 and 1280×800; recorded automated checks do not fill these boxes.

- [ ] Möbius: cross left/right and predict the vertical flip; top/bottom remain
  walls. Retry, make an in-chart rotation, and recover using Undo on Piece.
- [ ] Klein: left/right wraps without a flip; top/bottom reverses horizontal
  placement. Follow both seam orders and recover each with recorded Undo.
- [ ] Projective: both opposite-edge pairs reverse their tangent coordinate;
  the selector clearly marks this profile experimental.
- [ ] Sphere: identify chart A and B, cross each matching boundary, and explain
  why a cell in B is distinct from the same coordinate in A. The empty gap is
  outside the surface. Directions address chart axes; Undo reconstructs each
  cell's transported reverse rather than assuming one opposite key suffices.
- [ ] A split or mixed-frame piece either makes a valid one-to-one move or
  rejects atomically. Unsupported rotations explain that the object is unchanged.
- [ ] Retry restores position, chart domains and orientation; switching topology
  after seam traversal restores the Retry baseline with visible feedback. Replacement starts a fresh object.
- [ ] Both charts, labels and actions stay reachable at the review sizes. Play
  leaves surface practice and starts a fresh bounded session with normal timing.

Record observed failures and owner acceptance before promoting learnability or
the remaining inherited-transfer/certification gates.


## Square-surface and seam-presentation repair (2026-11-15)

Sphere and RP² enforce square admission in the native bridge. The Godot Space
panel exposes one coupled N extent within both axes' limits. Selection from a
rectangle explicitly squares and recentres with feedback; resizing preserves the
surface or rejects unchanged. Other profiles keep independent extents.

Native results expose detached enabled seam IDs, source/target axis and side,
and signed tangent correspondence from the normalized profile. The model forwards
this data; `explorer_seam_annotations.gd` draws persistent pair letters, colours
and arrowheads without deciding transport. Structural caching retains nodes
through moves. The fit envelope reserves space outside all four edges. Chart
labels use the generic BOARD_LABEL typography tokens, compatible with removal
of the separate spawn cue. No inherited movement authority is transferred.

Evidence: native bridge odd/even square admission and rejected-request state
preservation; Godot coupled controls and profile retention; annotation pairing,
arrow geometry and node-retention regressions; focused Explorer and full gates.
Human narrow/fullscreen seam comprehension remains an owner acceptance item.


Verification recorded 2026-11-15: `./scripts/build_godot_tet4d_core.sh`,
`./scripts/test_godot_tet4d_core.sh --explorer-piece-conformance`, isolated-HOME
`godot --headless --path godot/Tet4D.Godot --script tests/run_practice_explorer.gd`,
`CODEX_MODE=1 ./scripts/verify.sh` and
`GODOT_BIN="$(command -v godot)" ./scripts/verify_godot_4_7.sh` passed. The pinned
Godot gate ran 101 test scripts and 59 topology transport parity cases. The
initial shared-grid regression was fixed by moving annotations to their own
cleared rendering root; its focused renderer test and the complete gate passed.
The graphical preview could not initialize in the host environment; no human
visual acceptance is claimed.


Free-cellwise amendment verification scope: the bridge reports the native
`classification` for successful proposals, including `cellwise_deformation`.
The model renders detached result cells directly. The 8×8 owner trajectories
and deforming domino examples exercise the real bridge and model snapshot;
legacy E10 material-remapped rows stay explicitly superseded historical fixtures.


Free-cellwise verification recorded 2026-11-15: full native harness
`./scripts/test_godot_tet4d_core.sh` passed (ordinary 2D/ND, geometry, query,
topology, board extent and Explorer). The fixture/quotient module passed 78 tests.
Isolated-HOME `tests/run_practice_explorer.gd`,
`CODEX_MODE=1 ./scripts/verify.sh` and the pinned
`GODOT_BIN="$(command -v godot)" ./scripts/verify_godot_4_7.sh` all passed;
the pinned gate ran 101 scripts and 59 topology parity cases. Both owner
8×8 trajectories, mixed seam/interior deformation, rejection integrity and exact
snapshot Undo are covered. Human learnability and formal transfer remain separate.


Topology-selection recovery verification (2026-11-16): the reproduced Möbius
seam-crossing switch now succeeds. Isolated-HOME `tests/run_practice_explorer.gd`,
cockpit/typography locks and `CODEX_MODE=1 ./scripts/verify.sh` passed. Dropdown
regressions cover atomic baseline recovery with visible feedback, compatible
pose preservation, retained controls/tab selection, repeated profile choices and
rejected requests. No native movement/resolver changes or baseline updates.
