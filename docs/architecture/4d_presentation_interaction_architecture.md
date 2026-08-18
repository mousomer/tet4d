# 4D Presentation and Interaction Architecture

Role: accepted architecture contract
Status: Stage 54E-1 complete — human accepted
Scope: Live 4D Godot presentation and input adaptation only
Authority status: accepted contract governing Stage 54E-2 implementation;
runtime authority records remain contingent on concrete implementation evidence
Implementation evidence: Stage 54E-2a complete — reviewed green; Stage 54E-2b
complete — reviewed green; Stage 54E-2c complete — reviewed green; Stage
54E-2d complete — reviewed green; aggregate Stage 54E-2 complete — reviewed green

## 1. Purpose and current audit result

This accepted contract separates three presentation spaces that the current Live 4D
implementation blends into one rendering/camera path:

1. exact 4D `BasisState`;
2. slice-local 3D orientation; and
3. slice-set/layout transform.

The load-bearing rule is:

> The slice sequence is a presentation-layout coordinate. It is not the local
> X axis of each 3D slice.

The audit inspected `trace_replay_app.gd`, `control_frame_mapping.gd`,
`slice_basis_4d.gd`, `adaptive_layer_layout.gd`, `projection_layout.gd`,
`trace_coordinate_mapper.gd`, `trace_scene_renderer.gd`, `camera_rig.gd`,
and their focused Godot tests. It also reconciled the Stage 54C contract, the
Stage 54D-2 limitation recorded by PR #63, the active RDS documents, the
authority map, and the professional programme.

The existing renderer has no independently owned slice-local orientation. It
maps a canonical cell through `SliceBasis4D`, centres it, and immediately adds
an `AdaptiveLayerLayout` offset in `TraceCoordinateMapper.world_position()`.
`TraceSceneRenderer` then builds cells and grids at those final positions.
The `TraceSceneRenderer` and `CameraRig` are sibling children of `WorldRoot`;
there are no per-slice container transforms. `CameraRig` owns outer fitted and
free yaw, pitch, roll, focus, and zoom. Its target yaw is the sole yaw supplied
to the current input resolver. Therefore Stage 54E-2 must introduce the
slice-local orientation state and separate it from layout and outer viewing;
this is outcome **B** from the Stage 54E-1 brief.

This acceptance record does not alter runtime code, RDS requirements, persistence
schemas, keybindings, deterministic identities, or authority records.

## 2. Canonical gameplay space

The deterministic game coordinate is `C = (x, y, z, w)`. It is owned by the
inherited gameplay authority currently exercised through the native live
session/query boundary. It owns active-piece cells, locked cells, collision,
gravity, legal movement and rotation, scoring, topology, queue/RNG, spawn,
hard-drop destination, snapshots, hashes, replay/trace identity, and all
other deterministic state.

`+Y` is the gravity axis. Presentation-only transforms never mutate `C`, never
choose command legality, and never enter deterministic identity. Godot may
resolve an input intent into an existing canonical command and may display
canonical cells, but native gameplay remains the accept/reject authority.

## 3. Exact 4D BasisState space

`B` is the Stage 54C `SliceBasis4D` exact signed permutation in presentation
slot order:

```text
[visible_u, visible_y, visible_v, slice_axis]
```

Its input is canonical `C` plus the four canonical extents. It produces an
integer `layer_index` and an integer visible cell coordinate
`p = (u, y, v)`. The visible slots are three signed canonical axes; the fourth
is the signed current slice axis. Every absolute axis occurs exactly once and
`visible_y` is always `+Y`. A signed negative axis reverses its corresponding
extent with `presentation = extent - 1 - canonical`. The fourth slot's sign
defines layer order and its absolute axis defines layer membership.

`B` is exact/discrete state, not a floating-point `Basis`, not free orbit, not
a slice-layout transform, and not a gameplay-state mutation. It may change
which canonical axis is sliced, which cells occur in each slice, layer order,
and the visible signed axes. It must not change canonical cells, gravity,
gameplay state, or deterministic identity. `SliceBasis4D.presentation_coordinate`
and its inverse remain the source for this mapping.

## 4. Slice-local 3D presentation space

`L` is a new Godot-owned, live-session `SliceLocalOrientation` state. It is
the same transform for every slice. Its domain and codomain are the centred
visible 3D coordinates of one slice; its pivot is that slice's local board
origin, before any anchor is added. It defines the player's visible local 3D
frame: it changes the orientation of the volume inside every slice, never the
placement or order of slice origins.

The accepted contract represents `L` with separately named `local_yaw` and
`local_pitch` values. Let `theta = local_yaw`: rendering consumes this
continuous visual angle directly. Input projection instead derives
`q = nearest_yaw_quarter_turn(theta)` and uses only that exact quarter turn for
relative X/Z translation and local rotation commands. `L` owns the ordinary
Live-4D orientation interactions that change the visible X/Z frame: mouse
left-drag orbit, keyboard yaw, and keyboard pitch. Only `Q(q)` combines with
`B` for discrete controls.

`local_pitch` is allowed but visual-only for command resolution. It is a tilt
around the already selected local horizontal axis; it does not reassign local
right or local positive depth, and the grammar contains no viewer-relative
vertical translation. Fixed canonical gravity remains `+Y`. This is why pitch
can preserve the defined horizontal/depth command frame while changing the
depth elevation seen on screen.

Arbitrary `local_roll` is not part of the **normal Live-4D gameplay**
orientation contract. It would rotate displayed Right away from the constrained
horizontal/depth grammar while canonical gravity remains `+Y`. This is a
gameplay-projection convention, not a claim that roll is invalid generally.
The accepted Decision B removes the existing keyboard-roll exposure from
normal Live 4D in 54E-2. A reusable
low-level roll primitive may and should remain available to a future Explorer,
topology-inspection, or free-inspection mode; 54E-2 must not delete it merely
because ordinary gameplay stops exposing it. No local translation is needed or
approved for 54E-2. `L` does not alter `B`, membership, order, anchors,
canonical cells, or deterministic state.

## 5. Slice-set/layout space

`anchor_i` is the placement point for slice `i`, not a transform of the
individual contents of that slice. Today
`AdaptiveLayerLayout.offset_for_layer(i)` provides translation-only anchors in
an adaptive row/column matrix. The layout owner owns stable assignment,
row/column arrangement, gaps, anchors, and layout bounds.

The normative composition is anchor-only:

```text
B(C,D) = (i,p)
local_cell = G_D(p)
oriented_cell = L(local_cell)
world_cell = oriented_cell + anchor_i
```

Future collection layout may transform anchors as points, for example
`anchor_i' = M_layout(anchor_i)`, but it must then use
`world_cell = oriented_cell + anchor_i'`. It must not apply `M_layout` to
`oriented_cell`. Thus no layout operation rotates, scales, or otherwise
changes the local basis vectors of slice contents. An anchor displacement or
an arrangement of anchor points is not an X, Y, Z, or W gameplay direction.

