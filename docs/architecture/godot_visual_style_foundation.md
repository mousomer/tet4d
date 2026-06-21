# Godot Visual Style Foundation

Stage 32 implements the Godot product-shell visual style foundation defined by
`docs/architecture/godot_visual_style_authority.md`. This is a Godot
product-shell styling stage only.

## Purpose

Stage 32 adds a hybrid style-token system so standard Godot controls and
script-driven replay/board visuals use the same semantic colour roles. It does
not redesign the Stage 31 visual direction.

The primary product identity is:

```text
Tron-like technical diagram
```

`tron` is now the primary/default product theme. `diagnostic` remains the
development/debug theme, and `plain` remains the neutral/accessibility
fallback.

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

## Styled Shell Surfaces

Stage 32 styles:

- app/root background;
- top status and authority panels;
- left case browser shell surfaces through recursive panel styling;
- right inspector panels;
- settings panel and settings rows;
- generated buttons, sliders, dropdowns, and checkboxes;
- keyboard hint labels;
- bottom replay controls;
- settings screen, controls screen, and diagnostics screen shell controls.

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
- Tron is visibly dark/neon/technical without overwhelming board readability.
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
- replay visual role mapping;
- existing layout/settings/UX coverage from Stages 28-30.

## Boundary

This stage implements Godot product-shell styling only. This stage does not
change gameplay semantics. This stage does not change topology, movement,
trace semantics, replay frame semantics, or board-state semantics.

Python remains the gameplay semantic oracle. No authority transfer occurred.
Godot remains product-shell/replay-view presentation only.
