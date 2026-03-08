# tet4d Repo Instructions (Codex)

## Policy sources of truth
- RDS + workflow: `docs/RDS_AND_CODEX.md`
- Policy docs: `docs/policies/`
- Policy pack root: `config/project/policy/pack.json`
- Policy manifest: `config/project/policy/manifests/project_policy.json` (includes policy pack + index)
- Contributor directives manifest: `config/project/policy/manifests/contributor_directives.json`
- Risk gates manifest: `config/project/policy/manifests/risk_gates.json`
- Canonical maintenance contract:
  - `config/project/policy/manifests/canonical_maintenance.json`
  - `tools/governance/validate_project_contracts.py`
  - `tools/governance/check_risk_gates.py`
- Context router:
  - `config/project/policy/manifests/context_router_manifest.json`

## Governance rules
For any restructuring/update:
1. Produce a short plan + acceptance criteria.
2. Compare against relevant RDS sections and update RDS if required.
3. Keep canonical maintenance artifacts synchronized.
4. Update `docs/BACKLOG.md` when scope changes.
5. Follow contributor process directives in `config/project/policy/manifests/contributor_directives.json`.
6. Do not introduce `tetris_nd` imports; use `tet4d.engine.*` only (`config/project/policy/pack.json` constraints).
7. Repo uses `src/` layout with editable install for dev/CI (`pip install -e .[dev]`); do not add repo-root import shims.
8. Follow policy docs in `docs/policies/` for string sanitization, magic numbers, formatting, and no-reinventing-wheel.

## Verification contract
Run:

```bash
./scripts/verify.sh
```

Codex/local quick mode (same checks, lower stability repeats, quieter success output):

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

Fast staged local validation while a batch is in progress:

```bash
./scripts/verify_focus.sh [--docs] [ruff-targets...] [--pytest pytest-targets...]
```

Use `verify_focus.sh` for focused lint/tests and maintenance-doc checks before the full canonical gate. It does not replace `./scripts/verify.sh` before commit/push.

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