## 6. Final view and projection space

The rendering pipeline has a fourth *operation*, but not a fourth 4D basis:
the Godot `CameraRig` and `Camera3D` apply outer framing `V` and projection
`P` to the already laid-out collection. Under the selected Option A model,
normal Live-4D `V` owns only focus/pan, fit, zoom, and framing; `P` owns
projection. It does not independently yaw, pitch, or roll the slice
collection. Those ordinary orientation operations belong to `L`.

This restriction is required for coherent viewer-relative controls. An outer
rotation could only be added later if it either provably preserved the visible
local gameplay frame or became part of the discrete command-frame composition.
Neither is approved for normal Live 4D in 54E-2. Outer pan, zoom, fit, and
projection do not redefine local right or local positive depth and are
therefore excluded from command mapping.

This terminology is intentional: `slice-local orientation`, `slice-layout
transform`, `outer camera`, `final view`, and `projection` are distinct terms.
Unqualified “camera yaw”, “view rotation”, “local X”, and “viewer-relative”
are insufficient in this architecture.

### Interaction ownership (normative)

| Interaction | B | L | anchors | V/P | Relative mapping | Gameplay/Explorer scope |
| --- | --- | --- | --- | --- | --- | --- |
| XW basis turn | exact mutation | no | recompute | fit only | changes through B | gameplay + later Explorer as applicable |
| ZW basis turn | exact mutation | no | recompute | fit only | changes through B | gameplay + later Explorer |
| ZX basis turn | exact mutation | no | recompute | fit only | changes through B | gameplay + later Explorer |
| mouse left-drag | no | yaw/pitch | no | no | yaw affects mapping | Live-4D gameplay |
| right-drag | no | no | no | pan | none | Live-4D gameplay |
| wheel | no | no | no | zoom | none | Live-4D gameplay |
| keyboard yaw | no | yaw | no | no | affects mapping | Live-4D gameplay |
| keyboard pitch | no | pitch | no | no | does not alter discrete mapping | Live-4D gameplay |
| keyboard roll | no | no in normal gameplay | no | no gameplay roll | unavailable in gameplay; capability preserved for Explorer | normal gameplay excluded; future Explorer/free inspection |
| Fit View | no | no | no | fit | none | gameplay |
| Reset View | identity | local default | recompute | fitted default | reset | gameplay |
| layout change | no | no | anchors only | refit | none | presentation |
| camera preset | no | compatibility L component | no | compatibility framing component | yaw component | temporary 54E-2 decomposition; redesign 54E-4 |

## 7. Current-state transform and input graph

### Current rendering path

```text
canonical C=(x,y,z,w)
  -> SliceBasis4D.presentation_coordinate(B) -> (layer i, visible p=(u,y,v))
  -> TraceCoordinateMapper centres p in visible-board dimensions
  -> AdaptiveLayerLayout.offset_for_layer(i) is added directly
  -> one baked world position used by cells, grids, labels, markers, and Ghost
  -> sibling CameraRig applies combined outer yaw/pitch/roll/focus/zoom
  -> Camera3D projection -> screen
```

Native active-piece cells may legitimately have negative canonical `Y` while
the piece is spawning above the board. The active-cell presentation path must
preserve that `Y` through the same exact `B -> G_D -> L -> anchor` composition;
it must not clamp or collapse rejected points to a shared fallback origin.
Because exact `B` keeps `+Y` fixed, this is a bounded admission exception for
above-board active presentation only. Locked cells and Ghost cells retain the
ordinary strict in-board coordinate contract, and no gameplay legality or
spawn semantics move into Godot.

`TraceSceneRenderer.set_live_4d_basis()` stores `_live_4d_basis`; the app owns
the matching `_live_4d_basis`, passes it to the renderer, and uses it for HUD
and input mapping. `ProjectionLayout` owns a `TraceCoordinateMapper`, whose
`configure()` computes visible dimensions and `AdaptiveLayerLayout`. The
renderer regenerates node geometry at baked positions rather than applying a
per-slice transform hierarchy. Its basis-settle scale/position is a renderer
root presentation effect, not a per-slice local orientation.

`CameraRig` stores target/current yaw, pitch, roll, focus, and zoom. Its
`fit_bounds()` uses the whole matrix bounds and its `apply_preset()` changes
the same values. Final projection is `Camera3D`, currently orthographic.

### Current input path

```text
relative player intent
  -> translation/rotation preference
  -> TraceReplayApp._control_frame_mapping()
     -> exact app _live_4d_basis
     -> CameraRig.control_frame_yaw() [CameraRig target yaw]
  -> ControlFrameMapping.for_4d(B, yaw)
  -> canonical native command -> native deterministic gameplay
```

`ControlFrameMapping` quantizes this yaw to a nearest 90-degree turn, combines
it with `B`'s visible horizontal/depth/slice signed axes, and resolves relative
translation and rotations. The current focused tests establish this algorithm's
internal consistency (`test_control_frame_mapping.gd`) and establish that
`CameraRig` yaw/preset changes occur (`test_camera_rig.gd`); they do not prove
that the supplied yaw is a slice-local semantic frame. The basis and renderer
tests prove exact mapping, slicing, and adaptive anchor assignment, not local
orientation/layout isolation.

## 8. Resolver verdict

### DEFECTIVE

`CameraRig.control_frame_yaw()` is not the correct slice-local 3D frame for
`ControlFrameMapping`. It returns outer final-view yaw, which observes the
complete laid-out slice collection and is also changed by fit, free orbit,
camera presets, and matrix-focus workflows. No independent `L` exists.

The conflated spaces are slice-local orientation (missing), slice-set/layout
viewing (the matrix being framed), and final outer camera orientation. A front
or side-like outer view can happen to make a mapped command look plausible,
and an identity basis with an unmanipulated fitted view is the common special
case. Those cases do not establish the invariant: changing only outer yaw or a
preset currently changes the resolver input, despite leaving the local slice
frame undefined and unchanged.

Consequences are user-visible command remapping after a presentation-only
outer orbit/preset and an architectural inability to add layout movement or
rotation without contaminating controls. `test_control_frame_mapping.gd`
proves the existing basis-plus-yaw mapping; `test_camera_rig.gd` deliberately
proves that a Back preset changes yaw. Neither proves the required isolation.

## 9. Desired transform-composition contract

For a canonical cell `C`, dimensions `D`, and `B(C,D)=(i,p)`, the desired
rendering composition is:

```text
local_cell = G_D(p)                 # centred visible 3D geometry
oriented_cell = L(local_cell)       # same local transform for every i
world_cell = oriented_cell + anchor_i # anchor placement only
screen_cell = P(V(world_cell))      # outer final view and projection
```

