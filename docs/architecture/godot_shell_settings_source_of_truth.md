# Godot Shell Settings Registry Foundation

Stage 29 introduces a centralized declarative registry for Godot shell
settings. The registry is the single declaration point for shell/view/replay
settings that Godot may own. It is not a gameplay authority, a Python config
replacement, a parity surface, or a port of the pygame menu tree.

## Scope

Allowed Stage 29 categories:

- `replay`
- `display`
- `theme`
- `diagnostics`
- `controls_help`

Forbidden Stage 29 categories and setting IDs include gameplay, topology,
movement, rotation, drop, collision, lock, clear, spawn, piece, and keyboard
rebinding surfaces.

All Stage 29 settings use `authority = godot_shell` and are limited to
product-shell effects:

- replay playback speed multiplier for visual replay playback only;
- replay loop toggle;
- W/layer label visibility;
- visual projection emphasis;
- Godot shell theme selection;
- shell layout debug diagnostics;
- keyboard hint visibility.

None of these settings may alter trace content, board state, piece positions,
movement decisions, topology behavior, Python config, golden fixtures, parity
fixtures, or C++ semantic behavior.

## Implementation

The registry lives at:

- `godot/Tet4D.Godot/config/shell_settings_registry.json`

The supporting Godot scripts are:

- `godot/Tet4D.Godot/scripts/ui/settings/setting_spec.gd`
- `godot/Tet4D.Godot/scripts/ui/settings/settings_registry.gd`
- `godot/Tet4D.Godot/scripts/ui/settings/settings_store.gd`
- `godot/Tet4D.Godot/scripts/ui/settings/setting_control_factory.gd`
- `godot/Tet4D.Godot/scripts/ui/settings/settings_panel.gd`
- `godot/Tet4D.Godot/scripts/ui/settings_panel.gd`

`scripts/ui/settings_panel.gd` remains the concrete `SettingsPanel` class path
for the existing Godot project and class cache. The file under
`scripts/ui/settings/` keeps the Stage 29 target route present without
introducing a second settings implementation.

The panel renders controls from the registry:

- `bool` + `checkbox`
- `int` + `slider`
- `float` + `slider`
- `enum` + `dropdown`
- `string` + `text_field`
- `action` + `button`
- `readonly` + `label`

Invalid value/control combinations are rejected by registry validation. Numeric
settings require `min`, `max`, and `step`; enum settings require non-empty
options and a default inside the option values.

## Persistence

`SettingsStore` supports the Stage 29 persistence declarations:

- `none`
- `session`
- `local_shell`

Stage 48 supersedes the original unversioned Stage 29 storage path with the
validated, versioned contract in
`docs/architecture/godot_shell_settings_persistence.md`. Persistent values are
now written only to Godot user data at:

- `user://shell_settings.json`

The old `user://tet4d_shell_settings.cfg` file is no longer read or written.
Neither stage writes Python config, gameplay config, migration bundle data,
golden traces, parity fixtures, or native/C++ settings.

## Integration

The generated settings panel is visible in the existing replay/view shell:

- the right inspector settings section;
- the existing Settings screen.

The Stage 28 layout contract still owns the shell layout. The settings panel is
scrollable and does not add nested menu screens or one-item submenu shims.

## Tests

Godot tests cover:

- registry validation;
- unique setting IDs;
- known categories;
- fixed value/control mappings;
- numeric and enum schema requirements;
- forbidden semantic tokens in setting IDs/categories;
- generated panel sections;
- checkbox, slider, dropdown, and numeric value-label generation;
- ScrollContainer usage.

## Boundary

Python remains the gameplay oracle. Godot remains product shell, replay-view
presentation, display, diagnostics, and local shell UI. Stage 29 adds no
gameplay/topology/movement settings, no pygame menu-tree port, no C++ or
GDExtension semantic implementation, no parity slice, and no authority
transfer.
