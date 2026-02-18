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
13. `DONE` `pytest -q` currently passes (`126 passed`).
14. `DONE` `./scripts/ci_check.sh` is available and remains the expected local CI command.
15. `DONE` P2 frontend split executed:
16. `DONE` launcher flow extracted to `/Users/omer/workspace/test-code/tet4d/tetris_nd/launcher_play.py`.
17. `DONE` launcher settings/audio/display hub extracted to `/Users/omer/workspace/test-code/tet4d/tetris_nd/launcher_settings.py`.
18. `DONE` 3D setup/menu/config extracted to `/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_setup.py`.
19. `DONE` 4D render/view/clear animation layer extracted to `/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_render.py`.
20. `DONE` P3 tuning/tooling executed:
21. `DONE` playbot policy budgets/thresholds retuned in `/Users/omer/workspace/test-code/tet4d/config/playbot/policy.json`.
22. `DONE` offline policy comparison tool added: `/Users/omer/workspace/test-code/tet4d/tools/analyze_playbot_policies.py`.
23. `DONE` Translation/rotation arrow-diagram guide panel integrated into launcher menu, pause menu, unified settings, and keybindings menus.
24. `DONE` Complexity hotspots reduced in:
25. `/Users/omer/workspace/test-code/tet4d/tetris_nd/keybindings_menu.py` (`_run_menu_action`, `run_keybindings_menu`),
26. `/Users/omer/workspace/test-code/tet4d/tetris_nd/launcher_settings.py` (`run_settings_hub_menu`).
27. `DONE` New shared menu helper module added for arrow-diagram guide rendering:
28. `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_control_guides.py`.
29. `DONE` Validation after this batch:
30. `ruff check` passed,
31. `ruff check --select C901` passed,
32. `pytest -q` passed (`126 passed`).
33. `DONE` In-game side panels now include compact translation/rotation diagram guidance via shared control-helper rendering.
34. `DONE` CI now runs across Python `3.11`, `3.12`, `3.13`, and `3.14` via workflow matrix.
35. `DONE` Score analyzer design was codified as a dedicated RDS and initial runtime integration was added:
36. `DONE` config: `/Users/omer/workspace/test-code/tet4d/config/gameplay/score_analyzer.json`,
37. `DONE` runtime module: `/Users/omer/workspace/test-code/tet4d/tetris_nd/score_analyzer.py`,
38. `DONE` HUD summary lines now render quality/board-health/trend in 2D/3D/4D side panels.
39. `DONE` 4D dry-run stability hardening applied (higher dry-run budget floor + deterministic greedy fallback in dry-run path).
40. `DONE` Canonical maintenance contract added in:
41. `/Users/omer/workspace/test-code/tet4d/config/project/canonical_maintenance.json`
42. `DONE` Machine validator added and CI-wired:
43. `/Users/omer/workspace/test-code/tet4d/tools/validate_project_contracts.py` + `/Users/omer/workspace/test-code/tet4d/scripts/ci_check.sh`
44. `DONE` Contract coverage includes docs/help/tests/config synchronization checks.
45. `DONE` Canonical-maintenance expansion connected and enforced:
46. settings/save-state schemas + migration docs,
47. replay manifest + golden fixture directory,
48. help index + help asset manifest,
49. release checklist.
50. `DONE` Score analyzer phase-2 implementation completed:
51. analyzer settings are exposed in unified settings (`Audio/Display/Analytics`),
52. logging toggle persists via menu state and controls event/summary file writes,
53. analyzer protocol/persistence tests added in `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_score_analyzer.py`.
54. `DONE` CI stability follow-up implemented:
55. repeated dry-run stability tool added at `/Users/omer/workspace/test-code/tet4d/tools/check_playbot_stability.py`,
56. wired into local CI script (`/Users/omer/workspace/test-code/tet4d/scripts/ci_check.sh`).
57. `DONE` Small-window readability pass completed:
58. control helper rows now use constrained key/action columns to avoid overlap,
59. help controls page switches to stacked diagram layout on narrow windows.
60. `DONE` `launcher_settings.py` simplified by removing legacy dead paths and retaining one unified settings flow.

## 3. Active Open Backlog / TODO (Unified RDS Gaps + Technical Debt)