| Transform | Domain -> codomain | Pivot/origin | Owner | Representation | Orientation / controls |
| --- | --- | --- | --- | --- | --- |
| `B` | canonical 4D -> `(i,p)` | canonical extents | app/Stage 54C Godot presentation state | exact signed discrete | changes visible/slice axes; relative controls consume it |
| `G_D` | visible integer 3D point -> centred local 3D point | slice board centre | coordinate mapper | deterministic affine point conversion | no orientation; controls do not consume it |
| `L` | local 3D -> oriented local 3D | each slice local origin | new Godot `SliceLocalOrientation` | continuous `theta = local_yaw`, admitted pitch visual transform, and discrete `Q(q)` | shared visible local frame; `theta` reaches rendering continuously, `Q(q)` reaches relative controls, pitch is visual-only within the depth-preserving gameplay domain, roll is unavailable in normal gameplay |
| `anchor_i` | oriented local 3D -> world collection | slice origin `i` | layout owner | float translation; future point-only anchor arrangement | placement only; cannot alter local basis or controls |
| `V` | world collection -> final framing | outer focus | `CameraRig` | floating pan/fit/zoom state | no normal Live-4D rotation; forbidden from controls |
| `P` | final view -> screen | camera projection | `Camera3D` | projection parameters | projection only; forbidden from controls |

`B` is applied before `L`; `L` is applied before anchor addition. This makes it
structurally impossible for an anchor vector to be treated as a local X/Z
axis: `ControlFrameMapping` receives `B` and the control projection of `L`,
never an anchor, `V`, or `P` value.

## 10. Normative invariants

**Invariant A — slice-local orientation independence.** Changing only
slice-local Y orientation changes the internal horizontal/depth orientation
identically in every slice while anchors, layer order, layer membership, and
`B` remain unchanged.

**Invariant B — layout independence.** Changing only slice-layout state may
change positions of slice origins/anchors and their collection arrangement,
but the local basis vectors and orientation of the contents of every
individual slice remain identical before and after the operation. `B` and
relative gameplay command resolution are unchanged.

**Invariant C — visual/control correspondence.** For every supported
local-yaw quarter-turn and every exact signed `BasisState`, the canonical
displacement produced by a relative gameplay intent, when passed through the
same canonical-to-basis and slice-local rendering transforms used to display
the board, points in the semantic displayed direction represented by that
intent. Relative Right renders positive displayed horizontal (`+X`) and zero
displayed depth within tolerance. Relative Forward renders zero displayed
horizontal and the independently specified displayed-away depth sign (`+Z`)
within tolerance. Tests must declare those expected signs; they must not infer
them from the implementation under test.

Its executable proof is point-difference based. For an interior valid canonical
point `C` and resolver-selected unit displacement `ΔC`, map both points through
the exact basis: `B(C,D)=(i,p)` and `B(C+ΔC,D)=(i',p')`. For relative Right and
Forward, select cases where `i'=i` and both cells are valid. Then compute:

```text
ΔpreL = G_D(p') - G_D(p)
Δdisplayed = R(theta_q) * ΔpreL
```

Here `theta_q = q*pi/2` because Invariant C samples exact quarter turns; this
does not change the continuous `R(theta)` used for general rendering.

`G_D` is affine for cell positions because it centres the board; it must never
be applied directly to `ΔC` as a point. The difference cancels centring and
exercises the same point mapping used for rendered cells. Current-slice-axis
movement is outside this visible-local-vector proof and must not be treated as
a same-slice subtraction.

### Pitch-depth preservation (supporting invariant)

For every admitted normal Live-4D gameplay pitch, a semantic Forward
displacement after the complete permitted slice-local
visual orientation and final non-rotating framing/projection retains a positive
away-from-viewer depth component. Pitch may foreshorten depth, move it
vertically on screen, or change apparent elevation, but it must not reverse
Forward into Back. At implementation level, the relevant vector assertion is
`displayed_forward_depth > 0` throughout the admitted gameplay pitch domain.

Supporting invariants:

- `B` may change membership, ordering, and visible axes but never canonical
  gameplay state.
- `L`, anchors, `V`, and `P` never mutate `B`.
- all presentation-only operations leave snapshot, hash, RNG, score,
  collision, locked cells, queue/NEXT identity, and Ghost destination intact;
- local orientation is uniform across all slices; and
- layout state has no API path into command resolution.

## 11. Worked composition examples

Use asymmetric dimensions `D=(5,7,3,2)` and canonical cell
`C=(1,2,2,0)` unless stated otherwise. The examples use the coordinate
convention already implemented by `TraceCoordinateMapper`: visible Y is
centred and rendered with a sign inversion for world-up geometry.

### Case 1 — identity B plus a local Y quarter-turn

For the vector proof choose the interior point `C0=(2,2,1,0)`, so both
resolver destinations remain valid. With identity `B`, `p0=(2,2,1)` and
`G_D(p0)=(0,+1,0)`. The passive transform for `local_yaw=+90°` is
`R(+90°)=Basis(Vector3.UP,+PI/2)`.

Right resolves to `ΔC_right=+Z`: `C0+ΔC_right=(2,2,2,0)`,
`G_D(p_right)=(0,+1,+1)`, and therefore
`ΔpreL_right=(0,0,+1)`. Applying `R(+90°)` yields displayed `(+1,0,0)`:
screen-right. Forward resolves to `ΔC_forward=-X`:
`C0+ΔC_forward=(1,2,1,0)`, `G_D(p_forward)=(-1,+1,0)`, and therefore
`ΔpreL_forward=(-1,0,0)`. Applying `R(+90°)` yields displayed `(0,0,+1)`:
away. The board-centre translation is present in each point mapping and
cancels only when the points are subtracted. `anchor_0`, membership (layer
`W=0`), and order (`+W`) are unchanged; no anchor displacement participates.

### Case 2 — layout-only change

Keep identity `B` and identity `L`, but change a two-slice row from anchors
`anchor_0=(0,0,0), anchor_1=(7,0,0)` to a column
`anchor_0=(0,0,0), anchor_1=(0,-10,0)`. `C` remains in layer `0` with local coordinate
`(-1,+1,+1)` and the same local X/Y/Z axes. Relative X/Z and local rotation
commands resolve identically before and after the layout change. Only the
second slice origin changes; no local basis vector changes.

### Case 3 — exact XW turn

Let `B` be identity turned XW positive, yielding
`[+W,+Y,+Z,-X]`. The unchanged canonical `C=(1,2,2,0)` maps to layer
`i=3` because the signed `-X` slice coordinate is `5-1-1`; its visible local
cell is `(0,2,2)`. Slice axis and membership have changed from `+W` to `-X`,
and ordering is reversed by the sign. `L` remains the independently chosen
slice-local orientation and the layout algorithm receives the new layer count
of five; it does not reinterpret the fifth anchor as a local axis.

