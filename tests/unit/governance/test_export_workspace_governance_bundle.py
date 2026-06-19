from __future__ import annotations

from pathlib import Path

import tools.governance.export_workspace_governance_bundle as exporter


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_source_bundle(root: Path) -> Path:
    bundle = root / "bundle"
    _write(bundle / "README.md", "readme\n")
    _write(bundle / "nested" / "policy.md", "policy\n")
    return bundle


def test_export_helper_dry_run_does_not_write_files(
    tmp_path: Path, monkeypatch
) -> None:
    source = _make_source_bundle(tmp_path)
    target = tmp_path / "target"
    monkeypatch.setattr(exporter, "BUNDLE_ROOT", source)

    result = exporter.main(["--dry-run", "--target", str(target)])

    assert result == 0
    assert not target.exists()


def test_export_helper_refuses_overwrite_without_force(
    tmp_path: Path, monkeypatch
) -> None:
    source = _make_source_bundle(tmp_path)
    target = tmp_path / "target"
    _write(target / "README.md", "existing\n")
    monkeypatch.setattr(exporter, "BUNDLE_ROOT", source)

    result = exporter.main(["--target", str(target)])

    assert result == 1
    assert (target / "README.md").read_text(encoding="utf-8") == "existing\n"


def test_export_helper_copies_all_bundle_files_with_force(
    tmp_path: Path, monkeypatch
) -> None:
    source = _make_source_bundle(tmp_path)
    target = tmp_path / "target"
    _write(target / "README.md", "existing\n")
    monkeypatch.setattr(exporter, "BUNDLE_ROOT", source)

    result = exporter.main(["--force", "--target", str(target)])

    assert result == 0
    assert (target / "README.md").read_text(encoding="utf-8") == "readme\n"
    assert (target / "nested" / "policy.md").read_text(encoding="utf-8") == "policy\n"
