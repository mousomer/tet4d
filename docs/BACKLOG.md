# Consolidated Backlog

Generated: 2026-02-18  
Updated: 2026-03-04  
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
5. `WATCH` `[BKL-P3-013]` Interactive tutorials rollout watch:
   track data-driven lesson packs, deterministic step progression, input gating,
   and tutorial regression harness coverage across 2D/3D/4D.

## 4. Gap Mapping to RDS

1. `docs/rds/RDS_TETRIS_GENERAL.md`: CI/stability workflows and setup-menu dedup follow-up are closed; maintain drift watch only.
2. `docs/rds/RDS_PLAYBOT.md`: learning-mode architecture is implemented; maintain tuning/stability watch only.
3. `docs/rds/RDS_MENU_STRUCTURE.md`: menu graph modularization and interactive topology-lab workflow are closed; maintain drift watch only.
4. `docs/rds/RDS_FILE_FETCH_LIBRARY.md`: lifecycle/adaptive-fetch design baseline exists; implementation remains future-scoped.

## 4.1 Interactive Tutorials Plan (BKL-P3-013)

### Objective

Ship an in-game, step-driven tutorial system that:

1. Teaches movement in nD, rotation, camera control, and layer completion.
2. Works consistently across 2D, 3D, and 4D modes.
3. Is scriptable/data-driven, testable, and resilient to UI/input refactors.

### Scope

In-scope:

1. A tutorial engine (state machine + triggers + gating).
2. A data schema to define tutorial lessons (JSON/YAML).
3. Overlay UI: instruction panel, key prompts, highlights, ghost targets,
   progress indicator.
4. Interactive lessons:
   2D: move/rotate/drop + complete a line.
   3D: move in 3 axes, rotate in 3D, camera orbit/pan, complete a layer/plane.
   4D: move in 4 axes (or slice + axis select), rotate in 4D planes, camera +
   slice navigation, complete a hyper-layer (per runtime clearing definition).

Out-of-scope (this pack):

1. Full campaign/story mode.
2. Full localization framework implementation (leave hooks only).
3. Analytics backend (local event logging hooks only).

### Non-negotiable design constraints

1. Deterministic progression: steps advance only on explicit conditions.
2. No hard-coded lesson logic beyond generic triggers/conditions; lessons are data.
3. Input gating per step: allowed actions constrained; disallowed actions ignored
   (optional user feedback).
4. Skippable and restartable at any time.
5. Mode-agnostic core: 2D/3D/4D are content packs, not separate implementations.
6. Deterministic tutorial start contract:
   first step starts with a curated asymmetric piece, full visibility at least
   two gravity layers below top, and deterministic 1-2 seeded bottom layers.

### Context requirements (Codex router)

1. Code context: input handling, game loop/update, UI rendering, camera controls,
   piece transforms, line/layer clear logic.
2. Docs context: control scheme documentation, gameplay definitions for layer in
   3D/4D, UX conventions.
3. Config context: keybind mappings, settings flags, UI theme tokens.
4. Runtime context: tutorial event logs, step transitions, replay traces.
5. Git context: diff scope + feature branch hygiene.
6. Planning context: acceptance criteria + stop conditions.

### Deliverables

D1. Tutorial engine (core):

1. Load lesson definitions (JSON/YAML).
2. Maintain `(lesson_id, step_id)` state.
3. Evaluate conditions and triggers.
4. Enforce input gating.
5. Emit events:
   `step_started`, `hint_shown`, `condition_met`, `step_completed`,
   `lesson_completed`, `lesson_skipped`.

Implementation shape:

1. `TutorialManager` service.
2. `Step` definition with:
   `instruction_text`, optional `hint_text`,
   `allowed_actions`/`blocked_actions`,
   `on_enter` hooks (spawn target, camera preset, fixed seed),
   `completion_conditions`,
   `timeout_hint_seconds` (optional).

Condition system:

1. Event predicates: action performed, rotation plane used, camera moved.
2. World predicates: piece position/orientation, layer cleared, target cell filled.
3. Composite predicates: AND/OR DSL.

D2. Tutorial content schema (data-driven):

Schema requirements:

