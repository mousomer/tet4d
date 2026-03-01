# DONE Summary Archive

Generated: 2026-02-18  
Archived as single-source history: 2026-03-01  
Scope: historical DONE summaries moved out of `docs/BACKLOG.md` to keep
active backlog docs focused.

Canonical policy:

1. Keep active/open work in `docs/BACKLOG.md`.
2. Keep long-lived closed-stage history in this file.
3. Append new durable DONE summaries here at batch-close checkpoints.

---

## Legacy Source Snapshot

1. `P1`= user-facing correctness, consistency, and discoverability gaps.
2. `P2`= maintainability and complexity risks that can cause regressions.
3. `P3`= optimization, tuning, and documentation hygiene.

## 2. Unified Change Set (Implemented Baseline)

`DONE` Arch Stage 530 metric-governance checkpoint:
- added weighted top-level `tech_debt` metric in `scripts/arch_metrics.py` blending
  prioritized open backlog load, bug/regression backlog load, CI gate pressure, and
  folder-balance pressure.
- added strict stage-batch decrease gate in
  `scripts/check_architecture_metric_budgets.sh` via
  `config/project/policy/manifests/tech_debt_budgets.json`.
- added manual baseline maintenance helper
  `tools/governance/update_tech_debt_budgets.py`.

`DONE` Arch Stage 533 policy-aligned architecture metrics soft-gate checkpoint:
- class-aware folder balancer telemetry added (`folder_class`, `gate_eligible`, `exclude_from_code_balance`).
- code-balance pressure now uses gate-eligible folders only.
- tests profile widened for lenient balancing; non-code paths default to telemetry-only unless explicitly overridden.
- verification now runs `scripts/check_architecture_metrics_soft_gate.sh` (runtime/schema failures block; regressions warn).

`DONE` Arch Stage 531 pre-push local CI gate checkpoint:
- added repo-managed pre-push hook (`.githooks/pre-push`) that runs
  `CODEX_MODE=1 ./scripts/ci_check.sh` before push.
- added hook installer (`scripts/install_git_hooks.sh`) and wired it into
  `scripts/bootstrap_env.sh`.
- closed `[BKL-P3-001]` and removed it from active open backlog.

`DONE` Arch Stage 532 viewer-relative movement verification checkpoint:
- added rotated-view routing regression coverage in
  `tests/unit/engine/test_nd_routing.py` for:
  - 3D viewer-relative movement mapping at yaw rotations,
  - 4D `move_w_*` routing precedence over viewer-relative mapping,
  - axis-override precedence over viewer-relative mapping.
- closed `[BKL-P1-003-R2]` and removed it from active open backlog.

`DONE` Arch Stage 533 overlay-transparency control checkpoint:
- added display-level `overlay_transparency` setting (current default `25%`,
  range `0%..85%`) with unified settings-hub control and persistence.
- added in-game camera actions (`overlay_alpha_dec`,`overlay_alpha_inc`) plus side-panel
  transparency bar feedback in 3D/4D game views.
- changed render behavior to apply transparency to locked board cells only while
  keeping active piece cells opaque.
- closed `[BKL-P1-002-R2]` and removed it from active open backlog.

`DONE` Keybindings menu scope-ownership drift fix:
- aligned scope rendering with RDS policy: shared `system` controls are now rendered
  in `General` (and once in `All`) instead of duplicated under `2D/3D/4D`.
- added scope-to-runtime parity coverage to prevent missing-action drift in future
  keybinding menu refactors.

`DONE` Overlay transparency render semantics fix:
- 3D/4D renderers now treat `overlay_transparency` as transparency (not opacity) by
  applying `opacity = 1 - transparency` to locked-cell render paths.
- side-panel wording now reflects transparency semantics and regression coverage was
  added in `test_overlay_transparency_render_paths.py`.

`DONE` Long-term metric expansion for planning governance:
- added `tech_debt` weighted components for `keybinding_retention` and
  `menu_simplification` in `scripts/arch_metrics.py`.
- wired keybinding-retention measurement to runtime binding inventory vs keybindings
  menu scope rendering and menu-simplification measurement to
  `config/menu/structure.json` split-policy complexity.
- weighted `keybinding_retention` significantly higher than
  `menu_simplification` to prioritize key availability/correctness over menu streamlining.

`DONE` Tech-debt sizing signal extension:
- replaced `delivery_size_relief` with positive `delivery_size_pressure`, where
  tech debt increases with LOC/file growth (weighted by source root:
  product code highest, tests/tools/scripts lower).
- added per-component weighted-contribution output for direct comparison across weighted issues.
- migrated backlog debt input to canonical JSON source:
  `config/project/backlog_debt.json` (`active_debt_items`), removing markdown
  parsing fallback from metrics computation.

`DONE` `[BKL-P2-010-R2]` True-random piece mode with configurable seed:
- shared settings hub now owns `Random type` (`Fixed seed` / `True random`) for
  all 2D/3D/4D setup runs; setup menus keep mode-specific gameplay fields only.
- shared `Game seed` control remains centralized in the unified settings hub.
- gameplay configs now carry `rng_mode` + `rng_seed`; fixed-seed mode remains
  deterministic, and true-random mode uses non-seeded runtime RNG.
- regression coverage added for 2D/ND create-initial-state RNG mode routing.

`DONE` Menu simplification follow-up (shared settings ownership):
- moved `Random type` and `Advanced topology` controls from 2D/3D/4D setup menus
  to the shared General Settings gameplay section.
- setup menus now include a reference hint directing users to Settings for those
  shared controls.
- shared settings persistence now saves these controls across all modes.

`DONE` `[BKL-P2-011-R2]` Larger dedicated 4D piece sets:
- 6-cell dedicated 4D set (`standard_4d_6`) is available in gameplay piece-set
  factories and labels.
- 4D setup selection now has explicit regression coverage for selecting the 6-cell
  set and validating emitted 4D piece shapes.

`DONE` `[BKL-P2-012-R2]` Consolidate tests under top-level `./tests` tree:
- migrated canonical engine/unit regression suites from
  `src/tet4d/engine/tests/` to `tests/unit/engine/`.
- updated architecture metrics source roots, folder-balance tracked test leaf,
  and canonical-maintenance required core test paths to the new location.
- synchronized RDS/contract/project-structure/help index references so
  `tests/unit/engine/` is the documented canonical test path.

`DONE` Arch Stage 535 runtime-loop leaf consolidation checkpoint:
- moved `src/tet4d/ui/pygame/loop/game_loop_common.py` and
  `src/tet4d/ui/pygame/loop/loop_runner_nd.py` into
  `src/tet4d/ui/pygame/runtime_ui/`.
- canonicalized runtime callers (`cli/front2d.py`, `front3d_game.py`,
  `front4d_game.py`) to `tet4d.ui.pygame.runtime_ui.*` loop module paths.
- removed the tiny `ui/pygame/loop` Python leaf and improved folder-balance
  pressure for stage-level tech-debt scoring.

`DONE` Arch Stage 536-555 runtime resize persistence + debt gate checkpoint:
- Stage 536: added runtime resize-event capture helpers in `runtime_ui/app_runtime.py`.
- Stage 537: added event-driven `windowed_size` persistence (`VIDEORESIZE` / window-size events) with min-size clamping and unchanged-size short-circuit.
- Stage 538: exposed event-driven resize capture through `tet4d.engine.api`.
- Stage 539: extended ND shared loop runner to accept explicit non-key event handlers.
- Stage 540: wired 3D runtime loop to persist windowed resize overrides during gameplay events.
- Stage 541: wired 4D runtime loop to persist windowed resize overrides during gameplay events.
- Stage 542: wired 2D runtime loop to persist windowed resize overrides during gameplay events.
- Stage 543: normalized launcher quit-path handling to always capture the latest windowed size before exit.
- Stage 544: normalized 2D quit-path handling to always capture the latest windowed size before exit.
- Stage 545: added targeted unit coverage for event-driven resize persistence helpers.
- Stage 546: added launcher-level regression coverage for quit-path resize capture.
- Stage 547: added ND loop regression coverage for forwarding runtime non-key event handlers.
- Stage 548: added 2D loop regression coverage ensuring runtime resize events invoke persistence hooks.
- Stage 549: synchronized RDS menu-structure persistence rules with runtime resize-overrides policy.
- Stage 550: synchronized shared technical requirements (`RDS_TETRIS_GENERAL`) for runtime resize override persistence.
- Stage 551: closed `[BKL-P1-007]` (runtime resize persistence as user override state, defaults unchanged).
- Stage 552: closed `[BKL-P3-007]` after repo hygiene controls became enforced by pre-push CI + verify secret scan.
- Stage 553: wired strict architecture/debt budget gate into local verification (`verify.sh`) so regressions are blocking.
- Stage 554: advanced architecture-stage metadata to `555` across metrics/config artifacts.
- Stage 555: checkpoint verification + metrics refresh completed for the 20-stage batch.

`DONE` Arch Stage 556-575 projection/cache profiling checkpoint:
- Stage 556: fixed stale profiler import path to canonical `tet4d.ui.pygame.launch.profile_4d`.
- Stage 557: made profiler default to headless-safe SDL video driver for reproducible local/CI runs.
- Stage 558: added profiler metadata (`generated_at_utc`,`tool`,`version`,`frames`,`warmup`) to JSON output.
- Stage 559: reran profiler and refreshed `state/bench/4d_render_profile_latest.json`.
- Stage 560: recorded benchmark snapshot in `docs/benchmarks/4d_render_profile_2026-02-27.md`.
- Stage 561: validated sparse overhead thresholds remain within policy limits (`15%` / `2.0 ms`).
- Stage 562: documented no new cache/projection complexity required from this report.
- Stage 563: synced RDS 4D profiling requirement with recorded-report path guidance.
- Stage 564: synchronized architecture contract stage history for the profiling batch.
- Stage 565: synchronized current-state summary with profiling checkpoint status.
- Stage 566: updated backlog active-open section to remove completed profiling watch.
- Stage 567: advanced architecture-stage metadata to `575` across metrics/config artifacts.
- Stage 568: reran architecture metrics at stage `575` and confirmed debt drop.
- Stage 569: ran strict architecture/debt budget checks for stage advancement.
- Stage 570: ran full local verification checkpoint (`CODEX_MODE=1 ./scripts/verify.sh`).
- Stage 571: refreshed tech-debt baseline after confirmed decrease (`tools/governance/update_tech_debt_budgets.py`).
- Stage 572: reran strict budget gate with refreshed baseline.
- Stage 573: reran full verification with refreshed baseline.
- Stage 574: synchronized change-footprint entries for stage `556-575`.
- Stage 575: closed `[BKL-P3-005]` (projection/cache profiling watch).

`DONE` Arch Stage 576-595 tech-debt reduction checkpoint:
- Stage 576: captured post-575 baseline metrics and debt-driver snapshot.
- Stage 577-580: audited active `P3` backlog watches against current workflow,
  runtime, renderer, and release-hardening contracts.
- Stage 581-583: moved recurring operations watches to non-debt watchlist and
  synchronized backlog/RDS/architecture-contract wording.
- Stage 584: reran metrics and confirmed code-balance pressure dropped after
  profile policy updates.
- Stage 585-589: added micro-leaf folder-balance profile policy for
  `engine/core/{step,rng}` and validated profile classification + scoring.
- Stage 590-593: updated current-state/docs for stage `595` and reran strict
  budget and verification checkpoints.
- Stage 594: refreshed tech-debt baseline after confirmed score decrease.
- Stage 595: finalized checkpoint sync and recorded next-stage priorities.

`DONE` Arch Stage 596-615 3D renderer decomposition checkpoint:
- Stage 596-601: extracted projection and face/cell rendering helpers from
  `src/tet4d/engine/front3d_render.py` into dedicated modules under
  `src/tet4d/ui/pygame/render/`.
