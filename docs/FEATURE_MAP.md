# Feature Map

User-facing feature map for the shipped `tet4d` experience.

## 1. Launcher and Menus

- Unified launcher: `Play 2D`, `Play 3D`, `Play 4D`, `Help`, `Settings`, `Keybindings Setup`, `Bot Options`, `Quit`.
- Shared `Settings` menu (non-dimension-specific):
  - Audio: master volume, SFX volume, mute, save/reset.
  - Display: fullscreen toggle, windowed size capture, save/reset.
- Setup menus are dimension-specific and only show per-mode gameplay options.
- Pause menu is unified across modes: resume/restart/settings/keybindings/profiles/help/back to main/quit.
- Reset defaults requires confirmation.
- Autosave persists session continuity silently (`Autosaved` status), while explicit `Save` remains manual durable save.

## 2. Gameplay (2D/3D/4D)

- Deterministic sparse-board gameplay core (`x`, `y`, `z`, `w`; gravity on `y`).
- 2D line clear rule: one full `x` line clears.
- 3D and 4D clear full gravity-orthogonal planes.
- Animated piece rotation and animated clear feedback.
- Challenge mode: configurable randomly prefilled lower layers.
- Fullscreen and windowed play with stable menu/game return path.

## 3. View and Camera

- Grid modes:
  1. `OFF` (shadow/board silhouette only)
  2. `EDGE` (outer edges only)
  3. `FULL` (full lattice)
  4. `HELPER` (grid lines intersecting active piece)
- 3D camera controls:
  - `H/J/K/L` strict yaw mode (`-15 / -90 / +90 / +15`).
  - Additional pitch controls and mouse orbit/zoom.
- 4D rendering:
  - 4D board is displayed as multiple 3D `w`-layer boards.
  - Slicing selects focused `z`/`w` visual layers and does not alter physics.

## 4. Keybindings

- External JSON keybinding files per dimension:
  - `/Users/omer/workspace/test-code/tet4d/keybindings/2d.json`
  - `/Users/omer/workspace/test-code/tet4d/keybindings/3d.json`
  - `/Users/omer/workspace/test-code/tet4d/keybindings/4d.json`
- Built-in keyboard sets: `small` and `full`.
- In-app keybinding editor supports:
  - top-level scope sections (`General`, `2D`, `3D`, `4D`),
  - rebind,
  - conflict strategy,
  - save/load/save-as,
  - profile cycle/create/rename/delete,
  - reset to defaults.
- Grouped in-game helper panels: `Translation`, `Rotation`, `Camera/View`, `Slice`, `System`.

## 5. Piece Sets

- Native piece sets for 2D, 3D, and truly 4D gameplay.
- Optional 4D six-cell piece set.
- Random-cell piece sets per dimension.
- Debug rectangular piece sets (large deterministic fillers for verification).
- Lower-dimensional set embedding into higher-dimensional boards.
- Spawn safety: generated pieces are non-empty and non-zero sized.

## 6. Scoring and Assistance

- Base points for piece placement + larger rewards for clears.
- Score multiplier depends on assistance level:
  - bot mode,
  - grid mode,
  - speed level.
- Easier assistance yields lower score multiplier.
- Multiplier and bot status are visible in side panels.

## 7. Playbot

- Modes: `OFF`, `ASSIST`, `AUTO`, `STEP`.
- Planner algorithms: `AUTO`, `HEURISTIC`, `GREEDY_LAYER`.
- Planner profiles: `FAST`, `BALANCED`, `DEEP`, `ULTRA`.
- Adaptive planning under load:
  - budget clamp,
  - candidate caps,
  - lookahead throttling,
  - best-so-far fallback on timeout.
- Board-size-aware default planning budgets.
- 2D/3D/4D dry-run logic validation.
- Benchmark harness with config-driven thresholds and trend-history logging.

## 8. Persistence and Config

- Source-controlled config:
  - `/Users/omer/workspace/test-code/tet4d/config/menu/defaults.json`
  - `/Users/omer/workspace/test-code/tet4d/config/menu/structure.json`
  - `/Users/omer/workspace/test-code/tet4d/config/gameplay/tuning.json`
  - `/Users/omer/workspace/test-code/tet4d/config/playbot/policy.json`
  - `/Users/omer/workspace/test-code/tet4d/config/audio/sfx.json`
- User state persisted in:
  - `/Users/omer/workspace/test-code/tet4d/state/menu_settings.json`
- Missing/corrupt user state falls back to external defaults.

## 9. Verification Coverage

- Unit tests for board/game/pieces/scoring.
- Deterministic replay tests (2D/3D/4D controls).
- Long-run deterministic score snapshots across assist combinations.
- Playbot tests (planning fallback, dry run, greedy priorities, hard-drop thresholds).
- Benchmark checks integrated in CI script.
