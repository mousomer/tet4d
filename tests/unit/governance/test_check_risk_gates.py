from __future__ import annotations

import tools.governance.check_risk_gates as risk


def _payload_security(**overrides):
    payload = {
        "security_ownership": {
            "enabled": True,
            "sensitive_globs": ["tools/governance/*.py"],
            "min_sensitive_files": 2,
            "min_distinct_authors_per_file": 1,
            "max_files_below_min_authors": 0,
            "target_min_distinct_authors_per_file": 2,
            "max_files_below_target_authors_warn": 0,
        }
    }
    payload["security_ownership"].update(overrides)
    return payload


def test_security_ownership_warns_on_target_only(monkeypatch) -> None:
    monkeypatch.setattr(
        risk,
        "_match_sensitive_files",
        lambda _globs: ["a.py", "b.py"],
    )
    monkeypatch.setattr(risk, "_distinct_authors_for_file", lambda _path: 1)
    issues, warnings = risk._check_security_ownership(_payload_security())
    assert issues == []
    assert warnings
    assert "below target ownership threshold" in warnings[0].message


def test_security_ownership_blocks_when_min_violated(monkeypatch) -> None:
    monkeypatch.setattr(
        risk,
        "_match_sensitive_files",
        lambda _globs: ["a.py", "b.py"],
    )
    monkeypatch.setattr(risk, "_distinct_authors_for_file", lambda _path: 1)
    issues, warnings = risk._check_security_ownership(
        _payload_security(min_distinct_authors_per_file=2)
    )
    assert issues
    assert warnings == []
