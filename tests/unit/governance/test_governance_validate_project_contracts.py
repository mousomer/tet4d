from __future__ import annotations

import json
from pathlib import Path

import tools.governance.validate_project_contracts as contracts


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_policy_index_sync_detects_missing_unified_contract_token(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack_path = tmp_path / "config" / "project" / "policy_pack.json"
    _write_json(
        policy_pack_path,
        {
            "governance": {
                "contracts": {
                    "policy_pack": "config/project/policy_pack.json",
                    "secret_scan": "config/project/policy/manifests/secret_scan.json",
                }
            }
        },
    )
    index_path = tmp_path / "docs" / "policies" / "INDEX.md"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        "docs/policies/CI_COMPLIANCE_RUNBOOK.md\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack_path)
    monkeypatch.setattr(contracts, "POLICY_INDEX_PATH", index_path)

    issues = contracts._validate_policy_index_sync()

    assert issues
    assert any("policy_pack.json" in issue.message for issue in issues)


def test_policy_index_sync_reads_required_tokens_from_policy_pack(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack_path = tmp_path / "config" / "project" / "policy_pack.json"
    _write_json(
        policy_pack_path,
        {
            "governance": {
                "policy_index_contract": {
                    "required_tokens": ["docs/policies/LOCAL_POLICY.md"]
                },
                "contracts": {},
            }
        },
    )
    index_path = tmp_path / "docs" / "policies" / "INDEX.md"
    _write_text(index_path, "config/project/policy_pack.json\n")

    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack_path)
    monkeypatch.setattr(contracts, "POLICY_INDEX_PATH", index_path)

    issues = contracts._validate_policy_index_sync()

    assert any("docs/policies/LOCAL_POLICY.md" in issue.message for issue in issues)


def test_policy_manifest_string_safety_detects_path_like_literals(
    tmp_path: Path, monkeypatch
) -> None:
    policy_root = tmp_path / "config" / "project"
    manifests_dir = policy_root / "policy" / "manifests"
    path_like_literal = r"value:[ \t]*\n[ \t]*" + "C:" + r"\\temp"
    _write_json(
        policy_root / "policy_pack.json",
        {
            "governance": {"schema_version": 1},
            "code_rules": {"schema_version": 1},
            "maintenance_contract": {"schema_version": 1},
            "maintenance_docs": {},
            "deprecated_authorities": {},
        },
    )
    _write_json(
        manifests_dir / "help_assets_manifest.json",
        {"rules": [{"id": "test", "example": path_like_literal}]},
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_root / "policy_pack.json")
    monkeypatch.setattr(contracts, "POLICY_MANIFEST_DIR", manifests_dir)
    issues = contracts._validate_policy_manifest_string_safety()
    assert issues
    assert any("path-like literal" in issue.message for issue in issues)


def test_policy_manifest_string_safety_allows_clean_manifests(
    tmp_path: Path, monkeypatch
) -> None:
    policy_root = tmp_path / "config" / "project"
    manifests_dir = policy_root / "policy" / "manifests"
    _write_json(
        policy_root / "policy_pack.json",
        {
            "governance": {"schema_version": 1},
            "code_rules": {"schema_version": 1},
            "maintenance_contract": {"schema_version": 1},
            "maintenance_docs": {},
            "deprecated_authorities": {},
        },
    )
    _write_json(
        manifests_dir / "help_assets_manifest.json",
        {"rules": [{"id": "test", "forbidden_regex": [r"value:[ \t]*\n[ \t]*x"]}]},
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_root / "policy_pack.json")
    monkeypatch.setattr(contracts, "POLICY_MANIFEST_DIR", manifests_dir)
    issues = contracts._validate_policy_manifest_string_safety()
    assert issues == []


def test_required_paths_detect_untracked_file(tmp_path: Path, monkeypatch) -> None:
    rel = "docs/WORKFLOW_CODEX.md"
    workflow_doc = tmp_path / rel
    workflow_doc.parent.mkdir(parents=True, exist_ok=True)
    workflow_doc.write_text("workflow", encoding="utf-8")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "_git_tracked_paths", lambda issues: set())

    issues = contracts._validate_required_paths(
        {"required_paths": {"root_docs": [rel]}}
    )

    assert any(
        issue.message == f"required path is not tracked in git: {rel}"
        for issue in issues
    )


def test_required_paths_accept_git_tracked_file(tmp_path: Path, monkeypatch) -> None:
    rel = "docs/WORKFLOW_CODEX.md"
    workflow_doc = tmp_path / rel
    workflow_doc.parent.mkdir(parents=True, exist_ok=True)
    workflow_doc.write_text("workflow", encoding="utf-8")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "_git_tracked_paths", lambda issues: {rel})

    issues = contracts._validate_required_paths(
        {"required_paths": {"root_docs": [rel]}}
    )

    assert issues == []


def _write_minimal_cpp_safety_policy(root: Path) -> None:
    _write_text(
        root / "docs" / "governance" / "cpp_safety_policy.md",
        "\n".join(
            [
                "# C++ Safety Policy",
                "Python remains the semantic oracle.",
                "Use RAII.",
                "No raw owning pointers.",
                "No naked new or delete.",
                "Document the GDExtension boundary.",
                "Require parity evidence.",
                "Update the authority map.",
            ]
        ),
    )


def _write_minimal_native_tooling_ci_policy(root: Path) -> None:
    _write_text(
        root / "docs" / "governance" / "native_tooling_ci_policy.md",
        "\n".join(
            [
                "# Native Tooling CI Policy",
                "Local advisory mode skips unavailable tools.",
                "Local strict mode uses TET4D_STRICT_NATIVE_TOOLS.",
                "CI strict mode uses the same strict checks.",
                "clang-format and clang-tidy are native tooling gates.",
                "compile_commands.json is required for clang-tidy.",
                "Python remains the semantic oracle.",
                "See docs/architecture/authority_transfer_protocol.md.",
                "See docs/governance/technical_debt_register.md and TD-0004.",
            ]
        ),
    )


