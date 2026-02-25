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
- Preferred foldering heuristic for future slices: target roughly `6-15` files per
  leaf folder, treat `>20` mixed-responsibility files as a split signal, and avoid
  creating new folders that would remain `<=3` files without a strong boundary reason.
- Future stages tighten this until `pygame` imports are fully removed from engine.
