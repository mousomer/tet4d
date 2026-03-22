# Menu Structure RDS

Status: Active v0.8 (Verified 2026-02-21)  
Author: Omer + Codex  
Date: 2026-02-20  
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
9. Helper panel information hierarchy and control-guide visuals, including the
   frozen topology-playground visible shell

Primary implementation and maintenance files:
1. `src/tet4d/ui/pygame/front2d_game.py`
2. `src/tet4d/ui/pygame/front2d_setup.py`
3. `src/tet4d/ui/pygame/front2d_loop.py`
4. `src/tet4d/ui/pygame/front2d_session.py`
5. `src/tet4d/ui/pygame/front2d_frame.py`
6. `src/tet4d/ui/pygame/front2d_results.py`
7. `src/tet4d/ui/pygame/front3d_game.py`
8. `src/tet4d/ui/pygame/front4d_game.py`
9. `src/tet4d/ui/pygame/frontend_nd_setup.py`
10. `src/tet4d/ui/pygame/frontend_nd_state.py`
11. `src/tet4d/ui/pygame/frontend_nd_input.py`
12. `src/tet4d/ui/pygame/launch/settings_hub_model.py`
13. `src/tet4d/ui/pygame/launch/settings_hub_actions.py`
14. `src/tet4d/ui/pygame/launch/launcher_settings.py`
15. `src/tet4d/ui/pygame/menu/menu_controls.py`
16. `src/tet4d/ui/pygame/menu/menu_keybinding_shortcuts.py`
17. `src/tet4d/ui/pygame/menu/setup_menu_runner.py`
18. `src/tet4d/engine/runtime/menu_config.py`
19. `src/tet4d/engine/runtime/help_topics.py`
20. `config/menu/defaults.json`
21. `config/menu/structure.json`
22. `config/help/topics.json`
23. `config/help/action_map.json`

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
|-- Play
|   |-- Play 2D
|   |-- Play 3D
|   |-- Play 4D
|   |-- Play Last Custom Topology
|   |-- Bot
|   `-- Leaderboard
|-- Continue
|-- Tutorials
|   |-- Interactive Tutorials
|   |   |-- Play 2D Tutorial
|   |   |-- Play 3D Tutorial
|   |   `-- Play 4D Tutorial
|   |-- How to Play
|   |-- Controls Reference
|   `-- Help / FAQ
|-- Topology Playground
|-- Settings
|   |-- Game
|   |-- Display
|   |-- Audio
|   |-- Controls
|   |-- Profiles
|   `-- Advanced
`-- Quit
```

### 4.2 In-game pause menu map

