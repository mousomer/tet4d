# RDS Files And Codex Instructions

This document is section `3` of the unified documentation layout.

Architecture boundary contract:
- `docs/ARCHITECTURE_CONTRACT.md`

## RDS index

All requirement/design specs are in:
- `docs/rds/RDS_TETRIS_GENERAL.md`
- `docs/rds/RDS_KEYBINDINGS.md`
- `docs/rds/RDS_MENU_STRUCTURE.md`
- `docs/rds/RDS_PLAYBOT.md`
- `docs/rds/RDS_SCORE_ANALYZER.md`
- `docs/rds/RDS_PACKAGING.md`
- `docs/rds/RDS_FILE_FETCH_LIBRARY.md`
- `docs/rds/RDS_2D_TETRIS.md`
- `docs/rds/RDS_3D_TETRIS.md`
- `docs/rds/RDS_4D_TETRIS.md`

Read order:
1. General RDS
2. Keybindings RDS
3. Menu structure RDS
4. Playbot + score-analyzer RDS
5. Packaging RDS
6. File-fetch library RDS
7. Mode-specific RDS
8. This Codex instructions page

## Codex contributor workflow

1. Read the relevant RDS files before editing gameplay logic.
2. Keep keybindings external; do not hardcode mode keys in frontends.
3. Preserve deterministic behavior where seeds are used.
4. When refactoring frontends, keep behavior parity with existing tests.
5. Prefer small, composable helpers over large event/render functions.
6. For repo restructuring/governance updates, produce a short plan + acceptance criteria first and update `docs/BACKLOG.md` when scope changes.
7. Follow repo-root `AGENTS.md` verification contract (`./scripts/verify.sh`) after governance/CI/script changes.
8. Current source layout: runtime code is under `src/tet4d/engine/`; local dev/CI should use editable install (`pip install -e .`) so `tet4d` imports resolve without shims.
9. For architecture refactors, follow `docs/ARCHITECTURE_CONTRACT.md` and keep boundary checks green.
10. For `engine/core` work, keep `scripts/check_engine_core_purity.sh` green and avoid imports from non-core `tet4d.engine` modules.
11. Prefer 2D-first reducer/core slices when extracting gameplay logic to keep diffs small and CI triage simple.
12. After a 2D-first slice lands, close the same reducer seam for ND next to retire metrics debt (`core_step_state_method_calls`).

## Coding best practices

1. Keep game rules in engine modules (`game2d.py`,`game_nd.py`) and keep rendering thin.
2. Reuse shared projection/menu/input helpers to avoid 3D/4D drift.
3. Avoid side effects during import (especially in keybinding/config modules).
4. Keep files ASCII unless there is a strong reason otherwise.
5. Name helper functions by intent (`_advance_gravity`,`_tick_clear_animation`, etc.).
6. Keep complexity in check; run `ruff --select C901` on changes.

## Testing instructions

Run after every gameplay or input change:

```bash
scripts/bootstrap_env.sh
ruff check .
ruff check . --select C901
python3 tools/governance/validate_project_contracts.py
python3 tools/governance/scan_secrets.py
python3 tools/governance/check_pygame_ce.py
pytest -q
PYTHONPATH=. python3 tools/stability/check_playbot_stability.py --repeats 20 --seed-base 0
python3.14 -m compileall -q  front2d.py  cli/front2d.py  src/tet4d  src/tet4d/engine
```

For repository governance/CI changes, also run:

```bash
./scripts/check_git_sanitation.sh
./scripts/check_policy_compliance.sh
# includes scripts/check_architecture_boundaries.sh (import boundary gate)
# includes scripts/check_engine_core_purity.sh (strict core purity gate)
./scripts/verify.sh
```

Editable install is expected before running verification locally:

```bash
python3 -m pip install -e ".[dev]"
```

For interactive/Codex local runs, `CODEX_MODE=1 ./scripts/verify.sh` is allowed to reduce stability repeats and success log volume. CI remains authoritative via `./scripts/ci_check.sh`.
CI now also runs `scripts/arch_metrics.py` (informational) via `scripts/ci_check.sh` to track architecture migration debt (including reducer private-helper debt in `core/step` and `core/rules` during Stage 13+ refactors).

Minimum required coverage for gameplay-affecting changes:
1. Unit tests for engine correctness (move/rotate/lock/clear/scoring).
2. Replay determinism tests.
3. Per-mode smoke tests for key routing and system controls.
4. If controls changed, verify JSON keybinding load/save behavior.

## Done criteria for gameplay changes

1. RDS intent remains accurate or is updated in the same change.
2. Existing tests pass and new behavior has targeted tests.
3. No new C901 failures.
4. Usage docs remain valid (`README.md`, docs links, run commands).
5. Packaging docs/workflow remain valid when packaging files change:
6. `docs/RELEASE_INSTALLERS.md`,
7. `.github/workflows/release-packaging.yml`,
8. `packaging/`.

