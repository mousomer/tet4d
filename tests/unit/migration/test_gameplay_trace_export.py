from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.migration.export_gameplay_trace import build_gameplay_trace
from tools.migration.trace_cases import GAMEPLAY_CASES_BY_ID, GAMEPLAY_TRACE_CASES
from tools.migration.trace_schema import assert_trace_hygiene, stable_hash


STAGE17_PLAIN_ND_CASES = {
    "gameplay_plain_3d_rotation_short": 3,
    "gameplay_plain_4d_rotation_short": 4,
    "gameplay_plain_3d_plane_clear_short": 3,
    "gameplay_plain_4d_plane_clear_short": 4,
    "gameplay_plain_3d_spawn_blocked_game_over": 3,
    "gameplay_plain_4d_spawn_blocked_game_over": 4,
}


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


def test_stage17_plain_nd_oracle_cases_are_registered_and_deterministic() -> None:
    registered = {case.case_id for case in GAMEPLAY_TRACE_CASES}

    assert STAGE17_PLAIN_ND_CASES.keys() <= registered
    for case_id, dimension in STAGE17_PLAIN_ND_CASES.items():
        case = GAMEPLAY_CASES_BY_ID[case_id]
        first = build_gameplay_trace(case)
        second = build_gameplay_trace(case)

        assert first == second
        assert first["case_id"] == case_id
        assert first["dimension"] == dimension
        assert first["trace_type"] == "gameplay"
        assert first["topology_id"] == "plain"
        assert first["initial"]["settings"]["topology_mode"] == "bounded"
        assert first["frames"]
        assert first["final"]["state_hash"]
        assert_trace_hygiene(first)
        for frame in first["frames"]:
            assert frame["state_hash"]
            assert frame["topology_event"] is None


def test_stage17_plain_nd_rotation_traces_record_rotation_plane() -> None:
    for case_id, expected_plane in (
        ("gameplay_plain_3d_rotation_short", [0, 2]),
        ("gameplay_plain_4d_rotation_short", [0, 3]),
    ):
        trace = build_gameplay_trace(GAMEPLAY_CASES_BY_ID[case_id])
        frame = trace["frames"][0]

        assert frame["command_result"]["return_value"] is True
        assert frame["active_piece"]["last_rotation_plane"] == expected_plane
        assert frame["active_piece"]["last_rotation_steps"] == 1
        assert frame["locked_cells"] == []


def test_stage17_plain_nd_clear_traces_record_score_and_lines() -> None:
    for case_id in (
        "gameplay_plain_3d_plane_clear_short",
        "gameplay_plain_4d_plane_clear_short",
    ):
        trace = build_gameplay_trace(GAMEPLAY_CASES_BY_ID[case_id])
        frame = trace["frames"][0]

        assert frame["command_result"]["return_value"] == 1
        assert frame["lines"] == 1
        assert frame["score"] == 45
        assert frame["drop_lock_status"]["game_over"] is False
        assert trace["final"]["locked_cell_count"] == 1


def test_stage17_plain_nd_spawn_blocked_traces_record_game_over() -> None:
    for case_id in (
        "gameplay_plain_3d_spawn_blocked_game_over",
        "gameplay_plain_4d_spawn_blocked_game_over",
    ):
        trace = build_gameplay_trace(GAMEPLAY_CASES_BY_ID[case_id])
        frame = trace["frames"][0]

        assert trace["initial"]["active_piece"] is None
        assert frame["active_piece"] is not None
        assert frame["drop_lock_status"]["game_over"] is True
        assert frame["command_result"]["locked_cell_delta"] == 0
        assert trace["final"]["locked_cell_count"] == 1


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
