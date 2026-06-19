from __future__ import annotations

import argparse
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
BUNDLE_ROOT = ROOT / "docs" / "governance" / "workspace_bundle"


def _bundle_files() -> list[Path]:
    return sorted(path for path in BUNDLE_ROOT.rglob("*") if path.is_file())


def _target_path(source: Path, target: Path) -> Path:
    return target / source.relative_to(BUNDLE_ROOT)


def _copy_bundle(*, target: Path, force: bool, dry_run: bool) -> int:
    if not BUNDLE_ROOT.is_dir():
        print(f"Missing bundle source: {BUNDLE_ROOT}")
        return 1

    planned = [(source, _target_path(source, target)) for source in _bundle_files()]
    conflicts = [
        destination for _source, destination in planned if destination.exists()
    ]
    if conflicts and not force:
        print("Refusing to overwrite existing bundle files without --force:")
        for destination in conflicts:
            print(f"- {destination}")
        return 1

    action = "Would copy" if dry_run else "Copied"
    for source, destination in planned:
        print(f"{action}: {source.relative_to(BUNDLE_ROOT)} -> {destination}")
        if dry_run:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    print()
    print("Next steps:")
    print("1. Add a project-specific AGENTS.md using AGENTS.template.md.")
    print("2. Add project authority/config/testing overlays.")
    print("3. Add project verification commands.")
    print("4. Link the bundle from the project governance router.")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Copy the reusable workspace governance bundle."
    )
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return _copy_bundle(
        target=args.target.expanduser(),
        force=bool(args.force),
        dry_run=bool(args.dry_run),
    )


if __name__ == "__main__":
    raise SystemExit(main())
