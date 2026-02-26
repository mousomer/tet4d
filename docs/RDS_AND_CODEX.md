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
10. Redundant compatibility facades may be removed when callers are migrated, but keep
    boundary-enforcing adapters (for example `engine -> ui` compatibility shims) until the
    corresponding modules are physically moved and boundary checks remain green.
11. Public playbot APIs should now be imported from `tet4d.engine.api`; the
    `tet4d.ai.playbot` package only retains shared internal helper logic during migration.
12. For engine folder cleanup, prefer merged buckets (`engine/gameplay`,
    `engine/ui_logic`, `engine/runtime`) over many tiny folders; keep moves prefix-based
    and compatibility-shimmed to minimize import churn.
13. As merged-folder moves land, update imports inside moved modules to use the new
    merged buckets (for example `engine.runtime.*`) so old engine-path shims can be
    pruned later without broad churn.
14. Keep governance/tooling call sites stable during folder moves by leaving short
    engine-path compatibility shims until the next prune stage.
15. When multiple moved modules form a coherent cluster (for example `ui_logic`
    keybindings helpers), update moved callers to import from the same new folder
    immediately to reduce future shim-pruning churn.
16. Start `engine/runtime` with menu settings/config/persistence modules first; they
    are runtime/file-I/O concerns and a low-risk way to reduce the top-level
    `engine/` catch-all.
17. When moving runtime/config modules, prefer module-alias compatibility shims
    (`sys.modules[__name__] = impl`) over `import *` shims when tests or callers
    patch module-level globals/private helpers.
18. Continue building `engine/runtime` with score/analytics modules before touching
    gameplay-heavy files; this reduces top-level `engine/` count without affecting
    pygame/UI boundaries.
19. Start `engine/gameplay` with low-coupling helpers first (`challenge_mode`,
    `speed_curve`, `exploration_mode`) before moving heavily reused primitives or
    the main `game2d.py` / `game_nd.py` modules.
20. Once gameplay helpers land, move shared gameplay primitives (`pieces2d`,
    `pieces_nd`, `topology`) next and update moved gameplay modules to use local
    `engine.gameplay.*` imports before broad caller rewrites.
21. Before moving `game2d.py` / `game_nd.py`, first update them to import from the
    new gameplay/runtime clusters directly (prep seam stage) so later moves do not
    combine path migration with large import rewrites.
22. Add periodic shim-prune stages: remove only compatibility shims with zero callers
    (or after migrating the final callers) and prefer net-LOC-reduction batches to
    keep the restructuring maintainable.
23. Complete the `engine/runtime` analytics cluster (`score_analyzer*` and
    `assist_scoring`) before moving the main `game2d.py` / `game_nd.py` modules.
24. Before moving `game2d.py` / `game_nd.py`, move supporting gameplay modules such as
    `topology_designer.py` into `engine/gameplay` so game-module moves have fewer
    cross-folder concerns.
25. Use a prep seam for high-risk `game2d.py` / `game_nd.py` moves: add temporary
    `engine.gameplay.game2d/game_nd` aliases first, migrate a few internal callers,
    then swap in the real moved modules in the next stages.
26. For physical `game2d.py` / `game_nd.py` moves, prefer module-alias shims at the
    old engine paths so tests and monkeypatch-heavy callers keep module-global behavior.
27. Move `game2d.py` and `game_nd.py` in separate stages (2D first, then ND/3D/4D)
    even when the move mechanics are identical, so regressions are easier to isolate.
28. After moving `game2d.py` / `game_nd.py`, migrate engine-internal callers to
    `engine.gameplay.game2d/game_nd` before pruning old engine-path shims; keep
    tests/external imports stable until a dedicated compatibility-prune stage.
29. Migrate tests to canonical `engine.gameplay.game2d/game_nd` imports before
    deleting `engine.game2d` / `engine.game_nd`; this isolates shim-prune failures
    to true external callers rather than internal test churn.
30. Before deleting compatibility shims for moved modules, run a repo-wide import
    audit and record a zero-caller checkpoint in docs/backlog to make the prune
    stage clearly reversible and easier to review.
31. Once a moved-module shim is deleted, treat the new path as canonical in docs,
    tests, and tooling immediately; do not reintroduce compatibility imports in
    follow-up stages.
