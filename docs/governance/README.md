# Governance Router

This repository is Python-centered. Godot/C++ migration governance is an
overlay, not a replacement for existing Python/repo governance.

## Applies everywhere

- reusable workspace governance: `docs/governance/workspace_bundle/`
- machine-readable governance authority: `config/project/policy_pack.json`
- Codex workflow policy: `docs/governance/codex_policy.md`
- repo workflow explainer: `docs/WORKFLOW_CODEX.md`
- existing repo policies under `docs/policies/`
- secrets/security policy: `docs/governance/secrets_policy.md`
- config/constants policy: `docs/governance/config_policy.md`
- config authority validator:
  `tools/governance/validate_config_authority.py`
- native C++ safety policy: `docs/governance/cpp_safety_policy.md`
- native tooling CI policy:
  `docs/governance/native_tooling_ci_policy.md`
- first subsystem parity pilot:
  `docs/architecture/first_subsystem_parity_pilot.md`
- parity pilot audit and promotion gates:
  `docs/architecture/parity_pilot_audit_and_promotion_gates.md`
- second parity slice candidate selection:
  `docs/architecture/second_parity_slice_candidate_selection.md`
- trace metadata identity/digest parity:
  `docs/architecture/trace_metadata_identity_digest_parity.md`
- parity evidence review and third-slice selection:
  `docs/architecture/parity_evidence_review_and_third_slice_selection.md`
- topology identifier normalization parity:
  `docs/architecture/topology_identifier_normalization_parity.md`,
  `tools/migration/topology_identifier_normalization_parity.py`,
  `tests/fixtures/parity/topology_identifier_normalization.json`
- parity evidence package review:
  `docs/architecture/parity_evidence_package_review.md`
- trace schema/version normalization parity:
  `docs/architecture/trace_schema_version_normalization_parity.md`,
  `tools/migration/trace_schema_version_normalization_parity.py`,
  `tests/fixtures/parity/trace_schema_version_normalization.json`
- Python oracle boundary audit:
  `docs/architecture/python_oracle_boundary_audit.md`
- parity tooling package review:
  `docs/architecture/parity_tooling_package_review.md`
- testing policy: `docs/governance/testing_policy.md`
- review checklist: `docs/governance/review_checklist.md`
- GitHub PR template: `.github/pull_request_template.md`
- dependency/reuse policy: `docs/policies/POLICY_NO_REINVENTING_WHEEL.md`
- utility index: `docs/architecture/utility_index.md`
- utility reuse validator:
  `tools/governance/validate_utility_reuse.py`
- existing wheel/dedup checks:
  `tools/governance/check_wheel_reuse_rules.py` and
  `tools/governance/check_dedup_dead_code_rules.py`
- technical debt register:
  `docs/governance/technical_debt_register.md`
- technical debt validator:
  `tools/governance/validate_technical_debt.py`

## Reusable workspace governance

General programming rules live in `docs/governance/workspace_bundle/`.

The workspace bundle is reusable across projects. It does not define
tet4d-specific authority.

tet4d-specific rules live in this router,
`docs/architecture/authority_map.md`, `docs/architecture/parity_protocol.md`,
and the project overlay policies in `docs/governance/`.

## Review and PR checks

Reusable review guidance lives in
`docs/governance/workspace_bundle/review_checklist_template.md`.

tet4d-specific review checks live in `docs/governance/review_checklist.md`.

The GitHub PR template lives in `.github/pull_request_template.md`.

Project-contract validation checks that the review surfaces remain routed.
Stage 20 topology identifier normalization parity routing is also validated.
Stage 21 parity evidence package review routing is also validated.
Stage 22 trace schema/version normalization parity routing is also validated.
Stage 23 Python oracle boundary audit routing is also validated by governance
reachability.
Stage 24 parity tooling package review routing is also validated by governance
reachability.

## Technical debt and drift protection

General debt schema and calculations live in
`docs/governance/workspace_bundle/technical_debt_policy.md`.

General drift-protection principles live in
`docs/governance/workspace_bundle/drift_protection_policy.md`.

tet4d-specific debt items live in
`docs/governance/technical_debt_register.md`.

Debt validation is handled by
`tools/governance/validate_technical_debt.py`.

tet4d-specific drift surfaces live in
`docs/governance/drift_protection_map.md`.

Drift validation is handled by
`tools/governance/validate_drift_protection.py`.

## Applies to current Python implementation

- `docs/ARCHITECTURE_CONTRACT.md`
- relevant `docs/rds/*`
- current tests and trace behavior
- current semantic implementation under `src/tet4d/`

## Applies to Godot/C++ migration

- Godot/C++ migration policy: `docs/governance/godot_cpp_policy.md`
- native C++ safety policy: `docs/governance/cpp_safety_policy.md`
- native tooling CI policy:
  `docs/governance/native_tooling_ci_policy.md`
- native C++ tooling validator:
  `tools/governance/validate_native_cpp_tooling.py`
- architecture authority map: `docs/architecture/authority_map.md`
- parity protocol: `docs/architecture/parity_protocol.md`
- first subsystem parity pilot:
  `docs/architecture/first_subsystem_parity_pilot.md`
- parity pilot audit and promotion gates:
  `docs/architecture/parity_pilot_audit_and_promotion_gates.md`
- second parity slice candidate selection:
  `docs/architecture/second_parity_slice_candidate_selection.md`
