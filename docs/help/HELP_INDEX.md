# Help Index

Canonical help index for launcher, pause menu, and in-game helper surfaces.

## Topics

1. Gameplay basics (`2D/3D/4D`, gravity axis, clear rules)
2. Keybindings (`General`,`2D`,`3D`,`4D`)
3. Movement vs rotation controls
4. Camera and view controls
5. Grid modes (`OFF`,`EDGE`,`FULL`,`HELPER`)
6. Bot modes and planner profiles
7. Scoring and score-analyzer summary lines
8. Settings (audio/display/keybindings/profiles)
9. Challenge mode and debug piece sets
10. Playbot dry-run/stability verification workflow
11. Save/autosave/reset behavior and confirmation rules
12. Fullscreen/window behavior and display troubleshooting
13. Menu parity and settings IA split policy rules
14. Profile workflow (`cycle/create/rename/save-as/delete/reset`)
15. Grid helper semantics across 3D/4D rendered layer boards
16. Exploration mode (no gravity/lock/clear, minimal fitting board)
17. Gameplay help shortcut (`F1`)
18. Boundary topology presets (`bounded`,`wrap_all`,`invert_all`)
19. Gravity-axis wrap policy (default off)
20. Topic subpage paging (`[`/`]`, `PgUp`/`PgDn`) for long help content
21. Live key rows pulled from active keybinding profile per topic
22. Compact help-window policy (reduced non-critical detail first; controls stay available)
23. Launcher/pause parity entry points (`Settings`,`Keybindings`,`Help`,`Bot Options`,`Quit`)

## Control diagrams

1. Translation and rotation guidance is iconized per action row.
2. Primary icon renderer: `tetris_nd/control_icons.py`.
3. Legacy combined guide renderer remains available in:
4. `tetris_nd/menu_control_guides.py`
5. Entry point: `draw_translation_rotation_guides(...)`
6. Surfaces that must expose control visuals:
7. keybindings menus (row icons),
8. help controls page,
9. in-game helper panel.
10. Help topic render path uses:
11. `tetris_nd/help_topics.py` (context/dimension topic filtering)
12. `tetris_nd/help_menu.py` (live key rows + subpage rendering)
13. `config/help/topics.json` + `config/help/action_map.json`

## Maintenance rule

When adding/removing a menu option or keybinding action, update:
1. this index,
2. `assets/help/manifest.json`,
3. `config/help/topics.json`,
4. `config/help/action_map.json`,
5. `docs/FEATURE_MAP.md`,
6. `docs/BACKLOG.md`,
7. `tetris_nd/tests/test_help_topics.py`,
8. `tetris_nd/tests/test_help_menu.py`.
