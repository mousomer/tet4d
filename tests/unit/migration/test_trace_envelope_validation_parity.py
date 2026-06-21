from __future__ import annotations

import json
from pathlib import Path

import tools.parity.trace_envelope_validation_parity as parity


def test_fixture_loads_and_covers_expected_envelope_cases() -> None:
    fixture = parity._load_fixture()
    cases = fixture["cases"]
    assert isinstance(cases, list)
    assert [case["name"] for case in cases] == [
        "valid-minimal-envelope",
        "valid-unknown-event-payloads-ignored",
        "missing-generator-envelope-object",
        "missing-trace-version",
        "missing-final-state-hash-digest",
        "malformed-top-level-trace-type",
        "malformed-frames-container",
    ]


def test_valid_minimal_trace_envelope_passes() -> None:
    diagnostics = parity.validate_trace_envelope(
        {
            "case_id": "valid",
            "dimension": 2,
            "final": {"state_hash": "abc"},
            "frames": [],
            "generator": {"name": "unit", "schema_version": 1},
            "trace_type": "gameplay",
            "trace_version": 1,
        }
    )

    assert diagnostics == []


def test_invalid_fixture_cases_fail_with_stable_diagnostics() -> None:
    cases = {case.name: case for case in parity.python_oracle_cases()}

    assert cases["missing-generator-envelope-object"].actual_diagnostics == [
        "missing required field: generator"
    ]
    assert cases["missing-trace-version"].actual_diagnostics == [
        "missing required field: trace_version"
    ]
    assert cases["missing-final-state-hash-digest"].actual_diagnostics == [
        "missing required field: state_hash"
    ]
    assert cases["malformed-top-level-trace-type"].actual_diagnostics == [
        "malformed trace: expected object, got array"
    ]
    assert cases["malformed-frames-container"].actual_diagnostics == [
        "malformed field: frames must be an array, got object"
    ]


def test_python_oracle_fixture_expectations_match_actual_validation() -> None:
    cases = parity.python_oracle_cases()

    assert cases == parity.python_oracle_cases()
    assert all(
        case.actual_valid == case.expected_valid
        and case.actual_diagnostics == case.expected_diagnostics
        for case in cases
    )


def test_event_payload_semantics_are_not_inspected() -> None:
    diagnostics = parity.validate_trace_envelope(
        {
            "case_id": "unknown-event-payload",
            "dimension": 4,
            "final": {"state_hash": "abc"},
            "frames": [
                {
                    "events": [
                        {
                            "event_type": "unknown",
                            "board": "not validated by this slice",
                            "piece_position": {"x": "also ignored"},
                        }
                    ],
                    "frame_index": 0,
                }
            ],
            "generator": {"name": "unit", "schema_version": 1},
            "trace_type": "endgame",
            "trace_version": 1,
        }
    )

    assert diagnostics == []


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
        {
            "name": case.name,
            "valid": case.expected_valid,
            "diagnostics": list(case.expected_diagnostics),
        }
        for case in oracle_cases
    ]
    native_cases[0]["valid"] = False
    native_cases[0]["diagnostics"] = ["wrong"]

    failures = parity.compare_cases(native_cases, oracle_cases)

    assert any("trace envelope validation mismatch" in failure for failure in failures)
    assert any("expected Python validation result" in failure for failure in failures)
    assert any(
        "actual native/provisional validation result" in failure for failure in failures
    )


def test_load_fixture_rejects_malformed_fixture(tmp_path: Path, monkeypatch) -> None:
    fixture = tmp_path / "trace_envelope_validation.json"
    fixture.write_text(
        json.dumps(
            {
                "slice": "trace_envelope_validation",
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