32. Prioritize moving file-I/O-heavy helper modules (for example help/config/topic
    loaders) into `engine/runtime` before deeper gameplay/UI classes; this reduces
    side-effect debt with lower regression risk.
33. When moving UI helpers that still need config constants, add a narrow
    `engine.api` wrapper (for example `project_constant_int`) instead of allowing
    `ui/pygame` modules to import deep engine config modules directly.
34. Prefer extracting shared UI utility/caching helpers before renderers and menus;
    this reduces `pygame` imports in top-level engine with minimal behavior risk.
35. After shared UI helpers (`ui_utils`, text caches) move, extract projection/math
    render helpers next (`projection3d`) before larger renderer modules so import
    rebasing stays localized.
36. For UI helpers that need project-root/file-path context (for example icon/theme
    loaders), add a narrow `engine.api` path wrapper rather than importing
    `engine.runtime.project_config` directly from `ui/pygame`.
37. When moving UI helpers that need engine keybinding utilities, prefer adding
    narrow `engine.api` wrappers (for example `format_key_tuple` and runtime
    binding-group lookup) rather than importing `keybindings.py` directly from UI.
38. Sequence UI helper moves by dependency chain (icons/cache/utils -> control helper
    -> panel helper -> renderers) so each stage can keep imports local and avoid
    temporary deep imports from `ui/pygame` into engine internals.
39. Move UI camera/input helpers after projection utilities so local `ui/pygame`
    imports replace engine-path imports cleanly without extra compatibility layers.
40. Continue consolidating non-rendering menu/input modules under `engine/ui_logic`
    in parallel with UI pygame extractions to reduce top-level `engine/` crowding
    without increasing `ui -> engine.api` surface area.
41. Prefer moving small, dependency-light dispatch/layout helpers into `engine/ui_logic`
    before larger menu state/render modules to keep each foldering stage reviewable.
42. Canonicalize engine and test callers to UI helper modules (`tet4d.ui.pygame.*`)
    in separate stages before pruning engine-path compatibility shims; this keeps
    shim-removal stages small and easy to validate.
43. Apply the same pattern to shared math/projection helpers (`projection3d`)
    before attempting renderer-module moves so rendering regressions are easier to
    localize.
44. Treat shared UI math/projection helpers as high-value shim-pruning targets:
    once engine and test callers are canonicalized, remove the engine-path shim
    promptly to prevent renderer modules from drifting back to legacy imports.
45. For UI helpers referenced by both engine modules and `cli/*`, split
    canonicalization into engine-first and CLI-followup stages before pruning the
    engine-path shim to keep launcher-risk changes isolated.
46. Treat CLI launcher imports as their own canonicalization step even when no
    tests change, so wrapper/help regressions can be isolated from engine and
    shim-pruning diffs.
47. When a shared UI helper has no remaining test callers (engine+CLI only), use
    a two-step canonicalization plus prune sequence and verify via zero-caller
    grep before deleting the engine-path shim.
48. Apply the same staged canonicalization/pruning pattern to runtime shims
    (`engine/runtime/*` compatibility modules), splitting engine callers and
    CLI callers when both exist.
49. For runtime helpers used by launchers/menus, keep CLI canonicalization in its
    own stage before shim deletion so launcher regressions remain easy to bisect.
50. Zero-caller audits for runtime shim pruning should ignore canonical relative
    imports inside `src/tet4d/engine/runtime/*` (for example `.menu_config`
    within runtime modules) and only block external/legacy shim callers.
51. For high-fanout runtime shims (for example `project_config`), split
    canonicalization into engine-first, then CLI/tests, then prune to keep
    breakages easy to localize.
52. When pruning runtime shims after CLI/test migration, run a final repo-wide
    grep for `from tet4d.engine import <shim>` forms; test modules often use the
    aggregated import style and are easy to miss.
53. When a shim prune changes the canonical path mentioned in structure docs,
    update `docs/PROJECT_STRUCTURE.md` in the same stage so the folder map
    reflects the post-prune path immediately.
54. Apply the same engine-first / CLI+tests-followup / prune sequence to runtime
    state-persistence shims (`menu_settings_state`, `menu_persistence`) to keep
    launcher/settings regressions localized during migration.
