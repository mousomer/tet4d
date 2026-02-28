# Policy Pack Index

This repo’s policy pack is anchored in `config/project/policy/pack.json` (components + constraints) and `config/project/policy/manifests/project_policy.json` (`policy_pack` section).

- `no_reinventing_wheel` — governance; source: `docs/policies/POLICY_NO_REINVENTING_WHEEL.md`; enforced by `scripts/check_policy_compliance.sh`.
- `string_sanitation` — safety; source: `docs/policies/POLICY_STRING_SANITATION.md`; enforced by `scripts/check_policy_compliance.sh`.
- `no_magic_numbers` — governance; source: `docs/policies/POLICY_NO_MAGIC_NUMBERS.md`; enforced by `scripts/check_policy_compliance.sh`.

Contracts referenced by the pack:
- `config/project/policy/manifests/canonical_maintenance.json` (validated by `tools/governance/validate_project_contracts.py`)
- `config/project/policy/manifests/tech_debt_budgets.json` (validated by `scripts/check_architecture_metrics_soft_gate.sh`)
- `config/project/policy/manifests/architecture_metrics.json` (validated by `scripts/arch_metrics.py`)
- `config/project/policy/manifests/secret_scan.json` (validated by `python3 tools/governance/scan_secrets.py`)

Source of truth list: policy manifest + this index. Update both when adding or retiring policies.
