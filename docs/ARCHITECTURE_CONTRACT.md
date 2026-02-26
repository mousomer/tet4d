# Architecture Contract (Incremental Refactor)

This document defines the target dependency boundaries for `tet4d` and the
incremental enforcement strategy used while refactoring.

## Goals

- Preserve gameplay behavior while improving maintainability.
- Establish stable module boundaries and dependency direction.
- Keep CI green during incremental refactors.

## Target Boundaries

### Engine (`tet4d.engine`)

- Pure game logic and deterministic state transitions.
- No `pygame` imports.
- No file I/O or runtime persistence side effects in core update paths.
- No imports from UI adapters or tooling.

### Engine Core (`tet4d.engine.core`)

- Strict-purity subtree for extracted deterministic logic slices.
- No `pygame`, `tet4d.ui`, tooling imports, file I/O, `time`, `logging`, or `print`.
- `random` usage is isolated to `tet4d.engine.core.rng` for injected RNG support.

### UI Adapter (`tet4d.ui.pygame` planned)

- Owns `pygame` event loop, rendering, audio playback, and input mapping.
- Depends on `tet4d.engine.api` only (target state).

### Replay (`tet4d.replay` planned)

- Replay schema and serialization/deserialization live outside engine core.
- Engine consumes replay data, not replay files.
- Stage 8 enforces `tet4d.replay` -> `tet4d.engine.api` only (no deep engine imports).

### AI / Playbot (`tet4d.ai`)

- Depends on `tet4d.engine.api` (and replay schema if needed).
- Must not depend on deep engine internals long-term.
- Stage 6 introduces `tet4d.ai.playbot` as the stable AI seam while playbot internals
  are still physically hosted under `tet4d.engine.playbot` during migration.

### Tools (`tools/*`)

- Governance, benchmarks, and stability tools should use stable public engine APIs.
- Stage 7 enforces `tet4d.engine.api`-only imports for stability/playbot benchmark tools.
- Renderer profiling tools may use `tet4d.ui.pygame` adapter seams while UI extraction remains in progress.

## Dependency Direction (Target)

- `ui` -> `engine.api`
- `ai` -> `engine.api`
- `tools` -> `engine.api`
- `replay` -> `engine.api`
- `engine` -> (no `ui`, no `tools`, no `pygame`)

## 2D / 3D / 4D Principle

- 2D/3D/4D modes are configuration and adapter concerns over shared engine logic.
- Mode-specific rendering and input handling belong in UI adapters.
- Shared rules (collision, scoring, topology, rotations) belong in engine core.

## Enforcement Strategy (Incremental)

- Stage 1 introduces a boundary check script and wires it into policy checks.
- Because `src/tet4d/engine/` is currently mixed (logic + `pygame` adapters),
  the initial checker uses a locked baseline for existing `pygame` imports and
  fails on new violations.
- Stage 8 also locks the current `src/tet4d/ui/` deep-engine import baseline while
  enforcing strict `engine -> replay` and `replay/ai/tools -> engine.api` rules.
- Stage 9 adds a strict `engine/core` purity gate and architecture metrics (`scripts/arch_metrics.py`)
  to track remaining deep imports and side-effect migration debt.
- Stage 10 (slice 1) makes `engine/core` self-contained with no imports back into non-core
  `tet4d.engine` modules and begins routing lock/clear/score application through core rules.
- Stage 11 (slice 2, 2D-first) moves the actual 2D tick/gravity reducer path into
  `engine/core/step` while keeping `game2d.py` as a compatibility delegator.
- Stage 12 (slice 3) moves the ND tick/gravity reducer path into `engine/core/step`,
  leaving `game_nd.py` as a compatibility delegator and eliminating reducer wrapper debt.
- Stage 13 (slice 4, 2D model/action seam) moves 2D `Action` and reducer-facing state
  protocols into `engine/core/model` and makes core 2D action dispatch independent of
  `game2d.py` private helpers.
- Stage 14 (slice 5, 2D collision/existence seam) routes the 2D gravity-step existence
  check through `engine/core/rules`, removing direct private-state helper calls from the
  core reducer path and shrinking reducer impurity debt.
- Stage 15 (slice 6, 2D mapped-cell adapter seam) moves the remaining reducer-rule
  dependency on private 2D state mapping helpers behind a public compatibility adapter,
  reducing `engine/core` private-helper debt in `core/rules`.
- Stage 16 (slice 7, 2D core-view types) introduces core-owned 2D config/state view
  dataclasses and API adapters, starting the migration of 2D state/config representations
  into `engine/core/model` without changing gameplay behavior.
- Stage 17 (slice 8, 2D gravity transition helper) moves the 2D gravity-tick mutation
  branch out of `engine/core/step/reducer.py` into `engine/core/rules`, reducing direct
  state-field mutation debt in the core reducer.
- Stage 18 (slice 9, ND core-view types) mirrors Stage 16 for ND by introducing
  core-owned ND config/state view dataclasses plus `game_nd.py`/`engine.api` adapters,
  covering both 3D and 4D runtime states through the shared ND path.
- Stage 19 (slice 10, UI adapter import cleanup) routes the existing `tet4d.ui.pygame`
  entry/profile adapters through `tet4d.engine.api` lazy wrappers so UI modules stop
  importing deep engine internals directly.
- Stage 20 (slice 11, AI/playbot package migration seam) converts `tet4d.ai.playbot`
  into an API-only package with planner/controller/type submodules and migrates external
  callers (tests/tools/CLI) off `tet4d.engine.playbot.*` imports.
- Stage 21 (slice 12, debt budget gate) adds a fail-on-regression architecture budget
  check (`scripts/check_architecture_metric_budgets.sh`) to lock current debt counts
  while deeper engine/UI/AI extractions continue.
- Stage 23 (slice 13, first pygame module extraction) moves display-mode pygame calls
  into `tet4d.ui.pygame.display`, leaving `tet4d.engine.display` as a compatibility shim
  so `pygame_imports_non_test` can start decreasing without gameplay changes.
- Stage 24 (slice 14, pygame font-profile extraction) moves font profile creation into
  `tet4d.ui.pygame.font_profiles`, leaving `tet4d.engine.font_profiles` as a
  compatibility shim and further reducing engine-level `pygame` imports.
- Stage 25 (slice 15, playbot internal module relocation start) moves
  `engine/playbot/lookahead_common.py` to `ai/playbot/lookahead_common.py` and leaves an
  engine compatibility shim, beginning physical playbot-internal relocation without
  introducing deep engine imports into `tet4d.ai`.
- Stage 26 (slice 16, pygame key-display extraction) moves key-name formatting helpers to
  `tet4d.ui.pygame.key_display`, leaving `tet4d.engine.key_display` as a compatibility shim
  and further reducing engine `pygame` imports without gameplay changes.
- Stage 27 (slice 17, pygame control-guide extraction) moves translation/rotation guide
  rendering to `tet4d.ui.pygame.menu_control_guides`, leaving `tet4d.engine.menu_control_guides`
  as a compatibility shim and continuing the low-risk pygame-helper extraction path.
- Stage 28 (slice 18, pygame keybinding-defaults extraction) moves default keybinding
  maps/profile helpers to `tet4d.ui.pygame.keybindings_defaults`, leaving
  `tet4d.engine.keybindings_defaults` as a lazy compatibility shim for existing imports.
- Stage 29 (slice 19, pygame loop-event helper extraction) moves shared pygame event-loop
  processing to `tet4d.ui.pygame.game_loop_common`, leaving `tet4d.engine.game_loop_common`
  as a compatibility shim to preserve current engine/front-end call sites during migration.
- Stage 30 (slice 20, pygame menu-model helper extraction) moves menu-loop state/index
  helpers to `tet4d.ui.pygame.menu_model`, leaving `tet4d.engine.menu_model` as a
  compatibility shim while preserving current frontend imports.
- Stage 31 (slice 21, pygame menu-runner extraction) moves the generic menu event-loop
  runner to `tet4d.ui.pygame.menu_runner`, leaving `tet4d.engine.menu_runner` as a lazy
  compatibility shim while reducing another engine `pygame` import.
- Stage 32 (slice 22, keybindings-menu input loop extraction) moves keybindings menu
  pygame event polling to `tet4d.ui.pygame.keybindings_menu_input`, leaving
  `tet4d.engine.keybindings_menu_input` as a compatibility shim and keeping UI imports
  free of deep engine dependencies.
- Stage 33 (slice 23, redundant facade cleanup) removes trivial `engine -> core`
  re-export shims (`board.py`, `rng.py`, `types.py`) and the stale
  `engine/playbot/lookahead_common.py` shim while retaining `engine -> ui` compatibility
  adapters that still enforce the current architecture boundary.
