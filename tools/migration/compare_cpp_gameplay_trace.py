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
from tools.migration.trace_cases import GAMEPLAY_TRACE_CASES

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLDEN_DIR = ROOT / "migration" / "golden_traces" / "gameplay"
PLAIN_2D_CASES = {
    "gameplay_plain_2d_short",
    "gameplay_plain_2d_rotation_short",
    "gameplay_plain_2d_hard_drop_lock",
    "gameplay_plain_2d_line_clear_short",
}
PLAIN_ND_CASES = {
    "gameplay_plain_3d_short",
    "gameplay_plain_4d_short",
}
SUPPORTED_CASES = PLAIN_2D_CASES | PLAIN_ND_CASES


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _cpp_trace(case_id: str) -> dict[str, Any]:
    export_flag = (
        "--export-plain-nd-trace"
        if case_id in PLAIN_ND_CASES
        else "--export-plain-2d-trace"
    )
    command = [
        str(ROOT / "scripts" / "test_godot_tet4d_core.sh"),
        export_flag,
        case_id,
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


def _first_frame_mismatch(diffs: list[str]) -> str | None:
    for diff in diffs:
        marker = "$.frames["
        if not diff.startswith(marker):
            continue
        end = diff.find("]", len(marker))
        if end < 0:
            continue
        frame_index = diff[len(marker) : end]
        field_path = "$.frames[" + frame_index + "]" + diff[end + 1 :].split(": ", 1)[0]
        return f"first mismatching frame: {frame_index}; field path: {field_path}"
    return None


def compare_case(case_id: str, golden_dir: Path) -> list[str]:
    if case_id not in SUPPORTED_CASES:
        return [f"unsupported C++ gameplay parity case: {case_id}"]
    golden = _load_json(golden_dir / f"{case_id}.json")
    cpp = _cpp_trace(case_id)
    golden_contract = _contract_projection(golden)
    cpp_contract = _contract_projection(cpp)
    if cpp_contract != golden_contract:
        diffs = _field_diffs(golden_contract, cpp_contract)
        frame_mismatch = _first_frame_mismatch(diffs)
        hash_diffs = [
            diff
            for diff in diffs
            if "state_hash" in diff or "locked_cell_digest" in diff
        ]
        summary = []
        if frame_mismatch is not None:
            summary.append(frame_mismatch)
        summary.extend(hash_diffs[:10])
        return [
            *diffs[0:40],
            *summary,
            f"C++ gameplay trace contract mismatch for {case_id}",
            _canonical_diff(golden_contract, cpp_contract),
        ]
    return []


def plain_2d_cases() -> list[str]:
    return [
        case.case_id for case in GAMEPLAY_TRACE_CASES if case.case_id in PLAIN_2D_CASES
    ]


def plain_nd_cases() -> list[str]:
    return [
        case.case_id for case in GAMEPLAY_TRACE_CASES if case.case_id in PLAIN_ND_CASES
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare native C++ gameplay trace output with Python golden traces."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--case")
    group.add_argument(
        "--all-plain-2d",
        action="store_true",
        help="compare every Stage 11 plain 2D C++ parity case",
    )
    group.add_argument(
        "--all-plain-nd",
        action="store_true",
        help="compare every Stage 15 plain bounded 3D/4D C++ parity case",
    )
    parser.add_argument("--golden-dir", type=Path, default=DEFAULT_GOLDEN_DIR)
    args = parser.parse_args(argv)

    if args.all_plain_2d:
        case_ids = plain_2d_cases()
    elif args.all_plain_nd:
        case_ids = plain_nd_cases()
    else:
        case_ids = [args.case]
    failures: list[str] = []
    for case_id in case_ids:
        failures.extend(compare_case(case_id, args.golden_dir))
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print(
        "C++ gameplay parity passed for "
        + ", ".join(case_ids)
        + " (including state_hash)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
