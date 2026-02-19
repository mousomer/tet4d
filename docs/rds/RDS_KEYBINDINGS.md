# Keybindings RDS

Status: Active v0.7 (Verified 2026-02-19)  
Author: Omer + Codex  
Date: 2026-02-19  
Target Runtime: Python 3.11-3.14 + `pygame-ce`

## 1. Scope

Define keybinding requirements for all game dimensions and keyboard profiles:
1. 2D gameplay
2. 3D gameplay + camera/view
3. 4D gameplay + view
4. Shared in-app keybinding editor with local save/load
5. Dedicated keybindings setup menu and conflict-safe action routing

Implementation references:
1. `tetris_nd/keybindings.py`
2. `tetris_nd/menu_keybinding_shortcuts.py`
3. `keybindings/2d.json`
4. `keybindings/3d.json`
5. `keybindings/4d.json`

## 2. Keyboard Type Profiles

### 2.1 Profile model

1. Supported profiles:
2. `small` (default, compact keyboards)
3. `full` (numpad-first mappings)
4. `macbook` (no function-key dependency in default camera/view bindings)
5. Selection mechanism: env var `TETRIS_KEY_PROFILE=small|full|macbook`
5. No automatic keyboard hardware detection is currently implemented.

### 2.2 Precedence and defaults

1. Runtime loads bindings from JSON files when available.
2. Profile defaults are used when JSON files do not exist or are invalid and regenerated.
3. Practical precedence:
4. Existing JSON file > profile defaults
5. Profile defaults > hardcoded fallback

## 3. Shared System Keys (all dimensions)

1. `Esc`-> quit
2. `M`-> menu
3. `Y`-> restart
4. `C`-> toggle grid
5. `F1`(or `Tab` on macbook profile)-> help

## 4. Key Sets By Dimension And Keyboard Type

### 4.1 2D gameplay

#### `small` profile

1. Move `x-`/`x+`:`Left`/`Right`
2. Exploration vertical `y-`/`y+`:`PageUp`/`PageDown`
3. Soft drop: `Down`
4. Hard drop: `Space`
5. Rotate `x-y +`/`x-y -`:`Up`or`Q`/`W`

#### `full` profile

1. Move `x-`/`x+`:`Numpad4`/`Numpad6`
2. Exploration vertical `y-`/`y+`:`Numpad1`/`Numpad3`
3. Soft drop: `Numpad5`
4. Hard drop: `Numpad0`
5. Rotate `x-y +`:`Up`or`X`
6. Rotate `x-y -`:`Z`

#### 2D ND-key blocking requirement

1. 2D mode must ignore ND-only keys (`A/S/Z/X/R/T/F/G/V/B`, number-row rotation plane keys, 4D `w` movement keys).

### 4.2 3D gameplay

#### `small` profile

1. Move `x-`/`x+`:`Left`/`Right`
2. Move `z-`/`z+`:`Up`/`Down`
3. Exploration vertical `y-`/`y+`:`PageUp`/`PageDown`
4. Soft drop: `LShift`or`RShift`
5. Hard drop: `Space`
6. Rotate `x-y +`/`x-y -`:`Q`/`W`
7. Rotate `x-z +`/`x-z -`:`A`/`S`
8. Rotate `y-z +`/`y-z -`:`Z`/`X` Translation semantics:
1. `move_x_neg/move_x_pos`are viewer`left/right` intents.
2. `move_z_neg/move_z_pos`are viewer`away/closer` intents.
3. Runtime maps these intents to board axes based on current yaw.

#### `full` profile

1. Move `x-`/`x+`:`Numpad4`/`Numpad6`
2. Move `z-`/`z+`:`Numpad8`/`Numpad2`
3. Exploration vertical `y-`/`y+`:`Numpad1`/`Numpad3`
4. Soft drop: `Numpad5`
5. Hard drop: `Numpad0`
6. Rotate `x-y +`/`x-y -`:`Q`/`W`
7. Rotate `x-z +`/`x-z -`:`A`/`S`
8. Rotate `y-z +`/`y-z -`:`Z`/`X`

#### 3D camera group (profile-independent default)

1. Yaw `-`/`+`:`J`/`L`
2. Pitch `-`/`+`:`O`/`U`
3. Zoom out / in: `-`/`+`
4. Reset camera: `0`
5. Cycle projection: `P`

### 4.3 4D gameplay

#### `small` profile

