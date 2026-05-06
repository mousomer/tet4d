from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path


def _file_map(root: Path) -> dict[str, Path]:
    return {
        path.relative_to(root).as_posix(): path
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _copy_tree(source_root: Path, target_root: Path) -> list[Path]:
    written: list[Path] = []
    for relative_path, source_path in _file_map(source_root).items():
        target_path = target_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target_path)
        written.append(target_path)
    return written


def _remove_stale_files(source_root: Path, target_root: Path) -> list[Path]:
    source_files = set(_file_map(source_root))
    stale_files: list[Path] = []
    for relative_path, target_path in _file_map(target_root).items():
        if relative_path in source_files:
            continue
        target_path.unlink()
        stale_files.append(target_path)
    for directory in sorted(target_root.rglob("*"), reverse=True):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    return stale_files


def sync_bundle(
    bundle_root: Path, godot_assets_root: Path
) -> tuple[list[Path], list[Path]]:
    if not bundle_root.is_dir():
        raise FileNotFoundError(f"bundle root does not exist: {bundle_root}")
    godot_assets_root.mkdir(parents=True, exist_ok=True)
    removed = _remove_stale_files(bundle_root, godot_assets_root)
    written = _copy_tree(bundle_root, godot_assets_root)
    return written, removed


def compare_bundle(bundle_root: Path, godot_assets_root: Path) -> list[str]:
    if not bundle_root.is_dir():
        return [f"bundle root does not exist: {bundle_root}"]
    if not godot_assets_root.is_dir():
        return [f"godot asset copy does not exist: {godot_assets_root}"]

    failures: list[str] = []
    source_files = _file_map(bundle_root)
    target_files = _file_map(godot_assets_root)
    source_names = set(source_files)
    target_names = set(target_files)

    for missing_name in sorted(source_names - target_names):
        failures.append(
            f"missing godot bundle file: {godot_assets_root / missing_name}"
        )
    for extra_name in sorted(target_names - source_names):
        failures.append(f"stale godot bundle file: {godot_assets_root / extra_name}")
    for common_name in sorted(source_names & target_names):
        if filecmp.cmp(
            source_files[common_name], target_files[common_name], shallow=False
        ):
            continue
        failures.append(f"drifted godot bundle file: {godot_assets_root / common_name}")
    return failures


def check_bundle(bundle_root: Path, godot_assets_root: Path) -> int:
    failures = compare_bundle(bundle_root, godot_assets_root)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(f"godot bundle sync check passed: {godot_assets_root}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Copy the generated tet4d migration bundle into Godot assets."
    )
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--godot-assets", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        return check_bundle(args.bundle, args.godot_assets)

    try:
        written, removed = sync_bundle(args.bundle, args.godot_assets)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    if not args.quiet:
        for path in written:
            print(path)
        for path in removed:
            print(f"removed {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
