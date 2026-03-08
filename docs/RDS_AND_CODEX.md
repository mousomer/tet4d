# RDS Files And Codex Instructions

This document defines the concise contributor workflow and points to canonical
policy/manifests. It replaces historical stage-by-stage migration instructions
that are now tracked in `CURRENT_STATE.md` and `docs/BACKLOG.md`.

## Source-of-truth order

1. Policy manifests and contracts under `config/project/policy/manifests/`.
2. Policy docs under `docs/policies/`.
3. RDS specs under `docs/rds/`.
4. Active execution plan and checkpoint state:
   - `docs/BACKLOG.md`
   - `CURRENT_STATE.md`

## Policy index

- `docs/policies/INDEX.md`
- `docs/policies/POLICY_NO_REINVENTING_WHEEL.md`
- `docs/policies/POLICY_STRING_SANITATION.md`
- `docs/policies/POLICY_NO_MAGIC_NUMBERS.md`
- `docs/policies/POLICY_FORMATTING.md`
- `docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md`
- `docs/policies/CI_COMPLIANCE_RUNBOOK.md`
- `config/project/policy/pack.json`
- `config/project/policy/manifests/project_policy.json`
- `config/project/policy/manifests/contributor_directives.json`
- `config/project/policy/manifests/risk_gates.json`
- `config/project/policy/manifests/canonical_maintenance.json`
- `config/project/policy/manifests/context_router_manifest.json`

## RDS index

- `docs/rds/RDS_TETRIS_GENERAL.md`
- `docs/rds/RDS_KEYBINDINGS.md`
- `docs/rds/RDS_MENU_STRUCTURE.md`
- `docs/rds/RDS_PLAYBOT.md`
- `docs/rds/RDS_SCORE_ANALYZER.md`
- `docs/rds/RDS_PACKAGING.md`
- `docs/rds/RDS_FILE_FETCH_LIBRARY.md`
- `docs/rds/RDS_2D_TETRIS.md`
- `docs/rds/RDS_3D_TETRIS.md`
- `docs/rds/RDS_4D_TETRIS.md`

## Contributor workflow

1. Read relevant RDS sections before code changes.
2. For restructuring/behavior changes, define short plan + acceptance criteria.
3. Prefer existing helpers/APIs; avoid wheel reinvention.
4. Prefer medium-sized localized patches over ultra-narrow patch fragmentation. Split patches only when a broader patch becomes tool-rejected or hard to review.
5. Keep keybindings/settings/tutorial structure config-backed (non-Python).
6. Use runtime sanitization helpers for user/external strings.
7. Keep tunable thresholds in canonical config (avoid magic numbers).
8. Update docs in the same change when behavior/governance changes:
   - `docs/BACKLOG.md`
   - `CURRENT_STATE.md` and `docs/PROJECT_STRUCTURE.md` (generated sections
     are maintained by `tools/governance/generate_maintenance_docs.py`)
   - drift-protection contracts and thin-wrapper budgets in
     `config/project/policy/manifests/drift_protection.json`
   - `docs/CONFIGURATION_REFERENCE.md` when `config/` changes
   - `docs/USER_SETTINGS_REFERENCE.md` when user-facing settings surfaces change
   - relevant `docs/rds/*`
9. Keep contract files synchronized and valid:
   - `config/project/policy/manifests/canonical_maintenance.json`
   - `config/project/policy/manifests/context_router_manifest.json`
   - `config/project/policy/manifests/project_policy.json`

## Testing instructions

Primary verification:

```bash
./scripts/verify.sh
```

Codex/local quick mode:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

Fast staged local validation before the full gate:

```bash
./scripts/verify_focus.sh [--docs] [ruff-targets...] [--pytest pytest-targets...]
```

Use `verify_focus.sh` for focused lint/tests and maintenance-doc checks while a batch is in progress. It does not replace `./scripts/verify.sh` before commit/push.

For governance/contract changes, additionally run:

```bash
python3 tools/governance/validate_project_contracts.py
python3 tools/governance/generate_configuration_reference.py --check
python3 tools/governance/generate_maintenance_docs.py --check
python3 tools/governance/check_drift_protection.py
python3 tools/governance/check_risk_gates.py
./scripts/check_policy_compliance.sh
./scripts/check_git_sanitation.sh
```

CI preflight (recommended before push):

```bash
./scripts/ci_preflight.sh
```

## Notes on scope

- Detailed stage migration history does not belong in this file.
- Historical/active stage details belong in:
  - `docs/BACKLOG.md` (change footprint)
  - `CURRENT_STATE.md` (restart handoff)
