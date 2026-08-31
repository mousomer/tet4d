# Canonical Local Board Presentation Geometry Acceptance

Status: COMPLETE / REVIEWED GREEN

Date: 2026-08-27

Branch: `codex/canonical-local-board-geometry`

Starting HEAD: `addd0d194f8fb53f57daf03e8b48ca4dd07ee6d4`

Stage 54F-1 implementation HEAD: `d85605966ef9eb145f969a3d8e6550563c45b268`

## Stage 54F-1R Review Correction

Stage 54F-1 established the correct canonical local-board architecture, but
independent code review found a P1 domain regression: the mapper routed finite
continuous endgame particle positions through the new strict lattice-cell API.
Fractional and out-of-board 2D/3D particles, their interpolation/trails, and
derived event markers therefore collapsed to the local origin even though the
repository gates were green.

Stage 54F-1R preserves the one-owner architecture and separates its public
domains. `cell_position()` remains integral and in-board, with only the
existing explicit negative-Y active-spawn allowance. `point_position()` accepts
arbitrary well-formed finite three-axis presentation points. Both delegate to
the same canonical pitch, centring, Y inversion, and orientation formula, and
valid integral coordinates map identically through both APIs. Locked, active,
and Ghost cells use the strict path; particles and event/probe presentation
points use the continuous path. Malformed, NaN, and infinite input is rejected
before it can contaminate a transform.

The correction also replaces the former self-comparison slice-isolation test
with independently configured same-local/different-slice states, and makes
`AdaptiveLayerLayout` consume canonical `local_extent.x/y` rather than raw
semantic cell counts. Layout remains downstream and continues to own only
slice-set rows, columns, gaps, centring, and anchors.

The exact Stage 54C `SliceBasis4D` conversion is unchanged. Its pre-existing
integral coordinate validation still constrains 4D continuous replay points;
54F-1R neither weakens exact-basis semantics nor invents fractional signed-axis
rules.

## Outcome

Stage 54F-1 establishes one `LocalBoardPresentationGeometry` consumed by Live
2D, Live 3D, and every local Live-4D slice. The object owns unit cell pitch and
bounds, zero-centred local extent, cell transforms, six face-grid segment
sets, and twelve boundary segments. `TraceCoordinateMapper` is now the bounded
dimensional adapter and composition seam rather than a second geometry owner.

Semantic 2D `[X,Y]` becomes presentation-only `[X,Y,1]`. Validated 3D extents
pass directly. Live 4D derives visible extents and signed axis mapping from the
exact `SliceBasis4D`; basis coordinate reversal occurs before canonical local
mapping. `SliceLocalOrientation`, adaptive slice anchors/layout, camera fit,
labels, materials, and presentation-profile styling remain separate.

`GridRenderer` no longer recomputes flat grids, volumetric face grids, floor
lattices, or box outlines from board shapes. It converts canonical segment
descriptors to styled meshes and applies only display-face selection and small
z-fighting offsets. Live 2D cells no longer use a `0.08` thin-depth exception;
their rendered body depth matches their presentation body width while planar
camera/material treatment keeps the game visually two-dimensional.

## Structural Acceptance

