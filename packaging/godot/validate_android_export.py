#!/usr/bin/env python3
"""Validate the Android tablet Design Laboratory export configuration.

Runs without a Java SDK, an Android SDK, an emulator, or a device, so the
Android target's configuration is gated on every host. Give it an exported
resource pack to additionally prove which resources the Android export ships.
"""

from __future__ import annotations

import argparse
import configparser
import os
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from godot_pack import PackFormatError, read_pack_paths

PRESET_NAME = "Android Tablet"
APPLICATION_ID = "io.github.mousomer.tet4d.designer"
# The Design Laboratory is unusable without these; they are the platform
# independent catalogue, scenario, ownership, and shell resources.
REQUIRED_PACK_RESOURCES = (
    "config/built_in_style_catalog.json",
    "config/design_scenario_catalog.json",
    "config/shell_settings_registry.json",
    "assets/tet4d_bundle/manifest.json",
    "addons/tet4d_core/tet4d_core.gdextension",
)
# Private signing material must never reach the repository. Debug/test signing
# is supplied from the environment at build time instead.
SIGNING_SECRET_SUFFIXES = (".keystore", ".jks", ".p12", ".pepk")
SIGNING_SECRET_OPTIONS = (
    "keystore/debug",
    "keystore/debug_password",
    "keystore/debug_user",
    "keystore/release",
    "keystore/release_password",
    "keystore/release_user",
)
# display/window/handheld/orientation is an integer enum, not a string: 0
# Landscape, 2 Reverse Landscape, 4 Sensor Landscape. A string value is
# silently ignored by the engine and falls back to 0, so the accepted values
# are checked numerically.
LANDSCAPE_ORIENTATIONS = ("0", "2", "4")
_HOME_PREFIXES = ("/" + "Users/", "/" + "home/")
ABSOLUTE_PATH_PATTERN = re.compile(
    '"(?:' + "|".join(_HOME_PREFIXES) + r"|[A-Za-z]:\\)"
)


# Directories that are never part of the committed source tree.
PRUNED_DIRECTORIES = frozenset(
    {".git", ".venv", "venv", "node_modules", "artifacts", "dist", "build", "__pycache__", "third_party"}
)


class AndroidExportError(ValueError):
    """The Android export configuration violates the packaging contract."""


def _project_setting(project_text: str, key: str) -> str:
    match = re.search(rf'^{re.escape(key)}="?([^"\n]*)"?$', project_text, re.MULTILINE)
    return match.group(1) if match else ""


def _committed_signing_material(repository_root: Path) -> list[str]:
    found: list[str] = []
    for directory, subdirectories, filenames in os.walk(repository_root):
        subdirectories[:] = [name for name in subdirectories if name not in PRUNED_DIRECTORIES]
        for filename in filenames:
            if filename.endswith(SIGNING_SECRET_SUFFIXES):
                found.append(str(Path(directory, filename).relative_to(repository_root)))
    return found


def _presets(repository_root: Path) -> tuple[configparser.ConfigParser, str]:
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(repository_root / "godot/Tet4D.Godot/export_presets.cfg", encoding="utf-8")
    for section in parser.sections():
        if parser[section].get("name", "").strip('"') == PRESET_NAME:
            return parser, section
    raise AndroidExportError(f"export preset {PRESET_NAME!r} is not defined")


def _check_identity(options: configparser.SectionProxy, preset: configparser.SectionProxy, version: str) -> None:
    if preset.get("platform", "").strip('"') != "Android":
        raise AndroidExportError("Android preset does not target the Android platform")
    if options.get("package/unique_name", "").strip('"') != APPLICATION_ID:
        raise AndroidExportError(f"Android application ID must be {APPLICATION_ID}")
    if options.get("version/name", "").strip('"') != version:
        raise AndroidExportError("Android version name disagrees with pyproject.toml")


