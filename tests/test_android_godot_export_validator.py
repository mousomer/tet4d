from __future__ import annotations

import importlib.util
import shutil
import struct
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPORT_VALIDATOR = ROOT / "packaging/godot/validate_android_export.py"
PACKAGE_VALIDATOR = ROOT / "packaging/godot/validate_android_package.py"
PACK_READER = ROOT / "packaging/godot/godot_pack.py"


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pack(paths: list[str]) -> bytes:
    """A minimal Godot pack-format-4 file carrying only a directory."""
    directory = struct.pack("<I", len(paths))
    for path in paths:
        raw = path.encode("utf-8")
        directory += struct.pack("<I", len(raw)) + raw
        directory += struct.pack("<QQ", 0, 0) + b"\x00" * 16 + struct.pack("<I", 0)
    header = struct.pack("<6I", 0x43504447, 4, 4, 7, 2, 2)
    header += struct.pack("<QQ", 112, 112)
    header += b"\x00" * (112 - len(header))
    return header + directory


def _repository(tmp_path: Path) -> Path:
    """A repository copy holding only what the Android validator reads."""
    root = tmp_path / "repo"
    (root / "godot/Tet4D.Godot").mkdir(parents=True)
    shutil.copy(ROOT / "pyproject.toml", root / "pyproject.toml")
    for name in ("project.godot", "export_presets.cfg"):
        shutil.copy(ROOT / "godot/Tet4D.Godot" / name, root / "godot/Tet4D.Godot" / name)
    return root


def test_repository_android_export_configuration_is_valid() -> None:
    module = _module(EXPORT_VALIDATOR, "android_export_validator")
    result = module.validate(ROOT)
    assert result["application_id"] == "io.github.mousomer.tet4d.designer"
    assert result["python_runtime_required"] is False
    assert result["godot_editor_required"] is False


def test_pack_reader_round_trips_a_directory(tmp_path: Path) -> None:
    reader = _module(PACK_READER, "godot_pack_reader")
    pack_path = tmp_path / "sample.pck"
    pack_path.write_bytes(_pack(["config/built_in_style_catalog.json", "scenes/trace_replay.scn"]))
    assert reader.read_pack_paths(pack_path) == [
        "config/built_in_style_catalog.json",
        "scenes/trace_replay.scn",
    ]


def test_pack_must_carry_the_catalogue_and_scenarios(tmp_path: Path) -> None:
    module = _module(EXPORT_VALIDATOR, "android_export_validator")
    pack_path = tmp_path / "incomplete.pck"
    pack_path.write_bytes(_pack(["config/built_in_style_catalog.json"]))
    with pytest.raises(module.AndroidExportError, match="missing required resources"):
        module.validate(ROOT, pack_path)


def test_pack_must_not_carry_development_only_files(tmp_path: Path) -> None:
    module = _module(EXPORT_VALIDATOR, "android_export_validator")
    pack_path = tmp_path / "leaky.pck"
    pack_path.write_bytes(_pack([*module.REQUIRED_PACK_RESOURCES, "tests/run_tests.gd"]))
    with pytest.raises(module.AndroidExportError, match="development-only files"):
        module.validate(ROOT, pack_path)


@pytest.mark.parametrize(
    ("replacement", "expected"),
    [
        ('window/handheld/orientation="portrait"', "orientation must be landscape"),
        ("config/quit_on_go_back=true", "Back must not quit"),
    ],
)
def test_project_settings_are_enforced(tmp_path: Path, replacement: str, expected: str) -> None:
    module = _module(EXPORT_VALIDATOR, "android_export_validator")
    root = _repository(tmp_path)
    project = root / "godot/Tet4D.Godot/project.godot"
    original = 'window/handheld/orientation="landscape"' if "orientation" in replacement else "config/quit_on_go_back=false"
    project.write_text(project.read_text(encoding="utf-8").replace(original, replacement), encoding="utf-8")
    with pytest.raises(module.AndroidExportError, match=expected):
        module.validate(root)


def test_screen_support_must_stay_tablet_shaped(tmp_path: Path) -> None:
    module = _module(EXPORT_VALIDATOR, "android_export_validator")
    root = _repository(tmp_path)
    presets = root / "godot/Tet4D.Godot/export_presets.cfg"
    presets.write_text(
        presets.read_text(encoding="utf-8").replace("screen/support_normal=false", "screen/support_normal=true"),
        encoding="utf-8",
    )
    with pytest.raises(module.AndroidExportError, match="handset screens"):
        module.validate(root)


def test_committed_signing_material_is_rejected(tmp_path: Path) -> None:
    module = _module(EXPORT_VALIDATOR, "android_export_validator")
    root = _repository(tmp_path)
    (root / "release.keystore").write_bytes(b"not a real key")
    with pytest.raises(module.AndroidExportError, match="signing secrets are committed"):
        module.validate(root)


def _apk(tmp_path: Path, *, omit: str = "", unsigned: bool = False) -> Path:
    module = _module(PACKAGE_VALIDATOR, "android_package_validator")
    archive_path = tmp_path / "Tet4D-Designer-0.7.5-android-arm64.apk"
    members = {
        "AndroidManifest.xml": module.APPLICATION_ID.encode("utf-16-le"),
        "classes.dex": b"dex\n035\x00",
        "lib/arm64-v8a/libgodot_android.so": b"\x7fELF",
        "lib/arm64-v8a/libtet4d_core.android.template_release.arm64.so": b"\x7fELF",
        "assets/Tet4DDesigner.pck": b"\n".join(module.PCK_RESOURCES),
    }
    if not unsigned:
        members["META-INF/CERT.RSA"] = b"signature"
    members.pop(omit, None)
    with zipfile.ZipFile(archive_path, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    return archive_path


def test_complete_apk_is_accepted(tmp_path: Path) -> None:
    module = _module(PACKAGE_VALIDATOR, "android_package_validator")
    result = module.validate(_apk(tmp_path), ROOT)
    assert result["application_id"] == "io.github.mousomer.tet4d.designer"
    assert result["python_runtime_included"] is False


def test_apk_without_the_native_extension_is_rejected(tmp_path: Path) -> None:
    module = _module(PACKAGE_VALIDATOR, "android_package_validator")
    archive = _apk(tmp_path, omit="lib/arm64-v8a/libtet4d_core.android.template_release.arm64.so")
    with pytest.raises(module.AndroidPackageError, match="missing required APK members"):
        module.validate(archive, ROOT)


def test_unsigned_apk_is_rejected(tmp_path: Path) -> None:
    module = _module(PACKAGE_VALIDATOR, "android_package_validator")
    with pytest.raises(module.AndroidPackageError, match="unsigned"):
        module.validate(_apk(tmp_path, unsigned=True), ROOT)
