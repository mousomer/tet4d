from __future__ import annotations

import importlib.util
import struct
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


def _godot_pck(resources: set[str], payload: bytes = b"") -> bytes:
    """A parser-compatible Godot 4 PCK directory fixture, not raw path bytes."""
    header = bytearray(100)
    header[:4] = b"GDPC"
    struct.pack_into("<I", header, 4, 2)
    struct.pack_into("<I", header, 96, len(resources))
    entries = bytearray()
    for resource in sorted(resources):
        path = resource.encode("utf-8")
        entries.extend(struct.pack("<I", len(path)))
        entries.extend(path)
        entries.extend(struct.pack("<QQ", 0, 0))
        entries.extend(b"\0" * 16)
        entries.extend(struct.pack("<I", 0))
    return bytes(header + entries) + payload


def _archive(
    tmp_path: Path,
    *,
    omit: str = "",
    marker: bytes = b"",
    marker_member: str = "Tet4D Designer/Tet4DDesigner.exe",
    resources: set[str] | None = None,
    executable: bytes | None = None,
) -> Path:
    validator = _module()
    archive_path = tmp_path / "Tet4D-Designer-0.9.0-windows-x86_64.zip"
    if resources is None:
        resources = set(validator.REQUIRED_PCK_RESOURCES)
        resources.add(validator.DESIGNER_IDENTITY_MARKER)
    pck = _godot_pck(resources)
    files = {
        "Tet4D Designer/Tet4DDesigner.exe": executable
        if executable is not None
        else b"MZstandalone" + validator.DESIGNER_PRODUCT_NAME,
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
    assert result["version"] == "0.9.0"
    assert result["file_count"] == 3
    assert result["python_runtime_included"] is False
    assert result["godot_editor_required"] is False


def test_structured_pck_without_designer_marker_is_rejected(tmp_path: Path) -> None:
    validator = _module()
    with pytest.raises(ValueError, match="Designer identity marker"):
        validator.validate(
            _archive(tmp_path, resources=set(validator.REQUIRED_PCK_RESOURCES)), ROOT
        )


def test_game_identity_marker_cannot_pass_as_designer(tmp_path: Path) -> None:
    validator = _module()
    resources = set(validator.REQUIRED_PCK_RESOURCES)
    resources.add(validator.GAME_IDENTITY_MARKER)
    with pytest.raises(ValueError, match="Designer identity marker"):
        validator.validate(_archive(tmp_path, resources=resources), ROOT)


def test_source_configuration_text_is_not_exported_identity_evidence(tmp_path: Path) -> None:
    validator = _module()
    with pytest.raises(ValueError, match="Designer identity marker"):
        validator.validate(
            _archive(
                tmp_path,
                resources=set(validator.REQUIRED_PCK_RESOURCES),
                marker=b'config/tet4d_product_id="godot_designer"',
                marker_member="Tet4D Designer/Tet4DDesigner.pck",
            ),
            ROOT,
        )


def test_incorrect_executable_product_metadata_is_rejected(tmp_path: Path) -> None:
    validator = _module()
    archive_path = _archive(tmp_path, executable=b"MZnot-designer")
    with pytest.raises(ValueError, match="Designer product name"):
        validator.validate(archive_path, ROOT)


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
    marker = b"\\a\\tet4d\\tet4d"
    archive_path = _archive(
        tmp_path,
        marker=b"before-context:" + marker + b":after-context",
        marker_member=member,
    )

    with pytest.raises(
        ValueError,
        match=rf"{member}.*absolute path marker.*byte.*before-context.*after-context",
    ):
        validator.validate(archive_path, ROOT)
