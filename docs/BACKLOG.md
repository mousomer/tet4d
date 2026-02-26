# Consolidated Backlog

Generated: 2026-02-18  
Updated: 2026-02-24  
Scope: unified view of implemented change set + unresolved RDS/documentation/code gaps.

## 1. Priority Verification Rules

1. `P1`= user-facing correctness, consistency, and discoverability gaps.
2. `P2`= maintainability and complexity risks that can cause regressions.
3. `P3`= optimization, tuning, and documentation hygiene.

## 2. Unified Change Set (Implemented Baseline)

1. `DONE` Governance audit follow-up (public-repo hardening):
2. `DONE` repo-native policy files are CI-wired (`scripts/check_git_sanitation.sh`,`scripts/check_policy_compliance.sh`,`config/project/policy_manifest.json`),
3. `DONE` workspace baseline policy marker files are adopted (with repo-native policy checks preserved in `*_repo.sh` extension scripts).
4. `DONE` Local/Codex verification wrapper now supports quiet success + fail-loud logs with `CODEX_MODE=1` reduced stability repeats while CI remains on `scripts/ci_check.sh`.
5. `DONE` Arch Stage 9 baseline introduced `src/tet4d/engine/core/` purity split scaffolding, strict `engine/core` purity gate (`scripts/check_engine_core_purity.sh`), and CI-wired architecture debt metrics (`scripts/arch_metrics.py`).
6. `DONE` Arch Stage 10 slice 1 tightened `engine/core` self-containment (no non-core engine imports) and routed shared lock/clear/score application through `src/tet4d/engine/core/rules/locking.py`.
7. `DONE` Arch Stage 11 slice 2 moved the real 2D reducer tick/gravity path into `src/tet4d/engine/core/step/reducer.py` and left `game2d.py` as a compatibility delegator.
8. `DONE` Arch Stage 12 slice 3 moved the ND reducer tick/gravity path into `src/tet4d/engine/core/step/reducer.py`; reducer wrapper debt metric (`core_step_state_method_calls`) is now expected to be `0`.
9. `DONE` Arch Stage 13 slice 4 moved 2D `Action` + reducer-facing state protocols into `src/tet4d/engine/core/model/`, and core 2D action dispatch no longer calls `game2d.py` private `_apply_action`.
10. `DONE` Arch Stage 14 slice 5 routed 2D piece-existence/collision checks through `src/tet4d/engine/core/rules/state_queries.py`, reducing reducer private-state helper debt (`core_step_private_state_method_calls`) to `0`.
11. `DONE` Arch Stage 15 slice 6 added a public 2D mapped-piece adapter on `GameState` and switched core rules to use it, reducing `core_rules_private_state_method_calls` to `0`.
12. `DONE` Arch Stage 16 slice 7 introduced core-owned 2D config/state view dataclasses (`src/tet4d/engine/core/model/game2d_views.py`) plus `game2d.py`/`engine.api` adapters, starting 2D state/config representation migration into core.
13. `DONE` Arch Stage 17 slice 8 moved the 2D gravity-tick mutation branch into `src/tet4d/engine/core/rules/gravity_2d.py`, reducing `core_step_state_field_assignments` in `scripts/arch_metrics.py` to `0`.
14. `DONE` Arch Stage 18 slice 9 introduced core-owned ND config/state view dataclasses (`src/tet4d/engine/core/model/game_nd_views.py`) plus `game_nd.py`/`engine.api` adapters, extending core-view extraction to shared 3D/4D state representations.
15. `DONE` Arch Stage 19 slice 10 routed `src/tet4d/ui/pygame/{front3d,front4d,profile_4d}.py` through `tet4d.engine.api` lazy wrappers, reducing `ui_to_engine_non_api` to `0`.
16. `DONE` Arch Stage 20 slice 11 converted `tet4d.ai.playbot` into an API-only package (with planner/controller/type submodules) and migrated external callers off `tet4d.engine.playbot.*` imports (`external_callers_to_engine_playbot = 0`).
17. `DONE` Arch Stage 21 slice 12 added `scripts/check_architecture_metric_budgets.sh` and wired it into local/CI verification to fail on architecture debt regressions (UI deep imports, core-purity debt, and current engine side-effect baselines).
18. `DONE` Arch Stage 23 slice 13 moved pygame display-mode implementation to `src/tet4d/ui/pygame/display.py` and converted `src/tet4d/engine/display.py` into a compatibility shim, reducing `pygame_imports_non_test`.
19. `DONE` Arch Stage 24 slice 14 moved pygame font profile initialization to `src/tet4d/ui/pygame/font_profiles.py` and converted `src/tet4d/engine/font_profiles.py` into a compatibility shim, reducing `pygame_imports_non_test` again.
20. `DONE` Arch Stage 25 slice 15 moved `src/tet4d/engine/playbot/lookahead_common.py` to `src/tet4d/ai/playbot/lookahead_common.py` with an engine compatibility shim, starting physical playbot-internal relocation while preserving the AI boundary (`ai_to_engine_non_api = 0`).
21. `DONE` Arch Stage 26 slice 16 moved pygame key-name display helpers to `src/tet4d/ui/pygame/key_display.py` and converted `src/tet4d/engine/key_display.py` into a compatibility shim, reducing `pygame_imports_non_test` again.
22. `DONE` Arch Stage 27 slice 17 moved translation/rotation control-guide rendering to `src/tet4d/ui/pygame/menu_control_guides.py` and converted `src/tet4d/engine/menu_control_guides.py` into a compatibility shim, continuing staged pygame-helper extraction.
23. `DONE` Arch Stage 28 slice 18 moved default keybinding maps/profile helpers to `src/tet4d/ui/pygame/keybindings_defaults.py` and converted `src/tet4d/engine/keybindings_defaults.py` into a lazy compatibility shim, reducing `pygame_imports_non_test` again.
24. `DONE` Arch Stage 29 slice 19 moved shared pygame event-loop processing to `src/tet4d/ui/pygame/game_loop_common.py` and converted `src/tet4d/engine/game_loop_common.py` into a compatibility shim, reducing `pygame_imports_non_test` again.
25. `DONE` Arch Stage 30 slice 20 moved menu-loop state/index helpers to `src/tet4d/ui/pygame/menu_model.py` and converted `src/tet4d/engine/menu_model.py` into a compatibility shim, reducing `pygame_imports_non_test` again.
26. `DONE` Arch Stage 31 slice 21 moved the generic menu event-loop runner to `src/tet4d/ui/pygame/menu_runner.py` and converted `src/tet4d/engine/menu_runner.py` into a lazy compatibility shim, reducing `pygame_imports_non_test` again.
27. `DONE` Arch Stage 32 slice 22 moved keybindings-menu pygame event polling to `src/tet4d/ui/pygame/keybindings_menu_input.py` and converted `src/tet4d/engine/keybindings_menu_input.py` into a compatibility shim, reducing `pygame_imports_non_test` again while preserving `ui_to_engine_non_api = 0`.
28. `DONE` Arch Stage 33 slice 23 removed redundant engine re-export facades (`src/tet4d/engine/{board,rng,types}.py`) and the stale `src/tet4d/engine/playbot/lookahead_common.py` shim after migrating callers, while explicitly retaining `engine -> ui` compatibility adapters as boundary-preserving layers.
29. `DONE` Arch Stage 34 slice 24 removed redundant `src/tet4d/ai/playbot/` wrapper modules (planner/controller/types facades), migrated internal callers to `tet4d.engine.api`, and retained only `src/tet4d/ai/playbot/lookahead_common.py` as real package logic.
30. `DONE` Arch Stage 35 slice 25 started the merged-folder engine split sequence (`gameplay` / `ui_logic` / `runtime`) and moved low-risk menu/input helpers into `src/tet4d/engine/ui_logic/` with engine-path compatibility shims to minimize import churn.
31. `DONE` Arch Stage 36 slice 26 moved `menu_controls.py` and `keybindings_menu_model.py` into `src/tet4d/engine/ui_logic/`, leaving engine-path compatibility shims and establishing the next `ui_logic` cluster slice without behavior change.
32. `DONE` Arch Stage 37 slice 27 moved `menu_graph_linter.py` into `src/tet4d/engine/ui_logic/` and left a legacy engine-path shim so governance tooling remains stable during the folder split.
33. `DONE` Arch Stage 38 slice 28 moved `keybindings_catalog.py` into `src/tet4d/engine/ui_logic/` and updated `ui_logic` keybindings-menu model imports to use the same merged folder.
34. `DONE` Arch Stage 39 slice 29 created `src/tet4d/engine/runtime/` and moved menu settings/config persistence modules (`menu_settings_state.py`, `menu_persistence.py`, `menu_config.py`) behind engine-path compatibility shims.
35. `DONE` Arch Stage 40 slice 30 moved project/runtime config and runtime validation modules into `src/tet4d/engine/runtime/`, adding engine-path module-alias shims to preserve import behavior during the folder split.
36. `DONE` Arch Stage 41 slice 31 moved `score_analyzer.py` and `score_analyzer_features.py` into `src/tet4d/engine/runtime/` with engine-path module-alias shims to preserve gameplay/HUD/tests behavior.
37. `DONE` Arch Stage 42 slice 32 created `src/tet4d/engine/gameplay/` and moved low-coupling gameplay helpers (`challenge_mode.py`, `speed_curve.py`, `exploration_mode.py`) behind engine-path module-alias shims.
38. `DONE` Arch Stage 43 slice 33 moved gameplay primitives (`pieces2d.py`, `pieces_nd.py`, `topology.py`) into `src/tet4d/engine/gameplay/`, keeping engine-path module-alias shims and local gameplay-cluster imports.
39. `DONE` Arch Stage 44 slice 34 updated `game2d.py` / `game_nd.py` imports to use `engine.gameplay.*` and `engine.runtime.score_analyzer` directly as a prep seam before moving the main game modules.
40. `DONE` Arch Stage 45 slice 35 pruned unused compatibility shims from Stages 36-41 (unused runtime validation/score-analyzer-feature shims plus stale `menu_action_contracts` shim) and migrated remaining runtime-helper callers to `engine.runtime.runtime_helpers`, preserving a net LOC decrease; folder-ratio checkpoint after prune: top-level `engine/*.py=66`, `engine/ui_logic/*.py=7`, `engine/runtime/*.py=14`, `engine/gameplay/*.py=7`.
41. `DONE` Arch Stage 46 slice 36 moved `assist_scoring.py` into `src/tet4d/engine/runtime/` to complete the runtime analytics cluster, preserving behavior with an engine-path module-alias shim.
42. `DONE` Arch Stage 47 slice 37 moved `topology_designer.py` into `src/tet4d/engine/gameplay/`, retargeting project-config dependency to `engine.runtime.project_config` and preserving callers with an engine-path module-alias shim.
43. `DONE` Arch Stage 48 slice 38 added temporary `engine.gameplay.game2d` / `engine.gameplay.game_nd` aliases and migrated selected internal callers (`gameplay/challenge_mode.py`, `runtime/runtime_helpers.py`) as prep for physical game-module moves.
44. `DONE` Arch Stage 49 slice 39 moved `game2d.py` into `src/tet4d/engine/gameplay/`, rebased imports to gameplay/runtime/core cluster paths, and preserved callers/tests with an engine-path module-alias shim.
45. `DONE` Arch Stage 50 slice 40 moved `game_nd.py` into `src/tet4d/engine/gameplay/`, rebased imports to gameplay/runtime/core cluster paths, and preserved 3D/4D callers/tests with an engine-path module-alias shim.
46. `DONE` Arch Stage 51 slice 41 migrated engine-internal callers to `engine.gameplay.game2d/game_nd` and kept `engine.game2d` / `engine.game_nd` shims as a compatibility checkpoint for tests/external imports pending a later prune stage.
47. `DONE` Arch Stage 52 slice 42 migrated engine test imports to `engine.gameplay.game2d/game_nd`, reducing legacy game-module shim callers to external compatibility only.
48. `DONE` Arch Stage 53 slice 43 audited repo callers and found zero remaining imports of `tet4d.engine.game2d` / `tet4d.engine.game_nd`, clearing the way for shim removal.
49. `DONE` Arch Stage 54 slice 44 removed `src/tet4d/engine/game2d.py` and `src/tet4d/engine/game_nd.py` compatibility shims after the zero-caller audit, making `engine.gameplay.game2d/game_nd` canonical in-repo paths.
50. `DONE` Arch Stage 55 slice 45 moved `help_topics.py` into `src/tet4d/engine/runtime/` with an engine-path module-alias shim, reducing top-level engine file-I/O surface.
51. `DONE` Arch Stage 56 slice 46 moved `text_render_cache.py` into `src/tet4d/ui/pygame/` and routed its config lookup through a new `engine.api.project_constant_int` wrapper to preserve UI boundary rules.
52. `DONE` Arch Stage 57 slice 47 moved `ui_utils.py` into `src/tet4d/ui/pygame/` with an engine-path module-alias shim, reusing the `engine.api.project_constant_int` seam for config-driven cache limits.
53. `DONE` Arch Stage 58 slice 48 moved `projection3d.py` into `src/tet4d/ui/pygame/` with an engine-path module-alias shim and API-based config constant access.
54. `DONE` Arch Stage 59 slice 49 moved `control_icons.py` into `src/tet4d/ui/pygame/` and routed project-root access through `engine.api.project_root_path()` to preserve UI boundary rules.
55. `DONE` Arch Stage 60 slice 50 moved `control_helper.py` into `src/tet4d/ui/pygame/` and routed key-formatting/runtime-binding dependencies through narrow `engine.api` wrappers.
56. `DONE` Arch Stage 61 slice 51 moved `panel_utils.py` into `src/tet4d/ui/pygame/` with an engine-path module-alias shim after moving its helper dependencies.
57. `DONE` Arch Stage 62 slice 52 moved `camera_mouse.py` into `src/tet4d/ui/pygame/`, localizing its `projection3d` dependency and preserving engine-path imports for callers/tests.
58. `DONE` Arch Stage 63 slice 53 moved `menu_layout.py` into `src/tet4d/engine/ui_logic/` with an engine-path compatibility shim as part of UI-logic cluster consolidation.
59. `DONE` Arch Stage 64 slice 54 moved `key_dispatch.py` into `src/tet4d/engine/ui_logic/` with an engine-path compatibility shim, continuing non-rendering input/menu clustering.
60. `DONE` Arch Stage 65 slice 55 migrated engine and CLI callers to canonical `src/tet4d/engine/ui_logic/*` imports for dispatch/menu helper modules ahead of shim pruning.
61. `DONE` Arch Stage 66 slice 56 migrated tools and tests to canonical `src/tet4d/engine/ui_logic/*` imports, clearing remaining callers to UI-logic compatibility shims.
62. `DONE` Arch Stage 67 slice 57 removed zero-caller engine-path compatibility shims for migrated `ui_logic` modules after canonical import migration across engine/CLI/tools/tests.
63. `DONE` Arch Stage 68 slice 58 migrated engine and CLI callers to canonical `src/tet4d/engine/runtime/*` imports for analytics/help modules before runtime shim pruning.
64. `DONE` Arch Stage 69 slice 59 migrated tests to canonical `src/tet4d/engine/runtime/*` imports for analytics/help modules, preserving test placement and clearing remaining shim callers.
65. `DONE` Arch Stage 70 slice 60 removed zero-caller engine-path compatibility shims for `assist_scoring`, `help_topics`, and `score_analyzer` after runtime canonicalization.
66. `DONE` Arch Stage 71 slice 61 migrated engine front-game callers to `tet4d.ui.pygame.camera_mouse` as the first step in pruning the `camera_mouse` compatibility shim.
67. `DONE` Arch Stage 72 slice 62 migrated `camera_mouse` tests to `tet4d.ui.pygame.camera_mouse`, preserving test placement before removing the engine-path shim.
68. `DONE` Arch Stage 73 slice 63 removed the zero-caller `src/tet4d/engine/camera_mouse.py` compatibility shim after canonical engine/test import migration.
69. `DONE` Arch Stage 74 slice 64 migrated engine callers to canonical `src/tet4d/ui/pygame/control_helper.py` and `control_icons.py` imports before test migration and shim pruning.
70. `DONE` Arch Stage 75 slice 65 migrated control-helper/icon tests to canonical `src/tet4d/ui/pygame/*` imports, preserving test placement before shim pruning.
71. `DONE` Arch Stage 76 slice 66 removed zero-caller `src/tet4d/engine/control_helper.py` and `control_icons.py` compatibility shims after canonical engine/test import migration.
72. `DONE` Arch Stage 77 slice 67 migrated engine render/view callers to canonical `src/tet4d/ui/pygame/projection3d.py` imports before test migration and shim pruning.
73. `DONE` Arch Stage 78 slice 68 migrated `projection3d` tests to canonical `src/tet4d/ui/pygame/projection3d.py`, preserving test placement before shim pruning.
74. `DONE` Arch Stage 79 slice 69 removed the zero-caller `src/tet4d/engine/projection3d.py` compatibility shim after canonical engine/test import migration.
75. `DONE` Arch Stage 80 slice 70 migrated engine callers to canonical `src/tet4d/ui/pygame/ui_utils.py` imports before CLI migration and shim pruning.
76. `DONE` Arch Stage 81 slice 71 migrated the remaining CLI caller (`cli/front.py`) to canonical `src/tet4d/ui/pygame/ui_utils.py` imports before shim pruning.
77. `DONE` Arch Stage 82 slice 72 removed the zero-caller `src/tet4d/engine/ui_utils.py` compatibility shim after canonical engine/CLI import migration.
78. `DONE` Arch Stage 83 slice 73 migrated engine callers to canonical `src/tet4d/engine/runtime/menu_config.py` imports before CLI migration and shim pruning.
79. `DONE` Arch Stage 84 slice 74 migrated remaining CLI callers to canonical `src/tet4d/engine/runtime/menu_config.py` imports before shim pruning.
80. `DONE` Arch Stage 85 slice 75 removed the zero-caller `src/tet4d/engine/menu_config.py` compatibility shim after canonical engine/CLI import migration.
81. `DONE` Arch Stage 86 slice 76 migrated engine callers to canonical `src/tet4d/engine/runtime/project_config.py` imports before CLI/test migration and shim pruning.
82. `DONE` Arch Stage 87 slice 77 migrated remaining CLI/test callers to canonical `src/tet4d/engine/runtime/project_config.py` imports before shim pruning.
83. `DONE` Arch Stage 88 slice 78 removed the zero-caller `src/tet4d/engine/project_config.py` compatibility shim after canonical engine/CLI/test import migration.
84. `DONE` Arch Stage 89 slice 79 migrated engine callers to canonical `src/tet4d/engine/runtime/menu_settings_state.py` imports before CLI/test migration and shim pruning.
85. `DONE` Arch Stage 90 slice 80 migrated remaining CLI/test callers to canonical `src/tet4d/engine/runtime/menu_settings_state.py` imports before shim pruning.
86. `DONE` Arch Stage 91 slice 81 removed the zero-caller `src/tet4d/engine/menu_settings_state.py` compatibility shim after canonical engine/CLI/test import migration.
87. `DONE` Arch Stage 92 slice 82 migrated engine/test callers to canonical `src/tet4d/engine/runtime/runtime_config.py` imports before shim pruning.
88. `DONE` Arch Stage 93 slice 83 removed the zero-caller `src/tet4d/engine/runtime_config.py` compatibility shim after canonical engine/test import migration.
89. `DONE` Arch Stage 94 slice 84 migrated engine/CLI callers to canonical `src/tet4d/engine/runtime/menu_persistence.py` imports before shim pruning.
90. `DONE` Arch Stage 95 slice 85 removed the zero-caller `src/tet4d/engine/menu_persistence.py` compatibility shim after canonical engine/CLI import migration.
91. `DONE` Root `front.py --help` now shows wrapper selector options and delegates to the selected CLI frontend help output, so launcher help exposes actual runtime options.
92. `DONE` `scripts/ci_check.sh` now delegates to `scripts/verify.sh` as the canonical CI/local pipeline to reduce drift between local and GitHub checks.
93. `DONE` `scripts/check_architecture_boundaries.sh` now baseline-locks current transitional `engine -> tet4d.ui` imports (fail on new imports only), fixing GitHub repo-policy gate failures caused by stale allowlists.
94. `DONE` baseline policy/drift scripts now treat workspace policy-template marker files as optional in fresh public clones, preventing GitHub CI failures on missing local-only `.policy` assets.
95. `DONE` Arch Stage 96 slice 86 migrated engine callers to canonical `src/tet4d/ui/pygame/font_profiles.py` imports before CLI migration and shim pruning.
96. `DONE` Arch Stage 97 slice 87 migrated CLI callers to canonical `src/tet4d/ui/pygame/font_profiles.py` imports before shim pruning.
97. `DONE` Arch Stage 98 slice 88 removed the zero-caller `src/tet4d/engine/font_profiles.py` compatibility shim after canonical engine/CLI import migration.
98. `DONE` Arch Stage 99 slice 89 migrated engine callers to canonical `src/tet4d/ui/pygame/game_loop_common.py` imports before CLI migration and shim pruning.
99. `DONE` Arch Stage 100 slice 90 migrated CLI callers to canonical `src/tet4d/ui/pygame/game_loop_common.py` imports before shim pruning.
100. `DONE` Arch Stage 101 slice 91 removed the zero-caller `src/tet4d/engine/game_loop_common.py` compatibility shim after canonical engine/CLI import migration.
101. `DONE` Arch Stage 102 slice 92 migrated engine/CLI callers to canonical `src/tet4d/ui/pygame/menu_runner.py` imports before shim pruning.
102. `DONE` Arch Stage 103 slice 93 removed the zero-caller `src/tet4d/engine/menu_runner.py` compatibility shim after canonical engine/CLI import migration.
103. `DONE` Arch Stage 104 slice 94 migrated engine callers to canonical `src/tet4d/ui/pygame/panel_utils.py` and `src/tet4d/ui/pygame/text_render_cache.py` imports before shim pruning.
104. `DONE` Arch Stage 105 slice 95 removed the zero-caller `src/tet4d/engine/panel_utils.py` and `src/tet4d/engine/text_render_cache.py` compatibility shims after canonical engine-caller migration.
105. `DONE` Arch Stage 106 slice 96 migrated engine callers to canonical `src/tet4d/ui/pygame/keybindings_defaults.py` imports before shim pruning.
106. `DONE` Arch Stage 107 slice 97 removed the zero-caller `src/tet4d/engine/keybindings_defaults.py` compatibility shim after canonical engine import migration.
107. `DONE` Arch Stage 108 slice 98 migrated engine callers to canonical `src/tet4d/ui/pygame/keybindings_menu_input.py` imports before shim pruning.
108. `DONE` Arch Stage 109 slice 99 removed the zero-caller `src/tet4d/engine/keybindings_menu_input.py` compatibility shim after canonical engine import migration.
109. `DONE` Arch Stage 110 slice 100 removed the zero-caller `src/tet4d/engine/menu_model.py` compatibility shim after canonical UI-path migration.
110. `DONE` Arch Stage 111 slice 101 removed the zero-caller `src/tet4d/engine/menu_control_guides.py` compatibility shim after canonical UI-path migration.
111. `DONE` Arch Stage 112 slice 102 moved `src/tet4d/engine/playbot/types.py` to `src/tet4d/ai/playbot/types.py` and retained an engine compatibility shim pending canonical caller migration.
112. `DONE` Arch Stage 113 slice 103 migrated engine playbot/API callers to canonical `src/tet4d/ai/playbot/types.py` imports and removed the zero-caller `src/tet4d/engine/playbot/types.py` compatibility shim.
113. `DONE` Arch Stage 114 slice 104 routed topology-designer preset JSON reads through `src/tet4d/engine/runtime/topology_designer_storage.py` (runtime-owned I/O seam).
114. `DONE` Arch Stage 115 slice 105 routed topology-designer export JSON writes through `src/tet4d/engine/runtime/topology_designer_storage.py` (runtime-owned I/O seam).
115. `DONE` Arch Stage 116 slice 106 migrated engine/CLI/test callers to canonical `src/tet4d/engine/gameplay/challenge_mode.py` imports before shim pruning.
116. `DONE` Arch Stage 117 slice 107 removed the zero-caller `src/tet4d/engine/challenge_mode.py` compatibility shim after canonical gameplay import migration.
117. `DONE` Arch Stage 118 slice 108 migrated engine/CLI callers to canonical `src/tet4d/engine/gameplay/exploration_mode.py` imports before shim pruning.
118. `DONE` Arch Stage 119 slice 109 removed the zero-caller `src/tet4d/engine/exploration_mode.py` compatibility shim after canonical gameplay import migration.
119. `DONE` Arch Stage 120 slice 110 migrated engine/test callers to canonical `src/tet4d/engine/gameplay/speed_curve.py` imports before shim pruning.
120. `DONE` Arch Stage 121 slice 111 removed the zero-caller `src/tet4d/engine/speed_curve.py` compatibility shim after canonical gameplay import migration.
121. `DONE` Arch Stage 122 slice 112 migrated engine/CLI/test callers to canonical `src/tet4d/engine/gameplay/topology_designer.py` imports before shim pruning.
122. `DONE` Arch Stage 123 slice 113 removed the zero-caller `src/tet4d/engine/topology_designer.py` compatibility shim after canonical gameplay import migration.
123. `DONE` Arch Stage 124 slice 114 migrated engine/CLI/test callers to canonical `src/tet4d/engine/gameplay/topology.py` imports before shim pruning.
124. `DONE` Arch Stage 125 slice 115 removed the zero-caller `src/tet4d/engine/topology.py` compatibility shim after canonical gameplay import migration.
125. `DONE` Arch Stage 126 slice 116 migrated engine/CLI/test callers to canonical `src/tet4d/engine/gameplay/pieces2d.py` imports before shim pruning.
126. `DONE` Arch Stage 127 slice 117 removed the zero-caller `src/tet4d/engine/pieces2d.py` compatibility shim after canonical gameplay import migration.
127. `DONE` Arch Stage 128 slice 118 migrated engine/test callers to canonical `src/tet4d/engine/gameplay/pieces_nd.py` imports before shim pruning.
128. `DONE` Arch Stage 129 slice 119 removed the zero-caller `src/tet4d/engine/pieces_nd.py` compatibility shim after canonical gameplay import migration.
129. `DONE` Arch Stage 130 slice 120 routed keybindings JSON reads through `src/tet4d/engine/runtime/keybindings_storage.py` before write-path extraction.
130. `DONE` Arch Stage 131 slice 121 routed keybindings atomic-write persistence through `src/tet4d/engine/runtime/keybindings_storage.py`.
131. `DONE` Arch Stage 132 slice 122 routed keybindings profile-clone file copy persistence through `src/tet4d/engine/runtime/keybindings_storage.py`.
132. `DONE` Arch Stage 133 slice 123 routed help-topics JSON reads through `src/tet4d/engine/runtime/help_topics_storage.py`.
133. `DONE` Arch Stage 134 slice 124 routed menu settings state JSON reads through `src/tet4d/engine/runtime/menu_settings_state_storage.py`.
134. `DONE` Arch Stage 135 slice 125 routed menu settings state atomic JSON writes through `src/tet4d/engine/runtime/menu_settings_state_storage.py`.
135. `DONE` Arch Stage 136 slice 126 routed menu-config JSON object reads through shared helper `src/tet4d/engine/runtime/json_storage.py`.
136. `DONE` Arch Stage 137 slice 127 routed project-config JSON object reads through shared helper `src/tet4d/engine/runtime/json_storage.py`.
137. `DONE` Arch Stage 138 slice 128 routed runtime-config validation JSON object reads through shared helper `src/tet4d/engine/runtime/json_storage.py`.
138. `DONE` Arch Stage 139 slice 129 routed topology-designer storage JSON object reads through shared helper `src/tet4d/engine/runtime/json_storage.py`.
139. `DONE` Arch Stage 140 slice 130 routed topology-designer storage JSON writes through shared helper `src/tet4d/engine/runtime/json_storage.py`.
140. `DONE` Arch Stage 141 slice 131 routed help-topics storage JSON reads through shared helper `src/tet4d/engine/runtime/json_storage.py`.
141. `DONE` Arch Stage 142 slice 132 routed menu-settings-state storage JSON reads and atomic writes through shared helper `src/tet4d/engine/runtime/json_storage.py`.
142. `DONE` Arch Stage 143 slice 133 routed keybindings storage JSON reads through shared helper `src/tet4d/engine/runtime/json_storage.py`.
143. `DONE` Arch Stage 144 slice 134 routed score-analyzer config/summary JSON reads through `src/tet4d/engine/runtime/score_analyzer_storage.py`.
144. `DONE` Arch Stage 145 slice 135 routed score-analyzer summary writes and event-log appends through `src/tet4d/engine/runtime/score_analyzer_storage.py`.
28. `DONE` Root entrypoint wrapping is consolidated into `front.py` only (no root `front2d.py`/`front3d.py`/`front4d.py` wrappers), and `front.py` accepts wrapper-level `--frontend/--mode {main,2d,3d,4d}` selection while delegating to `cli/front*.py`.

