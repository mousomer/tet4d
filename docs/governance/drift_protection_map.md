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
- `docs/architecture/first_subsystem_parity_pilot.md`
- `docs/architecture/parity_pilot_audit_and_promotion_gates.md`
- `docs/architecture/second_parity_slice_candidate_selection.md`
- `docs/architecture/trace_metadata_identity_digest_parity.md`
- `docs/architecture/parity_evidence_review_and_third_slice_selection.md`
- `docs/architecture/topology_identifier_normalization_parity.md`
- `docs/architecture/parity_evidence_package_review.md`
- `docs/architecture/python_oracle_boundary_audit.md`
- `docs/architecture/parity_tooling_package_review.md`
- `docs/architecture/structural_parity_slice_selection.md`
- `docs/architecture/trace_envelope_validation_parity.md`
- `docs/architecture/godot_shell_layout_stabilization.md`
- `docs/architecture/godot_shell_settings_source_of_truth.md`
- `docs/architecture/godot_replay_shell_ux_acceptance.md`
- `docs/architecture/godot_visual_style_authority.md`
- `docs/governance/godot_cpp_policy.md`
- `docs/governance/cpp_safety_policy.md`
- `docs/governance/native_tooling_ci_policy.md`
- `docs/governance/testing_policy.md`
- `tools/governance/validate_authority_transfer.py`
- `tools/parity/first_subsystem_parity_pilot.py`
- `tools/parity/trace_metadata_identity_digest_parity.py`
- `native/tet4d_core/tests/trace_metadata_identity_digest_tests.cpp`
- `tests/fixtures/parity/trace_metadata_identity_digest.json`

Required invariants:

- Python remains the current semantic oracle.
- Godot remains shell/presentation unless authority is explicitly transferred.
- C++/GDExtension remains provisional until parity evidence and a completed
  authority-transfer record are documented.
- No policy claims C++ owns gameplay semantics without a transfer record.
- No policy claims GDScript owns topology, movement, collision, gravity,
  rotation, scoring, trace semantics, or replay correctness.
- First parity-pilot evidence stays process-only and does not transfer
  authority.
- Promotion-gate evidence for a second parity slice stays process-only and does
  not transfer authority.
- Second parity implementation must match the selected candidate in
  `docs/architecture/second_parity_slice_candidate_selection.md`.
- Stage 18 implementation evidence must stay within
  `docs/architecture/trace_metadata_identity_digest_parity.md`.
- The third-slice review must stay within
  `docs/architecture/parity_evidence_review_and_third_slice_selection.md`.
- The chosen third slice is topology identifier normalization only.
- Stage 20 topology identifier normalization parity lives in
  `docs/architecture/topology_identifier_normalization_parity.md`.
- Stage 21 parity evidence package review lives in
  `docs/architecture/parity_evidence_package_review.md`.
- Stage 22 trace schema/version normalization parity lives in
  `docs/architecture/trace_schema_version_normalization_parity.md`.
- Stage 23 Python oracle boundary audit lives in
  `docs/architecture/python_oracle_boundary_audit.md`.
- The Python oracle boundary audit must not transfer authority, approve
  semantic Python deletion, or authorize gameplay, topology, trace-event,
  movement, rendering, or Godot implementation changes.
- Stage 24 parity tooling package review lives in
  `docs/architecture/parity_tooling_package_review.md`.
- Stage 24 remains a decision-only review. Stage 25 may move approved parity
  harnesses to `tools/parity/`, but that routing refactor must not add parity
  logic or transfer authority.
- Stage 26 structural parity slice selection lives in
  `docs/architecture/structural_parity_slice_selection.md`.
- Stage 26 selects trace envelope validation for Stage 27 only and must not
  implement a harness, add fixtures, inspect trace events, or transfer
  authority.
- Stage 27 trace envelope validation parity lives in
  `docs/architecture/trace_envelope_validation_parity.md`.
- Stage 27 validates only structural trace envelope fields and must not inspect
  trace event semantics, board snapshots, piece positions, topology traversal,
  movement, rendering, native/Godot implementation, or transfer authority.
- Stage 28 Godot shell layout stabilization lives in
  `docs/architecture/godot_shell_layout_stabilization.md`.
- Stage 29 Godot shell settings registry foundation lives in
  `docs/architecture/godot_shell_settings_source_of_truth.md`.
- Stage 30 Godot replay shell UX acceptance lives in
  `docs/architecture/godot_replay_shell_ux_acceptance.md`.
