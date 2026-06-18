# Workflow For Codex And Contributors

This document explains how to apply the machine rules in
`config/project/policy_pack.json`.

## Workflow authority

- Machine-readable governance authority: `config/project/policy_pack.json`
- Thin dispatch file: `AGENTS.md`
- Governance router: `docs/governance/README.md`
- Human workflow explainer: `docs/WORKFLOW_CODEX.md`
- Restart handoff only: `CURRENT_STATE.md`
- Active backlog and scope tracker: `docs/BACKLOG.md`
- Durable product requirements: `docs/rds/`
- Architecture boundary contract: `docs/ARCHITECTURE_CONTRACT.md`
- Godot/C++ migration authority map: `docs/architecture/authority_map.md`

## Source-of-truth order

1. Newer task instructions.
2. `config/project/policy_pack.json` for governance, validation, maintenance
   automation, and generated maintenance-doc inputs.
3. Domain authorities such as
   `docs/plans/topology_playground_current_authority.md` when the task touches
   their scope.
4. `docs/governance/README.md` and `docs/architecture/authority_map.md` for
   Godot/C++ migration routing and authority boundaries.
5. `docs/WORKFLOW_CODEX.md` for human-readable repo workflow.
6. Relevant `docs/rds/*` contracts for product behavior.
7. `docs/ARCHITECTURE_CONTRACT.md` for dependency and package-boundary rules.
8. `CURRENT_STATE.md` and `docs/BACKLOG.md` for restart context and open work.

## Context-switch profiles

Use the smallest profile that matches the task. Load the listed authorities
first, then widen only if the change proves cross-cutting.

### review

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/WORKFLOW_CODEX.md`
4. `docs/DOCUMENTATION_MAP.md` to route to the current authority for the
   changed area
5. the changed diff, touched tests, and only the routed authority for that
   area

Verify: for docs-only review, run the matching docs/governance check such as
`.venv/bin/python tools/governance/validate_project_contracts.py`; for code
review, keep validation to the touched tests or a focused
`./scripts/verify_focus.sh --pytest ...` lane.
Skip unless cross-cutting: `docs/BACKLOG.md`, `docs/ARCHITECTURE_CONTRACT.md`,
topology-playground authority/spec docs.

### engine

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/ARCHITECTURE_CONTRACT.md`
4. relevant `docs/rds/*`
5. touched engine/runtime modules plus their tests

Verify: run focused engine checks such as `.venv/bin/ruff check <touched-engine-paths>`
and `.venv/bin/python -m pytest -q <touched-engine-tests>`.
Skip unless cross-cutting: full `docs/BACKLOG.md`, packaging docs,
topology-playground authority/spec docs.

### menu_ui

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/rds/RDS_MENU_STRUCTURE.md`
4. `docs/MENU_STRUCTURE_EDITING.md`
5. `config/menu/structure.json` and affected menu/render code

Verify: run focused menu checks such as `.venv/bin/python -m pytest -q tests/unit/engine/test_menu_layout.py tests/unit/engine/test_menu_runner.py tests/unit/engine/test_menu_navigation_keys.py tests/unit/engine/test_menu_policy.py`
plus touched menu-specific tests.
Skip unless cross-cutting: `docs/ARCHITECTURE_CONTRACT.md`,
`docs/RELEASE_CHECKLIST.md`, full `docs/BACKLOG.md`.

### topology_explorer

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/plans/topology_playground_current_authority.md`
4. `docs/plans/topology_playground_shell_redesign_spec.md`
5. `docs/BACKLOG.md` and the touched playground/runtime files

Verify: run focused explorer checks such as `.venv/bin/python -m pytest -q tests/unit/engine/test_topology_explorer.py tests/unit/engine/test_topology_explorer_runtime.py tests/unit/engine/test_topology_explorer_preview.py tests/unit/topology_lab/test_topology_lab_app.py`
plus touched explorer tests.
Skip unless cross-cutting: unrelated `docs/rds/*`, packaging docs, large
generated/reference docs.

