# Keybindings RDS

Status: Active v0.5  
Author: Omer + Codex  
Date: 2026-02-16  
Target Runtime: Python 3.14 + `pygame-ce`

## 1. Scope

Define keybinding requirements for all game dimensions and keyboard profiles:
1. 2D gameplay
2. 3D gameplay + camera + slicing
3. 4D gameplay + view + slicing
4. Shared in-app keybinding editor with local save/load
5. Dedicated keybindings setup menu and conflict-safe action routing

Implementation references:
1. `/Users/omer/workspace/test-code/tet4d/tetris_nd/keybindings.py`
2. `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_keybinding_shortcuts.py`
3. `/Users/omer/workspace/test-code/tet4d/keybindings/2d.json`
4. `/Users/omer/workspace/test-code/tet4d/keybindings/3d.json`
5. `/Users/omer/workspace/test-code/tet4d/keybindings/4d.json`

## 2. Keyboard Type Profiles

### 2.1 Profile model

1. Supported profiles:
2. `small` (default, compact keyboards)
3. `full` (numpad-first mappings)
4. Selection mechanism: env var `TETRIS_KEY_PROFILE=small|full`
5. No automatic keyboard hardware detection is currently implemented.

### 2.2 Precedence and defaults

1. Runtime loads bindings from JSON files when available.
2. Profile defaults are used when JSON files do not exist or are invalid and regenerated.
3. Practical precedence:
4. Existing JSON file > profile defaults
5. Profile defaults > hardcoded fallback

## 3. Shared System Keys (all dimensions)

1. `Esc` -> quit
2. `M` -> menu
3. `R` -> restart
4. `G` -> toggle grid

## 4. Key Sets By Dimension And Keyboard Type

### 4.1 2D gameplay

#### `small` profile

1. Move `x-`/`x+`: `Left` / `Right`
2. Soft drop: `Down`
3. Hard drop: `Space`
4. Rotate `x-y +`: `Up` or `X`
5. Rotate `x-y -`: `Z`

#### `full` profile

1. Move `x-`/`x+`: `Numpad4` / `Numpad6`
2. Soft drop: `Numpad5`
3. Hard drop: `Numpad0`
4. Rotate `x-y +`: `Up` or `X`
5. Rotate `x-y -`: `Z`

#### 2D ND-key blocking requirement

1. 2D mode must ignore ND-only keys (`Q/W/A/S/Z/X`, number-row rotation plane keys, `,/.`, slice keys).

### 4.2 3D gameplay

#### `small` profile

1. Move `x-`/`x+`: `Left` / `Right`
2. Move `z-`/`z+`: `Up` / `Down`
3. Soft drop: `LShift` or `RShift`
4. Hard drop: `Space`
5. Rotate `x-y +` / `x-y -`: `Q` / `W`
6. Rotate `x-z +` / `x-z -`: `A` / `S`
7. Rotate `y-z +` / `y-z -`: `Z` / `X`

Translation semantics:
1. `move_x_neg/move_x_pos` are viewer `left/right` intents.
2. `move_z_neg/move_z_pos` are viewer `away/closer` intents.
3. Runtime maps these intents to board axes based on current yaw.

#### `full` profile

1. Move `x-`/`x+`: `Numpad4` / `Numpad6`
2. Move `z-`/`z+`: `Numpad8` / `Numpad2`
3. Soft drop: `Numpad5`
4. Hard drop: `Numpad0`
5. Rotate `x-y +` / `x-y -`: `Q` / `W`
6. Rotate `x-z +` / `x-z -`: `A` / `S`
7. Rotate `y-z +` / `y-z -`: `Z` / `X`

#### 3D camera group (profile-independent default)

1. Yaw `-` / `+`: `J` / `L`
2. Pitch `-` / `+`: `K` / `I`
3. Zoom out / in: `-` / `+`
4. Reset camera: `0`
5. Cycle projection: `P`

#### 3D slice group (profile-independent default)

1. Slice `z-` / `z+`: `[` / `]`

### 4.3 4D gameplay

#### `small` profile

1. Move `x-`/`x+`: `Left` / `Right`
2. Move `z-`/`z+`: `Up` / `Down`
3. Move `w-`/`w+`: `,` / `.`
4. Soft drop: `LShift` or `RShift`
5. Hard drop: `Space`
6. Rotate `x-y +` / `x-y -`: `X` / `Z`
7. Rotate `x-z +` / `x-z -`: `1` / `2`
8. Rotate `y-z +` / `y-z -`: `3` / `4`
9. Rotate `x-w +` / `x-w -`: `5` / `6`
10. Rotate `y-w +` / `y-w -`: `7` / `8`
11. Rotate `z-w +` / `z-w -`: `9` / `0`

