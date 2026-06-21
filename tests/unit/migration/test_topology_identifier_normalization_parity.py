from __future__ import annotations

import json
from pathlib import Path

import tools.migration.topology_identifier_normalization_parity as parity


def test_python_oracle_cases_are_deterministic() -> None:
    cases = parity.python_oracle_cases()
    assert [case.name for case in cases] == [
        "plain-2d-canonical",
        "plain-2d-spacing",
        "wrap-all-4d-alias",
        "topology-prefix",
        "torus-alias",
        "projective-space-alias",
        "sphere-like-alias",
    ]
    assert cases == parity.python_oracle_cases()


def test_python_oracle_normalization_is_exact() -> None:
    cases = parity.python_oracle_cases()
    assert [case.actual for case in cases] == [
        "plain_2d",
        "plain_2d",
        "wrap_all_4d",
        "plain_3d",
        "wrap_all_2d",
        "invert_all_4d",
        "sphere_like_4d",
    ]


def test_normalize_topology_identifier_rejects_unknown_identifiers() -> None:
    try:
        parity.normalize_topology_identifier("mystery 4d")
    except ValueError as exc:
        assert "unknown topology identifier" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_compare_cases_detects_identifier_mismatch() -> None:
    oracle_cases = parity.python_oracle_cases()
    native_cases = [
        {"name": oracle_cases[0].name, "identifier": "plain_2d"},
        {"name": oracle_cases[1].name, "identifier": "plain_2d"},
        {"name": oracle_cases[2].name, "identifier": "wrap_all_4d"},
        {"name": oracle_cases[3].name, "identifier": "plain_3d"},
        {"name": oracle_cases[4].name, "identifier": "wrap_all_2d"},
        {"name": oracle_cases[5].name, "identifier": "invert_all_4d"},
        {"name": oracle_cases[6].name, "identifier": "sphere_like_4d-wrong"},
    ]

    failures = parity.compare_cases(native_cases, oracle_cases)

    assert any("identifier mismatch" in failure for failure in failures)
    assert any("expected Python canonical identifier" in failure for failure in failures)
    assert any("actual native/provisional canonical identifier" in failure for failure in failures)


def test_run_reports_advisory_when_native_unavailable_in_default_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        parity,
        "load_native_cases",
        lambda: (_ for _ in ()).throw(RuntimeError("compiler missing")),
    )

    result = parity.run(strict=False)

    assert result.failures == []
    assert result.advisories
    assert any("TET4D_STRICT_PARITY=1" in advisory for advisory in result.advisories)


def test_run_fails_when_native_unavailable_in_strict_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        parity,
        "load_native_cases",
        lambda: (_ for _ in ()).throw(RuntimeError("compiler missing")),
    )

    result = parity.run(strict=True)

    assert result.advisories == []
    assert any("compiler missing" in failure for failure in result.failures)


def test_load_fixture_rejects_malformed_payload(tmp_path: Path, monkeypatch) -> None:
    fixture = tmp_path / "topology_identifier_normalization.json"
    fixture.write_text(
        json.dumps(
            {
                "slice": "topology_identifier_normalization",
                "authority": "python",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(parity, "FIXTURE_PATH", fixture)

    try:
        parity.python_oracle_cases()
    except RuntimeError as exc:
        assert "cases array" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_load_fixture_rejects_bad_slice(tmp_path: Path, monkeypatch) -> None:
    fixture = tmp_path / "topology_identifier_normalization.json"
    fixture.write_text(
        json.dumps(
            {
                "slice": "wrong",
                "authority": "python",
                "cases": [
                    {
                        "name": "plain-2d-canonical",
                        "input": "plain_2d",
                        "expected": "plain_2d",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(parity, "FIXTURE_PATH", fixture)

    try:
        parity.python_oracle_cases()
    except RuntimeError as exc:
        assert "wrong slice" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
