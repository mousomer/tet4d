#!/usr/bin/env python3
"""Structural validation for a built Android tablet Design Laboratory APK.

Complements validate_android_export.py: that one gates the configuration on
every host, this one gates the artifact on a host that has the Android
toolchain. Neither requires a device.
"""

from __future__ import annotations

import argparse
import tomllib
import zipfile
from pathlib import Path

APPLICATION_ID = "io.github.mousomer.tet4d.designer"
REQUIRED_MEMBERS = (
    "AndroidManifest.xml",
    "classes.dex",
    "lib/arm64-v8a/libgodot_android.so",
    "lib/arm64-v8a/libtet4d_core.android.template_release.arm64.so",
)
PCK_RESOURCES = (
    b"config/built_in_style_catalog.json",
    b"config/design_scenario_catalog.json",
    b"config/shell_settings_registry.json",
    b"assets/tet4d_bundle/manifest.json",
)
# Upstream Godot template binaries legitimately carry their own build paths.
# Reject host and repository coupling introduced by Tet4D packaging only.
FORBIDDEN_PATH_MARKERS = (
    b"workspace/personal/repos",
    b"/Users/" + b"omer",
)
SIGNING_SUFFIXES = (".RSA", ".DSA", ".EC")


class AndroidPackageError(ValueError):
    """A built APK violates the packaging contract."""


def validate(archive_path: Path, repository_root: Path) -> dict[str, object]:
    version = tomllib.loads(
        (repository_root / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]
    if f"-{version}-android-arm64.apk" not in archive_path.name:
        raise AndroidPackageError("APK filename does not match pyproject.toml version")
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        missing = [name for name in REQUIRED_MEMBERS if name not in names]
        if missing:
            raise AndroidPackageError(f"missing required APK members: {missing}")
        development_only = sorted(
            name for name in names
            if name.endswith((".py", ".pyc", ".gd.uid")) or "/tests/" in name
        )
        if development_only:
            raise AndroidPackageError(f"development-only files entered the APK: {development_only[:5]}")
        # An installable evaluation artifact must be signed. Debug/test signing
        # is acceptable; the key itself is never committed.
        if not any(name.startswith("META-INF/") and name.endswith(SIGNING_SUFFIXES) for name in names):
            raise AndroidPackageError("APK is unsigned and cannot be installed for evaluation")
        pack_members = sorted(name for name in names if name.endswith(".pck"))
        if not pack_members:
            raise AndroidPackageError("APK does not contain a Godot resource pack")
        pack = archive.read(pack_members[0])
        manifest = archive.read("AndroidManifest.xml")
    missing_resources = [resource.decode() for resource in PCK_RESOURCES if resource not in pack]
    if missing_resources:
        raise AndroidPackageError(f"APK resource pack is missing: {missing_resources}")
    # The application ID appears in the binary manifest string pool as UTF-16.
    if APPLICATION_ID.encode("utf-16-le") not in manifest and APPLICATION_ID.encode() not in manifest:
        raise AndroidPackageError(f"APK manifest does not declare {APPLICATION_ID}")
    for marker in FORBIDDEN_PATH_MARKERS:
        if marker in pack:
            raise AndroidPackageError(f"APK contains development-only path marker {marker!r}")
    return {
        "version": version,
        "application_id": APPLICATION_ID,
        "member_count": len(names),
        "archive_bytes": archive_path.stat().st_size,
        "python_runtime_included": False,
        "godot_editor_required": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        result = validate(args.archive.resolve(), args.repository_root.resolve())
    except (OSError, AndroidPackageError, zipfile.BadZipFile) as exc:
        print(f"Android package INVALID: {exc}")
        return 1
    print(
        "Android package VALID: "
        f"{result['application_id']} {result['version']} · "
        f"{result['member_count']} members · {result['archive_bytes']} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
