#!/usr/bin/env python3
"""Structural validation for the current Godot Windows portable package."""

from __future__ import annotations

import argparse
import sys
import tomllib
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from godot_pack import PackFormatError, read_pack_paths_from_bytes

REQUIRED = {
    "Tet4D Designer/Tet4DDesigner.exe",
    "Tet4D Designer/Tet4DDesigner.pck",
    "Tet4D Designer/libtet4d_core.windows.template_release.x86_64.dll",
}
REQUIRED_PCK_RESOURCES = (
    "config/built_in_style_catalog.json",
    "config/design_scenario_catalog.json",
    "assets/tet4d_bundle/manifest.json",
    "assets/icons/tet4d_designer.svg",
    "scripts/ui/design_laboratory_panel.gdc",
)
DESIGNER_IDENTITY_MARKER = "config/tet4d_product_identity/godot_designer.tres.remap"
GAME_IDENTITY_MARKER = "config/tet4d_product_identity/godot_game.tres.remap"
DESIGNER_PRODUCT_NAME = "Tet4D Designer".encode("utf-16-le")
# Official Godot templates can contain upstream compiler source paths in their
# own diagnostic strings. Reject host/repository coupling introduced by Tet4D,
# not reproducible metadata already present in the pinned upstream executable.
FORBIDDEN_PATH_MARKERS = (
    b"/" + b"Users/",
    b"workspace/personal/repos",
    b"\\Users\\",
    b"\\a\\tet4d\\tet4d",
)
MARKER_CONTEXT_BYTES = 96


def _reject_forbidden_path_markers(payloads: dict[str, bytes]) -> None:
    for marker in FORBIDDEN_PATH_MARKERS:
        for member, payload in payloads.items():
            if marker in payload:
                offset = payload.index(marker)
                context_start = max(0, offset - MARKER_CONTEXT_BYTES)
                context_end = min(
                    len(payload), offset + len(marker) + MARKER_CONTEXT_BYTES
                )
                raise ValueError(
                    "package member "
                    f"{member!r} contains development-only absolute path marker "
                    f"{marker!r} at byte {offset}; bounded context "
                    f"{payload[context_start:context_end]!r}"
                )


def _validate_pck_resources(pck: bytes) -> None:
    try:
        resources = set(read_pack_paths_from_bytes(pck))
    except (PackFormatError, UnicodeDecodeError) as exc:
        raise ValueError(f"PCK resource table is invalid: {exc}") from exc
    missing_resources = [resource for resource in REQUIRED_PCK_RESOURCES if resource not in resources]
    if missing_resources:
        raise ValueError(f"PCK resource table is missing: {missing_resources}")
    if DESIGNER_IDENTITY_MARKER not in resources:
        raise ValueError("PCK resource table is missing the Designer identity marker")
    if GAME_IDENTITY_MARKER in resources:
        raise ValueError("PCK resource table carries the Game identity marker")


def _validate_source_version_contract(repository_root: Path, expected_version: str) -> None:
    project_text = (repository_root / "godot/Tet4D.Godot/project.godot").read_text(encoding="utf-8")
    export_text = (repository_root / "godot/Tet4D.Godot/export_presets.cfg").read_text(encoding="utf-8")
    if f'config/version="{expected_version}"' not in project_text:
        raise ValueError("project.godot version disagrees with pyproject.toml")
    if export_text.count(f'="{expected_version}"') < 4:
        raise ValueError("export preset version metadata disagrees with pyproject.toml")


def validate(archive_path: Path, repository_root: Path) -> dict[str, object]:
    expected_version = tomllib.loads((repository_root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    if f"-{expected_version}-windows-x86_64.zip" not in archive_path.name:
        raise ValueError("archive filename does not match pyproject.toml version")
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        missing = REQUIRED - names
        if missing:
            raise ValueError(f"missing required Windows files: {sorted(missing)}")
        forbidden = sorted(
            name for name in names
            if name.endswith((".py", ".pyc", ".gd.uid")) or "/tests/" in name or "/.godot/" in name
        )
        if forbidden:
            raise ValueError(f"development-only files entered package: {forbidden[:5]}")
        payloads = {
            "Tet4D Designer/Tet4DDesigner.exe": archive.read(
                "Tet4D Designer/Tet4DDesigner.exe"
            ),
            "Tet4D Designer/libtet4d_core.windows.template_release.x86_64.dll": archive.read(
                "Tet4D Designer/libtet4d_core.windows.template_release.x86_64.dll"
            ),
            "Tet4D Designer/Tet4DDesigner.pck": archive.read(
                "Tet4D Designer/Tet4DDesigner.pck"
            ),
        }
    executable = payloads["Tet4D Designer/Tet4DDesigner.exe"]
    native_dll = payloads[
        "Tet4D Designer/libtet4d_core.windows.template_release.x86_64.dll"
    ]
    pck = payloads["Tet4D Designer/Tet4DDesigner.pck"]
    if executable[:2] != b"MZ" or native_dll[:2] != b"MZ":
        raise ValueError("Windows executable or GDExtension does not have a PE header")
    if DESIGNER_PRODUCT_NAME not in executable:
        raise ValueError("Windows executable does not carry the Designer product name")
    _validate_pck_resources(pck)
    _reject_forbidden_path_markers(payloads)
    _validate_source_version_contract(repository_root, expected_version)
    return {
        "version": expected_version,
        "file_count": len(names),
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
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Windows package INVALID: {exc}")
        return 1
    print(
        "Windows package VALID: "
        f"Tet4D Designer {result['version']} · {result['file_count']} files · "
        f"{result['archive_bytes']} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
