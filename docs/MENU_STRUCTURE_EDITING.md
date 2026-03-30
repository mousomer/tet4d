# Menu Structure Editing Guide

This guide explains how to change menu structure in this repo without
reintroducing Python-owned menu IA.

Primary rule:

- change menu structure in config first
- keep Python consumers generic
- validate through the runtime schema and governance checks

## Primary file

Edit `config/menu/structure.json`.

The main sections are:

- `menus`: the actual menu graph
- `menu_entrypoints`: launcher and pause root menu ids
- `launcher_subtitles`: subtitle copy per launcher menu
- `launcher_route_actions`: route ids mapped to launcher actions
- `settings_hub_layout_rows`: visible settings-hub header/item order
- `settings_sections`: filtered settings-section ownership
- `launcher_settings_routes`: launcher settings actions mapped to filtered settings sections

## Menu Graph Changes

### Add or edit a menu

Every menu under `menus` needs:

- `title`
- `items`

Supported item types:

- `action`
- `submenu`
- `route`

### Add an action item

Use:

```json
{
  "type": "action",
  "label": "Display",
  "action_id": "settings_display"
}
```

Use an existing runtime-handled `action_id`, or add the runtime handling in the
appropriate action registry if this is a genuinely new action.

### Add a submenu item

Use:

```json
{
  "type": "submenu",
  "label": "Tutorials",
  "menu_id": "launcher_tutorials"
}
```

The `menu_id` must point to another entry under `menus`.

### Add a route item

Use:

```json
{
  "type": "route",
  "label": "Continue Last",
  "route_id": "continue_last"
}
```

Then map the route id in `launcher_route_actions`.

## Launcher Settings Changes

Launcher settings now rely on three config layers working together.

### 1. Visible launcher settings entries

Edit `menus.launcher_settings_root.items`.

This controls which top-level settings entries appear in the launcher, for
example:

- `Game`
- `Display`
- `Audio`
- `Controls`
- `Profiles`
- `Legacy Topology Editor Menu`

### 2. Unified settings hub layout

Edit `settings_hub_layout_rows`.

This controls the actual header/item order used by the shared settings screen.

Headers use:

```json
{ "kind": "header", "label": "Game" }
```

Rows use:

```json
{ "kind": "item", "label": "Random type", "row_key": "game_random_mode" }
```

### 3. Filtered settings sections

Edit `settings_sections`.

Each section defines:

- `title`
- `subtitle`
- `headers`
- `row_keys`

Example:

```json
"display": {
  "title": "Display settings",
  "subtitle": "Fullscreen, window size, overlay transparency, apply, save, reset, and back.",
  "headers": ["Display"],
  "row_keys": [
    "display_fullscreen",
    "display_width",
    "display_height",
    "display_overlay_transparency",
    "display_apply",
    "save",
    "reset",
    "back"
  ]
}
```

### Launcher settings routes

Edit `launcher_settings_routes`.

This maps launcher settings actions to filtered settings sections and initial
selected rows.

Example:

```json
"settings_display": {
  "section_id": "display",
  "initial_row_key": "display_fullscreen"
}
```

## Current Validation Rules

The config is expected to satisfy all of these:

- every `settings_sections.*.headers[]` value must exist as a header in `settings_hub_layout_rows`
- every `settings_sections.*.row_keys[]` value must exist as an item row in `settings_hub_layout_rows`
- every `launcher_settings_routes` key must be a real `action_id` in `menus.launcher_settings_root.items`
- every `launcher_settings_routes.*.section_id` must reference an existing `settings_sections` entry
- every `launcher_settings_routes.*.initial_row_key` must belong to that section’s `row_keys`

If any of these fail, runtime config validation and governance validation should
reject the change.

## What Not To Hardcode In Python

Do not reintroduce private settings IA maps in:

- `cli/front.py`
- `src/tet4d/ui/pygame/launch/settings_hub_model.py`

Those modules should consume validated config, not own menu structure.

## Typical Change Patterns

### Add a new launcher submenu

1. Add a new menu under `menus`
2. Add a `submenu` item pointing to it
3. Verify the target menu id exists

### Move a settings row between filtered sections

1. Keep the row in `settings_hub_layout_rows`
2. Move its `row_key` between `settings_sections.*.row_keys`
3. Update `headers` only if the visible grouped headers should change

### Rename a visible launcher settings label

1. Change the `label` in `menus.launcher_settings_root.items`
2. Keep the `action_id` stable unless you also intend to change routing/runtime behavior

### Add a new filtered launcher settings entry

1. Add an `action` item to `menus.launcher_settings_root.items`
2. Add or reuse a `settings_sections` entry
3. Add a `launcher_settings_routes` entry using that same action id
4. Ensure the section headers and row keys already exist in `settings_hub_layout_rows`

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/pytest -q tests/unit/engine/test_menu_policy.py tests/unit/engine/test_launcher_settings_layout.py tests/unit/engine/test_launcher_front_settings_routes.py
python3 tools/governance/validate_project_contracts.py
CODEX_MODE=1 ./scripts/verify.sh
```

If `config/menu/structure.json` changed, also refresh generated docs:

```bash
python3 tools/governance/generate_configuration_reference.py
python3 tools/governance/generate_maintenance_docs.py
```