- Stage 34 (slice 24, AI facade pruning) removes redundant `tet4d.ai.playbot`
  planner/controller/type wrapper modules and routes callers directly to
  `tet4d.engine.api`, leaving only the shared `ai/playbot/lookahead_common.py`
  implementation module in the `tet4d.ai.playbot` package.
- Stage 35 (slice 25, merged-folder sequence start) formalizes a minimal-change
  engine folder split strategy using merged responsibility buckets (`gameplay`,
  `ui_logic`, `runtime`) instead of many tiny folders, and moves low-risk
  menu/input helpers into `engine/ui_logic` with engine-path compatibility shims.
- Stage 36 (slice 26, `ui_logic` cluster expansion) moves menu interaction and
  keybindings-menu model helpers into `engine/ui_logic`, keeping engine-path
  compatibility shims while redirecting moved modules toward merged-folder imports.
- Stage 37 (slice 27, menu graph logic consolidation) moves the menu graph linter
  module into `engine/ui_logic` and keeps a compatibility shim at the legacy
  engine path so governance tooling can migrate without churn.
- Stage 38 (slice 28, keybindings catalog consolidation) moves the keybinding
  action catalog into `engine/ui_logic` and updates `ui_logic` callers to import
  the shared catalog from the same merged folder.
- Stage 39 (slice 29, runtime cluster start) creates `engine/runtime` and moves
  menu settings/config persistence modules behind engine-path compatibility shims,
  while `ui_logic` callers start using `engine.runtime.*` imports directly.
- Stage 40 (slice 30, runtime config cluster move) expands `engine/runtime` with
  project/runtime config and validation modules, preserving legacy engine import
  paths via module-alias shims for minimal churn.
- Stage 41 (slice 31, runtime analytics cluster move) moves score analyzer modules
  into `engine/runtime`, keeping engine-path module-alias shims so HUD, gameplay,
  and tests continue to resolve imports without behavior change.
- Stage 42 (slice 32, gameplay cluster start) creates `engine/gameplay` and moves
  low-coupling gameplay helpers (`challenge_mode`, `speed_curve`,
  `exploration_mode`) behind engine-path module-alias shims.
- Stage 43 (slice 33, gameplay primitives move) moves `pieces2d`, `pieces_nd`,
  and `topology` into `engine/gameplay`, with engine-path module-alias shims and
  local gameplay-cluster imports for moved primitives.
- Stage 44 (slice 34, game module prep seam) updates `game2d.py` and `game_nd.py`
  to import moved gameplay/runtime modules from their new cluster paths directly,
  reducing future shim-pruning churn before moving the main game modules.
- Stage 45 (slice 35, shim pruning checkpoint) removes unused compatibility shims
  from Stages 36-41 (including runtime validation leaf shims and unused UI-logic
  shims) and migrates the last runtime-helper callers to `engine.runtime.*`,
  keeping net LOC decreasing while documenting folder-ratio progress.
- Stage 46 (slice 36, runtime analytics completion) moves `assist_scoring.py`
  into `engine/runtime` alongside score-analyzer modules and keeps an engine-path
  module-alias shim for callers and tests during the transition.
- Stage 47 (slice 37, gameplay support move) moves `topology_designer.py` into
  `engine/gameplay`, updating it to depend on `engine.runtime.project_config` and
  local gameplay `topology`, with an engine-path module-alias shim for callers.
- Stage 48 (slice 38, game-module move prep) introduces temporary
  `engine.gameplay.game2d` / `engine.gameplay.game_nd` alias modules and migrates
  selected internal callers to those paths so the upcoming physical game-module
  moves are mostly file relocations plus import retargeting.
- Stage 49 (slice 39, high-risk gameplay move) performs the physical move of
  `game2d.py` into `engine/gameplay`, keeping the old path as a module-alias shim
  so tests/callers retain existing import and monkeypatch behavior.
- Stage 50 (slice 40, high-risk gameplay move) applies the same physical-move +
  module-alias-shim pattern to `game_nd.py`, so 3D/4D runtime paths migrate to
  `engine/gameplay` without breaking existing imports during the transition.
- Stage 51 (slice 41, shim-prune checkpoint) migrates engine-internal callers to
  `engine.gameplay.game2d/game_nd` and intentionally retains `engine.game2d` /
  `engine.game_nd` shims for tests and external-facing compatibility until a later
  prune stage can remove them with lower risk.
- Stage 52 (slice 42, compatibility reduction) migrates engine test imports to the
  canonical `engine.gameplay.game2d/game_nd` paths, shrinking the remaining caller
  set of the legacy `engine.game2d` / `engine.game_nd` shims before removal.
- Stage 53 (slice 43, shim-prune readiness audit) confirms there are no remaining
  repo callers importing `tet4d.engine.game2d` / `tet4d.engine.game_nd`, making
  the legacy game-module shims removable in the next stage.
- Stage 54 (slice 44, compatibility prune) deletes `engine.game2d` and
  `engine.game_nd` compatibility shims after the zero-caller audit, making
  `engine.gameplay.game2d/game_nd` the only in-repo game-module paths.
- Stage 55 (slice 45, runtime I/O extraction) moves `help_topics.py` into
  `engine/runtime`, keeping an engine-path module-alias shim so help-menu callers
  remain stable while reducing top-level engine file-I/O ownership.
- Stage 56 (slice 46, UI cache extraction) moves `text_render_cache.py` into
  `ui/pygame` and adds a small `engine.api` wrapper for `project_constant_int` so
  the moved UI module stays compliant with the `ui -> engine.api` boundary.
- Stage 57 (slice 47, UI helper extraction) moves `ui_utils.py` into `ui/pygame`
  using the same `engine.api.project_constant_int` seam, shrinking top-level
  engine pygame helpers while preserving existing engine-path imports via shim.
- Stage 58 (slice 48, UI projection extraction) moves `projection3d.py` into
  `ui/pygame`, keeping engine-path imports stable via module-alias shim and using
  `engine.api.project_constant_int` to preserve the `ui -> engine.api` boundary.
- Stage 59 (slice 49, UI icon extraction) moves `control_icons.py` into
  `ui/pygame`, replacing direct `project_config` access with a narrow
  `engine.api.project_root_path()` wrapper to keep UI modules off deep engine imports.
- Stage 60 (slice 50, UI control-helper extraction) moves `control_helper.py`
  into `ui/pygame` and uses narrow `engine.api` wrappers for key formatting and
  runtime binding groups so the moved UI helper avoids deep engine imports.
- Stage 61 (slice 51, UI panel helper extraction) moves `panel_utils.py` into
  `ui/pygame`, localizing panel/text/helper rendering utilities under the UI layer
  while preserving engine-path imports via a module-alias shim.
- Stage 62 (slice 52, UI camera input extraction) moves `camera_mouse.py` into
  `ui/pygame`, rebasing its dependency on `projection3d` locally and preserving
  engine imports for callers/tests with a module-alias shim.
- Stage 63 (slice 53, UI-logic clustering) moves `menu_layout.py` into
  `engine/ui_logic`, continuing the prefix-based consolidation of non-rendering
  menu/input logic while preserving engine-path imports via shim.
- Stage 64 (slice 54, UI-logic clustering) moves `key_dispatch.py` into
  `engine/ui_logic`, further reducing top-level engine input/menu utility clutter
  while preserving import compatibility through an engine-path module-alias shim.
- Stage 65 (slice 55, UI-logic canonicalization) migrates engine and CLI callers
  from engine-path compatibility shims to direct `engine/ui_logic/*` imports for
  dispatch, menu control, and keybinding/menu-model helpers before shim pruning.
- Stage 66 (slice 56, UI-logic canonicalization) migrates tools and tests to
  canonical `engine/ui_logic/*` imports so compatibility shims can be pruned
  without changing behavior or test placement.
- Stage 67 (slice 57, UI-logic shim pruning) removes zero-caller engine-path
  compatibility shims for migrated `ui_logic` modules after caller audits and
  canonical import rewrites across engine, CLI, tools, and tests.
- Stage 68 (slice 58, runtime canonicalization) migrates engine and CLI callers
  to canonical `engine/runtime/*` imports for analytics/help modules (`assist_scoring`,
  `help_topics`, `score_analyzer`) ahead of runtime shim pruning.
- Stage 69 (slice 59, runtime canonicalization) migrates tests to canonical
  `engine/runtime/*` imports while keeping tests in `src/tet4d/engine/tests/`,
  clearing remaining known callers to runtime compatibility shims.
