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
- Preferred foldering heuristic for future slices: target roughly `6-15` files per
  leaf folder, treat `>20` mixed-responsibility files as a split signal, and avoid
  creating new folders that would remain `<=3` files without a strong boundary reason.
- Future stages tighten this until `pygame` imports are fully removed from engine.
