#!/usr/bin/env python3
"""Validate the exported iPadOS Design Laboratory Xcode project.

Configuration validation runs without Xcode, a signing identity, a simulator,
or a device. Release validation additionally uses Apple's binary inspection
tools to gate the native slice and linkage contracts before the Xcode build.
"""

from __future__ import annotations

import argparse
import configparser
import plistlib
import re
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from godot_pack import PackFormatError, read_pack_file, read_pack_paths
from ipados_native import (
    DEVICE_ARCHITECTURES,
    SIMULATOR_ARCHITECTURES,
    IpadOsNativeError,
    validate_xcframework,
)

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
ARTIFACT_MODES = ("configuration", "release")
DESCRIPTOR_PATH = "addons/tet4d_core/tet4d_core.gdextension"
IOS_DEBUG_DECLARATION = (
    'ios.debug = "res://addons/tet4d_core/bin/'
    'libtet4d_core.ios.template_debug.xcframework"'
)
IOS_RELEASE_DECLARATION = (
    'ios.release = "res://addons/tet4d_core/bin/'
    'libtet4d_core.ios.template_release.xcframework"'
)
RELEASE_NATIVE_FRAMEWORK = "libtet4d_core.ios.template_release.xcframework"
RELEASE_NATIVE_FRAMEWORK_PATH = (
    "Tet4DDesigner/dylibs/addons/tet4d_core/bin/" + RELEASE_NATIVE_FRAMEWORK
)
GODOT_ENGINE_FRAMEWORK_PATH = "Tet4DDesigner.xcframework"
MOLTENVK_FRAMEWORK_PATH = "MoltenVK.xcframework"


class IpadOsProjectError(ValueError):
    """The exported Xcode project violates the packaging contract."""


def _build_setting(pbxproj: str, key: str) -> str:
    match = re.search(
        rf"^\s*{re.escape(key)} = \"?([^\";\n]+)\"?;", pbxproj, re.MULTILINE
    )
    return match.group(1).strip() if match else ""


def _check_source_export_preset(repository_root: Path) -> None:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(
        repository_root / "godot/Tet4D.Godot/export_presets.cfg",
        encoding="utf-8",
    )
    for section in parser.sections():
        preset = parser[section]
        if preset.get("name", "").strip('"') != "iPadOS":
            continue
        if preset.get("platform", "").strip('"') != "iOS":
            raise IpadOsProjectError("iPadOS export preset must target iOS")
        options = parser[f"{section}.options"]
        # Godot 4.7.2 uses an integer enum: 0 App Store, 1 Development,
        # 2 Ad-Hoc, 3 Enterprise. Strings and absence silently resolve wrong.
        if options.get("application/export_method_release") != "1":
            raise IpadOsProjectError(
                "iPadOS release export method must be integer enum 1 (Development)"
            )
        return
    raise IpadOsProjectError("iPadOS export preset is not defined")


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
        raise IpadOsProjectError(
            "Xcode marketing version disagrees with pyproject.toml"
        )
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
        raise IpadOsProjectError(
            f"iPad build must be landscape only, got {sorted(orientations)}"
        )
    # Without these two keys the nominated bundle is trapped in the application
    # sandbox and cannot be retrieved without the development repository.
    if not plist.get("UIFileSharingEnabled"):
        raise IpadOsProjectError("Documents directory is not exposed to the Files app")
    if not plist.get("LSSupportsOpeningDocumentsInPlace"):
        raise IpadOsProjectError(
            "Documents directory does not support opening in place"
        )
    return plist


def _check_export_options(project_root: Path) -> None:
    plist_path = project_root / "Tet4DDesigner/export_options.plist"
    if not plist_path.is_file():
        raise IpadOsProjectError("exported Xcode project has no export_options.plist")
    with plist_path.open("rb") as handle:
        options = plistlib.load(handle)
    if options.get("method") != "development":
        raise IpadOsProjectError(
            f"Xcode export method must be development, got {options.get('method')!r}"
        )


