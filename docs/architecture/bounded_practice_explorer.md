# Bounded practice Explorer contract

Scope: **bounded 2D/3D/4D practice**. 2D exposes the existing native
geometry/pose queries and classic catalogue through the live flat renderer.
This dimension-access repair does not activate the T2 topology runtime or
complete its separate native transport transfer. Bounded 2D uses the same
inherited geometry authority as the existing bounded practice adapter.
Keyboard movement defaults to the shared camera-relative control frame in
2D/3D/4D; absolute board-axis movement is opt-in. In 2D, A/D or Left/Right move
view-relative X (canonical X in explicit absolute mode); W/S, Up/Down or the
shared Z/X pair move Y, R/T rotate XY and Backspace retries. PageUp/PageDown
are retired from Explorer in every dimension; 9 fits the view. Ordinary piece actions update only practice readouts and
render inputs, without camera-status/control-help initialization.

The panel's Space tab (View | Piece | Space in every dimension) holds the
topology selector and board size. 2D exposes every native profile; 3D/4D list
Bounded with later profiles visibly unavailable. Board size steps within the
Live board contract and restarts the piece at the centre without changing the
Play setup; Sphere squares a rectangular board. The lower helper uses the same
legend structure in every dimension (movement compass, rotation glyphs,
PRACTICE); only 3D/4D add the separate Up/Down row. 2D projects its camera-relative
movement intents and rotation axes through the same camera-measured helper path as
3D/4D. 2D Explorer menus use the shared compact shell typography and control
padding, with the existing cockpit fit policy handling overflow.
Non-bounded movement is owned by the candidate T2A native piece runtime,
including indexed cell identity, atomic rejection and Retry. Switching profiles
preserves compatible cells and view. Seam-framed/domain poses recover the Retry
baseline as part of the requested switch, with visible feedback; failed native
admission preserves the source atomically.
The successor surface slice exposes Möbius/Klein, experimental projective and
the positive adjacent-edge Sphere, with native rotations and snapshot Undo.
This adapter integration does not claim complete T2 acceptance or terminal
authority transfer; the existing candidate designation remains explicit.

2D offers X/Y movement, XY rotation, replacement, Retry, target and flat
Reset/Fit/zoom; Z/W, orbit, exact basis and slice controls are absent.

Historical scope: **implemented bounded 3D/4D MVP only**. This remains the frozen baseline
for existing acceptance and regressions, not the forward limit of Explorer.
`docs/rds/RDS_EXPLORER_TOPOLOGIES.md` supersedes its 3D/4D-only,
bounded-only and Python-Explorer-oracle language for future 2D/3D/4D topology
product behavior. Native authority transfer is pending; historical MVP facts
below are not a claim that the new capability is present.

The Phase II Godot practice Sandbox composes existing authority. Native
`geometry_normalize_blocks`, `geometry_translate_blocks`,
`geometry_rotate_blocks`, `query_piece_pose_legal` and bounded
`query_topology_axis_wrap_cell_step` supply every geometry, placement and
adjacency query. Python reference and existing contracts retain inherited
semantic authority; native implementation ownership is not a transfer.
Godot stores detached query results and routes requests; it supplies no second
movement, rotation, collision or topology implementation. Existing Python
Explorer remains the reference for inherited free-practice intent. Existing
native geometry/query parity remains its semantic evidence and fallback.
No authority transfer or new deterministic rule is introduced.

The initial object is the configured native session's selected piece, centred
with native normalization/translation and checked by the native bounded-pose
query. Supported dimensions are 2D, 3D and 4D. Only bounded topology is
selectable. Model-level topology APIs and Python tools remain available.

Practice has no automatic tick, gravity, hold, drop, lock, score or queue
advance. Each deliberate axis translation or plane rotation requests a native
candidate and native pose validation; rejection preserves the entire pose.
Rotations use the inherited geometry pivot. Object Retry restores the exact
initial pose without changing camera, basis or inspected slice. Reset View
uses the existing composite view reset and preserves object coordinates.

Camera, exact signed 4D basis and slice-local orientation retain their current
Godot owners. Explorer opts into a free inspection basis with all six exact
XY/XZ/YZ/XW/YW/ZW view planes; Y may become a visible or hidden signed axis.
Each turn is a presentation-only ±90° turn with inverse/four-turn identity.
Visible extents, cell projection, inverse mapping and relative object rotation
follow all four signed basis slots. Ordinary Play retains the +Y-fixed basis.
Reset View restores the free inspection identity; Play creates a fresh Y-fixed
session. No object coordinates or native game state change on a view turn.
Existing dynamic control-frame mappings apply to all keyboard and clickable
movement intents, including 2D and Z/X aliases; camera-relative is the Explorer
default. Keyboard and button rotations in every dimension use the same
camera-relative rotation mapper. MOVE helpers project the mapped commands;
ROTATE glyph axes preserve both the axis and sign from that same mapper.
Keyboard and button rotations flash the same local-plane glyph.
Z/X provide Y up/down movement in every dimension;
PageUp/PageDown are retired. All relevant object
rotation planes remain available. Slice emphasis (active-slice frame, selected
label and receding neighbours) follows the object as in Play until Slice −/+
selects a coordinate along the current basis's hidden canonical axis; the first
step leaves the object's own slice span, and that layer then carries the
emphasis. Inspection never draws an automatic entry/slice dot, translates the
object or changes the basis. The ordinary first-cell origin marker is also
suppressed in Explorer only. Basis changes and Reset View return the emphasis
to the object.

