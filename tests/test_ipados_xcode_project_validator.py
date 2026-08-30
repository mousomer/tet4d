from __future__ import annotations

import importlib.util
import plistlib
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "packaging/godot/validate_ipados_project.py"


def _module():
    spec = importlib.util.spec_from_file_location("ipados_project_validator", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pack(paths: list[str]) -> bytes:
    directory = struct.pack("<I", len(paths))
    for path in paths:
        raw = path.encode("utf-8")
        directory += struct.pack("<I", len(raw)) + raw
        directory += struct.pack("<QQ", 0, 0) + b"\x00" * 16 + struct.pack("<I", 0)
    header = struct.pack("<6I", 0x43504447, 4, 4, 7, 2, 2) + struct.pack("<QQ", 112, 112)
    header += b"\x00" * (112 - len(header))
    return header + directory


def _project(
    tmp_path: Path,
    *,
    device_family: str = "2",
    orientations: list[str] | None = None,
    files_app: bool = True,
    in_place: bool = True,
    native: bool = False,
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
                f'\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = {module.BUNDLE_IDENTIFIER};',
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
    (root / "Tet4DDesigner.pck").write_bytes(_pack(list(module.REQUIRED_PACK_RESOURCES)))
    if native:
        (root / "libtet4d_core.ios.template_release.xcframework").mkdir()
    return root


def test_complete_project_is_accepted(tmp_path: Path) -> None:
    module = _module()
    result = module.validate(_project(tmp_path, native=True), ROOT)
    assert result["bundle_identifier"] == "io.github.mousomer.tet4d.designer"
    assert result["native_extension_present"] is True
    assert result["development_repository_required"] is False


def test_missing_native_extension_is_reported_not_hidden(tmp_path: Path) -> None:
    module = _module()
    project = _project(tmp_path, native=False)
    with pytest.raises(module.IpadOsProjectError, match="GDExtension xcframework is absent"):
        module.validate(project, ROOT)
    relaxed = module.validate(project, ROOT, require_native_extension=False)
    assert relaxed["native_extension_present"] is False


def test_iphone_device_family_is_rejected(tmp_path: Path) -> None:
    module = _module()
    with pytest.raises(module.IpadOsProjectError, match="iPad device family"):
        module.validate(_project(tmp_path, device_family="1", native=True), ROOT)


def test_portrait_orientation_is_rejected(tmp_path: Path) -> None:
    module = _module()
    project = _project(
        tmp_path,
        orientations=["UIInterfaceOrientationPortrait", "UIInterfaceOrientationLandscapeLeft"],
        native=True,
    )
    with pytest.raises(module.IpadOsProjectError, match="landscape only"):
        module.validate(project, ROOT)


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
        module.validate(_project(tmp_path, native=True, **kwargs), ROOT)


def test_pack_must_carry_the_catalogue_and_scenarios(tmp_path: Path) -> None:
    module = _module()
    project = _project(tmp_path, native=True)
    (project / "Tet4DDesigner.pck").write_bytes(_pack(["config/built_in_style_catalog.json"]))
    with pytest.raises(module.IpadOsProjectError, match="missing required resources"):
        module.validate(project, ROOT)