1. `CLOSED` No currently open gaps (verified 2026-02-18).
2. Ongoing stability and retuning are now automated:
3. `/Users/omer/workspace/test-code/tet4d/.github/workflows/ci.yml`
4. `/Users/omer/workspace/test-code/tet4d/.github/workflows/stability-watch.yml`
5. `/Users/omer/workspace/test-code/tet4d/tools/check_playbot_stability.py`
6. `/Users/omer/workspace/test-code/tet4d/tools/analyze_playbot_policies.py`
7. keybinding maintainability follow-up completed via:
8. `/Users/omer/workspace/test-code/tet4d/tetris_nd/key_display.py`
9. `/Users/omer/workspace/test-code/tet4d/tetris_nd/keybindings_menu_model.py`
10. dead control-line code removed from `/Users/omer/workspace/test-code/tet4d/tetris_nd/keybindings.py`.
11. menu split-policy enforcement is now config-validated in:
12. `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_config.py` (`settings_category_metrics` + policy checks).
13. help/control-guide coverage completion is tracked by:
14. `/Users/omer/workspace/test-code/tet4d/docs/help/HELP_INDEX.md`,
15. `/Users/omer/workspace/test-code/tet4d/assets/help/manifest.json`,
16. `/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_control_guides.py`.

## 4. Gap Mapping to RDS

1. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_TETRIS_GENERAL.md`: backlog follow-up items are now closed with automated CI + stability-watch workflows.
2. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_PLAYBOT.md`: periodic retuning is now operationalized through scheduled benchmark + policy-analysis workflow.
3. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_MENU_STRUCTURE.md`: guide rollout, menu IA split rules, and helper hierarchy items are now implemented and synced.

## 5. Change Footprint (Current Batch)

1. Key implementation/doc files updated include:
`/Users/omer/workspace/test-code/tet4d/front2d.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_game.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_game.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_render.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/gfx_game.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/control_helper.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/game2d.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/game_nd.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/dry_run.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_playbot.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_score_analyzer.py`,
`/Users/omer/workspace/test-code/tet4d/.github/workflows/ci.yml`,
`/Users/omer/workspace/test-code/tet4d/scripts/ci_check.sh`,
`/Users/omer/workspace/test-code/tet4d/tools/check_playbot_stability.py`,
`/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_SCORE_ANALYZER.md`,
`/Users/omer/workspace/test-code/tet4d/docs/FEATURE_MAP.md`,
`/Users/omer/workspace/test-code/tet4d/README.md`,
`/Users/omer/workspace/test-code/tet4d/config/project/canonical_maintenance.json`,
`/Users/omer/workspace/test-code/tet4d/tools/validate_project_contracts.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_project_contracts.py`,
`/Users/omer/workspace/test-code/tet4d/config/schema/menu_settings.schema.json`,
`/Users/omer/workspace/test-code/tet4d/config/schema/save_state.schema.json`,
`/Users/omer/workspace/test-code/tet4d/docs/migrations/menu_settings.md`,
`/Users/omer/workspace/test-code/tet4d/docs/migrations/save_state.md`,
`/Users/omer/workspace/test-code/tet4d/tests/replay/manifest.json`,
`/Users/omer/workspace/test-code/tet4d/docs/help/HELP_INDEX.md`,
`/Users/omer/workspace/test-code/tet4d/assets/help/manifest.json`,
`/Users/omer/workspace/test-code/tet4d/docs/RELEASE_CHECKLIST.md`.
`/Users/omer/workspace/test-code/tet4d/tetris_nd/help_menu.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/control_helper.py`,
`/Users/omer/workspace/test-code/tet4d/config/menu/structure.json`.
2. New split modules/helpers introduced:
`/Users/omer/workspace/test-code/tet4d/tetris_nd/panel_utils.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/loop_runner_nd.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/front3d_setup.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/front4d_render.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/launcher_play.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/launcher_settings.py`.
3. Offline/stability analysis tooling added:
`/Users/omer/workspace/test-code/tet4d/tools/analyze_playbot_policies.py`.
`/Users/omer/workspace/test-code/tet4d/tools/check_playbot_stability.py`.
4. Runtime policy retuned:
`/Users/omer/workspace/test-code/tet4d/config/playbot/policy.json` (reduced default budgets + tightened benchmark thresholds).
5. New score-analyzer defaults and telemetry hooks added:
`/Users/omer/workspace/test-code/tet4d/config/gameplay/score_analyzer.json`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/score_analyzer.py`.
6. Gap-closure batch additions:
`/Users/omer/workspace/test-code/tet4d/tetris_nd/key_display.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/keybindings_menu_model.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/menu_control_guides.py`,
`/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_menu_policy.py`,
`/Users/omer/workspace/test-code/tet4d/.github/workflows/stability-watch.yml`.

## 6. Source Inputs

1. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_TETRIS_GENERAL.md`
2. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_PLAYBOT.md`
3. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_MENU_STRUCTURE.md`
4. `/Users/omer/workspace/test-code/tet4d/docs/RDS_AND_CODEX.md`
5. `/Users/omer/workspace/test-code/tet4d/config/project/canonical_maintenance.json`
6. Consolidated implementation diffs in current workspace batch.