- Stage 70 (slice 60, runtime shim pruning) removes zero-caller engine-path
  compatibility shims for `assist_scoring`, `help_topics`, and `score_analyzer`
  after engine/CLI/tests caller migration to canonical `engine/runtime/*` paths.
- Stage 71 (slice 61, UI shim canonicalization) migrates engine front-game
  callers to `tet4d.ui.pygame.camera_mouse` directly before test migration and
  shim pruning, keeping the change scoped to a single helper family.
- Stage 72 (slice 62, UI shim canonicalization) migrates `camera_mouse` tests to
  the canonical `tet4d.ui.pygame.camera_mouse` module while keeping tests in
  `src/tet4d/engine/tests/` prior to shim removal.
- Stage 73 (slice 63, UI shim pruning) removes the zero-caller
  `engine/camera_mouse.py` compatibility shim after engine+test migration to the
  canonical `tet4d.ui.pygame.camera_mouse` module.
- Stage 74 (slice 64, UI shim canonicalization) migrates engine render/help/menu
  callers to canonical `tet4d.ui.pygame.control_helper` and
  `tet4d.ui.pygame.control_icons` imports before test migration and shim pruning.
- Stage 75 (slice 65, UI shim canonicalization) migrates control-helper/icon
  tests to canonical `tet4d.ui.pygame.*` imports while preserving test placement
  prior to pruning the corresponding engine compatibility shims.
- Stage 76 (slice 66, UI shim pruning) removes the zero-caller
  `engine/control_helper.py` and `engine/control_icons.py` compatibility shims
  after engine+test migration to canonical `tet4d.ui.pygame.*` imports.
- Stage 77 (slice 67, UI shim canonicalization) migrates engine render/view
  callers to canonical `tet4d.ui.pygame.projection3d` imports before test
  migration and shim pruning for the `projection3d` helper family.
- Stage 78 (slice 68, UI shim canonicalization) migrates `projection3d` tests to
  the canonical `tet4d.ui.pygame.projection3d` module while preserving test
  placement before removing the engine-path compatibility shim.
- Stage 79 (slice 69, UI shim pruning) removes the zero-caller
  `engine/projection3d.py` compatibility shim after engine+test migration to the
  canonical `tet4d.ui.pygame.projection3d` module.
- Stage 80 (slice 70, UI shim canonicalization) migrates engine callers to
  canonical `tet4d.ui.pygame.ui_utils` imports before CLI caller migration and
  `engine/ui_utils.py` compatibility-shim pruning.
- Stage 81 (slice 71, UI shim canonicalization) migrates the remaining CLI
  caller (`cli/front.py`) to canonical `tet4d.ui.pygame.ui_utils` imports,
  clearing known non-UI callers before shim pruning.
- Stage 82 (slice 72, UI shim pruning) removes the zero-caller
  `engine/ui_utils.py` compatibility shim after engine and CLI migration to the
  canonical `tet4d.ui.pygame.ui_utils` module.
- Stage 83 (slice 73, runtime shim canonicalization) migrates engine callers to
  canonical `engine.runtime.menu_config` imports before CLI migration and
  `engine/menu_config.py` compatibility-shim pruning.
- Stage 84 (slice 74, runtime shim canonicalization) migrates remaining CLI
  callers to canonical `engine.runtime.menu_config` imports, clearing known
  non-runtime callers before `engine/menu_config.py` shim pruning.
- Stage 85 (slice 75, runtime shim pruning) removes the zero-caller
  `engine/menu_config.py` compatibility shim after engine and CLI migration to
  the canonical `engine.runtime.menu_config` module.
- Stage 86 (slice 76, runtime shim canonicalization) migrates engine callers to
  canonical `engine.runtime.project_config` imports before CLI/test migration
  and `engine/project_config.py` compatibility-shim pruning.
- Stage 87 (slice 77, runtime shim canonicalization) migrates remaining CLI and
  tests to canonical `engine.runtime.project_config` imports before pruning the
  `engine/project_config.py` compatibility shim.
- Stage 88 (slice 78, runtime shim pruning) removes the zero-caller
  `engine/project_config.py` compatibility shim after engine, CLI, and test
  migration to the canonical `engine.runtime.project_config` module.
- Stage 89 (slice 79, runtime shim canonicalization) migrates engine callers to
  canonical `engine.runtime.menu_settings_state` imports before CLI/test
  migration and `engine/menu_settings_state.py` shim pruning.
- Stage 90 (slice 80, runtime shim canonicalization) migrates remaining CLI/test
  callers to canonical `engine.runtime.menu_settings_state` imports before
  pruning the `engine/menu_settings_state.py` compatibility shim.
- Stage 91 (slice 81, runtime shim pruning) removes the zero-caller
  `engine/menu_settings_state.py` compatibility shim after engine, CLI, and test
  migration to the canonical `engine.runtime.menu_settings_state` module.
- Stage 92 (slice 82, runtime shim canonicalization) migrates engine and test
  callers to canonical `engine.runtime.runtime_config` imports before pruning
  the `engine/runtime_config.py` compatibility shim.
- Stage 93 (slice 83, runtime shim pruning) removes the zero-caller
  `engine/runtime_config.py` compatibility shim after engine and test migration
  to the canonical `engine.runtime.runtime_config` module.
- Stage 94 (slice 84, runtime shim canonicalization) migrates engine and CLI
  callers to canonical `engine.runtime.menu_persistence` imports before pruning
  the `engine/menu_persistence.py` compatibility shim.
- Stage 95 (slice 85, runtime shim pruning) removes the zero-caller
  `engine/menu_persistence.py` compatibility shim after canonical engine/CLI
  migration to `engine.runtime.menu_persistence`.
- Preferred foldering heuristic for future slices: target roughly `6-15` files per
  leaf folder, treat `>20` mixed-responsibility files as a split signal, and avoid
  creating new folders that would remain `<=3` files without a strong boundary reason.
- Future stages tighten this until `pygame` imports are fully removed from engine.
- Boundary guards use baseline-lock allowlists for transitional engine-owned UI
  modules (including current `engine -> tet4d.ui` imports) and fail on new
  additions outside the recorded baseline until those modules are extracted.
- Stage 96 (slice 86, ui shim canonicalization) migrates engine callers to
  canonical `tet4d.ui.pygame.font_profiles` imports before CLI migration and
  pruning the `engine/font_profiles.py` compatibility shim.
- Stage 97 (slice 87, ui shim canonicalization) migrates CLI callers to
  canonical `tet4d.ui.pygame.font_profiles` imports before pruning the
  `engine/font_profiles.py` compatibility shim.
- Stage 98 (slice 88, ui shim pruning) removes the zero-caller
  `engine/font_profiles.py` compatibility shim after engine/CLI migration to
  `tet4d.ui.pygame.font_profiles`.
- Stage 99 (slice 89, ui shim canonicalization) migrates engine callers to
  canonical `tet4d.ui.pygame.game_loop_common` imports before CLI migration and
  pruning the `engine/game_loop_common.py` compatibility shim.
- Stage 100 (slice 90, ui shim canonicalization) migrates CLI callers to
  canonical `tet4d.ui.pygame.game_loop_common` imports before pruning the
  `engine/game_loop_common.py` compatibility shim.
- Stage 101 (slice 91, ui shim pruning) removes the zero-caller
  `engine/game_loop_common.py` compatibility shim after engine/CLI migration to
  `tet4d.ui.pygame.game_loop_common`.
- Stage 102 (slice 92, ui shim canonicalization) migrates engine and CLI
  callers to canonical `tet4d.ui.pygame.menu_runner` imports before pruning the
  `engine/menu_runner.py` compatibility shim.
- Stage 103 (slice 93, ui shim pruning) removes the zero-caller
  `engine/menu_runner.py` compatibility shim after engine/CLI migration to
  `tet4d.ui.pygame.menu_runner`.
- Stage 104 (slice 94, ui shim canonicalization) migrates engine callers to
  canonical `tet4d.ui.pygame.panel_utils` and `tet4d.ui.pygame.text_render_cache`
  imports before pruning the `engine/panel_utils.py` and `engine/text_render_cache.py` shims.
- Stage 105 (slice 95, ui shim pruning) removes the zero-caller
  `engine/panel_utils.py` and `engine/text_render_cache.py` compatibility shims
  after canonical engine-caller migration.
- Stage 106 (slice 96, ui shim canonicalization) migrates engine callers to
  canonical `tet4d.ui.pygame.keybindings_defaults` imports before pruning the
  `engine/keybindings_defaults.py` compatibility shim.
- Stage 107 (slice 97, ui shim pruning) removes the zero-caller
  `engine/keybindings_defaults.py` compatibility shim after canonical engine
  migration to `tet4d.ui.pygame.keybindings_defaults`.