1. Versioned (`schema_version`).
2. Validatable (unit tests + JSON schema where used).

Minimum fields:

1. `lesson_id`, `title`, `mode` (`2d|3d|4d`).
2. `steps[]` with:
   `id`,
   `ui: {text, hint, highlights[], key_prompts[]}`,
   `gating: {allow[], deny[]}`,
   `setup: {camera_preset?, spawn_piece?, board_preset?, rng_seed?}`,
   `complete_when: {events[], predicates[], logic}`,
   optional `fail_when`.

D3. Tutorial UI overlay:

UI elements:

1. Instruction panel (top/side).
2. Contextual key prompts (from keybind config).
3. Highlight system:
   piece/axes gizmo/target cells/camera widget.
4. Progress indicator (step X/Y).
5. Skip/restart controls (also accessible from pause menu).

Hard constraint:

1. UI depends on tutorial state + highlight descriptors only, not renderer internals.

### Tutorial curriculum (content packs)

Pack A: 2D tutorial (short, canonical)

Lesson A1 Movement:

1. Move left/right to marked columns.
2. Soft drop vs hard drop.
3. Hold (if supported) + next-preview explanation (non-blocking).

Lesson A2 Rotation:

1. Rotate CW/CCW.
2. Wall-kick demonstration (if supported).

Lesson A3 Clear a line:

1. Place piece to complete a nearly-finished line.
2. Clear confirmation + brief scoring explanation.

Definition of done (Pack A):

1. New player can complete a line in under two minutes without external docs.

Pack B: 3D tutorial

Lesson B1 Camera control:

1. Orbit.
2. Pan.
3. Zoom + reset view.

Lesson B2 Movement in 3 axes:

1. X/Y move (screen plane).
2. Z move (depth).
3. Layer/slice explanation if applicable.

Lesson B3 3D rotations:

1. Rotate around X/Y/Z (or equivalent mapping).
2. Demonstrate supported reference frame (camera-relative or world-relative).

Lesson B4 Clear a layer:

1. Complete a plane with constrained placement.
2. Show clear animation + resulting board state.

Definition of done (Pack B):

1. Player demonstrates camera orbit, depth move, one rotation, one plane clear.

Pack C: 4D tutorial

Lesson C1 Understanding slices:

1. W-slice concept.
2. Slice navigation (`W-`/`W+` or equivalent).
3. Active-slice indicator behavior.

Lesson C2 Movement in 4 axes:

1. Move in visible plane.
2. Move along W (or equivalent abstraction).
3. Confirm cross-slice placement.

Lesson C3 4D rotations (plane-based):

1. Rotate in visible 3D subspace.
2. Rotate involving W planes (`XW`/`YW`/`ZW` or equivalent).
3. Teach rotation-plane selection UX.

Lesson C4 Clear a hyper-layer:

1. Start from near-complete deterministic preset.
2. Complete with constrained placement.
3. Show clear + scoring explanation.

Definition of done (Pack C):

1. Player demonstrates slice navigation, one W-plane rotation, one hyper-layer clear.

### Sequencing plan (milestones)

M0 Spec + interfaces (planning only):

1. Formalize layer completion definitions in 3D and 4D.
2. Formalize canonical action list (`MoveX+`, `RotatePlaneXY`, `SliceW+`, etc.).
3. Define tutorial schema v1.

Acceptance:

1. One source of truth for actions + clearing definitions.

Stop condition:

1. Schema + action list reviewed once; no feature creep.

M1 Tutorial core engine:

1. Implement `TutorialManager`.
2. Implement condition evaluation.
3. Implement input gating at dispatch layer.
4. Implement persistence (last completed lesson + resume flag).

Acceptance:

1. Dummy three-step lesson advances deterministically and gating works.

Stop condition:

1. No UI polish beyond minimal debug text.

M2 Overlay UI + highlight system:

1. Instruction panel + key prompts from keybind config.
2. Render highlight descriptors.
3. Implement skip/restart lesson controls.

Acceptance:

1. Any step can render text + highlight + prompts without game-logic changes.

Stop condition:

1. No animation polish beyond basic clarity.

M3 Content Pack A (2D):

1. Author lesson content files.
2. Add deterministic line-clear presets.
3. Add lesson-file validation tests.

