from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

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


def _without_state_hash(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_state_hash(item)
            for key, item in value.items()
            if key != "state_hash"
        }
    if isinstance(value, list):
        return [_without_state_hash(item) for item in value]
    return value


def _contract_projection(trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": trace["case_id"],
        "commands": trace["commands"],
        "dimension": trace["dimension"],
        "final": _without_state_hash(trace["final"]),
        "frames": [_without_state_hash(frame) for frame in trace["frames"]],
        "initial": trace["initial"],
        "seed": trace["seed"],
        "topology_id": trace["topology_id"],
        "trace_type": trace["trace_type"],
        "trace_version": trace["trace_version"],
    }


def compare_case(case_id: str, golden_dir: Path) -> list[str]:
    if case_id != SUPPORTED_CASE:
        return [f"unsupported C++ gameplay parity case: {case_id}"]
    golden = _load_json(golden_dir / f"{case_id}.json")
    cpp = _cpp_trace()
    golden_contract = _contract_projection(golden)
    cpp_contract = _contract_projection(cpp)
    if cpp_contract != golden_contract:
        return [
            "C++ gameplay trace contract mismatch for gameplay_plain_2d_short",
            "state_hash is intentionally excluded; all other projected fields must match",
            json.dumps(
                {"expected": golden_contract, "actual": cpp_contract},
                indent=2,
                sort_keys=True,
            ),
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
    print(f"C++ gameplay parity passed for {args.case} (state_hash deferred)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
