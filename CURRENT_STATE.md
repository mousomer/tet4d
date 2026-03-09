# CURRENT_STATE (Restart Handoff)

Last updated: 2026-03-09  
Branch: `codex/explorer-topology-live`  
Worktree expectation: dirty only when an active batch is in progress

## Purpose

This file is the restart handoff for the current architecture baseline. It is
not a historical ledger. Long historical migration detail belongs in
`docs/history/DONE_SUMMARIES.md`.

Sections with `BEGIN/END GENERATED:*` markers are maintained by
`tools/governance/generate_maintenance_docs.py`.

<!-- BEGIN GENERATED:current_state_architecture_snapshot -->
## Current Architecture Snapshot

- `arch_stage`: `900`
- Canonical local gate: `CODEX_MODE=1 ./scripts/verify.sh`
- CI wrapper: `./scripts/ci_check.sh`
- Full local gate runs are serialized by `scripts/verify.sh`, use an isolated per-run state root via `TET4D_STATE_ROOT` when no explicit override is provided, and include the CI sanitation/policy checks (`scripts/check_policy_compliance.sh`, `scripts/check_policy_compliance_repo.sh`, `scripts/check_git_sanitation_repo.sh`) so local verification matches GitHub policy enforcement.
- Dependency direction:
  - `ui`, `ai`, `replay`, and `tools` may import engine modules directly
  - `engine` must not import `ui`, `ai`, `replay`, or `tools`
  - `engine/core` remains strict-pure
<!-- END GENERATED:current_state_architecture_snapshot -->

<!-- BEGIN GENERATED:current_state_metric_snapshot -->
## Current Metric Snapshot

From `python scripts/arch_metrics.py`:

