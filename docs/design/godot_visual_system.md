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
- Active W layers use a stronger outline and label weight. Inactive layers
  remain visible with a quieter structural outline.

## Board and shell relationship

Board bounds and grids support orientation. They must remain quieter than
active pieces, locked cells, the selected W layer, and terminal state. Active
pieces use crisp, warm-white edge outlines with restrained or zero emission in
the Instrument theme. Piece fill owns gameplay colour; the outline separates
every constituent cell clearly even at 3D/4D overview scale. Locked cells are
darker and use quieter edges, but adjacent cells must remain individually
parseable. The Pygame diagrammatic exterior view, clean cube-edge separation,
and stable W-slice rhythm remain the comparison standard.

In 3D and 4D, active and locked cells retain the same body scale and structural
wireframe envelope. Locking changes emphasis, not geometry: the wireframe stays
visibly present in a quieter warm-gray role, and the settled stack must not
acquire artificial gaps. The default 4D
fit keeps the complete W-slice matrix visible without making it feel remote.
Active cell wireframes remain crisp but subordinate to piece fill rather than
forming a bright cage. Live boards keep persistent View Options above the board
for restoring Quick Settings and toggling internal grid detail; the outer
orientation cage remains visible when grid detail is off.

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
