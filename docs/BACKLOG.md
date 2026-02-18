# Consolidated Backlog

Generated: 2026-02-18  
Updated: 2026-02-18  
Scope: unified view of implemented change set + unresolved RDS/documentation/code gaps.

## 1. Priority Verification Rules

1. `P1` = user-facing correctness, consistency, and discoverability gaps.
2. `P2` = maintainability and complexity risks that can cause regressions.
3. `P3` = optimization, tuning, and documentation hygiene.

## 2. Unified Change Set (Implemented Baseline)

1. `DONE` Pause/main menu parity updates: launcher and pause both expose settings, bot options, keybindings, help, and quit.
2. `DONE` Keybindings menu now supports `General/2D/3D/4D` scopes and clear category separation (`gameplay/camera/slice/system`).
3. `DONE` General keybindings are now separated in the main keybindings menu (not merged into default dimension views).
4. `DONE` Help expanded to include full key reference, settings reference, concepts, and control animation guidance.
5. `DONE` Keybinding/settings category docs externalized in `/Users/omer/workspace/test-code/tet4d/config/menu/structure.json` and validated in `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_config.py`.
6. `DONE` 4D helper-grid guidance now extends across all rendered `w`-layer boards.
7. `DONE` Pause row handler refactored to table-driven dispatch (complexity hotspot removed).
8. `DONE` Shared 3D/4D side-panel helpers extracted to `/Users/omer/workspace/test-code/tet4d/tetris_nd/panel_utils.py`.
9. `DONE` Shared 3D/4D runtime loop orchestration extracted to `/Users/omer/workspace/test-code/tet4d/tetris_nd/loop_runner_nd.py`.
10. `DONE` RDS wording and status metadata normalized (verified date and active status alignment).
11. `DONE` Baseline CI/runtime verification was previously green for this batch.
12. `DONE` `ruff check` currently passes.
13. `DONE` `pytest -q` currently passes (`121 passed`).
14. `DONE` `./scripts/ci_check.sh` is available and remains the expected local CI command.
15. `DONE` P2 frontend split executed:
16. `DONE` launcher flow extracted to `/Users/omer/workspace/test-code/tet4d/tetris_nd/launcher_play.py`.
17. `DONE` launcher settings/audio/display hub extracted to `/Users/omer/workspace/test-code/tet4d/tetris_nd/launcher_settings.py`.
18. `DONE` 3D setup/menu/config extracted to `/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_setup.py`.
19. `DONE` 4D render/view/clear animation layer extracted to `/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_render.py`.
20. `DONE` P3 tuning/tooling executed:
21. `DONE` playbot policy budgets/thresholds retuned in `/Users/omer/workspace/test-code/tet4d/config/playbot/policy.json`.
22. `DONE` offline policy comparison tool added: `/Users/omer/workspace/test-code/tet4d/tools/analyze_playbot_policies.py`.
23. `DONE` Translation/rotation GIF guide panel integrated into launcher menu, pause menu, unified settings, and keybindings menus.
24. `DONE` Complexity hotspots reduced in:
25. `/Users/omer/workspace/test-code/tet4d/tetris_nd/keybindings_menu.py` (`_run_menu_action`, `run_keybindings_menu`),
26. `/Users/omer/workspace/test-code/tet4d/tetris_nd/launcher_settings.py` (`run_settings_hub_menu`).
27. `DONE` New shared menu helper module added for animated guide rendering:
28. `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_gif_guides.py`.
29. `DONE` Validation after this batch:
30. `ruff check` passed,
31. `ruff check --select C901` passed,
32. `pytest -q` passed (`121 passed`).

## 3. Active Open Backlog / TODO (Unified RDS Gaps + Technical Debt)

1. `OPEN [P3]` Keep one source of truth for simplification debt: sync `/Users/omer/workspace/test-code/tet4d/docs/RDS_AND_CODEX.md` hotspot text with this backlog as code evolves.
2. `OPEN [P3]` Periodic retuning cadence: rerun planner analysis against trend history after major algorithm/piece-set changes.

## 4. Gap Mapping to RDS

1. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_TETRIS_GENERAL.md` (`## 10. Backlog Status`, Remaining follow-up) maps to:
2. frontend split for maintainability (completed in current batch),
3. continued empirical tuning from trend history (operational follow-up remains).
4. remaining operational follow-up: trend-driven retuning cadence and doc/source-of-truth synchronization.
5. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_PLAYBOT.md` (`## 12. Known Gaps and Roadmap`) maps to:
6. continued policy tuning (completed initial retune in current batch, periodic follow-up remains),
7. richer offline analysis tooling (completed in current batch).
7. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_MENU_STRUCTURE.md` maps to:
8. expanded control explainability requirement (GIF guidance in help/menu surfaces) and menu readability consistency.

## 5. Change Footprint (Current Batch)

1. Key implementation/doc files updated include:
`/Users/omer/workspace/test-code/tet4d/front.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/keybindings_menu.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_config.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_game.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_game.py`,
`/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_MENU_STRUCTURE.md`,
`/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_TETRIS_GENERAL.md`.
2. New split modules/helpers introduced:
`/Users/omer/workspace/test-code/tet4d/tetris_nd/panel_utils.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/loop_runner_nd.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_setup.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_render.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/launcher_play.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/launcher_settings.py`.
3. Offline analysis tooling added:
`/Users/omer/workspace/test-code/tet4d/tools/analyze_playbot_policies.py`.
4. Runtime policy retuned:
`/Users/omer/workspace/test-code/tet4d/config/playbot/policy.json` (reduced default budgets + tightened benchmark thresholds).

## 6. Source Inputs

1. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_TETRIS_GENERAL.md`
2. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_PLAYBOT.md`
3. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_MENU_STRUCTURE.md`
4. `/Users/omer/workspace/test-code/tet4d/docs/RDS_AND_CODEX.md`
5. Consolidated implementation diffs in current workspace batch.
