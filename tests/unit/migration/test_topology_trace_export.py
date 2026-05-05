from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.migration.export_topology_trace import build_topology_trace
from tools.migration.trace_cases import TOPOLOGY_CASES_BY_ID, TOPOLOGY_TRACE_CASES
from tools.migration.trace_schema import assert_trace_hygiene, stable_hash


def test_topology_trace_export_is_deterministic() -> None:
    case = TOPOLOGY_CASES_BY_ID["topology_sphere_like_4d"]

    first = build_topology_trace(case)
    second = build_topology_trace(case)

    assert first == second
    assert first["trace_version"] == 1
    assert first["case_id"] == "topology_sphere_like_4d"
    assert stable_hash(first) == stable_hash(second)
    assert_trace_hygiene(first)


def test_topology_trace_records_probe_transport_and_play_policy() -> None:
    trace = build_topology_trace(
        TOPOLOGY_CASES_BY_ID["topology_play_vs_sandbox_y_axis"]
    )

    frame = trace["frames"][0]
    policy = trace["initial"]["play_vs_sandbox_policy"]

    assert frame["legal"] is True
    assert frame["probe_result"]["traversal"]["source_boundary"] == "y+"
    assert frame["piece_transport"]["kind"] == "rigid_transform"
    assert policy["sandbox_translation_legal"] is True
    assert policy["play_soft_drop_legal"] is False
    assert policy["drop_intent_crosses_gravity_seam"] is True


def test_topology_playability_diagnostics_repeat_in_trace() -> None:
    trace = build_topology_trace(
        TOPOLOGY_CASES_BY_ID["topology_playability_diagnostics_stable"]
    )

    repeat = trace["initial"]["playability_repeat"]

    assert repeat["stable"] is True
    assert repeat["first_hash"] == repeat["repeat_hash"]
    assert trace["initial"]["diagnostics"]["validity"] == "invalid"


def test_topology_cli_case_exports_only_requested_case(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/migration/export_topology_trace.py",
            "--case",
            "topology_wrap_2d",
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
        "topology_wrap_2d.json"
    ]


def test_topology_cli_all_exports_expected_cases(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/migration/export_topology_trace.py",
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
        case.case_id for case in TOPOLOGY_TRACE_CASES
    )
