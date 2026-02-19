# Menu Structure RDS

Status: Active v0.6 (Verified 2026-02-19)  
Author: Omer + Codex  
Date: 2026-02-19  
Target Runtime: Python 3.11-3.14 + `pygame-ce`

## 1. Scope

Define a unified, readable, and keyboard/controller-first menu structure for:
1. Launch menus (2D, 3D, 4D entry points)
2. In-game pause menu
3. Settings navigation and editing
4. Reset-to-defaults flow
5. Persistent save/load of menu and settings state
6. Keybinding editor flow with local profile save/load
7. Unified main menu for choosing 2D/3D/4D with shared options
8. Audio, display, and analytics settings (including fullscreen/windowed mode)
9. Helper panel information hierarchy and control-guide visuals

Primary implementation and maintenance files:
1. `front2d.py`
2. `tetris_nd/front3d_game.py`
3. `tetris_nd/frontend_nd.py`
4. `tetris_nd/menu_controls.py`
5. `tetris_nd/menu_keybinding_shortcuts.py`
6. `tetris_nd/menu_config.py`
7. `tetris_nd/help_topics.py`
8. `config/menu/defaults.json`
9. `config/menu/structure.json`
10. `config/help/topics.json`
11. `config/help/action_map.json`

## 2. Design Goals

1. Readable at a glance, with clear hierarchy and focus state.
2. Easy to use with keyboard-only and controller digital input.
3. Consistent interaction model across all menus and modes.
4. Allow quick settings changes without extra navigation depth.
5. Support safe reset-to-defaults and explicit save state actions.
6. Ensure display mode transitions never corrupt menu/game layout.

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
5. WCAG 2.2 consistent help placement guidance (help available in predictable location).  
   Reference: [Consistent Help](https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html)
6. WAI-ARIA APG menu interaction model (predictable keyboard semantics for menu button and menubar patterns).  
   References: [Menu Button](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/), [Menu And Menubar](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/)