Acceptance:

1. Pack A completes end-to-end with no dead steps.

M4 Content Pack B (3D):

1. Author measurable camera steps.
2. Author movement + rotation steps with gating.
3. Add 3D plane-clear preset.

Acceptance:

1. Pack B stable across different keybinds.

M5 Content Pack C (4D):

1. Author slice-navigation steps.
2. Author rotation-plane selection steps with explicit events.
3. Add hyper-layer clear preset.

Acceptance:

1. Pack C stable end-to-end without accidental-behavior dependency.

M6 QA + regression harness:

1. Add tutorial replay mode (scripted inputs -> assert transitions).
2. Add static validation (schema, key prompt coverage, highlight coverage).
3. Add runtime tutorial event log export (last 200 events).

Acceptance:

1. Tutorial packs pass automated replay for at least one canonical keymap.

### File/module layout (recommended)

1. `tutorial/`
   `manager.py`
   `schema.py`
   `conditions.py`
   `gating.py`
   `events.py`
2. `tutorial/content/`
   `2d_pack.yaml`
   `3d_pack.yaml`
   `4d_pack.yaml`
3. `ui/tutorial_overlay.*`
4. `tests/tutorial/`
   `test_schema_validation.py`
   `test_step_transitions.py`

### Global acceptance criteria (release gate)

1. Tutorials work in 2D/3D/4D without per-pack code changes.
2. Every step defines completion conditions, gating set, and visible instruction.
3. No softlocks: skip and restart always recover to known state.
4. Deterministic clear presets for line/plane/hyper-layer lessons.

### Global stop conditions (anti-scope-creep)

1. Do not expand into advanced strategy coaching.
2. Do not add new control schemes; reflect existing actions only.
3. Do not add cinematic tutorial sequences; keep interactive and fast.

## 5. Change Footprint (Current Batch)

Current sub-batch (2026-03-04): CI compliance hardening + governance preflight.

- Stabilized sanitation inputs for local/context artifacts:
  - `.gitignore` now ignores `context-*.instructions.md`
  - `scripts/check_git_sanitation_repo.sh` now excludes `context-*.instructions.md`
- Added single-command CI preflight:
  - `scripts/ci_preflight.sh`
  - runs sanitation/policy checks + canonical `ci_check` pipeline.
- Added policy-manifest literal safety validation to catch string literals that
  can accidentally trigger absolute-path sanitation gates:
  - `tools/governance/validate_project_contracts.py`
  - `tests/unit/governance/test_governance_validate_project_contracts.py`
- Tuned wheel-reuse rule scopes to reduce low-signal noise while keeping
  high-risk runtime/UI/governance coverage:
  - `config/project/policy/manifests/wheel_reuse_rules.json`
- Added CI compliance runbook and wired it into canonical governance docs:
  - `docs/policies/CI_COMPLIANCE_RUNBOOK.md`
  - `docs/policies/INDEX.md`
  - `docs/RDS_AND_CODEX.md`
  - `CONTRIBUTING.md`
- Synced canonical maintenance contract for new script/doc tokens:
  - `config/project/policy/manifests/canonical_maintenance.json`

Tuned next-batch priorities:
1. CI compliance maintenance first (preflight + runbook triage discipline).
2. Tutorial stability closure for 4D/W-axis and step-transition edge-cases.
3. LOC-focused non-behavioral dedup in runtime/UI hotspots.

Current sub-batch (2026-03-04): directive-manifest normalization.

- Added canonical contributor directives manifest:
  - `config/project/policy/manifests/contributor_directives.json`
- Registered contributor directives in policy pack and policy contract map:
  - `config/project/policy/pack.json`
  - `config/project/policy/manifests/project_policy.json`
- Added contributor directives manifest to canonical maintenance required governance files:
  - `config/project/policy/manifests/canonical_maintenance.json`
- Added explicit validation for contributor directive manifest schema/IDs/content:
  - `tools/governance/validate_project_contracts.py`
- Synced instruction docs to reference the canonical contributor directives manifest:
  - `AGENTS.md`
  - `docs/RDS_AND_CODEX.md`