1. `DONE` Pause/main menu parity updates: launcher and pause both expose settings, bot options, keybindings, help, and quit.
2. `DONE`Keybindings menu now supports`General/2D/3D/4D` scopes and clear category separation (`gameplay/camera/system`).
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
15. `DONE` workspace baseline template scripts are now layered with tet4d repo extension policy checks (`scripts/check_*_repo.sh`) to preserve canonical maintenance contracts while staying policy-kit compatible.
16. `DONE` canonical-maintenance contract no longer pins workspace baseline template script text or exact workspace-policy metadata patch/path literals; baseline template identity is enforced by policy template drift hashes while contract content rules remain focused on repo-native scripts and CI entrypoints (with regex/presence checks for portable metadata).
15. `DONE` P2 frontend split executed:
16. `DONE`launcher flow extracted to`tetris_nd/launcher_play.py`.
17. `DONE`launcher settings/audio/display hub extracted to`tetris_nd/launcher_settings.py`.
18. `DONE`3D setup/menu/config extracted to`tetris_nd/front3d_setup.py`.
19. `DONE`4D render/view/clear animation layer extracted to`tetris_nd/front4d_render.py`.
20. `DONE` P3 tuning/tooling executed:
21. `DONE`playbot policy budgets/thresholds retuned in`config/playbot/policy.json`.
22. `DONE`offline policy comparison tool added:`tools/benchmarks/analyze_playbot_policies.py`.
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
43. `tools/governance/validate_project_contracts.py`+`scripts/ci_check.sh`
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
55. repeated dry-run stability tool added at `tools/stability/check_playbot_stability.py`,
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
67. `tools/governance/validate_project_contracts.py` now supports regex content rules,
68. stale fixed pass-count snapshots are blocked by `must_not_match_regex` rules in `config/project/canonical_maintenance.json`.
69. `DONE` Control-helper optimization batch completed:
70. action icons are now cached by `(action,width,height)` in `tetris_nd/control_icons.py` to avoid repeated per-frame redraw.
71. dimensional helper rows are assembled from shared row-spec builders in `tetris_nd/control_helper.py` to reduce duplication.
72. parity tests added for control UI helpers:
73. `tetris_nd/tests/test_control_ui_helpers.py`.
74. `DONE` Simplification batch completed:
75. shared UI helpers extracted to `tetris_nd/ui_utils.py` and consumed by launcher/help/keybindings/control views.
76. pause/settings menu row definitions externalized into `config/menu/structure.json` and loaded via `tetris_nd/menu_config.py`.
77. shared pause/settings list-panel renderer applied in `tetris_nd/pause_menu.py`.
78. keybindings menu split into dedicated input/view helpers:
79. `tetris_nd/keybindings_menu_input.py`, `tetris_nd/keybindings_menu_view.py`.
80. shared ND launcher orchestration extracted to `tetris_nd/launcher_nd_runner.py`.
81. shared 2D/ND lookahead selection helper extracted to `tetris_nd/playbot/lookahead_common.py`.
82. playbot policy validation monolith reduced by section validators in `tetris_nd/runtime_config_validation.py`.
83. `DONE` Post-split verification:
84. `ruff check .` passed,
85. `ruff check . --select C901` passed,
86. `pytest -q` passed.
87. `DONE` Follow-up simplification batch completed:
88. nested runtime help callbacks removed in `front2d.py` and `tetris_nd/loop_runner_nd.py`,
89. gameplay tuning validator decomposition completed in `tetris_nd/runtime_config_validation.py`,
90. shared 3D/4D projected grid-mode rendering extracted to `tetris_nd/grid_mode_render.py`,
91. keybinding split finalized with `tetris_nd/keybindings_defaults.py` and `tetris_nd/keybindings_catalog.py`,
92. score-analyzer feature extraction completed in `tetris_nd/score_analyzer_features.py`,
93. 2D side-panel extraction completed in `tetris_nd/gfx_panel_2d.py` and wired through `tetris_nd/gfx_game.py`.
94. `DONE` Validation after follow-up batch:
95. `ruff check .` passed,
96. `ruff check . --select C901` passed,
97. `pytest -q` passed,
98. `./scripts/ci_check.sh` passed.
99. `DONE` Next-stage decomposition + optimization batch completed:
100. runtime config validation split into dedicated section modules:
101. `tetris_nd/runtime_config_validation_shared.py`,
102. `tetris_nd/runtime_config_validation_gameplay.py`,
103. `tetris_nd/runtime_config_validation_playbot.py`,
104. `tetris_nd/runtime_config_validation_audio.py`,
105. with API compatibility maintained via `tetris_nd/runtime_config_validation.py`.
106. 3D frontend render/runtime split completed:
107. render/view path extracted to `tetris_nd/front3d_render.py`,
108. runtime loop/input orchestration retained in streamlined `tetris_nd/front3d_game.py`.
109. rendering optimization pass completed:
110. cached menu gradients in `tetris_nd/ui_utils.py`,
111. bounded text-surface cache in `tetris_nd/panel_utils.py`,
112. 2D panel text rendering now uses cached surfaces via `tetris_nd/gfx_panel_2d.py`.
113. `DONE` Validation after next-stage batch:
114. `ruff check .` passed,
115. `ruff check . --select C901` passed,
116. `pytest -q` passed,
117. `./scripts/ci_check.sh` passed.
118. `DONE` Further runtime optimization batch completed:
119. shared text-render cache extracted to `tetris_nd/text_render_cache.py`,
120. control-helper text rendering now uses cached surfaces (`tetris_nd/control_helper.py`),
121. panel/text cache now shared through `tetris_nd/panel_utils.py` and used by 2D panel rendering,
122. 4D layer rendering optimized to avoid per-layer full-board rescans:
123. locked cells are pre-indexed by `w` layer once per frame in `tetris_nd/front4d_render.py`,
124. layer-grid layout rectangles are memoized in `tetris_nd/front4d_render.py`.
125. `DONE` Validation after further optimization batch:
126. `ruff check .` passed,
127. `ruff check . --select C901` passed,
128. `pytest -q` passed,
129. `./scripts/ci_check.sh` passed.
130. `DONE` Repository secret scanning policy + scanner added and CI/local CI enforced:
131. `config/project/secret_scan.json`,
132. `tools/governance/scan_secrets.py`,
133. `scripts/ci_check.sh`.
134. `DONE` Path/constants externalization batch executed via:
135. `config/project/io_paths.json`,
136. `config/project/constants.json`,
137. `tetris_nd/project_config.py`,
138. and migrated consumers (`keybindings`, `menu_settings_state`, `runtime_config`, `score_analyzer`).
139. `DONE` Projection lattice caching + shared cached-gradient routing implemented in projection/render stack.
140. `DONE` Low-risk LOC-reduction batch executed:
141. pause-menu action dispatcher simplified and deduplicated in `tetris_nd/pause_menu.py`,
142. dead projected-grid draw helpers removed and shared cache-key helpers added in `tetris_nd/projection3d.py`,
143. shared projection cache-key builders wired into `tetris_nd/front3d_render.py` and `tetris_nd/front4d_render.py`,
144. score-analyzer validation/update flow consolidated in `tetris_nd/score_analyzer.py`.
145. `DONE` LOC snapshot after this batch:
146. Python LOC `22,934 -> 22,817` (`-117`),
147. non-test Python LOC `20,166 -> 20,049` (`-117`).
148. `DONE` Boundary topology preset baseline implemented/planned:
149. setup-level topology selector targets `bounded`,`wrap_all`,`invert_all` for 2D/3D/4D,
150. gravity-axis wrapping stays disabled by default,
151. deterministic replay/test coverage is required for topology-enabled runs.
152. `DONE` Small-profile rotation layout replanned to keyboard-pair ladder:
153. `2D`: `Q/W`,
154. `3D`: `Q/W`, `A/S`, `Z/X`,
155. `4D`: `Q/W`, `A/S`, `Z/X`, `R/T`, `F/G`, `V/B`.
156. `DONE` Default system-key conflicts were deconflicted for the new small 4D ladder by moving system defaults to:
157. restart=`Y`, toggle-grid=`C`.
158. `DONE` Advanced boundary-warping designer baseline implemented:
159. setup menus expose `topology_advanced` + hidden `topology_profile_index` controls,
160. per-axis/per-edge topology profile overrides are loaded from `config/topology/designer_presets.json`,
161. deterministic export path is available at `state/topology/selected_profile.json`.
162. `DONE` Config externalization follow-up implemented:
163. additional animation timings moved to `config/project/constants.json`,
164. runtime fallbacks are enforced via `tetris_nd/project_config.py`.
165. `DONE` Rotation-animation overlay rendering now uses topology-aware mapping across 2D/3D/4D frontends:
166. `tetris_nd/gfx_game.py`,
167. `tetris_nd/front3d_render.py`,
168. `tetris_nd/front4d_render.py`,
169. via shared overlay mapping in `tetris_nd/topology.py`.
170. `DONE` Invert-boundary seam traversal for seam-straddling ND pieces is stabilized by deterministic piece-level fallback mapping:
171. `tetris_nd/topology.py`,
172. with regressions in `tetris_nd/tests/test_topology.py` and `tetris_nd/tests/test_game_nd.py`.
173. `DONE` 4D view-plane camera turns (`xw`/`zw`) implemented as render-only animated controls:
174. `tetris_nd/front4d_render.py`,
175. with dedicated keybind actions (`view_xw_pos/neg`,`view_zw_pos/neg`) in:
176. `tetris_nd/keybindings_defaults.py`, `keybindings/4d.json`.
177. `DONE` 4D view-turn coverage added for routing separation, replay invariance, and render stability:
178. `tetris_nd/tests/test_nd_routing.py`,
179. `tetris_nd/tests/test_gameplay_replay.py`,
180. `tetris_nd/tests/test_front4d_render.py`.
181. `DONE` 4D renderer cache-key correctness hardening:
182. projection cache extras now include total `W` size to prevent stale lattice/helper cache reuse across differing 4D board depths.
183. `DONE` 4D hyper-view zoom-fit hardening:
184. per-layer zoom fit now accounts for `xw`/`zw` transforms and centered `w` offset; regression coverage added for outer-layer bounds.
185. `DONE` Full local gate revalidation executed through `scripts/ci_check.sh` after this batch.
186. `DONE` Black-box cross-config 4D frame-cache regression added and passing:
187. `tetris_nd/tests/test_front4d_render.py` now asserts distinct `4d-full` cache entries for differing total `W` sizes under full-frame draws.
188. `DONE` Projection-lattice cache observability helpers added for regression/profiling validation:
189. `tetris_nd/projection3d.py` (`clear_projection_lattice_cache`, `projection_lattice_cache_keys`, `projection_lattice_cache_size`).
190. `DONE` 4D render profiling tool added and exercised:
191. `tools/benchmarks/profile_4d_render.py` with latest report at `state/bench/4d_render_profile_latest.json`.
192. `DONE` Sparse hyper-view overhead threshold assertion passed (no immediate optimization needed).
193. `DONE` Unreferenced helper cleanup pass executed:
194. removed definition-only helpers in `tetris_nd/frontend_nd.py`, `tetris_nd/menu_keybinding_shortcuts.py`, `tetris_nd/menu_model.py`, `tetris_nd/project_config.py`, and `tetris_nd/score_analyzer.py`.
195. profiler/policy tool output paths remain constrained to project root (`tools/benchmarks/profile_4d_render.py`,`tools/benchmarks/bench_playbot.py`,`tools/benchmarks/analyze_playbot_policies.py`).
196. `DONE` Setup-menu dedup follow-up (`BKL-P2-007`) completed:
197. `tetris_nd/front3d_setup.py` was collapsed to a thin adapter over shared ND setup logic in `tetris_nd/frontend_nd.py`,
198. removing duplicated 3D setup render/value/config paths while preserving runtime behavior.
199. Added regression coverage:
200. `tetris_nd/tests/test_front3d_setup.py`.
201. `DONE (superseded)` 4D `xw`/`zw` board-slot permutation fix:
202. this improved panel ordering but did not satisfy basis-decomposition behavior (`xw` should swap board decomposition axes).
203. superseded by active `BKL-P1-001` for full basis-driven 4D board decomposition.
204. `DONE` `[BKL-P1-001]` 4D `xw`/`zw` basis-driven board decomposition fix:
205. renderer now derives layer axis/count and board dims from signed-axis view basis,
206. and routes grid/cells/helper/clear-animation through one shared 4D->(layer,cell3) map in `tetris_nd/front4d_render.py`.
207. Added regression coverage in `tetris_nd/tests/test_front4d_render.py` for:
208. `(5,4,3,2)` + `xw` => `5` boards of `(2,4,3)`,
209. `(5,4,3,2)` + `zw` => `3` boards of `(5,4,2)`,
210. and 4D coord-map bijection.
211. `DONE` `[BKL-P1-002]` 4D post-basis regression cleanup:
212. exploration-mode rotation tween rendering restored (fractional overlay coordinates preserved),
213. `move_w` intent now maps to current basis layer axis (`w`/`x`/`z` by view),
214. compact profile 4D `w` movement defaults changed from `,/.` to `N`/`/`,
215. `macbook` built-in profile added with no-function 4D view defaults (`1/2/3/4`) and help=`Tab`,
216. 4D layer-region clear hardening added for layer-count reductions.
217. validation coverage added in:
218. `tetris_nd/tests/test_front4d_render.py`,
219. `tetris_nd/tests/test_nd_routing.py`,
220. `tetris_nd/tests/test_keybindings.py`,
221. and full local gates passed.
222. `DONE` `[BKL-P1-003]` Keybinding consistency update:
223. 4D camera `view_xw/view_zw` defaults now use number pairs (`1/2`,`3/4`) across shipped profiles,
224. `macbook` 4D `move_w` defaults now use `,/.`,
225. `full` profile keeps `move_w` on keypad (`Numpad7/Numpad9`) and now uses the same 4D letter-pair rotation ladder as compact profile to avoid camera/view collisions,
226. 2D positive rotation keeps `Up` arrow as default alongside `Q`.
227. `DONE` `[BKL-P1-004]` Remove slicing across runtime/UI/docs:
228. ND routing no longer carries slice state or slice actions; 3D/4D input routing is now system -> gameplay -> view.
229. 3D/4D keybinding groups and helper panels are now `game/camera/system` only.
230. 4D HUD/panel no longer shows active-slice indicators or active-layer slice highlighting.
231. `DONE` `[BKL-P2-008]` No-slice keybinding UX regroup + cleanup:
232. keybinding editor/help now present gameplay as `Translation` + `Rotation` sections, with `System` and `Camera/View` separate.
233. side-panel helpers now hide exploration-only translation rows unless exploration mode is enabled.
234. legacy profile `slice` groups were removed from shipped profile JSON files (`keybindings/profiles/*/{3d,4d}.json`).
235. dead no-op compatibility code was removed from `tetris_nd/keybindings.py` (unused `_merge_bindings` and unreachable `len(groups)==1` load branch).
236. `DONE` `[BKL-P2-009]` Menu-structure redesign follow-up:
237. pause `Settings` now routes to the shared launcher settings hub (`Audio`,`Display`,`Analytics`,`Save`,`Reset`,`Back`) instead of a separate pause-only implementation.
238. obsolete `pause_settings_rows` config/runtime paths were removed from `config/menu/structure.json` and `tetris_nd/menu_config.py`.
239. pause settings summary text now matches shared scope: `Audio + Display + Analytics`.
240. `DONE` `[BKL-P2-010]` Launcher settings rows are now config-driven:
241. unified settings row layout moved to `config/menu/structure.json` (`settings_hub_layout_rows`).
242. `tetris_nd/menu_config.py` now validates and serves typed settings-hub layout rows.
243. `tetris_nd/launcher_settings.py` now renders/selects settings rows from config instead of hardcoded `_UNIFIED_SETTINGS_ROWS`.
244. `DONE` `[BKL-P2-011]` Camera controls moved to numeric mappings:
245. 3D camera defaults now use top-row digits (`1-0`) for yaw/pitch/zoom/projection/reset.
246. 4D camera defaults now use top-row digits for view/yaw/pitch/zoom and profile-specific advanced actions.
247. full-profile 4D exploration movement keys were remapped off conflicting keypad digits to keep numeric camera bindings conflict-free.
248. `DONE` `[BKL-P1-005]` macbook no-keypad camera fallback:
249. macbook advanced 4D camera defaults now avoid keypad dependency (`-`, `=`, `P`, `Backspace`).
250. updated runtime defaults, shipped macbook profile JSON, and keybinding tests for parity.
251. `DONE` `[BKL-P1-006]` menu rehaul v2 (core IA pass):
252. launcher top-level IA updated to `Play`,`Continue`,`Settings`,`Controls`,`Help`,`Bot`,`Quit`.
253. launcher `Play` now opens a mode picker (`2D`,`3D`,`4D`) and `Continue` launches the last-used mode setup directly.
254. pause menu was simplified to core actions (`Resume`,`Restart`,`Settings`,`Controls`,`Help`,`Bot`,`Back To Main Menu`,`Quit`).
255. controls entry now opens keybindings with `General` scope first in both launcher and pause.
256. `DONE` `[BKL-P2-012]` Validation/IO simplification follow-up:
257. keybinding save/load context resolution is now shared through `_resolve_keybindings_io_context` in `tetris_nd/keybindings.py`.
258. duplicated menu-config type guards were reduced through shared validators in `tetris_nd/menu_config.py`.
259. playbot test-only wrappers were removed from `tetris_nd/playbot/planner_nd.py`; tests now use `tetris_nd/playbot/planner_nd_core.py` directly.
260. obsolete compatibility shim `tetris_nd/menu_gif_guides.py` was removed; control-guide usage is unified on `tetris_nd/menu_control_guides.py`.
261. `DONE` `[BKL-P2-013]` Stage-2 dedup and boilerplate reduction:
262. shared string-list validation path added in `tetris_nd/menu_config.py` and wired into row/action/scope validators.
263. settings-category docs validation in `tetris_nd/menu_config.py` now reuses shared object/string validators.
264. keybinding profile-clone and dimension-loop handling in `tetris_nd/keybindings.py` now use shared helpers/constants.
265. repeated enum index/label boilerplate in `tetris_nd/playbot/types.py` now uses shared typed helpers.
266. keybinding legacy dual-path handling was removed by making `small` profile resolve directly to root `keybindings/{2d,3d,4d}.json` paths in `tetris_nd/keybindings.py`.
267. `DONE` `[BKL-P2-014]` Stage-3 dead-code and validator reduction:
268. removed unreferenced helpers from `tetris_nd/runtime_config.py` (`playbot_policy_payload`, `audio_sfx_payload`),
269. removed unreferenced `topology_mode_index` from `tetris_nd/topology.py`,
270. removed unreferenced `reset_topology_designer_cache` from `tetris_nd/topology_designer.py`,
271. further reduced validator duplication in `tetris_nd/menu_config.py` by reusing shared object/int/bool/string guards in launcher/menu/setup/split-rules paths.
272. `DONE` `[BKL-P2-015]` Stage-4 launcher/tooling simplification:
273. duplicated 2D/3D/4D launch flow in `tetris_nd/launcher_play.py` is now routed through one shared `_launch_mode_flow` pipeline with shared bot-kwargs and window-size helpers.
274. playbot benchmark wrapper indirection was removed from `tetris_nd/playbot/types.py`.
275. benchmark/policy tools now read thresholds/history paths directly from runtime config in:
276. `tools/benchmarks/bench_playbot.py`,
277. `tools/benchmarks/analyze_playbot_policies.py`.
278. `DONE` `[BKL-P2-016]` Stage-5 runtime-config dedup cleanup:
279. removed unused `STATE_DIR` constant/import path from `tetris_nd/runtime_config.py`,
280. shared bucket/key helpers now reduce repeated dimension-bucket lookup boilerplate in runtime-config accessors,
281. speed-curve and assist-factor lookups now reuse shared normalization helpers in `tetris_nd/runtime_config.py`.
282. `DONE` `[BKL-P2-017]` External transform icon-pack integration:
283. external SVG icon pack was normalized under `assets/help/icons/transform/svg`.
284. runtime action-to-icon mapping config was added in `config/help/icon_map.json`.
285. `tetris_nd/control_icons.py` now resolves icons from SVG assets first, with procedural fallback retained for missing actions (including drop actions).
286. help asset contracts/docs were updated (`assets/help/manifest.json`, `docs/help/HELP_INDEX.md`, `docs/PROJECT_STRUCTURE.md`, and canonical-maintenance rules).
287. `DONE` `[BKL-P2-018]` Desktop packaging baseline (embedded runtime):
288. added canonical packaging spec `packaging/pyinstaller/tet4d.spec`,
289. added OS build scripts `packaging/scripts/build_{macos,linux}.sh` and `packaging/scripts/build_windows.ps1`,
290. added packaging CI matrix workflow `.github/workflows/release-packaging.yml`,
291. added release packaging docs `docs/RELEASE_INSTALLERS.md` and packaging RDS `docs/rds/RDS_PACKAGING.md`,
292. synced `README.md`, `docs/RELEASE_CHECKLIST.md`, `docs/PROJECT_STRUCTURE.md`, and canonical-maintenance contract for packaging artifacts.
293. `DONE` `[BKL-P2-019]` Font profile unification with per-mode values:
294. added shared font model/factory module `tetris_nd/font_profiles.py`,
295. removed duplicated `GfxFonts` + `init_fonts()` implementations in:
296. `tetris_nd/gfx_game.py`,
297. `tetris_nd/frontend_nd.py`,
298. `tetris_nd/front3d_render.py`,
299. preserved profile-specific sizing (`2d` panel font `18`, `nd` panel font `17`) through wrapper-based profile routing.
300. `DONE` `[BKL-P2-020]` Repository hygiene cleanup + history purge:
301. removed tracked IDE/log/legacy-asset artifacts (`.idea`, `app.log`, legacy GIF guides, duplicate source icon pack),
302. expanded ignore policy to prevent reintroduction of local/non-source files,
303. synced help/structure docs and RDS cleanup policy wording,
304. executed full-history purge of removed artifacts across refs and followed with force-push + secret scan sweep.
305. `DONE` `[BKL-P2-021]` File-fetch lifecycle library RDS + design baseline:
306. added plan doc `docs/plans/PLAN_FILE_FETCH_LIBRARY_RDS_2026-02-20.md` with explicit existing-RDS comparison and scope.
307. added canonical design spec `docs/rds/RDS_FILE_FETCH_LIBRARY.md` covering file action taxonomy (`load`/residency/`save`/cleanup), optimization toolbox, and API contract.
308. documented runtime optimization strategy recommendation (`adaptive heuristics + optional contextual bandit`) and deferred full RL to future scale-driven milestones.
309. synced RDS discoverability in documentation indexes (`docs/RDS_AND_CODEX.md`, `docs/README.md`, `docs/PROJECT_STRUCTURE.md`).
310. `DONE` `[BKL-P2-022]` Menu graph modularization + runner migration:
311. launcher/pause trees now come from `config/menu/structure.json` (`menus`, `menu_entrypoints`) via `tetris_nd/menu_config.py`.
312. generic menu runtime added in `tetris_nd/menu_runner.py` (`MenuRunner`, `ActionRegistry`).
313. hardcoded launcher play picker removed from `front.py`; play menu is config-defined and now includes future routes (`tutorials`, `topology_lab`) under `Play`.
314. pause runtime migrated to menu graph runner while preserving pause decision semantics in `tetris_nd/pause_menu.py`.
315. menu graph lint contract added and CI/contract-wired:
316. `tetris_nd/menu_graph_linter.py`,
317. `tools/governance/lint_menu_graph.py`,
318. `tools/governance/validate_project_contracts.py`,
319. `scripts/ci_check.sh`.

