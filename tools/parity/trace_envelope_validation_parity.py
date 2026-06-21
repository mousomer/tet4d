from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRICT_PARITY_ENV = "TET4D_STRICT_PARITY"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "parity" / "trace_envelope_validation.json"


@dataclass(frozen=True)
class EnvelopeValidationCase:
    name: str
    trace: object
    expected_valid: bool
    expected_diagnostics: list[str]
    actual_diagnostics: list[str]

    @property
    def actual_valid(self) -> bool:
        return not self.actual_diagnostics


@dataclass(frozen=True)
class ParityResult:
    failures: list[str]
    advisories: list[str]


def _field_type(value: object) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if value is None:
        return "null"
    return type(value).__name__


def _require_key(payload: dict[str, object], key: str, diagnostics: list[str]) -> bool:
    if key not in payload:
        diagnostics.append(f"missing required field: {key}")
        return False
    return True


def _require_string(
    payload: dict[str, object], key: str, diagnostics: list[str]
) -> None:
    if not _require_key(payload, key, diagnostics):
        return
    if not isinstance(payload[key], str) or not payload[key]:
        diagnostics.append(
            f"malformed field: {key} must be a non-empty string, got {_field_type(payload[key])}"
        )


def _require_integer(
    payload: dict[str, object], key: str, diagnostics: list[str]
) -> None:
    if not _require_key(payload, key, diagnostics):
        return
    if isinstance(payload[key], bool) or not isinstance(payload[key], int):
        diagnostics.append(
            f"malformed field: {key} must be an integer, got {_field_type(payload[key])}"
        )


def validate_trace_envelope(trace: object) -> list[str]:
    diagnostics: list[str] = []
    if not isinstance(trace, dict):
        return [f"malformed trace: expected object, got {_field_type(trace)}"]

    _require_string(trace, "trace_type", diagnostics)
    _require_integer(trace, "trace_version", diagnostics)
    _require_string(trace, "case_id", diagnostics)
    _require_integer(trace, "dimension", diagnostics)

    if _require_key(trace, "generator", diagnostics):
        generator = trace["generator"]
        if not isinstance(generator, dict):
            diagnostics.append(
                f"malformed field: generator must be an object, got {_field_type(generator)}"
            )
        else:
            _require_string(generator, "name", diagnostics)
            _require_integer(generator, "schema_version", diagnostics)

    if _require_key(trace, "frames", diagnostics):
        frames = trace["frames"]
        if not isinstance(frames, list):
            diagnostics.append(
                f"malformed field: frames must be an array, got {_field_type(frames)}"
            )

    if _require_key(trace, "final", diagnostics):
        final = trace["final"]
        if not isinstance(final, dict):
            diagnostics.append(
                f"malformed field: final must be an object, got {_field_type(final)}"
            )
        else:
            _require_string(final, "state_hash", diagnostics)

    return diagnostics


def _load_fixture() -> dict[str, object]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("trace envelope validation fixture must be an object")
    if payload.get("slice") != "trace_envelope_validation":
        raise RuntimeError("trace envelope validation fixture has the wrong slice")
    if payload.get("authority") != "python":
        raise RuntimeError(
            "trace envelope validation fixture must declare python authority"
        )
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise RuntimeError(
            "trace envelope validation fixture must contain a cases array"
        )
    return payload


def python_oracle_cases() -> list[EnvelopeValidationCase]:
    fixture = _load_fixture()
    cases = fixture["cases"]
    assert isinstance(cases, list)
    validation_cases: list[EnvelopeValidationCase] = []
    for item in cases:
        if not isinstance(item, dict):
            raise RuntimeError("trace envelope validation cases must be objects")
        name = item.get("name")
        if not isinstance(name, str):
            raise RuntimeError("trace envelope validation case missing name")
        if "trace" not in item:
            raise RuntimeError(f"trace envelope validation case {name!r} missing trace")
        expected = item.get("expected")
        if not isinstance(expected, dict):
            raise RuntimeError(
                f"trace envelope validation case {name!r} missing expected result"
            )
        expected_valid = expected.get("valid")
        expected_diagnostics = expected.get("diagnostics")
        if not isinstance(expected_valid, bool):
            raise RuntimeError(
                f"trace envelope validation case {name!r} missing expected valid flag"
            )
        if not isinstance(expected_diagnostics, list) or not all(
            isinstance(diagnostic, str) for diagnostic in expected_diagnostics
        ):
            raise RuntimeError(
                f"trace envelope validation case {name!r} expected diagnostics must be strings"
            )

        trace = item["trace"]
        actual_diagnostics = validate_trace_envelope(trace)
        validation_cases.append(
            EnvelopeValidationCase(
                name=name,
                trace=trace,
                expected_valid=expected_valid,
                expected_diagnostics=list(expected_diagnostics),
                actual_diagnostics=actual_diagnostics,
            )
        )
    return validation_cases


