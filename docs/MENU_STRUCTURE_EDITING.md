# Menu Structure Editing Guide

This repo now has one canonical authored menu authority plus one compiled
runtime graph.

Primary rule:

- edit `config/menu/structure.json`
- let normalization compile the runtime graph
- keep Python menu consumers structural-generic
- do not add a second page tree in renderer, input, or launcher code

## Canonical authority

Edit `config/menu/structure.json`.

Authoring-time structure lives there. Runtime rendering, navigation, and input
must consume the compiled normalized graph exposed through
`src/tet4d/engine/runtime/menu_config.py`, not the raw authored tree.

The structural keys are:

- `menu_entrypoints`: root ids for launcher, pause, settings, and keybindings
- `menus`: every page plus every typed row/item declaration
- `launcher_subtitles`, `launcher_route_actions`, `ui_copy`: supporting copy and route metadata

All menu surfaces derive from that same config:

- launcher
- pause
- settings
- one scrolling `Game` settings page with section headers
- direct `Keyboard Bindings`
- retained legacy entries

The runtime compiler removes useless wrappers before the graph reaches UI
consumers:

- hidden rows are removed first
- empty pages/sections are dropped
- singleton sections without semantic value are dissolved
- unary submenu wrappers are collapsed
- single-setting pages are inlined into a parent runtime page
- single-forward submenu shims are rewritten to their direct target

Compatibility seams are allowed only at dispatch or page-resolution level. The
collapsed authored page must not survive as visible runtime structure.

## Supported item types

Each menu item must have a stable `id`.

Supported structural types:

- `action`
- `action_group`
- `submenu`
- `section`
- `info`
- `toggle`
- `selector`
- `slider`
- `stepper`
- `keybinding_group`
- `legacy_dispatch`

Control typing rule:

- `toggle` is boolean-only and must declare `semantic_type: "bool"`
- `selector` is categorical-only and must declare `semantic_type: "enum"`
- `slider` is numeric-only and must declare `semantic_type: "int"` or `"float"`
- `stepper` is numeric-only and must declare `semantic_type: "int"` or `"float"`
- renderers must not infer selector-vs-slider from the count of possible values

Use type-specific fields only where they apply:

- `action` / `legacy_dispatch`: `action_id`
- `action_group`: `default_action_id`, `actions`
- `submenu`: `menu_id`
- `toggle` / `selector` / `slider` / `stepper`: `setting_id`, `semantic_type`
- `selector`: `options_key`
- `keybinding_group`: `binding_group`, `binding_dimension`, optional `binding_bucket`

Optional shared metadata:

- `description`
- `help_text_key`
- `visibility`
- `enabled`
- `layout_role`

## Current structure

### Authored graph

Top-level entrypoints:

- `launcher_root`
- `pause_root`
- `settings_root`
- `keybindings_root`

Settings subtree:

- `settings_root`
- `settings_game_root`
- `settings_display`
- `settings_audio`

Keybindings subtree:

- `keybindings_root`
- `keybindings_scope_general`
- `keybindings_scope_2d`
- `keybindings_scope_3d`
- `keybindings_scope_4d`
- `keybindings_scope_all`

### Normalized runtime graph

Visible runtime pages intentionally drop collapsed wrappers:

- `settings_root`
- `settings_game_root`
- `settings_display`
- `settings_audio`
- `keybindings_root`
- `keybindings_scope_general`
- `keybindings_scope_2d`
- `keybindings_scope_3d`
- `keybindings_scope_4d`
- `keybindings_scope_all`

Notable normalized outcomes:

- authored `Play` rows can keep inline `Play` / `Setup` sub-actions through
  generic `action_group` rows without creating extra submenu depth
- authored `Game` settings stay materially flat: gameplay, topology-cache,
  animation, transparency, endgame, and pace rows live on one scrolling page
  instead of a submenu forest
- runtime compilation still removes hidden rows, unary wrappers, and direct
  forward shims before UI consumers read the graph
- `config/topology/lab_menu.json` remains copy-only for the specialized
  Topology Playground shell and is not a parallel visible structure authority

## What changed

The old split settings authorities are retired from live config:

- `settings_hub_rows`
- `settings_hub_layout_rows`
- `settings_sections`
- `launcher_settings_routes`

Do not reintroduce them or replace them with new Python-owned equivalents.

## Editing patterns

### Add a submenu page

1. Add a new menu under `menus`.
2. Add a `submenu` item in its parent menu.
3. Keep ordering in the parent menu authoritative; renderers must not reorder rows.

Example:

