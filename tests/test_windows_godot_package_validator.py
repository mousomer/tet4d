from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "packaging/godot/validate_windows_package.py"
RELEASE_CANDIDATE_ROOT = ROOT / "release-candidates/windows"


def _module():
    spec = importlib.util.spec_from_file_location("windows_package_validator", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _archive(
    tmp_path: Path,
    *,
    omit: str = "",
    marker: bytes = b"",
    marker_member: str = "Tet4D Designer/Tet4DDesigner.exe",
) -> Path:
    validator = _module()
    archive_path = tmp_path / "Tet4D-Designer-0.7.5-windows-x86_64.zip"
    pck = b"\n".join(validator.PCK_RESOURCES)
    files = {
        "Tet4D Designer/Tet4DDesigner.exe": b"MZstandalone",
        "Tet4D Designer/Tet4DDesigner.pck": pck,
        "Tet4D Designer/libtet4d_core.windows.template_release.x86_64.dll": b"MZnative",
    }
    files[marker_member] += marker
    with zipfile.ZipFile(archive_path, "w") as archive:
        for name, payload in files.items():
            if name != omit:
                archive.writestr(name, payload)
    return archive_path


def test_current_windows_portable_inventory_validates(tmp_path: Path) -> None:
    validator = _module()
    result = validator.validate(_archive(tmp_path), ROOT)
    assert result["version"] == "0.7.5"
    assert result["file_count"] == 3
    assert result["python_runtime_included"] is False
    assert result["godot_editor_required"] is False


def test_windows_release_candidate_directory_contains_no_archives() -> None:
    assert (RELEASE_CANDIDATE_ROOT / "README.md").is_file()
    assert list(RELEASE_CANDIDATE_ROOT.rglob("*.zip")) == []


@pytest.mark.parametrize(
    ("omit", "marker"),
    [
        ("Tet4D Designer/Tet4DDesigner.pck", b""),
        ("", b"/" + b"Users/developer/source"),
    ],
)
def test_incomplete_or_host_bound_package_is_rejected(
    tmp_path: Path,
    omit: str,
    marker: bytes,
) -> None:
    validator = _module()
    with pytest.raises(ValueError):
        validator.validate(_archive(tmp_path, omit=omit, marker=marker), ROOT)


def test_development_only_inventory_is_rejected(tmp_path: Path) -> None:
    validator = _module()
    archive_path = _archive(tmp_path)
    with zipfile.ZipFile(archive_path, "a") as archive:
        archive.writestr("Tet4D Designer/tests/probe.py", "raise SystemExit")
    with pytest.raises(ValueError):
        validator.validate(archive_path, ROOT)


def test_host_path_failure_names_the_offending_archive_member(tmp_path: Path) -> None:
    validator = _module()
    member = "Tet4D Designer/libtet4d_core.windows.template_release.x86_64.dll"
    archive_path = _archive(
        tmp_path,
        marker=b"\\a\\tet4d\\tet4d",
        marker_member=member,
    )

    with pytest.raises(ValueError, match=rf"{member}.*absolute path marker"):
        validator.validate(archive_path, ROOT)