### Case 4 — nontrivial combined operation

Use `B=[+W,+Y,+Z,-X]`, a non-zero `L` local yaw, a two-column adaptive layout
whose `anchor_3` is `(0,-9,0)`, and outer `V` pan/zoom framing. The exact
order is `C -> B -> G_D -> L -> (+ anchor_3) -> V -> P`. Control resolution
uses the exact signed visible/slice axes from `B` and the quantized yaw of `L`;
it ignores `anchor_3` and every `V`/`P` parameter.

### Case 5 — W=1

For `D=(5,7,3,1)` and identity `B`, there is one slice and `anchor_0` is visually
trivial. `L` still orients the single internal 3D volume, so relative controls
remain defined by `B` plus local yaw. No special command rule or shortcut is
introduced. If a later exact basis turn makes X or Z the slice axis, the same
mapping and layout contract applies.

## 12. Slice-local horizontal/depth and relative-control contract

### Slice-local horizontal/depth convention (normative)

Normal Live-4D gameplay names a constrained local frame: **Right**, **Left**,
**Forward**, **Back**, plus fixed gravity **Up/Down** semantics. Right is the
displayed horizontal direction toward screen-right within the player's visible
slice frame; Left is toward screen-left. Forward means movement **away from the
viewer into the displayed 3D slice volume**. Back means movement toward the
viewer out of that volume. `Forward` is the semantic command name; this
document deliberately does not use the ambiguous compound “Forward/Away”.

The explicitly defined ideal rendered depth sign for semantic Forward is
**displayed `+Z`**. At exact resolver quarter centres, post-`R` gameplay
Forward equals that vector. Between centres, the actual discrete command uses
`F(theta_q)` while rendering uses continuous `R(theta)`, so gameplay Forward
contains the residual yaw derived in the 54E-2c review correction below. The
normal Live-4D fixed camera mount/projection must display actual
resolver-selected Forward as receding/away and resolver-selected Right as
screen-right throughout the admitted yaw/pitch domain. This is a requirement
on the accepted presentation frame, not an inference from Godot's
camera-forward convention.

**Displayed-depth implementation clarification.** Here “away” means receding
from the player under the normal fitted Live-4D gameplay view after slice-local
orientation and final framing/projection. Displayed `+Z` is the exact-quarter
baseline; actual command safety additionally includes residual yaw. This
semantic presentation contract does not define either Godot world `+Z` or
`Camera3D` local `+Z` as away:

```text
board-frame +Z != Godot world +Z by definition
board-frame +Z != Camera3D local forward by definition
displayed +Z = ideal semantic Forward/away direction
```

The following are distinct and must never be silently substituted for one
another: a canonical signed axis; a `BasisState` visible signed slot; the
pre-`L` slice-local coordinate; the post-`L` displayed local coordinate;
Godot's world coordinate; camera/view direction; and semantic Forward/Back.
Identity `B` happens to make canonical `+Z` enter the pre-`L` depth slot,
but neither that coincidence nor Godot's `+Z` naming defines semantic Forward.

At identity `B=[+X,+Y,+Z,+W]` and `local_yaw=0`, choose an interior valid
point `C0`. The required proof is:

```text
relative Right   -> resolver ΔC=+X
                 -> B(C0,D)=(0,p0), B(C0+ΔC,D)=(0,p_right)
                 -> R(0) * (G_D(p_right) - G_D(p0)) = +X -> screen-right
relative Forward -> resolver ΔC=+Z
                 -> B(C0,D)=(0,p0), B(C0+ΔC,D)=(0,p_forward)
                 -> R(0) * (G_D(p_forward) - G_D(p0)) = +Z -> away
```

This is explicitly a difference of two point mappings; it does not apply
`G_D` to a displacement as though it were a point.

### Active frame, passive coordinates, and resolver turns

Let `theta = local_yaw` be the continuous visual yaw, and let
`q = ControlFrameMapping.nearest_yaw_quarter_turn(theta)` be its discrete
control quarter turn. Define the continuous visual transforms:

```text
F(theta) = active orientation of semantic displayed slice-local axes,
       expressed in pre-L coordinates
R(theta) = passive coordinate/render transform from pre-L coordinates into the
       fixed displayed local board frame
```

`F(theta)` maps fixed semantic displayed axes `(Right=+X, Forward=+Z)` into
pre-`L` coordinates. The discrete resolver implements the columns of
`F(theta_q)`, not arbitrary continuous `F(theta)`: at `q=1`,
Right is pre-`L` `+Z` and Forward is pre-`L` `-X`. Therefore:

```text
F(theta) = Basis(Vector3.UP, -theta)
R(theta) = F(theta)^-1 = Basis(Vector3.UP, +theta)
```

This is active/passive duality, not two competing orientations. Direct Godot
evaluation establishes that `Basis(Vector3.UP,+PI/2)` maps `+X -> -Z` and
`+Z -> +X`. Consequently `R(+90°)` maps the resolver's pre-`L` Right
`+Z` to displayed `+X`, and Forward `-X` to displayed `+Z`. The final
derived continuous renderer sign is therefore `Basis(Vector3.UP, +theta)`. The prior
negative renderer sign incorrectly used the active-frame transform as a
passive coordinate transform.

`Q(q)` consumes the un-negated discrete `q`, selected from `theta` by the
existing nearest-turn, ties-to-even rule. It selects from `B`'s signed
horizontal/depth slots:

```text
q=0: Right=horizontal,       Forward=depth
q=1: Right=depth,            Forward=-horizontal
q=2: Right=-horizontal,      Forward=-depth
q=3: Right=-depth,           Forward=horizontal
```

Thus `Q` produces the canonical displacement represented by `F(theta_q)`. For a valid
origin/destination pair, `B` maps each point to a visible coordinate and the
induced pre-`L` vector is their `G_D` point difference; `R` maps that difference
to invariant screen/depth meaning. It does not receive an affine `G_D(ΔC)`.

For exact-quarter-turn correspondence tests only, define
`theta_q = q*pi/2` and use `F(q)` and `R(q)` as shorthand for `F(theta_q)` and
`R(theta_q)`. This shorthand never quantizes the visual transform: non-quarter
angles continue to render through `F(theta)` and `R(theta)`.

| Local yaw | Resolver turn | Relative Right canonical displacement | Relative Forward canonical displacement | Displayed Right direction after R | Displayed Forward direction after R |
| --- | ---: | --- | --- | --- | --- |
| `0°` | 0 | `+X` | `+Z` | `+X` screen-right | `+Z` away |
| `+90°` | 1 | `+Z` | `-X` | `+X` screen-right | `+Z` away |
| `180°` | 2 | `-X` | `-Z` | `+X` screen-right | `+Z` away |
| `-90°` | 3 | `-Z` | `+X` | `+X` screen-right | `+Z` away |

