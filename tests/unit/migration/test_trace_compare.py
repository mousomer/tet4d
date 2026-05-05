from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.migration.export_endgame_trace import export_cases as export_endgame_cases
from tools.migration.export_gameplay_trace import export_cases as export_gameplay_cases
from tools.migration.export_topology_trace import export_cases as export_topology_cases
from tools.migration.trace_cases import (
    ENDGAME_TRACE_CASES,
    GAMEPLAY_TRACE_CASES,
    TOPOLOGY_TRACE_CASES,
)


def _write_temp_golden(root: Path) -> None:
    export_topology_cases(list(TOPOLOGY_TRACE_CASES), root / "topology")
    export_gameplay_cases(list(GAMEPLAY_TRACE_CASES), root / "gameplay")
    export_endgame_cases(list(ENDGAME_TRACE_CASES), root / "endgame")


def test_compare_trace_passes_when_traces_match(tmp_path: Path) -> None:
    _write_temp_golden(tmp_path)

    result = subprocess.run(
        [sys.executable, "tools/migration/compare_trace.py", str(tmp_path)],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "trace comparison passed" in result.stdout


def test_compare_trace_fails_when_trace_differs(tmp_path: Path) -> None:
    _write_temp_golden(tmp_path)
    drifted = tmp_path / "gameplay" / "gameplay_plain_2d_short.json"
    payload = json.loads(drifted.read_text(encoding="utf-8"))
    payload["final"]["score"] = 999
    drifted.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    result = subprocess.run(
        [sys.executable, "tools/migration/compare_trace.py", str(tmp_path)],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "gameplay_plain_2d_short.json" in result.stdout
    assert '-    "score": 999' in result.stdout


def test_compare_trace_accepts_single_topology_directory(tmp_path: Path) -> None:
    _write_temp_golden(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "tools/migration/compare_trace.py",
            str(tmp_path / "topology"),
        ],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_compare_trace_accepts_single_endgame_directory(tmp_path: Path) -> None:
    _write_temp_golden(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "tools/migration/compare_trace.py",
            str(tmp_path / "endgame"),
        ],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
