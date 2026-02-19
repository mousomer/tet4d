# Feature Map

User-facing feature map for the shipped `tet4d` experience.

## 1. Launcher and Menus

- Unified launcher: `Play 2D`,`Play 3D`,`Play 4D`,`Help`,`Settings`,`Keybindings Setup`,`Bot Options`,`Quit`.
- Shared `Settings` menu (non-dimension-specific):
  - Audio: master volume, SFX volume, mute, save/reset.
  - Display: fullscreen toggle, windowed size capture, save/reset.
  - Analytics: score-analyzer logging toggle, save/reset.
- Setup menus are dimension-specific and only show per-mode gameplay options.
- 3D/4D setup flows now share the same ND setup/menu engine (`tetris_nd/frontend_nd.py`) to reduce drift.
- Pause menu is unified across modes: resume/restart/settings/keybindings/profiles/help/back to main/quit.
- Help screen uses shared header/content/footer layout zones to reduce overlap in compact windows.
- Help topics are context/dimension-filtered from `config/help/topics.json` and ordered by priority.
- Help action rows are live-mapped from `config/help/action_map.json` + active runtime bindings.
- Long help content uses explicit subpage paging (`[`/`]`, `PgUp`/`PgDn`) instead of silent truncation.
- Launcher/pause action parity for `Settings`,`Keybindings`,`Help`,`Bot Options`,`Quit` is contract-enforced in config validation.
- Compact help policy is explicit (`layout.help.compact_*` thresholds): non-critical details collapse first while controls and key hints remain available.
- Reset defaults requires confirmation.
- Autosave persists session continuity silently (`Autosaved`status), while explicit`Save` remains manual durable save.

## 2. Gameplay (2D/3D/4D)

- Deterministic sparse-board gameplay core (`x`,`y`,`z`,`w`; gravity on`y`).
- 2D line clear rule: one full `x` line clears.
- 3D and 4D clear full gravity-orthogonal planes.
- Animated piece rotation and animated clear feedback.
- Challenge mode: configurable randomly prefilled lower layers.
- Fullscreen and windowed play with stable menu/game return path.
- Boundary topology presets in setup:
  - `bounded` (classic edges),
  - `wrap_all` (wrap non-gravity axes),
  - `invert_all` (wrap + mirror non-gravity axes),
  - gravity-axis wrapping is disabled by default.
- Advanced topology designer mode (hidden by default):
  - `Topology advanced` toggle reveals per-axis/per-edge profile selection.
  - Profile source file: `config/topology/designer_presets.json`.
  - Deterministic export path: `state/topology/selected_profile.json`.

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
  - 4D board is displayed as multiple 3D layer boards derived from current 4D view basis.
  - Quarter-turn hyperplane view turns update board decomposition:
    - identity: `W` boards of `(X,Y,Z)`,
    - `xw`: `X` boards of `(W,Y,Z)`,
    - `zw`: `Z` boards of `(X,Y,W)`.
  - Slicing selects focused `z`/`w` visual layers and does not alter physics.
  - Camera-only hyperplane view turns are supported:
    - `view_xw_neg/view_xw_pos` (default `F5/F6`)
    - `view_zw_neg/view_zw_pos` (default `F7/F8`)
  - View-plane turns are render-only and do not mutate gameplay state, scoring, or replay determinism.

## 4. Keybindings

- External JSON keybinding files per dimension:
  - `keybindings/2d.json`
- `keybindings/3d.json`
- `keybindings/4d.json`
- Built-in keyboard sets: `small`, `full`, and `macbook`.
- Compact (`small`) 4D `w` movement defaults: `N` / `/` (no `,/.` dependency).
- Small-profile rotation ladder:
  - 2D: `Q/W`
  - 3D: `Q/W`, `A/S`, `Z/X`
  - 4D: `Q/W`, `A/S`, `Z/X`, `R/T`, `F/G`, `V/B`
