# Game-Safe 4D Slice-Basis Contract

Status: Stage 54C normative presentation contract

## Scope and owner

Godot owns the live 4D presentation basis, basis-turn input routing, slice
decomposition, labels, indicators, transition animation, and focused teaching
flow. The canonical board, piece, gravity, topology, legality, scoring, replay,
snapshot, and state-hash owners do not change.

A basis turn changes how one canonical 4D state is observed. It never rotates
or rewrites that state.

## Exact state

`SliceBasis4D` is an exact signed permutation in presentation-slot order:

```text
[visible_u, visible_y, visible_v, slice_axis]
```

Each value names one signed canonical axis. The initial state is:

```text
[+X, +Y, +Z, +W]
```

Every valid state contains the absolute axes `X`, `Y`, `Z`, and `W` exactly
once, and `visible_y` is always `+Y`. There is no floating-point basis identity.

## Quarter-turn convention

For a positive quarter turn in canonical plane `A-B`:

```text
+A -> +B
+B -> -A
```

The negative turn is its exact inverse. Tet4D exposes `XW +/-90`, `ZW +/-90`,
and `ZX +/-90` as one exact 90-degree view-rotation family. `XW` and `ZW` may
exchange the slice axis with a visible non-gravity axis; `ZX` rotates the
visible X/Z frame while preserving the current slice-axis membership. The
operations transform the current signed basis and therefore compose rather
than toggle hard-coded layouts. Four equal quarter turns are identity and
opposite turns cancel exactly.

## Coordinate mapping

One pure mapper converts canonical `(x, y, z, w)` plus canonical extents and
the exact basis into:

```text
(layer_index, visible_cell_3d)
```

For a positive signed axis, the presentation coordinate equals the semantic
coordinate. For a negative signed axis:

```text
presentation = extent - 1 - semantic
```

The inverse applies the same reversal. This mapping is bijective for every
validated Stage 54B board shape, including asymmetric shapes and `W=1`.

The slice-axis sign defines presentation order. Labels retain the signed
semantic axis and semantic coordinate, so a reversed stack is not presented as
an ordinary positive stack. Layer count is the canonical extent of the current
slice axis. Visible board dimensions are the canonical extents selected by
`visible_u`, `+Y`, and `visible_v`.

Locked cells, active cells, guide/marker cells, grids, frames, labels, and
active-layer emphasis consume this mapper through the shared Godot board
presentation model.

## Input routing

Piece rotation, camera movement, layer-axis movement, and basis rotation remain
separate action groups. `view_xw_neg`, `view_xw_pos`, `view_zw_neg`,
`view_zw_pos`, `view_zx_neg`, and `view_zx_pos` semantic actions own the exact
view turns.

Presentation movement intents map through the committed exact basis:

- left/right use `visible_u`;
- away/closer use `visible_v`;
- previous/next layer use `slice_axis`;

The compact horizontal/depth/gravity indicator is a direct consumer of this
same basis: its horizontal and depth arrows use the signed visible slots, and
its stable gravity arrow remains `+Y` / down. It has no independent label or
orientation state.
- soft and hard drop remain canonical `+Y` gameplay commands.

The mapper emits an existing canonical movement command. Native gameplay still
accepts or rejects it; Godot does not calculate destinations, collision, seam
transport, or legality.

## Control-frame resolver

`ControlFrameMapping` is the single Godot presentation resolver for runtime
input, help copy, and the compact orientation marker. In Live 4D it composes
the exact signed basis with shared slice-local `L.local_yaw`, quantized to a
nearest quarter turn using the inherited Python convention. Outer camera
framing cannot enter the Live-4D resolver; 3D retains its existing camera-yaw
projection. The resolver fixes local Y at canonical `+Y`,
maps Forward/Away to local positive depth, and maps slice movement through the
signed current slice slot. Relative rotations multiply the local plane signs,
then canonicalize axis order and invert direction when the order is swapped.

The translation and rotation frame selections are setup-UI persistence only.
They do not enter native setup, snapshot/hash/replay identity, or authority.
`absolute` deliberately preserves the previous canonical command protocol.

## Gravity, camera, and lifecycle

`+Y` is always the visible vertical axis, rendered downward by the existing
world-coordinate convention. Stage 54C cannot place Y in the slice slot or
invert it.

A basis turn does not change shared `L`, outer fitted framing, zoom intent, or
pan offset. Basis-derived bounds and layout are recomputed independently.
Slice-local orientation and outer framing controls do not modify basis state.

The exact destination basis commits when an action begins. A short reduced-
motion-aware presentation settle animates toward that exact destination; the
intermediate parameter is never basis truth. Rapid commands compose from the
latest exact state and retarget the visual settle without dropping input.

Live-4D entry, new configured/random games, gameplay restart, and Reset View
reset to the canonical basis. Reset View restores `B + L + V/P` without a
native transition; Restart Game also reconstructs the native session from the
frozen current setup. The internal basis-only reset restores identity `B` and
dependent layout/bounds while preserving `L`, framing, projection, and
preferences. Setup/menu exit and mode transition discard basis with the rest
of the ephemeral presentation. Basis is excluded from setup/settings
persistence, native snapshots/hashes, and replay identity.

## Instruction

The existing Godot live-onboarding model owns a declarative five-step 4D basis
sequence. Its presentation predicates cover basis change, useful slicing,
finding a stable canonical coordinate's layer, exact target-basis matching,
and placement inspection. It queries live canonical cells where needed and
does not implement gameplay legality.

## Deterministic exclusion

Basis state and lesson progress are absent from native game state, gameplay
snapshots, state hashes, replay identity, setup identity, topology profiles,
and deterministic trace schemas. Interleaving basis-only actions with a fixed
canonical command sequence cannot change its deterministic result.
