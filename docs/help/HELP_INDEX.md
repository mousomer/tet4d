# Help Index

Canonical help index for launcher, pause menu, and in-game helper surfaces.

## Topics

1. Gameplay basics (`2D/3D/4D`, gravity axis, clear rules)
2. Keybindings (`General`,`2D`,`3D`,`4D`)
3. Movement vs rotation controls
4. Camera controls and slicing
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
15. Grid helper semantics and slice semantics in 3D/4D
16. Exploration mode (no gravity/lock/clear, minimal fitting board)
17. Gameplay help shortcut (`F1`)

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

## Maintenance rule

When adding/removing a menu option or keybinding action, update:
1. this index,
2. `assets/help/manifest.json`,
3. `docs/FEATURE_MAP.md`,
4. `docs/BACKLOG.md`.