Translation semantics:
1. `move_x_neg/move_x_pos` are viewer `left/right` intents.
2. `move_z_neg/move_z_pos` are viewer `away/closer` intents.
3. Runtime remaps `x/z` intents by current yaw; `move_w_neg/move_w_pos` remain fixed.

#### `full` profile

1. Move `x-`/`x+`: `Numpad4` / `Numpad6`
2. Move `z-`/`z+`: `Numpad8` / `Numpad2`
3. Move `w-`/`w+`: `Numpad7` / `Numpad9`
4. Soft drop: `Numpad5`
5. Hard drop: `Numpad0`
6. Rotate `x-y +` / `x-y -`: `X` / `Z`
7. Rotate `x-z +` / `x-z -`: `1` / `2`
8. Rotate `y-z +` / `y-z -`: `3` / `4`
9. Rotate `x-w +` / `x-w -`: `5` / `6`
10. Rotate `y-w +` / `y-w -`: `7` / `8`
11. Rotate `z-w +` / `z-w -`: `9` / `0`

#### 4D view group (profile-independent default)

1. Yaw `-` / `+`: `J` / `L`
2. Pitch `-` / `+`: `K` / `I`
3. Zoom out / in: `-` / `+`
4. Reset view: `Backspace` (planned deconflict from gameplay `rotate_zw -`)
4. Reset view: `Backspace` (implemented deconflict from gameplay `rotate_zw -`)

#### 4D slice group (profile-independent default)

1. Slice `z-` / `z+`: `[` / `]`
2. Slice `w-` / `w+`: `;` / `'`

## 5. Load, Change, Save Workflow

### 5.1 Startup load behavior

1. Each frontend calls `initialize_keybinding_files()` at startup.
2. For each dimension file:
3. If file exists and parses, it is loaded into in-memory binding maps.
4. If file missing or invalid, defaults are written to disk for that dimension.

### 5.2 Main vs gameplay menu parity (required)

Both menu contexts must expose the same keybinding profile actions:
1. Main/setup menu: load profile, save profile, rebind controls, reset profile to defaults.
2. In-game pause menu: load profile, save profile, rebind controls, reset profile to defaults.
3. Behavior and confirmation UX must be equivalent in both contexts.

### 5.3 Load and save from menu

1. Menu shortcut `L` -> load selected profile for current dimension.
2. Menu shortcut `S` -> save selected profile for current dimension.
3. Menu status line must display success/error message.

### 5.4 Changing/redefining bindings

1. User must be able to redefine controls in-app (interactive rebind mode).
2. Rebind flow:
3. Select action (for example `move_x_neg`).
4. Press new key.
5. Resolve conflicts (replace/swap/cancel).
6. Save to selected profile.
7. Rebind mode must be available from both main/setup and pause menus.

### 5.5 Keybinding editor menu requirements

1. The editor must be reachable from:
2. Setup menu (`Controls` -> `Edit Keybindings`)
3. Pause menu (`Settings` -> `Controls` -> `Edit Keybindings`)
4. The editor must list bindable actions grouped as:
5. `game`
6. `camera` (3D/4D only)
7. `slice` (3D/4D only)
8. `system`
9. Each row must show action name plus currently assigned keys.
10. Footer hints must expose: `Rebind`, `Clear`, `Load`, `Save`, `Save As`, `Reset`.
11. Failed operations (invalid file, duplicate profile, write error) must show non-blocking error text.
12. Editor must show conflict strategy (`replace`, `swap`, `cancel`) and let user cycle it.

### 5.6 Non-default profile support

1. Profiles are not limited to `small` and `full`; user-defined names are required.
2. Required operations:
3. Create profile (clone from current/built-in)
4. Rename profile
5. Delete profile (except protected built-ins)
6. Select active profile
7. Save/load per profile and per dimension
8. Built-in profiles (`small`, `full`) remain available as defaults and reset baselines.

### 5.7 Local save/load policy

1. Save/load operations are local filesystem operations only (no network/cloud dependency).
2. Default save target for the active profile is:
3. `/Users/omer/workspace/test-code/tet4d/keybindings/profiles/<profile>/<dimension>.json`
4. `Save As` must allow writing to a new local profile folder name.
5. `Load` must read the selected local profile file for the current dimension.
6. Invalid/missing files must not crash; loader falls back to defaults and reports status.

### 5.8 Dedicated keybindings setup menu

1. Main menu must include `Settings -> Controls -> Keybindings Setup`.
2. Pause menu must include the same `Keybindings Setup` entry.
3. Both entries open the same editor component and behavior.
4. User can test bindings in a lightweight input-preview subpanel before leaving menu.