- Follow-up LOC reduction pass:
  - reduced duplicate governance bullets in `AGENTS.md` by deferring to manifest/policy sources
  - reduced contributor-manifest overlap with policy docs (process-only directives retained)
  - collapsed contributor-directive validation helpers into compact validation flow
  - added risk-gates manifest + checker coverage for CI-enforced directives,
    dependency policy (`pip check` + blocked dependency list), and sensitive-file
    ownership thresholds:
    - `config/project/policy/manifests/risk_gates.json`
    - `tools/governance/check_risk_gates.py`
    - `scripts/verify.sh`
  - added policy-index drift enforcement so `docs/policies/INDEX.md` must stay in
    sync with policy IDs and contract paths declared in
    `config/project/policy/manifests/project_policy.json`:
    - `tools/governance/validate_project_contracts.py`
    - `config/project/policy/manifests/canonical_maintenance.json`
    - `docs/policies/INDEX.md`
  - added menu-simplification manifest enforcement:
    - validates that shared gameplay controls (`game_seed`,
      `game_random_mode`, `game_topology_advanced`, `gameplay_advanced`) are
      present in `settings_hub_layout_rows` and not duplicated in
      per-dimension `setup_fields`.
    - `tools/governance/validate_project_contracts.py`
  - hardened risk-gates security/dependency posture:
    - blocked dependency denylist now includes `pycrypto` and `python-jose`
    - security ownership scope is no longer no-op; it now requires a minimum
      matched sensitive-file set (`min_sensitive_files`) before pass.
    - `config/project/policy/manifests/risk_gates.json`
    - `tools/governance/check_risk_gates.py`
  - added runtime policy checker for two previously review-only policies:
    - string sanitation checks on text-entrypoint modules
    - no-magic-number checks for config-backed settings controls
    - `config/project/policy/manifests/policy_runtime_rules.json`
    - `tools/governance/check_policy_runtime_rules.py`
    - `scripts/verify.sh`
  - generalized no-reinventing-wheel enforcement:
    - new manifest-driven reuse rules that detect ad-hoc replacement code for
      stdlib/repo helpers and require explicit `Wheel Exception:` markers when
      deviations are intentional.
    - rules are now category-based (parsing/validation, normalization, path/config,
      algorithm utilities) rather than a bool-parser-specific example.
    - `config/project/policy/manifests/wheel_reuse_rules.json`
    - `tools/governance/check_wheel_reuse_rules.py`
  - converted LOC reduction into soft non-blocking guidance:
    - warning-only per-bucket LOC pressure report (batch-type aware), wired into
    verify for visibility without blocking important work.
    - `config/project/policy/manifests/loc_guidance.json`
    - `tools/governance/check_loc_guidance.py`
  - added dedup/dead-code contract gate:
    - legacy path reintroduction checks
    - TODO/FIXME backlog-ID linkage checks
    - duplicate governance helper-body detection in scoped paths
    - `config/project/policy/manifests/dedup_dead_code_rules.json`
    - `tools/governance/check_dedup_dead_code_rules.py`
  - upgraded security ownership to phased strictness:
    - keep blocking threshold at `min_distinct_authors_per_file`
    - add non-blocking warning target (`target_min_distinct_authors_per_file`)
      for gradual bus-factor improvement without CI breakage.
    - `config/project/policy/manifests/risk_gates.json`
    - `tools/governance/check_risk_gates.py`
  - extended wheel-reuse checker with AST-assisted detectors (not regex-only)
    for common reinvention patterns (`custom_bool_parser`,
    `custom_numeric_text_parser`, `custom_clamp_helper`).

Current sub-batch (2026-03-04): governance-doc cleanup and directive dedup.

- Replaced oversized duplicated instruction content in `docs/RDS_AND_CODEX.md`
  with a compact canonical workflow that references policy manifests, policy docs,
  RDS specs, and checkpoint docs (`CURRENT_STATE.md`, `docs/BACKLOG.md`).
- Removed historical stage-by-stage migration directives from `docs/RDS_AND_CODEX.md`
  and set explicit scope boundary: stage history belongs in this backlog + current-state handoff.