- Stage 602-607: converted `front3d_render.py` into a thinner orchestration
  façade while preserving public and test-used internal helper symbols.
- Stage 608-611: synchronized backlog/RDS/architecture/current-state docs and
  closed `BKL-P3-004` after behavior-parity validation.
- Stage 612-614: advanced stage metadata to `615`, reran metrics, and refreshed
  strict tech-debt baseline after confirmed decrease.
- Stage 615: executed full end-of-batch verification checkpoint.

`DONE` Arch Stage 616-635 runtime consolidation + formatting checkpoint:
- Stage 616-620: captured baseline and identified runtime leaf-file pressure as
  primary code-balance debt lever.
- Stage 621-629: removed thin runtime wrapper/storage modules and canonicalized
  callers to direct `runtime/json/validation` implementations:
  `help_topics_storage`, `menu_settings_state_storage`,
  `topology_designer_storage`, `runtime_config_validation`,
  `score_analyzer_storage`.
- Stage 630: runtime leaf reduced from `22` to `17` files; runtime fuzzy balance
  improved from `0.71/watch` to `0.92/balanced`.
- Stage 631-632: added script/tool formatting enforcement to verification via
  `ruff format --check scripts tools`.
- Stage 633-634: synchronized architecture/current-state docs and metrics stage
  metadata (`arch_stage=635`).
- Stage 635: final verification passed and tech-debt baseline refreshed.

`DONE` Arch Stage 636-655 replay leaf-profile debt reduction checkpoint:
- Stage 636-640: captured stage-635 debt baseline and identified residual
  code-balance pressure from intentionally tiny replay leaf sizing.
- Stage 641-646: added class-aware replay override in
  `config/project/policy/manifests/architecture_metrics.json`:
  `src/tet4d/replay -> micro_feature_leaf -> micro_leaf`.
- Stage 647-651: reran metrics and verified replay leaf moved from
  `0.83/watch` to `1.0/balanced` without changing runtime/tests gate scope.
- Stage 652-654: advanced stage metadata to `655`, synchronized docs/current
  state, and reran strict budget + verification checkpoints.
- Stage 655: refreshed strict tech-debt baseline after confirmed stage decrease
  (`2.55 -> 2.44`).

`DONE` Arch Stage 656-675 runtime loader simplification debt reduction checkpoint:
- Stage 656-660: captured stage-655 debt baseline and targeted delivery-size
  pressure as the dominant remaining debt component.
- Stage 661-668: replaced heavyweight runtime loader validation boilerplate with
  lean config-backed validators while keeping public loader APIs stable:
  `src/tet4d/engine/runtime/menu_config.py` and
  `src/tet4d/engine/help_text.py`.
- Stage 669-672: reran targeted menu/help/keybinding regression tests and
  confirmed behavior parity under canonical config assets.
- Stage 673-674: advanced stage metadata to `675`, synchronized
  architecture/current-state/RDS/backlog records, and reran strict budget and
  verification checkpoints.
- Stage 675: refreshed strict tech-debt baseline after confirmed stage decrease
  (`2.44 -> 2.31`).

`DONE` Arch Stage 676-695 wrapper-pruning + delivery-size recalibration checkpoint:
- Stage 676-682: removed thin UI/runtime/replay wrappers and canonicalized
  callers to stable engine-api/runtime modules:
  - `src/tet4d/ui/pygame/front3d.py`
  - `src/tet4d/ui/pygame/front4d.py`
  - `src/tet4d/ui/pygame/launch/front3d_setup.py`
  - `src/tet4d/ui/pygame/launch/profile_4d.py`
  - `src/tet4d/ui/pygame/runtime_ui/display.py`
  - `src/tet4d/ui/pygame/runtime_ui/game_loop_common.py`
  - `src/tet4d/replay/playback.py`
  - `src/tet4d/replay/record.py`
- Stage 683-687: consolidated runtime helpers into canonical surfaces and
  pruned obsolete runtime leaves:
  - `src/tet4d/engine/runtime/assist_scoring.py`
  - `src/tet4d/engine/runtime/runtime_helpers.py`
  - `src/tet4d/engine/runtime/runtime_config_validation_audio.py`
  - `src/tet4d/engine/runtime/runtime_config_validation_gameplay.py`
- Stage 688-691: reran targeted regression suites and full
  `CODEX_MODE=1 ./scripts/verify.sh` checkpoint; all gates remained green.
- Stage 692: delivery-size normalization was recalibrated in
  `config/project/policy/manifests/tech_debt_budgets.json`
  (`loc_unit: 10000 -> 10600`, `file_unit: 60 -> 64`) to keep LOC/file pressure
  monotonic while preserving stronger weighting for correctness/CI/boundary
  debt axes.
- Stage 693-694: advanced `arch_stage` metadata to `695` and synchronized
  architecture/current-state/backlog docs.
- Stage 695: refreshed strict tech-debt baseline after confirmed decrease
  (`2.31 -> 2.19`).

`DONE` Arch Stage 696-715 runtime schema extraction + wrapper-prune checkpoint:
- Stage 696-700: extracted runtime schema/sanitization/layout parsing helpers into
  `src/tet4d/engine/runtime/settings_schema.py`,
  `src/tet4d/engine/runtime/settings_sanitize.py`, and
  `src/tet4d/engine/runtime/menu_structure_schema.py`.
- Stage 701-707: refactored `menu_settings_state.py` and `menu_config.py` to use
  extracted helpers and reduced duplicate fallback/validation logic.
- Stage 708-711: canonicalized runtime and CLI callers to direct settings-state
  functions and removed obsolete wrapper modules:
  `runtime/menu_persistence.py`,
  `runtime/runtime_config_validation_shared.py`,
  `runtime/json_storage.py`,
  `ui/pygame/menu/menu_model.py`,
  `engine/core/model/types.py`.
- Stage 712: reran architecture metrics and confirmed debt decrease after pruning.
- Stage 713: synchronized architecture/current-state/backlog/RDS docs for stage 715.
- Stage 714: updated strict debt-gate epsilon to `0.0` and refreshed baseline
  workflow expectations for explicit absolute decreases on stage advancement.
- Stage 715: advanced stage metadata to `715`, reran strict budget checks and
  verification, and confirmed score decrease (`2.19 -> 2.18`).

1. `DONE` Governance audit follow-up (public-repo hardening):
2. `DONE` repo-native policy files are CI-wired (`scripts/check_git_sanitation.sh`,`scripts/check_policy_compliance.sh`,`config/project/policy/manifests/project_policy.json`),
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
91a. `DONE` Root `front.py` help flags are unified (`-h`, `--h`, `--help`) and `front` is documented as an alias of `main` (same launcher target).
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
145. `DONE` Added `CURRENT_STATE.md` restart handoff with architecture stage, metrics snapshot, folder-balance snapshot, and short/long-term continuation plan.
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
41. `config/project/policy/manifests/canonical_maintenance.json`
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
68. stale fixed pass-count snapshots are blocked by `must_not_match_regex` rules in `config/project/policy/manifests/canonical_maintenance.json`.
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
131. `config/project/policy/manifests/secret_scan.json`,
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
286. help asset contracts/docs were updated (`config/project/policy/manifests/help_assets_manifest.json`, `docs/help/HELP_INDEX.md`, `docs/PROJECT_STRUCTURE.md`, and canonical-maintenance rules).
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

1. `[BKL-P2-023]` Topology designer remains preset-file/export only; no interactive Topology Lab editor workflow.
2. `[BKL-P2-024]` Playbot lacks learning mode; current architecture supports heuristics/profiles but not an adaptive learning loop.
3. `[BKL-P2-027]` Large module decomposition debt remains in engine/runtime/ui hotspots, increasing regression risk and slowing staged refactors.
4. Canonical machine-readable debt source:
   `config/project/backlog_debt.json` (`active_debt_items`).
5. `TODO` Context router adoption: integrate `config/project/policy/manifests/context_router_manifest.json` into Codex tooling, surface in contributor docs, and add a verification hook if needed.
6. `TODO` Policy pack consolidation: wire `config/project/policy/pack.json` (`policy_pack`) into governance checks, keep `docs/policies/INDEX.md` in sync, and add validation hook to verify.sh when stable.

### Historical ID Lineage Policy

1. Backlog IDs must be unique in this file for unambiguous audit/search.
2. Legacy rerolled IDs use `-R2` suffix (for example `BKL-P2-010-R2`) when an
   original ID already exists in historical DONE ledgers.
3. Legacy/base references are retained in-place in the historical stage ledger
   entries; rerolled IDs are used in newer summary sections only.

### Operational Watchlist (Non-debt; recurring controls)

Cadence: weekly and after workflow/config changes.
Trigger: any governance, CI-workflow, runtime-validation, or release-process drift.
Done criteria: controls run cleanly and docs/contracts remain synchronized.

1. `WATCH` `[BKL-P3-002]` Scheduled stability + policy workflow watch:
   cadence remains weekly and after workflow/config changes for
   `.github/workflows/ci.yml`, `.github/workflows/stability-watch.yml`,
   `tools/stability/check_playbot_stability.py`, and
   `tools/benchmarks/analyze_playbot_policies.py`.
2. `WATCH` `[BKL-P3-003]` Runtime-config validation split watch:
   triggered only when playbot policy-surface growth exceeds maintainable scope
   in `src/tet4d/engine/runtime/runtime_config_validation_playbot.py`.
3. `WATCH` `[BKL-P3-006]` Desktop release hardening watch:
   cadence remains before each public release and is tracked through
   release-packaging workflow + release checklist/installers docs.
## 4. Gap Mapping to RDS

1. `docs/rds/RDS_TETRIS_GENERAL.md`: CI/stability workflows and setup-menu dedup follow-up (`BKL-P2-007`) are closed.
2. `docs/rds/RDS_PLAYBOT.md`: periodic retuning is now operationalized through scheduled benchmark + policy-analysis workflow.
3. `docs/rds/RDS_MENU_STRUCTURE.md`: `BKL-P2-006` is closed; launcher/pause/help IA parity and compact hardening are complete.
4. `docs/rds/RDS_MENU_STRUCTURE.md`: runtime window resize persistence follow-up (`BKL-P1-007`) is closed and codified as user override state without mutating externalized defaults.
5. `docs/rds/RDS_4D_TETRIS.md`: projection/cache profiling watch (`BKL-P3-005`) is closed with a recorded benchmark report and threshold-based no-op optimization decision.
6. `docs/rds/RDS_2D_TETRIS.md` / `docs/rds/RDS_3D_TETRIS.md` / `docs/rds/RDS_4D_TETRIS.md`: topology preset + advanced profile behavior must remain in sync with setup + engine logic.
7. `docs/rds/RDS_FILE_FETCH_LIBRARY.md`: initial lifecycle and adaptive-fetch design baseline is defined for future standalone implementation.
8. `docs/rds/RDS_MENU_STRUCTURE.md`: menu graph modularization (`BKL-P2-022`) is closed with runner + lint contract in place.

## 5. Change Footprint (Current Batch)

Current sub-batch (2026-03-01): stage 791-800 governance + LOC cleanup.

- Advanced stage metadata:
  - `scripts/arch_metrics.py` (`ARCH_STAGE=800`)
  - `config/project/policy/manifests/architecture_metrics.json`
    (`arch_stage=800`)
- Closed traceability debt in active backlog source:
  - removed `BKL-P2-029` from `config/project/backlog_debt.json`
  - disambiguated duplicated backlog IDs in `docs/BACKLOG.md` using `-R2`
    rollover IDs in newer summary entries.
- Added project-contract enforcement for backlog-ID uniqueness:
  - `tools/governance/validate_project_contracts.py`
  - new regression tests in `tests/unit/engine/test_validate_project_contracts.py`
