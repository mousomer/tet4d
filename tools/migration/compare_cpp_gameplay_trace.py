from __future__ import annotations

import argparse
import difflib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.migration.trace_schema import canonical_json

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLDEN_DIR = ROOT / "migration" / "golden_traces" / "gameplay"
SUPPORTED_CASE = "gameplay_plain_2d_short"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _cpp_trace() -> dict[str, Any]:
    command = [
        str(ROOT / "scripts" / "test_godot_tet4d_core.sh"),
        "--export-plain-2d-trace",
    ]
    result = subprocess.run(
        command,
        check=True,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def _contract_projection(trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": trace["case_id"],
        "commands": trace["commands"],
        "dimension": trace["dimension"],
        "final": trace["final"],
        "frames": trace["frames"],
        "generator": trace["generator"],
        "initial": trace["initial"],
        "seed": trace["seed"],
        "topology_id": trace["topology_id"],
        "trace_type": trace["trace_type"],
        "trace_version": trace["trace_version"],
    }


def _field_diffs(expected: Any, actual: Any, path: str = "$") -> list[str]:
    if type(expected) is not type(actual):
        return [
            f"{path}: type mismatch expected {type(expected).__name__}, got {type(actual).__name__}"
        ]
    if isinstance(expected, dict):
        diffs: list[str] = []
        expected_keys = set(expected)
        actual_keys = set(actual)
        for key in sorted(expected_keys - actual_keys):
            diffs.append(f"{path}.{key}: missing from C++ trace")
        for key in sorted(actual_keys - expected_keys):
            diffs.append(f"{path}.{key}: unexpected in C++ trace")
        for key in sorted(expected_keys & actual_keys):
            diffs.extend(_field_diffs(expected[key], actual[key], f"{path}.{key}"))
        return diffs
    if isinstance(expected, list):
        diffs = []
        if len(expected) != len(actual):
            diffs.append(
                f"{path}: length mismatch expected {len(expected)}, got {len(actual)}"
            )
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual)):
            diffs.extend(_field_diffs(expected_item, actual_item, f"{path}[{index}]"))
        return diffs
    if expected != actual:
        return [f"{path}: expected {expected!r}, got {actual!r}"]
    return []


def _canonical_diff(expected: Any, actual: Any) -> str:
    return "".join(
        difflib.unified_diff(
            canonical_json(expected).splitlines(keepends=True),
            canonical_json(actual).splitlines(keepends=True),
            fromfile="python-golden",
            tofile="cpp-native",
        )
    )


def compare_case(case_id: str, golden_dir: Path) -> list[str]:
    if case_id != SUPPORTED_CASE:
        return [f"unsupported C++ gameplay parity case: {case_id}"]
    golden = _load_json(golden_dir / f"{case_id}.json")
    cpp = _cpp_trace()
    golden_contract = _contract_projection(golden)
    cpp_contract = _contract_projection(cpp)
    if cpp_contract != golden_contract:
        return [
            *_field_diffs(golden_contract, cpp_contract)[0:40],
            "C++ gameplay trace contract mismatch for gameplay_plain_2d_short",
            _canonical_diff(golden_contract, cpp_contract),
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare native C++ gameplay trace output with Python golden traces."
    )
    parser.add_argument("--case", required=True)
    parser.add_argument("--golden-dir", type=Path, default=DEFAULT_GOLDEN_DIR)
    args = parser.parse_args(argv)

    failures = compare_case(args.case, args.golden_dir)
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print(f"C++ gameplay parity passed for {args.case} (including state_hash)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