- Preserved required contract anchors (`RDS index`, `Testing instructions`,
  `docs/BACKLOG.md`, `docs/rds/RDS_PACKAGING.md`) while reducing duplicate policy text.

Current sub-batch (2026-03-04): tutorial timing regression coverage + runtime dedup.

- Added tutorial runtime regression coverage for two active risks:
  - configured stage-delay gating enforcement before transition
  - ordered 4D W-axis stage progression (`move_w_neg` -> `move_w_pos`)
  - `tests/unit/engine/test_tutorial_runtime.py`
- Reduced duplicated runtime settings persistence/update plumbing by introducing
  a shared section saver in:
  - `src/tet4d/engine/runtime/menu_settings_state.py`
- Reduced API/keybindings wrapper duplication with proxy/alias consolidation in:
  - `src/tet4d/engine/api.py`
  - `src/tet4d/ui/pygame/keybindings.py`
- Verification:
  - `.venv/bin/pytest -q tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_tutorial_setup_apply.py tests/unit/engine/test_tutorial_content.py` passed.
  - `.venv/bin/pytest -q tests/unit/engine/test_keybindings.py tests/unit/engine/test_engine_api_determinism.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-04): tutorial control sequencing hardening.

- Added deterministic tutorial sequencing coverage for restart/redo/previous/next
  controls across all lesson modes (2D/3D/4D):
  - `tests/unit/engine/test_tutorial_runtime.py`
- Added repeated 4D W-axis progression smoke across lesson restarts to guard
  against recurrence of W-stage stalls:
  - `tests/unit/engine/test_tutorial_runtime.py`
- Added nonzero stage-delay regression coverage (`1500ms`) to ensure no
  premature transitions:
  - `tests/unit/engine/test_tutorial_runtime.py`
- Added live system-control keybinding prompt sync coverage in tutorial overlay:
  - `tests/unit/engine/test_tutorial_overlay.py`
- Reduced duplicate profile and per-mode update plumbing in:
  - `src/tet4d/ui/pygame/keybindings.py`
  - `src/tet4d/engine/runtime/menu_settings_state.py`
- Verification:
  - `.venv/bin/pytest -q tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_tutorial_overlay.py` passed.
  - `.venv/bin/pytest -q tests/unit/engine/test_keybindings.py tests/unit/engine/test_menu_policy.py tests/unit/engine/test_runtime_config.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.
  - `./scripts/ci_preflight.sh` passed (known non-blocking local warnings unchanged).

Current sub-batch (2026-03-03): scoring clear-size weighting (square-root).

- Added config-backed clear-size weighting so larger cleared layers award higher
  clear points with square-root scaling (`sqrt(layer_size/reference)`, floor `1.0`):
  - `config/gameplay/tuning.json` (`clear_scoring.layer_size_weighting`)
  - `src/tet4d/engine/runtime/runtime_config_validation_gameplay.py`
  - `src/tet4d/engine/runtime/runtime_config.py`
  - `src/tet4d/engine/gameplay/scoring_bonus.py`
  - `src/tet4d/engine/gameplay/game2d.py`
  - `src/tet4d/engine/gameplay/game_nd.py`
- Added regression coverage and runtime-config assertions:
  - `tests/unit/engine/test_scoring_bonus.py`
  - `tests/unit/engine/test_runtime_config.py`
- Updated scoring help text to reflect clear-size weighting:
  - `config/help/content/runtime_help_content.json`
  - `docs/rds/RDS_TETRIS_GENERAL.md`

Current sub-batch (2026-03-02): interactive tutorial runtime integration (M2-M6 baseline).

- Added tutorial runtime state layer with deterministic progression hooks and
  persistence of started/completed lessons:
  - `src/tet4d/engine/tutorial/runtime.py`
  - `src/tet4d/engine/tutorial/persistence.py`
  - `config/project/io_paths.json` (`tutorial_progress_file_default`)
  - `src/tet4d/engine/runtime/project_config.py`
- Extended API surface to expose tutorial runtime session helpers to UI loops:
  - `src/tet4d/engine/api.py`
- Added launcher tutorial selector and wired Play -> Tutorials route to launch
  guided runs for 2D/3D/4D:
  - `src/tet4d/ui/pygame/launch/tutorials_menu.py`
  - `cli/front.py`
  - `src/tet4d/ui/pygame/launch/launcher_play.py`
