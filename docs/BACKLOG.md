# Consolidated Backlog

Generated: 2026-02-18  
Updated: 2026-03-01  
Scope: active open backlog, governance watchlist, and current change footprint.

## 1. Priority Verification Rules

1. `P1` = user-facing correctness, consistency, and discoverability gaps.
2. `P2` = maintainability and complexity risks that can cause regressions.
3. `P3` = optimization, tuning, and documentation hygiene.

## 2. Unified Change Set (Implemented Baseline)

Historical DONE summaries were deduplicated and moved to a single source:

- `docs/history/DONE_SUMMARIES.md`

Policy for updates:

1. New implementation detail belongs in `## 5. Change Footprint` for the active batch.
2. At batch close, summarize and append durable DONE history in `docs/history/DONE_SUMMARIES.md`.
3. Keep `docs/BACKLOG.md` focused on active open issues and near-term execution.

Historical anchor references:

- `[BKL-P3-001]` pre-push local CI gate checkpoint is closed and retained in historical DONE source.

## 3. Active Open Backlog / TODO (Unified RDS Gaps + Technical Debt)

1. Canonical machine-readable debt source:
   `config/project/backlog_debt.json` (`active_debt_items`).
2. Policy-pack and context-router manifests are contract-validated via:
   `tools/governance/validate_project_contracts.py`.

### Historical ID Lineage Policy

1. Backlog IDs must be unique in this file for unambiguous audit/search.
2. Legacy rerolled IDs use `-R2` suffix (for example `BKL-P2-010-R2`) when an original ID already exists in historical DONE ledgers.
3. Legacy/base references are retained in historical files; active/open tracking stays in this file.

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
4. `WATCH` `[BKL-P3-007]` Module decomposition watch:
   large engine/runtime/ui module split pressure moved from active debt to watch
   after shared-settings and API dedup passes; monitor hotspot growth and
   continue staged LOC reduction.

## 4. Gap Mapping to RDS

1. `docs/rds/RDS_TETRIS_GENERAL.md`: CI/stability workflows and setup-menu dedup follow-up are closed; maintain drift watch only.
2. `docs/rds/RDS_PLAYBOT.md`: learning-mode architecture is implemented; maintain tuning/stability watch only.
3. `docs/rds/RDS_MENU_STRUCTURE.md`: menu graph modularization and interactive topology-lab workflow are closed; maintain drift watch only.
4. `docs/rds/RDS_FILE_FETCH_LIBRARY.md`: lifecycle/adaptive-fetch design baseline exists; implementation remains future-scoped.

## 5. Change Footprint (Current Batch)

Current sub-batch (2026-03-02): helper-panel runtime stability + cross-mode structure unification.

- Expanded release-packaging CI matrix to publish separate artifacts for:
  Linux, Windows, macOS x64, and macOS ARM64:
  - `.github/workflows/release-packaging.yml`
- Synced packaging docs with the explicit CI target list:
  - `docs/RELEASE_INSTALLERS.md`
- Unified default side-panel width across gameplay dimensions by aligning
  2D `rendering.2d.side_panel` with 3D/4D (`360`) via config-backed constants:
  - `config/project/constants.json`
  - `src/tet4d/engine/runtime/project_config.py`
  - `src/tet4d/ui/pygame/render/gfx_game.py`
- Fixed side-panel structure drift after gameplay state changes by keeping control
  panel sizing stable and clipping low-priority data separately in:
  - `src/tet4d/ui/pygame/render/panel_utils.py`
- Unified helper control-group skeleton for 2D/3D/4D side panels (same panel set
  and order with mode placeholders where controls are unavailable) in:
  - `src/tet4d/ui/pygame/render/control_helper.py`
- Enforced canonical runtime panel priority order:
  - `Main` > `Translation` > `Rotation` > `Camera` > `Data`
