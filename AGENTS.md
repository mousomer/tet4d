# tet4d Repo Instructions (Codex)

## Scope

This file is the root operational contract for Codex in this repo.

Use it to:
- choose the right source of truth,
- load the right context before editing,
- make reliable, reviewable edits,
- validate changes correctly,
- avoid patch thrashing and repo-policy violations.

Do not treat this file as a substitute for the detailed workflow and migration rules in `docs/RDS_AND_CODEX.md`.
Use that document whenever the task touches gameplay logic, architecture refactors, folder moves, compatibility shims, or staged cleanup.

---

## Policy sources of truth

Primary sources:

- RDS + workflow: `docs/RDS_AND_CODEX.md`
- Architecture boundary contract: `docs/ARCHITECTURE_CONTRACT.md`
- Current restart handoff / progress snapshot: `CURRENT_STATE.md`
- Topology-playground current authority:
  `docs/plans/topology_playground_current_authority.md`
- Policy docs: `docs/policies/`
- Policy index: `docs/policies/INDEX.md`
- Unified governance manifest: `config/project/policy/governance.json`
- Unified code-rules manifest: `config/project/policy/code_rules.json`
- Canonical maintenance contract:
  - `config/project/policy/manifests/canonical_maintenance.json`
  - `tools/governance/validate_project_contracts.py`
  - `tools/governance/check_risk_gates.py`

Supporting governance / metrics sources:

- Tech debt budgets:
  - `config/project/policy/governance.json` (`tech_debt_budget`)
- Canonical machine-readable debt backlog:
  - `config/project/backlog_debt.json`
- Backlog / scope tracking:
  - `docs/BACKLOG.md`

---

## Required context-loading order

Before editing, load context in this order as applicable:

1. Read this `AGENTS.md`.
2. Read `CURRENT_STATE.md` first for any long-running refactor, restart handoff, architecture cleanup, or staged migration task.
3. For any topology-playground task, read
   `docs/plans/topology_playground_current_authority.md` before older
   topology-playground manifests or audits.
   If this file conflicts with archived topology-playground manifests, follow
   the current-authority file.
   If a newer user/developer instruction severely conflicts with the
   current-authority file or with current code reality, stop and ask first,
   then update the manifest layer in the same batch if the direction changes.
4. Read `docs/RDS_AND_CODEX.md` for workflow rules and relevant RDS references.
5. Read the task-relevant RDS files before editing gameplay logic.
6. Read `docs/ARCHITECTURE_CONTRACT.md` before architecture refactors, folder moves, or boundary-sensitive changes.
7. Read relevant policy files when the task touches:
   - sanitization,
   - constants/config,
   - governance/tooling,
   - repo restructuring,
   - context routing,
   - canonical maintenance.

Do not start coding while operating on guessed repo state.

---

## Core operating principles

- Make correct, minimal, reviewable changes.
- Prefer patch reliability over patch ambition.
- Prefer narrow, deterministic edits over broad speculative rewrites.
- Preserve existing behavior unless the task explicitly changes behavior.
- Keep behavior parity with existing tests when refactoring.
- Prefer small, composable helpers over large event/render functions.
- Prefer existing repo helpers/functions/APIs before adding new implementation code.
- Preserve deterministic behavior where seeds are used.
- Keep keybindings external; do not hardcode mode keys in frontends.
- Features common to 2D/3D/4D setup menus should be centralized in the shared settings hub unless a strong documented mode-specific reason exists.

---

## Governance rules

For any restructuring or governance-affecting update:

1. Produce a short plan plus acceptance criteria before editing.
2. Compare against relevant RDS sections and update RDS if required.
3. Keep canonical maintenance artifacts synchronized.
4. Update `docs/BACKLOG.md` when scope changes.
5. Keep architecture boundary checks green.
6. Keep tech-debt budgets and staged checkpoint expectations synchronized when the task changes staged architecture metrics or checkpoint status.
7. Track LOC delta for every change and, unless delivering a new feature, prefer changes that reduce LOC.
8. Follow formatting and line-length policy across scripts and text files.
9. Default verification runs should use quiet mode; use verbose output only when diagnosing failures or flakes.
10. For topology-playground tasks, current-authority guidance and newer task
    instructions override archived manifests; if that precedence exposes a
    severe mismatch, ask first and update the manifest/history notes in the
    same batch before claiming completion.