- Stage 31 Godot visual style authority lives in
  `docs/architecture/godot_visual_style_authority.md`.
- Stage 31 defines Godot product-shell visual direction only and must not
  implement Godot theme resources, add style scripts, port pygame UI history,
  add gameplay/topology/movement settings, create parity evidence, or transfer
  authority.
- Forbidden second-slice areas remain excluded: topology movement, rotation,
  drop/collision, lock/clear/gameplay loop, rendering/projection/view
  semantics, and endgame physics.
- Native tooling CI readiness remains a quality gate and does not imply C++
  semantic authority.
- Trace metadata parity compares exact identity and exact digest only.

## Parity evidence review drift

Surfaces:

- `docs/architecture/parity_protocol.md`
- `docs/architecture/parity_pilot_audit_and_promotion_gates.md`
- `docs/architecture/authority_map.md`
- `docs/architecture/parity_evidence_review_and_third_slice_selection.md`
- `docs/architecture/parity_evidence_package_review.md`
- `docs/governance/README.md`
- `docs/governance/review_checklist.md`
- `docs/DOCUMENTATION_MAP.md`
- `AGENTS.md`
- `native/AGENTS.md`

Required invariants:

- The review compares the first pilot and Stage 18 evidence before choosing
  the third slice.
- The review document names topology identifier normalization as the selected
  third-slice candidate.
- The review stays process-only and does not transfer authority.
- Stage 20 implementation must remain within the selected candidate and avoid
  seam traversal, neighbor lookup, movement semantics, rotation, collision,
  gravity/drop, lock/clear/gameplay loop, rendering/projection/view
  semantics, and endgame physics.
- Further parity work must route through the Stage 21 evidence package review.
- The `tools/migration/` versus `tools/parity/` route decision must remain
  documented.
- Authority transfer remains blocked unless the authority-transfer protocol is
  satisfied.

## Parity evidence package review drift

Surfaces:

- `docs/architecture/parity_evidence_package_review.md`
- `docs/architecture/parity_protocol.md`
- `docs/architecture/parity_pilot_audit_and_promotion_gates.md`
- `docs/governance/README.md`
- `docs/governance/review_checklist.md`
- `docs/governance/drift_protection_map.md`
- `docs/DOCUMENTATION_MAP.md`
- `AGENTS.md`
- `native/AGENTS.md`

Required invariants:

- The package review summarizes Stages 15, 18, and 20.
- The package review does not transfer authority.
- The package review documents the `tools/migration/` versus `tools/parity/`
  route decision.
- The package review records authority-transfer readiness.
- Further parity work must use the package review before expansion.
- Stage 24 supersedes the Stage 21 package route decision only as a decision
  document, and Stage 25 is the isolated routing/refactor that applies that
  decision without semantic changes.

## Parity tooling package review drift

Surfaces:

- `docs/architecture/parity_tooling_package_review.md`
- `docs/architecture/parity_protocol.md`
- `docs/architecture/parity_evidence_package_review.md`
- `docs/architecture/authority_map.md`
- `docs/governance/README.md`
- `docs/governance/drift_protection_map.md`
- `docs/DOCUMENTATION_MAP.md`
- `AGENTS.md`

Required invariants:

- Stage 24 decides package routing only.
- Stage 24 records the package-routing decision only.
- Stage 25 applies the approved isolated `tools/parity/` routing/refactor.
- Stage 24 itself must not have created `tools/parity/` or moved
  `tools/migration/` files.
- Stage 24 must not add parity logic, fixtures, gameplay, topology, rendering,
  Godot, native-code, or authority-transfer changes.

## Trace schema/version parity drift

Surfaces:

- `docs/architecture/trace_schema_version_normalization_parity.md`
- `tools/parity/trace_schema_version_normalization_parity.py`
- `tests/fixtures/parity/trace_schema_version_normalization.json`
- `tests/unit/migration/test_trace_schema_version_normalization_parity.py`

Required invariants:

- Stage 22 remains trace schema/version normalization only.
- The fixture stays schema/version metadata-only and deterministic.
- Default mode is advisory when no safe native/provisional route exists.
- Strict mode with `TET4D_STRICT_PARITY=1` blocks native route unavailability
  and mismatches.
- No authority transfer is claimed.
- Native output is not faked.
- No trace events, board snapshots, topology movement, gameplay, rendering, or
  endgame semantics are allowed.