- Merged former `View/Overlay` actions into `Camera` so control tiers are explicit.
- Kept low-priority runtime lines inside the dedicated titled `Data` panel only.
- Reserved minimum layout space for `Data` so runtime/bot/analysis lines render in
  a boxed panel instead of collapsing under control-area pressure.
- Enforced full rotation helper visibility before lower-priority camera trimming:
  - 3D keeps all 3 rotation pairs.
  - 4D keeps all 6 rotation pairs.
- Canonical helper layout source updated:
  - `config/help/layout/runtime_help_action_layout.json`
- Added regression coverage for unified-structure guarantees:
  - `tests/unit/engine/test_control_ui_helpers.py`

Current sub-batch (2026-03-01): helper-panel unification and priority rendering fix.

- Unified 2D side-panel rendering with the shared panel pipeline used by 3D/4D:
  - `src/tet4d/ui/pygame/render/gfx_panel_2d.py`
  - `src/tet4d/ui/pygame/render/panel_utils.py`
- Unified summary/data composition via shared helper used by 2D/3D/4D:
  - `draw_unified_game_side_panel(...)` in `src/tet4d/ui/pygame/render/panel_utils.py`
  - `src/tet4d/engine/front3d_render.py`
  - `src/tet4d/engine/front4d_render.py`
- Simplified helper-panel utility internals by collapsing redundant text-row builders
  and summary-row merge helpers in:
  - `src/tet4d/ui/pygame/render/panel_utils.py`
- Further simplified helper-panel rendering flow to one compact unified path
  (`draw_unified_game_side_panel`) with reduced internal branch/adapter count.
- Merged top summary rows into `Main` as a single panel (title/score/lines/speed + main controls).
- Kept strict priority ordering under constrained height:
  - `Main` > `Translation`/`Rotation` > `Camera` > `View/Overlay` > `Data`.
- Added dedicated titled `Data` panel for tier-5 runtime/bot/analysis lines.
- Updated helper layout tiers and group minima:
  - `config/help/layout/runtime_help_action_layout.json`
  - `src/tet4d/ui/pygame/render/control_helper.py`
- Added regression coverage for summary-to-main merge behavior:
  - `tests/unit/engine/test_panel_utils.py`

Current sub-batch (2026-03-01): helper-panel tiering update for gameplay side panels.

- Reordered helper tiers across modes so top panel is consistent:
  - Tier 1: game title + score/lines/speed + `Main`
  - Tier 2: `Translation` + `Rotation`
  - Tier 3: `Camera`
  - Tier 4: `View/Overlay` (`locked-cells alpha`, `projection` where supported)
  - Tier 5: remaining runtime/bot/analysis data lines
- Canonicalized helper section membership/order in:
  - `config/help/layout/runtime_help_action_layout.json`
- Updated side-panel summary labels to use `Lines` in all modes:
  - `src/tet4d/engine/front3d_render.py`
  - `src/tet4d/engine/front4d_render.py`
- Updated helper-group coverage expectations:
  - `tests/unit/engine/test_control_ui_helpers.py`

Current sub-batch (2026-03-01): helper-panel contract unification (config intent + engine feasibility).

- Replaced hardcoded helper-group membership logic with data-driven panels/lines from:
  - `config/help/layout/runtime_help_action_layout.json`
- Added engine contract validation + runtime panel filtering:
  - `src/tet4d/engine/help_text.py`
  - `src/tet4d/engine/api.py`
- Rewired helper rendering to consume engine-provided panel specs while keeping shared rendering style:
  - `src/tet4d/ui/pygame/render/control_helper.py`
- Added coverage for helper-action layout constraints and capability-based line filtering:
  - `tests/unit/engine/test_help_text.py`
- Design sync:
  - `docs/rds/RDS_MENU_STRUCTURE.md`

Current sub-batch (2026-03-01): leaderboard runtime + scoring-help documentation + helper-panel camera visibility.

- Added persistent cross-mode leaderboard runtime storage and API adapters:
  - `src/tet4d/engine/runtime/leaderboard.py`
  - `src/tet4d/engine/runtime/project_config.py`
  - `src/tet4d/engine/api.py`
  - `config/project/io_paths.json`
  - `config/project/constants.json`