1. Move `x-`/`x+`:`Left`/`Right`
2. Move `z-`/`z+`:`Up`/`Down`
3. Move `w-`/`w+`:`N`/`/`
4. Exploration vertical `y-`/`y+`:`PageUp`/`PageDown`
5. Soft drop: `LShift`or`RShift`
6. Hard drop: `Space`
7. Rotate `x-y +`/`x-y -`:`Q`/`W`
8. Rotate `x-z +`/`x-z -`:`A`/`S`
9. Rotate `y-z +`/`y-z -`:`Z`/`X`
10. Rotate `x-w +`/`x-w -`:`R`/`T`
11. Rotate `y-w +`/`y-w -`:`F`/`G`
12. Rotate `z-w +`/`z-w -`:`V`/`B` Translation semantics:
1. `move_x_neg/move_x_pos`are viewer`left/right` intents.
2. `move_z_neg/move_z_pos`are viewer`away/closer` intents.
3. Runtime remaps `x/z` intents by current yaw.
4. Runtime remaps `move_w_neg/move_w_pos` to the currently displayed layer axis in 4D view decomposition (identity=`w`, `xw` view=`x`, `zw` view=`z`).

#### `full` profile

1. Move `x-`/`x+`:`Numpad4`/`Numpad6`
2. Move `z-`/`z+`:`Numpad8`/`Numpad2`
3. Move `w-`/`w+`:`Numpad7`/`Numpad9`
4. Exploration vertical `y-`/`y+`:`Numpad1`/`Numpad3`
5. Soft drop: `Numpad5`
6. Hard drop: `Numpad0`
7. Rotate `x-y +`/`x-y -`:`Q`/`W`
8. Rotate `x-z +`/`x-z -`:`A`/`S`
9. Rotate `y-z +`/`y-z -`:`Z`/`X`
10. Rotate `x-w +`/`x-w -`:`R`/`T`
11. Rotate `y-w +`/`y-w -`:`F`/`G`
12. Rotate `z-w +`/`z-w -`:`V`/`B`

#### 4D view group (profile-independent default)

1. Yaw `-`/`+`:`J`/`L`
2. Pitch `-`/`+`:`O`/`U`
3. Zoom out / in: `-`/`+`
4. View `xw -/+`: `1`/`2`
5. View `zw -/+`: `3`/`4`
6. Reset view: `Backspace`(implemented deconflict from gameplay`rotate_zw -`)
7. Conflict policy: gameplay `rotate_xw/*` and `rotate_zw/*` always keep priority over camera actions unless explicitly rebound by user.

#### 4.3.1 `macbook` profile (no function keys)
1. 4D gameplay uses compact defaults except `w` translation (`,`/`.`).
2. 4D view `xw -/+`: `1`/`2`.
3. 4D view `zw -/+`: `3`/`4`.
4. Help key default: `Tab`.

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

1. Menu shortcut `L`-> load selected profile for current dimension.
2. Menu shortcut `S`-> save selected profile for current dimension.
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
2. Setup menu (`Controls`->`Edit Keybindings`)
3. Pause menu (`Settings`->`Controls`->`Edit Keybindings`)
4. The editor must list bindable actions grouped as:
5. `General / System`
6. `Gameplay / Translation`
7. `Gameplay / Rotation`
8. `Camera / View` (3D/4D only)
8. Each row must show action name plus currently assigned keys.
9. Footer hints must expose: `Rebind`,`Clear`,`Load`,`Save`,`Save As`,`Reset`.
10. Failed operations (invalid file, duplicate profile, write error) must show non-blocking error text.
11. Editor must show conflict strategy (`replace`,`swap`,`cancel`) and let user cycle it.

### 5.6 Non-default profile support

1. Profiles are not limited to `small`and`full`; user-defined names are required.
2. Required operations:
3. Create profile (clone from current/built-in)
4. Rename profile
5. Delete profile (except protected built-ins)
6. Select active profile
7. Save/load per profile and per dimension
8. Built-in profiles (`small`,`full`) remain available as defaults and reset baselines.

### 5.7 Local save/load policy

1. Save/load operations are local filesystem operations only (no network/cloud dependency).
2. Default save target for the active profile is:
3. `keybindings/profiles/<profile>/<dimension>.json`
4. `Save As` must allow writing to a new local profile folder name.
5. `Load` must read the selected local profile file for the current dimension.
6. Invalid/missing files must not crash; loader falls back to defaults and reports status.

### 5.8 Dedicated keybindings setup menu

1. Main menu must include `Settings -> Controls -> Keybindings Setup`.
2. Pause menu must include the same `Keybindings Setup` entry.
3. Both entries open the same editor component and behavior.
4. User can test bindings in a lightweight input-preview subpanel before leaving menu.
5. Main-menu keybinding scope list must present `General` separately from dimension-specific scopes (`2D`,`3D`,`4D`).
6. `General` scope is for shared/system actions and should not be merged into a combined "all bindings" default view.

### 5.9 Default conflict policy for shipped layouts

1. Shipped defaults must avoid startup collisions between gameplay and system actions.
2. If a new default gameplay layout introduces overlap with system keys, system defaults must be reassigned in the same change.
3. User-defined rebind conflicts are still resolved by the runtime conflict strategy (`replace/swap/cancel`).