- `deep_imports.engine_to_ui_non_api.count = 0`
- `deep_imports.engine_to_ai_non_api.count = 0`
- `deep_imports.ui_to_engine_non_api.count = 147` (allowed under current rule)
- `deep_imports.ai_to_engine_non_api.count = 26` (allowed under current rule)
- `engine_core_purity.violation_count = 0`
- `migration_debt_signals.pygame_imports_non_test.count = 0`
- `tech_debt.score = 2.39` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 1.55`
2. `code_balance = 0.84`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_canonical_ownership -->
## Canonical Ownership After This Batch

### Engine

- `src/tet4d/engine/core/piece_transform.py`
- `src/tet4d/engine/core/rotation_kicks.py`
- `src/tet4d/engine/core/rules/lifecycle.py`
- `src/tet4d/engine/topology_explorer/*`
- `src/tet4d/engine/gameplay/*`
- `src/tet4d/engine/gameplay/api.py`
- `src/tet4d/engine/runtime/*`
- `src/tet4d/engine/runtime/api.py`
- `src/tet4d/engine/tutorial/*`
- `src/tet4d/engine/tutorial/api.py`
- `src/tet4d/engine/api.py (small compatibility facade for replay/tests/tutorial payload exports)`

### UI

- `src/tet4d/ui/pygame/front2d_game.py`
- `src/tet4d/ui/pygame/front2d_setup.py`
- `src/tet4d/ui/pygame/front2d_loop.py`
- `src/tet4d/ui/pygame/front2d_session.py`
- `src/tet4d/ui/pygame/front2d_frame.py`
- `src/tet4d/ui/pygame/front2d_results.py`
- `src/tet4d/ui/pygame/frontend_nd_setup.py`
- `src/tet4d/ui/pygame/frontend_nd_state.py`
- `src/tet4d/ui/pygame/frontend_nd_input.py`
- `src/tet4d/ui/pygame/front3d_game.py`
- `src/tet4d/ui/pygame/front4d_game.py`
- `src/tet4d/ui/pygame/front3d_render.py`
- `src/tet4d/ui/pygame/front4d_render.py`
- `src/tet4d/ui/pygame/topology_lab/*`
- `src/tet4d/ui/pygame/runtime_ui/*`
- `src/tet4d/ui/pygame/menu/*`
- `src/tet4d/ui/pygame/launch/* (with settings_hub_model.py owning settings model/layout, settings_hub_actions.py owning settings mutations/text-entry, and launcher_settings.py owning orchestration/view)`
- `src/tet4d/ui/pygame/render/*`

### AI

- `src/tet4d/ai/playbot/*`
<!-- END GENERATED:current_state_canonical_ownership -->

## Transform Ownership Note

- The requested piece-transform extraction plan is already complete in code.
- Canonical owner: `src/tet4d/engine/core/piece_transform.py`.
- Retrospective plan/inventory docs now exist at:
  - `docs/plans/piece_transform_extraction.md`
  - `docs/plans/piece_transform_inventory.md`
- Current `HEAD` has already progressed beyond the original extraction-stage
  non-goal and now uses center-of-piece block rotation semantics.

## What This Batch Changed

1. Folded 2D into the shared `src/tet4d/ui/pygame/` frontend structure and split
   ownership into `front2d_game.py` (orchestration), `front2d_setup.py`
   (setup/menu), `front2d_loop.py` (runtime orchestration), `front2d_session.py`
   (session/state), `front2d_frame.py` (per-frame/update), and
   `front2d_results.py` (results/leaderboard flow).
2. Moved engine-owned render/frontend adapters out of `src/tet4d/engine/` into
   UI ownership.
3. Removed all remaining reverse imports from `engine` into `ui` and `ai`.
4. Decomposed engine-owned convenience exports into
   `src/tet4d/engine/gameplay/api.py`, `src/tet4d/engine/runtime/api.py`, and
   `src/tet4d/engine/tutorial/api.py`, while keeping `src/tet4d/engine/api.py`
   as a thin compatibility facade.
5. Cut `menu_settings_state` -> UI keybinding side effects; live keybinding sync
   now happens in UI runtime/menu code.
6. Repointed AI planners/controllers/dry-run tooling to direct engine imports,
   eliminating `engine -> ai` wrapper pressure in `engine/api.py`.
7. Centralized shared rotation-with-kicks application through
   `resolve_rotated_piece(...)`, deleting duplicated first-fit application logic
   from 2D and ND gameplay states.
8. Zeroed the reverse-import metric budgets and aligned the boundary script with
   the current one-way rule.
9. Rewrote stale architecture docs so they describe the current architecture,
   not the old migration-only `engine.api` seam.
10. Moved remaining governance and render-benchmark callers off `engine.api` onto
    direct engine/UI owners, then reduced `src/tet4d/engine/api.py` to a small
    compatibility facade used mainly by replay and explicit compatibility tests.
11. Finished the 2D runtime decomposition by splitting `front2d_loop.py` into
    orchestration, session/state, frame/update, and results owners, then
    deleted `front2d_runtime.py` after migrating affected callers/tests.
12. Extracted the duplicated setup-menu event/save loop into
    `src/tet4d/ui/pygame/menu/setup_menu_runner.py` and rewired both 2D and ND
    setup flows to use it.
13. Removed duplicated settings/default wrappers from
    `src/tet4d/ui/pygame/launch/launcher_settings.py` by extending
    `src/tet4d/engine/runtime/menu_settings_state.py` and reusing
    `src/tet4d/engine/runtime/settings_schema.py` window-size helpers.
14. Finished ND frontend decomposition by splitting shared ND ownership into
    `frontend_nd_setup.py` (setup/menu/config), `frontend_nd_state.py`
    (state creation), and `frontend_nd_input.py` (gameplay/input routing), then
    deleted `frontend_nd.py`.
15. Finished settings-hub decomposition by splitting shared settings ownership
    into `settings_hub_model.py` (model/layout/defaults),
    `settings_hub_actions.py` (mutation/text-entry/save/reset), and
    `launcher_settings.py` (orchestration/view), then deleted
    `settings_hub_state.py`.
16. Split oversized engine-runtime helpers into stable facades plus smaller
    internal owners:
    - `menu_settings_state.py` over `runtime/menu_settings/`
    - `menu_structure_schema.py` over `runtime/menu_structure/`
    - `score_analyzer.py` over `runtime/score_analysis/`
17. Applied a correctness hotfix batch after the restructure: the settings hub
    now seeds analytics from persisted runtime state,
    `score_analysis_summary_snapshot()` returns detached copies, and the unused
    `dispatch_nd_gameplay_key()` helper was deleted from
    `frontend_nd_input.py`.
18. Hardened local verification against recurring Windows state collisions by
    adding a serialized `verify.sh` lock, a per-run `TET4D_STATE_ROOT` sandbox
    for full-gate runs, and env-aware pytest temp roots for Codex/local test
    helpers.
19. Converted `CURRENT_STATE.md` and `docs/PROJECT_STRUCTURE.md` to mixed
    manual/generated maintenance docs and added
    `tools/governance/generate_maintenance_docs.py` plus verify-time drift
    checks for the generated sections.
20. Added `docs/plans/cleanup_master_plan.md` as the canonical cleanup ledger and used code, not manifests, as the stage-status authority for the remaining dedup program.
21. Narrowed `src/tet4d/engine/api.py` by deleting raw piece-transform re-exports; replay/tests now consume stable engine contracts there while transform tests import the canonical kernel directly.
22. Extracted shared gameplay orchestration into `src/tet4d/engine/gameplay/lock_flow.py` (lock-analysis / score-bookkeeping) and `src/tet4d/engine/core/rules/lifecycle.py` (lock-and-respawn / hard-drop flow), then rewired `game2d.py`, `game_nd.py`, `core/rules/gravity_2d.py`, and `core/step/reducer.py` to consume those shared owners.
23. Moved keybinding path/profile/json ownership into `src/tet4d/engine/runtime/keybinding_store.py`; `src/tet4d/ui/pygame/keybindings.py` now owns runtime maps and rebinding behavior only.
24. Unified the install contract on editable install from `pyproject.toml`, removed `requirements.txt`, added `scripts/check_editable_install.sh`, and wired that smoke check into `scripts/verify.sh`.
25. Further thinned `src/tet4d/engine/runtime/menu_structure_schema.py` by moving menu graph parsing into `runtime/menu_structure/menu_parse.py` and settings/payload parsing into `runtime/menu_structure/settings_parse.py`, keeping `menu_structure_schema.py` as the stable validation facade only.
26. Reduced the fixed 4D tutorial board profile to `8 x 20 x 7 x 6` and the fixed 4D exploration board profile to `8 x 9 x 7 x 6`.
27. Unified tutorial instruction copy around one plain-language `Do this:` line, one optional `Tip:` line, and simpler `USE:` input prompts, with clearer layman wording across the 4D lesson pack.
28. Added larger dedicated 4D piece-set options (`True 4D (7-cell)` and `True 4D (8-cell)`) plus regression coverage for the new 4D bag families.
29. Added machine-checked drift protection via `config/project/policy/manifests/drift_protection.json`, `tools/governance/check_drift_protection.py`, a generated `Live Drift Watch` section in `CURRENT_STATE.md`, and verify-time enforcement of thin-wrapper LOC budgets plus tutorial copy taxonomy.
30. Fixed recurring GitHub CI parity drift by restoring the executable bit on `scripts/check_editable_install.sh` and teaching `scripts/check_git_sanitation_repo.sh` to fail if any direct-run shell entrypoint in the repo loses `100755` mode in git metadata.
31. Split Topology Lab topology ownership by gameplay mode (`normal` vs `explorer`) for 3D/4D, with engine-owned validation rejecting wrapped `Y` boundaries in Normal Game while Explorer Mode persists separate topology profiles and allows bidirectional vertical traversal.
32. Added explorer-only `move_up` / `move_down` keybinding groups and routing for 2D/3D/4D exploration, removed stale `move_y_*` gameplay naming from live help/control mappings, and hid 3D/4D topology-profile setup rows so advanced topology now flows through the mode-aware Topology Lab store.
33. Added a new engine-only explorer topology kernel under `src/tet4d/engine/topology_explorer/` covering general boundary gluing descriptors, signed-permutation transform validation, move-through-boundary mapping, movement-graph compilation, and basic quotient-topology presets without switching the live runtime/UI to the new model yet.
34. Added Stage 2 runtime-owned explorer topology integration: `topology_explorer_store.py` now owns JSON save/load for general explorer gluing profiles, `topology_explorer_bridge.py` converts the representable subset of legacy explorer edge-rule profiles into the new gluing model for preview/export, `topology_explorer_preview.py` compiles and exports movement-graph previews, and Topology Lab export now emits that explorer preview when the current explorer profile is representable as a true paired-boundary gluing.
35. Added `scripts/verify_focus.sh` as the documented fast-path staged local validation helper for focused lint/tests and maintenance-doc checks while keeping `./scripts/verify.sh` as the required pre-commit/pre-push gate.
36. Replaced the legacy edge-rule editor path for Explorer 2D, Explorer 3D, and Explorer 4D inside Topology Lab with direct general-gluing editors backed by `src/tet4d/engine/runtime/topology_explorer_store.py`, engine-owned explorer presets, and live sidebar previews compiled from the explorer movement graph; Normal Game remains on the legacy lab path in this phase.
37. Added engine-owned unsafe `Projective` / `Sphere` explorer preset families for 2D/3D/4D and surfaced them in Topology Lab with explicit `[unsafe]` labeling while keeping validation canonical in `src/tet4d/engine/topology_explorer/glue_validate.py`.
38. Routed live Explorer 2D gameplay/runtime through the general gluing engine by adding `src/tet4d/engine/gameplay/explorer_runtime_2d.py`, teaching `src/tet4d/engine/gameplay/game2d.py` to use `explorer_topology_profile` for explorer movement/collision/hard-drop behavior, and updating `src/tet4d/ui/pygame/front2d_setup.py` so advanced explorer setup loads stored gluing profiles while non-advanced explorer setup/export bridges legacy edge-rule selections into the same engine-owned explorer profile model.
39. Expanded explorer preview diagnostics so `src/tet4d/engine/runtime/topology_explorer_preview.py` now exports engine-owned tangent-basis arrow mappings for each gluing, and `src/tet4d/ui/pygame/launch/topology_lab_menu.py` renders those signed basis transforms in the live lab sidebar directly from the preview payload.
40. Relaxed the newer thin-wrapper drift budgets for `cli/front.py`, `src/tet4d/engine/api.py`, and `src/tet4d/ui/pygame/front2d_game.py`, and documented a contributor-process rule preferring medium-sized localized patches over ultra-narrow patch fragmentation while keeping the core architecture/purity gates unchanged.
40a. Clarified contributor edit-method selection so `apply_patch` is reserved for localized code edits with fresh context, while broad drifting maintenance-doc rewrites use one deterministic scripted rewrite instead of repeated patch retries.
40b. Hardened contributor write-safety and verification process rules: source-file rewrites now forbid multiline PowerShell `-replace` and BOM-producing writes, require a touched-file hygiene pass after non-patch rewrites, and explicitly ban parallel `verify.sh` / `ci_check.sh` runs.
40c. Tightened edit-method escalation so dirty/generated maintenance files skip patch-first behavior, and one rejected `apply_patch` attempt on a file is now the maximum before switching to a deterministic rewrite path.
41. Replaced the explorer Topology Lab's text-only right-hand sidebar with a scene-first graphical playground built from `src/tet4d/ui/pygame/topology_lab/scene3d.py`, `scene4d.py`, `transform_editor.py`, `preview.py`, and `arrow_overlay.py`, so explorer 2D/3D/4D topology editing now starts from the graphical explorer shell rather than from a detached editor panel.
42. Added engine-backed probe traversal support to the explorer lab via `advance_explorer_probe(...)` and `explorer_probe_options(...)` in `src/tet4d/engine/runtime/topology_explorer_preview.py`, and surfaced those controls in the same graphical explorer shell so seam edits, arrows, diagnostics, and movement feedback update in one coherent scene-first playground.
43. Completed the missing scene-first topology-lab owners under `src/tet4d/ui/pygame/topology_lab/` (`scene_state.py`, `explorer_tools.py`, `boundary_picker.py`, `scene2d.py`, `piece_sandbox.py`) and reduced `src/tet4d/ui/pygame/launch/topology_lab_menu.py` to orchestration over those owners.
44. Made seam arrows directly clickable in the explorer scene, added explicit probe path state plus reset behavior, and rendered scene-visible probe trace/sandbox status for Explorer 2D/3D/4D.
45. Added explorer-only sandbox and play-preview regression coverage, including direct Explorer 2D/3D/4D launch-from-draft checks and a sandbox guard that reports non-rigid seam-crossing failures explicitly instead of silently corrupting piece motion.
46. Added `src/tet4d/engine/runtime/topology_explorer_runtime.py` as the runtime-owned resolver/export facade for explorer setup and legacy-profile preview export, and migrated `front2d_setup.py`, `frontend_nd_setup.py`, and Topology Lab export to that runtime owner so the UI no longer imports the legacy edge-rule bridge directly.
47. Unified live Explorer launch with the same scene-first topology playground shell, so Explorer 2D/3D/4D now enter `run_explorer_playground(...)` directly and use bound explorer movement inside the probe/sandbox tools instead of a separate detached explorer frontend.

## Validation Status

Validation completed during this batch:

- focused cleanup slices covering `engine.api`, keybinding storage migration, and shared gameplay lifecycle/lock-flow helpers: passed
- focused `ruff check`: passed
- focused pytest batches covering the 2D split, compatibility facade, and shared kick-resolution paths: passed
- focused explorer-topology kernel tests (`test_topology_explorer.py`): passed
- focused 2D explorer runtime/setup tests (`test_game2d.py`, `test_front2d_setup.py`): passed
- `python scripts/arch_metrics.py`: passed with zero reverse imports
- `CODEX_MODE=1 ./scripts/verify.sh`: passed
- `CODEX_MODE=1 ./scripts/ci_check.sh`: passed

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy/manifests/drift_protection.json`.

Top 8 live Python hotspots by real LOC:

1. `scripts/arch_metrics.py`: `1869` real LOC
2. `src/tet4d/ui/pygame/launch/topology_lab_menu.py`: `1806` real LOC
3. `src/tet4d/engine/tutorial/setup_apply.py`: `1496` real LOC
4. `tools/governance/validate_project_contracts.py`: `1178` real LOC
5. `tools/governance/generate_configuration_reference.py`: `974` real LOC
6. `src/tet4d/ui/pygame/front4d_render.py`: `947` real LOC
7. `src/tet4d/engine/help_text.py`: `830` real LOC
8. `src/tet4d/ui/pygame/runtime_ui/help_menu.py`: `749` real LOC

Thin-wrapper budgets:

1. `cli/front.py: 684/840 real LOC (compatibility launcher wrapper)`
2. `cli/front2d.py: 15/24 real LOC (thin 2D launcher shim)`
3. `cli/front3d.py: 15/24 real LOC (thin 3D launcher shim)`
4. `cli/front4d.py: 15/24 real LOC (thin 4D launcher shim)`
5. `src/tet4d/engine/api.py: 91/160 real LOC (small engine compatibility facade)`
6. `src/tet4d/ui/pygame/front2d_game.py: 110/180 real LOC (2D orchestration entrypoint)`

Tutorial wording drift guard:

1. Lesson copy must not start with `Goal:` or `Action:`.
2. Tutorial overlay must keep `Do this:`, `Tip:`, and `USE:` tokens.
<!-- END GENERATED:current_state_drift_watch -->

## Next High-Value Follow-Ups

1. Keep trimming the runtime-engine facades (`menu_structure_schema.py`,
   `score_analyzer.py`, `menu_settings_state.py`) only if hotspot growth returns.
2. Watch `settings_hub_model.py` and `settings_hub_actions.py` for another split
   only if new feature work pushes them back into mixed responsibility.
3. Keep docs, budgets, generated references, and package manifests synchronized
   whenever ownership changes.
4. If more 2D/ND gameplay orchestration duplication remains after `lock_flow.py` and `core/rules/lifecycle.py`, extract only the next shared owner that produces net deletion.
5. Keep `engine.api` narrow and do not reintroduce raw transform or upper-layer
   convenience exports there.
6. Continue explorer topology by polishing the scene-first graphical explorer shell (especially richer 3D/4D picking/visualization), then delete the remaining legacy bridge once non-advanced explorer setup/export no longer depend on edge-rule conversion.

## Restart Checklist

1. `git branch --show-current`
2. `git status --short`
3. Read:
   - `AGENTS.md`
   - `docs/RDS_AND_CODEX.md`
   - `docs/ARCHITECTURE_CONTRACT.md`
   - `CURRENT_STATE.md`
4. Capture fresh metrics:

```bash
python scripts/arch_metrics.py
```

5. Re-run the local gate before commit:

```bash
CODEX_MODE=1 ./scripts/verify.sh
./scripts/ci_check.sh
```