- Integrated tutorial gating/event observation/step progression into gameplay loops:
  - `cli/front2d.py`
  - `src/tet4d/engine/frontend_nd.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
- Added tutorial in-game overlay renderer (instruction + key prompts + progress):
  - `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`
- Added canonical non-Python tutorial plan config:
  - `config/tutorial/plan.json`
  - `config/schema/tutorial_plan.schema.json`
  - `src/tet4d/engine/tutorial/content.py` loader/validator + cache
  - `src/tet4d/engine/api.py` runtime accessor (`tutorial_plan_payload_runtime`)
- Tightened runtime tutorial behavior contract:
  - step-pause enforcement now freezes gravity/bot tick while tutorial is running
  - tutorial stages now auto-redo if no currently legal stage action exists
    (prevents dead-end game-over states during gated steps)
  - active tutorial piece visibility is re-enforced at runtime; if visibility
    cannot be restored deterministically, tutorial session restarts
  - tutorial mode clamps board dimensions to configured minimums (2D/3D/4D)
    before session start to avoid invalid spawn/setup states
  - full-clear bonus stages now use deterministic one-piece board-clear presets:
    - `2d_almost_full_clear_o` + starter `O`
    - `3d_almost_full_clear_o3` + starter `O3`
    - `4d_almost_full_clear_cross4` + starter `CROSS4`
  - gameplay Esc now routes to menu/pause flow instead of instant quit
  - gameplay restart action no longer resets tutorial lesson to step 1
  - leaderboard registration is disabled during tutorial sessions
  - clear-step board presets (`2d_almost_line`, `3d_almost_layer`, `4d_almost_hyper_layer`)
    are applied deterministically
  - tutorial camera presets (`tutorial_3d_default`, `tutorial_4d_default`) are now
    applied by loop adapters
  - pause menu tutorial control is now hotkey-driven (no dedicated
    `tutorial_restart` row in pause menu)
  - tutorial pause/menu copy now exposes explicit tutorial exit wording
    (`Exit Tutorial`)
  - tutorial restart stability hardened:
    - pause-menu restart now emits tutorial `restart` action
    - tutorial `F9` now restarts the tutorial lesson session deterministically
      and reapplies step setup
    - visibility recovery now redoes the current step (instead of restarting the
      full lesson), reducing cross-step instability
  - 3D/4D move+rotate stages now force asymmetric starters (`SCREW3`/`SKEW4_A`)
  - 3D/4D layer-clear presets now use deterministic solvable hole patterns:
    - `3d_almost_layer_screw3`
    - `4d_almost_hyper_layer_skew4`
  - tutorial stage pacing increased (movement/rotation/drop delays) via
    config-backed constants
  - lesson packs now require full movement/rotation/camera action completion per mode
  - tutorial lesson segmentation and ordering were clarified and canonicalized:
    - translations
    - piece rotations
    - camera rotations (3D/4D)
    - camera controls (`toggle_grid`, transparency)
    - goals (target clear, line/layer clear, full board clear)
  - interactive system-control tutorial stages (`menu_button`, `help_button`,
    `restart_button`) were removed; controls are now guidance-only in overlay copy
  - movement and rotation stages now require 4 successful actions per direction
  - full-board clean stages now require `board_cleared` predicate in addition to
    clear-event predicates
  - tutorial overlay panel moved to enlarged left-side layout with clearer
    `Segment` + `Task` + `KEY/ACTION` formatting
  - files:
    - `config/tutorial/lessons.json`
    - `config/project/constants.json`
    - `config/menu/structure.json`
    - `src/tet4d/engine/tutorial/setup_apply.py`
    - `src/tet4d/engine/tutorial/runtime.py`
    - `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`
    - `src/tet4d/ui/pygame/front3d_game.py`
    - `src/tet4d/ui/pygame/front4d_game.py`
    - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
    - `src/tet4d/ui/pygame/runtime_ui/pause_menu.py`
    - `cli/front2d.py`
- Added regression coverage for tutorial runtime and new routing callbacks:
  - `tests/unit/engine/test_tutorial_runtime.py`
  - `tests/unit/engine/test_nd_routing.py`
  - `tests/unit/engine/test_front_launcher_routes.py`

Current sub-batch (2026-03-02): interactive tutorial core scaffolding (M0/M1 seed).

- Added canonical tutorial lesson-pack data source:
  - `config/tutorial/lessons.json`
- Added tutorial data schema contract:
  - `config/schema/tutorial_lessons.schema.json`
- Added tutorial core package with deterministic schema parsing, gating, condition
  evaluation, and step-state manager:
  - `src/tet4d/engine/tutorial/schema.py`
  - `src/tet4d/engine/tutorial/content.py`
  - `src/tet4d/engine/tutorial/gating.py`
  - `src/tet4d/engine/tutorial/conditions.py`
  - `src/tet4d/engine/tutorial/events.py`
  - `src/tet4d/engine/tutorial/manager.py`
  - `src/tet4d/engine/tutorial/__init__.py`
- Exposed tutorial content runtime accessors via engine API:
  - `src/tet4d/engine/api.py`
- Added unit coverage for schema validation, manager progression/gating, and
  runtime content loading/API exposure:
  - `tests/unit/engine/test_tutorial_schema.py`
  - `tests/unit/engine/test_tutorial_manager.py`
  - `tests/unit/engine/test_tutorial_content.py`
- Canonical maintenance sync:
  - `config/project/policy/manifests/canonical_maintenance.json`
- RDS/project-structure sync:
  - `docs/rds/RDS_TETRIS_GENERAL.md`
  - `docs/PROJECT_STRUCTURE.md`

Current sub-batch (2026-03-02): runtime parser/validation decomposition continuation.

- Reduced duplicate menu-structure parsing logic by extracting shared helpers to:
  - `src/tet4d/engine/runtime/menu_structure_parse_helpers.py`
- Extracted shared menu-graph traversal/collection helpers to:
  - `src/tet4d/engine/runtime/menu_structure_graph.py`
- Simplified `menu_structure_schema` by removing duplicate local parsers and
  consuming shared helpers for:
  - mode string-list parsing
  - copy-field parsing
  - `ui_copy` section parsing
  - menu reachability/action/route collection
- Reduced `runtime_config.py` validator concentration by extracting gameplay/audio
  payload validation to:
  - `src/tet4d/engine/runtime/runtime_config_validation_gameplay.py`
- Updated `runtime_config.py` to delegate to extracted gameplay/audio validators.
- Verification:
  - `.venv/bin/pytest -q tests/unit/engine/test_menu_policy.py tests/unit/engine/test_runtime_config.py tests/unit/engine/test_project_config.py`
  - `CODEX_MODE=1 ./scripts/verify.sh`

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

Current sub-batch (2026-03-03): tutorial control-flow hardening (Esc-back, stage redo, paced input).

- Added stage-local redo control (`F7`) without full lesson reset:
  - `src/tet4d/engine/tutorial/manager.py`
  - `src/tet4d/engine/tutorial/runtime.py`
  - `src/tet4d/engine/api.py`
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
  - `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`
- Enforced menu/help back semantics via Esc-only return event (`menu_back`) for tutorial progression:
  - `src/tet4d/ui/pygame/runtime_ui/help_menu.py`
  - `src/tet4d/ui/pygame/runtime_ui/pause_menu.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
  - `cli/front2d.py`
  - `config/tutorial/lessons.json`