The canonical entries are derived from the current `ControlFrameMapping`
algorithm: its `move_x_pos` uses `horizontal` with sign `+1`; its legacy
`move_z_neg` input label uses `depth` with sign `+1` and is the semantic
Forward intent. They are not copied from an assumed sign convention.

### Signed BasisState proof

Use the valid exact state `B = identity.turned("zx", +1) = [-Z,+Y,+X,+W]`.
It has the negatively signed visible horizontal slot `-Z`. At `q=+90°`, `Q`
selects Right as visible depth `+X` and Forward as negated visible horizontal
`+Z`. Choose the interior `C0=(2,2,1,0)`. The resolver produces canonical
`ΔC_right=+X` and `ΔC_forward=+Z`; each destination is valid and remains in
the same `+W` slice. The two exact point differences are:

```text
B(C0,D)              = (0,(1,2,2))
B(C0+ΔC_right,D)     = (0,(1,2,3))
B(C0+ΔC_forward,D)   = (0,(0,2,2))

G_D((1,2,3)) - G_D((1,2,2)) = +Z
G_D((0,2,2)) - G_D((1,2,2)) = -X
```

Applying `R(+90°)` maps them to displayed `+X` (screen-right) and `+Z`
(away). This exercises a negative visible slot, nonzero yaw, resolver sign
inversion, and the passive renderer transform; zero/180-degree errors cannot
cancel.

### Relative-control boundaries and pitch

| Control family | May affect canonical command resolution |
| --- | --- |
| relative horizontal/depth translation and local 3D rotations | exact `B` plus `Q(q)` |
| current-slice-axis translation | signed slice slot from `B` only |
| absolute controls | canonical action names only |

The continuous visual `theta` selects `q` only for this discrete command basis;
pitch does not affect it. Pitch
may visually tilt the shared slice-local volume, but it does not redefine the
discrete command frame, canonical `+Y` gravity, or create viewer-relative
vertical translation. This is a constrained gameplay presentation policy, not
a general fact about cameras. It is permitted only in an admitted normal
Live-4D gameplay pitch domain in which Pitch-depth preservation holds: rendered
semantic Forward must retain positive away depth and never become Back. Thus
the command frame is `B + Q(q)`, while rendering includes continuous `theta`
plus admitted local pitch. 54E-2 must prove permitted pitch changes leave the
resolved canonical Right/Forward frame unchanged and preserve positive Forward
depth; if the renderer cannot express that separation, pitch requires another
human decision. Normal outer yaw/pitch/roll, anchors, pan/fit/zoom, projection
type, and viewport geometry may not influence command resolution.

## 13. Camera-preset audit

`camera_preset.gd` contains no direct resolver call. However,
`TraceReplayApp` currently calls `CameraRig.apply_preset()`, which writes
combined target yaw/pitch; `_control_frame_mapping()` then reads its yaw.
Thus Front, Side, Back, Top, Iso, and Opposite Iso currently can change
relative command interpretation through the defective combined rig.

Under the corrected model their names are **ambiguous**, not intrinsically
local-orientation, outer-framing, or combined presets. In 54E-2 a bounded
compatibility adapter must decompose each existing definition coherently:
its yaw/pitch component targets `L`, while zoom/pan/fit targets `V/P`; it never
targets layout anchors and no outer rotation remains. This prevents the invalid
intermediate Side/Back mismatch in which a visible orientation changes while
relative controls retain a different frame.

Stage 54E-4 therefore requires **semantic redesign**, including separate
local-orientation versus outer-framing preset categories and an explicit
decision whether named combined presets are allowed. It decides persistence,
reset, labels, and any future layout preset scope; 54E-2 only provides the
coherent compatibility decomposition and does not modify current definitions.

Stage 54E-4a completed that redesign. `docs/architecture/camera_gui_preset_semantics.md`
is the canonical owner of preset taxonomy, per-family mutation permissions,
view-action semantics, Reset View/Fit View orchestration, presentation-context
lifetime, persistence ownership, and the compatibility disposition for the
existing IDs. It consumes the state-owner separation defined here. Its
human-approved lifecycle deliberately refines the earlier Stage 54E-2d rule:
Restart Game now preserves the current view, while Reset View establishes the
complete canonical view.

## 14. Ownership contract

| State | Owner | Semantic or presentation | Deterministic identity | Consumers |
| --- | --- | --- | --- | --- |
| canonical gameplay state | inherited gameplay authority/native session boundary | semantic | included by its existing contracts | native rules, snapshot/query boundary, Godot display |
| exact `BasisState` | Godot Live 4D app/presentation owner | presentation | excluded | mapper, renderer, HUD, input resolver |
| slice-local orientation | Godot Live 4D presentation owner | presentation | excluded | renderer; mouse orbit; keyboard yaw/pitch; relative-control resolver (yaw projection only) |
| slice-layout state | Godot adaptive-layout owner | presentation | excluded | anchors, bounds, renderer, outer framing |
| outer final-view state | Godot `CameraRig` | presentation | excluded | pan, fit, zoom, framing, and `Camera3D`; no normal Live-4D rotation |
| projection mode | Godot `Camera3D`/presentation owner | presentation | excluded | final screen rendering only |
| translation-frame preference | Godot setup/UI persistence owner | presentation preference | excluded | input resolver selection, HUD/help |
| rotation-frame preference | Godot setup/UI persistence owner | presentation preference | excluded | input resolver selection, HUD/help |

No authority transfer is required: this is Godot-native presentation behaviour.
If 54E-2 implements the accepted new state, it must update the authority map
and owning architecture/RDS documents only with concrete code and evidence.
No speculative `AE-####` record is created. The current map is broad but not
materially false; it does not claim that the missing state already exists.

## 15. Persistence and lifecycle contract

`B`, `L`, anchors, and outer `V/P` are transient presentation-context state.
They are not gameplay-run state or application preferences. Anchors are
derived from dimensions, `B`, layout policy, and viewport/layout inputs.
Projection mode is transient canonical-view state because the product exposes
no player-selectable camera-projection preference. Translation/rotation frame
preferences, camera sensitivity, invert-Y, and accessibility policy retain
their existing preference owners.

