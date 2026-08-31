from __future__ import annotations

import configparser
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
SIGNING_STAGER = ROOT / "packaging/godot/stage_android_export_preset.py"


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
        shutil.copy(
            ROOT / "godot/Tet4D.Godot" / name, root / "godot/Tet4D.Godot" / name
        )
    return root


def test_repository_android_export_configuration_is_valid() -> None:
    module = _module(EXPORT_VALIDATOR, "android_export_validator")
    result = module.validate(ROOT)
    assert result["application_id"] == "io.github.mousomer.tet4d.designer"
    assert result["python_runtime_required"] is False
    assert result["godot_editor_required"] is False


def test_tracked_android_preset_contains_no_release_signing_credentials() -> None:
    module = _module(SIGNING_STAGER, "android_signing_stager")
    source = ROOT / "godot/Tet4D.Godot/export_presets.cfg"
    parser, options_section = module._load_options(source)
    for option in module.RELEASE_SIGNING_OPTIONS:
        assert not parser[options_section].get(option, "").strip('"')


def test_staged_preset_injects_ephemeral_release_signing_only(tmp_path: Path) -> None:
    module = _module(SIGNING_STAGER, "android_signing_stager")
    source = ROOT / "godot/Tet4D.Godot/export_presets.cfg"
    staged = tmp_path / "project/export_presets.cfg"
    keystore = tmp_path / "editor/test-release.keystore"
    keystore.parent.mkdir()
    keystore.write_bytes(b"ephemeral test key")

    source_before = source.read_bytes()
    module.stage_release_signing(source, staged, keystore)
    module.validate_staged_release_signing(
        staged,
        keystore,
        module.TEST_KEYSTORE_ALIAS,
        module.TEST_KEYSTORE_PASSWORD,
    )
    assert source.read_bytes() == source_before


def test_debug_only_signing_is_not_release_signing(tmp_path: Path) -> None:
    module = _module(SIGNING_STAGER, "android_signing_stager")
    staged = tmp_path / "export_presets.cfg"
    shutil.copy(ROOT / "godot/Tet4D.Godot/export_presets.cfg", staged)
    keystore = tmp_path / "debug.keystore"
    keystore.write_bytes(b"ephemeral test key")

    parser, options_section = module._load_options(staged)
    parser[options_section]["keystore/debug"] = f'"{keystore}"'
    parser[options_section]["keystore/debug_user"] = '"androiddebugkey"'
    parser[options_section]["keystore/debug_password"] = '"android"'
    with staged.open("w", encoding="utf-8") as handle:
        parser.write(handle, space_around_delimiters=False)

    with pytest.raises(module.AndroidSigningStageError, match="keystore/release"):
        module.validate_staged_release_signing(
            staged, keystore, "androiddebugkey", "android"
        )


def test_android_build_keeps_release_export_and_uses_staged_preset_helper() -> None:
    build_script = (ROOT / "packaging/godot/build_android.sh").read_text(
        encoding="utf-8"
    )
    assert '--export-release "$PRESET_NAME"' in build_script
    assert "stage_android_export_preset.py" in build_script


def test_pack_reader_round_trips_a_directory(tmp_path: Path) -> None:
    reader = _module(PACK_READER, "godot_pack_reader")
    pack_path = tmp_path / "sample.pck"
    pack_path.write_bytes(
        _pack(["config/built_in_style_catalog.json", "scenes/trace_replay.scn"])
    )
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
    pack_path.write_bytes(
        _pack([*module.REQUIRED_PACK_RESOURCES, "tests/run_tests.gd"])
    )
    with pytest.raises(module.AndroidExportError, match="development-only files"):
        module.validate(ROOT, pack_path)


@pytest.mark.parametrize(
    ("replacement", "expected"),
    [
        ("window/handheld/orientation=1", "orientation must be landscape"),
        ("config/quit_on_go_back=true", "Back must not quit"),
    ],
)
def test_project_settings_are_enforced(
    tmp_path: Path, replacement: str, expected: str
) -> None:
    module = _module(EXPORT_VALIDATOR, "android_export_validator")
    root = _repository(tmp_path)
    project = root / "godot/Tet4D.Godot/project.godot"
    original = (
        "window/handheld/orientation=4"
        if "orientation" in replacement
        else "config/quit_on_go_back=false"
    )
    project.write_text(
        project.read_text(encoding="utf-8").replace(original, replacement),
        encoding="utf-8",
    )
    with pytest.raises(module.AndroidExportError, match=expected):
        module.validate(root)