- Added leaderboard UI + launcher/pause routing:
  - `src/tet4d/ui/pygame/launch/leaderboard_menu.py`
  - `cli/front.py`
  - `src/tet4d/ui/pygame/runtime_ui/pause_menu.py`
  - `config/menu/structure.json`
  - `src/tet4d/engine/ui_logic/menu_action_contracts.py`
- Added runtime session submission hooks in gameplay loops:
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
- Added scoring-rule explanations to non-Python help assets:
  - `config/help/topics.json`
  - `config/help/content/runtime_help_content.json`
- Improved 3D/4D in-game helper panel prioritization so camera actions appear before lower-priority groups:
  - `src/tet4d/ui/pygame/render/control_helper.py`
- Added/updated regression coverage:
  - `tests/unit/engine/test_leaderboard.py`
  - `tests/unit/engine/test_menu_policy.py`
  - `tests/unit/engine/test_pause_menu.py`
  - `tests/unit/engine/test_front_launcher_routes.py`
  - `tests/unit/engine/test_control_ui_helpers.py`
  - `tests/unit/engine/test_project_config.py`
- Verification:
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Hotfix (2026-03-01, same batch):
- Leaderboard session capture now records restart outcomes (keyboard restart and pause-menu restart) for 2D/3D/4D loops.
- 3D/4D helper panel ordering aligned to priority:
  - score summary first, then Translation, Rotation, Camera/View, System(menu), then low-priority data.
- Leaderboard entries now capture player names, and qualifying sessions prompt for player-name entry before commit.
- 4D viewer-relative input mapping now preserves translation/rotation intent across camera yaw and hyper-view (XW/ZW) rotations via basis-aware axis routing; added regression coverage in `tests/unit/engine/test_nd_routing.py`.
- Helper panel cleanup:
  - removed duplicated locked-cell-transparency line from 3D/4D side-panel headers (meter remains canonical display).
  - retained Camera/View ahead of System in grouped helper ordering while adding constrained-height row planning so System (`menu`, `help`, `restart`) remains visible.
- Leaderboard visual refresh:
  - switched to a structured table layout with explicit column headers and cell demarcations.
  - removed outcome/exit-type from displayed leaderboard columns.
- Helper panel visibility/layout follow-up:
  - improved narrow-panel key/action text fit by rebalancing key/value columns.
  - split 3D/4D side-panel priority tiers so score + dimensions stay in the top section.
  - moved camera and extended runtime state details to the low-priority section below controls.
  - prioritized camera control group visibility while retaining system controls (`menu`, `help`, `restart`) in grouped helper rendering.
- Code-review hardening follow-up:
  - fixed leaderboard table width scaling to prevent narrow-screen column overflow.
  - removed dead `_overlay_alpha_label` helpers no longer referenced by 3D/4D panel rendering.
  - added regression coverage for helper-group constrained-height planning and leaderboard column scaling:
    - `tests/unit/engine/test_control_ui_helpers.py`
    - `tests/unit/engine/test_leaderboard_menu.py`
- Helper-panel policy follow-up:
  - folded system controls into the top `Main` helper group (removed separate `System` group block).
  - removed the overflow footer copy (`open Help for full key guide`).
  - emphasized key-name rendering in helper rows.
  - moved `Dims`, `Score mod`, and locked-cell transparency into low-priority data lines; kept `Speed level` in top panel.

Current sub-batch (2026-03-01): stage 836+ governance contract tightening (context-router manifest).

- Added strict context-router manifest validation in project contracts:
  - `tools/governance/validate_project_contracts.py`
- Added regression coverage:
  - `tests/unit/engine/test_validate_project_contracts.py`
- Backlog TODO cleanup:
  - converted context-router and policy-pack consolidation TODO entries into enforced contract checks.

Current sub-batch (2026-03-01): stage 835+ playbot learning-mode baseline and debt closure.

