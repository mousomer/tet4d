from __future__ import annotations

import json
import importlib
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRICT_PARITY_ENV = "TET4D_STRICT_PARITY"
FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "parity" / "trace_metadata_identity_digest.json"
)
NATIVE_COMMAND = [
    str(ROOT / "scripts" / "test_godot_tet4d_core.sh"),
    "--trace-metadata-identity-digest",
]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

trace_schema = importlib.import_module("tools.migration.trace_schema")


@dataclass(frozen=True)
class MetadataCase:
    name: str
    payload: dict[str, object]
    identity: str
    digest: str


@dataclass(frozen=True)
class ParityResult:
    failures: list[str]
    advisories: list[str]


def load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def python_oracle_cases() -> list[MetadataCase]:
    fixture = load_fixture()
    cases = fixture.get("cases")
    if not isinstance(cases, list):
        raise RuntimeError("trace metadata parity fixture must contain a cases array")

    oracle_cases: list[MetadataCase] = []
    for item in cases:
        if not isinstance(item, dict):
            raise RuntimeError("trace metadata parity cases must be objects")
        name = item.get("name")
        if not isinstance(name, str):
            raise RuntimeError("trace metadata parity case missing name")
        payload = {
            "dimension": item.get("dimension"),
            "mode": item.get("mode"),
            "schema_version": item.get("schema_version"),
            "topology": item.get("topology"),
            "trace_id": item.get("trace_id"),
        }
        if not isinstance(payload["dimension"], int):
            raise RuntimeError(
                f"trace metadata parity case {name!r} missing integer dimension"
            )
        if not isinstance(payload["mode"], str):
            raise RuntimeError(f"trace metadata parity case {name!r} missing mode")
        if not isinstance(payload["schema_version"], int):
            raise RuntimeError(
                f"trace metadata parity case {name!r} missing integer schema_version"
            )
        if not isinstance(payload["topology"], str):
            raise RuntimeError(f"trace metadata parity case {name!r} missing topology")
        if not isinstance(payload["trace_id"], str):
            raise RuntimeError(f"trace metadata parity case {name!r} missing trace_id")
        identity = trace_schema.compact_canonical_json(payload)
        digest = trace_schema.stable_hash(payload)
        oracle_cases.append(
            MetadataCase(name=name, payload=payload, identity=identity, digest=digest)
        )
    return oracle_cases


def load_native_cases(command: list[str] | None = None) -> list[dict[str, str]]:
    try:
        result = subprocess.run(
            command or NATIVE_COMMAND,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise RuntimeError(f"unable to start native parity command: {exc}") from exc
    if result.returncode != 0:
        raise RuntimeError(
            "native parity command failed.\n"
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    payload = json.loads(result.stdout)
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise RuntimeError("native parity output is missing a cases array")
    normalized: list[dict[str, str]] = []
    for item in cases:
        if not isinstance(item, dict):
            raise RuntimeError("native parity cases must be objects")
        name = item.get("name")
        identity = item.get("identity")
        digest = item.get("digest")
        if (
            not isinstance(name, str)
            or not isinstance(identity, str)
            or not isinstance(digest, str)
        ):
            raise RuntimeError(
                "native parity cases must include name, identity, and digest"
            )
        normalized.append({"name": name, "identity": identity, "digest": digest})
    return normalized


def compare_cases(
    native_cases: list[dict[str, str]],
    oracle_cases: list[MetadataCase] | None = None,
) -> list[str]:
    oracle_index = {
        case.name: {"identity": case.identity, "digest": case.digest}
        for case in (oracle_cases or python_oracle_cases())
    }
    failures: list[str] = []
    native_names = {case["name"] for case in native_cases}
    oracle_names = set(oracle_index)

    for missing in sorted(oracle_names - native_names):
        failures.append(f"missing native parity case: {missing}")
    for extra in sorted(native_names - oracle_names):
        failures.append(f"unexpected native parity case: {extra}")
    for case in native_cases:
        expected = oracle_index.get(case["name"])
        if expected is None:
            continue
        if case["identity"] != expected["identity"]:
            failures.append(
                f"identity mismatch for {case['name']}: expected {expected['identity']}, got {case['identity']}"
            )
        if case["digest"] != expected["digest"]:
            failures.append(
                f"digest mismatch for {case['name']}: expected {expected['digest']}, got {case['digest']}"
            )
    return failures


def strict_mode_enabled() -> bool:
    return STRICT_PARITY_ENV in os.environ and os.environ[STRICT_PARITY_ENV] != "0"


def run(strict: bool | None = None) -> ParityResult:
    active_strict = strict_mode_enabled() if strict is None else strict
    try:
        native_cases = load_native_cases()
    except RuntimeError as exc:
        message = (
            "native parity unavailable: "
            f"{exc} "
            f"(rerun after native toolchain setup or set {STRICT_PARITY_ENV}=1 to make unavailability blocking)"
        )
        if active_strict:
            return ParityResult(failures=[message], advisories=[])
        return ParityResult(failures=[], advisories=[message])

    return ParityResult(failures=compare_cases(native_cases), advisories=[])


def main() -> int:
    result = run()
    if result.failures:
        print("Trace metadata identity/digest parity failed:")
        for failure in result.failures:
            print(f"- {failure}")
        return 1
    if result.advisories:
        print("Trace metadata identity/digest parity advisory:")
        for advisory in result.advisories:
            print(f"- {advisory}")
        return 0

    print("Trace metadata identity/digest parity passed.")
    for case in python_oracle_cases():
        print(f"- {case.name}: {case.digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