| Lifecycle event | B | L | anchors | V/P | frame preferences |
| --- | --- | --- | --- | --- | --- |
| application launch / Live 4D entry | identity | default yaw/pitch; no roll | recompute | fitted default | load existing preferences |
| start new game / Restart Game in the same presentation context | preserve current | preserve current | preserve current | preserve current | retain |
| Change Setup / main-menu return | clear with session | clear with session | discard | clear with session | retain |
| Reset View | identity | default yaw/pitch; no roll | recompute, not manually transformed | fitted outer default/projection default | retain |
| basis reset | identity only | unchanged | recompute from identity | unchanged unless invoked through Reset View | retain |
| changing mode | clear Live 4D state | clear | discard | mode owner chooses its default | retain |
| re-entry / application restart | identity | local default | recompute | canonical fitted view | load/retain |
| applying a preset | unchanged | receives yaw/pitch component | unchanged | receives zoom/pan/fit component | unchanged |

The active forward-looking lifecycle, including mode-specific 2D/3D/4D/replay
semantics, one composite Reset View, framing-only Fit View, and action-based
presets, is canonical in `camera_gui_preset_semantics.md`. No current view
state is persisted. A future saved-view/bookmark feature would require an
explicit versioned contract and recovery rules.

## 16. Scene-graph and implementation-structure implications

The corrected architecture can remain primarily data/coordinate-transform
driven; Stage 54E-2 does not need explicit per-slice container nodes merely
for aesthetic hierarchy. It does need a first-class transform model with
separate typed/queryable outputs for `G_D`, `L`, `anchor_i`, and `V`, rather
than one mapper function that returns their baked sum.

The minimum conceptual structure is:

```text
canonical-to-basis mapper (B)
  -> per-slice local content coordinate (G_D)
  -> shared slice-local orientation (L)
  -> per-layer anchor/layout point (anchor_i)
  -> outer CameraRig / Camera3D (V, P)
```

`L` should live in a new renderer-facing Godot presentation state/model, not in
`CameraRig`; `anchor_i` should remain in the layout owner; and `CameraRig`
should supply only outer framing. A future node hierarchy is permitted only if
it faithfully implements this ordering—for example an anchor container holding
a locally oriented content root—but it is not a prerequisite. The data API
must expose/test local coordinate, local orientation, anchor, and outer view
before composition. Any such nodes must retain one shared `L` value and must
not move an anchor into local-content coordinates.

## 17. Testing policy and executable verification design for Stage 54E-2

A **requirement/invariant test** proves accepted architecture or product
behaviour and survives refactoring unless the requirement changes. A
**characterization test** records what current code happens to do and may become
obsolete when accepted architecture deliberately changes it. A **regression
test** protects already accepted behaviour. Current combined-camera tests are
useful audit evidence, not automatically durable requirements.

When accepted Stage 54E-1 architecture contradicts a characterization assertion
that encodes defective combined-camera behaviour, 54E-2 must rewrite or replace
that assertion in the same green implementation slice that changes the runtime
behaviour. It must not retain it as a supposed regression requirement, add a
contradictory assertion beside it, or commit intentionally failing architecture
tests. Audit tests around `CameraRig.control_frame_yaw()`, presets changing
control yaw, and combined camera/control snapshots.

Invariant C is mandatory for `q ∈ {0°, +90°, 180°, -90°}`, for identity
`B`, and for at least one exact non-identity `B` with a negative visible
slot (the §12 `[-Z,+Y,+X,+W]` case qualifies). For every combination, tests
must choose an interior valid canonical point `C`, ask the resolver for unit
canonical `ΔC_right` and `ΔC_forward`, and ensure each destination is valid and
in the same displayed slice. For each intent, map both points through the exact
`B` presentation mapping to visible points `p_origin` and `p_destination`, then
compute `ΔpreL = G_D(p_destination) - G_D(p_origin)` and
`Δdisplayed = R(theta_q) * ΔpreL`, where `theta_q = q*pi/2` for this exact
quarter-turn correspondence test. Assert Right with
`Δdisplayed.x > 0` and `abs(Δdisplayed.z) <= tolerance`; assert Forward with
`abs(Δdisplayed.x) <= tolerance` and `Δdisplayed.z > 0`. This intentionally
uses rendered-point differences: the affine centring translation cancels, no
hand-written vector approximation is introduced, and the expected Forward sign
is specified here rather than inferred from the implementation.

The same relevant slices must cover Invariants A/B, asymmetric boards, `W=1`,
pitch isolation, outer-framing isolation, preset decomposition, helper/control
consistency, normal-gameplay roll according to the accepted decision, Ghost
canonical-destination isolation, deterministic isolation, and lifecycle.

## 18. Mandatory green-slice Stage 54E-2 delivery plan

“No independent `L` exists” means 54E-2 introduces a missing coordinate
space; it is not merely a source-argument replacement at
`_control_frame_mapping()`. That resolver injection point remains useful but
does not reduce the renderer/state work to wiring.

No 54E-2 sub-slice may rely on a later sub-slice to restore repository
correctness. Each must be mechanically coherent, carry its relevant tests,
finish green, and leave no knowingly contradictory old/new assertions or a
renderer/control local-frame disagreement. A monolithic 54E-2 commit is
forbidden. Prefer separate PRs for 54E-2a/b/c/d; at minimum use separately
reviewable green commits.

### 54E-2a — Presentation state and coordinate decomposition

Introduce `SliceLocalOrientation` (or equivalent) and separately queryable
`B`, `G_D`, `L`, and `anchor_i` in the coordinate/layout paths
(`trace_coordinate_mapper.gd`, `projection_layout.gd`, and
`adaptive_layer_layout.gd`), without rerouting all input. Add focused model
tests for decomposition, anchor-only layout, asymmetric dimensions, `W=1`,
signed basis mapping, active/passive mathematics, depth sign, and yaw vectors.
Establish displayed `+Z` as the exact-quarter semantic Forward/away baseline;
actual resolver-residual and fitted-camera integration are verified in
54E-2c. Repository green is required before 54E-2b.

Stage 54E-2a implementation evidence now exists in
`slice_local_orientation.gd`, `trace_coordinate_mapper.gd`,
`adaptive_layer_layout.gd`, and `projection_layout.gd`. It introduces explicit
`local_yaw`/`local_pitch`, continuous active `F(theta)` and passive `R(theta)`
queries, affine centred
point mapping, separately queryable anchors, and a compatibility composition
of `G_D(p) + anchor_i`. Focused Godot tests execute all four yaw quarter-turns
for identity and `[-Z,+Y,+X,+W]`, use mapped-point differences, and cover
anchor isolation, asymmetric `(5,7,3,2)` dimensions, signed mapping, and
`W=1` re-slicing. At the 54E-2a boundary, its compatibility position path
deliberately did not apply `L`; renderer migration was reserved for Stage
54E-2b. App input and `CameraRig` ownership remain unchanged for Stage 54E-2c.
This 54E-2a evidence is reviewed and accepted green; the following section
records the separately reviewable 54E-2b implementation.

### 54E-2b — Renderer composition

