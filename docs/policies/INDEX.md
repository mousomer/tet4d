# Policy Pack Index

This repo's active governance pack is anchored in
`config/project/policy/governance.json` and `config/project/policy/code_rules.json`.
They are the sole runtime policy sources for governance checks.

Domain-specific contracts remain in `config/project/policy/manifests/` where
they are still useful as standalone data files.

- `no_reinventing_wheel` - governance; source: `docs/policies/POLICY_NO_REINVENTING_WHEEL.md`; enforced by `scripts/check_policy_compliance.sh`.
- `string_sanitation` - safety; source: `docs/policies/POLICY_STRING_SANITATION.md`; enforced by `scripts/check_policy_compliance.sh`.
- `no_magic_numbers` - governance; source: `docs/policies/POLICY_NO_MAGIC_NUMBERS.md`; enforced by `scripts/check_policy_compliance.sh`.
- `formatting` - governance; source: `docs/policies/POLICY_FORMATTING.md`; enforced by `scripts/check_policy_compliance.sh`.
- `configuration_documentation` - governance; source: `docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md`; enforced by `scripts/verify.sh` and `tools/governance/generate_configuration_reference.py --check`.
- CI operations runbook: `docs/policies/CI_COMPLIANCE_RUNBOOK.md`.

Contracts referenced by the pack:
- `config/project/policy/governance.json` (validated by `tools/governance/validate_governance.py`)
- `config/project/policy/code_rules.json` (validated by `tools/governance/validate_governance.py`)
- `config/project/policy/manifests/canonical_maintenance.json` (validated by `tools/governance/validate_project_contracts.py`)
- `config/project/policy/manifests/secret_scan.json` (validated by `python3 tools/governance/scan_secrets.py`)
- `config/project/policy/manifests/replay_manifest.json` (validated by `tools/governance/validate_project_contracts.py`)
- `config/project/policy/manifests/help_assets_manifest.json` (validated by `tools/governance/validate_project_contracts.py`)

Source of truth list: unified governance manifests + canonical maintenance +
this index. Update them together when adding or retiring policies.
