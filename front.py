from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

_MAGIC_EXPORT_KEYS = {
    "__name__",
    "__file__",
    "__package__",
    "__cached__",
    "__loader__",
    "__spec__",
}

_CANONICAL_FRONTENDS = ("main", "2d", "3d", "4d")
_FRONTEND_ALIASES = {
    "front": "main",
}
_FRONTEND_TARGETS = {
    "main": "front.py",
    "2d": "front2d.py",
    "3d": "front3d.py",
    "4d": "front4d.py",
}
_HELP_FLAGS = {"-h", "--h", "--help"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _target_path(target_name: str) -> Path:
    return _repo_root() / "cli" / target_name


def _selector_parser(*, add_help: bool) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        add_help=False,
        allow_abbrev=False,
        description="Root wrapper for tet4d CLI launchers.",
    )
    if add_help:
        parser.add_argument(
            "-h",
            "--h",
            "--help",
            action="help",
            help="show this help message and exit",
        )
    parser.add_argument(
        "--frontend",
        "--mode",
        dest="frontend",
        choices=(*_CANONICAL_FRONTENDS, *_FRONTEND_ALIASES.keys()),
        default="main",
        help="select launcher target (default: main; alias: front=main)",
    )
    return parser


def _export_default_target() -> None:
    exported = runpy.run_path(str(_target_path("front.py")), run_name=__name__)
    for key in _MAGIC_EXPORT_KEYS:
        exported.pop(key, None)
    globals().update(exported)


def _parse_selector(argv: list[str]) -> tuple[str, list[str]]:
    ns, remaining = _selector_parser(add_help=False).parse_known_args(argv)
    selected = _FRONTEND_ALIASES.get(ns.frontend, ns.frontend)
    return _FRONTEND_TARGETS[selected], remaining


def _should_show_help(argv: list[str]) -> bool:
    return any(arg in _HELP_FLAGS for arg in argv)


def _normalize_help_aliases(argv: list[str]) -> list[str]:
    # Forward the wrapper alias `--h` as canonical `--help` to downstream CLI parsers.
    return ["--help" if arg == "--h" else arg for arg in argv]


if __name__ != "__main__":
    _export_default_target()
else:
    argv = _normalize_help_aliases(sys.argv[1:])
    target_name, remaining = _parse_selector(argv)
    if _should_show_help(argv):
        _selector_parser(add_help=True).print_help()
        print()
        print(f"[{Path('cli') / target_name} options]")
    sys.argv = [sys.argv[0], *remaining]
    runpy.run_path(str(_target_path(target_name)), run_name="__main__")