## 3. Active Open Backlog / TODO (Unified RDS Gaps + Technical Debt)

1. `[P3][BKL-P3-001] Pre-push local CI gate`
2. `Cadence:` before every push/release.
3. `Trigger:` any code/docs/config change on active branch.
4. `Done criteria:` latest `scripts/ci_check.sh` run exits `0` with no unresolved failures.
5. `[P3][BKL-P3-002] Scheduled stability + policy workflow watch`
6. `Cadence:` at least weekly and after workflow/config changes.
7. `Trigger:` `.github/workflows/ci.yml`, `.github/workflows/stability-watch.yml`, `tools/stability/check_playbot_stability.py`, or `tools/benchmarks/analyze_playbot_policies.py` changes.
8. `Done criteria:` scheduled workflow runs are green and no unresolved stability/policy alerts remain.
9. `[P3][BKL-P3-003] Runtime-config validation module split watch`
10. `Cadence:` when adding new policy sections.
11. `Trigger:` growth in `tetris_nd/runtime_config_validation_playbot.py` beyond current maintainable scope.
12. `Done criteria:` split completed with unchanged behavior and passing lint/tests.
13. `[P3][BKL-P3-004] 3D renderer decomposition watch`
14. `Cadence:` when adding new rendering responsibilities.
15. `Trigger:` major feature growth in `tetris_nd/front3d_render.py`.
16. `Done criteria:` render responsibilities are split into focused modules with behavior parity and passing regression tests.
17. `[P3][BKL-P3-005] Projection/cache profiling watch`
18. `Cadence:` after projection/camera/cache changes and before release.
19. `Trigger:` edits to projection/cache/zoom paths (3D/4D render stack).
20. `Done criteria:` `tools/benchmarks/profile_4d_render.py` report recorded; deeper caching is only added when measured overhead justifies it.
21. `[P3][BKL-P3-006] Desktop release hardening watch`
22. `Cadence:` before each public release.
23. `Trigger:` edits in `packaging/`, `.github/workflows/release-packaging.yml`, or `docs/RELEASE_INSTALLERS.md`.
24. `Done criteria:` package matrix artifacts are green and signing/notarization follow-up status is explicitly tracked in release notes.
25. `[P3][BKL-P3-007] Repository hygiene watch (history + secret scan)`
26. `Cadence:` before each push/release and after any cleanup of sensitive/non-source files.
27. `Trigger:` accidental commit of local artifacts, suspected secret exposure, or path-sanitization policy changes.
28. `Done criteria:` targeted paths are removed from tracked tree and git history when needed, `python3 tools/governance/scan_secrets.py` passes, and cleanup is documented in changelog/backlog.
29. `[P1][BKL-P1-002] 3D/4D active-piece transparency control`
30. `Cadence:` when adjusting 3D/4D rendering UX or accessibility settings.
31. `Trigger:` user feedback on occlusion/readability in 3D/4D boards.
32. `Done criteria:` active-piece transparency is supported in 3D/4D renders and user-adjustable via settings/config UI with documented defaults.
33. `[P1][BKL-P1-003] Viewer-relative movement regression verification (3D/4D)`
34. `Cadence:` after changes to camera/view rotation, movement routing, or ND input mapping.
35. `Trigger:` edits in 3D/4D key routing, camera transforms, or movement remapping logic.
36. `Done criteria:` automated and/or manual verification confirms movement inputs remain viewer-relative after board/view rotations in 3D and 4D.
37. `[P2][BKL-P2-010] True-random piece mode with configurable seed`
38. `Cadence:` when expanding piece-generation options or setup-menu gameplay settings.
39. `Trigger:` random piece-generator feature work (2D/3D/4D) or seed-handling changes.
40. `Done criteria:` a true-random piece mode exists with explicit seed configuration exposed in setup/config UI, and fixed-seed runs remain deterministic.
41. `[P2][BKL-P2-011] Larger dedicated 4D piece sets`
42. `Cadence:` when extending 4D gameplay content and balancing.
43. `Trigger:` new 4D piece-bag design/implementation work in `src/tet4d/engine/pieces_nd.py` or 4D setup menus.
44. `Done criteria:` one or more larger 4D piece sets are implemented, selectable in 4D setup, and covered by spawn/fit/rotation regression tests.
## 4. Gap Mapping to RDS