- Added deterministic adaptive learning mode (`LEARN`) for playbot profile tuning:
  - `src/tet4d/ai/playbot/types.py`
  - `src/tet4d/ai/playbot/controller.py`
- Added runtime policy keys for learning thresholds/window and validation wiring:
  - `config/playbot/policy.json`
  - `src/tet4d/engine/runtime/runtime_config_validation_playbot.py`
  - `src/tet4d/engine/runtime/runtime_config.py`
  - `src/tet4d/engine/runtime/settings_schema.py`
  - `config/gameplay/tuning.json` (`assist_scoring.bot_factors.learn`)
- Added regression coverage:
  - `tests/unit/engine/test_playbot.py`
  - `tests/unit/engine/test_runtime_config.py`
- Debt source reprioritization:
  - closed `BKL-P2-024` in `config/project/backlog_debt.json`
  - added operational tuning watch `BKL-P3-009`.

Current sub-batch (2026-03-01): stage 827-834 topology-lab workflow completion + launcher/runtime wiring.

- Added Topology Lab non-Python content/layout asset:
  - `config/topology/lab_menu.json`
- Added launcher-play Topology Lab interactive flow:
  - `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
  - `cli/front.py`
- Simplified launcher routing by making `Topology Lab` a direct `Play` action:
  - `config/menu/structure.json`
  - `src/tet4d/engine/ui_logic/menu_action_contracts.py`
  - `tests/unit/engine/test_menu_policy.py`
- Added runtime API adapters used by topology-lab workflow:
  - `src/tet4d/engine/api.py`
- Added shared numeric text-input helper and reused it in settings/lab menus:
  - `src/tet4d/ui/pygame/menu/numeric_text_input.py`
  - `src/tet4d/ui/pygame/launch/launcher_settings.py`
- Added regression coverage:
  - `tests/unit/engine/test_topology_lab_menu.py`
  - `tests/unit/engine/test_front_launcher_routes.py`
  - `tests/unit/engine/test_numeric_text_input.py`
- Canonical maintenance sync:
  - `config/project/policy/manifests/canonical_maintenance.json`
- Debt source sync:
  - closed `BKL-P2-023` in `config/project/backlog_debt.json`
- Verification:
  - `CODEX_MODE=1 ./scripts/verify.sh` passed
  - targeted menu/front/topology suites passed.

Current sub-batch (2026-03-01): stage 814+ shared gameplay-settings dedup + API dispatch cleanup.

- Consolidated shared gameplay settings load/save/clamp logic into runtime state layer:
  - `src/tet4d/engine/runtime/menu_settings_state.py`
  - `src/tet4d/engine/runtime/settings_schema.py`
- Added engine API runtime adapters for shared gameplay settings access:
  - `src/tet4d/engine/api.py`
- Rewired runtime consumers to use shared helpers (removed duplicate speedup parsing/clamps):
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
  - `src/tet4d/ui/pygame/launch/launcher_settings.py`
- Added regression coverage for shared gameplay settings persistence/clamp behavior:
  - `tests/unit/engine/test_keybindings.py`
- Backlog reprioritization:
  - moved decomposition pressure from active debt (`BKL-P2-027`) to operational
    watch (`BKL-P3-007`) in `config/project/backlog_debt.json` after this dedup
    tranche.
- Verification:
  - targeted suites passed (`test_keybindings.py`, `test_menu_policy.py`,
    `test_front3d_setup.py`, `test_pause_menu.py`,
    `test_display_resize_persistence.py`, `tests/test_leveling.py`)
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-01): pause hotkey parity + deterministic auto speed-up controls.

- Added dedicated pause hotkey default (`F10`) alongside `m`:
  - `config/keybindings/defaults.json`
  - `keybindings/2d.json`
  - `keybindings/3d.json`
  - `keybindings/4d.json`
- Added shared advanced gameplay defaults and settings row:
  - `config/menu/defaults.json` (`auto_speedup_enabled`, `lines_per_level`)
  - `config/menu/structure.json` (`gameplay_advanced` entry + category metrics update)
- Implemented settings hub advanced gameplay submenu and persistence wiring:
  - `src/tet4d/ui/pygame/launch/launcher_settings.py`
- Implemented deterministic speed-level helper:
  - `src/tet4d/engine/gameplay/leveling.py`
  - `tests/test_leveling.py`
- Applied speed-level progression in runtime loops (2D/3D/4D), with restart reset
  to session base speed and runtime gravity reconfiguration:
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
- Added engine API adapter for leveling helper to keep architecture boundary clean:
  - `src/tet4d/engine/api.py`
- Verification:
  - targeted pytest suites passed (76 tests)
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-01): stage 801-812 API/runtime dedup + debt-signal cleanup.

- Advanced stage metadata:
  - `scripts/arch_metrics.py` (`ARCH_STAGE=812`)
  - `config/project/policy/manifests/architecture_metrics.json` (`arch_stage=812`)
- Reduced repetitive wrapper/import boilerplate in `src/tet4d/engine/api.py`
  across:
  - runtime menu/settings/config/schema helpers
  - keybinding menu helper dispatch
  - frontend/render adapter dispatch
- Reduced duplicated helper logic in `src/tet4d/ui/pygame/keybindings.py`
  (key-list parsing, key tuple filtering, conflict-apply branch flow, profile
  creation delegation).
- Consolidated duplicated action/route collection loops in
  `src/tet4d/engine/runtime/menu_structure_schema.py`.
- Reworded canonical `BKL-P2-027` title in `config/project/backlog_debt.json`
  to classify it as structural maintenance debt (not bug backlog semantics),
  aligning tech-debt bug-pressure input with actual bug-class issues.
- Verification:
  - targeted suites passed (`test_keybindings.py`, `test_menu_policy.py`,
    `test_front4d_render.py`, `test_front3d_setup.py`,
    `test_validate_project_contracts.py`)
  - `CODEX_MODE=1 ./scripts/verify.sh` passed
  - `python scripts/arch_metrics.py` passed with debt score decrease:
    `9.81 -> 7.04`.

Current sub-batch (2026-03-01): stage 791-800 governance + LOC cleanup.

- Advanced stage metadata:
  - `scripts/arch_metrics.py` (`ARCH_STAGE=800`)
  - `config/project/policy/manifests/architecture_metrics.json` (`arch_stage=800`)
- Closed traceability debt in active backlog source:
  - removed `BKL-P2-029` from `config/project/backlog_debt.json`
  - disambiguated duplicated backlog IDs in historical summaries using `-R2` rollover IDs.
- Added project-contract enforcement for backlog-ID uniqueness:
  - `tools/governance/validate_project_contracts.py`
  - `tests/unit/engine/test_validate_project_contracts.py`
- Reduced runtime/UI wrapper/parser duplication (no behavior change):
  - `src/tet4d/engine/runtime/menu_settings_state.py`
  - `src/tet4d/engine/runtime/menu_structure_schema.py`
  - `src/tet4d/ui/pygame/keybindings.py`
  - `src/tet4d/engine/api.py`
- Documentation dedup/cleanup:
  - moved legacy DONE summaries from this file to `docs/history/DONE_SUMMARIES.md`
  - converted this file to active/open + current-batch scope only.
- Verification:
  - targeted policy/menu/keybinding/front4d/project-contract test suites passed
  - `CODEX_MODE=1 ./scripts/verify.sh` passed
  - `python scripts/arch_metrics.py` passed.

## 6. Source Inputs

1. `config/project/backlog_debt.json`
2. `scripts/arch_metrics.py`
3. `config/project/policy/manifests/tech_debt_budgets.json`
4. `docs/rds/*.md`
5. `docs/ARCHITECTURE_CONTRACT.md`
6. `CURRENT_STATE.md`
7. `docs/history/DONE_SUMMARIES.md`