def _check_pack(project_root: Path) -> tuple[int, str]:
    pack_path = project_root / "Tet4DDesigner.pck"
    if not pack_path.is_file():
        raise IpadOsProjectError("exported Xcode project has no Godot resource pack")
    try:
        paths = set(read_pack_paths(pack_path))
    except (OSError, PackFormatError) as exc:
        raise IpadOsProjectError(f"iPadOS resource pack is unreadable: {exc}") from exc
    missing = [name for name in REQUIRED_PACK_RESOURCES if name not in paths]
    if missing:
        raise IpadOsProjectError(
            f"iPadOS pack is missing required resources: {missing}"
        )
    development_only = sorted(
        name
        for name in paths
        if name.startswith("tests/") or name.endswith((".py", ".pyc", ".uid"))
    )
    if development_only:
        raise IpadOsProjectError(
            f"development-only files entered the iPadOS pack: {development_only[:5]}"
        )
    payload = pack_path.read_bytes()
    for marker in FORBIDDEN_PATH_MARKERS:
        if marker.encode() in payload:
            raise IpadOsProjectError(
                f"pack contains development-only path marker {marker!r}"
            )
    try:
        descriptor = read_pack_file(pack_path, DESCRIPTOR_PATH).decode("utf-8")
    except (PackFormatError, UnicodeDecodeError) as exc:
        raise IpadOsProjectError(
            f"iPadOS GDExtension descriptor is unreadable: {exc}"
        ) from exc
    return len(paths), descriptor


def _check_artifact_mode(
    project_root: Path, artifact_mode: str, descriptor: str
) -> Path | None:
    if artifact_mode not in ARTIFACT_MODES:
        raise IpadOsProjectError(f"unknown iPadOS artifact mode {artifact_mode!r}")
    has_debug_declaration = IOS_DEBUG_DECLARATION in descriptor
    has_release_declaration = IOS_RELEASE_DECLARATION in descriptor
    release_native = project_root / RELEASE_NATIVE_FRAMEWORK_PATH
    any_native = sorted(project_root.glob("**/libtet4d_core.ios.*.xcframework"))

    if artifact_mode == "configuration":
        if has_debug_declaration or has_release_declaration:
            raise IpadOsProjectError(
                "configuration artifact descriptor must deliberately omit unavailable iOS libraries"
            )
        if any_native:
            raise IpadOsProjectError(
                "configuration artifact must not carry a native framework it does not claim"
            )
        return None

    if not has_debug_declaration or not has_release_declaration:
        raise IpadOsProjectError(
            "release artifact requires the complete iOS GDExtension descriptor"
        )
    if not release_native.is_dir():
        raise IpadOsProjectError(
            f"release artifact is missing {RELEASE_NATIVE_FRAMEWORK_PATH}"
        )
    return release_native


def _check_release_native_frameworks(
    project_root: Path,
) -> dict[str, dict[str, list[str]]]:
    exact = {
        "exact_device": DEVICE_ARCHITECTURES,
        "exact_simulator": SIMULATOR_ARCHITECTURES,
    }
    return {
        "tet4d": validate_xcframework(
            project_root / RELEASE_NATIVE_FRAMEWORK_PATH,
            **exact,
            require_godot_cpp=True,
        ),
        "godot_engine": validate_xcframework(
            project_root / GODOT_ENGINE_FRAMEWORK_PATH,
            **exact,
        ),
        "moltenvk": validate_xcframework(
            project_root / MOLTENVK_FRAMEWORK_PATH,
        ),
    }


def validate(
    project_root: Path,
    repository_root: Path,
    artifact_mode: str,
    native_validator: Callable[
        [Path], dict[str, dict[str, list[str]]]
    ] = _check_release_native_frameworks,
) -> dict[str, object]:
    version = tomllib.loads(
        (repository_root / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]
    _check_source_export_preset(repository_root)
    _check_xcode_project(project_root, version)
    _check_info_plist(project_root)
    _check_export_options(project_root)
    pack_resources, descriptor = _check_pack(project_root)
    release_native = _check_artifact_mode(project_root, artifact_mode, descriptor)
    native_architectures = native_validator(project_root) if release_native else {}
    return {
        "version": version,
        "bundle_identifier": BUNDLE_IDENTIFIER,
        "artifact_mode": artifact_mode,
        "pack_resources": pack_resources,
        "native_extension_present": release_native is not None,
        "native_architectures": native_architectures,
        "python_runtime_required": False,
        "development_repository_required": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument(
        "--repository-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument(
        "--artifact-mode",
        choices=ARTIFACT_MODES,
        required=True,
        help="declare whether this is reduced configuration evidence or a release payload",
    )
    args = parser.parse_args()
    try:
        result = validate(
            args.project_root.resolve(),
            args.repository_root.resolve(),
            args.artifact_mode,
        )
    except (
        OSError,
        IpadOsNativeError,
        IpadOsProjectError,
        plistlib.InvalidFileException,
    ) as exc:
        print(f"iPadOS Xcode project INVALID: {exc}")
        return 1
    native = "with" if result["native_extension_present"] else "without"
    print(
        f"iPadOS {result['artifact_mode']} export VALID: "
        f"{result['bundle_identifier']} {result['version']} · "
        f"{result['pack_resources']} packed resources · {native} the Tet4D core GDExtension"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