1. `docs/rds/RDS_TETRIS_GENERAL.md`: CI/stability workflows and setup-menu dedup follow-up (`BKL-P2-007`) are closed.
2. `docs/rds/RDS_PLAYBOT.md`: periodic retuning is now operationalized through scheduled benchmark + policy-analysis workflow.
3. `docs/rds/RDS_MENU_STRUCTURE.md`: `BKL-P2-006` is closed; launcher/pause/help IA parity and compact hardening are complete.
4. `docs/rds/RDS_2D_TETRIS.md` / `docs/rds/RDS_3D_TETRIS.md` / `docs/rds/RDS_4D_TETRIS.md`: topology preset + advanced profile behavior must remain in sync with setup + engine logic.
5. `docs/rds/RDS_FILE_FETCH_LIBRARY.md`: initial lifecycle and adaptive-fetch design baseline is defined for future standalone implementation.
6. `docs/rds/RDS_MENU_STRUCTURE.md`: menu graph modularization (`BKL-P2-022`) is closed with runner + lint contract in place.

## 5. Change Footprint (Current Batch)

Current sub-batch (2026-02-23): repo governance alignment and CI hardening only (no gameplay logic changes).

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
`tools/stability/check_playbot_stability.py`,
`docs/rds/RDS_SCORE_ANALYZER.md`,
`docs/FEATURE_MAP.md`,
`README.md`,
`config/project/canonical_maintenance.json`,
`tools/governance/validate_project_contracts.py`,
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
`tetris_nd/launcher_settings.py`,
`tetris_nd/ui_utils.py`,
`tetris_nd/keybindings_menu_view.py`,
`tetris_nd/keybindings_menu_input.py`,
`tetris_nd/launcher_nd_runner.py`,
`tetris_nd/playbot/lookahead_common.py`.
3. Offline/stability analysis tooling added:
`tools/benchmarks/analyze_playbot_policies.py`.
`tools/stability/check_playbot_stability.py`.
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
`tools/governance/validate_project_contracts.py`,
`config/project/canonical_maintenance.json`,
`README.md`,
`docs/GUIDELINES_RESEARCH.md`,
`docs/RDS_AND_CODEX.md`,
`docs/rds/RDS_TETRIS_GENERAL.md`.
8. Control-helper optimization additions:
`tetris_nd/control_icons.py`,
`tetris_nd/control_helper.py`,
`tetris_nd/tests/test_control_ui_helpers.py`.
9. Follow-up simplification additions (current batch):
`tetris_nd/game_loop_common.py`,
`front2d.py`,
`tetris_nd/loop_runner_nd.py`,
`tetris_nd/runtime_config_validation.py`,
`tetris_nd/front3d_game.py`,
`tetris_nd/front4d_render.py`,
`tetris_nd/gfx_game.py`,
`tetris_nd/gfx_panel_2d.py`,
`tetris_nd/grid_mode_render.py`,
`tetris_nd/keybindings_defaults.py`,
`tetris_nd/keybindings_catalog.py`,
`tetris_nd/keybindings.py`,
`tetris_nd/score_analyzer_features.py`,
`tetris_nd/score_analyzer.py`.
10. Next-stage decomposition + optimization additions:
`tetris_nd/front3d_render.py`,
`tetris_nd/front3d_game.py`,
`tetris_nd/runtime_config_validation.py`,
`tetris_nd/runtime_config_validation_shared.py`,
`tetris_nd/runtime_config_validation_gameplay.py`,
`tetris_nd/runtime_config_validation_playbot.py`,
`tetris_nd/runtime_config_validation_audio.py`,
`tetris_nd/ui_utils.py`,
`tetris_nd/panel_utils.py`,
`tetris_nd/gfx_panel_2d.py`.
11. Further runtime optimization additions:
`tetris_nd/text_render_cache.py`,
`tetris_nd/control_helper.py`,
`tetris_nd/panel_utils.py`,
`tetris_nd/gfx_panel_2d.py`,
`tetris_nd/front4d_render.py`.
12. Security/config hardening + path/constants externalization additions:
`tetris_nd/project_config.py`,
`config/project/io_paths.json`,
`config/project/constants.json`,
`config/project/secret_scan.json`,
`tools/governance/scan_secrets.py`,
`scripts/ci_check.sh`,
`tetris_nd/runtime_config.py`,
`tetris_nd/menu_settings_state.py`,
`tetris_nd/keybindings.py`,
`tetris_nd/score_analyzer.py`,
`tetris_nd/projection3d.py`,
`tetris_nd/front3d_render.py`,
`tetris_nd/front4d_render.py`,
`README.md`,
`docs/SECURITY_AND_CONFIG_PLAN.md`.
13. Advanced topology-designer additions:
`config/topology/designer_presets.json`,
`tetris_nd/topology.py`,
`tetris_nd/topology_designer.py`,
`front2d.py`,
`tetris_nd/front3d_setup.py`,
`tetris_nd/frontend_nd.py`,
`tetris_nd/game2d.py`,
`tetris_nd/game_nd.py`,
`config/menu/defaults.json`,
`config/menu/structure.json`,
`config/schema/menu_settings.schema.json`,
`tetris_nd/tests/test_topology_designer.py`.
14. Latest simplification follow-up touched:
`tetris_nd/menu_config.py`,
`tetris_nd/keybindings.py`,
`tetris_nd/playbot/planner_2d.py`,
`tetris_nd/playbot/planner_nd.py`,
`tetris_nd/tests/test_playbot.py`,
`tetris_nd/menu_control_guides.py` (canonical guide module retained),
`tetris_nd/menu_gif_guides.py` (removed).
15. Stage-2 simplification follow-up touched:
`tetris_nd/menu_config.py`,
`tetris_nd/keybindings.py`,
`tetris_nd/playbot/types.py`.
16. Stage-3 simplification follow-up touched:
`tetris_nd/menu_config.py`,
`tetris_nd/runtime_config.py`,
`tetris_nd/topology.py`,
`tetris_nd/topology_designer.py`.
17. Stage-4 simplification follow-up touched:
`tetris_nd/launcher_play.py`,
`tetris_nd/playbot/types.py`,
`tools/benchmarks/bench_playbot.py`,
`tools/benchmarks/analyze_playbot_policies.py`.
18. Stage-5 simplification follow-up touched:
`tetris_nd/runtime_config.py`.
19. Current menu-graph modularization batch touched:
`config/menu/structure.json`,
`tetris_nd/menu_config.py`,
`tetris_nd/menu_runner.py`,
`tetris_nd/menu_graph_linter.py`,
`tools/governance/lint_menu_graph.py`,
`front.py`,
`tetris_nd/pause_menu.py`,
`tools/governance/validate_project_contracts.py`,
`scripts/ci_check.sh`,
`config/project/canonical_maintenance.json`,
`tetris_nd/tests/test_menu_policy.py`,
`tetris_nd/tests/test_menu_graph_linter.py`,
`docs/rds/RDS_MENU_STRUCTURE.md`,
`docs/CHANGELOG.md`,
`docs/plans/PLAN_MENU_GRAPH_MODULARIZATION_2026-02-21.md`.
19. Stage-6 icon-pack integration touched:
`assets/help/icons/transform/svg/*`,
`config/help/icon_map.json`,
`assets/help/manifest.json`,
`tetris_nd/control_icons.py`,
`config/project/canonical_maintenance.json`,
`docs/help/HELP_INDEX.md`,
`docs/PROJECT_STRUCTURE.md`.
20. Desktop packaging baseline touched:
`.github/workflows/release-packaging.yml`,
`packaging/pyinstaller/tet4d.spec`,
`packaging/scripts/build_macos.sh`,
`packaging/scripts/build_linux.sh`,
`packaging/scripts/build_windows.ps1`,
`docs/RELEASE_INSTALLERS.md`,
`docs/rds/RDS_PACKAGING.md`,
`README.md`,
`docs/RELEASE_CHECKLIST.md`,
`config/project/canonical_maintenance.json`.
21. Font profile unification touched:
`tetris_nd/font_profiles.py`,
`tetris_nd/gfx_game.py`,
`tetris_nd/frontend_nd.py`,
`tetris_nd/front3d_render.py`,
`front.py`,
`docs/rds/RDS_TETRIS_GENERAL.md`,
`docs/plans/PLAN_FONT_PROFILE_UNIFICATION_2026-02-20.md`.
22. File-fetch library RDS + planning touched:
`docs/plans/PLAN_FILE_FETCH_LIBRARY_RDS_2026-02-20.md`,
`docs/rds/RDS_FILE_FETCH_LIBRARY.md`,
`docs/RDS_AND_CODEX.md`,
`docs/README.md`,
`docs/PROJECT_STRUCTURE.md`.

