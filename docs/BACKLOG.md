# Consolidated Backlog

Generated: 2026-02-18  
Updated: 2026-02-19  
Scope: unified view of implemented change set + unresolved RDS/documentation/code gaps.

## 1. Priority Verification Rules

1. `P1`= user-facing correctness, consistency, and discoverability gaps.
2. `P2`= maintainability and complexity risks that can cause regressions.
3. `P3`= optimization, tuning, and documentation hygiene.

## 2. Unified Change Set (Implemented Baseline)

1. `DONE` Pause/main menu parity updates: launcher and pause both expose settings, bot options, keybindings, help, and quit.
2. `DONE`Keybindings menu now supports`General/2D/3D/4D` scopes and clear category separation (`gameplay/camera/slice/system`).
3. `DONE` General keybindings are now separated in the main keybindings menu (not merged into default dimension views).
4. `DONE` Help expanded to include full key reference, settings reference, concepts, and control animation guidance.
5. `DONE`Keybinding/settings category docs externalized in`config/menu/structure.json`and validated in`tetris_nd/menu_config.py`.
6. `DONE`4D helper-grid guidance now extends across all rendered`w`-layer boards.
7. `DONE` Pause row handler refactored to table-driven dispatch (complexity hotspot removed).
8. `DONE`Shared 3D/4D side-panel helpers extracted to`tetris_nd/panel_utils.py`.
9. `DONE`Shared 3D/4D runtime loop orchestration extracted to`tetris_nd/loop_runner_nd.py`.
10. `DONE` RDS wording and status metadata normalized (verified date and active status alignment).
11. `DONE` Baseline CI/runtime verification was previously green for this batch.
12. `DONE` `ruff check` currently passes.
13. `DONE` `pytest -q` currently passes.
14. `DONE` `./scripts/ci_check.sh` is available and remains the expected local CI command.
15. `DONE` P2 frontend split executed:
16. `DONE`launcher flow extracted to`tetris_nd/launcher_play.py`.
17. `DONE`launcher settings/audio/display hub extracted to`tetris_nd/launcher_settings.py`.
18. `DONE`3D setup/menu/config extracted to`tetris_nd/front3d_setup.py`.
19. `DONE`4D render/view/clear animation layer extracted to`tetris_nd/front4d_render.py`.
20. `DONE` P3 tuning/tooling executed:
21. `DONE`playbot policy budgets/thresholds retuned in`config/playbot/policy.json`.
22. `DONE`offline policy comparison tool added:`tools/analyze_playbot_policies.py`.
23. `DONE` Translation/rotation arrow-diagram guide panel integrated into launcher menu, pause menu, unified settings, and keybindings menus.
24. `DONE` Complexity hotspots reduced in:
25. `tetris_nd/keybindings_menu.py` (`_run_menu_action`,`run_keybindings_menu`),
26. `tetris_nd/launcher_settings.py` (`run_settings_hub_menu`).
27. `DONE` New shared menu helper module added for arrow-diagram guide rendering:
28. `tetris_nd/menu_control_guides.py`.
29. `DONE` Validation after this batch:
30. `ruff check` passed,
31. `ruff check --select C901` passed,
32. `pytest -q` passed.
33. `DONE` In-game side panels now include compact translation/rotation diagram guidance via shared control-helper rendering.
34. `DONE`CI now runs across Python`3.11`,`3.12`,`3.13`, and`3.14` via workflow matrix.
35. `DONE` Score analyzer design was codified as a dedicated RDS and initial runtime integration was added:
36. `DONE`config:`config/gameplay/score_analyzer.json`,
37. `DONE`runtime module:`tetris_nd/score_analyzer.py`,
38. `DONE` HUD summary lines now render quality/board-health/trend in 2D/3D/4D side panels.
39. `DONE`4D dry-run stability hardening applied (higher dry-run budget floor + deterministic greedy fallback in dry-run path).
40. `DONE` Canonical maintenance contract added in:
41. `config/project/canonical_maintenance.json`
42. `DONE` Machine validator added and CI-wired:
43. `tools/validate_project_contracts.py`+`scripts/ci_check.sh`
44. `DONE` Contract coverage includes docs/help/tests/config synchronization checks.
45. `DONE` Canonical-maintenance expansion connected and enforced:
46. settings/save-state schemas + migration docs,
47. replay manifest + golden fixture directory,
48. help index + help asset manifest,
49. release checklist.
50. `DONE` Score analyzer phase-2 implementation completed:
51. analyzer settings are exposed in unified settings (`Audio/Display/Analytics`),
52. logging toggle persists via menu state and controls event/summary file writes,
53. analyzer protocol/persistence tests added in `tetris_nd/tests/test_score_analyzer.py`.
54. `DONE` CI stability follow-up implemented:
55. repeated dry-run stability tool added at `tools/check_playbot_stability.py`,
56. wired into local CI script (`scripts/ci_check.sh`).
57. `DONE` Small-window readability pass completed:
58. control helper rows now use constrained key/action columns to avoid overlap,
59. help controls page switches to stacked diagram layout on narrow windows.
60. `DONE` `launcher_settings.py` simplified by removing legacy dead paths and retaining one unified settings flow.
61. `DONE` Local CI runner was hardened to a hermetic Python-module flow:
62. `scripts/ci_check.sh` now requires `ruff` and `pytest` in the selected `PYTHON_BIN`,
63. global command fallback for lint/test runners was removed.
64. `DONE` Local toolchain bootstrap was standardized:
65. `scripts/bootstrap_env.sh` now creates/updates `.venv` and installs `pygame-ce`, `ruff`, and `pytest`.
66. `DONE` Canonical docs freshness checks were strengthened:
67. `tools/validate_project_contracts.py` now supports regex content rules,
68. stale fixed pass-count snapshots are blocked by `must_not_match_regex` rules in `config/project/canonical_maintenance.json`.