## Canonical maintenance contract

1. Canonical maintenance rules are machine-checked and source-controlled in:
2. `config/project/canonical_maintenance.json`
3. Validation command:
4. `python3 tools/governance/validate_project_contracts.py`
5. Secret scan policy + command:
6. `config/project/secret_scan.json`
7. `python3 tools/governance/scan_secrets.py`
5. Validation is part of CI via:
6. `scripts/ci_check.sh`
7. Any change touching gameplay/config/menu/help should keep these artifacts synchronized in the same PR:
8. `docs/BACKLOG.md`
9. `docs/FEATURE_MAP.md`
10. `docs/rds/`
11. `README.md`
12. `src/tet4d/engine/tests/` (or relevant test suites)
13. Canonical connected artifacts now include:
14. `config/schema/*.schema.json`,
15. `docs/migrations/*.md`,
16. `tests/replay/manifest.json`+`tests/replay/golden/.gitkeep`,
17. `docs/help/HELP_INDEX.md`+`assets/help/manifest.json`,
18. `docs/RELEASE_CHECKLIST.md`.
19. `docs/RELEASE_INSTALLERS.md`+`packaging/`+`.github/workflows/release-packaging.yml`.
20. Repo governance enforcement files:
21. `AGENTS.md`,
22. `config/project/policy_manifest.json`,
23. `scripts/verify.sh`,
24. `scripts/check_git_sanitation.sh`,
25. `scripts/check_policy_compliance.sh`.
26. Workspace-local policy marker files (for example, `.workspace_policy_version.json`) are optional and must not be required by CI/policy checks.

## Simplification and Technical Debt Tracking (2026-02-18)

Authoritative open/deferred items are tracked in:
1. `docs/BACKLOG.md`

### Active open items (synced from `docs/BACKLOG.md`)

1. Active open items are maintained in `docs/BACKLOG.md` (single source of truth).
2. Current remaining items include:
3. `P3`: continuous CI/stability watch and optional future module splits.
4. Complexity budget (`C901`) remains enforced by `scripts/ci_check.sh` and CI workflows.
5. Current `BKL-P2-006` execution report:
6. `docs/plans/PLAN_HELP_AND_MENU_RESTRUCTURE_2026-02-19.md`
7. Current status: closed (`M1` + `M2` + `M3` + `M4` completed: help topic contract + schemas + shared layout-zone renderer + live key sync/paging + parity/compact hardening).

### Current complexity hotspots (`ruff --select C901`)

1. None currently open; keep this verified per change set.

### Recent simplification baseline (already completed)

1. Shared menu-state dispatcher pattern extracted and reused.
2. Shared camera pose animator extracted.
3. Shared ND movement dispatch pipeline extracted.
4. Branching piece-set selector replaced with registry maps.
5. App boot/display/audio persistence glue consolidated.
6. Shared UI helpers extracted to `tetris_nd/ui_utils.py`.
7. Pause/settings row definitions externalized to config and rendered by shared panel helpers.
8. Keybindings menu split into dedicated view/input modules.
9. Shared ND launcher runner extracted for 3D/4D setup-to-game flow.
10. Shared playbot lookahead helper extracted and used by 2D + ND planners.
11. Runtime playbot policy validation decomposed into section validators.
12. Runtime help flow now uses decision-based shared event handling (no nested callbacks in loops).
13. Shared 3D/4D projected grid-mode renderer extracted to `tetris_nd/grid_mode_render.py`.
14. Keybinding defaults/catalog split extracted to `tetris_nd/keybindings_defaults.py` + `tetris_nd/keybindings_catalog.py`.
15. Score-analyzer feature extraction split to `tetris_nd/score_analyzer_features.py`.
16. 2D side-panel renderer extracted to `tetris_nd/gfx_panel_2d.py`.
17. Runtime config validation now split by concern (`shared`/`gameplay`/`playbot`/`audio`) with stable import surface.
18. 3D frontend responsibilities now split between runtime/input orchestration (`front3d_game.py`) and render/view layer (`front3d_render.py`).
19. Rendering caches added:
20. gradient-surface cache in `tetris_nd/ui_utils.py`,
21. bounded text-surface cache in `tetris_nd/panel_utils.py` (used by shared side-panel render paths).
22. Shared text rendering cache extracted to `tetris_nd/text_render_cache.py` and reused by control-helper/panel paths.
23. 4D render path now pre-indexes locked cells by `w` layer per frame to avoid repeated full-board scans.
24. 4D layer-grid rectangle layout is memoized for stable window/layer-count combinations.

### Verification requirements for simplification PRs

1. No behavior changes without tests.
2. Add or update targeted tests before extraction/refactor.
3. Keep deterministic replay tests green.
4. Run:
5. `ruff check .`
6. `ruff check . --select C901`
7. `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3.11 -m pytest -q`
8. `python3.14 -m compileall -q  front.py  cli/front.py  src/tet4d  src/tet4d/engine`
