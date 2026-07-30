# Governance Router

tet4d is Python-centered. Godot/C++ migration governance is an overlay, not a
replacement for Python/repository governance. The machine-readable authority is
`config/project/policy_pack.json`; this file routes readers to human policy and
evidence.

## Core policy routes

| Concern | Read |
| --- | --- |
| Contributor workflow | `docs/WORKFLOW_CODEX.md`, `docs/governance/codex_policy.md` |
| Reusable programming rules | `docs/governance/workspace_bundle/programming_policy.md` |
| Reusable drift protection | `docs/governance/workspace_bundle/drift_protection_policy.md` |
| Python architecture | `docs/ARCHITECTURE_CONTRACT.md`, relevant `docs/rds/*` |
| Godot/C++ boundary | `docs/governance/godot_cpp_policy.md`, `docs/architecture/authority_map.md` |
| Native safety/tooling | `docs/governance/cpp_safety_policy.md`, `docs/governance/native_tooling_ci_policy.md` |
| Testing/parity | `docs/governance/testing_policy.md`, `docs/architecture/parity_protocol.md` |
| Authority transfer | `docs/architecture/authority_transfer_protocol.md`, `tools/governance/validate_authority_transfer.py` |
| Config/constants | `docs/governance/config_policy.md`, `tools/governance/validate_config_authority.py` |
| Secrets/security | `docs/governance/secrets_policy.md`, `config/project/policy/manifests/secret_scan.json` |
| Dependency/utility reuse | `docs/policies/POLICY_NO_REINVENTING_WHEEL.md`, `docs/architecture/utility_index.md`, `tools/governance/validate_utility_reuse.py` |
| Technical debt | `docs/governance/workspace_bundle/technical_debt_policy.md`, `docs/governance/technical_debt_register.md`, `tools/governance/validate_technical_debt.py` |
| Review | `docs/governance/review_checklist.md`, `docs/governance/workspace_bundle/review_checklist_template.md`, `.github/pull_request_template.md` |
| Drift protection | `docs/governance/drift_protection_map.md`, `tools/governance/validate_drift_protection.py` |

The reusable workspace bundle lives in `docs/governance/workspace_bundle/` and
does not define tet4d-specific authority.

## Work-type routing

| Work type | Additional context |
| --- | --- |
| Python gameplay/topology/trace | architecture contract, relevant RDS, current Python implementation/tests |
| Godot UI/product shell | `godot/AGENTS.md`, Godot/C++ policy, relevant product/presentation authority |
| Native C++/GDExtension | `native/AGENTS.md`, authority map, applicable parity/transfer protocol, native safety/tooling policy |
| Parity implementation | parity protocol, selected subsystem doc, harness, fixtures, tests |
| Parity evidence review | promotion gates, applicable evidence package, comparison outputs |
| Authority transfer | transfer protocol, fallback/evidence, authority-map update |
| Topology migration | current topology authority, topology plan, Python oracle/runtime, tests |
| Governance/validation | policy pack, affected validators/generators/tests |
| Mixed migration | union of the smallest relevant routes above |

Python remains the semantic oracle. Godot owns product-shell presentation.
Native implementations remain provisional unless a completed transfer record
and authority-map update say otherwise. Parity and promotion-gate evidence do
not transfer authority.

## Historical parity and migration evidence index

These documents remain validated and discoverable evidence. Load only the
documents applicable to the selected subsystem or review:

- pilot and reusable promotion gate:
  `docs/architecture/first_subsystem_parity_pilot.md`,
  `docs/architecture/parity_pilot_audit_and_promotion_gates.md`;
- candidate selection and trace metadata evidence:
  `docs/architecture/second_parity_slice_candidate_selection.md`,
  `docs/architecture/trace_metadata_identity_digest_parity.md`;
- evidence review and topology identifier normalization evidence:
  `docs/architecture/parity_evidence_review_and_third_slice_selection.md`,
  `docs/architecture/topology_identifier_normalization_parity.md`,
  `tools/parity/topology_identifier_normalization_parity.py`,
  `tests/fixtures/parity/topology_identifier_normalization.json`;
- package/evidence review and schema/version evidence:
  `docs/architecture/parity_evidence_package_review.md`,
  `docs/architecture/trace_schema_version_normalization_parity.md`,
  `tools/parity/trace_schema_version_normalization_parity.py`,
  `tests/fixtures/parity/trace_schema_version_normalization.json`;
- oracle/tooling reviews and later structural evidence:
  `docs/architecture/python_oracle_boundary_audit.md`,
  `docs/architecture/parity_tooling_package_review.md`,
  `docs/architecture/structural_parity_slice_selection.md`,
  `docs/architecture/trace_envelope_validation_parity.md`.

The detailed historical map is `docs/DOCUMENTATION_MAP.md`; completed work may
also be recovered through `docs/history/` and Git history.

## Enforcement and conflict rules

Governance entrypoints include `tools/governance/validate_governance.py`,
`tools/governance/validate_project_contracts.py`,
`tools/governance/validate_godot_semantic_boundary.py`,
`tools/governance/validate_native_cpp_tooling.py`,
`tools/governance/check_wheel_reuse_rules.py`, and
`tools/governance/check_dedup_dead_code_rules.py`.

When documents conflict:

1. safety/security wins over convenience;
2. current Python semantics win over migration convenience;
3. the authority map decides migration ownership;
4. folder-local `AGENTS.md` may tighten but not weaken root constraints;
5. migration governance may clarify but not silently supersede Python
   governance.
