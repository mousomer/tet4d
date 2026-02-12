# Menu Structure RDS

Status: Draft v0.2  
Author: Omer + Codex  
Date: 2026-02-12  
Target Runtime: Python 3.14 + `pygame-ce`

## 1. Scope

Define a unified, readable, and keyboard/controller-first menu structure for:
1. Launch menus (2D, 3D, 4D entry points)
2. In-game pause menu
3. Settings navigation and editing
4. Reset-to-defaults flow
5. Persistent save/load of menu and settings state
6. Keybinding editor flow with local profile save/load

Primary files impacted by future implementation:
1. `/Users/omer/workspace/test-code/tet4d/front2d.py`
2. `/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_game.py`
3. `/Users/omer/workspace/test-code/tet4d/tetris_nd/frontend_nd.py`
4. `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_controls.py`
5. `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_keybinding_shortcuts.py`

## 2. Design Goals

1. Readable at a glance, with clear hierarchy and focus state.
2. Easy to use with keyboard-only and controller digital input.
3. Consistent interaction model across all menus and modes.
4. Allow quick settings changes without extra navigation depth.
5. Support safe reset-to-defaults and explicit save state actions.

## 3. Research Basis (Best Practices)

This design is based on:
1. Xbox Accessibility Guideline 112 (logical, consistent navigation; keyboard/controller completeness).  
   Reference: [XAG 112](https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/112)
2. Xbox Accessibility Guideline 114 (clear context, labeling, hierarchy, and predictable screen transitions).  
   Reference: [XAG 114](https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/114)
