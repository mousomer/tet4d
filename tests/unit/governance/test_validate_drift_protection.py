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
        "docs/architecture/authority_map.md\n",
    )
    _write(root / "godot" / "AGENTS.md", "Godot UI only.\n")
    _write(root / "native" / "AGENTS.md", "Native C++ only.\n")
    _write(
        root / "docs" / "governance" / "README.md",
        ".github/pull_request_template.md\n"
        "docs/governance/workspace_bundle/review_checklist_template.md\n"
        "docs/governance/workspace_bundle/drift_protection_policy.md\n"
        "docs/governance/drift_protection_map.md\n"
        "docs/architecture/first_subsystem_parity_pilot.md\n"
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
        "docs/architecture/utility_index.md\n"
        "governance routing drift\n"
        "authority drift\n"
        "config/generated drift\n"
        "tools/migration/export_config_bundle.py\n"
        "tools/governance/generate_configuration_reference.py\n"
        "tools/governance/validate_authority_transfer.py\n",
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
        "presentation layer. C++/GDExtension is provisional until parity.\n",
    )
    _write(
        root / "docs" / "architecture" / "parity_protocol.md",
        "Python oracle. Golden fixtures and golden traces. Comparison mode. "
        "Authority transfer and subsystem promotion. "
        "First subsystem parity pilot stays evidence only.\n",
    )
    _write(
        root / "docs" / "architecture" / "authority_transfer_protocol.md",
        "Python remains the semantic oracle. Authority transfer protocol. "
        "First subsystem parity pilot stays evidence only.\n",
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