- Tightened stage success criteria for board-goal steps:
  - `config/tutorial/lessons.json` (`target_drop` now requires clear predicates)
- Enforced visible active-piece placement at every tutorial step setup apply:
  - `src/tet4d/engine/tutorial/setup_apply.py`
- Added config-backed tutorial action pacing (movement/rotation/drop delays):
  - `config/project/constants.json`
  - `src/tet4d/engine/runtime/project_config.py`
- Verification:
  - targeted tutorial suites passed
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-03): tutorial/menu flow consolidation (root Tutorials route, stage navigation, free-play handoff).

- Moved tutorial entrypoint to launcher root and removed pause-menu tutorial exit action:
  - `config/menu/structure.json`
  - `tests/unit/engine/test_menu_policy.py`
  - `tests/unit/engine/test_pause_menu.py`
- Tutorial launch now bypasses per-mode setup menus and starts from deterministic lesson presets:
  - `src/tet4d/ui/pygame/launch/launcher_play.py`
- Added tutorial stage navigation controls (`F5` previous, `F6` next) and
  preserved existing `F7` redo, `F8` main-menu exit, `F9` lesson restart:
  - `src/tet4d/engine/api.py`
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
  - `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`
- Tutorial end now transitions cleanly into free play by dropping completed
  tutorial session state in active loops:
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
- Hardened 4D W-move tutorial setup solvability and added regression coverage:
  - `src/tet4d/engine/tutorial/setup_apply.py`
  - `tests/unit/engine/test_tutorial_setup_apply.py`