7. Microsoft menu/flyout guidance (context relevance, concise labels, and flyout role boundaries).  
   Reference: [Menu And Context Flyouts](https://learn.microsoft.com/en-us/windows/apps/design/controls/menu-and-context-flyouts)
8. Material menu guidance (flat/scanable options, limited nesting depth, non-navigation misuse avoidance).  
   Reference: [Material Menus](https://m1.material.io/components/menus.html)
9. Content-structure guidance for scannable support docs and front-loaded headings.  
   Reference: [ONS Structuring Content](https://service-manual.ons.gov.uk/content/writing-for-users/structuring-content)

## 4. Target Information Architecture

### 4.1 Global top-level menu map

```text
Main Menu
├── Play 2D
├── Play 3D
├── Play 4D
├── Help
│   ├── Controls (2D/3D/4D)
│   ├── Scoring
│   ├── Piece Sets
│   ├── Bots
│   └── Slicing / Views
├── Settings
│   ├── Audio
│   ├── Display
│   └── Analytics
├── Keybindings Setup
│   ├── General
│   ├── 2D
│   ├── 3D
│   └── 4D
├── Bot Options
│   ├── Dimension (2D/3D/4D)
│   ├── Playbot mode
│   ├── Bot algorithm
│   ├── Bot profile
│   ├── Bot speed
│   └── Bot budget (ms)
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
4. Setup screens must include piece set source options (native, embedded lower-dimensional, random-cell, debug).
5. Setup screens must use the same layout skeleton and footer shortcuts.
6. Setup screens must expose topology preset selector:
7. `bounded`,`wrap_all`,`invert_all`.
8. Topology remains a dimension-specific gameplay setting (not a global settings-hub toggle).
9. Advanced topology designer controls stay hidden unless `Topology advanced` is enabled.
10. Advanced controls include `Topology profile` selector sourced from `config/topology/designer_presets.json`.

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
11. `Toggle Fullscreen`
12. `Adjust Audio`
13. `Toggle Score Logging`

### 7.2 Persistence model

Add persistent settings file:
1. `state/menu_settings.json` Minimum schema:
```json
{
  "version": 1,
  "last_mode": "4d",
  "active_profile": "small",
  "display": {
    "fullscreen": false,
    "windowed_size": [1200, 760]
  },
  "audio": {
    "master_volume": 0.8,
    "sfx_volume": 0.7,
    "mute": false
  },
  "settings": {
    "2d": {"width": 10, "height": 20, "speed_level": 1, "piece_set_index": 0, "topology_mode": 0, "topology_advanced": 0, "topology_profile_index": 0, "bot_mode_index": 0, "bot_algorithm_index": 0, "bot_profile_index": 1, "bot_speed_level": 7, "bot_budget_ms": 12},
    "3d": {"width": 6, "height": 18, "depth": 6, "speed_level": 1, "piece_set_index": 0, "topology_mode": 0, "topology_advanced": 0, "topology_profile_index": 0, "bot_mode_index": 0, "bot_algorithm_index": 0, "bot_profile_index": 1, "bot_speed_level": 7, "bot_budget_ms": 24},
    "4d": {"width": 10, "height": 20, "depth": 6, "fourth": 4, "speed_level": 1, "piece_set_index": 0, "topology_mode": 0, "topology_advanced": 0, "topology_profile_index": 0, "bot_mode_index": 0, "bot_algorithm_index": 0, "bot_profile_index": 1, "bot_speed_level": 7, "bot_budget_ms": 36}
  }
}
```

### 7.3 Save/load policy

1. Save must be explicit from menu action (no silent overwrite on every keypress).
2. Save/load must be profile-scoped.
3. Optional auto-save on successful game start is allowed and should run without confirmation.
4. If auto-save is enabled, it complements explicit `Save`; it must not remove explicit save actions.
5. Auto-save status feedback should be concise and non-intrusive (for example: `Autosaved` line in launcher).
6. On invalid/corrupt save data, fall back to defaults and show non-blocking warning.
7. Keybinding save/load is local and profile-scoped under `keybindings/profiles`.
8. Display and audio settings are persisted in the same settings state.
9. Analytics settings are persisted in the same settings state.

### 7.5 Category depth/split rule

1. Keep a settings category top-level when it remains small and quick:
2. `<= 5` adjustable fields,
3. `<= 2`action rows (` Apply/Save/Reset` style),
4. no nested mode-specific branching required.
5. Split category into a dedicated submenu when any threshold is exceeded:
6. `>= 6` adjustable fields, or
7. category requires separate basic/advanced groups, or
8. category introduces mode-specific variants that reduce scanability.
9. Current policy:
10. `Audio`and`Display`remain top-level in`Settings` while they stay below threshold.
11. If either expands beyond threshold, promote that category into its own submenu and keep top-level rows as entry points.

### 7.4 Reset-to-defaults policy

1. Reset action must always open confirmation:
2. `Confirm Reset`
3. `Cancel`
4. Reset should affect selected profile by default, with optional “Reset all profiles”.

## 8. Error Handling Requirements

1. File read/write errors must not crash menu flow.
2. Error messages must be plain language and include next step.
3. If settings file is missing, recreate with defaults.
4. If keybinding profile files are missing, recreate from selected profile defaults.
5. If fullscreen toggle fails, continue in windowed mode and show warning.

## 9. Implementation Notes (Current)

1. Extract reusable menu view model:
2. `tetris_nd/menu_model.py`
3. Extract persistence helpers:
4. `tetris_nd/menu_persistence.py`
5. Keep mode-specific field lists in existing frontend files.
6. Reuse `menu_controls.py` for action dispatch; extend with reset/apply/cancel actions.
7. Keep profile actions identical in main/setup and pause menus.

## 10. Testing Instructions

Required checks after implementation:
```bash
ruff check .
pytest -q
```Manual tests:
1. Keyboard-only navigation across all menu screens.
2. Controller digital input parity (where available).
3. Save, quit, relaunch, load: values persist correctly.
4. Reset-to-defaults confirmation works and is reversible via cancel.
5. Corrupt `menu_settings.json` fallback path.
6. Non-default profile create/rename/delete and profile-specific load/save.
7. Edit keybindings in setup and pause menus; save and reload locally.
8. Toggle fullscreen in setup, start game, return to menu, and verify layout size remains correct.
9. Change audio settings, restart app, and verify persistence.

## 11. Implementation Additions (Completed)

1. Shared `Edit Keybindings` submenu is reused by setup and pause flows.
2. Menu depth remains shallow (top-level -> setup/options -> edit actions).
3. Profile file actions (`Load`,`Save`,`Save As`,`Reset`) are integrated and consistent.
4. Keybindings menu parity is enforced between setup and pause routes.
5. In-game key helper is grouped into `Translation`,`Rotation`,`Camera/View`,`Slice`,`System`.
6. Help/Controls includes simple arrow-diagram previews for translation and rotation.

## 12. Stabilization Additions (Completed)

1. Shared startup flow is implemented via unified launcher and mode setup paths.
2. Dedicated `Keybindings Setup` screen is implemented.
3. Unified settings hub (`audio/display/analytics`) is implemented.
4. Display settings (`fullscreen`,`windowed size`,`reset`) are included in the unified hub.
5. Shared display-state manager handles layout refresh after display-mode changes.
6. Fullscreen return-to-menu shrinkage issue is resolved.
## 13. Acceptance Criteria

1. Menu hierarchy is consistent in 2D/3D/4D entrypoints and pause menu.
2. All required actions exist: settings change, reset defaults, save state, load state.
3. Profile actions are identical in main/setup and pause menus.
4. Non-default profiles can be redefined, saved, and loaded.

## 14. Implementation Status (2026-02-18)

Implemented in code:
1. Unified launcher added at `front.py`.
2. Main menu includes `Play 2D`,`Play 3D`,`Play 4D`,`Settings`,`Keybindings Setup`,`Bot Options`, and`Quit`.
3. `Settings` submenu unifies audio, display, and analytics controls.
4. `Bot Options` submenu centralizes bot mode/algorithm/profile/speed/budget with per-dimension selection.
5. 2D/3D/4D setup menus are dimension-specific only (shared controls removed).
6. Keybindings setup is a dedicated screen (`tetris_nd/keybindings_menu.py`) with grouped actions and conflict mode controls.
7. Defaults and menu structures are externalized:
8. `config/menu/defaults.json`
9. `config/menu/structure.json`
10. User overrides remain in `state/menu_settings.json`.
11. If the user settings file is missing/corrupt, runtime falls back to external defaults (not hardcoded literals).

Stabilization details:
1. Returning from gameplay to menu now reapplies persisted display mode.
2. Windowed size is captured and persisted after game sessions in windowed mode.
3. Focus and contrast states remain readable in default window sizes.
4. No crashes on missing/corrupt settings files.
5. Tests pass and base lint passes; remaining follow-up is tracked in `docs/BACKLOG.md`.
6. Fullscreen/window transitions no longer produce shrunken menu layouts.
7. Unified main menu controls 2D/3D/4D startup consistently.
8. In-game pause menu is implemented in all modes with:
9. resume/restart/back-to-main/quit actions
10. settings submenu (audio/display edits + save/reset)
11. keybindings editor entry
12. profile cycle and per-dimension keybinding load/save actions
13. Help menu is implemented in launcher and pause flows, including controls/scoring/piece sets/bots/slicing guidance.
14. Shared menu helpers were added in:
15. `tetris_nd/menu_model.py`
16. `tetris_nd/menu_persistence.py`
17. Keybindings menu supports `General/2D/3D/4D` scopes with explicit category descriptions loaded from menu structure config.
18. Pause menu row execution is table-driven, reducing branching complexity and improving parity maintenance.
19. 4D helper-grid mode now highlights guide intersections across all visible layer boards, not only the active layer.
20. Setup menus now include persisted topology presets (`bounded`,`wrap_all`,`invert_all`) per dimension.

## 15. Follow-up Status

1. Closed (`BKL-P2-006`): help/menu information architecture restructure is complete.
2. Closed (`BKL-P2-006`): help content synchronization with live keybindings/settings across launcher and pause is complete.
3. Execution plan for `BKL-P2-006` is documented in:
4. `docs/plans/PLAN_HELP_AND_MENU_RESTRUCTURE_2026-02-19.md`
5. Required execution milestones for `BKL-P2-006`:
6. Closed (`M1`): help-topic registry + action-topic mapping contract implemented via:
7. `config/help/topics.json`, `config/help/action_map.json`,
8. `config/schema/help_topics.schema.json`, `config/schema/help_action_map.schema.json`,
9. runtime validator/loader in `tetris_nd/help_topics.py`,
10. contract checks in `tools/validate_project_contracts.py` and tests in `tetris_nd/tests/test_help_topics.py`.
11. Closed (`M2`): shared layout-zone renderer implemented to eliminate fixed-coordinate overlap risk:
12. shared zone engine in `tetris_nd/menu_layout.py`,
13. help renderer migrated to zone-based layout in `tetris_nd/help_menu.py`,
14. layout regression coverage in `tetris_nd/tests/test_menu_layout.py`.
15. Closed (`M3`): full key/help synchronization + overflow paging behavior implemented via:
16. context/dimension-filtered topic rendering in `tetris_nd/help_topics.py` + `tetris_nd/help_menu.py`,
17. live action->key rows sourced from runtime bindings + `config/help/action_map.json`,
18. explicit subpage controls (`[`/`]`, `PgUp`/`PgDn`) replacing silent truncation,
19. contract lane checks in `tools/validate_project_contracts.py` and regression tests in `tetris_nd/tests/test_help_menu.py`.
20. Closed (`M4`): launcher/pause parity + compact-window validation implemented via:
21. config-driven pause action mapping in `config/menu/structure.json` (`pause_menu_actions`),
22. parity enforcement in `tetris_nd/menu_config.py` (`_enforce_menu_entrypoint_parity`),
23. pause runtime actions sourced from config in `tetris_nd/pause_menu.py`,
24. compact-window help behavior in `tetris_nd/help_menu.py` (`is_compact_help_view` + compact layout/content policy),
25. compact thresholds in `config/project/constants.json` (`layout.help.compact_*_threshold`),
26. M4 regression coverage in `tetris_nd/tests/test_menu_policy.py` and `tetris_nd/tests/test_help_menu.py`.
27. Arrow-diagram control guidance is implemented across launcher/pause/settings/keybindings and in-game side panels.
28. Very-small-window readability tuning for controls/help layouts is implemented.
29. Maintainability decomposition follow-up for keybinding modules is implemented (`key_display.py`,`keybindings_menu_model.py`, dead-control-line cleanup).
30. Help coverage expansion and menu parity pages are implemented.
31. Settings split-policy enforcement is implemented in runtime config validation (`menu_config.py`+`settings_category_metrics`).
32. Source-of-truth status is synchronized via `docs/BACKLOG.md`.
33. Closed: advanced topology-designer submenu controls are implemented with hidden-by-default profile selection.