Migrate `trace_scene_renderer.gd` and applicable presentation consumers so
board/active/locked/Ghost cells, grid, frame/wireframe, labels, markers, bounds,
and helper geometry compose `B -> G_D -> L -> +anchor_i`. Test Invariants A/B,
uniform local orientation, anchors unchanged under L, local bases unchanged
under layout, Ghost destination isolation, and renderer-relevant deterministic
isolation. Repository green is required before 54E-2c.

Stage 54E-2b implementation evidence now exists in `projection_layout.gd`,
`board_presentation_model.gd`, `trace_scene_renderer.gd`, and
`grid_renderer.gd`. `ProjectionLayout.oriented_world_position()` is the
authoritative renderer composition seam: it decomposes canonical input through
exact `B` and affine centred `G_D`, applies the one shared continuous
`SliceLocalOrientation`, and only then adds the layout anchor. Cells and
geometry-attached markers use that numerical seam. Grid, floor/lattice, and
frame geometry use equivalent per-slice scene nodes whose translation is the
anchor and whose child-local basis is the same shared `L`; neither path applies
`L` twice.

Per-slice world AABBs are derived by transforming all eight local board-volume
corners and are unioned for renderer/camera-fit input. Slice identity labels
remain root-level billboards attached through those oriented envelopes rather
than becoming physical local-basis geometry. Focused tests cover identity,
quarter and non-quarter yaw, pitch, signed `[-Z,+Y,+X,+W]`, asymmetric
dimensions, `W=1` re-slicing, multiple slices, anchor/layout invariance, shared
locked/active/Ghost deltas and bases, grid/frame orientation, label identity,
and corner containment. App input routing, `CameraRig`, and relative-control
ownership remain unchanged for Stage 54E-2c. Technical review accepted this
implementation; it is complete and reviewed green, and 54E-2c is now eligible.

### 54E-2c — Interaction and camera-rig separation

**Interactive-orientation refresh invariant.** `L` is shared mutable
presentation state, while oriented collection bounds are produced during
presentation configuration. A change to shared `L` must invalidate or recompute
every presentation result derived from it—including oriented collection bounds
and camera-fit inputs—before the next rendered or fit state is considered
coherent. This is a semantic integration requirement: it does not prescribe
signals, dirty flags, observers, or a rebuild cadence.

Route mouse-left yaw/pitch and keyboard yaw/pitch to `L`; retain right-drag
pan, wheel zoom, and Fit View in `V/P`; and give the resolver exact `B`
plus discrete `L` yaw. Decompose presets (yaw/pitch to L; framing to V/P) and
remove normal gameplay outer rotation. Under accepted Decision B, detach roll
from normal gameplay while retaining reusable Explorer capability. In this
same slice run Invariant C, pitch/framing/preset/helper tests, and replace
obsolete defect-encoding characterization tests. Pitch command isolation must
cover default, minimum, maximum, and representative intermediate admitted
pitch values, asserting resolved canonical Right and Forward are unchanged.
Pitch visual semantic preservation must assert the rendered semantic Forward
displacement has `away_depth_component > 0` at every admitted boundary/extreme
(and use a continuous analytical proof where practical). Repository green is
required before 54E-2d.

This slice must also verify the fitted-camera integration:

```text
post-R board-frame +Z -> normal fitted V/P -> visually recedes from viewer
```

The relevant test/manual visual verification must establish that actual camera
placement/orientation satisfies this semantic contract. If it does not, 54E-2
must reconcile presentation/camera composition rather than relabelling the
direction.

**Stage 54E-2c implementation evidence.** Normal Live-4D now has one app-owned
orientation mutation seam over the shared `SliceLocalOrientation`. Mouse-left
drag and keyboard yaw/pitch enter that seam; it applies the normal-game pitch
policy, resets the renderer fit reference, rerenders the current presentation,
recomputes oriented bounds, and refreshes resolver/HUD consumers without a
native gameplay transition. Right-drag remains outer pan, wheel/zoom remain
framing, and at the 54E-2c boundary ordinary roll actions were consumed without
mutating either `L` or the outer rig. Stage 54E-2d removes those normal-gameplay
action registrations. Generic `CameraRig` yaw/pitch/roll primitives remain available
to 3D, replay, and future free-inspection consumers.

The Live-4D resolver now consumes exact `B` plus
`Q(L.local_yaw)`; `CameraRig.control_frame_yaw()` remains only for the 3D
resolver. Rendering continues to consume continuous yaw and admitted pitch.
The temporary preset adapter sends legacy yaw/pitch to shared `L` and sends
zoom/pan/focus framing to `CameraRig`; final preset semantics remain Stage
54E-4.

The actual fitted mount required reconciliation. A proper near-side camera at
the old 25-degree yaw made board-frame `+Z` approach the viewer. The corrected
fixed Live-4D mount is on the far side at yaw `205 degrees`, pitch `20 degrees`,
with a fixed horizontal presentation reflection in outer `V`. The reflection
is applied once to the rendered-world subtree by a dedicated
`Live4DPresentationRoot` about the fitted focus and across the active camera's
vertical/depth plane; its normal is effective camera-right. Camera3D and the
HUD remain outside that node. This reverses camera-space X while preserving
camera-space Y and Z, keeps the collection in front of the camera, maps
board-frame `+X` to positive screen X, preserves the vertical presentation,
and maps board-frame `+Z` to negative Godot view Z (farther into the rendered
scene). It is not part of `B`, `G_D`, `L`, any slice anchor, or `Q(q)`, and
non-Live fits restore the presentation root to identity.

Screen-right acceptance is established from actual resolver-selected
canonical point pairs through `B`, two-point `G_D`, continuous `L`, anchor and
renderer/world placement, followed by `Camera3D.unproject_position()`. It is
not established by `Camera3D` Node3D scale, `global_basis.inverse()`, or a
reflection-state boolean. Forward is tested separately from the same world
points through `Camera3D.get_camera_transform().affine_inverse()`: Godot's
visible camera space uses negative Z, so increasing away depth means the
destination has a more-negative camera-space Z than the origin.

**Stage 54E-2c review correction.** The initial proof treated semantic
Forward as displayed `+Z`. That is only the special case where continuous yaw
is exactly at the resolver-selected quarter turn. It omitted residual
continuous yaw between `L.local_yaw` and the nearest-quarter command frame and
therefore did not prove the admitted pitch range across normal gameplay yaw.
The production counterexample is identity `B`, `theta=46 degrees`, `q=1`, and
`p=-60 degrees`: resolver-selected Forward mapped from an interior canonical
point through exact `B`, affine point-difference `G_D`, continuous `L`, and the
actual fitted view has normalized away depth `-0.182625` and approaches the
viewer.