3. WCAG 2.2 readability/focus requirements (contrast and visible focus).  
   References: [Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [Focus Appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance)
4. Nielsen usability heuristics (consistency, user control/freedom, recognition over recall, error prevention).  
   Reference: [NNG Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)

## 4. Target Information Architecture

### 4.1 Global top-level menu map

```text
Main Menu
├── Play
│   ├── 2D Setup
│   ├── 3D Setup
│   └── 4D Setup
├── Settings
│   ├── Gameplay
│   ├── Visual
│   ├── Controls
│   │   └── Edit Keybindings
│   └── Accessibility
├── Profiles
│   ├── Select Profile
│   ├── New Profile
│   ├── Rename Profile
│   ├── Delete Profile
│   ├── Save Profile
│   ├── Load Profile
│   └── Reset Profile To Defaults
└── Quit
```

### 4.2 In-game pause menu map

```text
Pause Menu
├── Resume
├── Restart Run
├── Settings (same shared sections, including Edit Keybindings)
├── Profiles (same actions as Main Menu)
├── Back To Main Menu
└── Quit
```

### 4.3 Setup screens (mode-specific)

1. 2D setup must expose at least: width, height, speed.
2. 3D setup must expose at least: width, height, depth, speed.
3. 4D setup must expose at least: width, height, depth, w, speed, 4D piece set.
4. Setup screens must include piece set source options (native, embedded lower-dimensional, random-cell).
5. Setup screens must use the same layout skeleton and footer shortcuts.

## 5. Layout and Readability Requirements

### 5.1 Layout

1. Use a three-zone layout:
2. Header (screen title + current section)
3. Content panel (focusable options)
4. Footer (shortcut hints + status messages)

### 5.2 Visual hierarchy

1. Focused item must have a high-contrast highlight and shape cue (not color-only).
2. Primary actions (Play, Resume, Save) must be visually stronger than destructive actions.
3. Related settings must be grouped with clear section labels.

### 5.3 Text/readability

1. Default body text should target at least 18 px equivalent in current window scale.
2. Maintain text/background contrast aligned with WCAG minimum guidance.
3. Avoid crowded line wrapping in options; keep one option per row.

## 6. Navigation and Interaction Model

### 6.1 Input behavior

1. `Up/Down`: move focus between rows.
2. `Left/Right`: change current setting value.
3. `Enter`: activate focused action.
4. `Esc`: back/cancel (never destructive).
5. `Tab`: next section when in multi-section settings.

### 6.2 Consistency rules

1. The same key should never mean “confirm” in one menu and “cancel” in another.
2. Linear lists should support optional loop navigation (last->first and first->last).
3. Focus order must match visible order.

### 6.3 Feedback

1. Every action must produce immediate feedback (status line or toast-like message).
2. Save/load/reset outcomes must show explicit success/failure text.

## 7. Settings Change, Reset, and Save State

### 7.1 Required actions

1. `Apply Changes` (in-memory update + immediate preview where possible)
2. `Save Profile` (persist selected profile to disk)
3. `Load Profile` (restore selected profile from disk)
4. `Reset Profile To Defaults` (with confirmation dialog)
5. `Cancel` (discard unsaved changes in current menu session)
6. `Rebind Control` (interactive per-action key capture)
7. `Profile Management` (select/create/rename/delete non-default profiles)
8. `Save Keybindings Locally`
9. `Load Keybindings Locally`
10. `Save Keybindings As New Profile`

### 7.2 Persistence model

Add persistent settings file:
1. `/Users/omer/workspace/test-code/tet4d/state/menu_settings.json`

Minimum schema:
```json
{
  "version": 1,
  "last_mode": "4d",
  "active_profile": "small",
  "settings": {
    "2d": {"width": 10, "height": 20, "speed_level": 1},
    "3d": {"width": 6, "height": 18, "depth": 6, "speed_level": 1},
    "4d": {"width": 10, "height": 20, "depth": 6, "fourth": 4, "speed_level": 1, "piece_set_index": 0}
  }
}
```

### 7.3 Save/load policy

1. Save must be explicit from menu action (no silent overwrite on every keypress).
2. Save/load must be profile-scoped.
3. Optional auto-save on successful game start is allowed only after explicit opt-in.
4. On invalid/corrupt save data, fall back to defaults and show non-blocking warning.
5. Keybinding save/load is local and profile-scoped under `keybindings/profiles`.

### 7.4 Reset-to-defaults policy

1. Reset action must open confirmation:
2. `Confirm Reset`
3. `Cancel`
4. Reset should affect selected profile by default, with optional “Reset all profiles”.

## 8. Error Handling Requirements

1. File read/write errors must not crash menu flow.
2. Error messages must be plain language and include next step.
3. If settings file is missing, recreate with defaults.
4. If keybinding profile files are missing, recreate from selected profile defaults.

## 9. Implementation Plan (Recommended)

1. Extract reusable menu view model:
2. `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_model.py`
3. Extract persistence helpers:
4. `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_persistence.py`
5. Keep mode-specific field lists in existing frontend files.
6. Reuse `menu_controls.py` for action dispatch; extend with reset/apply/cancel actions.
7. Keep profile actions identical in main/setup and pause menus.

## 10. Testing Instructions

Required checks after implementation:
```bash
ruff check /Users/omer/workspace/test-code/tet4d
pytest -q
```

Manual tests:
1. Keyboard-only navigation across all menu screens.
2. Controller digital input parity (where available).
3. Save, quit, relaunch, load: values persist correctly.
4. Reset-to-defaults confirmation works and is reversible via cancel.
5. Corrupt `menu_settings.json` fallback path.
6. Non-default profile create/rename/delete and profile-specific load/save.
7. Edit keybindings in setup and pause menus; save and reload locally.

## 11. Implementation Plan Additions

1. Add a shared `Edit Keybindings` submenu component reused by setup and pause flows.
2. Keep menu depth shallow: no more than 3 levels from top-level to rebind action.
3. Integrate local profile file actions directly in footer shortcuts (`Load`, `Save`, `Save As`, `Reset`).
4. Add setup control for piece set source per mode:
5. native set
6. lower-dimensional embedded set
7. random-cell generated set
8. Ensure switching piece set source is immediate in preview and persisted in settings state.

## 12. Acceptance Criteria

1. Menu hierarchy is consistent in 2D/3D/4D entrypoints and pause menu.
2. All required actions exist: settings change, reset defaults, save state, load state.
3. Profile actions are identical in main/setup and pause menus.
4. Non-default profiles can be redefined, saved, and loaded.
5. Focus and contrast states remain readable in default window sizes.
6. No crashes on missing/corrupt settings files.
7. Tests and lint pass after implementation.
