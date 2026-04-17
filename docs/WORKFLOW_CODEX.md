# Workflow For Codex And Contributors

This document explains how to apply the machine rules in
`config/project/policy_pack.json`.

## Workflow authority

- Machine-readable governance authority: `config/project/policy_pack.json`
- Thin dispatch file: `AGENTS.md`
- Human workflow explainer: `docs/WORKFLOW_CODEX.md`
- Restart handoff only: `CURRENT_STATE.md`
- Active backlog and scope tracker: `docs/BACKLOG.md`
- Durable product requirements: `docs/rds/`
- Architecture boundary contract: `docs/ARCHITECTURE_CONTRACT.md`

## Source-of-truth order

1. Newer task instructions.
2. `config/project/policy_pack.json` for governance, validation, maintenance
   automation, and generated maintenance-doc inputs.
3. Domain authorities such as
   `docs/plans/topology_playground_current_authority.md` when the task touches
   their scope.
4. `docs/WORKFLOW_CODEX.md` for human-readable repo workflow.
5. Relevant `docs/rds/*` contracts for product behavior.
6. `docs/ARCHITECTURE_CONTRACT.md` for dependency and package-boundary rules.
7. `CURRENT_STATE.md` and `docs/BACKLOG.md` for restart context and open work.

## Context-switch profiles

Use the smallest profile that matches the task. Load the listed authorities
first, then widen only if the change proves cross-cutting.

### review

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/WORKFLOW_CODEX.md`
4. the changed diff, touched tests, and the relevant authority for the changed
   area

### engine

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/ARCHITECTURE_CONTRACT.md`
4. relevant `docs/rds/*`
5. touched engine/runtime modules plus their tests

### menu_ui

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/rds/RDS_MENU_STRUCTURE.md`
4. `docs/MENU_STRUCTURE_EDITING.md`
5. `config/menu/structure.json` and affected menu/render code

### topology_explorer

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/plans/topology_playground_current_authority.md`
4. `docs/plans/topology_playground_shell_redesign_spec.md`
5. `docs/BACKLOG.md` and the touched playground/runtime files

### packaging

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/rds/RDS_PACKAGING.md`
4. `docs/RELEASE_CHECKLIST.md`
5. packaging scripts, workflow files, and targeted packaging tests

### governance

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `config/project/policy_pack.json`
4. `tools/governance/validate_project_contracts.py`
5. `tools/governance/generate_maintenance_docs.py`
6. `docs/BACKLOG.md`

### handoff

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `docs/BACKLOG.md`
4. `docs/PROJECT_STRUCTURE.md`
5. `git branch --show-current` and `git status --short`

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
6. For staged refactors, add new modules first, route one flow, verify, and
   only then remove old paths.
7. Do not treat partial progress as completion. Satisfy every stated
   acceptance criterion before claiming the batch is done.
8. Update docs in the same batch when scope or workflow changes:
   - `docs/BACKLOG.md`
   - `CURRENT_STATE.md`
   - `docs/PROJECT_STRUCTURE.md` when generated ownership or source-of-truth
     sections change
   - relevant `docs/rds/*`
9. Keep `CURRENT_STATE.md` as handoff-only; do not reintroduce it as a second
   workflow authority.
10. At the end of staged migration work, provide a delta report with files
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