## 3. Active Open Backlog / TODO (Unified RDS Gaps + Technical Debt)

1. `P3` Continuous watch only (no blocking open implementation gaps in this batch):
2. keep running `scripts/ci_check.sh` prior to pushes and releases,
3. keep scheduled stability + policy workflows active:
4. `.github/workflows/ci.yml`,
5. `.github/workflows/stability-watch.yml`,
6. `tools/check_playbot_stability.py`,
7. `tools/analyze_playbot_policies.py`.

## 4. Gap Mapping to RDS

1. `docs/rds/RDS_TETRIS_GENERAL.md`: backlog follow-up items are now closed with automated CI + stability-watch workflows.
2. `docs/rds/RDS_PLAYBOT.md`: periodic retuning is now operationalized through scheduled benchmark + policy-analysis workflow.
3. `docs/rds/RDS_MENU_STRUCTURE.md`: guide rollout, menu IA split rules, and helper hierarchy items are now implemented and synced.

## 5. Change Footprint (Current Batch)

1. Key implementation/doc files updated include:
`front2d.py`,
`tetris_nd/front3d_game.py`,
`tetris_nd/front4d_game.py`,
`tetris_nd/front4d_render.py`,
`tetris_nd/gfx_game.py`,
`tetris_nd/control_helper.py`,
`tetris_nd/game2d.py`,
`tetris_nd/game_nd.py`,
`tetris_nd/playbot/dry_run.py`,
`tetris_nd/tests/test_playbot.py`,
`tetris_nd/tests/test_score_analyzer.py`,
`.github/workflows/ci.yml`,
`scripts/ci_check.sh`,
`tools/check_playbot_stability.py`,
`docs/rds/RDS_SCORE_ANALYZER.md`,
`docs/FEATURE_MAP.md`,
`README.md`,
`config/project/canonical_maintenance.json`,
`tools/validate_project_contracts.py`,
`tetris_nd/tests/test_project_contracts.py`,
`config/schema/menu_settings.schema.json`,
`config/schema/save_state.schema.json`,
`docs/migrations/menu_settings.md`,
`docs/migrations/save_state.md`,
`tests/replay/manifest.json`,
`docs/help/HELP_INDEX.md`,
`assets/help/manifest.json`,
`docs/RELEASE_CHECKLIST.md`.
`tetris_nd/help_menu.py`,
`tetris_nd/control_helper.py`,
`config/menu/structure.json`.
2. New split modules/helpers introduced:
`tetris_nd/panel_utils.py`,
`tetris_nd/loop_runner_nd.py`,
`tetris_nd/front3d_setup.py`,
`tetris_nd/front4d_render.py`,
`tetris_nd/launcher_play.py`,
`tetris_nd/launcher_settings.py`.
3. Offline/stability analysis tooling added:
`tools/analyze_playbot_policies.py`.
`tools/check_playbot_stability.py`.
4. Runtime policy retuned:
`config/playbot/policy.json` (reduced default budgets + tightened benchmark thresholds).
5. New score-analyzer defaults and telemetry hooks added:
`config/gameplay/score_analyzer.json`,
`tetris_nd/score_analyzer.py`.
6. Gap-closure batch additions:
`tetris_nd/key_display.py`,
`tetris_nd/keybindings_menu_model.py`,
`tetris_nd/menu_control_guides.py`,
`tetris_nd/tests/test_menu_policy.py`,
`.github/workflows/stability-watch.yml`.
7. Toolchain/contract hardening additions:
`scripts/bootstrap_env.sh`,
`scripts/ci_check.sh`,
`tools/validate_project_contracts.py`,
`config/project/canonical_maintenance.json`,
`README.md`,
`docs/GUIDELINES_RESEARCH.md`,
`docs/RDS_AND_CODEX.md`,
`docs/rds/RDS_TETRIS_GENERAL.md`.

## 6. Source Inputs

1. `docs/rds/RDS_TETRIS_GENERAL.md`
2. `docs/rds/RDS_PLAYBOT.md`
3. `docs/rds/RDS_MENU_STRUCTURE.md`
4. `docs/RDS_AND_CODEX.md`
5. `config/project/canonical_maintenance.json`
6. Consolidated implementation diffs in current workspace batch.