| Criterion | Evidence | Result |
| --- | --- | --- |
| Canonical contract | Focused tests cover `[4,7,11]`, dimensions, unit size, 308 cells, end-cell centres/bounds, board bounds, six grid faces, twelve boundaries, and invalid zero extent. | PASS |
| Odd/even/degenerate | `[4,6,8]`, `[5,7,9]`, `[4,7,10]`, `[1,5,8]`, and `[1,1,1]` prove midpoint symmetry and non-zero one-cell bounds. | PASS |
| 2D adaptation | Mapper exposes local `[4,7,1]` with `[+X,+Y,presentation-only]`; native/canonical setup remains rank 2. | PASS |
| Full chain | 2D `[4,7]`, direct 3D `[4,7,1]`, and identity 4D `[4,7,1,1]` have equal structural snapshots and cell transforms. | PASS |
| Basis permutations | Identity and both signs of XW, ZW, and ZX turns derive asymmetric local extents/axis slots and separate slice counts from `[4,7,11,3]`. | PASS |
| Signed orientation | `ZX-` exposes `[+Z,+Y,-X]`; canonical X endpoints reverse local Z by three cells while extent remains `[11,7,4]`. | PASS |
| Discrete/continuous domains | Valid integral points agree through both APIs; real fractional 3D and finite out-of-board points map to independently derived exact values; fractional cells and malformed/non-finite points are rejected. | PASS |
| Slice isolation | Independent `[4,7,11,1]` and `[4,7,11,5]` mapper states use different slice counts and layout/spacing snapshots while retaining identical local-geometry structural snapshots. | PASS |
| Layout extent ownership | A focused internal-pitch perturbation produces canonical extent `[8,14,6]`; adaptive tile width/height and stride consume that extent rather than semantic counts `[4,7,3]`. No configurable pitch is introduced. | PASS |
| Renderer migration | Existing renderer tests retain grid counts, six cached volume faces, twelve boundaries per slice, active frames, shared `L`, cell placement, Ghost, and stable node counts; 2D adds full-depth assertions. | PASS |
| Endgame fractional production path | `TraceSceneRenderer` maps committed 2D `[-0.224,1.032]` to `[-1.724,0.468,0]` and committed 3D `[-0.192,1.016,1.048]` to `[-1.692,0.484,-0.452]`; a second particle remains distinct. | PASS |
| Out-of-board/interpolation/trail | Committed finite out-of-board coordinates map affinely; two committed particle frames interpolate to an independently derived midpoint and retain distinct trail samples. | PASS |
| Event marker | The committed 3D boundary event marker equals its mapped particle position plus only `EVENT_MARKER_HEIGHT`. | PASS |
| Strict cell regression | Renderer locked/Ghost cells and active cells use explicit strict APIs; fractional cell input remains invalid and active spawn retains only its authorized negative-Y allowance. | PASS |
| Profile compatibility | Existing default/override, grid/boundary, piece, Ghost, slice-spacing, palette/accessibility, and frozen-state profile tests pass unchanged. | PASS |
| Deterministic isolation | Existing native setup, state/hash, replay, active/next/Hold/Ghost, basis, and profile-isolation suites pass; no native/gameplay/schema source changed. | PASS |

## Real-Window Review

Evidence taxonomy: all visual evidence in this record is agent-driven. The
original Stage 54F-1 campaign and the focused Stage 54F-1R endgame pass are not
independent-human acceptance; no such claim is made.

### Stage 54F-1R focused endgame findings

The correction pass loaded committed `endgame_2d_classic` and
`endgame_3d_classic` through the production bundle loader, snapshot extractor,
`trace_replay.tscn`, and `TraceSceneRenderer` in a real Godot 4.7.1 macOS
DisplayServer window on Metal Forward+.

At half-frame interpolation, both modes reported four distinct, non-origin
particles and four non-degenerate moving trails. The 2D frame keeps ordinary
board centring/wireframe geometry unchanged while fractional particles occupy
separate affine positions. The 3D frame does the same in volume and visibly
places one boundary-event marker over its corresponding particle using the
authorized marker-height offset. The focused frames are
`stage_54f1r/2d_fractional_endgame.png` and
`stage_54f1r/3d_fractional_endgame.png` under the evidence directory below.

Environment:

- Godot `4.7.1.stable.official.a13da4feb`;
- macOS 26.6.2 (build 25G83), arm64, Apple M1 Pro;
- real macOS DisplayServer, Metal 4.0 Forward+, not headless;
- production entry scene `res://scenes/trace_replay.tscn`;
- requested 1600 x 960 window, 3456 x 2073 Retina viewport captures;
- Instrument/default presentation profile from the existing shell store;
- native fixed seed `54101`, speed 1, bounded topology, two hard drops per
  production capture; and
- agent-driven inspection, not independent human sign-off.

The final capture run exited zero with no runtime errors. Evidence is stored in
`docs/design/screenshots/canonical_local_board_geometry/`.

### 2D findings

Default `6x6`, asymmetric `4x7`, and minimum valid `4x6` boards remain
immediately readable as planar games. The one-cell presentation depth is not
perceived as a distracting slab under the accepted orthographic front-facing
camera. Piece faces remain square, active/Ghost/locked hierarchy remains
clear, the grid and outer boundary coincide with cell edges, the spawn cue
remains outside play, and framing is stable.

