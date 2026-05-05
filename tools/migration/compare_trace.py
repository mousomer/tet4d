from __future__ import annotations

import argparse
import difflib
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.migration.export_gameplay_trace import export_cases as export_gameplay_cases
from tools.migration.export_endgame_trace import export_cases as export_endgame_cases
from tools.migration.export_topology_trace import export_cases as export_topology_cases
from tools.migration.trace_cases import (
    ENDGAME_TRACE_CASES,
    GAMEPLAY_TRACE_CASES,
    TOPOLOGY_TRACE_CASES,
)
from tools.migration.trace_schema import canonical_json, read_json, trace_file_name


def _trace_targets(path: Path) -> list[tuple[str, Path]]:
    if path.name == "topology":
        return [("topology", path)]
    if path.name == "gameplay":
        return [("gameplay", path)]
    if path.name == "endgame":
        return [("endgame", path)]
    targets: list[tuple[str, Path]] = []
    if (path / "topology").exists():
        targets.append(("topology", path / "topology"))
    if (path / "gameplay").exists():
        targets.append(("gameplay", path / "gameplay"))
    if (path / "endgame").exists():
        targets.append(("endgame", path / "endgame"))
    if targets:
        return targets
    raise SystemExit(f"no topology/gameplay/endgame traces found under {path}")


def _expected_file_names(trace_type: str) -> list[str]:
    if trace_type == "topology":
        return [trace_file_name(case.case_id) for case in TOPOLOGY_TRACE_CASES]
    if trace_type == "gameplay":
        return [trace_file_name(case.case_id) for case in GAMEPLAY_TRACE_CASES]
    if trace_type == "endgame":
        return [trace_file_name(case.case_id) for case in ENDGAME_TRACE_CASES]
    raise ValueError(f"unknown trace type: {trace_type}")


def _regenerate(trace_type: str, out_dir: Path) -> None:
    if trace_type == "topology":
        export_topology_cases(list(TOPOLOGY_TRACE_CASES), out_dir)
        return
    if trace_type == "gameplay":
        export_gameplay_cases(list(GAMEPLAY_TRACE_CASES), out_dir)
        return
    if trace_type == "endgame":
        export_endgame_cases(list(ENDGAME_TRACE_CASES), out_dir)
        return
    raise ValueError(f"unknown trace type: {trace_type}")


def _canonical_file_text(path: Path) -> str:
    return canonical_json(read_json(path))


def compare_trace_path(path: Path) -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="tet4d-trace-compare-") as raw_tmp:
        tmp_root = Path(raw_tmp)
        for trace_type, expected_dir in _trace_targets(path):
            regenerated_dir = tmp_root / trace_type
            _regenerate(trace_type, regenerated_dir)
            for name in _expected_file_names(trace_type):
                expected_file = expected_dir / name
                regenerated_file = regenerated_dir / name
                if not expected_file.exists():
                    failures.append(f"missing checked-in trace: {expected_file}")
                    continue
                expected_text = _canonical_file_text(expected_file)
                regenerated_text = _canonical_file_text(regenerated_file)
                if expected_text == regenerated_text:
                    continue
                diff = "".join(
                    difflib.unified_diff(
                        expected_text.splitlines(keepends=True),
                        regenerated_text.splitlines(keepends=True),
                        fromfile=str(expected_file),
                        tofile=f"regenerated/{trace_type}/{name}",
                    )
                )
                failures.append(diff)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare checked-in golden traces against regenerated runtime traces."
    )
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    failures = compare_trace_path(args.path)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(f"trace comparison passed: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
