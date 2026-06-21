from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRICT_PARITY_ENV = "TET4D_STRICT_PARITY"
FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "parity" / "trace_schema_version_normalization.json"
)

_FORBIDDEN_METADATA_KEYS = {
    "events",
    "frames",
    "board",
    "boards",
    "cells",
    "pieces",
    "position",
    "positions",
    "neighbors",
    "seams",
    "movement",
    "rotation",
    "drop",
    "collision",
    "lock",
    "clear",
    "score",
    "game_loop",
    "renderer",
    "rendering",
    "projection",
    "view",
    "camera",
    "endgame",
}
_TRACE_KIND_ALIASES = {
    "golden": "golden",
    "golden_trace": "golden",
    "migration": "migration",
    "migration_trace": "migration",
    "replay": "replay",
    "trace_replay": "replay",
}
_TRACE_FAMILY_ALIASES = {
    "migration": "migration",
    "godot_native_migration": "migration",
    "trace_replay": "replay",
    "replay": "replay",
    "golden": "golden",
    "golden_trace": "golden",
}
_COMPATIBILITY_ALIASES = {
    "stable": "stable",
    "strict": "strict",
    "legacy_compatible": "legacy_compatible",
    "legacy": "legacy_compatible",
}


@dataclass(frozen=True)
class SchemaVersionCase:
    name: str
    metadata: dict[str, object]
    expected: dict[str, object]
    actual: dict[str, object]


@dataclass(frozen=True)
class ParityResult:
    failures: list[str]
    advisories: list[str]


def _normalize_label(raw: object, *, field: str) -> str:
    if not isinstance(raw, str):
        raise ValueError(f"{field} must be a string")
    cleaned = raw.strip().lower().replace("-", "_")
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        raise ValueError(f"{field} cannot be empty")
    return cleaned


def normalize_schema_version(raw: object) -> int:
    if isinstance(raw, bool):
        raise ValueError("schema_version must be an integer or version string")
    if isinstance(raw, int):
        version = raw
    elif isinstance(raw, str):
        cleaned = raw.strip().lower().replace("_", "-")
        match = re.fullmatch(r"(?:schema-)?v?([0-9]+)", cleaned)
        if match is None:
            raise ValueError(f"unknown schema_version {raw!r}")
        version = int(match.group(1))
    else:
        raise ValueError("schema_version must be an integer or version string")
    if version != 1:
        raise ValueError(f"unknown schema_version {raw!r}; expected version 1")
    return version


def _validate_metadata_only(metadata: dict[str, object]) -> None:
    forbidden = sorted(_FORBIDDEN_METADATA_KEYS.intersection(metadata))
    if forbidden:
        raise ValueError(
            "trace schema/version metadata must not include semantic payload keys: "
            + ", ".join(forbidden)
        )


def normalize_trace_schema_version(metadata: dict[str, object]) -> dict[str, object]:
    if not isinstance(metadata, dict):
        raise TypeError("trace schema/version metadata must be an object")
    _validate_metadata_only(metadata)

    schema_version = normalize_schema_version(metadata.get("schema_version"))
    trace_kind = _TRACE_KIND_ALIASES.get(
        _normalize_label(metadata.get("trace_kind"), field="trace_kind")
    )
    if trace_kind is None:
        raise ValueError(f"unknown trace_kind {metadata.get('trace_kind')!r}")
    trace_family = _TRACE_FAMILY_ALIASES.get(
        _normalize_label(metadata.get("trace_family"), field="trace_family")
    )
    if trace_family is None:
        raise ValueError(f"unknown trace_family {metadata.get('trace_family')!r}")
    compatibility = _COMPATIBILITY_ALIASES.get(
        _normalize_label(metadata.get("compatibility", "stable"), field="compatibility")
    )
    if compatibility is None:
        raise ValueError(f"unknown compatibility {metadata.get('compatibility')!r}")

    schema_id = f"trace_schema_v{schema_version}"
    return {
        "schema_version": schema_version,
        "trace_kind": trace_kind,
        "trace_family": trace_family,
        "compatibility": compatibility,
        "schema_id": schema_id,
        "schema_identity": f"{schema_id}:{trace_kind}:{trace_family}:{compatibility}",
    }


def _load_fixture() -> dict[str, object]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("trace schema/version fixture must be an object")
    if payload.get("slice") != "trace_schema_version_normalization":
        raise RuntimeError("trace schema/version fixture has the wrong slice")
    if payload.get("authority") != "python":
        raise RuntimeError("trace schema/version fixture must declare python authority")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise RuntimeError("trace schema/version fixture must contain a cases array")
    return payload


def python_oracle_cases() -> list[SchemaVersionCase]:
    fixture = _load_fixture()
    cases = fixture["cases"]
    assert isinstance(cases, list)
    normalized: list[SchemaVersionCase] = []
    for item in cases:
        if not isinstance(item, dict):
            raise RuntimeError("trace schema/version cases must be objects")
        name = item.get("name")
        metadata = item.get("metadata")
        expected = item.get("expected")
        if not isinstance(name, str):
            raise RuntimeError("trace schema/version case missing name")
        if not isinstance(metadata, dict):
            raise RuntimeError(f"trace schema/version case {name!r} missing metadata")
        if not isinstance(expected, dict):
            raise RuntimeError(f"trace schema/version case {name!r} missing expected")
        actual = normalize_trace_schema_version(metadata)
        normalized.append(
            SchemaVersionCase(
                name=name,
                metadata=metadata,
                expected=expected,
                actual=actual,
            )
        )
    return normalized


def compare_cases(
    native_cases: list[dict[str, object]],
    oracle_cases: list[SchemaVersionCase] | None = None,
) -> list[str]:
    oracle_index = {
        case.name: {
            "metadata": case.metadata,
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
        normalized = case.get("normalized")
        if not isinstance(name, str) or not isinstance(normalized, dict):
            failures.append("native parity cases must include name and normalized")
            continue
        expected = oracle_index.get(name)
        if expected is None:
            continue
        if normalized != expected["expected"]:
            failures.append(
                "schema/version mismatch for "
                f"{name}: input metadata {expected['metadata']!r}, expected Python normalized schema/version identity {expected['expected']!r}, actual native/provisional schema/version identity {normalized!r}"
            )
    return failures


def load_native_cases() -> list[dict[str, object]]:
    raise RuntimeError(
        "no safe native/provisional route is exposed for trace schema/version normalization"
    )


def strict_mode_enabled() -> bool:
    return STRICT_PARITY_ENV in os.environ and os.environ[STRICT_PARITY_ENV] != "0"


def run(strict: bool | None = None) -> ParityResult:
    active_strict = strict_mode_enabled() if strict is None else strict
    oracle_cases = python_oracle_cases()
    oracle_failures = [
        (
            "fixture mismatch for "
            f"{case.name}: input metadata {case.metadata!r}, expected Python normalized schema/version identity {case.expected!r}, actual Python normalized schema/version identity {case.actual!r}"
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
        print("Trace schema/version normalization parity failed:")
        for failure in result.failures:
            print(f"- {failure}")
        return 1

    print("Trace schema/version normalization parity:")
    print("- slice: trace_schema_version_normalization")
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
    for case in python_oracle_cases():
        print(f"- {case.name}: {case.actual['schema_identity']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
