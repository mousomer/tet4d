# CI Compliance Runbook

## Goal

Keep GitHub CI (`.github/workflows/ci.yml`) green and deterministic across all
supported Python versions.

## Pre-push command

Run this from repo root before pushing:

```bash
./scripts/ci_preflight.sh
```

`ci_preflight.sh` runs sanitation/policy checks and then the canonical CI entrypoint:
`./scripts/ci_check.sh`.

## Triage order when CI fails

1. Governance/sanitation gates:
   - `scripts/check_git_sanitation.sh`
   - `scripts/check_policy_compliance.sh`
   - `scripts/check_policy_template_drift.sh`
   - `scripts/check_git_sanitation_repo.sh`
   - `scripts/check_policy_compliance_repo.sh`
2. Main pipeline:
   - `./scripts/ci_check.sh` (delegates to `./scripts/verify.sh`)
3. If needed, isolate failing unit/module checks with the current repo virtualenv interpreter when available, for example `.venv/bin/python -m pytest -q`, and fix root cause.

## Hygiene rules for CI stability

1. Do not commit local context artifacts (for example `context-*.instructions.md`).
2. Local agent/worktree metadata (for example `.claude/` sandboxes or `.git` pointer files) is not project source and should be ignored by repo-content sanitation scans.
3. Do not commit absolute filesystem paths in docs/config/manifests.
4. Keep the unified policy sources synchronized:
   - `config/project/policy/governance.json`
   - `config/project/policy/code_rules.json`
   - `config/project/policy/manifests/canonical_maintenance.json`
5. Prefer the current repo virtualenv for local pytest, verify, and CI-style runs whenever it is available.
6. Treat policy warnings as debt to reduce in follow-up batches.

## Merge policy

1. Merge only when the full CI matrix is green.
2. If an urgent follow-up commit is needed, rerun `./scripts/ci_preflight.sh`
   before push.
