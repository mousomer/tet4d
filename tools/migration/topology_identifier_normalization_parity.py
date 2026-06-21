from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRICT_PARITY_ENV = "TET4D_STRICT_PARITY"
FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "parity" / "topology_identifier_normalization.json"
)

_DIMENSION_SUFFIXES = {"2d": 2, "3d": 3, "4d": 4}
_DIMENSION_TOKENS = {"2": 2, "3": 3, "4": 4}
_BASE_ALIASES = {
    "plain": "plain",
    "bounded": "plain",
    "wrap": "wrap_all",
    "wrap_all": "wrap_all",
    "torus": "wrap_all",
    "invert": "invert_all",
    "invert_all": "invert_all",
    "projective": "invert_all",
    "projective_space": "invert_all",
    "sphere": "sphere_like",
    "sphere_like": "sphere_like",
}


@dataclass(frozen=True)
class TopologyIdentifierCase:
    name: str
    input: str
    expected: str
    actual: str


@dataclass(frozen=True)
class ParityResult:
    failures: list[str]
    advisories: list[str]


def normalize_topology_identifier(raw: str) -> str:
    if not isinstance(raw, str):
        raise TypeError("topology identifier must be a string")
    cleaned = raw.strip().lower()
    if not cleaned:
        raise ValueError("topology identifier cannot be empty")
    cleaned = cleaned.replace("-", "_").replace("/", "_")
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if cleaned.startswith("topology_"):
        cleaned = cleaned.removeprefix("topology_")
    tokens = [token for token in cleaned.split("_") if token]
    if len(tokens) < 2:
        raise ValueError(
            f"topology identifier {raw!r} must include a base name and dimension"
        )
    suffix = tokens.pop()
    if suffix in _DIMENSION_SUFFIXES:
        dimension = _DIMENSION_SUFFIXES[suffix]
    elif suffix in _DIMENSION_TOKENS:
        dimension = _DIMENSION_TOKENS[suffix]
    else:
        raise ValueError(
            f"topology identifier {raw!r} must end with a dimension suffix like 2D, 3D, or 4D"
        )
    base = "_".join(tokens)
    canonical_base = _BASE_ALIASES.get(base)
    if canonical_base is None:
        raise ValueError(
            f"unknown topology identifier {raw!r}; expected plain, wrap all, invert all, torus, projective space, or sphere-like naming"
        )
    return f"{canonical_base}_{dimension}d"


def _load_fixture() -> dict[str, object]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(
            "topology identifier normalization fixture must be an object"
        )
    if payload.get("slice") != "topology_identifier_normalization":
        raise RuntimeError(
            "topology identifier normalization fixture has the wrong slice"
        )
    if payload.get("authority") != "python":
        raise RuntimeError(
            "topology identifier normalization fixture must declare python authority"
        )
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise RuntimeError(
            "topology identifier normalization fixture must contain a cases array"
        )
    return payload


def python_oracle_cases() -> list[TopologyIdentifierCase]:
    fixture = _load_fixture()
    cases = fixture["cases"]
    assert isinstance(cases, list)
    normalized: list[TopologyIdentifierCase] = []
    for item in cases:
        if not isinstance(item, dict):
            raise RuntimeError(
                "topology identifier normalization cases must be objects"
            )
        name = item.get("name")
        input_value = item.get("input")
        expected = item.get("expected")
        if not isinstance(name, str):
            raise RuntimeError("topology identifier normalization case missing name")
        if not isinstance(input_value, str):
            raise RuntimeError(
                f"topology identifier normalization case {name!r} missing input"
            )
        if not isinstance(expected, str):
            raise RuntimeError(
                f"topology identifier normalization case {name!r} missing expected"
            )
        actual = normalize_topology_identifier(input_value)
        normalized.append(
            TopologyIdentifierCase(
                name=name,
                input=input_value,
                expected=expected,
                actual=actual,
            )
        )
    return normalized


def compare_cases(
    native_cases: list[dict[str, str]],
    oracle_cases: list[TopologyIdentifierCase] | None = None,
) -> list[str]:
    oracle_index = {
        case.name: {
            "input": case.input,
            "expected": case.expected,
            "actual": case.actual,
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
        identifier = case.get("identifier")
        if not isinstance(name, str) or not isinstance(identifier, str):
            failures.append("native parity cases must include name and identifier")
            continue
        expected = oracle_index.get(name)
        if expected is None:
            continue
        if identifier != expected["expected"]:
            failures.append(
                "identifier mismatch for "
                f"{name}: input {expected['input']!r}, expected Python canonical identifier {expected['expected']}, actual native/provisional canonical identifier {identifier}"
            )
    return failures


def load_native_cases() -> list[dict[str, str]]:
    raise RuntimeError(
        "no safe native/provisional route is exposed for identifier-only topology normalization"
    )


def strict_mode_enabled() -> bool:
    return STRICT_PARITY_ENV in os.environ and os.environ[STRICT_PARITY_ENV] != "0"


def run(strict: bool | None = None) -> ParityResult:
    active_strict = strict_mode_enabled() if strict is None else strict
    oracle_cases = python_oracle_cases()
    oracle_failures = [
        (
            "fixture mismatch for "
            f"{case.name}: input {case.input!r}, expected Python canonical identifier {case.expected}, actual Python canonical identifier {case.actual}"
        )
        for case in oracle_cases
        if case.actual != case.expected
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
        print("Topology identifier normalization parity failed:")
        for failure in result.failures:
            print(f"- {failure}")
        return 1

    status = "strict" if strict_mode_enabled() else "advisory"
    print("Topology identifier normalization parity:")
    print("- slice: topology_identifier_normalization")
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
    print(f"- mode: {status}")
    for case in python_oracle_cases():
        print(f"- {case.name}: {case.actual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