- Stage 108 (slice 98, ui shim canonicalization) migrates engine callers to
  canonical `tet4d.ui.pygame.keybindings_menu_input` imports before pruning the
  `engine/keybindings_menu_input.py` compatibility shim.
- Stage 109 (slice 99, ui shim pruning) removes the zero-caller
  `engine/keybindings_menu_input.py` compatibility shim after canonical engine
  migration to `tet4d.ui.pygame.keybindings_menu_input`.
- Stage 110 (slice 100, ui shim pruning) removes the zero-caller
  `engine/menu_model.py` compatibility shim after canonical UI-path migration.
- Stage 111 (slice 101, ui shim pruning) removes the zero-caller
  `engine/menu_control_guides.py` compatibility shim after canonical UI-path migration.
- Stage 112 (slice 102, ai relocation) physically moves `engine/playbot/types.py`
  to `ai/playbot/types.py` while keeping an engine compatibility shim.
- Stage 113 (slice 103, ai relocation canonicalization) migrates engine playbot
  and API callers to `ai/playbot/types.py` and removes the zero-caller
  `engine/playbot/types.py` compatibility shim.
- Stage 114 (slice 104, runtime side-effect extraction) routes topology-designer
  preset JSON reads through `engine.runtime.topology_designer_storage`.
- Stage 115 (slice 105, runtime side-effect extraction) routes topology-designer
  export JSON writes through `engine.runtime.topology_designer_storage`.
- Stage 116 (slice 106, gameplay shim canonicalization) migrates engine/CLI/test
  callers to canonical `engine.gameplay.challenge_mode` imports before pruning
  the top-level `engine/challenge_mode.py` compatibility shim.
- Stage 117 (slice 107, gameplay shim pruning) removes the zero-caller
  `engine/challenge_mode.py` compatibility shim after canonical
  `engine.gameplay.challenge_mode` migration.
- Stage 118 (slice 108, gameplay shim canonicalization) migrates engine/CLI
  callers to canonical `engine.gameplay.exploration_mode` imports before
  pruning `engine/exploration_mode.py`.
- Stage 119 (slice 109, gameplay shim pruning) removes the zero-caller
  `engine/exploration_mode.py` compatibility shim after canonical
  `engine.gameplay.exploration_mode` migration.
- Stage 120 (slice 110, gameplay shim canonicalization) migrates engine/test
  callers to canonical `engine.gameplay.speed_curve` imports before pruning
  `engine/speed_curve.py`.
- Stage 121 (slice 111, gameplay shim pruning) removes the zero-caller
  `engine/speed_curve.py` compatibility shim after canonical
  `engine.gameplay.speed_curve` migration.
- Stage 122 (slice 112, gameplay shim canonicalization) migrates engine/CLI/test
  callers to canonical `engine.gameplay.topology_designer` imports before
  pruning `engine/topology_designer.py`.
- Stage 123 (slice 113, gameplay shim pruning) removes the zero-caller
  `engine/topology_designer.py` compatibility shim after canonical
  `engine.gameplay.topology_designer` migration.
- Stage 124 (slice 114, gameplay shim canonicalization) migrates engine/CLI/test
  callers to canonical `engine.gameplay.topology` imports before pruning
  `engine/topology.py`.
- Stage 125 (slice 115, gameplay shim pruning) removes the zero-caller
  `engine/topology.py` compatibility shim after canonical
  `engine.gameplay.topology` migration.
- Stage 126 (slice 116, gameplay shim canonicalization) migrates engine/CLI/test
  callers to canonical `engine.gameplay.pieces2d` imports before pruning
  `engine/pieces2d.py`.
- Stage 127 (slice 117, gameplay shim pruning) removes the zero-caller
  `engine/pieces2d.py` compatibility shim after canonical
  `engine.gameplay.pieces2d` migration.
- Stage 128 (slice 118, gameplay shim canonicalization) migrates engine/test
  callers to canonical `engine.gameplay.pieces_nd` imports before pruning
  `engine/pieces_nd.py`.
- Stage 129 (slice 119, gameplay shim pruning) removes the zero-caller
  `engine/pieces_nd.py` compatibility shim after canonical
  `engine.gameplay.pieces_nd` migration.
- Stage 130 (slice 120, runtime side-effect extraction) routes keybindings JSON
  file reads through `engine.runtime.keybindings_storage` before extracting
  write paths from `engine.ui_logic.keybindings`.
- Stage 131 (slice 121, runtime side-effect extraction) routes keybindings
  atomic-write persistence through `engine.runtime.keybindings_storage`.
- Stage 132 (slice 122, runtime side-effect extraction) routes keybindings
  profile-clone file copy persistence through
  `engine.runtime.keybindings_storage`.
- Stage 133 (slice 123, runtime side-effect extraction) routes help-topics JSON
  file reads through `engine.runtime.help_topics_storage`.
- Stage 134 (slice 124, runtime side-effect extraction) routes menu settings
  state JSON reads through `engine.runtime.menu_settings_state_storage`.
- Stage 135 (slice 125, runtime side-effect extraction) routes menu settings
  state atomic JSON writes through `engine.runtime.menu_settings_state_storage`.
- Stage 136 (slice 126, runtime side-effect extraction) routes menu-config JSON
  object reads through shared helper `engine.runtime.json_storage`.
- Stage 137 (slice 127, runtime side-effect extraction) routes project-config
  JSON object reads through shared helper `engine.runtime.json_storage`.
- Stage 138 (slice 128, runtime side-effect extraction) routes runtime-config
  validation JSON object reads through shared helper
  `engine.runtime.json_storage`.
- Stage 139 (slice 129, runtime side-effect extraction) routes topology-designer
  storage JSON object reads through shared helper `engine.runtime.json_storage`.
- Stage 140 (slice 130, runtime side-effect extraction) routes topology-designer
  storage JSON writes through shared helper `engine.runtime.json_storage`.
- Stage 141 (slice 131, runtime side-effect extraction) routes help-topics
  storage JSON reads through shared helper `engine.runtime.json_storage`.
- Stage 142 (slice 132, runtime side-effect extraction) routes menu-settings
  state storage JSON reads and atomic writes through shared helper
  `engine.runtime.json_storage`.
- Stage 143 (slice 133, runtime side-effect extraction) routes keybindings
  storage JSON reads through shared helper `engine.runtime.json_storage`.
- Stage 144 (slice 134, runtime side-effect extraction) routes score-analyzer
  config/summary JSON reads through `engine.runtime.score_analyzer_storage`.
- Stage 145 (slice 135, runtime side-effect extraction) routes score-analyzer
  summary writes and event-log appends through
  `engine.runtime.score_analyzer_storage`.
- Stage 146 (slice 136, sequential cleanup) moved `src/tet4d/engine/rotation_anim.py` implementation into `src/tet4d/engine/gameplay/rotation_anim.py` and retained an engine compatibility shim pending caller migration.
- Stage 147 (slice 137, sequential cleanup) migrated engine and CLI callers to canonical `src/tet4d/engine/gameplay/rotation_anim.py` imports before shim pruning.
- Stage 148 (slice 138, sequential cleanup) migrated tests to canonical `src/tet4d/engine/gameplay/rotation_anim.py` imports before shim pruning.
- Stage 149 (slice 139, sequential cleanup) removed the zero-caller `src/tet4d/engine/rotation_anim.py` compatibility shim after canonical gameplay import migration.
- Stage 150 (slice 140, sequential cleanup) migrated engine callers to canonical `src/tet4d/ui/pygame/display.py` imports before shim pruning.
- Stage 151 (slice 141, sequential cleanup) migrated CLI and tests to canonical `src/tet4d/ui/pygame/display.py` imports before shim pruning.
- Stage 152 (slice 142, sequential cleanup) removed the zero-caller `src/tet4d/engine/display.py` compatibility shim after canonical UI display import migration.
- Stage 153 (slice 143, sequential cleanup) migrated engine callers to canonical `src/tet4d/ui/pygame/key_display.py` imports before shim pruning.
- Stage 154 (slice 144, sequential cleanup) migrated `engine.api` helper usage to canonical `src/tet4d/ui/pygame/key_display.py` before shim pruning.
- Stage 155 (slice 145, sequential cleanup) removed the zero-caller `src/tet4d/engine/key_display.py` compatibility shim after canonical UI key-display import migration.
- Stage 156 (slice 146, sequential cleanup) added `engine.api` dry-run support wrappers for challenge prefills and runtime defaults to prepare `playbot.dry_run` relocation.
- Stage 157 (slice 147, sequential cleanup) moved `src/tet4d/engine/playbot/dry_run.py` to `src/tet4d/ai/playbot/dry_run.py` and retained an engine compatibility shim using only `tet4d.engine.api` in the moved module.
- Stage 158 (slice 148, sequential cleanup) migrated `engine.api` dry-run wrappers to canonical `src/tet4d/ai/playbot/dry_run.py` imports before shim pruning.
- Stage 159 (slice 149, sequential cleanup) expanded `src/tet4d/ai/playbot/__init__.py` lazy exports for dry-run APIs to strengthen the canonical AI package surface before shim pruning.
- Stage 160 (slice 150, sequential cleanup) removed the zero-caller `src/tet4d/engine/playbot/dry_run.py` compatibility shim after canonical AI dry-run import migration.
- Stage 161 (slice 151, sequential cleanup) moved `src/tet4d/engine/view_controls.py`
  implementation into `src/tet4d/ui/pygame/view_controls.py` and retained an
  engine compatibility shim pending caller migration.