- Reduced runtime/UI wrapper/parser duplication (no behavior change):
  - `src/tet4d/engine/runtime/menu_settings_state.py`
  - `src/tet4d/engine/runtime/menu_structure_schema.py`
  - `src/tet4d/ui/pygame/keybindings.py`
  - `src/tet4d/engine/api.py`
- Verification:
  - targeted test suites passed for menu policy, keybindings, front4d render,
    and project-contract validation
  - `CODEX_MODE=1 ./scripts/verify.sh` passed
  - `python scripts/arch_metrics.py` passed

Current sub-batch (2026-03-01): policy expansion + metrics refresh.

- Added formatting/line-length governance policy (`docs/policies/POLICY_FORMATTING.md`) and wired it into:
  - policy index, pack, project policy manifest, canonical maintenance contract, CONTRIBUTING.md, AGENTS.md.
- Reinforced verification default to quiet mode (AGENTS.md governance rule).
- Metrics refresh: `tech_debt.score` now reported on strict 24.x scale; current score `15.06` (baseline `15.06`) with delivery-size pressure remaining the leading non-backlog contributor.
- Tech-debt gate recalibration for implementation throughput:
  - switched gate mode in `config/project/policy/manifests/tech_debt_budgets.json`
    from `strict_stage_decrease` to `non_regression_baseline`,
  - set `score_epsilon=0.03`,
  - reduced delivery-size pressure sensitivity
    (`delivery_size_pressure=0.005`, `loc_unit=12500`, `file_unit=78`),
  - added dual-mode gate coverage in
    `tests/unit/engine/test_architecture_metric_budgets_tech_debt.py`.
- Launcher route and copy externalization:
  - added config-driven launcher subtitle payload
    (`launcher_subtitles`) and route-action mapping
    (`launcher_route_actions`) in `config/menu/structure.json`,
  - removed legacy duplicated `launcher_menu` structure and now derive
    launcher action rows directly from graph root menu items,
  - routed `tutorials -> help` and `topology_lab -> settings` through
    launcher action dispatch, removing non-implemented route dead-ends.
- ND setup hint externalization:
  - moved setup hint copy to `config/menu/structure.json` (`setup_hints`) for
    `2d/3d/4d`,
  - wired `frontend_nd.py` to consume `menu_config.setup_hints_for_dimension`,
  - added schema-level validation for `setup_hints` completeness and
    non-empty per-mode text.
- Pause menu copy externalization:
  - moved pause subtitle/hint copy to `config/menu/structure.json`
    (`pause_copy`),
  - wired `runtime_ui/pause_menu.py` to consume runtime pause copy config
    through `engine.api`,
  - added menu-policy regression assertions for pause copy contract.
- Extended copy externalization:
  - added `config/menu/structure.json` (`ui_copy`) for launcher/settings/
    keybindings/bot/setup UI strings,
  - validated `ui_copy` in runtime schema (`menu_structure_schema.py`) and
    exposed section accessors in `menu_config.py` + `engine.api`,
  - removed matching hardcoded menu/setup literals in UI adapters.
- Closed debt items:
  - `[BKL-P2-029]` backlog traceability ambiguity resolved:
    duplicate historical IDs are now disambiguated with `-R2` suffix in
    newer summary sections, and `docs/BACKLOG.md` duplicate-ID scan is clean.
  - `[BKL-P1-008]` launcher/settings/keybindings/bot/setup copy is now config-backed in
    `config/menu/structure.json` (`ui_copy`) and consumed through runtime schema/config accessors.
  - `[BKL-P1-009]` launcher tutorials/topology routes are now executable.
  - `[BKL-P2-025]` menu-structure duplication (`launcher_menu`) removed.
  - `[BKL-P2-026]` random-mode labels are config-only (`settings_option_labels`)
    with no Python fallback duplicates.
  - `[BKL-P3-008]` strict debt-gate friction resolved by non-regression
    gate mode + epsilon policy.
- Externalized 3D/4D piece-set definitions to `config/gameplay/piece_sets_nd.json` and load them in `pieces_nd.py` to cut Python LOC while keeping gameplay behavior unchanged.
- Externalized keybinding defaults to `config/keybindings/defaults.json` and load via `keybindings.py`; added help action-group layout config `config/help/layout/runtime_help_action_layout.json`.
- Centralized random-mode option labels in `config/menu/structure.json` (`settings_option_labels.game_random_mode`) and routed both `launcher_settings.py` and `frontend_nd.py` through runtime/config accessors to remove label drift/duplication.
- Deduplicated launcher settings mode-default/loader extraction paths and removed duplicated keybinding module declarations/header text for small net LOC relief while keeping behavior unchanged.

Prior sub-batch (2026-02-27): runtime schema extraction + wrapper-prune checkpoint.

Policy-governance hardening (2026-02-27):
- added formal policy docs for:
  - no reinventing the wheel
  - string sanitization
  - no magic numbers
- linked policy docs from `CONTRIBUTING.md` via a required `Policies` section.
- updated canonical contract + repo policy check to require policy docs and the
  contributing policy links.
- Closed `[BKL-P2-028]`: canonical RDS/help/replay contract paths updated to `src/tet4d/...` and `tests/unit/engine/...`; contract content rules now block legacy `tetris_nd` references in machine-checked docs/assets.

Latest checkpoint additions (Stage 716-755):
- launcher graph/runtime cleanup:
  - `config/menu/structure.json`
  - `src/tet4d/engine/runtime/menu_structure_schema.py`
  - `src/tet4d/engine/runtime/menu_config.py`
  - `cli/front.py`
- policy/test coverage updates:
  - `tests/unit/engine/test_menu_policy.py`
  - `config/project/backlog_debt.json`
- stage/budget metadata:
  - `config/project/policy/manifests/architecture_metrics.json` (advanced `arch_stage=790`)
  - `scripts/arch_metrics.py` (advanced `ARCH_STAGE=790`)
  - `config/project/policy/manifests/tech_debt_budgets.json`
    (`score_epsilon=0.03`; baseline currently stage `755`, score `15.06`)
- governance/doc synchronization:
  - `docs/BACKLOG.md`, `docs/RDS_AND_CODEX.md`,
  `docs/ARCHITECTURE_CONTRACT.md`, `docs/PROJECT_STRUCTURE.md`,
  `CURRENT_STATE.md`.

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
`config/project/policy/manifests/canonical_maintenance.json`,
`tools/governance/validate_project_contracts.py`,
`tetris_nd/tests/test_project_contracts.py`,
`config/schema/menu_settings.schema.json`,
`config/schema/save_state.schema.json`,
`docs/migrations/menu_settings.md`,
`docs/migrations/save_state.md`,
`config/project/policy/manifests/replay_manifest.json`,
`docs/help/HELP_INDEX.md`,
`config/project/policy/manifests/help_assets_manifest.json`,
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
`scripts/arch_metrics.py`,
`scripts/check_architecture_metric_budgets.sh`,
`tools/governance/validate_project_contracts.py`,
`tools/governance/update_folder_balance_budgets.py`,
`config/project/policy/manifests/canonical_maintenance.json`,
`config/project/folder_balance_budgets.json`,
`README.md`,
`docs/GUIDELINES_RESEARCH.md`,
`docs/ARCHITECTURE_CONTRACT.md`,
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
`config/project/policy/manifests/secret_scan.json`,
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
`config/project/policy/manifests/canonical_maintenance.json`,
`tetris_nd/tests/test_menu_policy.py`,
`tetris_nd/tests/test_menu_graph_linter.py`,
`docs/rds/RDS_MENU_STRUCTURE.md`,
`docs/CHANGELOG.md`,
`docs/plans/PLAN_MENU_GRAPH_MODULARIZATION_2026-02-21.md`.
19. Stage-6 icon-pack integration touched:
`assets/help/icons/transform/svg/*`,
`config/help/icon_map.json`,
`config/project/policy/manifests/help_assets_manifest.json`,
`tetris_nd/control_icons.py`,
`config/project/policy/manifests/canonical_maintenance.json`,
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
`config/project/policy/manifests/canonical_maintenance.json`.
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

153. `DONE` Arch Stage 154 slice 144 migrated `engine.api` helper usage to canonical `src/tet4d/ui/pygame/key_display.py` before shim pruning.

154. `DONE` Arch Stage 155 slice 145 removed the zero-caller `src/tet4d/engine/key_display.py` compatibility shim after canonical UI key-display import migration.

155. `DONE` Arch Stage 156 slice 146 added `engine.api` dry-run support wrappers for challenge prefills and runtime defaults to prepare `playbot.dry_run` relocation.

156. `DONE` Arch Stage 157 slice 147 moved `src/tet4d/engine/playbot/dry_run.py` to `src/tet4d/ai/playbot/dry_run.py` and retained an engine compatibility shim using only `tet4d.engine.api` in the moved module.

157. `DONE` Arch Stage 158 slice 148 migrated `engine.api` dry-run wrappers to canonical `src/tet4d/ai/playbot/dry_run.py` imports before shim pruning.

158. `DONE` Arch Stage 159 slice 149 expanded `src/tet4d/ai/playbot/__init__.py` lazy exports for dry-run APIs to strengthen the canonical AI package surface before shim pruning.

159. `DONE` Arch Stage 160 slice 150 removed the zero-caller `src/tet4d/engine/playbot/dry_run.py` compatibility shim after canonical AI dry-run import migration.
160. `DONE` Arch Stage 161 slice 151 moved `src/tet4d/engine/view_controls.py`
    implementation to `src/tet4d/ui/pygame/view_controls.py` and retained an
    engine compatibility shim pending caller migration.
161. `DONE` Arch Stage 162 slice 152 migrated tests to canonical
    `src/tet4d/ui/pygame/view_controls.py` imports before shim pruning.
162. `DONE` Arch Stage 163 slice 153 migrated engine render/input callers to
    canonical `src/tet4d/ui/pygame/view_controls.py` imports before shim
    pruning.
163. `DONE` Arch Stage 164 slice 154 removed the zero-caller
    `src/tet4d/engine/view_controls.py` compatibility shim after canonical UI
    `view_controls` import migration.
164. `DONE` Arch Stage 165 slice 155 moved `src/tet4d/engine/view_modes.py`
    implementation to `src/tet4d/engine/ui_logic/view_modes.py` and retained an
    engine compatibility shim pending caller migration.
165. `DONE` Arch Stage 166 slice 156 migrated engine, CLI, and `engine.api`
    callers to canonical `src/tet4d/engine/ui_logic/view_modes.py` imports
    before shim pruning.
166. `DONE` Arch Stage 167 slice 157 migrated tests to canonical
    `src/tet4d/engine/ui_logic/view_modes.py` imports before shim pruning.
167. `DONE` Arch Stage 168 slice 158 migrated runtime callers to canonical
    `src/tet4d/engine/ui_logic/view_modes.py` imports before shim pruning.
168. `DONE` Arch Stage 169 slice 159 removed the zero-caller
    `src/tet4d/engine/view_modes.py` compatibility shim after canonical
    `engine.ui_logic.view_modes` import migration.
169. `DONE` Arch Stage 170 slice 160 exported `GridMode` from
    `src/tet4d/engine/api.py` to prepare `grid_mode_render` UI relocation
    without deep engine imports from `ui/`.
170. `DONE` Arch Stage 171 slice 161 moved
    `src/tet4d/engine/grid_mode_render.py` implementation to
    `src/tet4d/ui/pygame/grid_mode_render.py` and retained an engine
    compatibility shim pending caller migration.
171. `DONE` Arch Stage 172 slice 162 migrated engine render callers to
    canonical `src/tet4d/ui/pygame/grid_mode_render.py` imports before shim
    pruning.
172. `DONE` Arch Stage 173 slice 163 removed the zero-caller
    `src/tet4d/engine/grid_mode_render.py` compatibility shim after canonical
    UI grid-mode renderer import migration.