### render

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/PROJECT_STRUCTURE.md` for current frontend/render ownership routing
4. touched render/frontend hotspot files such as
   `src/tet4d/ui/pygame/render/`, `src/tet4d/ui/pygame/front3d_render.py`,
   `src/tet4d/ui/pygame/front4d_render.py`, and
   `src/tet4d/ui/pygame/locked_cell_explosion/render.py`
5. the relevant `docs/rds/*` contract when the render change carries product
   behavior impact

Verify: run focused render checks such as `.venv/bin/python -m pytest -q tests/unit/render/test_locked_cell_explosion.py tests/unit/render/test_active_piece_projection_guides.py tests/unit/render/test_projection_guide_animation.py tests/unit/engine/test_front4d_render.py tests/unit/engine/test_gfx_game_rotation_render.py`
plus touched render/frontend tests.
Skip unless cross-cutting: full `docs/BACKLOG.md`,
`docs/plans/topology_playground_current_authority.md`,
`docs/RELEASE_CHECKLIST.md`.

### packaging

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/rds/RDS_PACKAGING.md`
4. `docs/RELEASE_CHECKLIST.md`
5. packaging scripts, workflow files, and targeted packaging tests

Verify: run the targeted packaging lane first, such as
`.venv/bin/python -m pytest -q tests/unit/engine/test_windows_packaging.py tests/unit/engine/test_frozen_runtime_paths.py tests/unit/engine/test_front_launcher_routes.py`.
Skip unless cross-cutting: topology-playground authority/spec docs, full
`docs/BACKLOG.md`, unrelated `docs/rds/*`.

### governance

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `config/project/policy_pack.json`
4. `docs/governance/README.md`
5. `docs/architecture/authority_map.md`
6. `tools/governance/validate_project_contracts.py`
7. `tools/governance/generate_maintenance_docs.py`
8. `docs/BACKLOG.md`

Verify: run `.venv/bin/python tools/governance/validate_project_contracts.py`,
`.venv/bin/python tools/governance/generate_maintenance_docs.py --check`, and
`.venv/bin/python tools/governance/generate_configuration_reference.py --check`;
touch `tools/governance/generate_maintenance_docs.py` explicitly when the batch
changes generated maintenance-doc expectations.
Skip unless cross-cutting: unrelated `docs/rds/*`,
`docs/RELEASE_CHECKLIST.md`, topology-playground authority/spec docs.

### handoff

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/BACKLOG.md`
4. `docs/PROJECT_STRUCTURE.md`
5. `git branch --show-current` and `git status --short`

Verify: run maintenance/doc drift checks such as
`.venv/bin/python tools/governance/validate_project_contracts.py` and
`.venv/bin/python tools/governance/generate_maintenance_docs.py --check` before
handoff, plus `CODEX_MODE=1 ./scripts/verify.sh` if the batch changed code.
Skip unless cross-cutting: unrelated `docs/rds/*`,
`docs/ARCHITECTURE_CONTRACT.md`, packaging docs.

## Boundary model

- Machine-readable policy data belongs in `config/project/policy_pack.json`.
- `tools/governance/validate_project_contracts.py` owns validation procedure only.
  It may parse files, compare them to pack data, and report drift; it must not
  become a second policy inventory.
- `tools/governance/generate_maintenance_docs.py` owns rendering procedure only.
  Generated maintenance-doc inputs belong in the `maintenance_docs` section of
  `config/project/policy_pack.json`.
- `docs/WORKFLOW_CODEX.md` explains repo workflow only.
- `CURRENT_STATE.md` owns restart handoff only.
- `docs/BACKLOG.md` owns open work and current change footprint only.
- `docs/PROJECT_STRUCTURE.md` owns generated ownership and source-of-truth
  snapshots only.

## Required workflow

1. Read the relevant authorities before editing. Do not operate on guessed repo
   state.
2. Start restructuring or behavior changes with a short plan and explicit
   acceptance criteria.
3. Compare the task against the current sources of truth before changing code
   or governance files.
4. Authority files must be tracked in Git; untracked local-only copies do not
   satisfy the repo contract.
5. Prefer existing helpers and APIs over new local reinventions.
6. Before introducing a new repo-owned runtime constant, first identify the
   config authority where it belongs; do not add direct code constants for
   runtime/tuning/default/layout values.
7. For staged refactors, add new modules first, route one flow, verify, and
   only then remove old paths.
8. Do not treat partial progress as completion. Satisfy every stated
   acceptance criterion before claiming the batch is done.
9. Update docs in the same batch when scope or workflow changes:
   - `docs/BACKLOG.md`
   - `CURRENT_STATE.md`
   - `docs/PROJECT_STRUCTURE.md` when generated ownership or source-of-truth
     sections change
   - relevant `docs/rds/*`
10. Keep `CURRENT_STATE.md` as handoff-only; do not reintroduce it as a second
   workflow authority.
11. At the end of staged migration work, provide a delta report with files
    added, files modified, files not touched, satisfied acceptance criteria,
    unsatisfied acceptance criteria, remaining old paths, and follow-up
    blockers.

## Edit discipline

1. Read the exact current file before editing it.
2. Use `apply_patch` for localized edits with fresh context.
3. For broad doc rewrites or generated maintenance files, switch to one
   deterministic rewrite instead of retrying drifting patches.
4. After one rejected `apply_patch` attempt on a file, stop retrying broad
   patches and switch edit method.
5. Preserve UTF-8 without BOM and avoid literal escape-text insertion on
   non-patch rewrites.
6. After any non-patch source rewrite, run a touched-file hygiene pass before
   broader tests.

## Verification

Primary local gate:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

Menu IA/settings migrations must include smoke coverage (automated or manual) for:
- root launch
- 2D setup
- 3D setup
- 4D setup
- Settings root
- Endgame / Explosion page
- Back/Esc/Q behavior

Focused validation during a batch:

```bash
./scripts/verify_focus.sh [--docs] [ruff-targets...] [--pytest pytest-targets...]
```

Focused keybinding contract validation:

```bash
./scripts/check_keybinding_contract.sh
```

CI preflight:

```bash
./scripts/ci_preflight.sh
```

Rules:

1. Never run `./scripts/verify.sh` and `./scripts/ci_check.sh` in parallel.
2. prefer the current repo virtualenv interpreter when one is available.
3. Run the full local gate before completion unless the task is explicitly
   documentation-only and the gate is blocked for an external reason.

## Notes

- `docs/rds/` is for durable product requirements, not repo workflow.
- Domain-specific manifests under `config/project/policy/manifests/` remain
  valid standalone data files, but repo governance authority lives only in
  `config/project/policy_pack.json`.
