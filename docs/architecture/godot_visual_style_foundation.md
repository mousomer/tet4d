# Godot Visual Style Foundation

Stage 32 implements the Godot product-shell visual style foundation defined by
`docs/architecture/godot_visual_style_authority.md`. This is a Godot
product-shell styling stage only.

## Purpose

Stage 32 adds a hybrid style-token system so standard Godot controls and
script-driven replay/board visuals use the same semantic colour roles. It does
not redesign the Stage 31 visual direction.

Stage 32b tightens that implementation toward the Stage 31 Neon CAD Cockpit
direction without adding a new theme or visual authority. The refinement keeps
`tron` as the product default and makes the existing shell controls read as a
compact technical cockpit: thin grid-border panels, dark board framing,
metadata-value labels, direct checkbox/dropdown/slider controls, and stable
inspector panel roles. This is still product-shell styling only.

Stage 33 extends the same foundation through
`docs/architecture/godot_vector_arcade_cockpit_overhaul.md`. It keeps the
semantic style-role architecture and updates the Godot shell toward the Vector
Arcade Cockpit product direction: command-card menus, grouped keycap/action
hints, settings cards, persistent inspector sectioning, `Vector Arcade`
display labeling for the internal `tron` theme ID, and stronger board/W-label
visual emphasis.

The primary product identity is:

```text
Vector Arcade Cockpit
```

`tron` is the primary/default product theme ID and displays as `Vector Arcade`.
`diagnostic` remains the development/debug theme, and `plain` remains the
neutral/accessibility fallback.

## Palette Data

The central Godot-side palette file is:

- `godot/Tet4D.Godot/config/shell_theme_palettes.json`

It defines exactly three themes:

- `diagnostic`
- `plain`
- `tron`

Each theme defines every Stage 31 semantic colour role. The Godot tests verify
theme IDs, role completeness, colour parsing, and that the three palettes are
visibly distinct.

## Style Architecture

The style-token implementation lives under:

- `godot/Tet4D.Godot/scripts/ui/style/shell_style_roles.gd`
- `godot/Tet4D.Godot/scripts/ui/style/shell_theme_palette.gd`
- `godot/Tet4D.Godot/scripts/ui/style/shell_style_manager.gd`
- `godot/Tet4D.Godot/scripts/ui/style/shell_control_style_applier.gd`

Responsibilities:

- `shell_style_roles.gd` owns the canonical required colour-role list.
- `shell_theme_palette.gd` represents one loaded palette and validates role
  completeness.
- `shell_style_manager.gd` loads palettes, defaults to `tron`, validates all
  themes, exposes `get_color(role)`, and emits `theme_changed`.
- `shell_control_style_applier.gd` applies style roles to panels, labels,
  buttons, option buttons, checkboxes, sliders, settings rows, and keyboard
  hints.

The control applier is the shared local/CI contract for generated shell
controls. Checkboxes, dropdowns, sliders, line edits, value labels, inspector
panels, top/bottom bars, and the board frame must route through the style
manager rather than hard-coded node colours.

Replay visuals also use the same style manager through `ReplayVisuals`, so
board/replay materials resolve through semantic roles instead of an unrelated
hard-coded palette path.

## Theme Setting Flow

Stage 32 uses the existing Stage 29 setting:

- `theme.name`

No second theme setting was added. The setting now defaults to `tron`, and its
dropdown values remain exactly:

```text
diagnostic
plain
tron
```

Flow:

```text
theme.name changes
        -> SettingsStore records the shell-local value
        -> SettingsPanel updates its ShellStyleManager
        -> ReplayHud receives display_mode_changed
        -> TraceReplayApp updates renderer and HUD display mode
        -> ReplayHud applies control styling
        -> ReplayVisuals uses the same palette roles for board/replay visuals
```

The setting option values remain exactly `diagnostic`, `plain`, and `tron`.
Only the display label for `tron` changes to `Vector Arcade`.

## Styled Shell Surfaces

Stage 32 styles:

- app/root background;
- top status and authority panels;
- left case browser shell surfaces through recursive panel styling;
- right inspector panels;
- settings panel and settings rows;
- generated buttons, sliders, dropdowns, line edits, and checkboxes;
- keyboard hint labels;
- bottom replay controls;
- settings screen, controls screen, and diagnostics screen shell controls.

Stage 32b additionally records these direct-control affordances:

- checkboxes use explicit checked/unchecked cockpit boxes;
- sliders use a dark board-colour track, neon fill, and focus grabber;
- numeric/value labels use `diagnostic.metadata`;
- the board shell frame uses `background.board` with a grid border;
- inspector panels use stable `Inspector*` node names for deterministic role
  application.

Stage 33 additionally records:

- command-card menu buttons with visible shortcut text;
- structured keycap/action hint groups in the viewer, inspector, bottom
  controls, and controls screen;
- settings rows as compact generated cards;
- explicit inspector section headers for trace, view, controls, diagnostics,
  and quick settings;
- `Vector Arcade` user-facing labeling for the internal `tron` theme.

## Styled Board And Replay Visuals

Stage 32 routes these replay/board visual elements through semantic roles:

- board background/fill;
- board/grid lines;
- board outlines;
- active/current cells;
- locked cells;
- current/past/future trace markers through probe/particle roles;
- event/diagnostic markers;
- W/layer labels;
- W/layer label chips;
- live board fill and grid roles.

Projection strength remains visual-only. No projection math, topology
traversal, movement logic, replay frame semantics, event interpretation,
board-state derivation, or piece-position derivation changed.

## Manual Acceptance Checklist

Manual visual acceptance should check:

- Godot shell opens in Tron by default.
- Vector Arcade is visibly dark/neon/technical without overwhelming board readability.
- Diagnostic remains readable/debug-oriented.
- Plain is visibly light/neutral.
- Theme dropdown switches between `diagnostic`, `plain`, and `tron`.
- Right inspector changes with theme.
- Settings panel changes with theme.
- Board background/grid changes with theme.
- W/layer labels remain readable in all themes.
- Keyboard hints remain readable in all themes.
- Settings descriptions remain readable and wrapped.
- No gameplay/topology/movement settings are exposed.
- Replay remains read-only.

If macOS assistive-access restrictions block automated clicking/navigation,
record that as an environment limitation and do not claim automated click
verification.

## Tests

Godot tests cover:

- palette completeness and distinctness;
- style manager default/fallback/theme-change behavior;
- `theme.name` default/options/control mapping;
- settings panel style application and refresh;
- generated checkbox, slider, and value-label cockpit styling;
- replay viewer board/bottom-bar style-contract snapshot;
- structured keycap/action hint snapshots;
- `Vector Arcade` display label coverage for the internal `tron` theme;
- replay visual role mapping;
- existing layout/settings/UX coverage from Stages 28-30.

## Boundary

This stage implements Godot product-shell styling only. This stage does not
change gameplay semantics. This stage does not change topology, movement,
trace semantics, replay frame semantics, or board-state semantics.

Python remains the gameplay semantic oracle. No authority transfer occurred.
Godot remains product-shell/replay-view presentation only.
