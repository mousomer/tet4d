from __future__ import annotations

import hashlib
import importlib.util
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "packaging/godot/validate_windows_package.py"
TRACKED_CANDIDATE = (
    ROOT
    / "release-candidates/windows/Tet4D-Designer-0.7.5-windows-x86_64.zip"
)
TRACKED_CANDIDATE_SHA256 = (
    "04941cb3f6d1070521f7a4d2d306fee5478908e3cf5e51d782c96a7e973913b9"
)


def _module():
    spec = importlib.util.spec_from_file_location("windows_package_validator", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _archive(tmp_path: Path, *, omit: str = "", marker: bytes = b"") -> Path:
    validator = _module()
    archive_path = tmp_path / "Tet4D-Designer-0.7.5-windows-x86_64.zip"
    pck = b"\n".join(validator.PCK_RESOURCES)
    files = {
        "Tet4D Designer/Tet4DDesigner.exe": b"MZ" + marker + b"standalone",
        "Tet4D Designer/Tet4DDesigner.pck": pck,
        "Tet4D Designer/libtet4d_core.windows.template_release.x86_64.dll": b"MZnative",
    }
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


def test_tracked_windows_candidate_is_exact_and_valid() -> None:
    validator = _module()
    assert hashlib.sha256(TRACKED_CANDIDATE.read_bytes()).hexdigest() == (
        TRACKED_CANDIDATE_SHA256
    )
    result = validator.validate(TRACKED_CANDIDATE, ROOT)
    assert result["version"] == "0.7.5"
    assert result["file_count"] == 3


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
