from __future__ import annotations

from pathlib import Path

import tools.governance.validate_drift_protection as drift


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _manifest(*files: str) -> str:
    rows = [
        "# Workspace Governance Bundle Manifest",
        "",
        "| File | Purpose | Copy target | Project customization required? |",
        "|---|---|---|---|",
    ]
    for filename in files:
        rows.append(
            f"| `{filename}` | Purpose | `docs/governance/workspace_bundle/` | No |"
        )
    return "\n".join(rows) + "\n"


def _valid_fixture(root: Path) -> None:
    _write(
        root / "AGENTS.md",
        "docs/governance/workspace_bundle/programming_policy.md\n"
        "docs/governance/workspace_bundle/drift_protection_policy.md\n"
        "docs/architecture/parity_evidence_review_and_third_slice_selection.md\n"
        "docs/architecture/topology_identifier_normalization_parity.md\n"
        "docs/architecture/parity_evidence_package_review.md\n"
        "docs/architecture/trace_schema_version_normalization_parity.md\n"
        "docs/architecture/authority_map.md\n",
    )
    _write(root / "godot" / "AGENTS.md", "Godot UI only.\n")
    _write(
        root / "native" / "AGENTS.md",
        "Native C++ only. docs/architecture/topology_identifier_normalization_parity.md\n"
        "Native C++ only. docs/architecture/trace_schema_version_normalization_parity.md\n",
    )
    _write(
        root / "docs" / "governance" / "README.md",
        ".github/pull_request_template.md\n"
        "docs/governance/workspace_bundle/review_checklist_template.md\n"
        "docs/governance/workspace_bundle/drift_protection_policy.md\n"
        "docs/governance/drift_protection_map.md\n"
        "docs/architecture/first_subsystem_parity_pilot.md\n"
        "docs/architecture/parity_pilot_audit_and_promotion_gates.md\n"
        "docs/architecture/second_parity_slice_candidate_selection.md\n"
        "docs/architecture/trace_metadata_identity_digest_parity.md\n"
        "docs/architecture/parity_evidence_review_and_third_slice_selection.md\n"
        "docs/architecture/topology_identifier_normalization_parity.md\n"
        "docs/architecture/parity_evidence_package_review.md\n"
        "docs/architecture/trace_schema_version_normalization_parity.md\n"
        "topology identifier normalization\n"
        "trace schema/version normalization\n"
        "docs/governance/technical_debt_register.md\n"
        "docs/governance/native_tooling_ci_policy.md\n"
        "tools/governance/validate_drift_protection.py\n"
        "tools/governance/validate_technical_debt.py\n"
        "docs/governance/review_checklist.md\n"
        "docs/governance/config_policy.md\n"
        "docs/governance/godot_cpp_policy.md\n"
        "docs/governance/cpp_safety_policy.md\n"
        "docs/governance/testing_policy.md\n",
    )
    _write(
        root / "docs" / "governance" / "review_checklist.md",
        "technical debt\ntechnical-debt\n"
        "drift protection\n"
        "authority\n"
        "config/generated generated outputs\n"
        "dependency / utility reuse\n"
        "godot semantic boundary\n"
        "native c++ safety\n"
        "native tooling ci readiness\n"
        "first parity pilot\n"
        "promotion gates\n"
        "parity\n"
        "tools/governance/validate_governance.py\n",
    )
    _write(
        root / ".github" / "pull_request_template.md",
        "authority\ntechnical debt\ndrift protection\nvalidation\n"
        "native tooling TET4D_STRICT_NATIVE_TOOLS\n"
        "git diff --cached --check\n",
    )
    _write(
        root / "docs" / "governance" / "technical_debt_register.md",
        "docs/governance/workspace_bundle/technical_debt_policy.md\n"
        "docs/governance/workspace_bundle/drift_protection_policy.md\n",
    )
    _write(
        root / "docs" / "governance" / "drift_protection_map.md",
        "tet4d-specific drift surfaces\n"
        "docs/governance/workspace_bundle/drift_protection_policy.md\n"
        "docs/governance/review_checklist.md\n"
        "docs/governance/technical_debt_register.md\n"
        "docs/governance/config_policy.md\n"
        "docs/governance/godot_cpp_policy.md\n"
        "docs/governance/cpp_safety_policy.md\n"
        "docs/governance/native_tooling_ci_policy.md\n"
        "docs/governance/testing_policy.md\n"
        "docs/architecture/authority_map.md\n"
        "docs/architecture/parity_protocol.md\n"
        "docs/architecture/authority_transfer_protocol.md\n"
        "docs/architecture/first_subsystem_parity_pilot.md\n"
        "docs/architecture/parity_pilot_audit_and_promotion_gates.md\n"
        "docs/architecture/second_parity_slice_candidate_selection.md\n"
        "docs/architecture/trace_metadata_identity_digest_parity.md\n"
        "docs/architecture/parity_evidence_review_and_third_slice_selection.md\n"
        "docs/architecture/topology_identifier_normalization_parity.md\n"
        "docs/architecture/parity_evidence_package_review.md\n"
        "docs/architecture/trace_schema_version_normalization_parity.md\n"
        "docs/architecture/utility_index.md\n"
        "governance routing drift\n"
        "authority drift\n"
        "config/generated drift\n"
        "selected candidate\n"
        "forbidden second-slice areas\n"
        "tools/migration/first_subsystem_parity_pilot.py\n"
        "tools/migration/trace_metadata_identity_digest_parity.py\n"
        "tools/migration/topology_identifier_normalization_parity.py\n"
        "tools/migration/trace_schema_version_normalization_parity.py\n"
        "tests/unit/migration/test_first_subsystem_parity_pilot.py\n"
        "tests/unit/migration/test_trace_metadata_identity_digest_parity.py\n"
        "tests/unit/migration/test_topology_identifier_normalization_parity.py\n"
        "tests/unit/migration/test_trace_schema_version_normalization_parity.py\n"
        "native/tet4d_core/tests/trace_metadata_identity_digest_tests.cpp\n"
        "tests/fixtures/parity/trace_metadata_identity_digest.json\n"
        "tests/fixtures/parity/topology_identifier_normalization.json\n"
        "tests/fixtures/parity/trace_schema_version_normalization.json\n"
        "tools/migration/export_config_bundle.py\n"
        "tools/governance/generate_configuration_reference.py\n"
        "tools/governance/validate_authority_transfer.py\n",
    )
    _write(
        root / "docs" / "governance" / "drift_protection_map.md",
        "tet4d-specific drift surfaces\n"
        "docs/governance/workspace_bundle/drift_protection_policy.md\n"
        "docs/governance/review_checklist.md\n"
        "docs/governance/technical_debt_register.md\n"
        "docs/governance/config_policy.md\n"
        "docs/governance/godot_cpp_policy.md\n"
        "docs/governance/cpp_safety_policy.md\n"
        "docs/governance/native_tooling_ci_policy.md\n"
        "docs/governance/testing_policy.md\n"
        "docs/architecture/authority_map.md\n"
        "docs/architecture/parity_protocol.md\n"
        "docs/architecture/authority_transfer_protocol.md\n"
        "docs/architecture/first_subsystem_parity_pilot.md\n"
        "docs/architecture/parity_pilot_audit_and_promotion_gates.md\n"
        "docs/architecture/second_parity_slice_candidate_selection.md\n"
        "docs/architecture/trace_metadata_identity_digest_parity.md\n"
        "docs/architecture/parity_evidence_review_and_third_slice_selection.md\n"
        "docs/architecture/topology_identifier_normalization_parity.md\n"
        "docs/architecture/parity_evidence_package_review.md\n"
        "docs/architecture/trace_schema_version_normalization_parity.md\n"
        "docs/architecture/utility_index.md\n"
        "governance routing drift\n"
        "authority drift\n"
        "config/generated drift\n"
        "selected candidate\n"
        "forbidden second-slice areas\n"
        "tools/migration/first_subsystem_parity_pilot.py\n"
        "tools/migration/trace_metadata_identity_digest_parity.py\n"
        "tools/migration/topology_identifier_normalization_parity.py\n"
        "tools/migration/trace_schema_version_normalization_parity.py\n"
        "tests/unit/migration/test_first_subsystem_parity_pilot.py\n"
        "tests/unit/migration/test_trace_metadata_identity_digest_parity.py\n"
        "tests/unit/migration/test_topology_identifier_normalization_parity.py\n"
        "tests/unit/migration/test_trace_schema_version_normalization_parity.py\n"
        "native/tet4d_core/tests/trace_metadata_identity_digest_tests.cpp\n"
        "tests/fixtures/parity/trace_metadata_identity_digest.json\n"
        "tests/fixtures/parity/topology_identifier_normalization.json\n"
        "tests/fixtures/parity/trace_schema_version_normalization.json\n"
        "tools/migration/export_config_bundle.py\n"
        "tools/governance/generate_configuration_reference.py\n"
        "tools/governance/validate_authority_transfer.py\n"
        "trace metadata parity drift\n"
        "trace metadata identity/digest parity\n"
        "exact identity\n"
        "exact digest\n"
        "topology identifier parity drift\n"
        "topology identifier normalization parity\n"
        "identifier-only\n"
        "default mode is advisory\n"
        "strict mode blocks unavailability\n"
        "parity evidence package review drift\n"
        "parity evidence package review\n"
        "trace schema/version normalization parity\n"
        "tools/migration/\n"
        "tools/parity/\n",
    )
    _write(
        root / "docs" / "architecture" / "trace_metadata_identity_digest_parity.md",
        "Stage 18 trace metadata identity/digest parity. "
        "Python oracle trace_schema.py. "
        "Metadata-only fixture. "
        "Exact comparison only. "
        "This slice does not transfer authority.\n",
    )
    _write(
        root
        / "docs"
        / "architecture"
        / "parity_evidence_review_and_third_slice_selection.md",
        "Stage 19 parity evidence review and third-slice selection. "
        "Python remains the semantic oracle. "
        "Reviewed the first pilot and Stage 18 evidence. "
        "Topology identifier normalization only. "
        "This review does not transfer authority. "
        "Stage 20 implementation may only implement topology identifier normalization.\n",
    )
    _write(
        root / "docs" / "architecture" / "topology_identifier_normalization_parity.md",
        "Stage 20 topology identifier normalization parity. "
        "Python remains the semantic oracle. "
        "The slice is identifier-only. "
        "This slice does not transfer authority. "
        "Default mode is advisory when the native/provisional route is unavailable. "
        "Strict mode TET4D_STRICT_PARITY blocks that unavailability. "
        "Explicit exclusions: seam traversal, neighbor lookup, topology movement, "
        "rendering/projection/view/camera, and endgame physics. "
        "Harness tools/migration/topology_identifier_normalization_parity.py. "
        "Fixture tests/fixtures/parity/topology_identifier_normalization.json. "
        "Canonical identifiers plain_2d wrap_all_4d invert_all_4d sphere_like_4d. "
        "Exact equality comparison.\n",
    )
    _write(
        root / "docs" / "architecture" / "parity_evidence_package_review.md",
        "Stage 21 parity evidence package review. "
        "Reviews Stage 15 first pilot, Stage 18 trace metadata, and Stage 20 topology identifier evidence. "
        "This evidence package review does not transfer authority. "
        "The tooling route decision keeps tools/migration/ and defers tools/parity/.\n",
    )
    _write(
        root / "docs" / "architecture" / "trace_schema_version_normalization_parity.md",
        "Stage 22 trace schema/version normalization parity. "
        "Python remains the semantic oracle. "
        "The slice is schema/version metadata-only. "
        "Default mode is advisory when no safe native/provisional route exists. "
        "Strict mode TET4D_STRICT_PARITY=1 blocks unavailability. "
        "No safe native/provisional route exists. "
        "This slice does not transfer authority. "
        "Explicit exclusions: trace events, board snapshots, topology movement, "
        "gameplay, rendering, and endgame physics.\n",
    )
    _write(
        root
        / "docs"
        / "governance"
        / "workspace_bundle"
        / "drift_protection_policy.md",
        "# Drift Protection Policy\nReusable guidance.\n",
    )
    _write(
        root
        / "docs"
        / "governance"
        / "workspace_bundle"
        / "review_checklist_template.md",
        "# Review Checklist Template\nReusable guidance.\n",
    )
    _write(
        root / "docs" / "governance" / "workspace_bundle" / "MANIFEST.md",
        _manifest(
            "drift_protection_policy.md",
            "review_checklist_template.md",
            "MANIFEST.md",
        ),
    )
    _write(
        root / "docs" / "architecture" / "authority_map.md",
        "Python is the current semantic oracle. Godot is the product shell and "
        "presentation layer. C++/GDExtension is provisional until parity. "
        "Stage 20 docs/architecture/topology_identifier_normalization_parity.md "
        "topology identifier normalization does not transfer authority. "
        "Stage 21 docs/architecture/parity_evidence_package_review.md provisional evidence. "
        "Stage 22 docs/architecture/trace_schema_version_normalization_parity.md "
        "schema/version metadata evidence.\n",
    )
    _write(
        root / "docs" / "architecture" / "parity_protocol.md",
        "Python oracle. Golden fixtures and golden traces. Comparison mode. "
        "Authority transfer and subsystem promotion. "
        "First subsystem parity pilot stays evidence only. "
        "docs/architecture/parity_pilot_audit_and_promotion_gates.md "
        "before a second parity slice. "
        "Stage 18 trace metadata identity/digest parity evidence and "
        "implementation details live in "
        "docs/architecture/trace_metadata_identity_digest_parity.md. "
        "Stage 19 evidence review and third-slice selection live in "
        "docs/architecture/parity_evidence_review_and_third_slice_selection.md. "
        "Stage 20 docs/architecture/topology_identifier_normalization_parity.md "
        "topology identifier normalization does not transfer authority. "
        "Stage 21 docs/architecture/parity_evidence_package_review.md does not transfer authority. "
        "Stage 22 docs/architecture/trace_schema_version_normalization_parity.md "
        "trace schema/version normalization. "
        "docs/architecture/second_parity_slice_candidate_selection.md.\n",
    )
    _write(
        root / "docs" / "architecture" / "authority_transfer_protocol.md",
        "Python remains the semantic oracle. Authority transfer protocol. "
        "First subsystem parity pilot stays evidence only.\n",
    )
    _write(
        root / "docs" / "architecture" / "parity_pilot_audit_and_promotion_gates.md",
        "Python remains the semantic oracle. "
        "This evidence does not transfer authority. "
        "Promotion gates are required before a second parity slice. "
        "selected Stage 18 trace metadata identity/digest parity "
        "implementation doc docs/architecture/trace_metadata_identity_digest_parity.md. "
        "docs/architecture/parity_evidence_review_and_third_slice_selection.md. "
        "docs/architecture/topology_identifier_normalization_parity.md. "
        "docs/architecture/parity_evidence_package_review.md. "
        "docs/architecture/trace_schema_version_normalization_parity.md "
        "schema/version metadata.\n",
    )
    _write(
        root / "docs" / "architecture" / "second_parity_slice_candidate_selection.md",
        "Chosen candidate: trace metadata identity/digest. "
        "Decision status: selected. "
        "Stage 18 implementation allowed: yes. "
        "Python remains the semantic oracle. "
        "Native/C++ remains provisional. "
        "Candidate selection does not transfer authority. "
        "Explicit exclusions: topology movement, rotation, drop/collision, "
        "rendering/projection/view, endgame physics.\n",
    )
    _write(root / "docs" / "architecture" / "utility_index.md", "Utility index.\n")
    _write(
        root / "docs" / "governance" / "godot_cpp_policy.md",
        "GDScript must not implement semantic truth for topology, movement, "
        "collision, gravity, rotation, scoring, trace semantics, or replay semantics.\n",
    )
    _write(root / "docs" / "governance" / "cpp_safety_policy.md", "C++ safety.\n")
    _write(
        root / "docs" / "governance" / "native_tooling_ci_policy.md",
        "Local advisory mode. Local strict mode. CI strict mode. "
        "compile_commands.json. Python remains the semantic oracle. "
        "docs/architecture/authority_transfer_protocol.md.\n",
    )
    _write(root / "docs" / "governance" / "testing_policy.md", "Testing parity.\n")
    _write(
        root / "docs" / "governance" / "config_policy.md",
        "Generated from those sources. config/project/constants.json\n",
    )
    _write(
        root / "docs" / "policies" / "INDEX.md",
        "docs/policies/POLICY_NO_MAGIC_NUMBERS.md\n",
    )
    _write(
        root / "docs" / "policies" / "POLICY_NO_MAGIC_NUMBERS.md",
        "No magic numbers policy.\n",
    )
    _write(
        root / "tools" / "governance" / "validate_governance.py",
        "\n".join(validator.removesuffix(".py") for validator in drift.VALIDATORS),
    )
    for rel in drift.REQUIRED_FILES:
        path = root / rel
        if path.exists():
            continue
        _write(path, "def main():\n    return 0\n" if rel.endswith(".py") else "doc\n")