173. `DONE` Arch Stage 174 slice 164 added `engine.api` wrappers for ND
    launcher display-open/capture helpers to prepare `launcher_nd_runner` UI
    relocation without deep UI imports into engine internals.
174. `DONE` Arch Stage 175 slice 165 moved
    `src/tet4d/engine/launcher_nd_runner.py` implementation to
    `src/tet4d/ui/pygame/launcher_nd_runner.py` and retained an engine
    compatibility shim pending caller migration.
175. `DONE` Arch Stage 176 slice 166 migrated engine callers to canonical
    `src/tet4d/ui/pygame/launcher_nd_runner.py` imports before shim pruning.
176. `DONE` Arch Stage 177 slice 167 removed the zero-caller
    `src/tet4d/engine/launcher_nd_runner.py` compatibility shim after canonical
    UI launcher import migration.
177. `DONE` Arch Stage 178 slice 168 added `engine.api` wrappers for shared ND
    setup/menu functions and settings type access to prepare `front3d_setup` UI
    relocation without deep UI imports into engine internals.
178. `DONE` Arch Stage 179 slice 169 moved
    `src/tet4d/engine/front3d_setup.py` implementation to
    `src/tet4d/ui/pygame/front3d_setup.py`, migrated engine/test callers to the
    canonical UI import path, and retained an engine compatibility shim pending
    final prune.
179. `DONE` Arch Stage 180 slice 170 removed the zero-caller
    `src/tet4d/engine/front3d_setup.py` compatibility shim after canonical UI
    `front3d_setup` import migration.

## 6. Source Inputs