## 6. JSON/Profile Storage Requirements

### 6.1 File locations

1. Built-in/default compatibility files:
2. `/Users/omer/workspace/test-code/tet4d/keybindings/2d.json`
3. `/Users/omer/workspace/test-code/tet4d/keybindings/3d.json`
4. `/Users/omer/workspace/test-code/tet4d/keybindings/4d.json`
5. Profile-specific files (required for non-default profiles):
6. `/Users/omer/workspace/test-code/tet4d/keybindings/profiles/<profile>/2d.json`
7. `/Users/omer/workspace/test-code/tet4d/keybindings/profiles/<profile>/3d.json`
8. `/Users/omer/workspace/test-code/tet4d/keybindings/profiles/<profile>/4d.json`

### 6.2 Canonical shape

```json
{
  "dimension": 4,
  "profile": "small",
  "bindings": {
    "game": {
      "move_x_neg": ["left"],
      "move_x_pos": ["right"]
    },
    "slice": {
      "slice_z_neg": ["["],
      "slice_z_pos": ["]"]
    },
    "camera": {
      "yaw_neg": ["j"],
      "yaw_pos": ["l"]
    }
  }
}
```

### 6.3 Group requirements by dimension

1. 2D: `game`
2. 3D: `game`, `camera`, `slice`
3. 4D: `game`, `camera`, `slice`

### 6.4 Compatibility requirement

1. 2D loader must accept both canonical grouped format and legacy flat game-action format under `bindings`.
2. Legacy default files must keep loading even when profile storage is introduced.

### 6.5 Storage validation requirements

1. JSON writes should be atomic (`temp file` then `replace`) to avoid partial files.
2. Unknown actions in loaded JSON should be ignored with warning status, not crash.
3. Missing required actions should inherit defaults for those actions only.
4. Action maps must enforce no hidden gameplay/view collisions for active key profile.

## 7. Change Safety Rules

1. Keep keybindings external; do not hardcode per-mode keys in frontend loops.
2. After load/save, rebuild panel control lines to match runtime state.
3. Keybinding updates must preserve system actions and menu discoverability.
4. Profile changes must not break existing JSON files created in prior runs.
5. Gameplay actions must not be shadowed by camera/view actions in the same mode.

## 8. Testing Instructions

Minimum checks after keybinding changes:

```bash
ruff check /Users/omer/workspace/test-code/tet4d
pytest -q
```

Manual checks:
1. Delete one keybinding file and confirm regeneration on startup.
2. Edit a key in JSON, press `L` in setup menu, and verify behavior in game.
3. Press `S` in setup menu and confirm JSON is updated.
4. Verify 2D ignores ND-only keys.
5. Rebind one action from setup menu and one from pause menu; verify parity.
6. Trigger a key conflict and verify conflict-resolution flow.
7. Save profile locally, restart app, load profile, and verify key behavior persists.
8. In 4D, verify `9/0` rotations repeatedly work and are not consumed by view reset.

## 9. Acceptance Criteria

1. All dimensions can load/save keybindings without crash.
2. Small and full profile defaults are documented and reproducible.
3. User can create and use non-default profiles, redefine keys, and persist them.
4. Main/setup and in-game pause sections provide the same keybinding profile actions.
5. JSON schema and group handling are explicit and consistent with code.
6. Tests pass and menu feedback is visible for load/save/rebind/reset actions.
7. Keybinding editor supports local save/load and conflict-safe rebinding.
8. 4D `9/0` rotation path is conflict-free and reliable under key repeat.

## 11. Implementation Status (2026-02-16)

Implemented in code:
1. Dedicated keybinding setup screen added (`/Users/omer/workspace/test-code/tet4d/tetris_nd/keybindings_menu.py`).
2. Runtime action groups now include `system` for rebinding visibility alongside `game/camera/slice`.
3. 3D/4D `z` movement defaults use `Up` for `z-` and `Down` for `z+` in small profile; full profile uses `Numpad8`/`Numpad2`.
4. 4D camera reset default is `Backspace`.
5. Rebind safety guard prevents camera actions from overriding gameplay/slice/system keys (protects 4D `9/0` rotations).
6. Keybinding conflict and 4D camera override behavior are covered by tests in `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_keybindings.py`.

## 10. Implementation Plan (Keybindings)

1. Implement a shared keybinding editor model and renderer for setup/pause menus.
2. Add action-group metadata so each dimension can render only valid groups/actions.
3. Add rebind capture state with conflict resolution (`replace`, `swap`, `cancel`).
4. Add local profile IO helpers (`load`, `save`, `save_as`, `reset`) with atomic writes.
5. Add test coverage for editor-state transitions and profile file round-trips.