- Clarified 2D drop-phase instruction wording (precision drop vs line clear):
  - `config/tutorial/lessons.json`
- Enforced menu back parity for `Backspace` with `Esc`:
  - `src/tet4d/ui/pygame/menu/menu_runner.py`
  - `src/tet4d/ui/pygame/menu/menu_controls.py`
  - `src/tet4d/ui/pygame/menu/keybindings_menu.py`
- Verification:
  - `PYTHONPATH=src .venv/bin/pytest -q tests/unit/engine/test_tutorial_setup_apply.py tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_menu_policy.py tests/unit/engine/test_pause_menu.py tests/unit/engine/test_front_launcher_routes.py tests/unit/engine/test_nd_routing.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-03): tutorial camera/transparency UX alignment + stage-stability hardening.

- Unified helper-panel control taxonomy with camera/transparency parity:
  - moved `grid mode` into camera panel and exposed camera panel in 2D
  - added transparency meter bar (`Locked-cell transparency`) to 2D/3D/4D side panels
  - files:
    - `config/help/layout/runtime_help_action_layout.json`
    - `src/tet4d/ui/pygame/render/control_helper.py`
    - `src/tet4d/ui/pygame/render/gfx_panel_2d.py`
    - `src/tet4d/ui/pygame/render/gfx_game.py`
    - `src/tet4d/engine/front3d_render.py`
    - `src/tet4d/engine/front4d_render.py`
    - `tests/unit/engine/test_control_ui_helpers.py`
- Tutorial runtime pacing/stability updates:
  - added config-backed `>=1s` step transition hold
  - added transparency target-range progression predicate with per-step randomized target in `20%-80%`
  - enabled `soft_drop` as always-allowed tutorial action
  - passed overlay/grid runtime predicates into tutorial progression for 2D/3D/4D loops
  - files:
    - `config/project/constants.json`
    - `src/tet4d/engine/runtime/project_config.py`
    - `src/tet4d/engine/tutorial/manager.py`
    - `src/tet4d/engine/tutorial/runtime.py`
    - `src/tet4d/engine/api.py`
    - `cli/front2d.py`
    - `src/tet4d/ui/pygame/front3d_game.py`
    - `src/tet4d/ui/pygame/front4d_game.py`
- Tutorial content updates:
  - 4D movement stages now require double action count (`event_count_required=2`)
  - layer-fill and full-clear goal steps now accept `toggle_grid` and require `grid_enabled`
  - transparency stages now require target-range predicate completion
  - file:
    - `config/tutorial/lessons.json`
- Removed `Restart Tutorial` from pause menu action graph:
  - `config/menu/structure.json`
  - `src/tet4d/engine/ui_logic/menu_action_contracts.py`
  - `src/tet4d/ui/pygame/runtime_ui/pause_menu.py`
  - `tests/unit/engine/test_pause_menu.py`
- Verification:
  - `PYTHONPATH=src pytest -q tests/unit/engine/test_control_ui_helpers.py tests/unit/engine/test_tutorial_content.py tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_pause_menu.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

## 6. Source Inputs

1. `config/project/backlog_debt.json`
2. `scripts/arch_metrics.py`
3. `config/project/policy/manifests/tech_debt_budgets.json`
4. `docs/rds/*.md`
5. `docs/ARCHITECTURE_CONTRACT.md`
6. `CURRENT_STATE.md`
7. `docs/history/DONE_SUMMARIES.md`