- Stage 162 (slice 152, sequential cleanup) migrated tests to canonical
  `src/tet4d/ui/pygame/view_controls.py` imports before shim pruning.
- Stage 163 (slice 153, sequential cleanup) migrated engine render/input callers
  to canonical `src/tet4d/ui/pygame/view_controls.py` imports before shim
  pruning.
- Stage 164 (slice 154, sequential cleanup) removed the zero-caller
  `src/tet4d/engine/view_controls.py` compatibility shim after canonical UI
  `view_controls` import migration.
- Stage 165 (slice 155, sequential cleanup) moved `src/tet4d/engine/view_modes.py`
  implementation into `src/tet4d/engine/ui_logic/view_modes.py` and retained an
  engine compatibility shim pending caller migration.
- Stage 166 (slice 156, sequential cleanup) migrated engine, CLI, and
  `engine.api` callers to canonical `src/tet4d/engine/ui_logic/view_modes.py`
  imports before shim pruning.
- Stage 167 (slice 157, sequential cleanup) migrated tests to canonical
  `src/tet4d/engine/ui_logic/view_modes.py` imports before shim pruning.
- Stage 168 (slice 158, sequential cleanup) migrated runtime callers to
  canonical `src/tet4d/engine/ui_logic/view_modes.py` imports before shim
  pruning.
- Stage 169 (slice 159, sequential cleanup) removed the zero-caller
  `src/tet4d/engine/view_modes.py` compatibility shim after canonical
  `engine.ui_logic.view_modes` import migration.
- Stage 170 (slice 160, sequential cleanup) exported `GridMode` from
  `src/tet4d/engine/api.py` to prepare `grid_mode_render` UI relocation without
  introducing `ui -> engine` deep imports.
- Stage 171 (slice 161, sequential cleanup) moved
  `src/tet4d/engine/grid_mode_render.py` implementation into
  `src/tet4d/ui/pygame/grid_mode_render.py` and retained an engine
  compatibility shim pending caller migration.
- Stage 172 (slice 162, sequential cleanup) migrated engine render callers to
  canonical `src/tet4d/ui/pygame/grid_mode_render.py` imports before shim
  pruning.
- Stage 173 (slice 163, sequential cleanup) removed the zero-caller
  `src/tet4d/engine/grid_mode_render.py` compatibility shim after canonical UI
  grid-mode renderer import migration.
- Stage 174 (slice 164, sequential cleanup) added `engine.api` wrappers for ND
  launcher display-open/capture helpers to prepare `launcher_nd_runner` UI
  relocation without deep UI imports into engine internals.
- Stage 175 (slice 165, sequential cleanup) moved
  `src/tet4d/engine/launcher_nd_runner.py` implementation into
  `src/tet4d/ui/pygame/launcher_nd_runner.py` and retained an engine
  compatibility shim pending caller migration.
- Stage 176 (slice 166, sequential cleanup) migrated engine callers to
  canonical `src/tet4d/ui/pygame/launcher_nd_runner.py` imports before shim
  pruning.
- Stage 177 (slice 167, sequential cleanup) removed the zero-caller
  `src/tet4d/engine/launcher_nd_runner.py` compatibility shim after canonical
  UI launcher import migration.
- Stage 178 (slice 168, sequential cleanup) added `engine.api` wrappers for
  shared ND setup/menu functions and settings type access to prepare
  `front3d_setup` UI relocation without deep UI imports into engine internals.
- Stage 179 (slice 169, sequential cleanup) moved `src/tet4d/engine/front3d_setup.py`
  implementation into `src/tet4d/ui/pygame/front3d_setup.py`, migrated
  engine/test callers to the canonical UI import path, and retained an engine
  compatibility shim pending final prune.
- Stage 180 (slice 170, sequential cleanup) removed the zero-caller
  `src/tet4d/engine/front3d_setup.py` compatibility shim after canonical UI
  `front3d_setup` import migration.
