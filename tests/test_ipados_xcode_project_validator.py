from __future__ import annotations

import importlib.util
import plistlib
import shutil
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "packaging/godot/validate_ipados_project.py"


def _module():
    spec = importlib.util.spec_from_file_location(
        "ipados_project_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FULL_DESCRIPTOR = b"""[configuration]
entry_symbol = \"tet4d_core_library_init\"

[libraries]
ios.debug = \"res://addons/tet4d_core/bin/libtet4d_core.ios.template_debug.xcframework\"
ios.release = \"res://addons/tet4d_core/bin/libtet4d_core.ios.template_release.xcframework\"
"""
CONFIGURATION_DESCRIPTOR = b"""[configuration]
entry_symbol = \"tet4d_core_library_init\"

[libraries]
"""


def _pack(paths: list[str], descriptor: bytes) -> bytes:
    payloads = {
        path: descriptor if path == "addons/tet4d_core/tet4d_core.gdextension" else b""
        for path in paths
    }
    file_data = b""
    entry_data: list[tuple[str, int, int]] = []
    for path, payload in payloads.items():
        entry_data.append((path, len(file_data), len(payload)))
        file_data += payload

    directory = struct.pack("<I", len(entry_data))
    for path, offset, size in entry_data:
        raw = path.encode("utf-8")
        directory += struct.pack("<I", len(raw)) + raw
        directory += (
            struct.pack("<QQ", offset, size) + b"\x00" * 16 + struct.pack("<I", 0)
        )
    directory_offset = 112 + len(file_data)
    header = struct.pack("<6I", 0x43504447, 4, 4, 7, 2, 2)
    header += struct.pack("<QQ", 112, directory_offset)
    header += b"\x00" * (112 - len(header))
    return header + file_data + directory


def _repository(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "godot/Tet4D.Godot").mkdir(parents=True)
    shutil.copy(ROOT / "pyproject.toml", root / "pyproject.toml")
    shutil.copy(
        ROOT / "godot/Tet4D.Godot/export_presets.cfg",
        root / "godot/Tet4D.Godot/export_presets.cfg",
    )
    return root


def _project(
    tmp_path: Path,
    *,
    device_family: str = "2",
    orientations: list[str] | None = None,
    files_app: bool = True,
    in_place: bool = True,
    native: bool = False,
    artifact_mode: str = "release",
    export_method: str = "development",
    descriptor: bytes | None = None,
) -> Path:
    module = _module()
    root = tmp_path / "ipad"
    (root / "Tet4DDesigner.xcodeproj/project.xcworkspace").mkdir(parents=True)
    (root / "Tet4DDesigner.xcodeproj/xcshareddata").mkdir(parents=True)
    (root / "Tet4DDesigner").mkdir(parents=True)
    (root / "Tet4DDesigner.xcodeproj/project.pbxproj").write_text(
        "\n".join(
            [
                "// !$*UTF8*$!",
                "\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 15.0;",
                f"\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = {module.BUNDLE_IDENTIFIER};",
                f'\t\t\t\tTARGETED_DEVICE_FAMILY = "{device_family}";',
            ]
        ),
        encoding="utf-8",
    )
    plist = {
        "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
        "UISupportedInterfaceOrientations": orientations
        if orientations is not None
        else sorted(module.LANDSCAPE_ORIENTATIONS),
        "UIFileSharingEnabled": files_app,
        "LSSupportsOpeningDocumentsInPlace": in_place,
    }
    with (root / "Tet4DDesigner/Tet4DDesigner-Info.plist").open("wb") as handle:
        plistlib.dump(plist, handle)
    with (root / "Tet4DDesigner/export_options.plist").open("wb") as handle:
        plistlib.dump({"method": export_method}, handle)
    if descriptor is None:
        descriptor = (
            FULL_DESCRIPTOR if artifact_mode == "release" else CONFIGURATION_DESCRIPTOR
        )
    (root / "Tet4DDesigner.pck").write_bytes(
        _pack(list(module.REQUIRED_PACK_RESOURCES), descriptor)
    )
    if native:
        (root / module.RELEASE_NATIVE_FRAMEWORK).mkdir()
    return root


def test_complete_project_is_accepted(tmp_path: Path) -> None:
    module = _module()
    result = module.validate(_project(tmp_path, native=True), ROOT, "release")
    assert result["bundle_identifier"] == "io.github.mousomer.tet4d.designer"
    assert result["artifact_mode"] == "release"
    assert result["native_extension_present"] is True
    assert result["development_repository_required"] is False


def test_configuration_artifact_is_accepted_as_configuration_only(
    tmp_path: Path,
) -> None:
    module = _module()
    project = _project(tmp_path, artifact_mode="configuration")
    result = module.validate(project, ROOT, "configuration")
    assert result["artifact_mode"] == "configuration"
    assert result["native_extension_present"] is False


def test_configuration_artifact_cannot_masquerade_as_release(tmp_path: Path) -> None:
    module = _module()
    project = _project(tmp_path, artifact_mode="configuration")
    with pytest.raises(
        module.IpadOsProjectError, match="complete iOS GDExtension descriptor"
    ):
        module.validate(project, ROOT, "release")


def test_release_artifact_requires_native_framework(tmp_path: Path) -> None:
    module = _module()
    project = _project(tmp_path, artifact_mode="release")
    with pytest.raises(module.IpadOsProjectError, match="missing libtet4d_core"):
        module.validate(project, ROOT, "release")


def test_configuration_artifact_rejects_full_descriptor(tmp_path: Path) -> None:
    module = _module()
    project = _project(
        tmp_path,
        artifact_mode="configuration",
        descriptor=FULL_DESCRIPTOR,
    )
    with pytest.raises(module.IpadOsProjectError, match="deliberately omit"):
        module.validate(project, ROOT, "configuration")


def test_source_release_method_is_explicit_development_enum(tmp_path: Path) -> None:
    module = _module()
    project = _project(tmp_path, native=True)
    repository = _repository(tmp_path)
    preset = repository / "godot/Tet4D.Godot/export_presets.cfg"
    preset.write_text(
        preset.read_text(encoding="utf-8").replace(
            "application/export_method_release=1",
            'application/export_method_release="development"',
        ),
        encoding="utf-8",
    )
    with pytest.raises(module.IpadOsProjectError, match="integer enum 1"):
        module.validate(project, repository, "release")


def test_generated_export_method_must_be_development(tmp_path: Path) -> None:
    module = _module()
    project = _project(tmp_path, native=True, export_method="app-store")
    with pytest.raises(module.IpadOsProjectError, match="must be development"):
        module.validate(project, ROOT, "release")


def test_build_script_separates_configuration_and_release_outputs() -> None:
    script = (ROOT / "packaging/godot/build_ipados.sh").read_text(encoding="utf-8")
    assert 'ARTIFACT_DIR="$ARTIFACT_BASE_DIR/$ARTIFACT_MODE-export"' in script
    assert '"--artifact-mode" "$ARTIFACT_MODE"' in script
    assert (
        'cp -R "$native_xcframework" "$staged_project_root/addons/tet4d_core/bin/"'
        in script
    )


def test_iphone_device_family_is_rejected(tmp_path: Path) -> None:
    module = _module()
    with pytest.raises(module.IpadOsProjectError, match="iPad device family"):
        module.validate(
            _project(tmp_path, device_family="1", native=True), ROOT, "release"
        )


def test_portrait_orientation_is_rejected(tmp_path: Path) -> None:
    module = _module()
    project = _project(
        tmp_path,
        orientations=[
            "UIInterfaceOrientationPortrait",
            "UIInterfaceOrientationLandscapeLeft",
        ],
        native=True,
    )
    with pytest.raises(module.IpadOsProjectError, match="landscape only"):
        module.validate(project, ROOT, "release")


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"files_app": False}, "not exposed to the Files app"),
        ({"in_place": False}, "opening in place"),
    ],
)
def test_sandboxed_documents_directory_is_rejected(
    tmp_path: Path, kwargs: dict[str, bool], expected: str
) -> None:
    """A nominated bundle the designer cannot retrieve is not an export."""
    module = _module()
    with pytest.raises(module.IpadOsProjectError, match=expected):
        module.validate(_project(tmp_path, native=True, **kwargs), ROOT, "release")


def test_pack_must_carry_the_catalogue_and_scenarios(tmp_path: Path) -> None:
    module = _module()
    project = _project(tmp_path, native=True)
    (project / "Tet4DDesigner.pck").write_bytes(
        _pack(["config/built_in_style_catalog.json"], FULL_DESCRIPTOR)
    )
    with pytest.raises(module.IpadOsProjectError, match="missing required resources"):
        module.validate(project, ROOT, "release")
