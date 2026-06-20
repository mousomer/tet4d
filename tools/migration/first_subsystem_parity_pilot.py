from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRICT_PARITY_ENV = "TET4D_STRICT_PARITY"
PILOT_COMMAND = [
    str(ROOT / "scripts" / "test_godot_tet4d_core.sh"),
    "--pilot-stable-hash",
]
PILOT_CASES = (
    "",
    "tet4d",
    "oracle-check",
    "hash-bridge",
)
FNV_OFFSET_BASIS = 14695981039346656037
FNV_PRIME = 1099511628211


@dataclass(frozen=True)
class PilotCase:
    input: str
    python_hash: str


@dataclass(frozen=True)
class PilotRunResult:
    failures: list[str]
    advisories: list[str]


def python_oracle_stable_hash_text(text: str) -> str:
    value = FNV_OFFSET_BASIS
    for byte in text.encode("utf-8"):
        value ^= byte
        value = (value * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"


def python_oracle_cases() -> list[PilotCase]:
    return [
        PilotCase(input=text, python_hash=python_oracle_stable_hash_text(text))
        for text in PILOT_CASES
    ]


def load_native_cases(
    command: list[str] | None = None,
) -> list[dict[str, str]]:
    try:
        result = subprocess.run(
            command or PILOT_COMMAND,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise RuntimeError(
            f"unable to start native parity pilot command: {exc}"
        ) from exc
    if result.returncode != 0:
        raise RuntimeError(
            "native parity pilot command failed.\n"
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    payload = json.loads(result.stdout)
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise RuntimeError("native parity pilot output is missing a cases array")
    normalized: list[dict[str, str]] = []
    for item in cases:
        if not isinstance(item, dict):
            raise RuntimeError("native parity pilot cases must be objects")
        input_text = item.get("input")
        native_hash = item.get("native_hash")
        if not isinstance(input_text, str) or not isinstance(native_hash, str):
            raise RuntimeError(
                "native parity pilot cases must include input and native_hash"
            )
        normalized.append({"input": input_text, "native_hash": native_hash})
    return normalized


def compare_cases(
    native_cases: list[dict[str, str]],
    oracle_cases: list[PilotCase] | None = None,
) -> list[str]:
    oracle_index = {
        case.input: case.python_hash for case in (oracle_cases or python_oracle_cases())
    }
    failures: list[str] = []
    native_inputs = {case["input"] for case in native_cases}
    oracle_inputs = set(oracle_index)

    for missing in sorted(oracle_inputs - native_inputs):
        failures.append(f"missing native pilot case: {missing!r}")
    for extra in sorted(native_inputs - oracle_inputs):
        failures.append(f"unexpected native pilot case: {extra!r}")
    for case in native_cases:
        expected = oracle_index.get(case["input"])
        if expected is None:
            continue
        if case["native_hash"] != expected:
            failures.append(
                "hash mismatch for "
                f"{case['input']!r}: expected {expected}, got {case['native_hash']}"
            )
    return failures


def strict_mode_enabled() -> bool:
    return STRICT_PARITY_ENV in os.environ and os.environ[STRICT_PARITY_ENV] != "0"


def run(strict: bool | None = None) -> PilotRunResult:
    active_strict = strict_mode_enabled() if strict is None else strict
    try:
        native_cases = load_native_cases()
    except RuntimeError as exc:
        message = (
            "native parity pilot unavailable: "
            f"{exc} "
            f"(rerun after native toolchain setup or set {STRICT_PARITY_ENV}=1 "
            "to make unavailability blocking)"
        )
        if active_strict:
            return PilotRunResult(failures=[message], advisories=[])
        return PilotRunResult(failures=[], advisories=[message])

    return PilotRunResult(failures=compare_cases(native_cases), advisories=[])


def main() -> int:
    result = run()
    if result.failures:
        print("First subsystem parity pilot failed:")
        for failure in result.failures:
            print(f"- {failure}")
        return 1
    if result.advisories:
        print("First subsystem parity pilot advisory:")
        for advisory in result.advisories:
            print(f"- {advisory}")
        return 0

    print("First subsystem parity pilot passed.")
    for case in python_oracle_cases():
        print(f"- {case.input!r}: {case.python_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
