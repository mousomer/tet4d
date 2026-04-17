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


def test_required_paths_detect_untracked_file(
    tmp_path: Path, monkeypatch
) -> None:
    rel = "docs/WORKFLOW_CODEX.md"
    workflow_doc = tmp_path / rel
    workflow_doc.parent.mkdir(parents=True, exist_ok=True)
    workflow_doc.write_text("workflow", encoding="utf-8")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "_git_tracked_paths", lambda issues: set())

    issues = contracts._validate_required_paths({"required_paths": {"root_docs": [rel]}})

    assert any(
        issue.message == f"required path is not tracked in git: {rel}"
        for issue in issues
    )


def test_required_paths_accept_git_tracked_file(
    tmp_path: Path, monkeypatch
) -> None:
    rel = "docs/WORKFLOW_CODEX.md"
    workflow_doc = tmp_path / rel
    workflow_doc.parent.mkdir(parents=True, exist_ok=True)
    workflow_doc.write_text("workflow", encoding="utf-8")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "_git_tracked_paths", lambda issues: {rel})

    issues = contracts._validate_required_paths({"required_paths": {"root_docs": [rel]}})

    assert issues == []


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
    current_state_rule = next(rule for rule in rules if rule["file"] == "CURRENT_STATE.md")

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
                "settings_root": {
                    "items": [{"type": "submenu", "label": "Different"}]
                }
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