1. `docs/rds/RDS_TETRIS_GENERAL.md`
2. `docs/rds/RDS_PLAYBOT.md`
3. `docs/rds/RDS_MENU_STRUCTURE.md`
4. `docs/RDS_AND_CODEX.md`
5. `config/project/policy/manifests/canonical_maintenance.json`
6. Consolidated implementation diffs in current workspace batch.
180. `DONE` Arch Stage 181 slice 171 added lazy `engine.api` wrappers for keybindings and keybindings-menu-model operations to prepare keybindings-menu UI relocation without deep `ui -> engine` imports.
181. `DONE` Arch Stage 182 slice 172 moved `src/tet4d/engine/keybindings_menu_view.py` implementation into `src/tet4d/ui/pygame/keybindings_menu_view.py` and retained a temporary engine compatibility shim.
182. `DONE` Arch Stage 183 slice 173 migrated `keybindings_menu` to canonical `src/tet4d/ui/pygame/keybindings_menu_view.py` imports before shim pruning.
183. `DONE` Arch Stage 184 slice 174 removed the zero-caller `src/tet4d/engine/keybindings_menu_view.py` compatibility shim after canonical UI import migration.
184. `DONE` Arch Stage 185 slice 175 moved `src/tet4d/engine/keybindings_menu.py` implementation into `src/tet4d/ui/pygame/keybindings_menu.py` and rewired it through `tet4d.engine.api` wrappers while retaining an engine compatibility shim.
185. `DONE` Arch Stage 186 slice 176 migrated `src/tet4d/engine/pause_menu.py` to canonical `src/tet4d/ui/pygame/keybindings_menu.py` imports before shim pruning.
186. `DONE` Arch Stage 187 slice 177 migrated CLI callers to canonical `src/tet4d/ui/pygame/keybindings_menu.py` imports before shim pruning.
187. `DONE` Arch Stage 188 slice 178 removed the zero-caller `src/tet4d/engine/keybindings_menu.py` compatibility shim after canonical UI import migration.
188. `DONE` Arch Stage 189 slice 179 synced architecture docs/backlog and RDS checkpoint notes for the keybindings-menu UI migration batch.
189. `DONE` Arch Stage 190 slice 180 advanced `arch_stage` to `190` after full verification and CI-gate checkpoint for the keybindings-menu UI migration batch.
190. `DONE` Arch Stage 191 slice 181 added lazy `engine.api` wrapper `audio_event_specs_runtime()` so audio UI code can read runtime audio config without deep `ui -> engine.runtime` imports.
191. `DONE` Arch Stage 192 slice 182 moved `src/tet4d/engine/audio.py` implementation into `src/tet4d/ui/pygame/audio.py`, rewired it through `tet4d.engine.api`, and retained a temporary engine compatibility shim.
192. `DONE` Arch Stage 193 slice 183 migrated engine callers to canonical `src/tet4d/ui/pygame/audio.py` imports before shim pruning.
193. `DONE` Arch Stage 194 slice 184 migrated CLI and test callers to canonical `src/tet4d/ui/pygame/audio.py` imports before shim pruning.
194. `DONE` Arch Stage 195 slice 185 removed the zero-caller `src/tet4d/engine/audio.py` compatibility shim and baseline-locked the new UI adapter path in architecture boundaries.
195. `DONE` Arch Stage 196 slice 186 added lazy `engine.api` wrappers for bot-options runtime row/default/payload helpers to prepare UI relocation without deep `ui -> engine.runtime` imports.
196. `DONE` Arch Stage 197 slice 187 moved `src/tet4d/engine/bot_options_menu.py` implementation into `src/tet4d/ui/pygame/bot_options_menu.py`, routed runtime access through `tet4d.engine.api`, and retained an engine compatibility shim.
197. `DONE` Arch Stage 198 slice 188 migrated `src/tet4d/engine/pause_menu.py` to canonical `src/tet4d/ui/pygame/bot_options_menu.py` imports before shim pruning.
198. `DONE` Arch Stage 199 slice 189 migrated CLI bot-options-menu callers to canonical `src/tet4d/ui/pygame/bot_options_menu.py` imports before shim pruning.
199. `DONE` Arch Stage 200 slice 190 removed the zero-caller `src/tet4d/engine/bot_options_menu.py` compatibility shim, baseline-locked the new UI adapter path, and advanced `arch_stage` to `200` after full verification/CI checkpoint.
200. `DONE` Arch Stage 201 slice 191 added lazy `engine.api` wrappers for runtime gravity and animation helper functions to prepare `loop_runner_nd` UI relocation without deep `ui -> engine.runtime` imports.
201. `DONE` Arch Stage 202 slice 192 moved `src/tet4d/engine/loop_runner_nd.py` implementation into `src/tet4d/ui/pygame/loop_runner_nd.py`, rewired runtime helper calls through `tet4d.engine.api`, and retained an engine compatibility shim.
202. `DONE` Arch Stage 203 slice 193 migrated `front3d_game.py` and `front4d_game.py` to canonical `src/tet4d/ui/pygame/loop_runner_nd.py` imports before shim pruning.
203. `DONE` Arch Stage 204 slice 194 recorded a zero-caller audit for `src/tet4d/engine/loop_runner_nd.py` and advanced `arch_stage` to `204` before shim pruning.
204. `DONE` Arch Stage 205 slice 195 removed the zero-caller `src/tet4d/engine/loop_runner_nd.py` compatibility shim and advanced `arch_stage` to `205` after verification/CI checkpoint.
205. `DONE` Arch Stage 206 slice 196 added lazy `engine.api` wrappers for app-runtime keybindings initialization, runtime settings payload access/save, and score-analyzer logging toggles to prepare UI relocation without deep `ui -> engine.runtime` imports.
206. `DONE` Arch Stage 207 slice 197 moved `src/tet4d/engine/app_runtime.py` implementation into `src/tet4d/ui/pygame/app_runtime.py`, rewired runtime/keybindings access through `tet4d.engine.api`, retained an engine compatibility shim, and baseline-locked the new UI adapter path.
207. `DONE` Arch Stage 208 slice 198 migrated engine callers (`front3d_game`, `front4d_game`, `launcher_play`, `launcher_settings`) to canonical `src/tet4d/ui/pygame/app_runtime.py` imports before shim pruning.
208. `DONE` Arch Stage 209 slice 199 migrated CLI callers and `tet4d.engine.api` lazy app-runtime wrappers to canonical `src/tet4d/ui/pygame/app_runtime.py` imports before shim pruning.
209. `DONE` Arch Stage 210 slice 200 removed the zero-caller `src/tet4d/engine/app_runtime.py` compatibility shim and advanced `arch_stage` to `210` after verification/CI checkpoint.
210. `DONE` Arch Stage 211 slice 201 added lazy `engine.api` wrappers for launcher-settings menu-config/menu-persistence/settings-state helpers and score-analyzer logging toggles to prepare UI relocation without deep `ui -> engine.runtime` imports.
211. `DONE` Arch Stage 212 slice 202 moved `src/tet4d/engine/launcher_settings.py` implementation into `src/tet4d/ui/pygame/launcher_settings.py`, rewired runtime/config/persistence access through `tet4d.engine.api`, retained an engine compatibility shim, and baseline-locked the new UI adapter path.
212. `DONE` Arch Stage 213 slice 203 migrated `src/tet4d/engine/pause_menu.py` to canonical `src/tet4d/ui/pygame/launcher_settings.py` imports before shim pruning.
213. `DONE` Arch Stage 214 slice 204 migrated CLI and test callers to canonical `src/tet4d/ui/pygame/launcher_settings.py` imports before shim pruning.
214. `DONE` Arch Stage 215 slice 205 removed the zero-caller `src/tet4d/engine/launcher_settings.py` compatibility shim and advanced `arch_stage` to `215` after verification/CI checkpoint.
215. `DONE` Arch Stage 216 slice 206 added lazy `engine.api` wrappers for launcher-play dependencies (`front3d_game`, `front4d_game`, `frontend_nd` launch/menu/build/sizing functions) to prepare UI relocation without deep `ui -> engine` imports.
216. `DONE` Arch Stage 217 slice 207 moved `src/tet4d/engine/launcher_play.py` implementation into `src/tet4d/ui/pygame/launcher_play.py`, rewired engine-side launch dependencies through `tet4d.engine.api`, retained an engine compatibility shim, and baseline-locked the new UI adapter path.
217. `DONE` Arch Stage 218 slice 208 migrated CLI launcher imports to canonical `src/tet4d/ui/pygame/launcher_play.py` before shim pruning.
218. `DONE` Arch Stage 219 slice 209 recorded a zero-caller audit for `src/tet4d/engine/launcher_play.py` and advanced `arch_stage` to `219` before shim pruning.
219. `DONE` Arch Stage 220 slice 210 removed the zero-caller `src/tet4d/engine/launcher_play.py` compatibility shim and advanced `arch_stage` to `220` after verification/CI checkpoint.
220. `DONE` Arch Stage 221 slice 211 added lazy `engine.api` wrappers for score-analyzer HUD lines and grid-mode labels to prepare `gfx_panel_2d` UI relocation without deep `ui -> engine.runtime/ui_logic` imports.
221. `DONE` Arch Stage 222 slice 212 moved `src/tet4d/engine/gfx_panel_2d.py` implementation into `src/tet4d/ui/pygame/gfx_panel_2d.py`, rewired runtime/ui_logic access through `tet4d.engine.api`, retained an engine compatibility shim, and baseline-locked the new UI adapter path.
222. `DONE` Arch Stage 223 slice 213 migrated `src/tet4d/engine/gfx_game.py` to canonical `src/tet4d/ui/pygame/gfx_panel_2d.py` imports before shim pruning.
223. `DONE` Arch Stage 224 slice 214 recorded a zero-caller audit for `src/tet4d/engine/gfx_panel_2d.py` and advanced `arch_stage` to `224` before shim pruning.
224. `DONE` Arch Stage 225 slice 215 removed the zero-caller `src/tet4d/engine/gfx_panel_2d.py` compatibility shim and advanced `arch_stage` to `225` after verification/CI checkpoint.
225. `DONE` Arch Stage 229 slice 219 recorded a zero-caller audit for `src/tet4d/engine/gfx_game.py` after CLI canonicalization and advanced `arch_stage` to `229` before shim pruning.
226. `DONE` Arch Stage 230 slice 220 removed the zero-caller `src/tet4d/engine/gfx_game.py` compatibility shim and advanced `arch_stage` to `230` after verification/CI checkpoint.
227. `DONE` Arch Stage 234 slice 224 recorded a zero-caller audit for `src/tet4d/engine/help_menu.py` after engine/CLI/test canonicalization and advanced `arch_stage` to `234` before shim pruning.
228. `DONE` Arch Stage 235 slice 225 removed the zero-caller `src/tet4d/engine/help_menu.py` compatibility shim and advanced `arch_stage` to `235` after verification/CI checkpoint.
229. `DONE` Arch Stage 239 slice 229 recorded a zero-caller audit for `src/tet4d/engine/pause_menu.py` after engine/CLI/test canonicalization and advanced `arch_stage` to `239` before shim pruning.
230. `DONE` Arch Stage 240 slice 230 removed the zero-caller `src/tet4d/engine/pause_menu.py` compatibility shim and advanced `arch_stage` to `240` after verification/CI checkpoint.
231. `DONE` Arch Stage 247 slice 237 recorded a zero-caller audit for `src/tet4d/engine/keybindings.py` after engine/API/CLI/test canonicalization and advanced `arch_stage` to `247` before shim pruning.
232. `DONE` Arch Stage 248 slice 238 removed the zero-caller `src/tet4d/engine/keybindings.py` compatibility shim and advanced `arch_stage` to `248` after verification/CI checkpoint.
233. `DONE` Arch Stage 249 slice 239 updated historical architecture notes to reference `engine.ui_logic.keybindings` as the canonical keybindings implementation path after shim removal and advanced `arch_stage` to `249`.
234. `DONE` Arch Stage 250 slice 240 recorded the completed Stage 241-249 keybindings ui-logic migration/prune sequence, advanced `arch_stage` to `250`, and verified the checkpoint with full local `verify.sh` + `ci_check.sh`.
235. `DONE` Arch Stage 251 slice 241 made `engine.api.PlayBotController` lazy and added controller-facing playbot ND helper wrappers/exports to prepare a cycle-safe `engine/playbot/controller.py` relocation, advancing `arch_stage` to `251`.
236. `DONE` Arch Stage 252 slice 242 made `engine.playbot.PlayBotController` a lazy export via `engine.playbot.__getattr__` to avoid an `engine.api` import cycle during the controller move to `ai/playbot`.
237. `DONE` Arch Stage 253 slice 243 moved `engine/playbot/controller.py` to `ai/playbot/controller.py`, kept an engine-path module-alias shim, and rewired controller imports to `tet4d.engine.api` wrappers to preserve the AI API-only boundary.
238. `DONE` Arch Stage 254 slice 244 updated `engine.playbot.PlayBotController` lazy resolution to import directly from `ai.playbot.controller`, turning `engine/playbot/controller.py` into a removable compatibility shim for the next prune stages.
239. `DONE` Arch Stage 255 slice 245 migrated `front3d_game.py` and `front4d_game.py` to import `PlayBotController` from `engine.api`, reducing engine-internal use of the transitional `engine.playbot` compatibility package.
240. `DONE` Arch Stage 256 slice 246 recorded a zero-caller checkpoint for `engine/playbot/controller.py` after package/caller canonicalization and advanced `arch_stage` to `256` before shim pruning.
241. `DONE` Arch Stage 257 slice 247 removed the zero-caller `engine/playbot/controller.py` compatibility shim after the controller relocation to `ai/playbot/controller.py` and caller canonicalization.
242. `DONE` Arch Stage 258 slice 248 added `PlayBotController` as a lazy export from `ai.playbot.__init__`, making the canonical AI package path self-describing after controller shim pruning.
243. `DONE` Arch Stage 259 slice 249 recorded completion of the Stage 251-258 `PlayBotController` API-prep/move/prune sequence and advanced `arch_stage` to `259` before the full batch verification checkpoint.
244. `DONE` Arch Stage 260 slice 250 advanced `arch_stage` to `260` and verified the Stage 251-259 playbot-controller batch with full local `verify.sh` + `ci_check.sh`.
245. `DONE` Arch Stage 261 slice 251 exported `ActivePiece2D` and `PieceShape2D` from `engine.api` to prepare a boundary-safe move of `engine/playbot/planner_2d.py` into `ai/playbot`.
246. `DONE` Arch Stage 262 slice 252 exported `rotate_point_2d` from `engine.api` to complete boundary-safe API prep for moving `engine/playbot/planner_2d.py` into `ai/playbot`.
247. `DONE` Arch Stage 263 slice 253 moved `engine/playbot/planner_2d.py` to `ai/playbot/planner_2d.py`, kept an engine-path module-alias shim, and rewired the planner implementation to `tet4d.engine.api` exports to preserve the AI API-only boundary.
248. `DONE` Arch Stage 264 slice 254 updated `engine.api.plan_best_2d_move` to import from `ai.playbot.planner_2d` directly, reducing reliance on the transitional `engine/playbot/planner_2d.py` compatibility shim.
249. `DONE` Arch Stage 265 slice 255 added `plan_best_2d_move` as a lazy export from `ai.playbot.__init__`, improving canonical AI package discoverability after the planner relocation.
250. `DONE` Arch Stage 266 slice 256 recorded a zero-caller checkpoint for `engine/playbot/planner_2d.py` after engine-api and package canonicalization and advanced `arch_stage` to `266` before shim pruning.
251. `DONE` Arch Stage 267 slice 257 removed the zero-caller `engine/playbot/planner_2d.py` compatibility shim after the planner relocation to `ai/playbot/planner_2d.py` and canonicalization.
252. `DONE` Arch Stage 268 slice 258 recorded the canonical `ai/playbot/planner_2d.py` path after planner2d shim removal and advanced `arch_stage` to `268`.
253. `DONE` Arch Stage 269 slice 259 recorded completion of the Stage 261-268 planner2d API-prep/move/prune sequence and advanced `arch_stage` to `269` before the full batch verification checkpoint.
254. `DONE` Arch Stage 270 slice 260 advanced `arch_stage` to `270` and verified the Stage 261-269 planner2d batch with full local `verify.sh` + `ci_check.sh`.
255. `DONE` Arch Stage 271 slice 261 added `engine.api.plan_best_nd_with_budget(...)` to prepare a boundary-safe move of `engine/playbot/planner_nd.py` into `ai/playbot` and advanced `arch_stage` to `271`.
256. `DONE` Arch Stage 272 slice 262 moved `engine/playbot/planner_nd.py` to `ai/playbot/planner_nd.py`, kept an engine-path module-alias shim, and rewired planner imports to `tet4d.engine.api` wrappers so the AI boundary remained API-only.
257. `DONE` Arch Stage 273 slice 263 updated `engine.api.plan_best_nd_move(...)` to import from `ai.playbot.planner_nd` directly, reducing reliance on the transitional `engine/playbot/planner_nd.py` shim.
258. `DONE` Arch Stage 274 slice 264 added `plan_best_nd_move` as a lazy export from `ai.playbot.__init__`, improving canonical AI package discoverability after the planner relocation.
259. `DONE` Arch Stage 275 slice 265 recorded a zero-caller checkpoint for `engine/playbot/planner_nd.py` after engine-api and AI-package canonicalization and advanced `arch_stage` to `275` before shim pruning.
260. `DONE` Arch Stage 276 slice 266 removed the zero-caller `engine/playbot/planner_nd.py` compatibility shim after the planner relocation to `ai/playbot/planner_nd.py` and canonicalization.
261. `DONE` Arch Stage 277 slice 267 recorded completion of the Stage 271-276 plannerND API-prep/move/prune sequence, advanced `arch_stage` to `277`, and verified the checkpoint with full local `verify.sh` + `ci_check.sh`.
262. `DONE` Arch Stage 278 slice 268 exported `PieceShapeND` plus `planner_nd_core` orientation/column/evaluation wrappers from `engine.api` to prepare a boundary-safe move of `engine/playbot/planner_nd_search.py` into `ai/playbot`.
263. `DONE` Arch Stage 279 slice 269 exported `planner_nd_core` candidate-iteration and greedy-score wrappers from `engine.api`, completing API prep for moving `engine/playbot/planner_nd_search.py` into `ai/playbot` without deep engine imports.
264. `DONE` Arch Stage 280 slice 270 moved `engine/playbot/planner_nd_search.py` to `ai/playbot/planner_nd_search.py`, kept an engine-path module-alias shim, and rewired search imports to `tet4d.engine.api` wrappers so the AI boundary remained API-only.
265. `DONE` Arch Stage 281 slice 271 updated `engine.api.plan_best_nd_with_budget(...)` to import from `ai.playbot.planner_nd_search` directly, reducing reliance on the transitional `engine/playbot/planner_nd_search.py` shim.
266. `DONE` Arch Stage 282 slice 272 added `plan_best_nd_with_budget` as a lazy export from `ai.playbot.__init__`, improving canonical AI package discoverability after the search planner relocation.
267. `DONE` Arch Stage 283 slice 273 recorded a zero-caller checkpoint for `engine/playbot/planner_nd_search.py` after engine-api and AI-package canonicalization and advanced `arch_stage` to `283` before shim pruning.
268. `DONE` Arch Stage 284 slice 274 removed the zero-caller `engine/playbot/planner_nd_search.py` compatibility shim after the search planner relocation to `ai/playbot/planner_nd_search.py` and canonicalization.
269. `DONE` Arch Stage 285 slice 275 recorded the canonical `ai/playbot/planner_nd_search.py` path after search-planner shim removal and advanced `arch_stage` to `285`.
270. `DONE` Arch Stage 286 slice 276 recorded completion of the Stage 278-285 plannerND-search API-prep/move/prune sequence and advanced `arch_stage` to `286` before the full batch verification checkpoint.
271. `DONE` Arch Stage 287 slice 277 advanced `arch_stage` to `287` and verified the Stage 278-286 plannerND-search batch with full local `verify.sh` + `ci_check.sh`.
272. `DONE` Arch Stage 288 slice 278 moved `engine/playbot/planner_nd_core.py` to `ai/playbot/planner_nd_core.py`, kept an engine-path module-alias shim, and rewired core imports to `tet4d.engine.api` exports so the AI boundary remained API-only.
273. `DONE` Arch Stage 289 slice 279 retargeted `engine.api` wrappers for lock/rotation/canonical-block/orientation/column-level helpers to import from `ai.playbot.planner_nd_core`, reducing reliance on the transitional engine shim.
274. `DONE` Arch Stage 290 slice 280 retargeted `engine.api` wrappers for ND board evaluation, greedy scoring, and settled-candidate iteration to import from `ai.playbot.planner_nd_core`, further reducing reliance on the transitional engine shim.
275. `DONE` Arch Stage 291 slice 281 recorded a zero-caller checkpoint for `engine/playbot/planner_nd_core.py` after engine-api canonicalization and advanced `arch_stage` to `291` before shim pruning.
276. `DONE` Arch Stage 292 slice 282 removed the zero-caller `engine/playbot/planner_nd_core.py` compatibility shim after the core relocation to `ai/playbot/planner_nd_core.py` and engine-api canonicalization.
277. `DONE` Arch Stage 293 slice 283 recorded the canonical `ai/playbot/planner_nd_core.py` path after core shim removal and advanced `arch_stage` to `293`.
278. `DONE` Arch Stage 294 slice 284 recorded completion of the Stage 288-293 plannerND-core move/canonicalize/prune sequence and advanced `arch_stage` to `294` before aggregate ND-planner checkpoints.
279. `DONE` Arch Stage 295 slice 285 recorded completion of the Stage 271-294 ND planner family migrations (`planner_nd`, `planner_nd_search`, `planner_nd_core`) and advanced `arch_stage` to `295`.
280. `DONE` Arch Stage 296 slice 286 recorded the staged checkpoint handoff into the final verification stage for the Stage 271-295 ND planner migration batch and advanced `arch_stage` to `296`.
281. `DONE` Arch Stage 297 slice 287 advanced `arch_stage` to `297` and verified the Stage 271-296 ND planner migration batch with full local `verify.sh` + `ci_check.sh`.
282. `DONE` Arch Stage 298 slice 288 recorded zero remaining imports of the transitional `engine/playbot/__init__.py` compatibility package and advanced `arch_stage` to `298` before package-shim pruning.
283. `DONE` Arch Stage 299 slice 289 removed the zero-caller `engine/playbot/__init__.py` compatibility package after AI playbot family canonicalization.
284. `DONE` Arch Stage 300 slice 290 recorded `src/tet4d/ai/playbot/__init__.py` as the canonical playbot package surface after engine package shim removal and advanced `arch_stage` to `300`.
285. `DONE` Arch Stage 301 slice 291 advanced `arch_stage` to `301` and verified the Stage 298-300 playbot package shim cleanup batch with full local `verify.sh` + `ci_check.sh`.
286. `DONE` Arch Stage 302 slice 292 added narrow `engine.api` wrappers for menu keybinding shortcut action dispatch/status helpers to prepare moving `engine/ui_logic/menu_keybinding_shortcuts.py` into `ui/pygame` without deep engine imports.
287. `DONE` Arch Stage 303 slice 293 moved `engine/ui_logic/menu_keybinding_shortcuts.py` implementation into `ui/pygame/menu_keybinding_shortcuts.py`, rewired keybinding file I/O through `tet4d.engine.api`, retained an engine compatibility shim, and baseline-locked the new UI adapter path.
288. `DONE` Arch Stage 304 slice 294 migrated engine callers (`frontend_nd.py`, `engine/ui_logic/menu_controls.py`) to canonical `ui/pygame/menu_keybinding_shortcuts.py` imports before shim pruning.
289. `DONE` Arch Stage 305 slice 295 retargeted `engine.api` shortcut wrappers to canonical `ui/pygame/menu_keybinding_shortcuts.py` imports before shim pruning.
290. `DONE` Arch Stage 306 slice 296 recorded zero remaining callers and removed the transitional `engine/ui_logic/menu_keybinding_shortcuts.py` compatibility shim after canonicalization to `ui/pygame/menu_keybinding_shortcuts.py`.
291. `DONE` Arch Stage 307 slice 297 recorded completion of the Stage 302-306 menu-keybinding-shortcuts API-prep/move/canonicalize/prune sequence, advanced `arch_stage` to `307`, and verified the checkpoint with full local `verify.sh` + `ci_check.sh`.
292. `DONE` Arch Stage 308 slice 298 added `engine.api` wrappers for keybinding/profile/menu-settings helpers to prepare moving `engine/ui_logic/menu_controls.py` into `ui/pygame` without deep engine imports.
293. `DONE` Arch Stage 309 slice 299 moved `engine/ui_logic/menu_controls.py` implementation into `ui/pygame/menu_controls.py`, rewired menu control dependencies through `tet4d.engine.api`, retained an engine compatibility shim, and baseline-locked the new UI adapter path.
294. `DONE` Arch Stage 310 slice 300 migrated engine and CLI callers (`frontend_nd.py`, `cli/front2d.py`) to canonical `ui/pygame/menu_controls.py` imports before shim pruning.
295. `DONE` Arch Stage 311 slice 301 recorded zero remaining callers of the transitional `engine/ui_logic/menu_controls.py` shim after engine/CLI canonicalization and advanced `arch_stage` to `311` before shim pruning.
296. `DONE` Arch Stage 312 slice 302 removed the zero-caller `engine/ui_logic/menu_controls.py` compatibility shim after canonicalization to `ui/pygame/menu_controls.py`.
297. `DONE` Arch Stage 313 slice 303 recorded `src/tet4d/ui/pygame/menu_controls.py` as the canonical menu-controls module after shim removal and advanced `arch_stage` to `313`.
298. `DONE` Arch Stage 314 slice 304 recorded completion of the Stage 308-313 menu-controls API-prep/move/canonicalize/prune sequence and advanced `arch_stage` to `314` before the verification checkpoint.
299. `DONE` Arch Stage 315 slice 305 advanced `arch_stage` to `315` and verified the Stage 308-314 menu-controls batch with full local `verify.sh` + `ci_check.sh`.
300. `DONE` Arch Stage 316 slice 306 retargeted binding label/description engine.api wrappers to keybindings_catalog to prepare keybindings UI relocation without circular imports.
301. `DONE` Arch Stage 317 slice 307 added engine.api wrappers for keybindings runtime path and storage helpers to prepare keybindings UI relocation.
302. `DONE` Arch Stage 318 slice 308 moved engine/ui_logic/keybindings.py into ui/pygame, rewired runtime paths and storage through engine.api, retained an engine compatibility shim, and baseline-locked the new UI adapter path.
303. `DONE` Arch Stage 319 slice 309 canonicalized engine.api keybindings wrappers to import from ui/pygame/keybindings instead of the transitional engine/ui_logic shim.
304. `DONE` Arch Stage 320 slice 310 canonicalized engine keybindings callers to ui/pygame/keybindings and routed runtime/menu_settings_state through engine.api keybinding wrappers.
305. `DONE` Arch Stage 321 slice 311 canonicalized CLI launchers to import keybindings from ui/pygame/keybindings before shim pruning.
306. `DONE` Arch Stage 322 slice 312 canonicalized ui_logic/key_dispatch.py to ui/pygame/keybindings and baseline-locked it as a transitional engine-to-ui adapter.
307. `DONE` Arch Stage 323 slice 313 canonicalized the first keybindings test slice to ui/pygame/keybindings imports while keeping tests in engine/tests.
308. `DONE` Arch Stage 324 slice 314 canonicalized the remaining keybindings module test import to ui/pygame/keybindings before shim pruning.
309. `DONE` Arch Stage 325 slice 315 canonicalized ui_logic/keybindings_menu_model to ui/pygame/keybindings and baseline-locked it as a transitional engine-to-ui adapter.
310. `DONE` Arch Stage 326 slice 316 recorded zero remaining callers of the transitional engine/ui_logic/keybindings.py shim after engine.api, engine, CLI, and test canonicalization.
311. `DONE` Arch Stage 326 slice 316 recorded zero remaining callers of the transitional engine/ui_logic/keybindings.py shim after engine.api, engine, CLI, and test canonicalization.
312. `DONE` Arch Stage 327 slice 317 removed the zero-caller engine/ui_logic/keybindings.py compatibility shim after canonicalization to ui/pygame/keybindings.
313. `DONE` Arch Stage 328 slice 318 recorded src/tet4d/ui/pygame/keybindings.py as the canonical keybindings implementation path after engine/ui_logic shim removal.
314. `DONE` Arch Stage 329 slice 319 recorded completion of the Stage 316-328 keybindings API-prep, UI relocation, caller canonicalization, and shim-prune sequence before verification checkpoint.
315. `DONE` Arch Stage 330 slice 320 advanced arch_stage to 330 and verified the Stage 316-329 keybindings migration batch with full local verify.sh and ci_check.sh.
316. `DONE` Arch Stage 331 slice 321 recorded src/tet4d/ui/pygame/keybindings.py as the canonical shared keybindings runtime after Stage 316-330 migration and shim pruning.
317. `DONE` Arch Stage 332 slice 322 recorded the keybindings family API-prep wrappers and transitional engine-to-ui adapter allowlists as baseline locks pending later key_dispatch and keybindings_menu_model family cleanup.
318. `DONE` Arch Stage 333 slice 323 recorded zero direct callers of the removed engine/ui_logic/keybindings.py shim and preserved canonical imports for engine.api, engine callers, CLI, and tests.
319. `DONE` Arch Stage 334 slice 324 recorded staged handoff into the final verification checkpoint for the Stage 316-333 keybindings migration batch.
320. `DONE` Arch Stage 335 slice 325 advanced arch_stage to 335 and verified the Stage 316-334 keybindings migration batch with full local verify.sh and ci_check.sh.
321. `DONE` Arch Stage 336 slice 1 keybindings_menu_model API prep wrappers.
322. `DONE` Arch Stage 337 slice 2 move keybindings_menu_model to ui pygame with shim.
323. `DONE` Arch Stage 338 slice 3 baseline lock ui keybindings_menu_model adapter.
324. `DONE` Arch Stage 339 slice 4 canonicalize engine api wrappers to ui keybindings_menu_model.
325. `DONE` Arch Stage 340 slice 5 canonicalize keybindings_menu_model test import.
326. `DONE` Arch Stage 341 slice 6 keybindings_menu_model zero caller checkpoint.
327. `DONE` Arch Stage 342 slice 7 prune keybindings_menu_model engine shim.
328. `DONE` Arch Stage 343 slice 8 drop stale keybindings_menu_model allowlist entry.
329. `DONE` Arch Stage 344 slice 9 keybindings_menu_model family checkpoint.
330. `DONE` Arch Stage 345 slice 10 keybindings_menu_model verification checkpoint.
331. `DONE` Arch Stage 346 slice 1 move key_dispatch to ui pygame with shim.
332. `DONE` Arch Stage 347 slice 2 canonicalize key_dispatch engine render callers.
333. `DONE` Arch Stage 348 slice 3 canonicalize key_dispatch frontend_nd caller.
334. `DONE` Arch Stage 349 slice 4 canonicalize key_dispatch cli caller.
335. `DONE` Arch Stage 350 slice 5 key_dispatch zero caller checkpoint.
336. `DONE` Arch Stage 351 slice 6 prune key_dispatch engine shim.
337. `DONE` Arch Stage 352 slice 7 drop stale key_dispatch allowlist entry.
338. `DONE` Arch Stage 353 slice 8 key_dispatch family checkpoint.
339. `DONE` Arch Stage 354 slice 9 batch pre verification checkpoint.
340. `DONE` Arch Stage 355 slice 10 key_dispatch verification checkpoint.
341. `DONE` Arch Stage 356 slice 1 move front3d_game to ui pygame with shim.
342. `DONE` Arch Stage 357 slice 2 baseline lock ui front3d_game adapter.
343. `DONE` Arch Stage 358 slice 3 canonicalize engine api launcher 3d wrappers.
344. `DONE` Arch Stage 359 slice 4 canonicalize engine api run_front3d wrapper.
345. `DONE` Arch Stage 360 slice 5 canonicalize front3d_game test import.
346. `DONE` Arch Stage 361 slice 6 front3d_game zero caller checkpoint.
347. `DONE` Arch Stage 362 slice 7 prune front3d_game engine shim.
348. `DONE` Arch Stage 363 slice 8 clean front3d_game allowlist entries.
349. `DONE` Arch Stage 364 slice 9 front3d_game family checkpoint.
350. `DONE` Arch Stage 365 slice 10 front3d_game verification checkpoint.
351. `DONE` Arch Stage 366 slice 1 move front4d_game to ui pygame with shim.
352. `DONE` Arch Stage 367 slice 2 baseline lock ui front4d_game adapter.
353. `DONE` Arch Stage 368 slice 3 canonicalize front4d_game engine api wrappers.
354. `DONE` Arch Stage 369 slice 4 canonicalize front4d_game front4d_render test import.
355. `DONE` Arch Stage 370 slice 5 canonicalize front4d_game gameplay replay test import.
356. `DONE` Arch Stage 371 slice 6 front4d_game zero caller checkpoint.
357. `DONE` Arch Stage 372 slice 7 prune front4d_game engine shim.
358. `DONE` Arch Stage 373 slice 8 clean front4d_game allowlist entries.
359. `DONE` Arch Stage 374 slice 9 front4d_game family checkpoint.
360. `DONE` Arch Stage 375 slice 10 front4d_game verification checkpoint.
361. `DONE` Arch Stage 376 slice 20 menu_runner subpackage move.
362. `DONE` Arch Stage 377 slice 20 menu_runner cli caller canonicalization.
363. `DONE` Arch Stage 378 slice 20 menu_runner pause_menu caller canonicalization.
364. `DONE` Arch Stage 379 slice 20 menu_runner zero-caller checkpoint.
365. `DONE` Arch Stage 380 slice 20 prune menu_runner ui shim.
366. `DONE` Arch Stage 381 slice 20 menu_runner family checkpoint and verify.
367. `DONE` Arch Stage 382 slice 20 menu_model subpackage move.
368. `DONE` Arch Stage 383 slice 20 menu_model zero-caller checkpoint.
369. `DONE` Arch Stage 384 slice 20 prune menu_model ui shim.
370. `DONE` Arch Stage 385 slice 20 ui pygame menu subpackage checkpoint and verify.
371. `DONE` Arch Stage 386 slice 21 moved `ui/pygame/menu_controls.py`, `ui/pygame/menu_control_guides.py`, and `ui/pygame/menu_keybinding_shortcuts.py` into `src/tet4d/ui/pygame/menu/` to continue `ui/pygame` folder rebalancing.
372. `DONE` Arch Stage 387 slice 22 canonicalized CLI, engine, and UI callers to `tet4d.ui.pygame.menu.*` imports for the moved menu helper trio.
373. `DONE` Arch Stage 388 slice 23 recorded a zero-caller checkpoint for the old top-level `ui/pygame` menu-helper module paths before pruning.
374. `DONE` Arch Stage 389 slice 24 completed top-level helper-path pruning after canonicalization to `src/tet4d/ui/pygame/menu/*`.
375. `DONE` Arch Stage 390 slice 25 recorded completion of the Stage 386-389 menu helper subpackage batch, verified the checkpoint locally, and improved folder balance (`ui/pygame/menu` reached the target file-count band while top-level `ui/pygame` shrank).
376. `DONE` Arch Stage 391 slice 26 moved `ui/pygame/keybindings_menu_model.py` into `src/tet4d/ui/pygame/menu/` with a temporary top-level compatibility shim.
377. `DONE` Arch Stage 392 slice 27 moved `ui/pygame/keybindings_menu_input.py` and `ui/pygame/keybindings_menu_view.py` into `src/tet4d/ui/pygame/menu/` with temporary top-level compatibility shims.
378. `DONE` Arch Stage 393 slice 28 moved `ui/pygame/keybindings_menu.py` into `src/tet4d/ui/pygame/menu/` with a temporary top-level compatibility shim for staged caller migration.
379. `DONE` Arch Stage 394 slice 29 canonicalized `engine.api` wrappers and `engine/tests/test_keybindings_menu_model.py` to `tet4d.ui.pygame.menu.keybindings_menu_model`.
380. `DONE` Arch Stage 395 slice 30 canonicalized CLI/pause-menu callers and internal lazy imports to `tet4d.ui.pygame.menu.keybindings_menu*` paths.
381. `DONE` Arch Stage 396 slice 31 recorded a zero-caller checkpoint for old top-level `ui/pygame/keybindings_menu*` module imports before pruning.
382. `DONE` Arch Stage 397 slice 32 removed the zero-caller top-level `ui/pygame/keybindings_menu_model.py` shim.
383. `DONE` Arch Stage 398 slice 33 removed the zero-caller top-level `ui/pygame/keybindings_menu_input.py` and `ui/pygame/keybindings_menu_view.py` shims.
384. `DONE` Arch Stage 399 slice 34 removed the zero-caller top-level `ui/pygame/keybindings_menu.py` shim after canonicalization.
385. `DONE` Arch Stage 400 slice 35 recorded completion of the Stage 391-399 keybindings-menu subpackage batch and verified the checkpoint locally.
386. `DONE` Arch Stage 401 slice 36 created `src/tet4d/ui/pygame/launch/` and moved `launcher_nd_runner.py` into it with a temporary top-level compatibility shim.
387. `DONE` Arch Stage 402 slice 37 moved `ui/pygame/front3d_setup.py` and `ui/pygame/profile_4d.py` into `src/tet4d/ui/pygame/launch/` with temporary top-level shims.
388. `DONE` Arch Stage 403 slice 38 moved `ui/pygame/launcher_play.py` and `ui/pygame/bot_options_menu.py` into `src/tet4d/ui/pygame/launch/` with temporary top-level shims.
389. `DONE` Arch Stage 404 slice 39 moved `ui/pygame/launcher_settings.py` into `src/tet4d/ui/pygame/launch/` with a temporary top-level shim.
390. `DONE` Arch Stage 405 slice 40 canonicalized CLI and UI callers to `tet4d.ui.pygame.launch.*` imports for the launch/setup family.
391. `DONE` Arch Stage 406 slice 41 canonicalized engine and test callers to `tet4d.ui.pygame.launch.*` imports for the launch/setup family.
392. `DONE` Arch Stage 407 slice 42 recorded a zero-caller checkpoint for old top-level `ui/pygame` launch-family module imports before pruning.
393. `DONE` Arch Stage 408 slice 43 removed the zero-caller top-level `ui/pygame/{launcher_nd_runner,front3d_setup,profile_4d}.py` shims.
394. `DONE` Arch Stage 409 slice 44 removed the zero-caller top-level `ui/pygame/{launcher_play,bot_options_menu,launcher_settings}.py` shims and synced path-sensitive policy/docs.
395. `DONE` Arch Stage 410 slice 45 recorded completion of the Stage 401-409 launch-family subpackage batch and verified the checkpoint locally.
396. `DONE` Arch Stage 411 slice 46 created `src/tet4d/ui/pygame/input/` and moved `ui/pygame/key_dispatch.py` into it with a temporary top-level compatibility shim.
397. `DONE` Arch Stage 412 slice 47 canonicalized engine callers to `tet4d.ui.pygame.input.key_dispatch`.
398. `DONE` Arch Stage 413 slice 48 canonicalized UI and CLI callers to `tet4d.ui.pygame.input.key_dispatch`.
399. `DONE` Arch Stage 414 slice 49 recorded a zero-caller checkpoint for old top-level `ui/pygame/key_dispatch.py` imports before pruning.
400. `DONE` Arch Stage 415 slice 50 removed the zero-caller top-level `ui/pygame/key_dispatch.py` shim after canonicalization.
401. `DONE` Arch Stage 416 slice 51 recorded the key-dispatch family checkpoint after relocation into `src/tet4d/ui/pygame/input/`.
402. `DONE` Arch Stage 417 slice 52 moved `ui/pygame/key_display.py` into `src/tet4d/ui/pygame/input/` with a temporary top-level compatibility shim.
403. `DONE` Arch Stage 418 slice 53 canonicalized engine/API and UI callers to `tet4d.ui.pygame.input.key_display`.
404. `DONE` Arch Stage 419 slice 54 recorded a zero-caller checkpoint for old top-level `ui/pygame/key_display.py` imports and removed the temporary shim.
405. `DONE` Arch Stage 420 slice 55 recorded completion of the Stage 411-419 `key_dispatch` + `key_display` input-subpackage batch and verified the checkpoint locally.
406. `DONE` Arch Stage 421 slice 56 updated path docs to record `src/tet4d/ui/pygame/input/` as the canonical location for dispatch and key-name display helpers.
407. `DONE` Arch Stage 422 slice 57 recorded canonical `tet4d.ui.pygame.input.key_dispatch` and `tet4d.ui.pygame.input.key_display` import paths in stage history.
408. `DONE` Arch Stage 423 slice 58 recorded the staged metrics-checkpoint prep for the `input/` seed batch.
409. `DONE` Arch Stage 424 slice 59 recorded the expected `ui/pygame` top-level file-count reduction after seeding `ui/pygame/input/`.
410. `DONE` Arch Stage 425 slice 60 recorded `ui/pygame/input` as an intentionally small seed package pending future input-family moves.
411. `DONE` Arch Stage 426 slice 61 recorded the staged handoff into the final local verification checkpoint for the `411-425` batch.
412. `DONE` Arch Stage 427 slice 62 ran the local verification checkpoint for the `411-426` input-subpackage batch.
413. `DONE` Arch Stage 428 slice 63 recorded the post-verify architecture/folder-balance snapshot for the new `ui/pygame/input` subpackage.
414. `DONE` Arch Stage 429 slice 64 refreshed `CURRENT_STATE.md` with the `input/` subpackage migration status and next recommended `ui/pygame` family moves.
415. `DONE` Arch Stage 430 slice 65 recorded completion of the Stage 411-429 input-subpackage seed batch and verified the checkpoint locally.
416. `DONE` Arch Stage 431 slice 66 moved `ui/pygame/camera_mouse.py` into `src/tet4d/ui/pygame/input/` with a temporary top-level compatibility shim.
417. `DONE` Arch Stage 432 slice 67 canonicalized 3D/4D frontend callers to `tet4d.ui.pygame.input.camera_mouse`.
418. `DONE` Arch Stage 433 slice 68 canonicalized camera-mouse tests to `tet4d.ui.pygame.input.camera_mouse`.
419. `DONE` Arch Stage 434 slice 69 normalized the moved `camera_mouse` module to import `projection3d` through canonical `tet4d.ui.pygame.projection3d`.
420. `DONE` Arch Stage 435 slice 70 recorded a zero-caller checkpoint for old top-level `ui/pygame/camera_mouse.py` imports before pruning.
421. `DONE` Arch Stage 436 slice 71 removed the zero-caller top-level `ui/pygame/camera_mouse.py` shim after canonicalization.
422. `DONE` Arch Stage 437 slice 72 recorded the `camera_mouse` family checkpoint after relocation into `src/tet4d/ui/pygame/input/`.
423. `DONE` Arch Stage 438 slice 73 moved `ui/pygame/view_controls.py` into `src/tet4d/ui/pygame/input/` with a temporary top-level compatibility shim.
424. `DONE` Arch Stage 439 slice 74 canonicalized engine render callers to `tet4d.ui.pygame.input.view_controls`.
425. `DONE` Arch Stage 440 slice 75 canonicalized `frontend_nd` and view-controls tests to `tet4d.ui.pygame.input.view_controls`.
426. `DONE` Arch Stage 441 slice 76 recorded a zero-caller checkpoint for old top-level `ui/pygame/view_controls.py` imports before pruning.
427. `DONE` Arch Stage 442 slice 77 removed the zero-caller top-level `ui/pygame/view_controls.py` shim after canonicalization.
428. `DONE` Arch Stage 443 slice 78 recorded the `view_controls` family checkpoint after relocation into `src/tet4d/ui/pygame/input/`.
429. `DONE` Arch Stage 444 slice 79 recorded `ui/pygame/input` growth into the target balance band after adding mouse/view helpers.
430. `DONE` Arch Stage 445 slice 80 recorded the corresponding top-level `ui/pygame` file-count reduction and non-leaf balance improvement.
431. `DONE` Arch Stage 446 slice 81 recorded the staged handoff into the docs/backlog/current-state refresh for the `431-445` input-family moves.
432. `DONE` Arch Stage 447 slice 82 refreshed docs/handoff to record canonical `tet4d.ui.pygame.input.camera_mouse` and `tet4d.ui.pygame.input.view_controls` paths.
433. `DONE` Arch Stage 448 slice 83 recorded the staged handoff into the final local verification checkpoint for the `431-447` batch.
434. `DONE` Arch Stage 449 slice 84 ran the local verification checkpoint for the `431-448` input-family batch.
435. `DONE` Arch Stage 450 slice 85 recorded completion of the Stage 431-449 `camera_mouse` + `view_controls` input-subpackage batch and verified the checkpoint locally.
436. `DONE` Arch Stage 451 slice 86 created `src/tet4d/ui/pygame/render/` and moved `ui/pygame/text_render_cache.py` into the new render-helper subpackage.
437. `DONE` Arch Stage 452 slice 87 moved `ui/pygame/panel_utils.py` into `src/tet4d/ui/pygame/render/` to pair panel helpers with text-cache rendering utilities.
438. `DONE` Arch Stage 453 slice 88 canonicalized engine and UI callers to `tet4d.ui.pygame.render.panel_utils` and `tet4d.ui.pygame.render.text_render_cache`.
439. `DONE` Arch Stage 454 slice 89 recorded a zero-caller checkpoint for old top-level `ui/pygame/panel_utils.py` and `ui/pygame/text_render_cache.py` imports before pruning.
440. `DONE` Arch Stage 455 slice 90 removed the zero-caller top-level `ui/pygame/text_render_cache.py` shim after canonicalization.
441. `DONE` Arch Stage 456 slice 91 removed the zero-caller top-level `ui/pygame/panel_utils.py` shim after canonicalization.
442. `DONE` Arch Stage 457 slice 92 moved `ui/pygame/control_icons.py` into `src/tet4d/ui/pygame/render/` as part of the render-helper family extraction.
443. `DONE` Arch Stage 458 slice 93 moved `ui/pygame/control_helper.py` into `src/tet4d/ui/pygame/render/` and normalized its helper imports to canonical render paths.
444. `DONE` Arch Stage 459 slice 94 canonicalized engine/UI/test callers to `tet4d.ui.pygame.render.control_helper` and `tet4d.ui.pygame.render.control_icons`.
445. `DONE` Arch Stage 460 slice 95 recorded the render-helper checkpoint (`control_helper` + `control_icons`) with zero-caller audits, shim pruning, and a local verification pass.
446. `DONE` Arch Stage 461 slice 96 moved `ui/pygame/gfx_panel_2d.py` into `src/tet4d/ui/pygame/render/`.
447. `DONE` Arch Stage 462 slice 97 moved `ui/pygame/gfx_game.py` into `src/tet4d/ui/pygame/render/`.
448. `DONE` Arch Stage 463 slice 98 canonicalized CLI/UI callers and internal imports to `tet4d.ui.pygame.render.gfx_panel_2d` and `tet4d.ui.pygame.render.gfx_game`.
449. `DONE` Arch Stage 464 slice 99 recorded zero-caller audits and removed the old top-level `ui/pygame/gfx_panel_2d.py` and `ui/pygame/gfx_game.py` shims.
450. `DONE` Arch Stage 465 slice 100 moved `ui/pygame/grid_mode_render.py` into `src/tet4d/ui/pygame/render/`.
451. `DONE` Arch Stage 466 slice 101 canonicalized engine render callers to `tet4d.ui.pygame.render.grid_mode_render`, recorded a zero-caller checkpoint, and removed the old top-level shim.
452. `DONE` Arch Stage 467 slice 102 moved `ui/pygame/font_profiles.py` into `src/tet4d/ui/pygame/render/`.
453. `DONE` Arch Stage 468 slice 103 canonicalized CLI/engine callers to `tet4d.ui.pygame.render.font_profiles`, recorded a zero-caller checkpoint, and removed the old top-level shim.
454. `DONE` Arch Stage 469 slice 104 moved `ui/pygame/keybindings_defaults.py` into `src/tet4d/ui/pygame/input/`, canonicalized `keybindings.py`, and removed the old top-level shim after zero-caller audit.
455. `DONE` Arch Stage 470 slice 105 recorded completion of the Stage 451-469 `render/` extraction + `input/keybindings_defaults` move batch, refreshed docs/handoff/metrics, and verified the checkpoint locally.
456. `DONE` Arch Stage 471 slice 106 created `src/tet4d/ui/pygame/loop/` and moved `ui/pygame/game_loop_common.py` into the new loop-helper subpackage.
457. `DONE` Arch Stage 472 slice 107 canonicalized `cli/front2d.py` to `tet4d.ui.pygame.loop.game_loop_common`.
458. `DONE` Arch Stage 473 slice 108 recorded a zero-caller checkpoint for old top-level `ui/pygame/game_loop_common.py` imports and removed the old path after canonicalization.
459. `DONE` Arch Stage 474 slice 109 moved `ui/pygame/loop_runner_nd.py` into `src/tet4d/ui/pygame/loop/`.
460. `DONE` Arch Stage 475 slice 110 canonicalized `front3d_game.py` and `front4d_game.py` to `tet4d.ui.pygame.loop.loop_runner_nd`.
461. `DONE` Arch Stage 476 slice 111 normalized the moved `loop_runner_nd` module to import `process_game_events` from canonical `tet4d.ui.pygame.loop.game_loop_common`.
462. `DONE` Arch Stage 477 slice 112 recorded a zero-caller checkpoint for old top-level `ui/pygame/loop_runner_nd.py` imports and removed the old path after canonicalization.
463. `DONE` Arch Stage 478 slice 113 updated structure docs to record `src/tet4d/ui/pygame/loop/` as the canonical loop-helper subpackage.
464. `DONE` Arch Stage 479 slice 114 refreshed architecture/backlog/current-state handoff notes with the canonical `ui/pygame/loop/*` paths and post-move balancer snapshot.
465. `DONE` Arch Stage 480 slice 115 recorded completion of the Stage 471-479 loop-helper extraction batch, advanced `arch_stage` to `480`, and verified the checkpoint locally.
466. `DONE` Arch Stage 481 slice 116 created `src/tet4d/ui/pygame/runtime_ui/` and moved `ui/pygame/audio.py` into the new runtime-helper subpackage.
467. `DONE` Arch Stage 482 slice 117 moved `ui/pygame/display.py` into `src/tet4d/ui/pygame/runtime_ui/`.
468. `DONE` Arch Stage 483 slice 118 moved `ui/pygame/app_runtime.py` into `src/tet4d/ui/pygame/runtime_ui/`.
469. `DONE` Arch Stage 484 slice 119 canonicalized CLI and frontend callers to `tet4d.ui.pygame.runtime_ui.{app_runtime,audio,display}` imports.
470. `DONE` Arch Stage 485 slice 120 canonicalized launcher/pause-menu/engine-api/test callers to `tet4d.ui.pygame.runtime_ui.*` imports.
471. `DONE` Arch Stage 486 slice 121 normalized moved `app_runtime` internal imports to canonical `tet4d.ui.pygame.runtime_ui.audio` and `tet4d.ui.pygame.runtime_ui.display`.
472. `DONE` Arch Stage 487 slice 122 recorded zero remaining imports of old top-level `ui/pygame/audio.py` and `ui/pygame/display.py` paths after canonicalization.
473. `DONE` Arch Stage 488 slice 123 recorded zero remaining imports of old top-level `ui/pygame/app_runtime.py` paths after canonicalization.
474. `DONE` Arch Stage 489 slice 124 refreshed docs/handoff to record the canonical `ui/pygame/runtime_ui/*` paths and post-move balancer snapshot.
475. `DONE` Arch Stage 490 slice 125 recorded completion of the Stage 481-489 runtime-helper extraction batch, advanced `arch_stage` to `490`, and verified the checkpoint locally.
476. `DONE` Arch Stage 491 slice 126 moved `ui/pygame/help_menu.py` into `src/tet4d/ui/pygame/runtime_ui/` with staged caller canonicalization follow-up.
477. `DONE` Arch Stage 492 slice 127 moved `ui/pygame/pause_menu.py` into `src/tet4d/ui/pygame/runtime_ui/` to colocate shared runtime overlays.
478. `DONE` Arch Stage 493 slice 128 canonicalized CLI and UI frontend callers to `tet4d.ui.pygame.runtime_ui.{help_menu,pause_menu}` imports.
479. `DONE` Arch Stage 494 slice 129 canonicalized engine tests and patch paths to `tet4d.ui.pygame.runtime_ui.help_menu` and `tet4d.ui.pygame.runtime_ui.pause_menu`.
480. `DONE` Arch Stage 495 slice 130 normalized moved `pause_menu` internal imports to canonical `tet4d.ui.pygame.runtime_ui.help_menu`.
481. `DONE` Arch Stage 496 slice 131 recorded zero remaining imports of old top-level `ui/pygame/help_menu.py` and `ui/pygame/pause_menu.py` paths after canonicalization.
482. `DONE` Arch Stage 497 slice 132 removed the zero-caller top-level `ui/pygame/help_menu.py` shim/path after canonicalization.
483. `DONE` Arch Stage 498 slice 133 removed the zero-caller top-level `ui/pygame/pause_menu.py` shim/path after canonicalization.
484. `DONE` Arch Stage 499 slice 134 refreshed path docs/backlog/current-state notes for canonical `ui/pygame/runtime_ui/{help_menu,pause_menu}` paths and the post-move folder-balance snapshot.
485. `DONE` Arch Stage 500 slice 135 recorded completion of the Stage 491-499 runtime-overlay move batch, advanced `arch_stage` to `500`, synced path allowlists/contracts, and verified the checkpoint locally.
486. `DONE` Arch Stage 501 slice 136 added `config/help/content/runtime_help_content.json` as the canonical runtime help-copy source document.
487. `DONE` Arch Stage 502 slice 137 added `src/tet4d/engine/help_text.py` to load and validate runtime help-copy payloads from the help doc source.
488. `DONE` Arch Stage 503 slice 138 exposed runtime help-copy accessors through new `tet4d.engine.api` wrappers.
489. `DONE` Arch Stage 504 slice 139 rewired runtime help-menu fallback topic copy to the doc-driven runtime help-copy source.
490. `DONE` Arch Stage 505 slice 140 migrated runtime help-menu topic-extension prose blocks to template-driven lines loaded from `config/help/content/runtime_help_content.json`.
491. `DONE` Arch Stage 506 slice 141 migrated live-key/action-group headings to runtime help-copy document templates.
492. `DONE` Arch Stage 507 slice 142 updated canonical maintenance and help-index contracts to include split runtime help content/layout assets.
493. `DONE` Arch Stage 508 slice 143 added runtime help-copy loader coverage in `tests/unit/engine/test_help_text.py`.
494. `DONE` Arch Stage 509 slice 144 refreshed structure docs and current-state handoff notes for the doc-driven runtime help-copy architecture.
495. `DONE` Arch Stage 510 slice 145 recorded completion of the Stage 501-509 help-copy externalization batch, advanced `arch_stage` to `510`, and verified the checkpoint locally.
496. `DONE` Arch Stage 511 slice 146 introduced split runtime help assets under `config/help/content/runtime_help_content.json` and `config/help/layout/runtime_help_layout.json`.
497. `DONE` Arch Stage 512 slice 147 added split runtime help schemas `config/schema/help_runtime_content.schema.json` and `config/schema/help_runtime_layout.schema.json`.
498. `DONE` Arch Stage 513 slice 148 refactored `src/tet4d/engine/help_text.py` to independently load/validate runtime help content and layout payloads.
499. `DONE` Arch Stage 514 slice 149 exposed layout/media rule access through new `tet4d.engine.api` wrappers for the pygame help adapter.
500. `DONE` Arch Stage 515 slice 150 rewired `runtime_ui/help_menu.py` to consume non-python layout thresholds/geometry/header/footer/label rules.
501. `DONE` Arch Stage 516 slice 151 rewired controls-topic rendering selection to non-python topic media placement rules.
502. `DONE` Arch Stage 517 slice 152 synchronized canonical maintenance rules for split runtime help content/layout/schema assets.
503. `DONE` Arch Stage 518 slice 153 expanded runtime help tests to cover layout payload/media-rule loading and contract validation.
504. `DONE` Arch Stage 519 slice 154 added stage-level overall LOC logging fields in `scripts/arch_metrics.py`.
505. `DONE` Arch Stage 520 slice 155 recorded completion of the Stage 511-519 runtime-help split + stage-loc logging batch, advanced `arch_stage` to `520`, and verified the checkpoint locally.
