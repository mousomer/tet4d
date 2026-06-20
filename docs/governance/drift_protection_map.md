# tet4d Drift Protection Map

This document defines tet4d-specific drift surfaces.

General drift-protection principles live in
`docs/governance/workspace_bundle/drift_protection_policy.md`.

## Governance routing drift

Surfaces:

- `AGENTS.md`
- `godot/AGENTS.md`
- `native/AGENTS.md`
- `docs/governance/README.md`
- `docs/governance/review_checklist.md`
- `docs/governance/workspace_bundle/review_checklist_template.md`
- `.github/pull_request_template.md`

Required invariants:

- Root `AGENTS.md` routes to workspace governance and tet4d authority.
- Local `AGENTS.md` files route only local concerns.
- `docs/governance/README.md` links active governance surfaces.
- New governance files are reachable from a router, index, manifest, or local
  `AGENTS.md`.
- Review surfaces route to workspace governance, tet4d authority, debt, drift,
  generated-file, validation, and staging checks.

## Workspace bundle drift

Surfaces:

- `docs/governance/workspace_bundle/`
- `docs/governance/workspace_bundle/MANIFEST.md`
- `tools/governance/validate_workspace_bundle.py`

Required invariants:

- Every bundle Markdown file is listed in the manifest.
- Bundle files remain project-neutral.
- Project overlays link to workspace policies they extend.

## Authority drift

Surfaces:

- `docs/architecture/authority_map.md`
- `docs/architecture/parity_protocol.md`
- `docs/architecture/authority_transfer_protocol.md`
- `docs/governance/godot_cpp_policy.md`
- `docs/governance/cpp_safety_policy.md`
- `docs/governance/testing_policy.md`
- `tools/governance/validate_authority_transfer.py`

Required invariants:

- Python remains the current semantic oracle.
- Godot remains shell/presentation unless authority is explicitly transferred.
- C++/GDExtension remains provisional until parity evidence and a completed
  authority-transfer record are documented.
- No policy claims C++ owns gameplay semantics without a transfer record.
- No policy claims GDScript owns topology, movement, collision, gravity,
  rotation, scoring, trace semantics, or replay correctness.

## Validator integration drift

Surfaces:

- `tools/governance/validate_governance.py`
- `tools/governance/validate_project_contracts.py`
- `tools/governance/validate_workspace_bundle.py`
- `tools/governance/validate_technical_debt.py`
- `tools/governance/validate_config_authority.py`
- `tools/governance/validate_utility_reuse.py`
- `tools/governance/validate_godot_semantic_boundary.py`
- `tools/governance/validate_native_cpp_tooling.py`
- `tools/governance/validate_drift_protection.py`
- `tools/governance/validate_authority_transfer.py`

Required invariants:

- Active governance validators are wired into `validate_governance.py`.
- Project-contract checks know about active governance validators.
- Validator output remains deterministic and actionable.

## Debt/advisory drift

Surfaces:

- `docs/governance/technical_debt_register.md`
- `tools/governance/validate_technical_debt.py`
- advisory validators

Required invariants:

- Advisory findings are covered by debt categories or explicit accepted policy.
- Suppressions are classified, removed, or recorded as debt.
- Debt totals are calculable.

## Config/generated drift

Surfaces:

- `docs/governance/config_policy.md`
- `docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md`
- `docs/policies/POLICY_NO_MAGIC_NUMBERS.md`
- `docs/CONFIGURATION_REFERENCE.md`
- `config/project/policy_pack.json`
- `config/project/constants.json`
- `config/gameplay/tuning.json`
- `config/menu/defaults.json`
- `tools/governance/validate_config_authority.py`
- `tools/governance/generate_configuration_reference.py`
- `tools/migration/export_config_bundle.py`
- `migration/exported_bundle/`
- `migration/exported_bundle/manifest.json`
- `migration/exported_bundle/docs/authority_index.json`
- `migration/exported_bundle/config/tet4d_config_bundle.json`

Required invariants:

- Generated config/reference surfaces identify source authority or generator.
- Config policy and config validators agree on standard config sources.
- Generated bundle files are not treated as hand-authored authority.

## Utility-index drift

Surfaces:

- `docs/architecture/utility_index.md`
- `docs/policies/POLICY_NO_REINVENTING_WHEEL.md`
- `tools/governance/validate_utility_reuse.py`

Required invariants:

- Reusable helper authorities are documented.
- Utility-reuse validator and no-reinventing-wheel policy agree on the
  search-first rule.
- Accepted duplicate-helper advisories are represented as debt or suppressions.

## Deferred drift checks

The following are intentionally deferred:

- full authority-transfer record validation
- one-to-one mapping between each advisory finding and a debt record
- exhaustive TODO/FIXME debt coverage
- full generated-output checksum comparison
