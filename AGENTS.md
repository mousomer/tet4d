# tet4d Repo Instructions (Codex)

## Policy sources of truth
- RDS + workflow: `docs/RDS_AND_CODEX.md`
- Policy docs: `docs/policies/`
- Policy pack root: `config/project/policy/pack.json`
- Policy manifest: `config/project/policy/manifests/project_policy.json` (includes policy pack + index)
- Canonical maintenance contract:
  - `config/project/policy/manifests/canonical_maintenance.json`
  - `tools/governance/validate_project_contracts.py`
- Context router:
  - `config/project/policy/manifests/context_router_manifest.json`

## Governance rules
For any restructuring/update:
1. Produce a short plan + acceptance criteria.
2. Compare against relevant RDS sections and update RDS if required.
3. Keep canonical maintenance artifacts synchronized.
4. Update `docs/BACKLOG.md` when scope changes.
5. Do not introduce `tetris_nd` imports; use `tet4d.engine.*` only.
6. `tetris_nd/` compatibility shim is removed; treat any new `tetris_nd` import as a policy violation.
7. Repo uses `src/` layout with editable install for dev/CI (`pip install -e .[dev]`); do not add repo-root import shims.
8. Do not reinvent the wheel: prefer existing repo helpers/functions/APIs before adding new implementation code.
9. Do not hardcode magic numbers in Python code; prefer non-Python config-backed constants (for example `config/*` + runtime/config accessors) unless externalizing the value would add disproportionate complexity.
10. Sanitize external or user-controlled string inputs via runtime sanitization helpers before use.

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
CI and local verification assume the repo package is installed in editable mode.

## Safety & sanitation
- No secrets in repo.
- No hard-coded absolute paths.
- Use `config/project/io_paths.json` helpers.