- trace metadata identity/digest parity:
  `docs/architecture/trace_metadata_identity_digest_parity.md`
- parity evidence review and third-slice selection:
  `docs/architecture/parity_evidence_review_and_third_slice_selection.md`
- parity evidence package review:
  `docs/architecture/parity_evidence_package_review.md`
- trace schema/version normalization parity:
  `docs/architecture/trace_schema_version_normalization_parity.md`
- Python oracle boundary audit:
  `docs/architecture/python_oracle_boundary_audit.md`
- parity tooling package review:
  `docs/architecture/parity_tooling_package_review.md`
- authority-transfer protocol:
  `docs/architecture/authority_transfer_protocol.md`
- authority-transfer validator:
  `tools/governance/validate_authority_transfer.py`
- migration plan: `docs/plans/godot_core_port_plan.md`
- topology migration plan: `docs/plans/topology_godot_core_port_plan.md`
- utility index: `docs/architecture/utility_index.md`
- relevant local `AGENTS.md` files

## Work-type routing

| Work type | Read first |
|---|---|
| Python gameplay/topology/trace behavior | `AGENTS.md`, `docs/WORKFLOW_CODEX.md`, `docs/ARCHITECTURE_CONTRACT.md`, relevant `docs/rds/*` |
| Godot UI/product shell | `AGENTS.md`, `godot/AGENTS.md`, `docs/governance/godot_cpp_policy.md`, `docs/architecture/authority_map.md` |
| C++/GDExtension/native | `AGENTS.md`, `native/AGENTS.md`, `docs/governance/godot_cpp_policy.md`, `docs/governance/cpp_safety_policy.md`, `docs/governance/native_tooling_ci_policy.md`, `docs/architecture/parity_protocol.md`, `docs/architecture/first_subsystem_parity_pilot.md`, `docs/architecture/parity_pilot_audit_and_promotion_gates.md`, `docs/architecture/second_parity_slice_candidate_selection.md`, `docs/architecture/trace_metadata_identity_digest_parity.md`, `docs/architecture/trace_schema_version_normalization_parity.md`, `docs/architecture/authority_map.md` |
| Testing/parity | `docs/architecture/parity_protocol.md`, `docs/architecture/first_subsystem_parity_pilot.md`, `docs/architecture/parity_pilot_audit_and_promotion_gates.md`, `docs/architecture/second_parity_slice_candidate_selection.md`, `docs/architecture/trace_metadata_identity_digest_parity.md`, `docs/architecture/parity_evidence_package_review.md`, `docs/architecture/trace_schema_version_normalization_parity.md`, `docs/governance/testing_policy.md`, relevant test docs and trace plans |
| Python oracle boundary audit | `docs/architecture/authority_map.md`, `docs/architecture/python_oracle_boundary_audit.md`, `docs/architecture/parity_protocol.md`, relevant Python gameplay/topology/trace surfaces |
| Parity tooling/package review | `docs/architecture/parity_tooling_package_review.md`, `docs/architecture/parity_protocol.md`, `docs/architecture/parity_evidence_package_review.md`, current `tools/migration/*parity*.py` harnesses |
| Config/constants | `docs/governance/config_policy.md`, `docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md`, `docs/policies/POLICY_NO_MAGIC_NUMBERS.md`, `tools/governance/validate_config_authority.py` |
| Dependency / utility reuse | `docs/policies/POLICY_NO_REINVENTING_WHEEL.md`, `docs/architecture/utility_index.md`, `tools/governance/validate_utility_reuse.py`, `tools/governance/check_wheel_reuse_rules.py`, `tools/governance/check_dedup_dead_code_rules.py` |
| Technical debt / drift foundations | `docs/governance/technical_debt_register.md`, `docs/governance/workspace_bundle/technical_debt_policy.md`, `docs/governance/workspace_bundle/drift_protection_policy.md`, `tools/governance/validate_technical_debt.py` |
| Secrets/security | `docs/governance/secrets_policy.md`, `config/project/policy/manifests/secret_scan.json` |
| Mixed migration | all relevant Python, Godot, native, testing, config, and authority docs above |

## Authority rule

The existing Python implementation is the semantic oracle. Godot and C++ code
are ports/adapters until explicitly promoted by documented parity evidence.
Promotion also requires
`docs/architecture/authority_transfer_protocol.md`; parity evidence alone does
not transfer authority. First parity-pilot evidence is process-only and does
not transfer authority. Governance validation also checks that parity routing
and promotion-gate routing remain intact. Governance validation also checks
 second parity slice candidate-selection routing, the trace metadata
 identity/digest parity route, and the parity evidence review and third-slice
 selection route. Governance validation also checks the Stage 21 parity
 evidence package review route and the Stage 22 trace schema/version
 normalization parity route. Stage 23 Python oracle boundary audit keeps
 Python gameplay semantics and golden traces authoritative while marking
 incidental Python UI/history as non-authoritative for porting. Stage 24
 parity tooling package review approves a future Stage 25 `tools/parity/`
 routing/refactor only; it does not move files or transfer authority.

## Conflict rule

When documents conflict:

1. Safety/security rules win over convenience.
2. Existing Python semantics win over migration convenience.
3. The authority map decides ownership.
4. Folder-local `AGENTS.md` may add narrower constraints but must not weaken
   root constraints.
5. New Godot/C++ governance may clarify migration work but must not silently
   supersede existing Python governance.
