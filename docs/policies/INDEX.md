# Policy Pack Index

This repo's policy pack is anchored in `config/project/policy/pack.json`
(components + constraints) and `config/project/policy/manifests/project_policy.json`
(`policy_pack` section).
Canonical inventory source is
`config/project/policy/manifests/policy_registry.json` (project policy and this
index are validated against it).

- `no_reinventing_wheel` - governance; source: `docs/policies/POLICY_NO_REINVENTING_WHEEL.md`; enforced by `scripts/check_policy_compliance.sh`.
- `string_sanitation` - safety; source: `docs/policies/POLICY_STRING_SANITATION.md`; enforced by `scripts/check_policy_compliance.sh`.
- `no_magic_numbers` - governance; source: `docs/policies/POLICY_NO_MAGIC_NUMBERS.md`; enforced by `scripts/check_policy_compliance.sh`.
- `formatting` - governance; source: `docs/policies/POLICY_FORMATTING.md`; enforced by `scripts/check_policy_compliance.sh`.
- `configuration_documentation` - governance; source: `docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md`; enforced by `scripts/verify.sh` and `tools/governance/generate_configuration_reference.py --check`.
- CI operations runbook: `docs/policies/CI_COMPLIANCE_RUNBOOK.md`.

Contracts referenced by the pack:
- `config/project/policy/manifests/canonical_maintenance.json` (validated by `tools/governance/validate_project_contracts.py`)
- `config/project/policy/manifests/tech_debt_budgets.json` (validated by `scripts/check_architecture_metrics_soft_gate.sh`)
- `config/project/policy/manifests/architecture_metrics.json` (validated by `scripts/arch_metrics.py`)
- `config/project/policy/manifests/secret_scan.json` (validated by `python3 tools/governance/scan_secrets.py`)
- `config/project/policy/manifests/contributor_directives.json` (validated by `tools/governance/validate_project_contracts.py`)
- `config/project/policy/manifests/risk_gates.json` (validated by `tools/governance/check_risk_gates.py`)
- `config/project/policy/manifests/policy_runtime_rules.json` (validated by `tools/governance/check_policy_runtime_rules.py`)
- `config/project/policy/manifests/wheel_reuse_rules.json` (validated by `tools/governance/check_wheel_reuse_rules.py`)
- `config/project/policy/manifests/loc_guidance.json` (validated by `tools/governance/check_loc_guidance.py`)
- `config/project/policy/manifests/dedup_dead_code_rules.json` (validated by `tools/governance/check_dedup_dead_code_rules.py`)

Source of truth list: policy manifest + this index. Update both when adding or
retiring policies.