- Stage 181 (slice 171, keybindings menu UI prep) adds lazy `engine.api` wrappers for keybindings and keybindings-menu-model operations to prepare UI relocation without `ui -> engine` deep imports.
- Stage 182 (slice 172, keybindings menu UI relocation) moves `src/tet4d/engine/keybindings_menu_view.py` implementation into `src/tet4d/ui/pygame/keybindings_menu_view.py` and retains a temporary engine compatibility shim.
- Stage 183 (slice 173, keybindings menu UI canonicalization) migrates `keybindings_menu` to import `tet4d.ui.pygame.keybindings_menu_view` before shim pruning.
- Stage 184 (slice 174, keybindings menu UI shim pruning) removes the zero-caller `src/tet4d/engine/keybindings_menu_view.py` compatibility shim.
- Stage 185 (slice 175, keybindings menu UI relocation) moves `src/tet4d/engine/keybindings_menu.py` implementation into `src/tet4d/ui/pygame/keybindings_menu.py` and rewires it through `tet4d.engine.api` wrappers, retaining a temporary engine compatibility shim.
- Stage 186 (slice 176, keybindings menu UI canonicalization) migrates `src/tet4d/engine/pause_menu.py` to canonical `tet4d.ui.pygame.keybindings_menu` imports.
- Stage 187 (slice 177, keybindings menu UI canonicalization) migrates CLI keybindings-menu callers to canonical `tet4d.ui.pygame.keybindings_menu` imports.
- Stage 188 (slice 178, keybindings menu UI shim pruning) removes the zero-caller `src/tet4d/engine/keybindings_menu.py` compatibility shim.
- Stage 189 (slice 179, architecture checkpoint) records the keybindings-menu UI family migration and shim pruning sequence in RDS/contract tracking artifacts.
- Stage 190 (slice 180, validation checkpoint) advances `arch_stage` to `190` after full verification/CI gate confirmation for the batch.
- Stage 191 (slice 181, audio UI prep) adds lazy `engine.api` wrapper `audio_event_specs_runtime()` so audio UI code can consume runtime audio config without `ui -> engine.runtime` deep imports.
- Stage 192 (slice 182, audio UI relocation) moves `src/tet4d/engine/audio.py` implementation into `src/tet4d/ui/pygame/audio.py`, rewires it through `tet4d.engine.api`, and retains a temporary engine compatibility shim.
- Stage 193 (slice 183, audio UI canonicalization) migrates engine callers (`app_runtime`, front games, launcher/settings, pause/bot-options menus) to canonical `tet4d.ui.pygame.audio` imports.
- Stage 194 (slice 184, audio UI canonicalization) migrates CLI and test callers to canonical `tet4d.ui.pygame.audio` imports before shim pruning.
- Stage 195 (slice 185, audio UI shim pruning) removes the zero-caller `src/tet4d/engine/audio.py` compatibility shim and baseline-locks `src/tet4d/ui/pygame/audio.py` in architecture boundaries.
- Stage 196 (slice 186, bot-options UI prep) adds lazy `engine.api` wrappers for runtime menu row/default/payload helpers so the bot-options menu UI can avoid deep runtime imports.
- Stage 197 (slice 187, bot-options UI relocation) moves `src/tet4d/engine/bot_options_menu.py` implementation into `src/tet4d/ui/pygame/bot_options_menu.py`, routes runtime access through `tet4d.engine.api`, and retains a temporary engine compatibility shim.
- Stage 198 (slice 188, bot-options UI canonicalization) migrates `pause_menu.py` to canonical `tet4d.ui.pygame.bot_options_menu` imports before shim pruning.
- Stage 199 (slice 189, bot-options UI canonicalization) migrates CLI bot-options-menu callers to canonical `tet4d.ui.pygame.bot_options_menu` imports before shim pruning.
- Stage 200 (slice 190, bot-options UI shim pruning/checkpoint) removes the zero-caller `src/tet4d/engine/bot_options_menu.py` compatibility shim, baseline-locks `src/tet4d/ui/pygame/bot_options_menu.py`, and advances `arch_stage` to `200` after full verification/CI checkpoint.
- Stage 201 (slice 191, loop-runner UI prep) adds lazy `engine.api` wrappers for runtime gravity and animation helper functions so ND loop orchestration can move to UI without `ui -> engine.runtime` deep imports.
- Stage 202 (slice 192, loop-runner UI relocation) moves `src/tet4d/engine/loop_runner_nd.py` implementation into `src/tet4d/ui/pygame/loop_runner_nd.py`, rewires runtime helper calls through `tet4d.engine.api`, and retains an engine compatibility shim.
- Stage 203 (slice 193, loop-runner UI canonicalization) migrates `front3d_game.py` and `front4d_game.py` to canonical `tet4d.ui.pygame.loop_runner_nd` imports.
- Stage 204 (slice 194, loop-runner UI zero-caller audit checkpoint) records zero remaining imports of `src/tet4d/engine/loop_runner_nd.py` before shim pruning and advances `arch_stage` to `204`.
- Stage 205 (slice 195, loop-runner UI shim pruning/checkpoint) removes the zero-caller `src/tet4d/engine/loop_runner_nd.py` compatibility shim and advances `arch_stage` to `205` after full verification/CI checkpoint.
- Stage 206 (slice 196, app-runtime UI prep) adds lazy `engine.api` wrappers for keybindings initialization, runtime settings payload access/save, and score-analyzer logging toggles so app runtime can move to UI without `ui -> engine.runtime` deep imports.
- Stage 207 (slice 197, app-runtime UI relocation) moves `src/tet4d/engine/app_runtime.py` implementation into `src/tet4d/ui/pygame/app_runtime.py`, rewires runtime/keybindings interactions through `tet4d.engine.api`, retains an engine compatibility shim, and baseline-locks the new UI adapter path.
- Stage 208 (slice 198, app-runtime UI canonicalization) migrates engine callers (`front3d_game`, `front4d_game`, `launcher_play`, `launcher_settings`) to canonical `tet4d.ui.pygame.app_runtime` imports.
- Stage 209 (slice 199, app-runtime UI canonicalization) migrates CLI callers and `engine.api` lazy display wrappers to canonical `tet4d.ui.pygame.app_runtime` imports before shim pruning.
- Stage 210 (slice 200, app-runtime UI shim pruning/checkpoint) removes the zero-caller `src/tet4d/engine/app_runtime.py` compatibility shim and advances `arch_stage` to `210` after full verification/CI checkpoint.
- Stage 211 (slice 201, launcher-settings UI prep) adds lazy `engine.api` wrappers for menu-config layout/default payload helpers, menu-persistence save/load functions, settings-state defaults, and score-analyzer logging toggles to prepare launcher-settings UI relocation without deep `ui -> engine.runtime` imports.
- Stage 212 (slice 202, launcher-settings UI relocation) moves `src/tet4d/engine/launcher_settings.py` implementation into `src/tet4d/ui/pygame/launcher_settings.py`, rewires runtime/config/persistence access through `tet4d.engine.api`, retains an engine compatibility shim, and baseline-locks the new UI adapter path.
- Stage 213 (slice 203, launcher-settings UI canonicalization) migrates `pause_menu.py` to canonical `tet4d.ui.pygame.launcher_settings` imports before shim pruning.
- Stage 214 (slice 204, launcher-settings UI canonicalization) migrates CLI and test callers to canonical `tet4d.ui.pygame.launcher_settings` imports before shim pruning.
- Stage 215 (slice 205, launcher-settings UI shim pruning/checkpoint) removes the zero-caller `src/tet4d/engine/launcher_settings.py` compatibility shim and advances `arch_stage` to `215` after full verification/CI checkpoint.
- Stage 216 (slice 206, launcher-play UI prep) adds lazy `engine.api` wrappers for `front3d_game`, `front4d_game`, and `frontend_nd` launch/menu/build/sizing functions so launcher-play can move to UI without `ui -> engine` deep imports.
- Stage 217 (slice 207, launcher-play UI relocation) moves `src/tet4d/engine/launcher_play.py` implementation into `src/tet4d/ui/pygame/launcher_play.py`, rewires engine-side launch dependencies through `tet4d.engine.api`, retains an engine compatibility shim, and baseline-locks the new UI adapter path.
- Stage 218 (slice 208, launcher-play UI canonicalization) migrates CLI launcher imports to canonical `tet4d.ui.pygame.launcher_play` before shim pruning.
- Stage 219 (slice 209, launcher-play UI zero-caller audit checkpoint) records zero remaining imports of `src/tet4d/engine/launcher_play.py` before shim pruning and advances `arch_stage` to `219`.
- Stage 220 (slice 210, launcher-play UI shim pruning/checkpoint) removes the zero-caller `src/tet4d/engine/launcher_play.py` compatibility shim and advances `arch_stage` to `220` after full verification/CI checkpoint.
- Stage 221 (slice 211, gfx-panel UI prep) adds lazy `engine.api` wrappers for score-analyzer HUD lines and grid-mode labels so the 2D side-panel renderer can move to UI without deep `ui -> engine.runtime/ui_logic` imports.
- Stage 222 (slice 212, gfx-panel UI relocation) moves `src/tet4d/engine/gfx_panel_2d.py` implementation into `src/tet4d/ui/pygame/gfx_panel_2d.py`, rewires runtime/ui_logic lookups through `tet4d.engine.api`, retains an engine compatibility shim, and baseline-locks the new UI adapter path.
- Stage 223 (slice 213, gfx-panel UI canonicalization) migrates `src/tet4d/engine/gfx_game.py` to canonical `tet4d.ui.pygame.gfx_panel_2d` imports before shim pruning.
- Stage 224 (slice 214, gfx-panel UI zero-caller audit checkpoint) records zero remaining imports of `src/tet4d/engine/gfx_panel_2d.py` before shim pruning and advances `arch_stage` to `224`.
- Stage 225 (slice 215, gfx-panel UI shim pruning/checkpoint) removes the zero-caller `src/tet4d/engine/gfx_panel_2d.py` compatibility shim and advances `arch_stage` to `225` after full verification/CI checkpoint.
- Stage 229 (slice 219, gfx-game UI zero-caller audit checkpoint) records zero remaining imports of `src/tet4d/engine/gfx_game.py` after CLI canonicalization and advances `arch_stage` to `229` before shim pruning.
- Stage 230 (slice 220, gfx-game UI shim pruning/checkpoint) removes the zero-caller `src/tet4d/engine/gfx_game.py` compatibility shim and advances `arch_stage` to `230` after full verification/CI checkpoint.
- Stage 234 (slice 224, help-menu UI zero-caller audit checkpoint) records zero remaining imports of `src/tet4d/engine/help_menu.py` after engine/CLI/test canonicalization and advances `arch_stage` to `234` before shim pruning.
- Stage 235 (slice 225, help-menu UI shim pruning/checkpoint) removes the zero-caller `src/tet4d/engine/help_menu.py` compatibility shim and advances `arch_stage` to `235` after full verification/CI checkpoint.
- Stage 239 (slice 229, pause-menu UI zero-caller audit checkpoint) records zero remaining imports of `src/tet4d/engine/pause_menu.py` after engine/CLI/test canonicalization and advances `arch_stage` to `239` before shim pruning.
- Stage 240 (slice 230, pause-menu UI shim pruning/checkpoint) removes the zero-caller `src/tet4d/engine/pause_menu.py` compatibility shim and advances `arch_stage` to `240` after full verification/CI checkpoint.
- Stage 247 (slice 237, keybindings ui-logic zero-caller audit checkpoint) records zero remaining imports of `src/tet4d/engine/keybindings.py` after engine/API/CLI/test canonicalization and advances `arch_stage` to `247` before shim pruning.
- Stage 248 (slice 238, keybindings ui-logic shim pruning/checkpoint) removes the zero-caller `src/tet4d/engine/keybindings.py` compatibility shim and advances `arch_stage` to `248` after full verification/CI checkpoint.
- Stage 249 (slice 239, keybindings post-prune docs sync) updates historical architecture notes to reference `engine.ui_logic.keybindings` as the canonical keybindings implementation path after shim removal and advances `arch_stage` to `249`.
- Stage 250 (slice 240, keybindings batch checkpoint) records the completed Stage 241-249 keybindings ui-logic migration/prune sequence, advances `arch_stage` to `250`, and verifies the checkpoint with full local `verify.sh` + `ci_check.sh`.
- Stage 251 (slice 241, playbot-controller API prep) makes `tet4d.engine.api.PlayBotController` a lazy export to avoid future controller relocation import cycles and adds controller-facing playbot ND helper wrappers/exports for the next migration stages, advancing `arch_stage` to `251`.
- Stage 252 (slice 242, playbot package lazy export prep) makes `tet4d.engine.playbot.PlayBotController` a lazy export through `engine.playbot.__getattr__` so `engine/playbot/controller.py` can move to `ai/playbot` without creating an `engine.api` import cycle.
- Stage 253 (slice 243, playbot controller physical relocation) moves `engine/playbot/controller.py` to `ai/playbot/controller.py`, keeps an engine-path module-alias shim, and rewires controller imports to use `tet4d.engine.api` wrappers so the AI boundary remains API-only.
- Stage 254 (slice 244, playbot package canonicalization) updates `engine.playbot.PlayBotController` lazy resolution to import directly from `ai.playbot.controller`, making `engine.playbot/controller.py` a removable compatibility shim in the next stages.
- Stage 255 (slice 245, playbot controller caller canonicalization) migrates `front3d_game.py` and `front4d_game.py` to import `PlayBotController` from `engine.api`, reducing engine-internal dependence on the transitional `engine.playbot` compatibility package.
- Stage 256 (slice 246, playbot controller zero-caller checkpoint) records zero remaining direct callers of `engine/playbot/controller.py` after engine package/caller canonicalization and advances `arch_stage` to `256` before shim pruning.
- Stage 257 (slice 247, playbot controller shim pruning) removes the zero-caller `engine/playbot/controller.py` compatibility shim after the controller relocation to `ai/playbot/controller.py` and caller canonicalization.
- Stage 258 (slice 248, playbot package canonical export polish) adds `PlayBotController` as a lazy export from `ai.playbot.__init__`, making the canonical AI package path self-describing after controller shim pruning.
- Stage 259 (slice 249, playbot controller family checkpoint) records completion of the Stage 251-258 `PlayBotController` API-prep/move/prune sequence and advances `arch_stage` to `259` before the full batch verification checkpoint.
- Stage 260 (slice 250, playbot controller batch verification checkpoint) advances `arch_stage` to `260` and verifies the Stage 251-259 playbot-controller batch with full local `verify.sh` + `ci_check.sh`.
- Stage 261 (slice 251, planner2d API prep types) exports `ActivePiece2D` and `PieceShape2D` from `engine.api` so the upcoming `playbot/planner_2d.py` move can avoid direct gameplay module imports while keeping the AI boundary API-only.
- Stage 262 (slice 252, planner2d API prep rotation helper) exports `rotate_point_2d` from `engine.api` so `planner_2d` can complete its move to `ai/playbot` without importing `gameplay.pieces2d` directly.
- Stage 263 (slice 253, planner2d physical relocation) moves `engine/playbot/planner_2d.py` to `ai/playbot/planner_2d.py`, keeps an engine-path module-alias shim, and rewires the planner implementation to use `tet4d.engine.api` exports so the AI boundary remains API-only.
- Stage 264 (slice 254, planner2d engine-api canonicalization) updates `engine.api.plan_best_2d_move` to import from `ai.playbot.planner_2d` directly, reducing reliance on the transitional `engine.playbot/planner_2d.py` compatibility shim.
- Stage 265 (slice 255, planner2d AI package export polish) adds `plan_best_2d_move` as a lazy export from `ai.playbot.__init__`, improving canonical AI package discoverability after the planner relocation.
- Stage 266 (slice 256, planner2d zero-caller checkpoint) records zero remaining callers of `engine/playbot/planner_2d.py` after engine-api and package canonicalization and advances `arch_stage` to `266` before shim pruning.
- Stage 267 (slice 257, planner2d shim pruning) removes the zero-caller `engine/playbot/planner_2d.py` compatibility shim after the planner relocation to `ai/playbot/planner_2d.py` and canonicalization.
- Stage 268 (slice 258, planner2d post-prune docs sync) records the canonical `ai/playbot/planner_2d.py` path after shim removal and advances `arch_stage` to `268`.
- Stage 269 (slice 259, planner2d family checkpoint) records completion of the Stage 261-268 planner2d API-prep/move/prune sequence and advances `arch_stage` to `269` before the full batch verification checkpoint.
- Stage 270 (slice 260, planner2d batch verification checkpoint) advances `arch_stage` to `270` and verifies the Stage 261-269 planner2d batch with full local `verify.sh` + `ci_check.sh`.
- Stage 271 (slice 261, plannerND API prep search wrapper) adds `engine.api.plan_best_nd_with_budget(...)` so `planner_nd` can move to `ai/playbot` while remaining API-only at the AI boundary.
- Stage 272 (slice 262, plannerND physical relocation) moves `engine/playbot/planner_nd.py` to `ai/playbot/planner_nd.py`, keeps an engine-path module-alias shim, and rewires planner imports to `tet4d.engine.api` wrappers so the AI boundary remains API-only.
- Stage 273 (slice 263, plannerND engine-api canonicalization) updates `engine.api.plan_best_nd_move(...)` to import from `ai.playbot.planner_nd` directly, reducing reliance on the transitional `engine/playbot/planner_nd.py` shim.
- Stage 274 (slice 264, plannerND AI package export polish) adds `plan_best_nd_move` as a lazy export from `ai.playbot.__init__`, improving canonical AI package discoverability after the planner relocation.
- Stage 275 (slice 265, plannerND zero-caller checkpoint) records zero remaining callers of `engine/playbot/planner_nd.py` after engine-api and AI-package canonicalization and advances `arch_stage` to `275` before shim pruning.
- Stage 276 (slice 266, plannerND shim pruning) removes the zero-caller `engine/playbot/planner_nd.py` compatibility shim after the planner relocation to `ai/playbot/planner_nd.py` and canonicalization.
- Stage 277 (slice 267, plannerND family verification checkpoint) records completion of the Stage 271-276 plannerND API-prep/move/prune sequence, advances `arch_stage` to `277`, and verifies the checkpoint with full local `verify.sh` + `ci_check.sh`.
- Stage 278 (slice 268, plannerND-search API prep wrappers I) exports `PieceShapeND` plus `planner_nd_core` orientation/column/evaluation wrappers from `engine.api` to prepare a boundary-safe move of `engine/playbot/planner_nd_search.py` into `ai/playbot`.
- Stage 279 (slice 269, plannerND-search API prep wrappers II) exports `planner_nd_core` candidate-iteration and greedy-score wrappers from `engine.api`, completing API prep for moving `engine/playbot/planner_nd_search.py` into `ai/playbot` without deep engine imports.
- Stage 280 (slice 270, plannerND-search physical relocation) moves `engine/playbot/planner_nd_search.py` to `ai/playbot/planner_nd_search.py`, keeps an engine-path module-alias shim, and rewires search imports to `tet4d.engine.api` wrappers so the AI boundary remains API-only.
- Stage 281 (slice 271, plannerND-search engine-api canonicalization) updates `engine.api.plan_best_nd_with_budget(...)` to import from `ai.playbot.planner_nd_search` directly, reducing reliance on the transitional `engine/playbot/planner_nd_search.py` shim.
- Stage 282 (slice 272, plannerND-search AI package export polish) adds `plan_best_nd_with_budget` as a lazy export from `ai.playbot.__init__`, improving canonical AI package discoverability after the search planner relocation.
- Stage 283 (slice 273, plannerND-search zero-caller checkpoint) records zero remaining callers of `engine/playbot/planner_nd_search.py` after engine-api and AI-package canonicalization and advances `arch_stage` to `283` before shim pruning.
- Stage 284 (slice 274, plannerND-search shim pruning) removes the zero-caller `engine/playbot/planner_nd_search.py` compatibility shim after the search planner relocation to `ai/playbot/planner_nd_search.py` and canonicalization.
- Stage 285 (slice 275, plannerND-search post-prune docs sync) records the canonical `ai/playbot/planner_nd_search.py` path after shim removal and advances `arch_stage` to `285`.
- Stage 286 (slice 276, plannerND-search family checkpoint) records completion of the Stage 278-285 plannerND-search API-prep/move/prune sequence and advances `arch_stage` to `286` before the full batch verification checkpoint.
- Stage 287 (slice 277, plannerND-search batch verification checkpoint) advances `arch_stage` to `287` and verifies the Stage 278-286 plannerND-search batch with full local `verify.sh` + `ci_check.sh`.
- Stage 288 (slice 278, plannerND-core physical relocation) moves `engine/playbot/planner_nd_core.py` to `ai/playbot/planner_nd_core.py`, keeps an engine-path module-alias shim, and rewires core imports to `tet4d.engine.api` exports so the AI boundary remains API-only.
- Stage 289 (slice 279, plannerND-core engine-api canonicalization I) retargets `engine.api` wrappers for lock/rotation/canonical-block/orientation/column-level helpers to import from `ai.playbot.planner_nd_core`, reducing reliance on the transitional engine shim.
- Stage 290 (slice 280, plannerND-core engine-api canonicalization II) retargets `engine.api` wrappers for ND board evaluation, greedy scoring, and settled-candidate iteration to import from `ai.playbot.planner_nd_core`, further reducing reliance on the transitional engine shim.
- Stage 291 (slice 281, plannerND-core zero-caller checkpoint) records zero remaining callers of `engine/playbot/planner_nd_core.py` after engine-api canonicalization and advances `arch_stage` to `291` before shim pruning.
- Stage 292 (slice 282, plannerND-core shim pruning) removes the zero-caller `engine/playbot/planner_nd_core.py` compatibility shim after the core relocation to `ai/playbot/planner_nd_core.py` and engine-api canonicalization.
- Stage 293 (slice 283, plannerND-core post-prune docs sync) records the canonical `ai/playbot/planner_nd_core.py` path after shim removal and advances `arch_stage` to `293`.
- Stage 294 (slice 284, plannerND-core family checkpoint) records completion of the Stage 288-293 plannerND-core move/canonicalize/prune sequence and advances `arch_stage` to `294` before the aggregate ND-planner checkpoint stages.
- Stage 295 (slice 285, ND planner aggregate checkpoint I) records completion of the Stage 271-294 ND planner family migrations (`planner_nd`, `planner_nd_search`, `planner_nd_core`) and advances `arch_stage` to `295`.
- Stage 296 (slice 286, ND planner aggregate checkpoint II) records the staged checkpoint handoff into the final verification stage for the Stage 271-295 ND planner migration batch and advances `arch_stage` to `296`.
- Stage 297 (slice 287, ND planner aggregate verification checkpoint) advances `arch_stage` to `297` and verifies the Stage 271-296 ND planner migration batch with full local `verify.sh` + `ci_check.sh`.
- Stage 298 (slice 288, playbot package shim zero-caller checkpoint) records zero remaining imports of the transitional `src/tet4d/engine/playbot/__init__.py` compatibility package and advances `arch_stage` to `298` before package-shim pruning.
- Stage 299 (slice 289, playbot package shim pruning) removes the zero-caller `src/tet4d/engine/playbot/__init__.py` compatibility package after AI playbot family canonicalization.
- Stage 300 (slice 290, playbot package post-prune docs sync) records `src/tet4d/ai/playbot/__init__.py` as the canonical playbot package surface after engine package shim removal and advances `arch_stage` to `300`.
- Stage 301 (slice 291, playbot package cleanup verification checkpoint) advances `arch_stage` to `301` and verifies the Stage 298-300 playbot package shim cleanup batch with full local `verify.sh` + `ci_check.sh`.
- Stage 302 (slice 292, menu-keybinding-shortcuts API prep) adds narrow `engine.api` wrappers for menu keybinding shortcut action dispatch/status helpers so `engine/ui_logic/menu_keybinding_shortcuts.py` can move to `ui/pygame` without deep engine imports.
- Stage 303 (slice 293, menu-keybinding-shortcuts UI relocation) moves `src/tet4d/engine/ui_logic/menu_keybinding_shortcuts.py` implementation into `src/tet4d/ui/pygame/menu_keybinding_shortcuts.py`, rewires keybinding file I/O through `tet4d.engine.api`, retains an engine compatibility shim, and baseline-locks the new UI adapter path.
- Stage 304 (slice 294, menu-keybinding-shortcuts caller canonicalization) migrates engine callers (`frontend_nd.py`, `engine/ui_logic/menu_controls.py`) to canonical `src/tet4d/ui/pygame/menu_keybinding_shortcuts.py` imports before shim pruning.
- Stage 305 (slice 295, menu-keybinding-shortcuts engine-api canonicalization) retargets `engine.api` shortcut wrappers to import from `src/tet4d/ui/pygame/menu_keybinding_shortcuts.py`, removing the last internal dependency on the transitional `engine/ui_logic` shim before pruning.
- Stage 306 (slice 296, menu-keybinding-shortcuts shim pruning) records zero remaining callers and removes the transitional `src/tet4d/engine/ui_logic/menu_keybinding_shortcuts.py` compatibility shim after canonicalization to `src/tet4d/ui/pygame/menu_keybinding_shortcuts.py`.
- Stage 307 (slice 297, menu-keybinding-shortcuts family verification checkpoint) records completion of the Stage 302-306 API-prep/move/canonicalize/prune sequence, advances `arch_stage` to `307`, and verifies the checkpoint with full local `verify.sh` + `ci_check.sh`.
- Stage 308 (slice 298, menu-controls API prep I) adds `engine.api` wrappers for keybinding conflict/profile helpers, binding-action lookup, and menu-settings load/save/reset calls so `engine/ui_logic/menu_controls.py` can move to `ui/pygame` without deep engine imports.
- Stage 309 (slice 299, menu-controls UI relocation) moves `src/tet4d/engine/ui_logic/menu_controls.py` implementation into `src/tet4d/ui/pygame/menu_controls.py`, rewires menu control dependencies through `tet4d.engine.api`, retains an engine compatibility shim, and baseline-locks the new UI adapter path.
- Stage 310 (slice 300, menu-controls caller canonicalization) migrates engine and CLI callers (`frontend_nd.py`, `cli/front2d.py`) to canonical `src/tet4d/ui/pygame/menu_controls.py` imports before shim pruning.
- Stage 311 (slice 301, menu-controls zero-caller checkpoint) records zero remaining callers of the transitional `src/tet4d/engine/ui_logic/menu_controls.py` shim after engine/CLI canonicalization and advances `arch_stage` to `311` before shim pruning.
- Stage 312 (slice 302, menu-controls shim pruning) removes the zero-caller `src/tet4d/engine/ui_logic/menu_controls.py` compatibility shim after canonicalization to `src/tet4d/ui/pygame/menu_controls.py`.
- Stage 313 (slice 303, menu-controls post-prune docs sync) records `src/tet4d/ui/pygame/menu_controls.py` as the canonical menu-controls module after shim removal and advances `arch_stage` to `313`.
- Stage 314 (slice 304, menu-controls family checkpoint) records completion of the Stage 308-313 menu-controls API-prep/move/canonicalize/prune sequence and advances `arch_stage` to `314` before the verification checkpoint.
- Stage 315 (slice 305, menu-controls family verification checkpoint) advances `arch_stage` to `315` and verifies the Stage 308-314 menu-controls batch with full local `verify.sh` + `ci_check.sh`.

