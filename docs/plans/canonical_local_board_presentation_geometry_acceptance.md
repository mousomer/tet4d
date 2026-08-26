# Canonical Local Board Presentation Geometry Acceptance

Status: COMPLETE / LOCAL AGENT-DRIVEN ACCEPTANCE GREEN

Date: 2026-08-26

Branch: `codex/canonical-local-board-geometry`

Starting HEAD: `addd0d194f8fb53f57daf03e8b48ca4dd07ee6d4`

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
| Slice isolation | Every layer lookup under each basis returns the same canonical local geometry; slice index affects only anchor/content/presentation. | PASS |
| Renderer migration | Existing renderer tests retain grid counts, six cached volume faces, twelve boundaries per slice, active frames, shared `L`, cell placement, Ghost, and stable node counts; 2D adds full-depth assertions. | PASS |
| Profile compatibility | Existing default/override, grid/boundary, piece, Ghost, slice-spacing, palette/accessibility, and frozen-state profile tests pass unchanged. | PASS |
| Deterministic isolation | Existing native setup, state/hash, replay, active/next/Hold/Ghost, basis, and profile-isolation suites pass; no native/gameplay/schema source changed. | PASS |

## Real-Window Review

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

## Authority, Risks, and Deferrals

Authority effect: none. This names and formalizes one implementation owner
inside already-established Godot presentation authority. Stage 54B remains
the board-validity owner, Stage 54C remains the exact-basis owner, native/
inherited systems retain gameplay authority, and no AE record is required.

Remaining advisory: independent human product review may still assess the
intentional full-depth 2D mesh under unusual camera/debug views. No ordinary
2D regression was observed.

Recommended exact Stage 54F-2 scope: only separately evidenced visual polish
above this fixed geometry contract—projection/camera/material treatment or
review-driven comparison tooling. It must not add another geometry owner,
change gameplay dimensions, or merge 4D slice-set layout into local geometry.