def compare_cases(
    native_cases: list[dict[str, object]],
    oracle_cases: list[EnvelopeValidationCase] | None = None,
) -> list[str]:
    oracle_index = {
        case.name: {
            "valid": case.expected_valid,
            "diagnostics": case.expected_diagnostics,
        }
        for case in (oracle_cases or python_oracle_cases())
    }
    failures: list[str] = []
    native_names = {case.get("name") for case in native_cases if isinstance(case, dict)}
    oracle_names = set(oracle_index)

    for missing in sorted(oracle_names - native_names):
        failures.append(f"missing native parity case: {missing}")
    for extra in sorted(native_names - oracle_names):
        failures.append(f"unexpected native parity case: {extra}")
    for case in native_cases:
        if not isinstance(case, dict):
            failures.append("native parity cases must be objects")
            continue
        name = case.get("name")
        valid = case.get("valid")
        diagnostics = case.get("diagnostics")
        if (
            not isinstance(name, str)
            or not isinstance(valid, bool)
            or not isinstance(diagnostics, list)
        ):
            failures.append(
                "native parity cases must include name, valid, and diagnostics"
            )
            continue
        if not all(isinstance(diagnostic, str) for diagnostic in diagnostics):
            failures.append("native parity diagnostics must be strings")
            continue
        expected = oracle_index.get(name)
        if expected is None:
            continue
        if valid != expected["valid"] or diagnostics != expected["diagnostics"]:
            failures.append(
                "trace envelope validation mismatch for "
                f"{name}: expected Python validation result {expected!r}, actual native/provisional validation result "
                f"{{'valid': {valid!r}, 'diagnostics': {diagnostics!r}}}"
            )
    return failures


def load_native_cases() -> list[dict[str, object]]:
    raise RuntimeError(
        "no safe native/provisional route is exposed for trace envelope validation"
    )


def strict_mode_enabled() -> bool:
    return STRICT_PARITY_ENV in os.environ and os.environ[STRICT_PARITY_ENV] != "0"


def run(strict: bool | None = None) -> ParityResult:
    active_strict = strict_mode_enabled() if strict is None else strict
    oracle_cases = python_oracle_cases()
    oracle_failures = [
        (
            "fixture mismatch for "
            f"{case.name}: expected Python trace envelope validation result "
            f"{{'valid': {case.expected_valid!r}, 'diagnostics': {case.expected_diagnostics!r}}}, "
            f"actual Python trace envelope validation result "
            f"{{'valid': {case.actual_valid!r}, 'diagnostics': {case.actual_diagnostics!r}}}"
        )
        for case in oracle_cases
        if case.actual_valid != case.expected_valid
        or case.actual_diagnostics != case.expected_diagnostics
    ]
    if oracle_failures:
        return ParityResult(failures=oracle_failures, advisories=[])

    try:
        native_cases = load_native_cases()
    except RuntimeError as exc:
        message = (
            "native/provisional output unavailable: "
            f"{exc} "
            f"(rerun after adding a safe native route or set {STRICT_PARITY_ENV}=1 to make unavailability blocking)"
        )
        if active_strict:
            return ParityResult(failures=[message], advisories=[])
        return ParityResult(failures=[], advisories=[message])

    return ParityResult(
        failures=compare_cases(native_cases, oracle_cases), advisories=[]
    )


def main() -> int:
    result = run()
    if result.failures:
        print("Trace envelope validation parity failed:")
        for failure in result.failures:
            print(f"- {failure}")
        return 1

    print("Trace envelope validation parity:")
    print("- slice: trace_envelope_validation")
    print(f"- fixture: {FIXTURE_PATH.relative_to(ROOT).as_posix()}")
    print(f"- case count: {len(python_oracle_cases())}")
    print("- Python oracle status: pass")
    if result.advisories:
        print("- native/provisional status: unavailable")
        for advisory in result.advisories:
            print(f"- advisory: {advisory}")
        print("- comparison status: advisory")
    else:
        print("- native/provisional status: available")
        print("- comparison status: pass")
    print(f"- strict mode: {'yes' if strict_mode_enabled() else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