## 6. JSON/Profile Storage Requirements

### 6.1 File locations

1. Built-in/default compatibility files:
2. `keybindings/2d.json`
3. `keybindings/3d.json`
4. `keybindings/4d.json`
5. Profile-specific files (required for non-default profiles):
6. `keybindings/profiles/<profile>/2d.json`
7. `keybindings/profiles/<profile>/3d.json`
8. `keybindings/profiles/<profile>/4d.json`

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
    "camera": {
      "yaw_neg": ["j"],
      "yaw_pos": ["l"]
    }
  }
}
```

### 6.3 Group requirements by dimension

1. 2D runtime groups: `game`,`system`
2. 3D runtime groups: `game`,`camera`,`system`
3. 4D runtime groups: `game`,`camera`,`system`
4. UI presentation requirement: `game` must be split into `Gameplay / Translation` and `Gameplay / Rotation`.

### 6.4 Compatibility requirement

1. 2D loader must accept both canonical grouped format and legacy flat game-action format under `bindings`.
2. Legacy default files must keep loading even when profile storage is introduced.
3. Legacy `slice` groups/actions in old 3D/4D profile JSON files are ignored on load and removed on next save.

### 6.5 Storage validation requirements

1. JSON writes should be atomic (`temp file`then`replace`) to avoid partial files.
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
ruff check .
pytest -q
```Manual checks:
1. Delete one keybinding file and confirm regeneration on startup.
2. Edit a key in JSON, press `L` in setup menu, and verify behavior in game.
3. Press `S` in setup menu and confirm JSON is updated.
4. Verify 2D ignores ND-only keys.
5. Rebind one action from setup menu and one from pause menu; verify parity.
6. Trigger a key conflict and verify conflict-resolution flow.
7. Save profile locally, restart app, load profile, and verify key behavior persists.
8. In 4D, verify `V/B` (`rotate_zw`) repeatedly work and are not consumed by camera/system keys.
9. Verify `view_xw/*` and `view_zw/*` rotate camera only and do not affect gameplay state.

## 9. Acceptance Criteria

1. All dimensions can load/save keybindings without crash.
2. Small and full profile defaults are documented and reproducible.
3. User can create and use non-default profiles, redefine keys, and persist them.
4. Main/setup and in-game pause sections provide the same keybinding profile actions.
5. JSON schema and group handling are explicit and consistent with code.
6. Tests pass and menu feedback is visible for load/save/rebind/reset actions.
7. Keybinding editor supports local save/load and conflict-safe rebinding.
8. 4D `V/B` rotation path is conflict-free and reliable under key repeat.
9. 4D camera hyperplane actions (`view_xw/*`,`view_zw/*`) are bindable and conflict-safe.

## 11. Implementation Status (2026-02-18)

Implemented in code:
1. Dedicated keybinding setup screen added (`tetris_nd/keybindings_menu.py`).
2. Runtime action groups now include `system`for rebinding visibility alongside`game/camera`.
3. Keybinding editor/help presentation now splits gameplay actions into `Translation` + `Rotation` sections (no slice group).
4. 3D/4D `z`movement defaults use`Up`for`z-`and`Down`for`z+`in small profile; full profile uses`Numpad8`/`Numpad2`.
5. 4D camera reset default is `Backspace`.
6. Small-profile rotation ladder uses keyboard pairs:
7. `2D`: `Q/W`,
8. `3D`: `Q/W`,`A/S`,`Z/X`,
9. `4D`: `Q/W`,`A/S`,`Z/X`,`R/T`,`F/G`,`V/B`.
10. Rebind safety guard prevents camera actions from overriding gameplay/system keys.
11. Keybinding conflict and camera override behavior are covered by tests in `tetris_nd/tests/test_keybindings.py`.
12. In-game pause menus (2D/3D/4D) now include keybinding entry and profile actions:
13. `Keybindings Setup`,`Profile Previous`,`Profile Next`,`Save Keybindings`,`Load Keybindings`.
14. Main keybindings section menu separates `General`from`2D/3D/4D` scopes for clearer navigation.

## 10. Implementation Plan (Keybindings)

1. Implement a shared keybinding editor model and renderer for setup/pause menus.
2. Add action-group metadata so each dimension can render only valid groups/actions.
3. Add rebind capture state with conflict resolution (`replace`,`swap`,`cancel`).
4. Add local profile IO helpers (`load`,`save`,`save_as`,`reset`) with atomic writes.
5. Add test coverage for editor-state transitions and profile file round-trips.
6. Completed:
7. profile actions now include `load/save/save as/reset/create/rename/delete` via keybindings setup + pause entrypoints.
8. reset actions now require confirmation.
9. In-game key helper layout is grouped into clear sections:
10. `Translation`,`Rotation`,`Camera/View`,`System`.
11. arrow-diagram key guides are available in Help UI for translation and rotation.
