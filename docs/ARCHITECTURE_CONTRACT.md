# Architecture Contract

Status: active architecture baseline  
Last updated: 2026-03-07  
Arch stage: 900

This contract defines the dependency direction, ownership rules, and enforcement
mechanisms for the current `tet4d` codebase. Historical migration narratives live
in `docs/history/DONE_SUMMARIES.md`; this file is the current-state contract only.

## Goals

1. Keep `tet4d.engine` reusable as a lower layer.
2. Keep deterministic gameplay/state logic independent from UI, AI, and tooling.
3. Reduce duplicate ownership by moving adapter concerns out of `engine`.
4. Keep architecture gates actionable and aligned with the actual code.

## Dependency Direction

Allowed direction:

- `tet4d.ui` -> `tet4d.engine`
- `tet4d.ai` -> `tet4d.engine`
- `tet4d.replay` -> `tet4d.engine`
- `tools/*` -> `tet4d.engine`

Forbidden reverse direction:

- `tet4d.engine` -> `tet4d.ui`
- `tet4d.engine` -> `tet4d.ai`
- `tet4d.engine` -> `tet4d.replay`
- `tet4d.engine` -> `tools/*`

Interpretation:

1. Upper layers may import engine modules directly when that removes wrapper
   duplication.
2. `tet4d.engine.api` is a small compatibility facade for stable engine-owned
   helpers. Replay code and explicit compatibility tests may use it, but runtime
   UI, AI, and tools should prefer the narrow direct owner that already exists.
3. Engine modules must never depend back on UI or AI adapters.

## Ownership Rules

### Engine (`src/tet4d/engine`)

Owns:

1. Core model/state types.
2. Deterministic gameplay rules and topology.
3. Runtime config, persistence, validation, and tutorial state machinery.
4. Engine-owned convenience exports in `tet4d.engine.api`.

Must not own:

1. `pygame` event loops.
2. Rendering adapters.
3. Audio playback adapters.
4. Playbot package ownership.
5. Reverse imports into `tet4d.ui` or `tet4d.ai`.

### Engine Core (`src/tet4d/engine/core`)

Owns pure deterministic helpers only.

Forbidden in `engine/core`:

1. `pygame`
2. file I/O
3. `print`
4. `logging`
5. `time`
6. imports from non-core `tet4d.engine`
7. imports from `tet4d.ui`, `tet4d.ai`, `tet4d.replay`, or `tools`

### UI (`src/tet4d/ui/pygame`)

Owns:

1. Event loops and runtime bootstrap.
2. Rendering, layout, and camera/view adapters.
3. Menu surfaces and gameplay frontends.
4. Keybinding runtime and adapter-local state sync.

UI may import engine modules directly. It should prefer the narrowest engine
owner that already exists instead of adding new `engine.api` wrappers.

### AI (`src/tet4d/ai/playbot`)

Owns:

1. Playbot controller/planners/dry-run tooling.
2. AI-specific types and policy interpretation.

AI may import engine modules directly. It must not be re-exported back through
`tet4d.engine` in ways that recreate reverse ownership.

### Replay (`src/tet4d/replay`)

Owns replay schema and playback helpers. Replay stays outside engine core and may
consume engine state/config types as needed.

### Tools (`tools/*`)

Own governance, benchmark, and stability checks. Tools should prefer stable
engine-owned helpers, but direct engine or UI imports are acceptable when they
measure UI-specific behavior or when they remove wrapper duplication without
creating reverse dependencies.

## Package Placement Rules

1. Pure deterministic logic goes in `src/tet4d/engine/core/`.
2. Non-core gameplay/runtime logic goes in `src/tet4d/engine/`.
3. `pygame` adapters go in `src/tet4d/ui/pygame/`.
4. Playbot code goes in `src/tet4d/ai/playbot/`.
5. CLI entrypoints stay in `cli/` and should be thin shims over package code.
6. New wrappers are justified only when they reduce duplication or preserve a
   stable public engine-owned contract.

## Current Canonical Owners

1. Piece-local transform math: `src/tet4d/engine/core/piece_transform.py`
2. Rotation-kick candidate and resolution logic: `src/tet4d/engine/core/rotation_kicks.py`
3. Engine gameplay convenience exports: `src/tet4d/engine/gameplay/api.py`
4. Engine runtime convenience exports: `src/tet4d/engine/runtime/api.py`
5. Engine tutorial convenience exports: `src/tet4d/engine/tutorial/api.py`
6. 2D orchestration frontend: `src/tet4d/ui/pygame/front2d_game.py`
7. 2D setup/menu owner: `src/tet4d/ui/pygame/front2d_setup.py`
8. 2D runtime loop owner: `src/tet4d/ui/pygame/front2d_loop.py`
9. 2D runtime compatibility facade: `src/tet4d/ui/pygame/front2d_runtime.py`
10. Shared setup-menu runner: `src/tet4d/ui/pygame/menu/setup_menu_runner.py`
11. ND setup/menu/config owner: `src/tet4d/ui/pygame/frontend_nd_setup.py`
12. ND gameplay/input owner: `src/tet4d/ui/pygame/frontend_nd.py`
13. Settings-hub state/actions owner: `src/tet4d/ui/pygame/launch/settings_hub_state.py`
14. Settings-hub orchestration/view owner: `src/tet4d/ui/pygame/launch/launcher_settings.py`
15. 3D render adapter: `src/tet4d/ui/pygame/front3d_render.py`
16. 4D render adapter: `src/tet4d/ui/pygame/front4d_render.py`
17. Shared tutorial runtime UI helpers: `src/tet4d/ui/pygame/runtime_ui/`

## Enforcement

Architecture is enforced by both hard boundary checks and metrics.

### Hard checks

1. `scripts/check_architecture_boundaries.sh`
   - engine must not import `pygame`
   - engine must not import `tet4d.ui`
   - engine must not import `tet4d.ai`
   - engine must not import `tet4d.replay`
   - engine must not import `tools`
2. `scripts/check_engine_core_purity.sh`
   - strict `engine/core` purity gate

### Metric budgets

1. `scripts/arch_metrics.py`
2. `tools/governance/architecture_metric_budget.py`

Current non-negotiable zero budgets:

1. `engine_core_purity.violation_count = 0`
2. `deep_imports.engine_core_to_engine_non_core_imports.count = 0`
3. `deep_imports.engine_to_ui_non_api.count = 0`
4. `deep_imports.engine_to_ai_non_api.count = 0`
5. `migration_debt_signals.pygame_imports_non_test.count = 0`

Upper-layer direct imports into engine are tracked but are not boundary
violations under the current architecture.

## Refactor Policy

1. Prefer deletion over new wrappers.
2. Prefer moving ownership to the real package rather than preserving a stale
   transitional location.
3. If a wrapper remains, document why it still exists.
4. Update docs and architecture gates in the same batch as code movement.
5. Keep `CURRENT_STATE.md`, `docs/PROJECT_STRUCTURE.md`, and `docs/BACKLOG.md`
   synchronized whenever ownership changes.

## Acceptance Criteria For Architecture Batches

1. `tet4d.engine` has no reverse imports into `tet4d.ui` or `tet4d.ai`.
2. Moved UI code is owned by `src/tet4d/ui/pygame/`, not mirrored in `engine`.
3. Moved AI code is owned by `src/tet4d/ai/playbot/`, not mirrored in `engine`.
4. Architecture scripts and metric budgets match the implemented rule set.
5. `CODEX_MODE=1 ./scripts/verify.sh` passes.