The corrected derivation uses active `F(theta)` for the semantic local frame
and passive `R(theta)=F(theta)^-1` for coordinates rendered by `L`. Let
`q=Q(theta)`, `theta_q=q*pi/2`, and `delta=theta-theta_q`. The resolver obtains
canonical Forward from exact `B` at `q`; after exact `B` and the difference of
two affine `G_D` point mappings, its pre-`L` board-coordinate vector is
`R(-theta_q)(0,0,1)`. Continuous passive render yaw produces
`R(theta)R(-theta_q)(0,0,1)=R(delta)(0,0,1)`. Pitch acts last about displayed
Right, so actual rendered semantic Forward is:

```text
d(delta,p) = (sin(delta),
              -sin(p) cos(delta),
               cos(p) cos(delta))
```

The accepted fixed camera's outward direction is
`o=(-sin(25)cos(20), sin(20), -cos(25)cos(20))`. Thus positive away depth is:

```text
away(delta,p) = sin(25) cos(20) sin(delta)
              + cos(delta) [sin(20) sin(p)
              + cos(25) cos(20) cos(p)]
```

For exact quarter-turn yaw (`delta=0`), the earlier pitch-only special-case
interval is approximately `(-68.120 degrees, +111.880 degrees)` and remains a
truthful description of displayed `+Z` only. Nearest-quarter resolution admits
`delta` throughout `[-45 degrees,+45 degrees]`, with the existing ties-to-even
policy selecting the exact boundary frame. Over the central gameplay interval,
the worst endpoint is `delta=-45 degrees`; strict all-yaw safety reduces to:

```text
sin(20) sin(p) + cos(25) cos(20) cos(p) > sin(25) cos(20)
```

Solving that inequality gives the actual strict normal-gameplay-safe interval
`(-42.479647 degrees, +86.240113 degrees)`. The least disruptive product policy
is asymmetric `[-40 degrees, +60 degrees]`: it preserves the current Top
preset, keeps the former upper product limit, and moves only the unsafe lower
limit. The lower limit retains `2.479647 degrees` of angular margin and
`0.025049` normalized away depth at the worst residual yaw. The unconstrained
low-level orientation primitive remains available outside normal gameplay.

Focused evidence uses a normalized sign tolerance of `1e-6` and cross-products
quarter centres and both sides of every
nearest-quarter boundary (including positive/negative wrapped cases and
ties-to-even) with corrected minimum, maximum, zero, and intermediate pitch;
identity and `[-Z,+Y,+X,+W]`; actual resolver-selected Right/Forward; two-point
`B/G_D` mapping; continuous `L`; and actual fitted view-space signs. It also
proves the rejected `46/-60` state, lower clamp and deterministic isolation,
pitch command isolation, outer-yaw/pan/zoom/Fit independence, preset
decomposition, refreshed renderer bounds/fit reference, Live-4D roll
detachment, and retained non-Live/free-camera primitives. Stage 54E-2c is
complete and reviewed green; Stage 54E-2d is complete and reviewed green, and
aggregate Stage 54E-2 is complete and reviewed green.

### 54E-2d — Lifecycle, authority, and contract reconciliation

Complete entry, new game, restart, setup change, Reset View, basis reset, mode
transition, preset lifecycle, and presentation cleanup. Under accepted Decision
B, reconcile the owning binding/configuration/help/RDS contracts and
tests now, with concrete implementation evidence; do not establish authority
speculatively. Finish the deterministic-isolation matrix, lifecycle coverage,
representative Live-4D manual visual verification, preset compatibility,
asymmetric/`W=1` cases, and signed BasisState cases. Repository green is
required.

Stage 54E-4, not 54E-2, decides final preset categories, labels, and
persistence. Stage 54D-3 Hold remains separate deterministic-core work after
human acceptance.

**Stage 54E-2d reviewed-green implementation evidence.** The app now owns
three explicit lifecycle seams: complete ephemeral default restoration,
synchronous presentation teardown, and an internal basis-only reset. Live-4D
entry, configured/random launch, Restart Game, and Reset View restore identity
`B`, default shared `L`, recomputed anchors/bounds/fit reference, canonical
orthographic fitted `V/P`, and the accepted reflection. Reset View performs no
native transition. Restart Game retains the frozen current setup and invokes
the existing native reset boundary.

Change Setup, main-menu return, replay entry, and 4D-to-other-live-mode
transitions synchronously detach renderer children, discard derived
presentation/bounds/fit/interpolation state, and clear focus, zoom, roll,
projection override, orientation gizmo, and reflection authority. Re-entry
rebuilds one coherent first frame from fresh defaults. The internal basis-only
seam restores identity `B` and dependent layout/bounds while preserving `L`,
focus/pan, zoom, projection, and preferences. Presets remain the bounded 54E-2c
compatibility decomposition.

Normal Live-4D roll IDs are absent from the public action contract, runtime
`InputMap`, routing, and help; generic low-level `CameraRig` roll remains.
Settings/setup persistence tests prove `B/L/V/P`, reflection, and fit state are
absent while established frame, display, sensitivity, invert-Y, and
Reduced-Motion preferences remain. This is concrete Godot presentation
implementation evidence only: it transfers or establishes no gameplay,
native-session, topology, replay, or persistence authority. External technical
review accepted the implementation and evidence. Stage 54E-2d and the aggregate
Stage 54E-2 are complete and reviewed green.

## 19. Human acceptance decisions

The project owner explicitly accepted all three decisions. They are binding
constraints for Stage 54E-2; this acceptance record itself changes no runtime
behaviour.

### Decision A — ACCEPTED

Option A: `B -> G_D -> L -> anchor -> V/P`, anchor-only layout, and no
independently rotating outer normal-game camera.

### Decision B — ACCEPTED

Remove roll from the normal Live-4D gameplay control surface while preserving
it as an intended future Explorer/free-inspection capability. Stage 54E-2 must
reconcile bindings, help, configuration authority, the owning public keybinding
contract, and tests, while retaining reusable low-level roll capability where it
supports Explorer, topology/geometry inspection, or other free-inspection modes.

### Decision C — ACCEPTED

Pitch may visually tilt the shared slice-local volume without altering the
discrete gameplay command frame only within an admitted normal Live-4D pitch
domain that preserves semantic Forward as away from the viewer. The command
frame remains determined by `B + Q(q)`, where `q` is derived from continuous
`local_yaw = theta`; the precise numeric limit belongs
to 54E-2 implementation evidence, not this acceptance record. The admitted
domain must satisfy Pitch-depth preservation, including
`displayed_forward_depth > 0` throughout its range.

## 20. Stage boundary

The accepted sequential Stage 54E-2 implementation through 54E-2d is complete
and reviewed green. Stage 54E-3 — setup/menu information architecture — is now
the next eligible Stage 54E implementation slice. Stage 54E-4/5 remain later
programme work, and Stage 54D-3 Hold remains independently eligible.

**STAGE 54E-1 COMPLETE — HUMAN ACCEPTED**