def _write_minimal_native_tooling_governance(root: Path) -> None:
    _write_text(
        root / "tools" / "governance" / "validate_native_cpp_tooling.py",
        "def main():\n    return 0\n",
    )
    _write_text(
        root / "tools" / "governance" / "validate_governance.py",
        "from tools.governance import validate_native_cpp_tooling\n",
    )


def _write_minimal_parity_governance(root: Path) -> None:
    _write_text(root / "AGENTS.md", "Python semantic oracle. Godot. C++. Parity.\n")
    _write_text(root / "docs" / "WORKFLOW_CODEX.md", "Workflow.\n")
    _write_text(root / "godot" / "AGENTS.md", "Godot UI only.\n")
    _write_text(
        root / "docs" / "architecture" / "parity_protocol.md",
        "\n".join(
            [
                "# Parity Protocol",
                "Python remains the semantic oracle.",
                "C++/GDExtension implementations require golden evidence.",
                "Comparison modes define exact and tolerance comparisons.",
                "Disagreement rules favor Python.",
                "Fixture location includes migration/golden_traces.",
                "Authority transfer updates the authority map.",
                "First subsystem parity pilot stays evidence only.",
            ]
        ),
    )
    _write_text(
        root / "docs" / "architecture" / "authority_map.md",
        "See docs/architecture/parity_protocol.md. "
        "Authority transfer is subsystem-specific.\n",
    )
    _write_text(
        root / "docs" / "governance" / "testing_policy.md",
        "## C++ / Python parity\nPython oracle required. "
        "Visual Godot tests are not substitutes.\n",
    )
    _write_text(
        root / "docs" / "governance" / "godot_cpp_policy.md",
        "See docs/architecture/parity_protocol.md. "
        "C++ remains provisional until the authority map records transfer.\n",
    )
    _write_text(
        root / "docs" / "governance" / "review_checklist.md",
        "## Parity / authority transfer\n"
        "- Python oracle identified.\n"
        "- Godot visual checks are not semantic parity.\n"
        "- First parity pilot evidence was documented as process-only.\n",
    )
    _write_text(
        root / "docs" / "governance" / "README.md",
        "docs/architecture/parity_protocol.md\n"
        "docs/architecture/first_subsystem_parity_pilot.md\n"
        "Testing/parity\n",
    )
    _write_text(
        root / "docs" / "architecture" / "first_subsystem_parity_pilot.md",
        "First subsystem parity pilot stays evidence only.\n",
    )


def _write_minimal_godot_semantic_boundary_governance(root: Path) -> None:
    _write_text(root / "godot" / "scripts" / "app.gd", "func _ready():\n\tpass\n")
    _write_text(
        root / "tools" / "governance" / "validate_godot_semantic_boundary.py",
        "def main():\n    return 0\n",
    )
    _write_text(
        root / "tools" / "governance" / "validate_governance.py",
        "from tools.governance import validate_godot_semantic_boundary\n",
    )
    _write_text(
        root / "docs" / "governance" / "godot_cpp_policy.md",
        "## Godot semantic boundary\n"
        "GDScript must not independently compute semantic state.\n",
    )
    _write_text(
        root / "godot" / "AGENTS.md",
        "Do not compute semantic truth in GDScript; use adapter APIs.\n",
    )
    _write_text(
        root / "docs" / "governance" / "review_checklist.md",
        "## Godot semantic boundary\n"
        "GDScript remains presentation. Check semantic-boundary validator suppressions.\n",
    )


def _write_minimal_config_authority_governance(root: Path) -> None:
    _write_text(
        root / "tools" / "governance" / "validate_config_authority.py",
        "def main():\n    return 0\n",
    )
    _write_text(
        root / "tools" / "governance" / "validate_governance.py",
        "from tools.governance import validate_config_authority\n",
    )
    _write_text(
        root / "docs" / "governance" / "config_policy.md",
        "Config authority routes through POLICY_NO_MAGIC_NUMBERS. "
        "Use config/project/constants.json.\n",
    )
    _write_text(
        root / "docs" / "policies" / "POLICY_NO_MAGIC_NUMBERS.md",
        "See docs/governance/config_policy.md and validate_config_authority.\n",
    )
    _write_text(
        root / "docs" / "governance" / "review_checklist.md",
        "Check config-authority validator hardcoded constants.\n",
    )
    _write_text(
        root / "docs" / "governance" / "README.md",
        "Route config_policy through validate_config_authority.\n",
    )


def _write_minimal_utility_reuse_governance(root: Path) -> None:
    _write_text(
        root / "tools" / "governance" / "validate_utility_reuse.py",
        "def main():\n    return 0\n",
    )
    _write_text(
        root / "tools" / "governance" / "validate_governance.py",
        "from tools.governance import validate_utility_reuse\n",
    )
    _write_text(
        root / "docs" / "architecture" / "utility_index.md",
        "## Required fields\nOwner\nReuse rule\nMigration relevance\n",
    )
    _write_text(
        root / "docs" / "policies" / "POLICY_NO_REINVENTING_WHEEL.md",
        "docs/architecture/utility_index.md\n"
        "check_wheel_reuse_rules.py\n"
        "check_dedup_dead_code_rules.py\n"
        "validate_utility_reuse.py\n",
    )
    _write_text(
        root / "docs" / "governance" / "codex_policy.md",
        "Search existing helpers before adding new ones. See utility_index.\n",
    )
    _write_text(
        root / "docs" / "governance" / "review_checklist.md",
        "## Dependency / utility reuse\n"
        "No-reinvention checks include validate_utility_reuse.\n",
    )
    _write_text(
        root / "docs" / "governance" / "README.md",
        "utility_index policy_no_reinventing_wheel validate_utility_reuse "
        "check_wheel_reuse_rules check_dedup_dead_code_rules\n",
    )