55. For runtime state shims referenced by tests via `from tet4d.engine import ...`,
    expect aggregated-import cleanup during the CLI/test stage and treat those
56. For `menu_persistence`-style runtime shims used by both launchers and in-game
    menus, migrate engine and CLI callers in the same stage when there are no
    test imports, then prune in a follow-up stage after a repo-wide zero-caller audit.
57. Runtime shim prune stages should include a final `ci_check.sh` run (not just
    `verify.sh`) when they remove persistence/config modules used by launchers,
    so compileall + benchmark checks exercise the post-shim import graph.
58. `check_architecture_boundaries.sh` baseline-locks current transitional
    `engine -> tet4d.ui` imports (same model as pygame baseline locking) and
    should fail only on new imports outside the recorded allowlist until UI extraction completes.
59. Workspace policy-template marker files (`.workspace_policy_version.json`,
    `.policy/policy_template_hashes.json`) are optional in a fresh public clone;
    baseline policy/drift scripts should no-op on missing markers while repo-extension
    policy checks continue enforcing repo-specific governance.
60. For UI shims used by both engine and CLI launchers (for example
    `font_profiles`), keep the engine-caller migration and CLI-caller migration
    in separate stages before shim pruning so launcher regressions remain isolated.
61. Before pruning a UI compatibility shim after CLI migration, run a repo-wide
    grep for aggregated imports (`from tet4d.engine import <shim>`) in tests and
    support modules; they are easy to miss even when engine/CLI callers are clean.
62. `font_profiles`-style UI shims can be pruned without a test migration stage
    when repo-wide grep confirms zero engine/CLI/tests callers and the canonical
    module (`tet4d.ui.pygame.font_profiles`) is already imported directly.
63. Apply the same engine-first / CLI-followup / prune sequence to `game_loop_common`
    because it is used by both launcher CLI and engine loop runners.
64. `game_loop_common` prune stages should include a final zero-caller grep for
    `process_game_events` import forms because launcher and loop-runner imports
    often differ (absolute vs relative).
65. When a `game_loop_common`-style shim is fully canonicalized (engine+CLI only,
    no test imports), prune the shim immediately in the next stage to keep UI
    migration progress visible in top-level `engine/`.
66. `menu_runner` canonicalization can combine engine and CLI callers in one
    stage when there are no test imports, followed by an immediate zero-caller
    prune stage.
67. `menu_runner` prune stages should still run `ci_check.sh` (not just
    `verify.sh`) because launcher/menu loops are exercised indirectly by compile
    and benchmark imports even when pytest coverage is unchanged.
68. For paired UI utility shims that are imported together (`panel_utils` +
    `text_render_cache`), migrate callers in one stage and prune both shims in a
    single follow-up stage after a combined zero-caller audit.
69. Combined zero-caller audits for paired shims should ignore canonical relative
    imports inside `src/tet4d/ui/pygame/*` (for example `.text_render_cache`
    within `panel_utils.py`) and only block legacy engine/CLI/tool callers.
70. For simple constant/lookup UI shims (`keybindings_defaults`), engine-caller
    canonicalization is usually a single-file change; keep it isolated before the
    prune stage to simplify regression triage.
71. `keybindings_defaults` prune stages can skip a CLI/test migration phase when
    repo-wide grep confirms there are no non-engine callers before deletion.
72. `keybindings_menu_input` is typically an engine-only shim; canonicalize the
    import in `keybindings_menu.py` first, then prune after a zero-caller audit.
73. Engine-only UI-input shim prune stages (`keybindings_menu_input`) can reuse
    the standard verify+ci_check prune cadence even when no CLI/tests change.
    test rewrites as part of shim-prune prep (not post-prune fixes).
56. Runtime shim zero-caller audits should allow canonical imports within
    `engine/runtime/*` (for example `.menu_settings_state` in
    `runtime/menu_persistence.py`) and only block external shim callers.
57. Runtime shims with no CLI callers (for example `runtime_config`) can use a
    two-stage engine+tests canonicalization followed by prune, but still require
    a repo-wide zero-caller audit before deletion.
