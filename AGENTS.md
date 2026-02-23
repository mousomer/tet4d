# tet4d Repo Instructions (Codex)

## Policy sources of truth
- RDS + workflow: docs/RDS_AND_CODEX.md
- Canonical maintenance contract:
  - config/project/canonical_maintenance.json
  - tools/validate_project_contracts.py

## Governance rules
For any restructuring/update:
1) Produce a short plan + acceptance criteria.
2) Compare against relevant RDS sections and update RDS if required.
3) Keep canonical maintenance artifacts synchronized.
4) Update docs/BACKLOG.md when scope changes.

## Verification contract
Run:
    ./scripts/verify.sh

Verification must pass:
- ruff
- ruff (C901)
- pytest
- contract validation
- secret scan
- pygame-ce check
- playbot stability sweep
- compileall
- planner benchmark assertions

## Safety & sanitation
- No secrets in repo.
- No hard-coded absolute paths.
- Use config/project/io_paths.json helpers.
