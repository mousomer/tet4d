# Tet4D Drift Protection Map

This tet4d-specific map records durable drift surfaces. General policy lives in
`docs/governance/workspace_bundle/drift_protection_policy.md`; completed stage
narratives remain in their owning evidence documents and history.

## Stable drift classes

The table consolidates governance routing drift, authority drift, and
config/generated drift into capability-based checks.

| Class | Primary surfaces | Required invariants |
| --- | --- | --- |
| Governance routing | `AGENTS.md`, local `AGENTS.md`, `docs/governance/README.md`, `docs/governance/review_checklist.md`, `.github/pull_request_template.md` | One machine policy source; local rules only tighten; new governance is reachable; task and completion contracts remain routed |
| Semantic authority | `docs/architecture/authority_map.md`, parity and transfer protocols, relevant RDS | Python remains oracle unless a completed named transfer exists; Godot is presentation; native authority is explicit and reversible |
| Validation | `tools/governance/validate_governance.py` and its validators | Validators are wired, deterministic, actionable, and do not become a second policy inventory |
| Config/generated | config policy, `config/project/policy_pack.json`, generators, generated references/bundles | Generated files identify source/generator and are not hand-authored authority |
| Debt/advisories | technical-debt register and advisory validators | New warnings are classified; suppressions are narrow or recorded |
| Utility reuse | utility index, reuse policy, reuse validators | Search-first and shared-helper ownership remain consistent |
| Native safety/tooling | native safety/tooling policies and native checks | Ownership/lifetime rules hold; local advisory and strict CI modes remain distinct |
| Repository hygiene | sanitation scripts, Git staging, PR/review contracts | One objective per PR; no unrelated staging; diff and sanitation gates pass |

## Active governance surfaces

- `AGENTS.md`
- `godot/AGENTS.md`
- `native/AGENTS.md`
- `docs/WORKFLOW_CODEX.md`
- `docs/governance/README.md`
- `docs/governance/task_contract.md`
- `docs/governance/completion_report.md`
- `docs/governance/review_checklist.md`
- `docs/governance/workspace_bundle/review_checklist_template.md`
- `.github/pull_request_template.md`
- `config/project/policy_pack.json`
- `docs/architecture/authority_transfer_protocol.md`
- `tools/governance/validate_authority_transfer.py`

## Validator integration

- `tools/governance/validate_governance.py`
- `tools/governance/validate_project_contracts.py`
- `tools/governance/validate_workspace_bundle.py`
- `tools/governance/validate_technical_debt.py`
- `tools/governance/validate_config_authority.py`
- `tools/governance/validate_utility_reuse.py`
- `tools/governance/validate_godot_semantic_boundary.py`
- `tools/governance/validate_live_board_visual_roles.py`
- `tools/governance/validate_native_cpp_tooling.py`
- `tools/governance/validate_drift_protection.py`
- `tools/governance/validate_authority_transfer.py`

Active validators must be called by the unified governance runner where
applicable. The project-contract validator interprets
`config/project/policy_pack.json`; it must not duplicate policy-shaped
inventories in Python.

## Historical parity evidence manifest

These paths remain validated evidence and are consulted conditionally through
`docs/architecture/parity_protocol.md`. Their completed sequencing is not a
universal task checklist.

Documents:

- `docs/architecture/first_subsystem_parity_pilot.md`
- `docs/architecture/parity_pilot_audit_and_promotion_gates.md`
- `docs/architecture/second_parity_slice_candidate_selection.md`
- `docs/architecture/trace_metadata_identity_digest_parity.md`
- `docs/architecture/parity_evidence_review_and_third_slice_selection.md`
- `docs/architecture/topology_identifier_normalization_parity.md`
- `docs/architecture/parity_evidence_package_review.md`
- `docs/architecture/trace_schema_version_normalization_parity.md`
- `docs/architecture/python_oracle_boundary_audit.md`
- `docs/architecture/parity_tooling_package_review.md`
- `docs/architecture/structural_parity_slice_selection.md`
- `docs/architecture/trace_envelope_validation_parity.md`

Harnesses, fixtures, and tests:

- `tools/parity/first_subsystem_parity_pilot.py`
- `tests/unit/migration/test_first_subsystem_parity_pilot.py`
- `tools/parity/trace_metadata_identity_digest_parity.py`
- `tests/unit/migration/test_trace_metadata_identity_digest_parity.py`
- `native/tet4d_core/tests/trace_metadata_identity_digest_tests.cpp`
- `tests/fixtures/parity/trace_metadata_identity_digest.json`
- `tools/parity/topology_identifier_normalization_parity.py`
- `tests/unit/migration/test_topology_identifier_normalization_parity.py`
- `tests/fixtures/parity/topology_identifier_normalization.json`
- `tools/parity/trace_schema_version_normalization_parity.py`
- `tests/unit/migration/test_trace_schema_version_normalization_parity.py`
- `tests/fixtures/parity/trace_schema_version_normalization.json`
- `tools/parity/trace_envelope_validation_parity.py`
- `tests/unit/migration/test_trace_envelope_validation_parity.py`
- `tests/fixtures/parity/trace_envelope_validation.json`

The historical tooling route decision between `tools/migration/` and
`tools/parity/` remains recorded in the owning evidence. All evidence remains
process-only until the authority-transfer protocol is completed.

## Generated and config surfaces

- `docs/CONFIGURATION_REFERENCE.md`
- `docs/USER_SETTINGS_REFERENCE.md`
- `migration/exported_bundle/`
- `migration/exported_bundle/manifest.json`
- `migration/exported_bundle/docs/authority_index.json`
- `migration/exported_bundle/config/tet4d_config_bundle.json`
- `tools/governance/generate_configuration_reference.py`
- `tools/governance/generate_maintenance_docs.py`
- `tools/migration/export_config_bundle.py`

## Deferred strictness

- one-to-one mapping of every advisory finding to a debt record;
- exhaustive TODO/FIXME debt coverage;
- strict native tooling CI until clang tools and a compile database are
  reproducible.
