# Keybindings Editing Guide

If you only need the short practical version, use
`docs/SHORT_KEYBINDINGS_GUIDE.md`.

Edit keybindings through config first.

The keybinding contract is split by concern:

1. `config/keybindings/catalog.json`
   owns action metadata, grouping, scope/menu copy, helper layout, and
   dimension applicability.
2. `config/keybindings/defaults.json`
   owns shipped built-in default key assignments.
3. Profile files under `keybindings/` and `keybindings/profiles/` store mutable
   local bindings generated and maintained by runtime code.
4. Runtime behavior and mutable live maps are owned by
   `src/tet4d/engine/runtime/keybinding_runtime_state.py` plus
   `src/tet4d/engine/runtime/keybinding_store.py`, with
   `src/tet4d/ui/pygame/keybindings.py` acting as the pygame-facing adapter.

## What To Edit

Edit `config/keybindings/catalog.json` when changing:

- action ids
- action labels or descriptions
- action group ownership
- dimension applicability
- gameplay bucket labels
- keybindings menu scope titles/descriptions
- helper/control reference structure

Edit `config/keybindings/defaults.json` when changing:

- built-in profile names
- shipped default keys for `small`, `full`, `macbook`, or `tiny`
- `system`, `game`, `explorer`, or `camera` default assignments
- `disabled_keys_2d`

Edit Python only when changing:

- runtime conflict behavior
- save/load/profile management behavior
- key parsing or sanitization behavior
- runtime-only adapter logic

## Contract Rules

`catalog.json` rules:

- every action must declare a valid `group`
- every action must declare supported `dimensions`
- `gameplay_bucket` is only valid for gameplay actions
- scope/menu copy lives under `scopes.menu_sections`

`defaults.json` rules:

- every referenced action id must exist in `catalog.json`
- every action must appear under its declared catalog group
- every action must be assigned only in supported dimensions
- default key lists may use integer keycodes or accepted key-name strings
- built-in profiles must include every required action for their declared groups/dimensions

Saved profile file rules:

- payload `dimension` must be `2`, `3`, or `4`
- payload `schema_version` may be absent for legacy files, but if present it
  must be supported by the runtime
- `bindings` group names must be valid for that dimension
- every referenced action id must exist in `catalog.json`
- every action must belong to the correct group and dimension
- saved key lists may use integers or key-name strings
- saved key-name strings must stay within the runtime-supported token set, including serialized keypad token forms written by the app itself
- saved custom profiles may be partial override payloads; built-in defaults may not

## Common Edits

Change a label or description:

1. Edit the action entry in `config/keybindings/catalog.json`.
2. Do not touch `config/keybindings/defaults.json` unless the actual keys also change.

Change a built-in default key:

1. Edit the action under the correct profile/group/dimension in `config/keybindings/defaults.json`.
2. Keep the action id exactly aligned with `config/keybindings/catalog.json`.
3. You may write keycodes as integers or readable key-name strings such as `"g"` or `"space"`.

Add a new action:

1. Add the action metadata to `config/keybindings/catalog.json`.
2. Add built-in defaults for the relevant profiles/dimensions in `config/keybindings/defaults.json`.
3. Update runtime code only if the action changes behavior rather than just documentation/default mappings.

## Validation

Run:

```bash
./scripts/check_keybinding_contract.sh
PYTHONPATH=src .venv/bin/pytest -q tests/unit/engine/test_keybindings.py tests/unit/engine/test_keybindings_menu_model.py tests/unit/engine/test_help_topics.py tests/unit/engine/test_tutorial_content.py
python3 tools/governance/validate_project_contracts.py
CODEX_MODE=1 ./scripts/verify.sh
```

## Notes

- Do not add UI-local copies of keybinding labels, action lists, or section
  titles when the same data belongs in `config/keybindings/catalog.json`.
- Do not treat `config/keybindings/defaults.json` as live user state; it only defines shipped defaults.
- Invalid custom profile files now fail load explicitly; they are not silently rewritten during normal active-profile load.
