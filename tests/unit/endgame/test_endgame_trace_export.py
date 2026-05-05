from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.migration.export_endgame_trace import build_endgame_trace, export_cases
from tools.migration.trace_cases import ENDGAME_CASES_BY_ID, ENDGAME_TRACE_CASES
from tools.migration.trace_schema import assert_trace_hygiene, canonical_json, stable_hash


def test_endgame_trace_export_is_deterministic() -> None:
    case = ENDGAME_CASES_BY_ID["endgame_4d_sphere_like"]

    first = build_endgame_trace(case)
    second = build_endgame_trace(case)

    assert first == second
    assert first["trace_type"] == "endgame"
    assert first["trace_version"] == 1
    assert stable_hash(first) == stable_hash(second)
    assert_trace_hygiene(first)


def test_endgame_trace_records_particles_events_energy_and_w_motion() -> None:
    trace = build_endgame_trace(ENDGAME_CASES_BY_ID["endgame_4d_wrap_all"])

    first_frame = trace["frames"][0]
    assert first_frame["events"][0]["source_boundary"] == "w+"
    assert first_frame["particles"][0]["velocity"] == [0.0, 0.0, 0.0, 1.2]
    assert "kinetic_energy" in first_frame["energy"]
    assert len(first_frame["particles"][0]["position"]) == 4


def test_endgame_export_is_byte_identical_when_repeated(tmp_path: Path) -> None:
    export_cases(list(ENDGAME_TRACE_CASES), tmp_path)
    first = {
        path.name: canonical_json(__import__("json").loads(path.read_text(encoding="utf-8")))
        for path in sorted(tmp_path.glob("*.json"))
    }

    export_cases(list(ENDGAME_TRACE_CASES), tmp_path)
    second = {
        path.name: canonical_json(__import__("json").loads(path.read_text(encoding="utf-8")))
        for path in sorted(tmp_path.glob("*.json"))
    }

    assert first == second


def test_endgame_cli_case_exports_only_requested_case(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/migration/export_endgame_trace.py",
            "--case",
            "endgame_4d_wrap_all",
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
        "endgame_4d_wrap_all.json"
    ]
