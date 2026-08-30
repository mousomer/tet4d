#!/usr/bin/env python3
"""Validate the exported iPadOS Design Laboratory Xcode project.

Runs without Xcode, a signing identity, a simulator, or a device, so the
iPadOS target's structure and metadata are gated on any macOS host that can
run the pinned Godot editor.
"""

from __future__ import annotations

import argparse
import plistlib
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from godot_pack import PackFormatError, read_pack_paths

BUNDLE_IDENTIFIER = "io.github.mousomer.tet4d.designer"
# Apple device family 2 is iPad. Godot's preset index 1 resolves to it.
IPAD_DEVICE_FAMILY = "2"
REQUIRED_PACK_RESOURCES = (
    "config/built_in_style_catalog.json",
    "config/design_scenario_catalog.json",
    "config/shell_settings_registry.json",
    "assets/tet4d_bundle/manifest.json",
    "addons/tet4d_core/tet4d_core.gdextension",
)
LANDSCAPE_ORIENTATIONS = frozenset(
    {"UIInterfaceOrientationLandscapeLeft", "UIInterfaceOrientationLandscapeRight"}
)
FORBIDDEN_PATH_MARKERS = ("workspace/personal/repos",)


class IpadOsProjectError(ValueError):
    """The exported Xcode project violates the packaging contract."""


def _build_setting(pbxproj: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)} = \"?([^\";\n]+)\"?;", pbxproj, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _check_xcode_project(project_root: Path, version: str) -> None:
    pbxproj_path = project_root / "Tet4DDesigner.xcodeproj/project.pbxproj"
    if not pbxproj_path.is_file():
        raise IpadOsProjectError("exported Xcode project has no project.pbxproj")
    pbxproj = pbxproj_path.read_text(encoding="utf-8")
    if _build_setting(pbxproj, "PRODUCT_BUNDLE_IDENTIFIER") != BUNDLE_IDENTIFIER:
        raise IpadOsProjectError(f"Xcode project must build {BUNDLE_IDENTIFIER}")
    if _build_setting(pbxproj, "TARGETED_DEVICE_FAMILY") != IPAD_DEVICE_FAMILY:
        raise IpadOsProjectError("Xcode project must target the iPad device family")
    deployment_target = _build_setting(pbxproj, "IPHONEOS_DEPLOYMENT_TARGET")
    if not deployment_target:
        raise IpadOsProjectError("Xcode project declares no iOS deployment target")
    if _build_setting(pbxproj, "MARKETING_VERSION") not in ("", version):
        raise IpadOsProjectError("Xcode marketing version disagrees with pyproject.toml")
    for scheme in ("project.xcworkspace", "xcshareddata"):
        if not (project_root / "Tet4DDesigner.xcodeproj" / scheme).exists():
            raise IpadOsProjectError(f"Xcode project is missing {scheme}")


def _check_info_plist(project_root: Path) -> dict[str, object]:
    plist_path = project_root / "Tet4DDesigner/Tet4DDesigner-Info.plist"
    if not plist_path.is_file():
        raise IpadOsProjectError("exported Xcode project has no Info.plist")
    with plist_path.open("rb") as handle:
        plist = plistlib.load(handle)
    orientations = set(plist.get("UISupportedInterfaceOrientations", [])) | set(
        plist.get("UISupportedInterfaceOrientations~ipad", [])
    )
    if not orientations or not orientations <= LANDSCAPE_ORIENTATIONS:
        raise IpadOsProjectError(f"iPad build must be landscape only, got {sorted(orientations)}")
    # Without these two keys the nominated bundle is trapped in the application
    # sandbox and cannot be retrieved without the development repository.
    if not plist.get("UIFileSharingEnabled"):
        raise IpadOsProjectError("Documents directory is not exposed to the Files app")
    if not plist.get("LSSupportsOpeningDocumentsInPlace"):
        raise IpadOsProjectError("Documents directory does not support opening in place")
    return plist


def _check_pack(project_root: Path) -> int:
    pack_path = project_root / "Tet4DDesigner.pck"
    if not pack_path.is_file():
        raise IpadOsProjectError("exported Xcode project has no Godot resource pack")
    try:
        paths = set(read_pack_paths(pack_path))
    except (OSError, PackFormatError) as exc:
        raise IpadOsProjectError(f"iPadOS resource pack is unreadable: {exc}") from exc
    missing = [name for name in REQUIRED_PACK_RESOURCES if name not in paths]
    if missing:
        raise IpadOsProjectError(f"iPadOS pack is missing required resources: {missing}")
    development_only = sorted(
        name for name in paths
        if name.startswith("tests/") or name.endswith((".py", ".pyc", ".uid"))
    )
    if development_only:
        raise IpadOsProjectError(f"development-only files entered the iPadOS pack: {development_only[:5]}")
    payload = pack_path.read_bytes()
    for marker in FORBIDDEN_PATH_MARKERS:
        if marker.encode() in payload:
            raise IpadOsProjectError(f"pack contains development-only path marker {marker!r}")
    return len(paths)


def validate(
    project_root: Path,
    repository_root: Path,
    require_native_extension: bool = True,
) -> dict[str, object]:
    version = tomllib.loads(
        (repository_root / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]
    _check_xcode_project(project_root, version)
    _check_info_plist(project_root)
    pack_resources = _check_pack(project_root)
    native = sorted(project_root.glob("**/libtet4d_core.ios.*.xcframework"))
    if require_native_extension and not native:
        raise IpadOsProjectError(
            "the Tet4D core GDExtension xcframework is absent; the exported project "
            "will build but the application cannot run"
        )
    return {
        "version": version,
        "bundle_identifier": BUNDLE_IDENTIFIER,
        "pack_resources": pack_resources,
        "native_extension_present": bool(native),
        "python_runtime_required": False,
        "development_repository_required": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--allow-missing-native-extension",
        action="store_true",
        help="validate structure and metadata only, on a host without the iOS SDK",
    )
    args = parser.parse_args()
    try:
        result = validate(
            args.project_root.resolve(),
            args.repository_root.resolve(),
            require_native_extension=not args.allow_missing_native_extension,
        )
    except (OSError, IpadOsProjectError, plistlib.InvalidFileException) as exc:
        print(f"iPadOS Xcode project INVALID: {exc}")
        return 1
    native = "with" if result["native_extension_present"] else "WITHOUT"
    print(
        "iPadOS Xcode project VALID: "
        f"{result['bundle_identifier']} {result['version']} · "
        f"{result['pack_resources']} packed resources · {native} the Tet4D core GDExtension"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
