# Godot Visual System

Role: current authority for Godot product-shell visual design

## Direction

Tet4D should read as a calm geometry instrument: geometric, restrained,
precise, readable, and slightly futuristic. The Python/Pygame interface is the
strongest internal reference for hierarchy, negative space, quiet board
framing, controlled colour, and separation between play and diagnostics. Godot
does not copy every Pygame detail; it carries those qualities into the shared
Godot component system.

The board is the primary visual object. Shell chrome explains and controls it
without competing with it. Glow, repeated bright borders, heavy nested cards,
and simultaneous accent colours are exceptional treatments rather than the
default grammar.

## Theme purposes

The persisted theme IDs remain `plain`, `diagnostic`, and `tron`.

| ID | Display purpose |
| --- | --- |
| `plain` | Default Instrument presentation: calm, dark, and generally usable |
| `diagnostic` | High-clarity inspection with stronger structural separation |
| `tron` | Optional Vector Arcade presentation with more energy and colour |

High Contrast composes with all three identities. It is an accessibility
override, not a replacement theme.

## Semantic roles

Palette data remains in
`godot/Tet4D.Godot/config/shell_theme_palettes.json`. UI and renderer code must
consume semantic roles through the shared style manager. State roles cover
focus, selected, disabled, warning, error, success, paused, game over, and
active/inactive W layers; state must never depend on colour alone.

The default palette uses near-black blue backgrounds, warm off-white text, a
single muted gold interaction accent, quiet blue-grey structure, and
piece-owned gameplay colour. Diagnostic may strengthen blue and amber
separation. Vector Arcade may use cyan as its primary accent, but the board
still outranks the shell.

## Typography

- Display title: 30 px, used once per primary screen.
- Screen title: 24 px.
- Section title: 13 px, uppercase or compact title case.
- Body: 15 px.
- Supporting text: 13 px.
- Trace IDs, hashes, seeds, frame indexes, and schema values use the platform
  monospace face where the existing control supports it.

Use weight, size, and spacing before colour to create hierarchy. Supporting
copy is visually secondary but must remain readable at the default scale.

## Spacing and shape

The base spacing unit is 4 px. Normal steps are 8, 12, 16, 24, and 32 px.
Panels normally use 16 px padding; dense replay/live shell panels and compact
rows use 12 px so the supported constrained viewport remains scroll-safe.
Major screen groups use 24 px separation.

Borders are one pixel by default. Focus uses a three-pixel external-equivalent
outline, or four pixels in High Contrast. Corners are subtle: 3 px for
controls, 4 px for panels, and never more than 6 px in the default theme.
Nested panels should normally differ by background value rather than repeat a
bright frame.

## Component and state rules

- Normal controls use a quiet elevated surface and structural border.
- Hover changes surface value and uses a restrained accent border.
- Focus is always visible without flooding the whole control with accent.
- Selected controls add a persistent leading or outline cue.
- Disabled controls reduce contrast while retaining label legibility.
- Warning and error roles are reserved for actionable state.
- Pause and game-over use text plus a bordered status badge; game over uses
  the error role without turning the full shell red.
- Active basis-derived layers use a stronger outline and label weight. Inactive layers
  remain visible with a quieter structural outline.

## Board and shell relationship

Board bounds and grids support orientation. The governed live-board hierarchy is
**Active / Locked / Ghost > active frame > board wireframe > internal grid > floor fill > background**.
Ghost and locked cells have distinct jobs and need not be ordered by one alpha
value. The ordinary board wireframe defines each volume and takes clear visual
precedence over the continuously visible but subordinate, cell-scale internal
grid. Active/current frames are a distinct, stronger semantic role. Internal
grids generate interior subdivisions only; the explicit wireframe owns
coincident outer boundaries rather than relying on alpha stacking. Active/current slice frames may
use stronger emphasis without promoting every board edge. Grid detail remains behind cells according
to projected depth rather than being drawn indiscriminately on top. Active
pieces are the strongest gameplay object, using crisp warm-white edge outlines
with restrained or zero emission in the Instrument theme. Piece fill owns
gameplay colour; the outline separates every constituent cell clearly even at
3D/4D overview scale. Locked cells use semi-transparent fill controlled by the
persistent `settled_cells.opacity` preference, plus a strong persistent outline
so occupied structure remains unambiguous. The Pygame diagrammatic exterior
view, clean cube-edge separation, and stable signed-slice rhythm remain the
comparison standard.

The live ghost uses the dedicated `cell.ghost` role with a clearly visible
predictive fill, smaller body, and stronger persistent outline. It remains
weaker than the active piece and distinct from transparent locked cells and
the grid without relying only on hue or animation. High Contrast strengthens
the ghost and grid roles; Reduced Motion does not change ghost geometry. Exact
active/ghost coincidence is not double-painted.

In 3D and 4D, active and locked cells retain the same body scale and structural
wireframe envelope. Locking changes emphasis, not geometry: the wireframe stays
visibly present in a quieter warm-gray role, and the settled stack must not
acquire artificial gaps. The default 4D
fit keeps the complete current-slice matrix visible without making it feel remote.
Active cell wireframes remain crisp but subordinate to piece fill rather than
forming a bright cage. Live boards keep persistent View Options above the board
for restoring Quick Settings and toggling grid visibility. A selected Grid: On
state always renders the lattice; board-detail preferences may not silently
remove it. The outer orientation cage remains visible when Grid: Off.
On volumetric boards, grid rectangles belong to the three camera-relative rear
faces of each box: one face per axis. As the camera orbits, rear-face selection
updates so the three front faces remain free of grid detail. Grids must never
bisect the play volume or obstruct cells on a front face.

