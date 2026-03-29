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
    governance_path = tmp_path / "governance.json"
    code_rules_path = tmp_path / "code_rules.json"
    _write_json(
        governance_path,
        {
            "verification_command": "./scripts/verify.sh",
            "ci_entrypoint": "./scripts/ci_check.sh",
        },
    )
    _write_json(code_rules_path, {"sanitation": {}})

    monkeypatch.setattr(validate_governance, "GOVERNANCE_PATH", governance_path)
    monkeypatch.setattr(validate_governance, "CODE_RULES_PATH", code_rules_path)

    issues = validate_governance._validate_unified_manifest_shape()
    assert issues
    assert any("governance.json missing required key: architecture" in issue for issue in issues)
    assert any("code_rules.json missing required key: wheel_reuse" in issue for issue in issues)


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