def test_screen_support_must_stay_tablet_shaped(tmp_path: Path) -> None:
    module = _module(EXPORT_VALIDATOR, "android_export_validator")
    root = _repository(tmp_path)
    presets = root / "godot/Tet4D.Godot/export_presets.cfg"
    presets.write_text(
        presets.read_text(encoding="utf-8").replace(
            "screen/support_normal=false", "screen/support_normal=true"
        ),
        encoding="utf-8",
    )
    with pytest.raises(module.AndroidExportError, match="handset screens"):
        module.validate(root)


def test_committed_signing_material_is_rejected(tmp_path: Path) -> None:
    module = _module(EXPORT_VALIDATOR, "android_export_validator")
    root = _repository(tmp_path)
    (root / "release.keystore").write_bytes(b"not a real key")
    with pytest.raises(
        module.AndroidExportError, match="signing secrets are committed"
    ):
        module.validate(root)


def test_committed_release_preset_credentials_are_rejected(tmp_path: Path) -> None:
    module = _module(EXPORT_VALIDATOR, "android_export_validator")
    root = _repository(tmp_path)
    presets = root / "godot/Tet4D.Godot/export_presets.cfg"
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(presets, encoding="utf-8")
    android_section = next(
        section
        for section in parser.sections()
        if parser[section].get("name", "").strip('"') == module.PRESET_NAME
    )
    parser[f"{android_section}.options"]["keystore/release"] = '"release.keystore"'
    with presets.open("w", encoding="utf-8") as handle:
        parser.write(handle, space_around_delimiters=False)
    with pytest.raises(module.AndroidExportError, match="must not be committed"):
        module.validate(root)


def _apk(tmp_path: Path, *, omit: str = "", unsigned: bool = False) -> Path:
    module = _module(PACKAGE_VALIDATOR, "android_package_validator")
    archive_path = tmp_path / "Tet4D-Designer-0.7.5-android-arm64.apk"
    members = {
        "AndroidManifest.xml": module.APPLICATION_ID.encode("utf-16-le"),
        "classes.dex": b"dex\n035\x00",
        "lib/arm64-v8a/libgodot_android.so": b"\x7fELF",
        "lib/arm64-v8a/libtet4d_core.android.template_release.arm64.so": b"\x7fELF",
        "assets/assets.sparsepck": b"sparse project directory",
    }
    members.update({name: b"project asset" for name in module.PROJECT_ASSET_MEMBERS})
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
    archive = _apk(
        tmp_path, omit="lib/arm64-v8a/libtet4d_core.android.template_release.arm64.so"
    )
    with pytest.raises(
        module.AndroidPackageError, match="missing required APK members"
    ):
        module.validate(archive, ROOT)


def test_unsigned_apk_is_rejected(tmp_path: Path) -> None:
    module = _module(PACKAGE_VALIDATOR, "android_package_validator")
    with pytest.raises(module.AndroidPackageError, match="unsigned"):
        module.validate(_apk(tmp_path, unsigned=True), ROOT)


def test_apk_without_sparse_project_metadata_is_rejected(tmp_path: Path) -> None:
    module = _module(PACKAGE_VALIDATOR, "android_package_validator")
    archive = _apk(tmp_path, omit="assets/assets.sparsepck")
    with pytest.raises(module.AndroidPackageError, match="missing required APK members"):
        module.validate(archive, ROOT)


def test_apk_without_a_required_project_asset_is_rejected(tmp_path: Path) -> None:
    module = _module(PACKAGE_VALIDATOR, "android_package_validator")
    archive = _apk(tmp_path, omit=module.PROJECT_ASSET_MEMBERS[0])
    with pytest.raises(module.AndroidPackageError, match="missing required project assets"):
        module.validate(archive, ROOT)


def test_apk_project_assets_must_not_leak_machine_paths(tmp_path: Path) -> None:
    module = _module(PACKAGE_VALIDATOR, "android_package_validator")
    archive = _apk(tmp_path)
    with zipfile.ZipFile(archive, "a") as apk:
        machine_path = b"/" + b"home/" + b"runner/work/tet4d"
        apk.writestr("assets/generated.cache", machine_path)
    with pytest.raises(module.AndroidPackageError, match="generated.cache.*path marker"):
        module.validate(archive, ROOT)