New target (Piece page) marks the anchor cell of a translated pose the native
bounded-pose query accepts, so every target is reachable by deliberate moves
and never lies under the object. Each axis seeks up to a third of its extent,
and successive targets alternate direction so both Y signs are practised. No
target exists until the player asks for one.

The Explorer rail opens on View. Piece selection, replacement, Retry and
canonical object controls live on a secondary Piece page. Raw coordinate,
selected-cell, neighbor and view-angle diagnostics are not shown in this
player-facing rail. Native inspection queries remain available to tests and
existing model consumers; removing their UI does not redefine adjacency.

View is the primary interactive panel; Piece is the secondary page for object
selection and manipulation. VIEW is one shared helper/control component inside
the View page: its keycaps are clickable and print the current bindings for
all six exact planes, look, zoom, framing and slice inspection. Its semantic
action descriptors also drive keyboard dispatch, so the printed help and
buttons cannot choose different commands. The lower object helper remains
visible with Explorer translations, object rotations, Z/X and Retry; there is
no separate lower VIEW copy. Explorer-only Shift+1/2, Shift+3/4 and Shift+5/6
rotate XY, YZ and YW respectively. Plain 1–6 keep XZ/XW/ZW; exact modifier
matching prevents shifted shortcuts from also invoking the plain pair. Controls never take
gameplay keyboard focus. No gravity/drop, hold or pause actions are shown.
Ordinary practice actions update only changed readouts. They do not run Live
HUD initialization, restyle the panel, reparent its controls, or reset its tab
and scroll positions. Helpers refresh when their bindings, control frame or
presentation settings change.
Camera orbit, exact basis turns, Reset/Fit View, inspection and replacement
preserve the existing pane and helper-row nodes. Spatial helper metadata and
W-key display order update in place; changed metadata alone is not a reason
to destroy/recreate a pane's contents. Dimension changes retain the Explorer
tabs and controls, toggling dimension-specific controls in place.
Ordinary commands preserve the surrounding panel allocation and fit scale
through every rendered frame. Only rejected-action feedback is shown in a
bounded, font-relative scrolling readout. Successful actions do not add diagnostic status prose.
Changing text must not change the cockpit's intrinsic height. Window size,
font/UI scale, density and dimension changes may recalculate layout.

Replace piece (Space; P alias) cycles through the configured native production catalogue;
the piece selector also permits direct choice. Native catalogue entries supply
names, cells and colours. Native normalization/translation and bounded pose
queries prepare and validate replacement atomically. An unavailable or
non-fitting choice leaves the previous object unchanged. Replacement updates
the object and its Retry baseline while preserving camera, basis, inspected
slice, marked target, panel/tab/scroll state and native game queue/hash.
No native gameplay command or RNG draw is used for replacement.

Practice snapshots are transient render inputs, labelled as practice, without
claiming a gameplay hash or replay identity. The underlying configured native
session is never advanced by practice. Play explicitly configures a fresh
ordinary bounded session from the frozen setup; practice pose is not imported.
Menu navigation retains the detached practice pose for return; a new ordinary
game/replay clears practice state and restores ordinary HUD/control behavior.

Conformance and bootstrap evidence live in `test_practice_explorer.gd`.
Real novice acceptance is specified in `docs/plans/bounded_practice_explorer.md`;
`EXPLORER_LEARNING_READY` cannot pass on automated evidence alone.

Explorer presentation/input inventory is owned by
`LiveInputContract.explorer_profile(dimension, basis, control_frame)`. It
returns detached axis, rotation, session, topology, capability and helper
descriptors. Panels retain their controls and toggle them from that inventory;
helpers and the existing 2D input routes consume the same profile. This
refactor preserves bindings, allocation and native authority. Player dispatch
no longer exposes cell/neighbor diagnostic commands; model/native inspection
queries remain available. Unified dispatch and Explorer-owned action IDs are
reserved for Phase 2 of `docs/plans/explorer_cockpit_unification.md`.

## Surface runtime extension

Explorer keyboard dispatch is dimension-parameterised and consumes only its
Explorer action descriptor. It runs before Live handlers in `_unhandled_input`;
Replace alone claims keyboard input early to prevent a focused GUI button from
also activating on Space. Pointer and shell shortcuts retain their existing
owners. Explorer has independent held-key timers, disarmed by focus loss,
navigation or modal ownership. Keyboard X/Z/W and rotations retain existing
relative control-frame mapping; movement buttons use that same dispatcher.
Movement and rotation buttons enter the same relative dispatcher as keyboard input.
This changes action ownership, not defaults, native sessions, geometry or view
basis. The Phase 2 compatibility boundary is recorded in
`docs/plans/explorer_cockpit_unification.md`.

The owner-authorized 2D surface candidate follows `explorer_surface_runtime.md`.
It reuses the native piece runtime for Möbius, Klein and experimental projective
seams. The normal Sphere uses the positive adjacent-edge single-square profile;
the separately versioned spherical double is compatibility-only. RDS §2.5
probe semantics permit coincident destinations and different cell transforms
for Klein/RP²/S². Undo restores a validated source snapshot; physical whole-piece
inverse recovery is not a traversal gate. Coherent rotation remains a bounded
runtime capability; undefined development is a technical limitation. Targets remain bounded-only until a domain-aware target contract
is accepted. Bounded learning readiness and formal topology transfer remain open.
