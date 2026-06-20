from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
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
    result = subprocess.run(
        command or PILOT_COMMAND,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
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


def run() -> list[str]:
    return compare_cases(load_native_cases())


def main() -> int:
    failures = run()
    if failures:
        print("First subsystem parity pilot failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("First subsystem parity pilot passed.")
    for case in python_oracle_cases():
        print(f"- {case.input!r}: {case.python_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