def _check_tablet_shape(options: configparser.SectionProxy) -> None:
    """A landscape tablet build: large screens only, arm64 only."""
    if options.get("architectures/arm64-v8a") != "true":
        raise AndroidExportError("Android tablet build must include arm64-v8a")
    if options.get("screen/support_large") != "true" or options.get("screen/support_xlarge") != "true":
        raise AndroidExportError("Android tablet build must declare large screen support")
    if options.get("screen/support_small") != "false" or options.get("screen/support_normal") != "false":
        raise AndroidExportError("Android tablet build must not advertise handset screens")
    # Reuse the prebuilt export template rather than introducing a parallel
    # Gradle build system alongside the existing packaging scripts.
    if options.get("gradle_build/use_gradle_build") != "false":
        raise AndroidExportError("Android export must use the prebuilt template, not a Gradle build")


def _check_project_settings(repository_root: Path) -> None:
    project_text = (repository_root / "godot/Tet4D.Godot/project.godot").read_text(encoding="utf-8")
    orientation = _project_setting(project_text, "window/handheld/orientation")
    if orientation not in LANDSCAPE_ORIENTATIONS:
        raise AndroidExportError(f"handheld orientation must be landscape, not {orientation!r}")
    # The engine default would let the system Back gesture quit the process and
    # discard an in-flight comparison session.
    if "config/quit_on_go_back=false" not in project_text:
        raise AndroidExportError("system Back must not quit the application")


def _check_no_committed_secrets(repository_root: Path, options: configparser.SectionProxy) -> None:
    for option in SIGNING_SECRET_OPTIONS:
        if options.get(option, '""').strip('"'):
            raise AndroidExportError(f"signing material must not be committed in {option}")
    committed_secrets = sorted(_committed_signing_material(repository_root))
    if committed_secrets:
        raise AndroidExportError(f"signing secrets are committed: {committed_secrets}")
    export_text = (repository_root / "godot/Tet4D.Godot/export_presets.cfg").read_text(encoding="utf-8")
    if ABSOLUTE_PATH_PATTERN.search(export_text):
        raise AndroidExportError("export presets must not depend on a development machine path")


def _check_pack(pack_path: Path) -> int:
    try:
        paths = set(read_pack_paths(pack_path))
    except (OSError, PackFormatError) as exc:
        raise AndroidExportError(f"Android resource pack is unreadable: {exc}") from exc
    missing = [name for name in REQUIRED_PACK_RESOURCES if name not in paths]
    if missing:
        raise AndroidExportError(f"Android pack is missing required resources: {missing}")
    development_only = sorted(
        name for name in paths
        if name.startswith("tests/") or name.endswith((".py", ".pyc", ".uid"))
    )
    if development_only:
        raise AndroidExportError(f"development-only files entered the Android pack: {development_only[:5]}")
    return len(paths)


def validate(repository_root: Path, pack_path: Path | None = None) -> dict[str, object]:
    version = tomllib.loads(
        (repository_root / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]
    parser, section = _presets(repository_root)
    preset = parser[section]
    options = parser[f"{section}.options"]
    _check_identity(options, preset, version)
    _check_tablet_shape(options)
    _check_project_settings(repository_root)
    _check_no_committed_secrets(repository_root, options)
    pack_resources = _check_pack(pack_path) if pack_path is not None else 0
    return {
        "version": version,
        "application_id": APPLICATION_ID,
        "version_code": options.get("version/code", ""),
        "pack_resources": pack_resources,
        "python_runtime_required": False,
        "godot_editor_required": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--pack", type=Path, default=None, help="exported Android .pck to inspect")
    args = parser.parse_args()
    try:
        result = validate(args.repository_root.resolve(), args.pack.resolve() if args.pack else None)
    except (OSError, AndroidExportError) as exc:
        print(f"Android export configuration INVALID: {exc}")
        return 1
    print(
        "Android export configuration VALID: "
        f"{result['application_id']} {result['version']} (code {result['version_code']}) · "
        f"{result['pack_resources']} packed resources"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
