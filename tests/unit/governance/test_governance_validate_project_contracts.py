from __future__ import annotations

import json
from pathlib import Path

import tools.governance.validate_project_contracts as contracts


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_policy_index_sync_detects_missing_unified_contract_token(
    tmp_path: Path, monkeypatch
) -> None:
    governance_path = tmp_path / "config" / "project" / "policy" / "governance.json"
    _write_json(
        governance_path,
        {
            "contracts": {
                "canonical_maintenance": "config/project/policy/manifests/canonical_maintenance.json",
                "secret_scan": "config/project/policy/manifests/secret_scan.json",
            }
        },
    )
    index_path = tmp_path / "docs" / "policies" / "INDEX.md"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        "config/project/policy/governance.json\nconfig/project/policy/code_rules.json\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(contracts, "GOVERNANCE_PATH", governance_path)
    monkeypatch.setattr(contracts, "POLICY_INDEX_PATH", index_path)

    issues = contracts._validate_policy_index_sync()

    assert issues
    assert any("canonical_maintenance.json" in issue.message for issue in issues)


def test_policy_manifest_string_safety_detects_path_like_literals(
    tmp_path: Path, monkeypatch
) -> None:
    policy_root = tmp_path / "config" / "project" / "policy"
    manifests_dir = policy_root / "manifests"
    path_like_literal = r"value:[ \t]*\n[ \t]*" + "C:" + r"\\temp"
    _write_json(policy_root / "governance.json", {"schema_version": 1})
    _write_json(policy_root / "code_rules.json", {"schema_version": 1})
    _write_json(
        manifests_dir / "help_assets_manifest.json",
        {"rules": [{"id": "test", "example": path_like_literal}]},
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "GOVERNANCE_PATH", policy_root / "governance.json")
    monkeypatch.setattr(contracts, "CODE_RULES_PATH", policy_root / "code_rules.json")
    monkeypatch.setattr(contracts, "POLICY_MANIFEST_DIR", manifests_dir)
    issues = contracts._validate_policy_manifest_string_safety()
    assert issues
    assert any("path-like literal" in issue.message for issue in issues)


def test_policy_manifest_string_safety_allows_clean_manifests(
    tmp_path: Path, monkeypatch
) -> None:
    policy_root = tmp_path / "config" / "project" / "policy"
    manifests_dir = policy_root / "manifests"
    _write_json(policy_root / "governance.json", {"schema_version": 1})
    _write_json(policy_root / "code_rules.json", {"schema_version": 1})
    _write_json(
        manifests_dir / "help_assets_manifest.json",
        {"rules": [{"id": "test", "forbidden_regex": [r"value:[ \t]*\n[ \t]*x"]}]},
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "GOVERNANCE_PATH", policy_root / "governance.json")
    monkeypatch.setattr(contracts, "CODE_RULES_PATH", policy_root / "code_rules.json")
    monkeypatch.setattr(contracts, "POLICY_MANIFEST_DIR", manifests_dir)
    issues = contracts._validate_policy_manifest_string_safety()
    assert issues == []


def test_governance_directives_include_staged_migration_contract() -> None:
    payload = json.loads(contracts.GOVERNANCE_PATH.read_text(encoding="utf-8"))
    directives = payload["contributor_directives"]["directives"]
    directive_ids = {item["id"] for item in directives}
    assert {
        "staged_migration_honesty",
        "additive_migration_first",
        "delta_report_required",
    }.issubset(directive_ids)


def test_rds_and_codex_rule_requires_control_contract_tokens() -> None:
    manifest = contracts._load_manifest()
    rules = manifest["content_rules"]
    rds_rule = next(rule for rule in rules if rule["file"] == "docs/RDS_AND_CODEX.md")
    must_contain = set(rds_rule["must_contain"])
    assert "do not treat partial progress as completion" in must_contain
    assert (
        "add new modules first, route one flow to them, verify, and only then remove old paths"
        in must_contain
    )
    assert (
        "provide a delta report with: files added, files modified, files not touched, satisfied acceptance criteria, unsatisfied acceptance criteria, remaining old paths, and follow-up blockers"
        in must_contain
    )
