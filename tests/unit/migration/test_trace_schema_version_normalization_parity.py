from __future__ import annotations

import json
from pathlib import Path

import tools.migration.trace_schema_version_normalization_parity as parity


def test_fixture_loads_and_is_schema_version_metadata_only() -> None:
    fixture = parity._load_fixture()
    cases = fixture["cases"]
    assert isinstance(cases, list)
    assert len(cases) == 4
    for item in cases:
        assert isinstance(item, dict)
        metadata = item["metadata"]
        assert isinstance(metadata, dict)
        assert "events" not in metadata
        assert "board" not in metadata
        assert "pieces" not in metadata


def test_python_oracle_normalization_is_deterministic() -> None:
    cases = parity.python_oracle_cases()
    assert cases == parity.python_oracle_cases()
    assert [case.actual["schema_identity"] for case in cases] == [
        "trace_schema_v1:golden:migration:stable",
        "trace_schema_v1:golden:migration:stable",
        "trace_schema_v1:golden:migration:strict",
        "trace_schema_v1:replay:replay:legacy_compatible",
    ]


def test_numeric_and_string_schema_versions_normalize_consistently() -> None:
    assert parity.normalize_schema_version(1) == 1
    assert parity.normalize_schema_version("1") == 1
    assert parity.normalize_schema_version("v1") == 1
    assert parity.normalize_schema_version("schema-v1") == 1


def test_trace_kind_and_family_labels_normalize_consistently() -> None:
    normalized = parity.normalize_trace_schema_version(
        {
            "schema_version": "1",
            "trace_kind": "Golden Trace",
            "trace_family": "Godot Native Migration",
            "compatibility": "legacy-compatible",
        }
    )
    assert normalized == {
        "schema_version": 1,
        "trace_kind": "golden",
        "trace_family": "migration",
        "compatibility": "legacy_compatible",
        "schema_id": "trace_schema_v1",
        "schema_identity": "trace_schema_v1:golden:migration:legacy_compatible",
    }


def test_unknown_schema_versions_fail_with_actionable_error() -> None:
    try:
        parity.normalize_schema_version("v99")
    except ValueError as exc:
        assert "unknown schema_version" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_malformed_metadata_fails_with_actionable_error() -> None:
    try:
        parity.normalize_trace_schema_version(
            {"schema_version": 1, "trace_kind": "golden", "board": []}
        )
    except ValueError as exc:
        assert "must not include semantic payload keys" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_run_reports_advisory_when_native_unavailable_in_default_mode(
    monkeypatch,
) -> None:
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


def test_compare_cases_reports_actionable_mismatch() -> None:
    oracle_cases = parity.python_oracle_cases()
    native_cases = [
        {"name": case.name, "normalized": dict(case.expected)}
        for case in oracle_cases[:-1]
    ]
    bad = dict(oracle_cases[-1].expected)
    bad["schema_identity"] = "wrong"
    native_cases.append({"name": oracle_cases[-1].name, "normalized": bad})

    failures = parity.compare_cases(native_cases, oracle_cases)

    assert any("schema/version mismatch" in failure for failure in failures)
    assert any(
        "expected Python normalized schema/version identity" in failure
        for failure in failures
    )
    assert any(
        "actual native/provisional schema/version identity" in failure
        for failure in failures
    )


def test_load_fixture_rejects_malformed_fixture(tmp_path: Path, monkeypatch) -> None:
    fixture = tmp_path / "trace_schema_version_normalization.json"
    fixture.write_text(
        json.dumps(
            {
                "slice": "trace_schema_version_normalization",
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