## Structural parity slice selection drift

Surfaces:

- `docs/architecture/structural_parity_slice_selection.md`
- `docs/architecture/parity_protocol.md`
- `docs/architecture/authority_map.md`
- `docs/governance/README.md`
- `docs/governance/drift_protection_map.md`
- `docs/DOCUMENTATION_MAP.md`

Required invariants:

- Stage 26 selects trace envelope validation for Stage 27.
- Stage 26 does not implement a parity harness or add fixtures.
- Trace envelope validation remains structural and top-level only.
- Trace events, board snapshots, piece positions, topology traversal,
  movement, drop/collision/lock, rendering/view/camera, Godot implementation,
  C++ implementation, and authority transfer remain excluded.

## Trace envelope validation parity drift

Surfaces:

- `docs/architecture/trace_envelope_validation_parity.md`
- `tools/parity/trace_envelope_validation_parity.py`
- `tests/fixtures/parity/trace_envelope_validation.json`
- `tests/unit/migration/test_trace_envelope_validation_parity.py`

Required invariants:

- Stage 27 remains trace envelope validation only.
- The fixture stays envelope-only and deterministic.
- Default mode is advisory when no safe native/provisional route exists.
- Strict mode with `TET4D_STRICT_PARITY=1` blocks native route unavailability
  and mismatches.
- No authority transfer is claimed.
- Native output is not faked.
- No trace event semantics, board snapshots, piece positions, topology
  traversal, movement, drop/collision/lock, rendering, Godot implementation,
  C++ implementation, or authority transfer is allowed.

## Parity pilot drift

Surfaces:

- `docs/architecture/first_subsystem_parity_pilot.md`
- `docs/architecture/parity_pilot_audit_and_promotion_gates.md`
- `docs/architecture/second_parity_slice_candidate_selection.md`
- `docs/architecture/trace_metadata_identity_digest_parity.md`
- `tools/parity/first_subsystem_parity_pilot.py`
- `tools/parity/trace_metadata_identity_digest_parity.py`
- `tests/unit/migration/test_first_subsystem_parity_pilot.py`
- `tests/unit/migration/test_trace_metadata_identity_digest_parity.py`
- `native/tet4d_core/tests/plain_2d_core_tests.cpp`
- `native/tet4d_core/tests/trace_metadata_identity_digest_tests.cpp`
- `tests/fixtures/parity/trace_metadata_identity_digest.json`

Required invariants:

- The pilot compares a fixed, deterministic text fixture set with exact
  string comparison.
- Python remains the oracle for the pilot.
- The audit/gates doc remains reachable from parity and governance routing.
- Any second parity slice must reference the promotion gates before expansion.
- Any second parity implementation must match the selected candidate-selection
  document before expansion.
- The pilot never records a `transferred` authority state.
- The Stage 18 metadata parity slice never records a `transferred` authority
  state.

## Trace metadata parity drift

Surfaces:

- `docs/architecture/trace_metadata_identity_digest_parity.md`
- `tools/parity/trace_metadata_identity_digest_parity.py`
- `tests/unit/migration/test_trace_metadata_identity_digest_parity.py`
- `native/tet4d_core/tests/trace_metadata_identity_digest_tests.cpp`
- `tests/fixtures/parity/trace_metadata_identity_digest.json`

Required invariants:

- The slice compares exact compact canonical metadata identity and exact
  SHA-256 digest.
- The fixture stays metadata-only and deterministic.
- The native path remains provisional and does not transfer authority.
- The slice preserves explicit exclusions for movement, rotation, collision,
  rendering, and endgame semantics.

## Topology identifier parity drift

Surfaces:

- `docs/architecture/topology_identifier_normalization_parity.md`
- `tools/parity/topology_identifier_normalization_parity.py`
- `tests/fixtures/parity/topology_identifier_normalization.json`
- `tests/unit/migration/test_topology_identifier_normalization_parity.py`

Required invariants:

- Stage 20 remains topology identifier normalization only.
- The fixture stays identifier-only and deterministic.
- Default mode is advisory when the native/provisional route is unavailable.
- Strict mode blocks unavailability and mismatches.
- No authority transfer is claimed.
- No seam traversal, movement, or gameplay semantics are allowed.

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
- Native tooling validation preserves local advisory mode and strict
  `TET4D_STRICT_NATIVE_TOOLS=1` behavior.

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
- strict native tooling CI enforcement until the native compile database and
  clang tools are reproducible
