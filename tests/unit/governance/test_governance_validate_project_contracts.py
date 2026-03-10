from __future__ import annotations

import json
from pathlib import Path

import tools.governance.validate_project_contracts as contracts


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_policy_registry_sync_passes(tmp_path: Path, monkeypatch) -> None:
    policy_path = tmp_path / "project_policy.json"
    registry_path = tmp_path / "policy_registry.json"
    payload = {
        "policy_pack": {
            "registry_manifest": "config/project/policy/manifests/policy_registry.json",
            "policies": [
                {"id": "formatting", "source": "docs/policies/POLICY_FORMATTING.md"}
            ],
            "contracts": [
                {
                    "id": "canonical_maintenance",
                    "path": "config/project/policy/manifests/canonical_maintenance.json",
                    "validated_by": "tools/governance/validate_project_contracts.py",
                }
            ],
        }
    }
    _write_json(policy_path, payload)
    _write_json(
        registry_path,
        {
            "policies": payload["policy_pack"]["policies"],
            "contracts": payload["policy_pack"]["contracts"],
        },
    )
    monkeypatch.setattr(contracts, "PROJECT_POLICY_PATH", policy_path)
    monkeypatch.setattr(contracts, "POLICY_REGISTRY_PATH", registry_path)
    issues = contracts._validate_policy_registry_sync()
    assert issues == []


def test_policy_registry_sync_detects_drift(tmp_path: Path, monkeypatch) -> None:
    policy_path = tmp_path / "project_policy.json"
    registry_path = tmp_path / "policy_registry.json"
    _write_json(
        policy_path,
        {
            "policy_pack": {
                "registry_manifest": "config/project/policy/manifests/policy_registry.json",
                "policies": [
                    {"id": "formatting", "source": "docs/policies/POLICY_FORMATTING.md"}
                ],
                "contracts": [
                    {
                        "id": "canonical_maintenance",
                        "path": "config/project/policy/manifests/canonical_maintenance.json",
                        "validated_by": "tools/governance/validate_project_contracts.py",
                    }
                ],
            }
        },
    )
    _write_json(
        registry_path,
        {
            "policies": [],
            "contracts": [],
        },
    )
    monkeypatch.setattr(contracts, "PROJECT_POLICY_PATH", policy_path)
    monkeypatch.setattr(contracts, "POLICY_REGISTRY_PATH", registry_path)
    issues = contracts._validate_policy_registry_sync()
    assert issues
    assert any("out of sync" in issue.message for issue in issues)


def test_policy_manifest_string_safety_detects_path_like_literals(
    tmp_path: Path, monkeypatch
) -> None:
    policy_root = tmp_path / "config" / "project" / "policy"
    manifests_dir = policy_root / "manifests"
    _write_json(policy_root / "pack.json", {"version": "test"})
    _write_json(
        manifests_dir / "wheel_reuse_rules.json",
        {
            "rules": [
                {
                    "id": "test",
                    "forbidden_regex": [r"value:[ \\t]*\n[ \\t]*t:" + r"\s*"],
                }
            ]
        },
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_MANIFEST_DIR", manifests_dir)
    issues = contracts._validate_policy_manifest_string_safety()
    assert issues
    assert any("path-like literal" in issue.message for issue in issues)


def test_policy_manifest_string_safety_allows_clean_manifests(
    tmp_path: Path, monkeypatch
) -> None:
    policy_root = tmp_path / "config" / "project" / "policy"
    manifests_dir = policy_root / "manifests"
    _write_json(policy_root / "pack.json", {"version": "test"})
    _write_json(
        manifests_dir / "wheel_reuse_rules.json",
        {"rules": [{"id": "test", "forbidden_regex": [r"value:[ \t]*\n[ \t]*x"]}]},
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_MANIFEST_DIR", manifests_dir)
    issues = contracts._validate_policy_manifest_string_safety()
    assert issues == []

def test_contributor_directives_include_staged_migration_contract() -> None:
    payload = json.loads(contracts.CONTRIBUTOR_DIRECTIVES_PATH.read_text(encoding="utf-8"))
    directives = payload["directives"]
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