145. `DONE` Arch Stage 146 slice 136 moved `src/tet4d/engine/rotation_anim.py` implementation into `src/tet4d/engine/gameplay/rotation_anim.py` and retained an engine compatibility shim pending caller migration.

146. `DONE` Arch Stage 147 slice 137 migrated engine and CLI callers to canonical `src/tet4d/engine/gameplay/rotation_anim.py` imports before shim pruning.

147. `DONE` Arch Stage 148 slice 138 migrated tests to canonical `src/tet4d/engine/gameplay/rotation_anim.py` imports before shim pruning.

148. `DONE` Arch Stage 149 slice 139 removed the zero-caller `src/tet4d/engine/rotation_anim.py` compatibility shim after canonical gameplay import migration.

149. `DONE` Arch Stage 150 slice 140 migrated engine callers to canonical `src/tet4d/ui/pygame/display.py` imports before shim pruning.

150. `DONE` Arch Stage 151 slice 141 migrated CLI and tests to canonical `src/tet4d/ui/pygame/display.py` imports before shim pruning.

151. `DONE` Arch Stage 152 slice 142 removed the zero-caller `src/tet4d/engine/display.py` compatibility shim after canonical UI display import migration.

152. `DONE` Arch Stage 153 slice 143 migrated engine callers to canonical `src/tet4d/ui/pygame/key_display.py` imports before shim pruning.

## 6. Source Inputs

1. `docs/rds/RDS_TETRIS_GENERAL.md`
2. `docs/rds/RDS_PLAYBOT.md`
3. `docs/rds/RDS_MENU_STRUCTURE.md`
4. `docs/RDS_AND_CODEX.md`
5. `config/project/canonical_maintenance.json`
6. Consolidated implementation diffs in current workspace batch.