def _messages(results: list[drift.CheckResult]) -> list[str]:
    return [failure for result in results for failure in result.failures]


def test_valid_minimal_fixture_passes(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)

    assert _messages(drift.validate(tmp_path)) == []


def test_parity_package_review_missing_doc_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    (tmp_path / "docs" / "architecture" / "parity_evidence_package_review.md").unlink()

    failures = _messages(drift.validate(tmp_path))

    assert any("parity_evidence_package_review.md" in item for item in failures)


def test_parity_package_review_missing_protocol_route_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    protocol = tmp_path / "docs" / "architecture" / "parity_protocol.md"
    protocol.write_text(
        protocol.read_text(encoding="utf-8").replace(
            "Stage 21 docs/architecture/parity_evidence_package_review.md does not transfer authority. ",
            "",
        ),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("parity evidence package review" in item for item in failures)


def test_parity_package_review_missing_tooling_route_decision_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    drift_map = tmp_path / "docs" / "governance" / "drift_protection_map.md"
    drift_map.write_text(
        drift_map.read_text(encoding="utf-8").replace("tools/parity/\n", ""),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("tools/migration vs tools/parity" in item for item in failures)


def test_missing_drift_map_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    (tmp_path / "docs" / "governance" / "drift_protection_map.md").unlink()

    failures = _messages(drift.validate(tmp_path))

    assert any("drift_protection_map.md" in failure for failure in failures)


def test_router_missing_drift_map_link_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    router = tmp_path / "docs" / "governance" / "README.md"
    router.write_text(
        router.read_text(encoding="utf-8").replace(
            "docs/governance/drift_protection_map.md\n", ""
        ),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any(
        "does not link to docs/governance/drift_protection_map.md" in item
        for item in failures
    )


def test_router_missing_drift_validator_link_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    router = tmp_path / "docs" / "governance" / "README.md"
    router.write_text(
        router.read_text(encoding="utf-8").replace(
            "tools/governance/validate_drift_protection.py\n", ""
        ),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any(
        "does not link to tools/governance/validate_drift_protection.py" in item
        for item in failures
    )


def test_root_agents_missing_workspace_drift_policy_link_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        agents.read_text(encoding="utf-8").replace(
            "docs/governance/workspace_bundle/drift_protection_policy.md\n", ""
        ),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("AGENTS.md does not link" in item for item in failures)


def test_governance_runner_missing_drift_validator_reference_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    runner = tmp_path / "tools" / "governance" / "validate_governance.py"
    runner.write_text(
        runner.read_text(encoding="utf-8").replace("validate_drift_protection", ""),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("validate_drift_protection.py" in item for item in failures)


def test_governance_runner_missing_authority_transfer_validator_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    runner = tmp_path / "tools" / "governance" / "validate_governance.py"
    runner.write_text(
        runner.read_text(encoding="utf-8").replace("validate_authority_transfer", ""),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("validate_authority_transfer.py" in item for item in failures)


def test_workspace_bundle_authority_transfer_protocol_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path
        / "docs"
        / "governance"
        / "workspace_bundle"
        / "authority_transfer_protocol.md",
        "Project authority transfer.\n",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("authority-transfer protocol" in item for item in failures)


def test_authority_map_missing_python_oracle_concept_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "architecture" / "authority_map.md",
        "Godot is product shell. C++ is provisional until parity.\n",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("Python semantic oracle" in item for item in failures)


def test_authority_map_missing_godot_shell_concept_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "architecture" / "authority_map.md",
        "Python is the semantic oracle. C++ is provisional until parity.\n",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("Godot shell/presentation" in item for item in failures)


def test_authority_map_missing_cpp_provisional_concept_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "architecture" / "authority_map.md",
        "Python is the semantic oracle. Godot is product shell presentation.\n",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("C++ provisional until parity" in item for item in failures)


def test_godot_policy_missing_semantic_boundary_concepts_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "godot_cpp_policy.md",
        "GDScript is presentation only.\n",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("collision" in item for item in failures)


def test_native_tooling_policy_missing_ci_concepts_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "native_tooling_ci_policy.md",
        "Native tooling policy.\n",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("CI strict mode" in item for item in failures)


def test_dangerous_authority_inversion_phrase_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "testing_policy.md",
        "Native core is the source of truth.\n",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("dangerous authority-inversion phrase" in item for item in failures)


def test_conditional_future_authority_transfer_phrase_does_not_fail(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "testing_policy.md",
        "Native core is the source of truth after parity transfer.\n",
    )

    failures = _messages(drift.validate(tmp_path))

    assert not any("dangerous authority-inversion phrase" in item for item in failures)


def test_review_checklist_missing_drift_concept_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    checklist = tmp_path / "docs" / "governance" / "review_checklist.md"
    checklist.write_text(
        checklist.read_text(encoding="utf-8").replace("drift protection\n", ""),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("drift protection" in item for item in failures)


def test_review_checklist_missing_first_parity_pilot_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    checklist = tmp_path / "docs" / "governance" / "review_checklist.md"
    checklist.write_text(
        checklist.read_text(encoding="utf-8").replace("first parity pilot\n", ""),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("first parity pilot" in item for item in failures)


def test_review_checklist_missing_promotion_gates_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    checklist = tmp_path / "docs" / "governance" / "review_checklist.md"
    checklist.write_text(
        checklist.read_text(encoding="utf-8").replace("promotion gates\n", ""),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("promotion gates" in item for item in failures)


def test_parity_protocol_missing_audit_link_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    parity_protocol = tmp_path / "docs" / "architecture" / "parity_protocol.md"
    parity_protocol.write_text("Parity protocol.\n", encoding="utf-8")

    failures = _messages(drift.validate(tmp_path))

    assert any("parity_pilot_audit_and_promotion_gates.md" in item for item in failures)


def test_governance_router_missing_audit_link_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    router = tmp_path / "docs" / "governance" / "README.md"
    router.write_text(
        router.read_text(encoding="utf-8").replace(
            "docs/architecture/parity_pilot_audit_and_promotion_gates.md\n", ""
        ),
        encoding="utf-8",
    )
    drift_map = tmp_path / "docs" / "governance" / "drift_protection_map.md"
    drift_map.write_text(
        drift_map.read_text(encoding="utf-8").replace(
            "docs/architecture/parity_pilot_audit_and_promotion_gates.md\n", ""
        ),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("parity_pilot_audit_and_promotion_gates.md" in item for item in failures)


def test_drift_map_missing_first_pilot_surfaces_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    drift_map = tmp_path / "docs" / "governance" / "drift_protection_map.md"
    drift_map.write_text(
        drift_map.read_text(encoding="utf-8")
        .replace("tools/migration/first_subsystem_parity_pilot.py\n", "")
        .replace("tests/unit/migration/test_first_subsystem_parity_pilot.py\n", ""),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any(
        "tools/migration/first_subsystem_parity_pilot.py" in item for item in failures
    )
    assert any(
        "tests/unit/migration/test_first_subsystem_parity_pilot.py" in item
        for item in failures
    )


def test_parity_audit_missing_no_transfer_wording_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    audit_doc = (
        tmp_path / "docs" / "architecture" / "parity_pilot_audit_and_promotion_gates.md"
    )
    audit_doc.write_text("Promotion gates only.\n", encoding="utf-8")

    failures = _messages(drift.validate(tmp_path))

    assert any("no-authority-transfer wording" in item for item in failures)


def test_second_parity_selection_missing_parity_link_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    parity_doc = tmp_path / "docs" / "architecture" / "parity_protocol.md"
    parity_doc.write_text(
        parity_doc.read_text(encoding="utf-8").replace(
            "docs/architecture/second_parity_slice_candidate_selection.md", ""
        ),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("second parity slice selection" in item for item in failures)


def test_second_parity_selection_missing_governance_reachability_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    router = tmp_path / "docs" / "governance" / "README.md"
    router.write_text(
        router.read_text(encoding="utf-8").replace(
            "docs/architecture/second_parity_slice_candidate_selection.md\n", ""
        ),
        encoding="utf-8",
    )
    drift_map = tmp_path / "docs" / "governance" / "drift_protection_map.md"
    drift_map.write_text(
        drift_map.read_text(encoding="utf-8").replace(
            "docs/architecture/second_parity_slice_candidate_selection.md\n", ""
        ),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any(
        "reachable from governance README or drift map" in item for item in failures
    )


def test_second_parity_selection_missing_drift_map_listing_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    drift_map = tmp_path / "docs" / "governance" / "drift_protection_map.md"
    drift_map.write_text(
        drift_map.read_text(encoding="utf-8").replace(
            "docs/architecture/second_parity_slice_candidate_selection.md\n", ""
        ),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("drift_protection_map.md must list" in item for item in failures)


def test_second_parity_selection_missing_no_transfer_wording_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    selection_doc = (
        tmp_path
        / "docs"
        / "architecture"
        / "second_parity_slice_candidate_selection.md"
    )
    selection_doc.write_text("Chosen candidate only.\n", encoding="utf-8")

    failures = _messages(drift.validate(tmp_path))

    assert any(
        "candidate selection does not transfer authority" in item for item in failures
    )


def test_parity_evidence_review_missing_stage20_boundary_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    review_doc = (
        tmp_path
        / "docs"
        / "architecture"
        / "parity_evidence_review_and_third_slice_selection.md"
    )
    review_doc.write_text(
        "Stage 19 parity evidence review and third-slice selection. "
        "Python remains the semantic oracle. "
        "Reviewed the first pilot and Stage 18 evidence. "
        "Topology identifier normalization only. "
        "This review does not transfer authority.\n",
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("Stage 20 boundary" in item for item in failures)


def test_pr_template_missing_review_concept_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    template = tmp_path / ".github" / "pull_request_template.md"
    template.write_text(
        "authority\ntechnical debt\nvalidation\nstaging\n", encoding="utf-8"
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("drift protection" in item for item in failures)


def test_pr_template_unreachable_from_review_governance_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    router = tmp_path / "docs" / "governance" / "README.md"
    router.write_text(
        router.read_text(encoding="utf-8").replace(
            ".github/pull_request_template.md\n", ""
        ),
        encoding="utf-8",
    )
    drift_map = tmp_path / "docs" / "governance" / "drift_protection_map.md"
    drift_map.write_text(
        drift_map.read_text(encoding="utf-8").replace(
            ".github/pull_request_template.md\n", ""
        ),
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("pull_request_template.md is not reachable" in item for item in failures)


def test_technical_debt_register_missing_drift_policy_link_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    register = tmp_path / "docs" / "governance" / "technical_debt_register.md"
    register.write_text(
        "docs/governance/workspace_bundle/technical_debt_policy.md\n",
        encoding="utf-8",
    )

    failures = _messages(drift.validate(tmp_path))

    assert any("workspace drift policy" in item for item in failures)