58. Include API-facade imports (`tet4d.engine.api`) in runtime-shim caller audits;
    they are easy to miss and can silently keep a compatibility shim alive.
42. After moving a helper into `engine/ui_logic`, migrate internal engine/CLI callers
    to the canonical path first, then remove the compatibility shim in a follow-up stage.
43. Migrate tools/tests to canonical paths before shim pruning to avoid mixing
    path cleanup with behavioral test changes and to keep tests in test folders.
44. After a zero-caller audit, delete compatibility shims promptly to avoid top-level `engine/` clutter regrowth and to ensure net LOC decreases over the cleanup sequence.
45. Apply the same caller-migration-then-prune sequence to `engine/runtime` shims (analytics/help modules) to keep runtime clustering consistent with the `ui_logic` cleanup flow.
46. Keep tests in test folders while migrating canonical imports; only change import paths, not test placement, when pruning compatibility shims.
47. After runtime shim caller audits reach zero, prune those shims promptly to keep top-level `engine/` focused on canonical modules and active compatibility needs only.
48. For `ui/pygame` helper shim removal, migrate engine callers first, then tests, then prune the shim to keep failures easy to triage.
49. For `ui/pygame` helper test migrations, keep test files in `src/tet4d/engine/tests/` and change imports only, so shim-prune regressions are isolated to pathing.
50. For single-helper `ui/pygame` shim pruning, prefer one helper family per stage batch (engine callers -> tests -> prune) to keep CI triage simple.
51. For small paired UI helpers (e.g., `control_helper` + `control_icons`), treat them as one family and migrate engine callers together before test updates and shim pruning.
52. For paired UI helper test migrations, prefer changing both helper imports in the same test file before pruning either shim to avoid mixed-module import states.
53. After paired UI helper caller audits reach zero, prune both shims in one stage to ensure a measurable top-level `engine/` file-count reduction.
54. For `engine/core` work, keep `scripts/check_engine_core_purity.sh` green and avoid imports from non-core `tet4d.engine` modules.
55. Prefer 2D-first reducer/core slices when extracting gameplay logic to keep diffs small and CI triage simple.
56. After a 2D-first slice lands, close the same reducer seam for ND next to retire metrics debt (`core_step_state_method_calls`).

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

For interactive/Codex local runs, `CODEX_MODE=1 ./scripts/verify.sh` is allowed to reduce stability repeats and success log volume. CI remains authoritative via `./scripts/ci_check.sh`, which now delegates to `./scripts/verify.sh` as a thin wrapper to avoid local/CI pipeline drift.
CI now runs `scripts/arch_metrics.py` (informational) plus `scripts/check_architecture_metric_budgets.sh` (fail-on-regression) via `scripts/ci_check.sh` to track and lock architecture migration debt (including private-helper debt, reducer field-mutation debt, 2D/ND core-view extraction, UI deep-import reduction, playbot import-surface migration, early pygame-module extraction progress, and playbot internal relocation progress across Stages 13-32).

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
9. Root wrapper entrypoint is `front.py`; it may provide wrapper-only mode selection (for example `--frontend/--mode`) so long as it delegates to `cli/front*.py` without gameplay changes.
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
24. `scripts/check_git_sanitation.sh` (workspace baseline template),
25. `scripts/check_policy_compliance.sh` (workspace baseline template),
26. `scripts/check_policy_template_drift.sh` (workspace baseline template),
27. `scripts/check_git_sanitation_repo.sh` + `scripts/check_policy_compliance_repo.sh` (repo-native extensions).
28. Workspace policy marker files (for example, `.workspace_policy_version.json`) are required when the workspace baseline is adopted; repo-native CI checks must remain in the `*_repo.sh` extension layer.
29. Canonical maintenance should not pin workspace baseline template script message text or exact workspace-policy metadata patch values/path literals (`policy_version`, `policy_source_path`); baseline identity is enforced by `scripts/check_policy_template_drift.sh` + `.policy/policy_template_hashes.json`, while local contract content rules should focus on repo-native scripts and CI entrypoints (using regex/presence checks for portable metadata).

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
9. Architecture stage checkpoint (`arch_stage: 160`) routes score-analyzer
   summary writes and event-log appends through
   `src/tet4d/engine/runtime/score_analyzer_storage.py`.