```json
{
  "id": "settings_audio",
  "type": "submenu",
  "label": "Audio",
  "menu_id": "settings_audio"
}
```

### Add a settings control

1. Choose the owning settings page under `menus`.
2. Add a typed `toggle`, `selector`, `slider`, or `stepper` item there.
3. Reuse an existing `setting_id` already handled by the settings runtime unless this is a real new setting.
4. Pick the control from semantic type first:
   `bool -> toggle`, `enum -> selector`, `int/float -> slider` or `stepper`.

Example:

```json
{
  "id": "endgame_preset_id",
  "type": "selector",
  "label": "Relic-field preset",
  "semantic_type": "enum",
  "options_key": "game_endgame_preset",
  "setting_id": "endgame_preset_id"
}
```

### Add or edit a setup field

Setup fields in `setup_fields` are semantically typed too.

- numeric setup fields must declare `semantic_type`, `control`, `min`, and `max`
- categorical setup fields must declare `semantic_type: "enum"`, `control: "selector"`, and either literal `options` or `options_source`
- boolean setup fields must declare `semantic_type: "bool"` and `control: "toggle"`
- setup sliders are numeric-only; discrete counts such as board dimensions should use `stepper`

Example:

```json
{
  "label": "Board width",
  "attr": "width",
  "semantic_type": "int",
  "control": "stepper",
  "min": 6,
  "max": 16
}
```

### Add a same-row sub-action group

1. Use `action_group` when one visible row needs multiple explicit actions
   without another full menu layer.
2. Keep the row generic; the runtime navigation contract is `Up/Down` select
   row, `Left/Right` switch sub-action, `Enter` activate selected sub-action.
3. Use stable nested action ids and keep `default_action_id` explicit.

Example:

```json
{
  "id": "play_3d_row",
  "type": "action_group",
  "label": "3D",
  "default_action_id": "play",
  "actions": [
    {
      "id": "play",
      "label": "Play",
      "action_id": "play_3d"
    },
    {
      "id": "setup",
      "label": "Setup",
      "action_id": "setup_3d"
    }
  ]
}
```

### Add a keybindings group section

1. Choose the owning `keybindings_scope_*` page.
2. Add a `keybinding_group` item.
3. Keep the runtime binding groups authoritative for the actions inside that group; the menu config only declares placement and grouping.

Example:

```json
{
  "id": "keybindings_4d_camera",
  "type": "keybinding_group",
  "label": "4D Camera / View",
  "description": "Projection and view-turn controls.",
  "binding_group": "camera",
  "binding_dimension": "4d"
}
```

### Add a legacy-backed destination

1. Place it in the canonical tree where it belongs.
2. Use `legacy_dispatch`.
3. Keep the legacy behavior behind the action handler, not in a parallel menu definition.

Example:

```json
{
  "id": "settings_legacy_topology_editor",
  "type": "legacy_dispatch",
  "label": "Legacy Topology Editor Menu",
  "action_id": "settings_legacy_topology_editor"
}
```

## Shared scrolling contract

Scrolling is not structural authority.

The config decides:

- page hierarchy
- row order
- item type
- labels and metadata

The shared menu layout engine decides:

- viewport size
- content height
- scroll offset
- scrollbar geometry
- clipping and visible rows

Current shared overflow implementation:

- `src/tet4d/ui/pygame/ui_utils.py`
- `src/tet4d/ui/pygame/launch/launcher_settings.py`
- `src/tet4d/ui/pygame/menu/keybindings_menu_view.py`

If a page grows past the available height, use that shared overflow path. Do
not add page-local scroll math, and do not treat the overflow viewport as a
second structure authority.

## What not to hardcode in Python

Do not create a second structure authority in:

- `cli/front.py`
- `src/tet4d/ui/pygame/launch/settings_hub_model.py`
- `src/tet4d/ui/pygame/launch/launcher_settings.py`
- `src/tet4d/ui/pygame/menu/keybindings_menu_model.py`
- `src/tet4d/ui/pygame/menu/keybindings_menu_view.py`

Specialized runtime behavior is fine. Re-authored structure is not.

## Verification

Run:

```bash
pytest -q tests/unit/engine/test_menu_policy.py tests/unit/engine/test_launcher_settings_layout.py tests/unit/engine/test_launcher_front_settings_routes.py tests/unit/engine/test_keybindings_menu_model.py
python3 tools/governance/validate_project_contracts.py
python3 tools/governance/generate_configuration_reference.py --check
python3 tools/governance/generate_maintenance_docs.py --check
CODEX_MODE=1 ./scripts/verify.sh
```
