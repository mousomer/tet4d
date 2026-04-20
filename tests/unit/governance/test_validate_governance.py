from __future__ import annotations

import json
from pathlib import Path

import tools.governance.check_risk_gates as risk_gates
import tools.governance.validate_governance as validate_governance


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_unified_manifest_shape_requires_core_sections(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack_path = tmp_path / "policy_pack.json"
    _write_json(
        policy_pack_path,
        {
            "authority_model": {
                "machine_authority": "config/project/policy_pack.json",
                "dispatch_file": "AGENTS.md",
                "workflow_doc": "docs/WORKFLOW_CODEX.md",
                "handoff_doc": "CURRENT_STATE.md",
                "product_requirements_root": "docs/rds/",
            },
            "governance": {
                "verification_command": "./scripts/verify.sh",
                "ci_entrypoint": "./scripts/ci_check.sh",
            },
            "code_rules": {"sanitation": {}},
        },
    )

    monkeypatch.setattr(validate_governance, "POLICY_PACK_PATH", policy_pack_path)

    issues = validate_governance._validate_unified_manifest_shape()
    assert issues
    assert any(
        "policy_pack.json governance missing required key: architecture" in issue
        for issue in issues
    )
    assert any(
        "policy_pack.json code_rules missing required key: wheel_reuse" in issue
        for issue in issues
    )
    assert any(
        "policy_pack.json code_rules missing required key: config_backed_runtime_constants"
        in issue
        for issue in issues
    )


def test_risk_gates_accept_unified_required_ids() -> None:
    directives_payload = {
        "required_ci_enforced_ids": ["verification_required"],
        "directives": [
            {
                "id": "verification_required",
                "enforced_by": ["scripts/verify.sh"],
            }
        ],
    }
    issues = risk_gates._check_contributor_directives({}, directives_payload)
    assert issues == []


def test_main_executes_policy_runtime_rules_check(monkeypatch, capsys) -> None:
    calls: list[str] = []

    monkeypatch.setattr(validate_governance, "_validate_unified_manifest_shape", lambda: [])
    monkeypatch.setattr(
        validate_governance,
        "_checks",
        lambda: (
            validate_governance.GovernanceCheck(
                "policy_runtime_rules", lambda: calls.append("policy_runtime_rules") or 0
            ),
        ),
    )

    assert validate_governance.main() == 0
    assert calls == ["policy_runtime_rules"]
    assert "Unified governance validation passed." in capsys.readouterr().out
