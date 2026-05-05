from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.migration.export_config_bundle import (
    build_trace_index,
    export_bundle,
    file_sha256,
)


def _bundle_file_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_config_bundle_export_writes_expected_files(tmp_path: Path) -> None:
    written = export_bundle(tmp_path)

    assert tmp_path / "manifest.json" in written
    assert tmp_path / "config" / "tet4d_config_bundle.json" in written
    assert tmp_path / "docs" / "authority_index.json" in written
    assert tmp_path / "schemas" / "schema_index.json" in written
    assert tmp_path / "README.md" in written
    for trace_type in ("topology", "gameplay", "endgame"):
        assert any((tmp_path / "traces" / trace_type).glob("*.json"))


def test_config_bundle_repeated_export_is_byte_identical(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    export_bundle(first)
    export_bundle(second)

    assert _bundle_file_bytes(first) == _bundle_file_bytes(second)


def test_config_bundle_cli_check_passes_for_matching_bundle(tmp_path: Path) -> None:
    export_bundle(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "tools/migration/export_config_bundle.py",
            "--out",
            str(tmp_path),
            "--check",
        ],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "config bundle comparison passed" in result.stdout


def test_config_bundle_source_config_is_not_mutated(tmp_path: Path) -> None:
    source_paths = [
        Path("config/project/constants.json"),
        Path("config/menu/structure.json"),
        Path("config/menu/defaults.json"),
        Path("config/project/policy_pack.json"),
    ]
    before = {path.as_posix(): file_sha256(path) for path in source_paths}

    export_bundle(tmp_path)

    after = {path.as_posix(): file_sha256(path) for path in source_paths}
    assert after == before


def test_config_bundle_trace_index_matches_golden_trace_counts() -> None:
    trace_index = build_trace_index()

    assert {
        trace_type: len(entries) for trace_type, entries in trace_index.items()
    } == {
        "topology": len(tuple(Path("migration/golden_traces/topology").glob("*.json"))),
        "gameplay": len(tuple(Path("migration/golden_traces/gameplay").glob("*.json"))),
        "endgame": len(tuple(Path("migration/golden_traces/endgame").glob("*.json"))),
    }
    assert all(trace_index[trace_type] for trace_type in trace_index)