- Stage 316 (slice 306, retargeted binding label/description engine.api wrappers to keybindings_catalog to prepare keybindings UI relocation without circular imports).
- Stage 317 (slice 307, added engine.api wrappers for keybindings runtime path and storage helpers to prepare keybindings UI relocation).
- Stage 318 (slice 308, moved engine/ui_logic/keybindings.py into ui/pygame, rewired runtime paths and storage through engine.api, retained an engine compatibility shim, and baseline-locked the new UI adapter path).
- Stage 319 (slice 309, canonicalized engine.api keybindings wrappers to import from ui/pygame/keybindings instead of the transitional engine/ui_logic shim).
- Stage 320 (slice 310, canonicalized engine keybindings callers to ui/pygame/keybindings and routed runtime/menu_settings_state through engine.api keybinding wrappers).
- Stage 321 (slice 311, canonicalized CLI launchers to import keybindings from ui/pygame/keybindings before shim pruning).
- Stage 322 (slice 312, canonicalized ui_logic/key_dispatch.py to ui/pygame/keybindings and baseline-locked it as a transitional engine-to-ui adapter).
- Stage 323 (slice 313, canonicalized the first keybindings test slice to ui/pygame/keybindings imports while keeping tests in engine/tests).
- Stage 324 (slice 314, canonicalized the remaining keybindings module test import to ui/pygame/keybindings before shim pruning).
- Stage 325 (slice 315, canonicalized ui_logic/keybindings_menu_model to ui/pygame/keybindings and baseline-locked it as a transitional engine-to-ui adapter).
- Stage 326 (slice 316, recorded zero remaining callers of the transitional engine/ui_logic/keybindings.py shim after engine.api, engine, CLI, and test canonicalization).
- Stage 326 (slice 316, recorded zero remaining callers of the transitional engine/ui_logic/keybindings.py shim after engine.api, engine, CLI, and test canonicalization).