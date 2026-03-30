# Short Keybindings Guide

Use this guide when you need to make a direct keybinding config edit quickly.

For the full contract and validation rules, use
`docs/KEYBINDINGS_EDITING.md`.

## Which File To Edit

Edit `config/keybindings/catalog.json` for:

- action ids
- labels and descriptions
- groups
- dimension applicability
- keybindings menu section titles/descriptions

Edit `config/keybindings/defaults.json` for:

- shipped default keys
- built-in profiles such as `small`, `full`, `macbook`, and `tiny`

## Numbers Or Key Names

`config/keybindings/defaults.json` now accepts either:

- integer `pygame` key codes
- readable key-name strings such as `"g"`, `"space"`, or `"left"`

The runtime normalizes both forms to canonical integer keycodes.

Examples:

- `"g"` -> `103`
- `"space"` -> `32`
- `"left"` -> `pygame.K_LEFT`

If you prefer numbers, the numeric values are `pygame` key codes.

Examples:

- `32` = `Space`
- `27` = `Escape`
- `13` = `Return`
- `97` = `A`
- `100` = `D`
- `103` = `G`

Special keys also use `pygame` constants, but they are stored as integers in
the JSON file.

Examples:

- `pygame.K_LEFT`
- `pygame.K_RIGHT`
- `pygame.K_UP`
- `pygame.K_DOWN`

If you are unsure which number to use:

1. copy the style of a nearby existing binding in `defaults.json`
2. look up the matching `pygame.K_*` constant in code
3. or print it locally with:

```python
import pygame

print(pygame.K_SPACE)
print(pygame.K_g)
print(pygame.K_LEFT)
```

## Common Tasks

### 1. Change the default key for an existing action

Edit `config/keybindings/defaults.json`.

Example:

```json
{
  "profiles": {
    "small": {
      "game": {
        "d3": {
          "hard_drop": [32]
        }
      }
    }
  }
}
```

Change only the key list for the action you want. Either of these styles is valid:

```json
"hard_drop": [32]
```

```json
"hard_drop": ["space"]
```

### 2. Change a label or description shown in the UI

Edit `config/keybindings/catalog.json`.

Example:

```json
{
  "actions": {
    "hard_drop": {
      "label": "Hard Drop",
      "description": "Drop the active piece immediately.",
      "group": "game",
      "dimensions": [2, 3, 4]
    }
  }
}
```

Do not edit `defaults.json` unless the actual keys also change.

### 3. Add a new action

1. Add the action to `config/keybindings/catalog.json`.
2. Add default bindings for the built-in profiles in
   `config/keybindings/defaults.json`.

Example catalog entry:

```json
{
  "actions": {
    "toggle_guides": {
      "label": "Toggle Guides",
      "description": "Show or hide guide overlays.",
      "group": "system",
      "dimensions": [2, 3, 4]
    }
  }
}
```

Example defaults entry:

```json
{
  "profiles": {
    "small": {
      "system": {
        "toggle_guides": ["g"]
      }
    }
  }
}
```

If you add a new action but do not add built-in defaults where required, the
contract check will fail.

## Rules To Remember

- Every action in `defaults.json` must exist in `catalog.json`.
- The action must be assigned in the correct group.
- The action must only be assigned in allowed dimensions.
- Built-in profiles must stay complete.
- Custom saved profiles may stay partial, but they still must validate.

## Validation

Run:

```bash
./scripts/check_keybinding_contract.sh
CODEX_MODE=1 ./scripts/verify.sh
```

## When You Need The Full Guide

Use `docs/KEYBINDINGS_EDITING.md` for:

- saved profile rules
- schema/versioning details
- runtime-vs-config ownership boundaries
- the full validation workflow