```text
Pause Menu
|-- Resume
|-- Restart Run
|-- Settings (same shared sections as launcher)
|-- Controls
|-- Help
|-- Leaderboard
|-- Bot
|-- Back To Main Menu
`-- Quit
```

### 4.3 Setup screens (mode-specific)

1. 2D setup must expose at least: width, height, speed.
2. 3D setup must expose at least: width, height, depth, speed.
3. 4D setup must expose at least: width, height, depth, w, speed, 4D piece set.
4. Setup screens must include piece set source options (native, embedded lower-dimensional, random-cell, debug).
5. Setup screens must use the same layout skeleton and footer shortcuts.
6. Setup screens must expose the safe topology preset selector:
7. `bounded`,`wrap_all`,`invert_all`.
8. Ordinary play setup screens keep only minimal safe topology selection for the migrated path; they do not own custom topology profile editing.
9. Shared settings hub owns `Random type`, the shared rotation animation mode selector, kick permissiveness (`kick_level`), separate `2D`/`ND` rotation animation durations plus shared translation animation duration, and other shared gameplay controls; rigid `2D` rotation must use the same topology-aware overlay path in bounded and wrapped/custom-topology play rather than a bounded-only sprite fallback, and the hub must not advertise full custom-topology editing.
10. `Play Last Custom Topology` and the root `Topology Playground` action are the direct launcher routes into custom topology play/edit flows.
11. `kick_level` is a shared gameplay rule, not a per-mode setup field, and persists in `state/menu_settings.json`.
12. `Tutorials` is the learning/support umbrella, but `Interactive Tutorials`,
    `How to Play`, `Controls Reference`, and `Help / FAQ` must remain explicit
    sibling destinations.
13. `Settings -> Controls` is for persistent input configuration only; controls
    reference/help content must stay under `Tutorials` or another explicit
    learning/reference surface.

## 5. Layout and Readability Requirements

### 5.1 Layout

1. Launcher and ordinary menus use a three-zone layout:
2. Header (screen title + current section)
3. Content panel (focusable options)
4. Footer (shortcut hints + status messages)
5. The frozen Topology Playground shell uses:
6. compact top bar
7. contextual left sidebar
8. larger center workspace
9. small right helper
10. compact bottom strip

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

1. The same key should never mean "confirm" in one menu and "cancel" in another.
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
10. Runtime window resize events in windowed mode must persist `display.windowed_size` to `state/menu_settings.json` as user override state.
11. Runtime resize persistence must never mutate `config/menu/defaults.json`.

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
4. Reset should affect selected profile by default, with optional "Reset all profiles".

## 8. Error Handling Requirements

1. File read/write errors must not crash menu flow.
2. Error messages must be plain language and include next step.
3. If settings file is missing, recreate with defaults.
4. If keybinding profile files are missing, recreate from selected profile defaults.
5. If fullscreen toggle fails, continue in windowed mode and show warning.

## 9. Implementation Notes (Current)

1. Menu graph source-of-truth lives in `config/menu/structure.json` under `menus` and `menu_entrypoints`.
2. Runtime graph parsing/validation lives in `src/tet4d/engine/runtime/menu_config.py` with legacy fallback support for older payloads.
3. Generic runtime navigation and dispatch lives in:
4. `src/tet4d/ui/pygame/menu/menu_runner.py` (`MenuRunner`, `ActionRegistry`).
5. Launcher and pause menus must consume graph items; no hardcoded tree/picker lists in runtime modules.
6. Menu graph lint contract lives in:
7. `src/tet4d/engine/ui_logic/menu_graph_linter.py` + `tools/governance/lint_menu_graph.py`.

## 10. Testing Instructions

Required checks after implementation:
```bash
ruff check .
pytest -q
python tools/governance/lint_menu_graph.py
python tools/governance/validate_project_contracts.py
```
Manual tests:
1. Keyboard-only navigation across all menu screens.
2. Controller digital input parity (where available).
3. Save, quit, relaunch, load: values persist correctly.
4. Reset-to-defaults confirmation works and is reversible via cancel.
5. Corrupt `menu_settings.json` fallback path.
6. Non-default profile create/rename/delete and profile-specific load/save.
7. Edit keybindings in setup and pause menus; save and reload locally.
8. Toggle fullscreen in setup, start game, return to menu, and verify layout size remains correct.
9. Resize window during gameplay and verify the new `windowed_size` is persisted in `state/menu_settings.json` and used on next startup.
9. Change audio settings, restart app, and verify persistence.

## 11. Implementation Additions (Completed)

1. Shared `Edit Keybindings` submenu is reused by setup and pause flows.
2. Menu depth remains shallow (top-level -> setup/options -> edit actions).
3. Profile file actions (`Load`,`Save`,`Save As`,`Reset`) are integrated and consistent.
4. Keybindings menu parity is enforced between setup and pause routes.
5. In-game helper panel membership/order is data-driven from
   `config/help/layout/runtime_help_action_layout.json` using stable
   panel/line IDs, per-mode includes, and runtime `requires` predicates.
6. Engine runtime decides helper-line feasibility (capabilities/settings),
   while UI renderer only resolves key labels/tokens and draws the rows.
7. Runtime side panel uses a unified hierarchy across 2D/3D/4D:
8. Tier 1 `Main` panel includes title + score/lines/speed summary rows plus main controls.
9. Tier 2 is `Translation`; Tier 3 is `Rotation`; Tier 4 is `Camera`.
10. Tier 5 is a dedicated `Data` panel (runtime/bot/analysis lines).
11. Overlay/projection helper actions are rendered inside `Camera` (not a separate panel).
12. Rotation helper rows are complete per mode in runtime side panels:
    2D: 1 pair, 3D: 3 pairs, 4D: 6 pairs.
13. Side-panel content composition (summary + data) uses one shared helper path for
    2D/3D/4D to avoid tier drift across dimensions.
14. Runtime side-panel rendering should use shared adapter:
15. `draw_unified_game_side_panel(...)` in `src/tet4d/ui/pygame/render/panel_utils.py`.
16. Help/Controls includes simple arrow-diagram previews for translation and rotation.
17. For topology-playground migration/state questions, `docs/plans/topology_playground_current_authority.md` is the current authority; older topology-playground manifests and stage plans are historical unless explicitly reactivated.
18. Explorer Playground primary workspace controls must expose `Editor`, `Sandbox`, and `Play` as the only top-level workspace buttons.
19. Explorer Playground helper/status scaffolding must be keyed to the canonical workspace model (`editor`, `sandbox`, `play`) rather than treating legacy `Inspect` / `Edit` labels as the primary top-level structure. New helper code should prefer Editor/Probe/workspace naming, and any retained legacy inspect naming must be limited to compatibility input normalization rather than active runtime/UI flow.
20. Editor-tool selection must live in contextual secondary controls or compatibility shortcuts; selecting an Editor tool must not mutate topology until an explicit apply/place/toggle action is invoked. Contextual row ownership and helper/status copy should stay isolated in dedicated helper modules so `Editor`-owned `Trace`, `Editor`-owned `Probe Neighbors`, and `Sandbox`-owned `Neighbors` remain explicit in code as well as UI, and workspace-shell helpers should read stable scene/value selectors rather than private `controls_panel.py` adjustment helpers. Retired `explorer_profile` / `explorer_draft` shell mirrors must not retake authority through menu/helper code, and probe-state helper/menu code must use canonical probe selectors instead of any resurrected raw probe storage.
21. The legacy Inspect dot is the Editor probe/dot. Its movement, rendered dot position, and trace must stay consistent across seam traversal and across `2D`, `3D`, and `4D`; the Editor probe must not reuse sandbox-piece box semantics.
22. Editor trace visibility must be an explicit `Trace` contextual control owned by `Editor`, and disabling trace must not hide or disable the editor probe itself. `Probe Neighbors` must be a distinct Editor-owned optional dot overlay derived from canonical probe state.
23. Explorer Playground sandbox helper/status content must surface neighbor-search as explicit `Neighbors` `on` / `off` state owned by `Sandbox` instead of hiding it as dimension-specific behavior. Sandbox neighbor markers must appear as small dots only when that control is enabled, remain distinct from sandbox piece boxes, and stay separate from the Editor-owned `Probe Neighbors` overlay.
24. Sandbox must show a sandbox piece by default on entry in `2D`, `3D`, and `4D`, and sandbox projection focus must stay coupled to a visible sandbox cell so the `3D`/`4D` piece remains on-screen after entry and movement.
25. In `3D` and `4D`, projected sandbox piece cells must render as full box-shaped piece cells rather than as neighbor-style dots.
26. Explorer Playground must keep an explicit right-side helper panel visible in the shell outside the explorer viewport, and that panel must stay concise: minimal movement keys, minimal rotation keys, and at most one short current workspace/tool context line rather than a full status dump or shadow menu.
27. Neighbor dots must remain visually distinct from sandbox piece cells and must disappear entirely when the explicit `Neighbor` control is off.
28. Menu items and critical workspace controls in the Explorer shell must be fully visible and readable; clipped or partially hidden controls are layout regressions.

## 12. Stabilization Additions (Completed)

1. Shared startup flow is implemented via unified launcher and mode setup paths.
2. Dedicated controls-settings screen is implemented (backed by `src/tet4d/ui/pygame/menu/keybindings_menu.py`) for persistent input configuration.
3. Unified settings hub (`audio/display/game/advanced/analytics` via one shared surface) is implemented.
4. Display settings (`fullscreen`,`windowed size`,`reset`) are included in the unified hub.
5. Shared display-state manager handles layout refresh after display-mode changes.
6. Fullscreen return-to-menu shrinkage issue is resolved.
## 13. Acceptance Criteria

1. Menu hierarchy is consistent in 2D/3D/4D entrypoints and pause menu.
2. All required actions exist: settings change, reset defaults, save state, load state.
3. Profile actions are identical in main/setup and pause menus.
4. Non-default profiles can be redefined, saved, and loaded.

## 14. Implementation Status (2026-02-21)

Implemented in code:
1. Unified launcher added at `front.py`.
2. Main menu root includes `Play`,`Continue`,`Tutorials`,`Topology Playground`,`Settings`, and `Quit`.
3. `Tutorials` keeps separate learning/support destinations for interactive tutorials, how-to-play guidance, controls reference, and help/FAQ.
4. `Settings` submenu uses short section labels (`Game`,`Display`,`Audio`,`Controls`,`Profiles`,`Advanced`) while reusing the shared settings/keybindings surfaces underneath.
5. `Bot` and `Leaderboard` are play-adjacent launcher destinations rather than `Settings` entries.
6. 2D/3D/4D setup menus are dimension-specific only (shared controls removed).
7. Controls setup is a dedicated screen (`src/tet4d/ui/pygame/menu/keybindings_menu.py`) with grouped actions and conflict mode controls.
7. Defaults and menu structures are externalized:
8. `config/menu/defaults.json`
9. `config/menu/structure.json`
10. settings-hub row layout is config-defined in `config/menu/structure.json` (`settings_hub_layout_rows`) and consumed by `src/tet4d/ui/pygame/launch/settings_hub_model.py` + `src/tet4d/ui/pygame/launch/launcher_settings.py`.
11. gameplay option labels used across setup/settings (for example random mode) are sourced from `config/menu/structure.json` (`settings_option_labels`) without Python fallback literals.
12. setup hint copy for `2D/3D/4D` is sourced from
    `config/menu/structure.json` (`setup_hints`) and consumed by `frontend_nd_setup.py`.
13. pause subtitle/hint copy is sourced from `config/menu/structure.json`
    (`pause_copy`) and consumed by `runtime_ui/pause_menu.py`.
14. launcher/settings/keybindings/bot/setup UI copy is sourced from
    `config/menu/structure.json` (`ui_copy`) and consumed via
    `menu_structure_schema.py` + `menu_config.py` accessors in the UI adapters.
15. User overrides remain in `state/menu_settings.json`.
16. If the user settings file is missing/corrupt, runtime falls back to external defaults (not hardcoded literals).

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
10. settings routed to shared settings hub (audio/display/gameplay/analytics + save/reset/back)
11. keybindings editor entry
12. profile cycle and per-dimension keybinding load/save actions
13. Help menu is implemented in launcher and pause flows, including controls/scoring/piece sets/bots/view guidance.
14. Shared menu helpers were added in:
15. `src/tet4d/ui/pygame/menu/keybindings_menu_model.py`
16. `src/tet4d/engine/runtime/menu_settings_state.py`
17. Keybindings menu supports `General/2D/3D/4D` scopes with explicit category descriptions loaded from menu structure config.
18. Pause menu row execution is table-driven, reducing branching complexity and improving parity maintenance.
19. 4D helper-grid mode now highlights guide intersections across all visible layer boards, not only the active layer.
20. Setup menus now include persisted topology presets (`bounded`,`wrap_all`,`invert_all`) per dimension.
21. Launcher and pause menu trees now run through one generic graph runtime (`src/tet4d/ui/pygame/menu/menu_runner.py`) with per-surface action registries.
22. Hardcoded play-mode picker was removed from `front.py`; mode options now come from `config/menu/structure.json` (`menus.launcher_play`).
23. Top-level IA is frozen to `Play`, `Continue`, `Tutorials`, `Topology Playground`, `Settings`, and `Quit`.
24. `Tutorials` keeps `Interactive Tutorials`, `How to Play`, `Controls Reference`, and `Help / FAQ` as explicit siblings rather than collapsing help into tutorials.
25. `Settings -> Controls` and `Tutorials -> Controls Reference` are distinct destinations and must not share one ambiguous `Controls` label.
26. `Leaderboard` and `Bot` remain off the root layer and off `Settings`; they live in the play-adjacent launcher flow instead.
27. Launcher subtitles and route-action mapping are config-driven in
    `config/menu/structure.json` (`launcher_subtitles`, `launcher_route_actions`);
    no launcher subtitle copy or route-label mapping remains hardcoded in `front.py`.
28. Legacy duplicated `launcher_menu` rows were removed; launcher action rows are
    now derived from graph root menu items (`menus.launcher_root.items`).
29. Menu graph lint contract is enforced via:
30. `src/tet4d/engine/ui_logic/menu_graph_linter.py`,
31. `tools/governance/lint_menu_graph.py`,
32. `tools/governance/validate_project_contracts.py`,
33. `scripts/ci_check.sh`.

## 15. Follow-up Status

1. Closed (`BKL-P2-006`): help/menu information architecture restructure is complete.
2. Closed (`BKL-P2-006`): help content synchronization with live keybindings/settings across launcher and pause is complete.
3. Execution plan for `BKL-P2-006` is documented in:
4. `docs/plans/PLAN_HELP_AND_MENU_RESTRUCTURE_2026-02-19.md`
5. Required execution milestones for `BKL-P2-006`:
6. Closed (`M1`): help-topic registry + action-topic mapping contract implemented via:
7. `config/help/topics.json`, `config/help/action_map.json`,
8. `config/schema/help_topics.schema.json`, `config/schema/help_action_map.schema.json`,
9. runtime validator/loader in `src/tet4d/engine/runtime/help_topics.py`,
10. contract checks in `tools/governance/validate_project_contracts.py` and tests in `tests/unit/engine/test_help_topics.py`.
11. Closed (`M2`): shared layout-zone renderer implemented to eliminate fixed-coordinate overlap risk:
12. shared zone engine in `src/tet4d/engine/ui_logic/menu_layout.py`,
13. help renderer migrated to zone-based layout in `src/tet4d/ui/pygame/runtime_ui/help_menu.py`,
14. layout regression coverage in `tests/unit/engine/test_menu_layout.py`.
15. Closed (`M3`): full key/help synchronization + overflow paging behavior implemented via:
16. context/dimension-filtered topic rendering in `src/tet4d/engine/runtime/help_topics.py` + `src/tet4d/ui/pygame/runtime_ui/help_menu.py`,
17. live action->key rows sourced from runtime bindings + `config/help/action_map.json`,
18. explicit subpage controls (`[`/`]`, `PgUp`/`PgDn`) replacing silent truncation,
19. contract lane checks in `tools/governance/validate_project_contracts.py` and regression tests in `tests/unit/engine/test_help_menu.py`.
20. Closed (`M4`): launcher/pause parity + compact-window validation implemented via:
21. config-driven pause action mapping in `config/menu/structure.json` (`pause_menu_actions`),
22. parity enforcement in `src/tet4d/engine/runtime/menu_config.py` (`_enforce_menu_entrypoint_parity`),
23. pause runtime actions sourced from config in `src/tet4d/ui/pygame/runtime_ui/pause_menu.py`,
24. compact-window help behavior in `src/tet4d/ui/pygame/runtime_ui/help_menu.py` (`is_compact_help_view` + compact layout/content policy),
25. compact thresholds in `config/project/constants.json` (`layout.help.compact_*_threshold`),
26. M4 regression coverage in `tests/unit/engine/test_menu_policy.py` and `tests/unit/engine/test_help_menu.py`.
27. Arrow-diagram control guidance is implemented across launcher/pause/settings/keybindings and in-game side panels.
28. Very-small-window readability tuning for controls/help layouts is implemented.
29. Maintainability decomposition follow-up for keybinding modules is implemented (`key_display.py`,`keybindings_menu_model.py`, dead-control-line cleanup).
30. Help coverage expansion and menu parity pages are implemented.
31. Settings split-policy enforcement is implemented in runtime config validation (`menu_config.py`+`settings_category_metrics`).
32. Source-of-truth status is synchronized via `docs/BACKLOG.md`.
33. Closed: advanced topology-designer submenu controls are implemented with hidden-by-default profile selection.
34. Closed (`BKL-P2-009`): duplicate pause-only settings implementation removed; pause `Settings` now routes through the same shared settings hub used by launcher (`Audio`,`Display`,`Game`,`Analytics`,`Save`,`Reset`,`Back`).
35. Closed (`BKL-P2-010`): launcher settings rows are now config-driven via `settings_hub_layout_rows` in `config/menu/structure.json`; hardcoded settings row definitions were removed from `src/tet4d/ui/pygame/launch/launcher_settings.py`.
36. Closed (`BKL-P2-022`): menu graph modularization implemented (`menus` graph + `MenuRunner` + `ActionRegistry` + lint/contract hooks), with launcher and pause migrated off hardcoded trees.
37. Closed (`BKL-P2-023`): Topology Lab interactive workflow is implemented with config-backed copy/layout (`config/topology/lab_menu.json`) and runtime save/export actions (`src/tet4d/ui/pygame/launch/topology_lab_menu.py`).

## 16. Menu Rehaul v2 (Core IA Implemented, `BKL-P1-006`)

Research-driven goals for the next rehaul pass:
1. reduce first-time navigation friction and menu depth,
2. keep high-frequency actions and state visibility in one place,
3. preserve keyboard-only predictability and pause/launcher parity,
4. eliminate remaining panel-density clutter in compact windows.

Guideline basis (re-validated 2026-02-20):
1. Xbox XAG 112/114 for consistent, complete navigation and clear context hierarchy.
2. WCAG 2.2 (`Focus Appearance`, `Contrast Minimum`, `Consistent Help`) for readability and predictable help entry points.
3. WAI-ARIA menu interaction patterns for keyboard semantics.
4. Apple HIG menu guidance (`short list of top-level choices`, `grouping and separators`) for scanability.
5. Game Accessibility Guidelines (`clear language`, `remember settings`, `easy start`) for player-facing friction reduction.

Target IA delta:
1. Replace broad top-level labels with intent labels:
2. `Play`, `Continue`, `Tutorials`, `Topology Playground`, `Settings`, `Quit`.
3. Keep dimension selection under `Play`, keep `Tutorials` as the learning/support umbrella, and keep custom-topology editing under `Topology Playground` without adding extra root clutter.
4. Keep settings/reference separation explicit:
5. `Settings -> Controls` means configuration,
6. `Tutorials -> Controls Reference` means reference/help.
7. Keep `Leaderboard` and `Bot` play-adjacent instead of pushing them into `Settings`.
8. Keep mode-specific settings (`board`, `topology`, `piece set`, `challenge`) inside per-mode setup screens only.

Interaction and layout constraints:
1. Max top-level rows: `6` (including contextual `Continue`).
2. Max submenu depth: `2` (top-level -> section -> editor/action).
3. One primary action per view (`Play` or `Apply`), destructive actions isolated at bottom (`Reset`, `Quit`).
4. Always-visible status line for save/load/autosave feedback.
5. In compact windows, hide non-critical helper blocks before truncating actionable rows.

Execution status:
1. Completed (`R1`): IA and labels rewritten in `config/menu/structure.json`:
2. launcher top-level actions now `Play`,`Continue`,`Tutorials`,`Topology Playground`,`Settings`,`Quit`.
3. Completed (`R2` core): launcher and pause action lists were simplified to core, high-frequency flows.
4. Completed (`R2` follow-up): Tutorials/help and controls-settings/controls-reference splits are now explicit in launcher wording and routing.
5. Completed (`R3/R4`): help/controls discoverability and compact-window regression protections remain enforced by existing layout/help policy and tests.

Execution artifact:
1. Detailed execution plan lives in `docs/plans/PLAN_MENU_REHAUL_V2_2026-02-20.md`.


## 17. Topology Lab Mode Split (2026-03-08)

1. Topology Lab now edits separate topology profiles for `(gameplay mode, dimension)` rather than one shared 3D/4D profile bucket.
2. Required pairs are `normal/3d`, `explorer/3d`, `normal/4d`, and `explorer/4d`.
3. Lab entry flow must expose a gameplay-path chooser plus `Dimension` (`3D`, `4D`); the primary value must read as `Explorer Playground`, while `Normal Game` must be labeled as a legacy-compatibility branch rather than a peer modern editor mode.
4. In `Normal Game`, gravity-axis `Y` boundaries are visually locked and any attempted seam touching `Y+` or `Y-` must be rejected immediately by engine-owned validation.
5. In `Explorer Mode`, `Y` boundaries are selectable and may be wrapped or inverted subject to the general bijection rules.
6. Any retained `Normal Game` row-adjustment support must stay narrow and must not compete visually or structurally with the Explorer Playground editor controls. Legacy row layout/value presentation should stay with the normal menu row/value helpers, and legacy export should not require a separate legacy-support module once direct export orchestration can live elsewhere.
7. Ordinary 2D/3D/4D play setup screens no longer expose `topology_profile_index` or other custom-topology editor rows; custom topology selection belongs to the Explorer Playground only.