The shared shell palette is the sole owner of the live-board identities:
`background.board`, `grid.major` (`board.grid`), `grid.minor`
(`board.wireframe`), `layer.active` (`board.frame_active`), `cell.active`,
`cell.locked`, `cell.ghost`, and
`axis.x/y/z/w`. Consumers may derive alpha, depth attenuation, and transient
emphasis from those roles but may not replace their base colour locally. Normal
internal grid lines use an unshaded dark/desaturated steel-blue `grid.major`
derivative (0.055 world units at 0.31 alpha, 63% of the rejected calibration);
the `grid.minor` wireframe is 0.099 world units and remains independently
stronger. High
Contrast increases thickness and contrast while keeping active, ghost, locked,
grid, and wireframe distinct rather than only increasing alpha. The gravity
floor uses the same grid-role lattice derivative plus a quiet 0.18-alpha filled depth
cue; rear faces may attenuate modestly but never disappear. The orientation
gizmo renders exactly the three visible basis axes (`visible_u`, `+Y`, and
`visible_v`), never the slice axis. Axis colour identifies the canonical axis,
while sign identifies only direction and text.

The canonical gravity floor uses a quiet filled plane distinct from the other
five open boundaries. Four-dimensional signed slice-axis labels remain readable at the
fitted overview scale, while the active-slice frame uses emphasis rather than
excessive thickness. Live 3D/4D views include a compact, screen-anchored XYZ
orientation marker whose arrows track the world axes as the camera moves.

Pointer controls in normal Live 4D use left drag for shared slice-local
orientation `L`, right drag for outer-framing translation/pan, and the wheel
for outer-framing zoom. Other modes may retain their camera interaction. Shift
has no live camera or soft-drop binding; 3D/4D soft drop uses Ctrl only.

The fixed fitted Live-4D horizontal presentation is applied once to the
renderer-only `Live4DPresentationRoot`, across the active camera's
vertical/depth plane about the fitted focus. The HUD and `Camera3D` are outside
that subtree, so text remains left-to-right and the camera keeps identity
scale. The orientation gizmo applies the same presented-axis mapping without
mirroring its screen-anchored UI. Screen-right conformance is measured through
actual `Camera3D.unproject_position()` coordinates; camera basis inspection is
not a substitute for rendered projection evidence.

Live control helpers and runtime `InputMap` registration consume the same
binding contract. Helper copy must not duplicate key assignments. Application
actions use a stronger clickable-button treatment than passive key-reference
tags. Windowed/fullscreen state, including OS-driven mode changes, is persisted
and restored with the other shell presentation preferences.

In 4D, each signed semantic slice ID is attached to its camera-relative rear vertical face.
Selection is conveyed through visual emphasis, without adding "active" text.
The compact basis indicator derives its horizontal/depth arrow labels and
directions from the exact signed basis, states the signed slice axis, and keeps
Y-down gravity stable. Basis controls, piece rotation, slice
navigation, and camera controls remain visually distinct. Reduced Motion snaps
the short basis settle while preserving the exact destination state.

The setup Controls section separately selects relative or absolute Translation
and Rotation. Relative help says Left/Right, Forward/Back, Slice, and local
planes with the resolved signed axes; absolute help says canonical axes and
planes. The same control-frame resolver drives both wording and commands.

Camera presets (`Iso`, `Front`, `Side`, `Back`, `Top`, and `Opposite Iso`) are
presentation-only yaw/pitch/zoom shortcuts selected from the compact CAMERA
control. They do not carry or mutate `BasisState`; a manual orbit reports the
derived `Custom` state. **4D VIEW ROTATION** means the exact signed XW, ZW, or
ZX quarter-turn transformation. Re-slicing is used only where that exact turn
changes slice membership. Live-4D relative controls compose exact `B` with
quantized `SliceLocalOrientation.local_yaw`; outer `CameraRig` framing does not
participate in Live-4D command mapping. Pitch never remaps gravity, and
absolute controls remain canonical. Reset View restores canonical basis and
coherent shared-L/Iso framing defaults.

Fit View changes framing only. Reset View restores exact basis, shared slice
orientation, and fitted projection/framing without restarting gameplay.
Restart Game additionally reconstructs the frozen native setup. Change Setup,
main-menu return, and mode changes must remove the old Live-4D renderer tree
and reflection before the next visible frame. Normal Live-4D controls expose
no roll action; reusable free-inspection roll remains outside this surface.

`tools/governance/validate_live_board_visual_roles.py` protects the known grid,
wireframe, ghost, locked, and orientation-gizmo consumption paths. It is
intentionally scoped: unrelated decorative colours remain permitted.

Main menu, setup, settings, onboarding, replay, live HUD, diagnostics, pause,
and game-over surfaces all use the same tokens. Diagnostic density may be
higher, but diagnostic framing must not leak into primary play.

## Accessibility composition

Visible keyboard focus, UI scaling, scroll-safe constrained windows,
colour-independent state cues, Reduced Motion, and input isolation are
invariants. High Contrast increases text and structural contrast and focus
weight while preserving spacing, hierarchy, and the selected base-theme ID.
Reduced Motion changes decorative transitions and emission only; it never
changes gameplay or replay timing.

## Boundary

This authority owns Godot presentation only. It changes no movement, rotation,
gravity, locking, scoring, dimensions, seeds, piece generation, persistence
schema, topology, replay semantics, deterministic hash, or native authority.
Python remains the semantic oracle.