Intentional visible change: edge-on inspection would now reveal a full local
cell body rather than the removed `0.08` thin mesh. The normal 2D product view
is unchanged in purpose and stronger structurally.

### 3D findings

Default `6x10x6`, asymmetric `4x7x5`, and narrow `4x6x2` boards retain readable
volume depth. Rear-face subdivisions, gravity floor/lattice, and the outer
wireframe share cell-edge coordinates without half-cell drift. The Z=2
minimum remains volumetric rather than collapsing into a plane.

### 4D findings

Standard `5x10x4x4`, asymmetric `4x7x3x2`, W=1 `4x7x2x1`, and six-slice
`4x7x2x6` captures preserve coherent per-slice volumes, active/inactive
hierarchy, labels, and responsive slice-set separation. W=1 remains one local
volume. Multiple slices repeat the same local extent and grid while only the
adaptive anchors change.

An XW+ capture reports basis `[+W,+Y,+Z,-X]` and derives local `[2,7,3]` rather
than stale XYZ dimensions. A ZX- capture reports `[+Z,+Y,-X,+W]`; the negative
visible X orientation is reflected in the basis HUD and content direction
without altering board size.

### Controlled convergence

The controlled real-window frame renders three synthetic but production-
renderer inputs side by side:

```text
2D [4,7] -> local [4,7,1]
3D direct local [4,7,1]
4D local [4,7,1], one slice
```

Mode-specific labels and active-slice emphasis were suppressed. The run
reported `structural_equal=true`; the frame shows equal centring, pitch, grid
coordinates, boundary envelope, and cell locations. Remaining fill/outline
differences are legitimate material treatment. Executable snapshots, rather
than pixels, are the equality oracle.

## Verification

Passed on the final tracked implementation/documentation tree:

```text
python3 tools/governance/check_godot_settings_externalization.py
python3 tools/governance/validate_project_contracts.py
python3 tools/governance/generate_maintenance_docs.py --check
python3 tools/governance/generate_configuration_reference.py --check
python3 tools/governance/validate_godot_semantic_boundary.py
./scripts/check_git_sanitation_repo.sh
git diff --check
godot --headless --path godot/Tet4D.Godot --script res://tests/run_tests.gd
GODOT_BIN=/Applications/Godot.app/Contents/MacOS/Godot ./scripts/verify_godot_4_7.sh
CODEX_MODE=1 ./scripts/verify.sh
```

Results: project contracts checked 117 required paths; focused Godot reported
`Godot replay tests passed`; the pinned Godot 4.7.1 gate included the shared
topology transport matrix; and the full repository gate reported `verify: OK`.
Expected negative-path settings/native-input messages and existing headless
resource-teardown advisories remain non-failing.

Stage 54F-1R reran the same complete gate set on the corrected tree on
2026-08-27. The dedicated geometry/mapper/model/renderer run reported
`Stage 54F-1R focused Godot tests passed`; the full Godot suite reported
`Godot replay tests passed`; semantic-boundary validation scanned 111 scripts;
project-contract validation checked 117 required paths; the pinned Godot
4.7.1 gate passed all 59 shared topology transport cases; focused real-window
2D/3D endgame capture exited zero; and the full gate reported `verify: OK`.

## Authority, Risks, and Deferrals

Authority effect: none. This names and formalizes one implementation owner
inside already-established Godot presentation authority. Stage 54B remains
the board-validity owner, Stage 54C remains the exact-basis owner, native/
inherited systems retain gameplay authority, and no AE record is required.

Remaining advisory: independent human product review may still assess the
intentional full-depth 2D mesh under unusual camera/debug views. No ordinary
2D regression was observed. Independently, exact `SliceBasis4D` still accepts
only its established integral coordinate domain, so fractional 4D replay-point
semantics remain a pre-existing limitation outside Stage 54F-1R.

Recommended exact Stage 54F-2 scope: only separately evidenced visual polish
above this fixed geometry contract—projection/camera/material treatment or
review-driven comparison tooling. It must not add another geometry owner,
change gameplay dimensions, or merge 4D slice-set layout into local geometry.