def test_utility_reuse_governance_requires_validator(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_utility_reuse_governance()

    assert any("validate_utility_reuse.py" in issue.message for issue in issues)


def test_utility_reuse_governance_requires_doc_tokens(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(
        tmp_path / "tools" / "governance" / "validate_utility_reuse.py",
        "def main():\n    return 0\n",
    )
    _write_text(
        tmp_path / "tools" / "governance" / "validate_governance.py",
        "from tools.governance import validate_utility_reuse\n",
    )
    _write_text(tmp_path / "docs" / "architecture" / "utility_index.md", "Utility\n")
    _write_text(
        tmp_path / "docs" / "policies" / "POLICY_NO_REINVENTING_WHEEL.md",
        "Wheel\n",
    )
    _write_text(tmp_path / "docs" / "governance" / "codex_policy.md", "Codex\n")
    _write_text(tmp_path / "docs" / "governance" / "review_checklist.md", "Review\n")
    _write_text(tmp_path / "docs" / "governance" / "README.md", "Router\n")
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_utility_reuse_governance()

    assert any("utility reuse governance token" in issue.message for issue in issues)


def test_utility_reuse_governance_accepts_baseline(tmp_path: Path, monkeypatch) -> None:
    _write_minimal_utility_reuse_governance(tmp_path)
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    assert contracts._validate_utility_reuse_governance() == []


def test_workspace_bundle_governance_routes_validator(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_workspace_bundle_governance()

    assert any("workspace_bundle/README.md" in issue.message for issue in issues)


def _write_minimal_technical_debt_governance(root: Path) -> None:
    _write_text(
        root / "docs" / "governance" / "workspace_bundle" / "technical_debt_policy.md",
        "Technical debt policy.\n",
    )
    _write_text(
        root
        / "docs"
        / "governance"
        / "workspace_bundle"
        / "drift_protection_policy.md",
        "Drift protection policy.\n",
    )
    _write_text(
        root / "docs" / "governance" / "workspace_bundle" / "MANIFEST.md",
        "technical_debt_policy.md\ndrift_protection_policy.md\n",
    )
    _write_text(
        root / "docs" / "governance" / "technical_debt_register.md",
        "Project-specific debt register.\n",
    )
    _write_text(
        root / "docs" / "governance" / "README.md",
        "technical_debt_register.md technical_debt_policy.md "
        "drift_protection_policy.md validate_technical_debt.py\n",
    )
    _write_text(
        root / "docs" / "governance" / "review_checklist.md",
        "technical-debt delta advisory validator findings drift protection\n",
    )
    _write_text(
        root / "tools" / "governance" / "validate_technical_debt.py",
        "def main():\n    return 0\n",
    )
    _write_text(
        root / "tools" / "governance" / "validate_governance.py",
        "from tools.governance import validate_technical_debt\n",
    )


def test_technical_debt_governance_requires_register(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_technical_debt_governance()

    assert any("technical_debt_register.md" in issue.message for issue in issues)


def test_technical_debt_governance_requires_router_debt_link(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_technical_debt_governance(tmp_path)
    _write_text(tmp_path / "docs" / "governance" / "README.md", "Router\n")
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_technical_debt_governance()

    assert any("technical_debt_register.md" in issue.message for issue in issues)


def test_technical_debt_governance_requires_router_drift_link(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_technical_debt_governance(tmp_path)
    _write_text(
        tmp_path / "docs" / "governance" / "README.md",
        "technical_debt_register.md technical_debt_policy.md validate_technical_debt.py\n",
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_technical_debt_governance()

    assert any("drift_protection_policy.md" in issue.message for issue in issues)


def test_technical_debt_governance_requires_review_delta(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_technical_debt_governance(tmp_path)
    _write_text(tmp_path / "docs" / "governance" / "review_checklist.md", "Review\n")
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_technical_debt_governance()

    assert any("technical-debt delta" in issue.message for issue in issues)


def test_technical_debt_governance_requires_runner_reference(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_technical_debt_governance(tmp_path)
    _write_text(
        tmp_path / "tools" / "governance" / "validate_governance.py",
        "def main():\n    return 0\n",
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_technical_debt_governance()

    assert any("validate_technical_debt" in issue.message for issue in issues)


def test_technical_debt_governance_accepts_without_drift_validator(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_technical_debt_governance(tmp_path)
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    assert contracts._validate_technical_debt_governance() == []


def _write_minimal_drift_protection_governance(root: Path) -> None:
    _write_text(
        root
        / "docs"
        / "governance"
        / "workspace_bundle"
        / "drift_protection_policy.md",
        "Reusable drift policy.\n",
    )
    _write_text(
        root / "docs" / "governance" / "drift_protection_map.md",
        "tet4d-specific surfaces\n"
        "docs/governance/workspace_bundle/drift_protection_policy.md\n"
        "governance routing drift\n"
        "authority drift\n"
        "config/generated drift\n",
    )
    _write_text(
        root / "tools" / "governance" / "validate_drift_protection.py",
        "def main():\n    return 0\n",
    )
    _write_text(
        root / "tools" / "governance" / "validate_governance.py",
        "from tools.governance import validate_drift_protection\n",
    )
    _write_text(
        root / "docs" / "governance" / "README.md",
        "drift_protection_policy.md drift_protection_map.md "
        "validate_drift_protection.py\n",
    )
    _write_text(
        root / "docs" / "governance" / "review_checklist.md",
        "drift protection validate_governance.py generated outputs\n",
    )


def test_drift_protection_governance_requires_map(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_drift_protection_governance()

    assert any("drift_protection_map.md" in issue.message for issue in issues)


def test_drift_protection_governance_requires_validator(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_drift_protection_governance(tmp_path)
    (tmp_path / "tools" / "governance" / "validate_drift_protection.py").unlink()
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_drift_protection_governance()

    assert any("validate_drift_protection.py" in issue.message for issue in issues)


def test_drift_protection_governance_requires_router_links(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_drift_protection_governance(tmp_path)
    _write_text(tmp_path / "docs" / "governance" / "README.md", "Router\n")
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_drift_protection_governance()

    assert any("drift_protection_map.md" in issue.message for issue in issues)
    assert any("validate_drift_protection.py" in issue.message for issue in issues)


def test_drift_protection_governance_requires_runner_reference(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_drift_protection_governance(tmp_path)
    _write_text(
        tmp_path / "tools" / "governance" / "validate_governance.py",
        "def main():\n    return 0\n",
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_drift_protection_governance()

    assert any("validate_drift_protection" in issue.message for issue in issues)


def test_drift_protection_governance_requires_review_checklist(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_drift_protection_governance(tmp_path)
    _write_text(tmp_path / "docs" / "governance" / "review_checklist.md", "Review\n")
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_drift_protection_governance()

    assert any("drift protection" in issue.message for issue in issues)


def test_drift_protection_governance_rejects_workspace_policy_copy(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_drift_protection_governance(tmp_path)
    _write_text(
        tmp_path / "docs" / "governance" / "drift_protection_map.md",
        "tet4d-specific surfaces\n"
        "docs/governance/workspace_bundle/drift_protection_policy.md\n"
        "governance routing drift\nauthority drift\nconfig/generated drift\n"
        "## General drift risks\n",
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_drift_protection_governance()

    assert any("must not copy workspace policy" in issue.message for issue in issues)


def test_drift_protection_governance_accepts_baseline(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_drift_protection_governance(tmp_path)
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    assert contracts._validate_drift_protection_governance() == []


def _write_minimal_authority_transfer_governance(root: Path) -> None:
    _write_text(
        root / "docs" / "architecture" / "authority_transfer_protocol.md",
        "Authority transfer protocol.\n"
        "Candidate and blocked statuses only.\n"
        "First subsystem parity pilot stays evidence only.\n"
        "This record must not be transferred.\n",
    )
    _write_text(
        root / "tools" / "governance" / "validate_authority_transfer.py",
        "def main():\n    return 0\n",
    )
    _write_text(
        root / "tools" / "governance" / "validate_governance.py",
        "from tools.governance import validate_authority_transfer\n",
    )
    _write_text(
        root / "docs" / "governance" / "README.md",
        "authority_transfer_protocol.md validate_authority_transfer.py\n"
        "docs/architecture/first_subsystem_parity_pilot.md\n",
    )
    _write_text(
        root / "docs" / "architecture" / "authority_map.md",
        "authority_transfer_protocol.md\n",
    )
    _write_text(
        root / "docs" / "architecture" / "parity_protocol.md",
        "authority_transfer_protocol.md first_subsystem_parity_pilot.md\n",
    )
    _write_text(
        root / "docs" / "governance" / "drift_protection_map.md",
        "authority_transfer_protocol.md validate_authority_transfer.py\n",
    )
    _write_text(
        root / "docs" / "governance" / "review_checklist.md",
        "authority transfer transfer record fallback path\n",
    )
    _write_text(
        root / "docs" / "governance" / "workspace_bundle" / "README.md",
        "Reusable governance.\n",
    )


def test_authority_transfer_governance_requires_protocol(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_authority_transfer_governance()

    assert any("authority_transfer_protocol.md" in issue.message for issue in issues)


def test_authority_transfer_governance_requires_validator(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_authority_transfer_governance(tmp_path)
    (tmp_path / "tools" / "governance" / "validate_authority_transfer.py").unlink()
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_authority_transfer_governance()

    assert any("validate_authority_transfer.py" in issue.message for issue in issues)


def test_authority_transfer_governance_requires_router_links(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_authority_transfer_governance(tmp_path)
    _write_text(tmp_path / "docs" / "governance" / "README.md", "Router\n")
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_authority_transfer_governance()

    assert any("authority_transfer_protocol.md" in issue.message for issue in issues)
    assert any("validate_authority_transfer.py" in issue.message for issue in issues)


def test_authority_transfer_governance_requires_architecture_links(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_authority_transfer_governance(tmp_path)
    _write_text(tmp_path / "docs" / "architecture" / "authority_map.md", "Map\n")
    _write_text(tmp_path / "docs" / "architecture" / "parity_protocol.md", "Parity\n")
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_authority_transfer_governance()

    assert any("authority_map.md" in issue.message for issue in issues)
    assert any("parity_protocol.md" in issue.message for issue in issues)


def test_authority_transfer_governance_requires_drift_surface(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_authority_transfer_governance(tmp_path)
    _write_text(tmp_path / "docs" / "governance" / "drift_protection_map.md", "Map\n")
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_authority_transfer_governance()

    assert any("drift_protection_map.md" in issue.message for issue in issues)


def test_authority_transfer_governance_rejects_workspace_record_text(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_authority_transfer_governance(tmp_path)
    _write_text(
        tmp_path / "docs" / "governance" / "workspace_bundle" / "README.md",
        "tet4d authority-transfer transfer record\n",
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_authority_transfer_governance()

    assert any("workspace" in issue.message for issue in issues)


def test_authority_transfer_governance_accepts_baseline(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_authority_transfer_governance(tmp_path)
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    assert contracts._validate_authority_transfer_governance() == []


def _valid_pr_template() -> str:
    return "\n".join(
        [
            "# Pull Request Checklist",
            "## Summary",
            "- Scope is limited.",
            "- Unrelated dirty files were not staged.",
            "## Authority",
            "- Python semantic authority is preserved.",
            "- Godot/GDScript boundary remains presentation only.",
            "- C++/GDExtension remains provisional.",
            "- authority-transfer protocol checked.",
            "## Governance",
            "- Existing utilities searched; duplicate implementations avoided.",
            "- config/constants authority checked.",
            "- Generated files were not hand-edited.",
            "- Technical debt delta described.",
            "- Drift protection impact described.",
            "## Validation commands",
            "- CODEX_MODE=1 ./scripts/verify.sh",
            "- git diff --cached --check",
            "",
        ]
    )


def _write_minimal_review_template_governance(root: Path) -> None:
    _write_text(root / ".github" / "pull_request_template.md", _valid_pr_template())
    _write_text(
        root
        / "docs"
        / "governance"
        / "workspace_bundle"
        / "review_checklist_template.md",
        "General programming. Generated files. Technical debt. Drift risk. Validators. Staging.\n",
    )
    _write_text(
        root / "docs" / "governance" / "review_checklist.md",
        "docs/governance/workspace_bundle/review_checklist_template.md\n"
        "docs/architecture/authority_map.md\n"
        "docs/architecture/parity_protocol.md\n"
        "docs/architecture/authority_transfer_protocol.md\n"
        "docs/governance/technical_debt_register.md\n"
        "docs/governance/drift_protection_map.md\n"
        "generated bundle\n"
        "staging discipline\n",
    )
    _write_text(
        root / "docs" / "governance" / "README.md",
        ".github/pull_request_template.md\n"
        "docs/governance/review_checklist.md\n"
        "docs/governance/workspace_bundle/review_checklist_template.md\n",
    )


def test_review_template_governance_requires_pr_template(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_review_template_governance(tmp_path)
    (tmp_path / ".github" / "pull_request_template.md").unlink()
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_review_template_governance()

    assert any("pull_request_template.md" in issue.message for issue in issues)


def test_review_template_governance_requires_router_pr_template_link(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_review_template_governance(tmp_path)
    _write_text(tmp_path / "docs" / "governance" / "README.md", "Router\n")
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_review_template_governance()

    assert any(".github/pull_request_template.md" in issue.message for issue in issues)


def test_review_template_governance_requires_workspace_template_link(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_review_template_governance(tmp_path)
    _write_text(tmp_path / "docs" / "governance" / "review_checklist.md", "Review\n")
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_review_template_governance()

    assert any(
        "workspace_bundle/review_checklist_template.md" in issue.message
        for issue in issues
    )


def test_review_template_governance_rejects_workspace_tet4d_terms(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_review_template_governance(tmp_path)
    _write_text(
        tmp_path
        / "docs"
        / "governance"
        / "workspace_bundle"
        / "review_checklist_template.md",
        "tet4d Python semantic oracle\n",
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_review_template_governance()

    assert any("forbidden term" in issue.message for issue in issues)


def test_review_template_governance_accepts_baseline(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_review_template_governance(tmp_path)
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    assert contracts._validate_review_template_governance() == []


def test_pr_template_missing_required_concepts_fails(
    tmp_path: Path, monkeypatch
) -> None:
    missing_terms = (
        "Python semantic authority",
        "Godot/GDScript boundary",
        "C++/GDExtension remains provisional",
        "authority-transfer protocol",
        "utilities searched; duplicate",
        "config/constants authority",
        "Generated files",
        "Technical debt",
        "Drift protection",
        "Validation commands",
        "git diff --cached --check",
    )
    _write_minimal_review_template_governance(tmp_path)
    template = _valid_pr_template()
    for term in missing_terms:
        _write_text(
            tmp_path / ".github" / "pull_request_template.md",
            template.replace(term, ""),
        )
        monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

        issues = contracts._validate_review_template_governance()

        assert issues, f"expected missing concept failure for {term}"


def test_config_authority_governance_requires_validator(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_config_authority_governance()

    assert any("validate_config_authority.py" in issue.message for issue in issues)


def test_config_authority_governance_requires_doc_tokens(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(
        tmp_path / "tools" / "governance" / "validate_config_authority.py",
        "def main():\n    return 0\n",
    )
    _write_text(
        tmp_path / "tools" / "governance" / "validate_governance.py",
        "from tools.governance import validate_config_authority\n",
    )
    _write_text(tmp_path / "docs" / "governance" / "config_policy.md", "Config\n")
    _write_text(
        tmp_path / "docs" / "policies" / "POLICY_NO_MAGIC_NUMBERS.md",
        "Numbers\n",
    )
    _write_text(tmp_path / "docs" / "governance" / "review_checklist.md", "Review\n")
    _write_text(tmp_path / "docs" / "governance" / "README.md", "Router\n")
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_config_authority_governance()

    assert any("config authority governance token" in issue.message for issue in issues)


def test_config_authority_governance_accepts_baseline(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_config_authority_governance(tmp_path)
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    assert contracts._validate_config_authority_governance() == []


def test_native_cpp_safety_governance_requires_style_files(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_text(
        tmp_path / "native" / "AGENTS.md",
        "See docs/governance/cpp_safety_policy.md\n"
        "See docs/governance/native_tooling_ci_policy.md\n",
    )
    _write_minimal_cpp_safety_policy(tmp_path)
    _write_minimal_native_tooling_ci_policy(tmp_path)
    _write_minimal_native_tooling_governance(tmp_path)

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_native_cpp_safety_governance()

    assert any(".clang-format" in issue.message for issue in issues)
    assert any(".clang-tidy" in issue.message for issue in issues)


def test_native_cpp_safety_governance_rejects_warnings_as_errors_star(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_text(
        tmp_path / "native" / "AGENTS.md",
        "See docs/governance/cpp_safety_policy.md\n"
        "See docs/governance/native_tooling_ci_policy.md\n",
    )
    _write_minimal_cpp_safety_policy(tmp_path)
    _write_minimal_native_tooling_ci_policy(tmp_path)
    _write_minimal_native_tooling_governance(tmp_path)
    _write_text(tmp_path / ".clang-format", "BasedOnStyle: LLVM\n")
    _write_text(
        tmp_path / ".clang-tidy",
        "Checks: clang-analyzer-*\nWarningsAsErrors: '*'\n",
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_native_cpp_safety_governance()

    assert any("WarningsAsErrors" in issue.message for issue in issues)


def test_native_cpp_safety_governance_requires_tooling_validator(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_text(
        tmp_path / "native" / "AGENTS.md",
        "See docs/governance/cpp_safety_policy.md\n"
        "See docs/governance/native_tooling_ci_policy.md\n",
    )
    _write_minimal_cpp_safety_policy(tmp_path)
    _write_minimal_native_tooling_ci_policy(tmp_path)
    _write_text(tmp_path / ".clang-format", "BasedOnStyle: LLVM\n")
    _write_text(
        tmp_path / ".clang-tidy",
        "Checks: clang-analyzer-*, cppcoreguidelines-*\nWarningsAsErrors: ''\n",
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_native_cpp_safety_governance()

    assert any("validate_native_cpp_tooling.py" in issue.message for issue in issues)


def test_native_cpp_safety_governance_accepts_baseline(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_text(
        tmp_path / "native" / "AGENTS.md",
        "See docs/governance/cpp_safety_policy.md\n"
        "See docs/governance/native_tooling_ci_policy.md\n",
    )
    _write_minimal_cpp_safety_policy(tmp_path)
    _write_minimal_native_tooling_ci_policy(tmp_path)
    _write_minimal_native_tooling_governance(tmp_path)
    _write_text(tmp_path / ".clang-format", "BasedOnStyle: LLVM\n")
    _write_text(
        tmp_path / ".clang-tidy",
        "Checks: clang-analyzer-*, cppcoreguidelines-*\nWarningsAsErrors: ''\n",
    )
    _write_text(
        tmp_path / "docs" / "governance" / "README.md",
        "docs/governance/native_tooling_ci_policy.md\n",
    )
    _write_text(
        tmp_path / "docs" / "governance" / "review_checklist.md",
        "Native tooling CI readiness TET4D_STRICT_NATIVE_TOOLS CI strict.\n",
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    assert contracts._validate_native_cpp_safety_governance() == []


def test_native_cpp_safety_governance_requires_native_tooling_policy(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_text(
        tmp_path / "native" / "AGENTS.md",
        "See docs/governance/cpp_safety_policy.md\n"
        "See docs/governance/native_tooling_ci_policy.md\n",
    )
    _write_minimal_cpp_safety_policy(tmp_path)
    _write_minimal_native_tooling_governance(tmp_path)
    _write_text(tmp_path / ".clang-format", "BasedOnStyle: LLVM\n")
    _write_text(
        tmp_path / ".clang-tidy",
        "Checks: clang-analyzer-*, cppcoreguidelines-*\nWarningsAsErrors: ''\n",
    )
    _write_text(
        tmp_path / "docs" / "governance" / "README.md",
        "docs/governance/native_tooling_ci_policy.md\n",
    )
    _write_text(
        tmp_path / "docs" / "governance" / "review_checklist.md",
        "Native tooling CI readiness TET4D_STRICT_NATIVE_TOOLS CI strict.\n",
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_native_cpp_safety_governance()

    assert any("native_tooling_ci_policy.md" in issue.message for issue in issues)


def test_native_cpp_safety_governance_requires_native_tooling_route(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_text(
        tmp_path / "native" / "AGENTS.md",
        "See docs/governance/cpp_safety_policy.md\n",
    )
    _write_minimal_cpp_safety_policy(tmp_path)
    _write_minimal_native_tooling_ci_policy(tmp_path)
    _write_minimal_native_tooling_governance(tmp_path)
    _write_text(tmp_path / ".clang-format", "BasedOnStyle: LLVM\n")
    _write_text(
        tmp_path / ".clang-tidy",
        "Checks: clang-analyzer-*, cppcoreguidelines-*\nWarningsAsErrors: ''\n",
    )
    _write_text(
        tmp_path / "docs" / "governance" / "README.md",
        "docs/governance/native_tooling_ci_policy.md\n",
    )
    _write_text(
        tmp_path / "docs" / "governance" / "review_checklist.md",
        "Native tooling CI readiness TET4D_STRICT_NATIVE_TOOLS CI strict.\n",
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_native_cpp_safety_governance()

    assert any("native_tooling_ci_policy" in issue.message for issue in issues)


def test_native_cpp_safety_governance_requires_native_tooling_review(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_text(
        tmp_path / "native" / "AGENTS.md",
        "See docs/governance/cpp_safety_policy.md\n"
        "See docs/governance/native_tooling_ci_policy.md\n",
    )
    _write_minimal_cpp_safety_policy(tmp_path)
    _write_minimal_native_tooling_ci_policy(tmp_path)
    _write_minimal_native_tooling_governance(tmp_path)
    _write_text(tmp_path / ".clang-format", "BasedOnStyle: LLVM\n")
    _write_text(
        tmp_path / ".clang-tidy",
        "Checks: clang-analyzer-*, cppcoreguidelines-*\nWarningsAsErrors: ''\n",
    )
    _write_text(
        tmp_path / "docs" / "governance" / "README.md",
        "docs/governance/native_tooling_ci_policy.md\n",
    )
    _write_text(tmp_path / "docs" / "governance" / "review_checklist.md", "Review\n")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_native_cpp_safety_governance()

    assert any("native tooling token" in issue.message for issue in issues)


def test_cpp_parity_protocol_governance_requires_protocol(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_cpp_parity_protocol_governance()

    assert any("parity_protocol.md" in issue.message for issue in issues)


def test_cpp_parity_protocol_governance_rejects_dangerous_wording(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_minimal_parity_governance(tmp_path)
    _write_text(
        tmp_path / "docs" / "governance" / "extra.md",
        "Visual correctness is parity.\n",
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_cpp_parity_protocol_governance()

    assert any("dangerous parity wording" in issue.message for issue in issues)


def test_cpp_parity_protocol_governance_requires_fixture_readme(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_minimal_parity_governance(tmp_path)
    (tmp_path / "tests" / "replay" / "golden").mkdir(parents=True)

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_cpp_parity_protocol_governance()

    assert any("tests/replay/golden" in issue.message for issue in issues)


def test_cpp_parity_protocol_governance_accepts_baseline(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_minimal_parity_governance(tmp_path)
    _write_text(
        tmp_path / "tests" / "replay" / "golden" / "README.md",
        "See docs/architecture/parity_protocol.md.\n",
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    assert contracts._validate_cpp_parity_protocol_governance() == []


def test_godot_semantic_boundary_governance_requires_validator(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "godot" / "scripts" / "app.gd", "func _ready():\n\tpass\n")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_godot_semantic_boundary_governance()

    assert any(
        "validate_godot_semantic_boundary.py" in issue.message for issue in issues
    )


def test_godot_semantic_boundary_governance_requires_doc_tokens(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "godot" / "scripts" / "app.gd", "func _ready():\n\tpass\n")
    _write_text(
        tmp_path / "tools" / "governance" / "validate_godot_semantic_boundary.py",
        "def main():\n    return 0\n",
    )
    _write_text(
        tmp_path / "tools" / "governance" / "validate_governance.py",
        "from tools.governance import validate_godot_semantic_boundary\n",
    )
    _write_text(tmp_path / "docs" / "governance" / "godot_cpp_policy.md", "Godot\n")
    _write_text(tmp_path / "godot" / "AGENTS.md", "Godot\n")
    _write_text(tmp_path / "docs" / "governance" / "review_checklist.md", "Godot\n")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_godot_semantic_boundary_governance()

    assert any("semantic-boundary token" in issue.message for issue in issues)


def test_godot_semantic_boundary_governance_accepts_baseline(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_godot_semantic_boundary_governance(tmp_path)

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    assert contracts._validate_godot_semantic_boundary_governance() == []


def test_governance_directives_include_staged_migration_contract() -> None:
    payload = json.loads(contracts.POLICY_PACK_PATH.read_text(encoding="utf-8"))
    directives = payload["governance"]["contributor_directives"]["directives"]
    directive_ids = {item["id"] for item in directives}
    assert {
        "staged_migration_honesty",
        "additive_migration_first",
        "delta_report_required",
    }.issubset(directive_ids)


def test_workflow_codex_rule_requires_control_contract_tokens() -> None:
    manifest = contracts._load_manifest()
    rules = manifest["content_rules"]
    workflow_rule = next(
        rule for rule in rules if rule["file"] == "docs/WORKFLOW_CODEX.md"
    )
    must_contain = set(workflow_rule["must_contain"])
    assert "Workflow authority" in must_contain
    assert "config/project/policy_pack.json" in must_contain
    assert "Authority files must be tracked in Git" in must_contain
    assert "## Context-switch profiles" in must_contain
    assert "## Boundary model" in must_contain
    assert "CODEX_MODE=1 ./scripts/verify.sh" in must_contain


def test_current_state_rule_enforces_restart_only_scope() -> None:
    manifest = contracts._load_manifest()
    rules = manifest["content_rules"]
    current_state_rule = next(
        rule for rule in rules if rule["file"] == "CURRENT_STATE.md"
    )

    must_contain = set(current_state_rule["must_contain"])
    must_not_contain = set(current_state_rule["must_not_contain"])
    must_not_match_regex = set(current_state_rule["must_not_match_regex"])

    assert "## Active Focus" in must_contain
    assert "## Known Watchouts" in must_contain
    assert "docs/PROJECT_STRUCTURE.md" in must_contain
    assert "## Active Batch Note" in must_not_contain
    assert "## What This Batch Changed" in must_not_contain
    assert "^Branch:" in must_not_match_regex


def test_menu_simplification_rule_reads_required_rows_from_policy_pack(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack = tmp_path / "config" / "project" / "policy_pack.json"
    menu_path = tmp_path / "config" / "menu" / "structure.json"
    _write_json(
        policy_pack,
        {
            "governance": {
                "menu_simplification_manifest_rule": {
                    "rule_id": "menu-simplification-common-settings",
                    "required_shared_row_keys": ["shared_test_key"],
                }
            }
        },
    )
    _write_json(
        menu_path,
        {
            "menus": {"settings_game_root": {"items": []}},
            "setup_fields": {"runtime": [{"attr": "shared_test_key"}]},
        },
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)
    monkeypatch.setattr(contracts, "MENU_STRUCTURE_PATH", menu_path)

    issues = contracts._validate_menu_simplification_rule()

    assert any("shared_test_key" in issue.message for issue in issues)


def test_menu_structure_single_source_reads_policy_pack_contract_data(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack = tmp_path / "config" / "project" / "policy_pack.json"
    menu_path = tmp_path / "config" / "menu" / "structure.json"
    literal_target = (
        tmp_path
        / "src"
        / "tet4d"
        / "ui"
        / "pygame"
        / "launch"
        / "settings_hub_model.py"
    )
    _write_json(
        policy_pack,
        {
            "governance": {
                "menu_structure_single_source": {
                    "required_menus": ["settings_root"],
                    "required_submenu_labels": [
                        {"menu_id": "settings_root", "labels": ["Custom"]}
                    ],
                    "required_item_labels": [],
                    "required_item_types": ["submenu"],
                    "banned_python_literals": [
                        {
                            "file": "src/tet4d/ui/pygame/launch/settings_hub_model.py",
                            "literal": "FORBIDDEN_LITERAL =",
                            "message": "custom drift",
                        }
                    ],
                }
            }
        },
    )
    _write_json(
        menu_path,
        {
            "menus": {
                "settings_root": {"items": [{"type": "submenu", "label": "Different"}]}
            }
        },
    )
    _write_text(literal_target, "FORBIDDEN_LITERAL = True\n")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)
    monkeypatch.setattr(contracts, "MENU_STRUCTURE_PATH", menu_path)

    issues = contracts._validate_menu_structure_single_source_of_truth()

    assert any("Custom" in issue.message for issue in issues)
    assert any(issue.message == "custom drift" for issue in issues)


def test_menu_structure_single_option_policy_detects_redundant_pages() -> None:
    payload = {
        "menus": {
            "submenu_wrapper": {
                "items": [{"type": "submenu", "label": "Child", "menu_id": "child"}]
            },
            "action_back": {
                "items": [
                    {"type": "action", "label": "Open", "action_id": "open"},
                    {"type": "action", "label": "Back", "action_id": "back"},
                ]
            },
            "setting_back": {
                "items": [
                    {
                        "type": "toggle",
                        "label": "Enabled",
                        "semantic_type": "bool",
                        "setting_id": "enabled",
                    },
                    {"type": "action", "label": "Back", "action_id": "back"},
                ]
            },
            "capture_exempt": {
                "layout_role": "capture",
                "items": [
                    {"type": "action", "label": "Confirm", "action_id": "confirm"}
                ],
            },
            "allow_exempt": {
                "allow_single_option": True,
                "allow_single_option_reason": "Intentional landing page.",
                "items": [{"type": "action", "label": "Open", "action_id": "open"}],
            },
        }
    }

    issues = contracts._validate_menu_structure_single_option_menus(
        "config/menu/structure.json",
        payload,
    )

    messages = "\n".join(issue.message for issue in issues)
    assert "submenu_wrapper" in messages
    assert "action_back" in messages
    assert "setting_back" in messages
    assert "capture_exempt" not in messages
    assert "allow_exempt" not in messages


def test_menu_control_typing_detects_mismatched_semantic_controls(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack = tmp_path / "config" / "project" / "policy_pack.json"
    menu_path = tmp_path / "config" / "menu" / "structure.json"
    _write_json(
        policy_pack,
        {
            "governance": {
                "menu_control_typing_contract": {
                    "setting_semantic_types": ["bool", "enum", "int", "float"],
                    "menu_control_types": ["toggle", "selector", "slider", "stepper"],
                    "setup_control_types": ["toggle", "selector", "slider", "stepper"],
                    "selector_options_key_required": True,
                    "enum_setup_option_source_tokens": ["piece_set_labels"],
                }
            }
        },
    )
    _write_json(
        menu_path,
        {
            "settings_option_labels": {"good_enum": ["A", "B"]},
            "menus": {
                "settings_game_root": {
                    "items": [
                        {
                            "id": "bad_enum_slider",
                            "type": "slider",
                            "semantic_type": "enum",
                            "setting_id": "bad_enum_slider",
                        }
                    ]
                }
            },
            "setup_fields": {
                "2d": [
                    {
                        "label": "Topology",
                        "attr": "topology_mode",
                        "semantic_type": "enum",
                        "control": "slider",
                        "min": 0,
                        "max": 2,
                    }
                ]
            },
        },
    )

    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)
    monkeypatch.setattr(contracts, "MENU_STRUCTURE_PATH", menu_path)

    issues = contracts._validate_menu_control_typing()

    assert any("bad_enum_slider" in issue.message for issue in issues)
    assert any(
        "enum fields must use control=selector" in issue.message for issue in issues
    )


def test_menu_control_typing_accepts_semantic_type_aligned_controls(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack = tmp_path / "config" / "project" / "policy_pack.json"
    menu_path = tmp_path / "config" / "menu" / "structure.json"
    _write_json(
        policy_pack,
        {
            "governance": {
                "menu_control_typing_contract": {
                    "setting_semantic_types": ["bool", "enum", "int", "float"],
                    "menu_control_types": ["toggle", "selector", "slider", "stepper"],
                    "setup_control_types": ["toggle", "selector", "slider", "stepper"],
                    "selector_options_key_required": True,
                    "enum_setup_option_source_tokens": ["piece_set_labels"],
                }
            }
        },
    )
    _write_json(
        menu_path,
        {
            "settings_option_labels": {
                "game_random_mode": ["Fixed seed", "True random"]
            },
            "menus": {
                "settings_game_root": {
                    "items": [
                        {
                            "id": "game_random_mode",
                            "type": "selector",
                            "semantic_type": "enum",
                            "options_key": "game_random_mode",
                            "setting_id": "game_random_mode",
                        },
                        {
                            "id": "game_seed",
                            "type": "stepper",
                            "semantic_type": "int",
                            "setting_id": "game_seed",
                        },
                        {
                            "id": "display_fullscreen",
                            "type": "toggle",
                            "semantic_type": "bool",
                            "setting_id": "display_fullscreen",
                        },
                    ]
                }
            },
            "setup_fields": {
                "2d": [
                    {
                        "label": "Piece set",
                        "attr": "piece_set_index",
                        "semantic_type": "enum",
                        "control": "selector",
                        "options_source": "piece_set_labels",
                    },
                    {
                        "label": "Board width",
                        "attr": "width",
                        "semantic_type": "int",
                        "control": "stepper",
                        "min": 6,
                        "max": 16,
                    },
                ]
            },
        },
    )

    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)
    monkeypatch.setattr(contracts, "MENU_STRUCTURE_PATH", menu_path)

    assert contracts._validate_menu_control_typing() == []


def test_deprecated_authority_checks_detect_reintroduced_path(
    tmp_path: Path, monkeypatch
) -> None:
    blocked = tmp_path / "docs" / "RDS_AND_CODEX.md"
    blocked.parent.mkdir(parents=True, exist_ok=True)
    blocked.write_text("stale redirect", encoding="utf-8")
    policy_pack = tmp_path / "config" / "project" / "policy_pack.json"
    _write_json(
        policy_pack,
        {
            "deprecated_authorities": {
                "blocked_paths": ["docs/RDS_AND_CODEX.md"],
                "reference_checks": [],
            }
        },
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)

    issues = contracts._validate_deprecated_authorities()

    assert issues
    assert any("deprecated authority path present" in issue.message for issue in issues)