Do not claim a governance update is complete if docs, manifests, metrics, or validation were left stale.

---

## Repo architecture and import constraints

- Do not introduce `tetris_nd` imports.
- The `tetris_nd/` compatibility shim is removed; any new `tetris_nd` import is a policy violation.
- Repo uses `src/` layout with editable install for dev/CI (`pip install -e .[dev]` or equivalent editable install path for the task environment).
- Do not add repo-root import shims.
- Runtime code is under `src/tet4d/engine/`.
- Use canonical imports under `tet4d.*`.
- Public playbot APIs should be imported from `tet4d.engine.api`; `tet4d.ai.playbot` retains shared internal helper logic during migration.
- Redundant compatibility facades may be removed when callers are migrated, but boundary-enforcing adapters must remain until the corresponding modules are physically moved and boundary checks stay green.

Do not bypass architecture boundaries for convenience.

---

## Code policy rules

### No reinventing the wheel
- Prefer existing repo helpers/functions/APIs before writing new implementation code.
- Check `tet4d.engine.api`, shared runtime helpers, existing adapters, and canonical config/path helpers first.

### No magic numbers
- Do not hardcode magic numbers in Python code.
- Prefer config-backed constants and runtime/config accessors unless externalizing the value would add disproportionate complexity.

### String sanitization
- Sanitize external or user-controlled string inputs with canonical runtime sanitization helpers before use.

### Paths and secrets
- No secrets in repo.
- No hard-coded absolute paths.
- Use `config/project/io_paths.json` helpers where path resolution is needed.

---

## Codex edit discipline

### Edit scope rules

- Work from the Git repo root only.
- Use relative paths only.
- Prefer one-file, one-purpose edits.
- Do not combine implementation changes, import rewires, formatting churn, and test rewrites in one patch batch unless the task clearly requires it.
- Do not edit the same file from parallel workstreams.
- Assume `apply_patch` is fragile and reduce risk before every edit.

### Required file-edit protocol

For every file edit:

1. Read the exact current file from disk first.
2. Patch only against that exact current text.
3. Keep the patch minimal and local.
4. If later edits depend on surrounding text, re-read the file after the patch lands before editing it again.

If a patch is rejected:

1. Stop assuming prior file contents are still valid.
2. Re-read the exact file from disk.
3. Regenerate a smaller patch against the exact current text.
4. If the second patch attempt on the same file also fails, stop patching that file.
5. Rewrite the full file deterministically, preserving unrelated behavior, encoding, and newline conventions.

Do not thrash on repeated patch retries.

### New-file protocol

When adding a new file:

1. Create the file in a dedicated step.
2. Verify the file exists at the expected relative path.
3. Only then update imports, package exports, callers, or tests.

Do not create a file and rewire multiple dependent files in the same first step.

### Python package discipline

- Update `__init__.py` separately from creating a new module when practical.
- Keep import rewires separate from logic edits when practical.
- Do not reorder unrelated imports unless required.
- Do not introduce import-time side effects.

### Refactor / migration protocol

For nontrivial refactors:

1. Add the new helper/module/function first.
2. Validate syntax/import sanity.
3. Rewire one caller at a time.
4. Run focused validation after each rewire.
5. Update tests last unless tests are required first to establish the seam.

Prefer staged migration over big-bang replacement.

---

## tet4d-specific staged refactor discipline

For gameplay logic, topology logic, UI extraction, runtime moves, compatibility-shim pruning, or engine folder cleanup:

- Read the relevant RDS files first.
- Follow `docs/RDS_AND_CODEX.md`.
- Follow `docs/ARCHITECTURE_CONTRACT.md`.
- Read `CURRENT_STATE.md` first for long-running threads before making changes.

Additional rules:

- Prefer merged buckets (`engine/gameplay`, `engine/ui_logic`, `engine/runtime`) over many tiny folders.
- Keep moves prefix-based and compatibility-shimmed to minimize import churn.
- Keep governance/tooling call sites stable during folder moves until the dedicated prune stage.
- Use zero-caller audits before deleting compatibility shims.
- Treat launcher/CLI canonicalization as a separate risk surface where the RDS workflow says to isolate it.
- Update structure docs when canonical paths change.
- Keep tests and docs aligned with canonical import paths once a shim is deleted.

Do not improvise move order for major architecture work when the RDS workflow already specifies it.

---

## Validation contract

Run:

```bash
./scripts/verify.sh
