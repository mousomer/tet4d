from __future__ import annotations

import json
from subprocess import CompletedProcess

import tools.migration.first_subsystem_parity_pilot as pilot


def test_python_oracle_stable_hash_text_matches_known_values() -> None:
    assert pilot.python_oracle_stable_hash_text("") == "cbf29ce484222325"
    assert pilot.python_oracle_stable_hash_text("tet4d") == "49fb984865ccbc22"
    assert pilot.python_oracle_stable_hash_text("oracle-check") == "e476b146b3fe66de"


def test_compare_cases_detects_mismatch() -> None:
    native_cases = [
        {"input": "", "native_hash": "cbf29ce484222325"},
        {"input": "tet4d", "native_hash": "0000000000000000"},
    ]

    failures = pilot.compare_cases(native_cases)

    assert any("hash mismatch" in failure for failure in failures)
    assert any("expected" in failure and "got" in failure for failure in failures)


def test_load_native_cases_parses_native_pilot_output(monkeypatch) -> None:
    payload = {
        "cases": [
            {"input": "", "native_hash": "cbf29ce484222325"},
            {"input": "tet4d", "native_hash": "49fb984865ccbc22"},
            {"input": "oracle-check", "native_hash": "e476b146b3fe66de"},
            {"input": "hash-bridge", "native_hash": "71e8bc601a9fb8e1"},
        ]
    }

    def fake_run(*args, **kwargs):
        return CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr(pilot.subprocess, "run", fake_run)

    native_cases = pilot.load_native_cases(["pilot"])

    assert native_cases == payload["cases"]
    assert pilot.compare_cases(native_cases) == []


def test_python_oracle_cases_are_deterministic() -> None:
    assert pilot.PILOT_CASES == ("", "tet4d", "oracle-check", "hash-bridge")
    assert pilot.python_oracle_cases() == pilot.python_oracle_cases()


def test_run_reports_advisory_when_native_unavailable_in_default_mode(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        pilot,
        "load_native_cases",
        lambda command=None: (_ for _ in ()).throw(RuntimeError("compiler missing")),
    )

    result = pilot.run(strict=False)

    assert result.failures == []
    assert result.advisories
    assert any("TET4D_STRICT_PARITY=1" in advisory for advisory in result.advisories)


def test_run_fails_when_native_unavailable_in_strict_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        pilot,
        "load_native_cases",
        lambda command=None: (_ for _ in ()).throw(RuntimeError("compiler missing")),
    )

    result = pilot.run(strict=True)

    assert result.advisories == []
    assert any("compiler missing" in failure for failure in result.failures)
