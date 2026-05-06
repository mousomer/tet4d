from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.migration.export_config_bundle import export_bundle
from tools.migration.sync_unity_bundle import sync_bundle


def test_sync_unity_bundle_copies_bundle_and_check_passes(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundle"
    unity_root = tmp_path / "unity" / "Assets" / "StreamingAssets" / "tet4d_bundle"
    export_bundle(bundle_root)

    sync_bundle(bundle_root, unity_root)

    result = subprocess.run(
        [
            sys.executable,
            "tools/migration/sync_unity_bundle.py",
            "--bundle",
            str(bundle_root),
            "--unity-assets",
            str(unity_root),
            "--check",
        ],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "unity bundle sync check passed" in result.stdout


def test_sync_unity_bundle_check_fails_on_intentional_drift(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundle"
    unity_root = tmp_path / "unity" / "Assets" / "StreamingAssets" / "tet4d_bundle"
    export_bundle(bundle_root)
    sync_bundle(bundle_root, unity_root)

    drifted = unity_root / "manifest.json"
    drifted.write_text('{"bundle_type":"drift"}\n', encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "tools/migration/sync_unity_bundle.py",
            "--bundle",
            str(bundle_root),
            "--unity-assets",
            str(unity_root),
            "--check",
        ],
        check=False,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "drifted unity bundle file" in result.stdout
    assert "manifest.json" in result.stdout


def test_sync_unity_bundle_removes_stale_files(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundle"
    unity_root = tmp_path / "unity" / "Assets" / "StreamingAssets" / "tet4d_bundle"
    export_bundle(bundle_root)
    sync_bundle(bundle_root, unity_root)

    stale = unity_root / "stale.txt"
    stale.write_text("obsolete\n", encoding="utf-8")
    assert stale.exists()

    sync_bundle(bundle_root, unity_root)

    assert not stale.exists()


def test_sync_unity_bundle_copy_contains_no_absolute_paths(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundle"
    unity_root = tmp_path / "unity" / "Assets" / "StreamingAssets" / "tet4d_bundle"
    export_bundle(bundle_root)
    sync_bundle(bundle_root, unity_root)

    forbidden_markers = ("/" + "Users" + "/", "\\" + "Users" + "\\")
    for path in unity_root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert all(marker not in text for marker in forbidden_markers), path
