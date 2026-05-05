from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.migration.export_gameplay_trace import build_gameplay_trace
from tools.migration.trace_cases import GAMEPLAY_CASES_BY_ID, GAMEPLAY_TRACE_CASES
from tools.migration.trace_schema import assert_trace_hygiene, stable_hash


def test_gameplay_trace_export_is_deterministic() -> None:
    case = GAMEPLAY_CASES_BY_ID["gameplay_launch_topology_parity"]

    first = build_gameplay_trace(case)
    second = build_gameplay_trace(case)

    assert first == second
    assert first["trace_version"] == 1
    assert first["case_id"] == "gameplay_launch_topology_parity"
    assert stable_hash(first) == stable_hash(second)
    assert_trace_hygiene(first)


def test_gameplay_trace_records_y_axis_drop_policy() -> None:
    trace = build_gameplay_trace(GAMEPLAY_CASES_BY_ID["gameplay_y_axis_drop_policy"])

    translation, soft_drop, gravity = trace["frames"]

    assert translation["command_result"]["return_value"] is True
    assert translation["topology_event"]["crosses_gravity_seam"] is True
    assert soft_drop["command_result"]["return_value"] is False
    assert soft_drop["topology_event"]["intent"] == "soft_drop"
    assert gravity["command_result"]["locked_cell_delta"] == 1
    assert trace["final"]["locked_cell_count"] == 1


def test_gameplay_trace_records_launch_topology_parity() -> None:
    trace = build_gameplay_trace(
        GAMEPLAY_CASES_BY_ID["gameplay_launch_topology_parity"]
    )
    parity = trace["initial"]["launch_parity"]

    assert parity["profile_digest_equal"] is True
    assert parity["first_transport_equal"] is True
    assert parity["configured_transport_dims"] == [4, 4, 4, 4]
    assert (
        trace["frames"][0]["topology_event"]["traversals"][0]["source_boundary"] == "y+"
    )


def test_gameplay_cli_case_exports_only_requested_case(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/migration/export_gameplay_trace.py",
            "--case",
            "gameplay_plain_4d_short",
            "--out",
            str(tmp_path),
        ],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert sorted(path.name for path in tmp_path.glob("*.json")) == [
        "gameplay_plain_4d_short.json"
    ]


def test_gameplay_cli_all_exports_expected_cases(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/migration/export_gameplay_trace.py",
            "--all",
            "--out",
            str(tmp_path),
            "--quiet",
        ],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert sorted(path.stem for path in tmp_path.glob("*.json")) == sorted(
        case.case_id for case in GAMEPLAY_TRACE_CASES
    )
