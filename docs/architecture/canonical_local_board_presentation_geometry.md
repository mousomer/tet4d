# Canonical Local Board Presentation Geometry

Status: canonical Godot presentation contract
Stage: 54F-1
Owner: Godot/GDScript presentation
Authority effect: formalizes existing presentation authority; no gameplay
authority transfer or establishment

## 1. Scope

`LocalBoardPresentationGeometry` is the sole mathematical owner of one
displayed local board volume. It owns:

- three local presentation extents and their authoritative semantic-axis map;
- a unit cell pitch and one-cell physical extent on every local axis;
- a zero-centred local origin and local board bounds;
- local cell centres, transforms, and cell bounds;
- the interior subdivision segments on each of the six local faces; and
- the twelve outer-boundary segments.

It does not own gameplay dimension validity, gameplay coordinates, materials,
visibility, labels, HUD, camera/projection/framing, accessibility/style values,
continuous slice-local orientation, or multi-slice arrangement.

Two distinctions are normative:

```text
semantic dimensions != presentation dimensional embedding
```

```text
local board geometry != camera framing != slice-set layout != styling
```

## 2. Dimensional adapters

Validated semantic extents enter through `TraceCoordinateMapper`:

```text
2D [X,Y]       -> local [X,Y,1], axes [+X,+Y,presentation-only]
3D [X,Y,Z]     -> local [X,Y,Z], axes [+X,+Y,+Z]
4D [X,Y,Z,W]   -> SliceBasis4D visible dimensions and signed visible slots
```

The 2D third axis is a presentation-only degenerate axis. It has one cell of
physical presentation extent, but it never enters canonical session setup,
native state, piece coordinates, collision, clearing, persistence, replay,
snapshot/hash identity, or topology semantics.

For 4D, `SliceBasis4D` remains the exact owner of signed-axis selection and
coordinate reversal. The geometry receives the first three signed slots and
their extents; it does not remap semantic coordinates itself. The remaining
slot supplies the separate slice count and semantic slice labels.

## 3. Geometry convention

For local dimensions `[D_x,D_y,D_z]`, the cell pitch and full cell extent are
`1`. The local board extent is therefore the vector `[D_x,D_y,D_z]`, its
centre is the origin, and its bounds are `-extent/2 .. +extent/2`.

For a basis-local cell coordinate `[x,y,z]`, the canonical centre is:

```text
(x - (D_x - 1)/2,
 -(y - (D_y - 1)/2),
  z - (D_z - 1)/2)
```

The Y inversion is the accepted Godot world-up presentation convention; it is
not a gravity or gameplay-coordinate mutation. Odd, even, asymmetric, and
single-cell axes use the same formula. A single-cell axis occupies
`[-0.5,+0.5]`, never zero thickness.

Piece body inset, opacity, face panels, outlines, and emission are style above
the unit-cell geometry. In particular, 2D may use a simpler face/material
treatment and planar camera while occupying the same full local cell envelope.

## 4. Grid and boundary contract

All grid lines originate as canonical face-grid segments. For a face, the
geometry emits one segment for every interior cell edge on its two in-plane
axes. `GridRenderer` alone chooses which canonical faces are displayed:

- 2D displays the negative-Z face as a planar grid;
- 3D and 4D cache all six faces and show camera-relative rear faces;
- the gravity floor reuses the negative-Y face segments; and
- style-only offsets prevent z-fighting without changing the underlying grid
  coordinate system.

Ordinary wireframes and 4D active-slice frames both consume the same twelve
canonical boundary segments. Their role, material, opacity, and thickness are
presentation-profile/accessibility concerns, not alternate geometry.

## 5. Composition and ownership

The accepted composition is:

```text
semantic coordinate
  -> exact basis coordinate (4D only, B)
  -> LocalBoardPresentationGeometry cell transform (G_D)
  -> shared slice-local orientation (4D only, L)
  -> slice-set anchor (4D only)
  -> outer camera/framing (V/P)
```

`AdaptiveLayerLayout` continues to own slice spacing, row/column arrangement,
slice-set centring, and anchors. It never changes local dimensions, cells,
grids, or boundaries. `SliceLocalOrientation` continues to own `L` and applies
after canonical local mapping. Camera owners frame exposed bounds and may use
different 2D, 3D, and 4D defaults.

## 6. Structural equivalence

Before orientation, anchors, camera, labels, materials, and visibility, these
must have identical structural geometry:

```text
2D [X,Y]
3D [X,Y,1]
4D with visible [X,Y,1] and slice-axis extent 1
```

Identity includes local dimensions, cell pitch, extent, centre, cell
transforms/bounds, face-grid segments, and boundary segments. Axis-mapping
metadata may differ because the semantic source differs.

Negative visible basis axes preserve dimensions and geometry extent while
`SliceBasis4D` reverses the associated basis-local coordinate. Every displayed
slice of one 4D state consumes the same local geometry; only content,
slice-set transform, labels, and active/inactive presentation can differ.

## 7. Isolation and verification

The contract is presentation-only. No method validates or mutates gameplay
setup, state, legality, gravity, topology, queue/RNG, Hold, Ghost landing,
score, replay, or hashes.

Required evidence includes asymmetric and degenerate geometry tests,
odd/even centring, the full dimensional chain, all supported exact basis
turns and signs, renderer segment consumption, deterministic/profile
regressions, pinned Godot verification, full repository verification, and
agent-driven real-window 2D/3D/4D acceptance. Visual evidence may differ in
camera, HUD, materials, and slice framing; structural equality is executable
evidence rather than screenshot equality.
