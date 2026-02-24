# tet4d Repo Instructions (Codex)

## Policy sources of truth
- RDS + workflow: `docs/RDS_AND_CODEX.md`
- Canonical maintenance contract:
  - `config/project/canonical_maintenance.json`
  - `tools/governance/validate_project_contracts.py`

## Governance rules
For any restructuring/update:
1. Produce a short plan + acceptance criteria.
2. Compare against relevant RDS sections and update RDS if required.
3. Keep canonical maintenance artifacts synchronized.
4. Update `docs/BACKLOG.md` when scope changes.
5. Do not introduce new imports of `tetris_nd`; prefer `tet4d.engine.*`.
6. Treat shim removal as gated work:
   - remove `tetris_nd/` only after zero non-shim `tetris_nd` imports remain and CI passes
   - remove repo-root `tet4d/` shim only after import setup is standardized (install/editable install or equivalent)

## Verification contract
Run:

```bash
./scripts/verify.sh
```

Codex/local quick mode (same checks, lower stability repeats, quieter success output):

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

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

CI remains authoritative and runs `./scripts/ci_check.sh` via `.github/workflows/ci.yml`.

## Safety & sanitation
- No secrets in repo.
- No hard-coded absolute paths.
- Use `config/project/io_paths.json` helpers.
