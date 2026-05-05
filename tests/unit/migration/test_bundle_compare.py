from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.migration.export_config_bundle import export_bundle


def test_export_config_bundle_check_fails_on_manifest_drift(tmp_path: Path) -> None:
    export_bundle(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["bundle_version"] = 999
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

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

    assert result.returncode == 1
    assert "manifest.json" in result.stdout
    assert '-  "bundle_version": 999' in result.stdout


def test_compare_config_bundle_tool_fails_on_missing_file(tmp_path: Path) -> None:
    export_bundle(tmp_path)
    (tmp_path / "README.md").unlink()

    result = subprocess.run(
        [
            sys.executable,
            "tools/migration/compare_config_bundle.py",
            str(tmp_path),
        ],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "missing checked-in bundle file" in result.stdout
    assert "README.md" in result.stdout


def test_compare_config_bundle_tool_passes_for_matching_bundle(tmp_path: Path) -> None:
    export_bundle(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "tools/migration/compare_config_bundle.py",
            str(tmp_path),
        ],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "config bundle comparison passed" in result.stdout