- Shared system defaults are deconflicted from the 4D small ladder:
  - restart=`Y`, toggle-grid=`C`, menu=`M`, quit=`Esc`.
- In-app keybinding editor supports:
  - top-level scope sections (`General`,`2D`,`3D`,`4D`),
  - rebind,
  - conflict strategy,
  - save/load/save-as,
  - profile cycle/create/rename/delete,
  - reset to defaults.
- Grouped in-game helper panels: `Translation`,`Rotation`,`Camera/View`,`Slice`,`System`.
- Helper panel hierarchy prioritizes critical controls/state higher; bot/analyzer diagnostics render in the lowest section.
- Action icons in helper/menu rows are cached by action + size for smoother repeated rendering.
- Translation/rotation arrow-diagram guides are available in:
  - Help pages,
  - launcher/pause/settings/keybindings menus,
  - in-game side-panel control helper areas (space permitting).

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
- Score analyzer is integrated on lock events:
  - board-health and placement-quality feature extraction,
  - HUD summary lines (`Quality`,`Board health`,`Trend`),
  - config at `config/gameplay/score_analyzer.json`,
  - persisted telemetry outputs (`state/analytics/score_events.jsonl`,`state/analytics/score_summary.json`) when logging is enabled.

## 7. Playbot

- Modes: `OFF`,`ASSIST`,`AUTO`,`STEP`.
- Planner algorithms: `AUTO`,`HEURISTIC`,`GREEDY_LAYER`.
- Planner profiles: `FAST`,`BALANCED`,`DEEP`,`ULTRA`.
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
  - `config/menu/defaults.json`
- `config/menu/structure.json`
- `config/help/topics.json`
- `config/help/action_map.json`
- `config/topology/designer_presets.json`
- `config/gameplay/tuning.json`
- `config/gameplay/score_analyzer.json`
- `config/playbot/policy.json`
- `config/audio/sfx.json`
- `config/project/io_paths.json`
- `config/project/constants.json`
- `config/project/secret_scan.json`
- User state persisted in:
  - `state/menu_settings.json`
- Missing/corrupt user state falls back to external defaults.
- Path handling uses safe repo-relative `Path` resolution and rejects unsafe absolute/traversal values for state outputs.

## 9. Verification Coverage

- Unit tests for board/game/pieces/scoring.
- Deterministic replay tests (2D/3D/4D controls).
- Long-run deterministic score snapshots across assist combinations.
- Playbot tests (planning fallback, dry run, greedy priorities, hard-drop thresholds).
- Repeated playbot dry-run stability checks via `tools/check_playbot_stability.py`.
- Benchmark checks integrated in CI script.
- 4D renderer profiling tool for projection/cache/zoom change validation: `tools/profile_4d_render.py`.
- CI matrix validates Python `3.11`,`3.12`,`3.13`, and`3.14`.
- Scheduled stability watch runs repeated dry-run checks and policy-analysis snapshots.

## 10. Canonical maintenance automation

- Canonical maintenance contract file:
  - `config/project/canonical_maintenance.json`
- Contract validator:
  - `tools/validate_project_contracts.py`
- Secret scanner:
  - `tools/scan_secrets.py`
- CI runs this validator through:
  - `scripts/ci_check.sh`
- `.github/workflows/stability-watch.yml`
- Contract currently enforces synchronized maintenance of:
  - documentation set (`README`,`docs`,`RDS`,`BACKLOG`,`FEATURE_MAP`),
  - help guide renderer (`tetris_nd/menu_control_guides.py`) and help manifest,
  - core tests and canonical runtime config files,
  - schema + migration files (`config/schema`,`docs/migrations`),
  - replay manifest contract (`tests/replay/manifest.json`+`tests/replay/golden/.gitkeep`),
  - help content contract (`docs/help/HELP_INDEX.md`,`assets/help/manifest.json`),
  - release checklist (`docs/RELEASE_CHECKLIST.md`).
