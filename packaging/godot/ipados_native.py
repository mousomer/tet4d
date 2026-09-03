#!/usr/bin/env python3
"""Assemble and inspect the self-contained Tet4D iOS native distribution."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import subprocess
import tempfile
from collections import Counter
from collections.abc import Callable
from pathlib import Path

DEVICE_ARCHITECTURES = frozenset({"arm64"})
SIMULATOR_ARCHITECTURES = frozenset({"x86_64"})
CommandRunner = Callable[[list[str]], str]


class IpadOsNativeError(ValueError):
    """The iPadOS native distribution violates its binary contract."""


def _run(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise IpadOsNativeError(
            f"native inspection command failed: {command[0]}: {detail.strip()}"
        ) from exc
    return result.stdout


def _lines(command: list[str], runner: CommandRunner) -> list[str]:
    return [line.strip() for line in runner(command).splitlines() if line.strip()]


def architectures(binary: Path, runner: CommandRunner = _run) -> frozenset[str]:
    found = frozenset(_lines(["lipo", "-archs", str(binary)], runner))
    if len(found) == 1 and " " in next(iter(found)):
        found = frozenset(next(iter(found)).split())
    if not found:
        raise IpadOsNativeError(f"could not determine architectures for {binary}")
    return found


def _archive_members(archive: Path, runner: CommandRunner) -> Counter[str]:
    return Counter(
        member
        for member in _lines(["ar", "-t", str(archive)], runner)
        if not member.startswith("__.SYMDEF")
    )


def _symbols(archive: Path, mode: str, runner: CommandRunner) -> set[str]:
    flags = ["-u", "-j"] if mode == "undefined" else ["-gU", "-j"]
    return set(_lines(["nm", *flags, str(archive)], runner))


def _is_godot_cpp_symbol(symbol: str) -> bool:
    return symbol.startswith("__Z") and "N5godot" in symbol


def combine_archives(
    tet4d_archive: Path,
    godot_cpp_archive: Path,
    output_archive: Path,
    expected_architecture: str,
    runner: CommandRunner = _run,
) -> dict[str, object]:
    """Combine thin archives and prove members and required symbols survive."""
    expected = frozenset({expected_architecture})
    for label, archive in (
        ("Tet4D", tet4d_archive),
        ("godot-cpp", godot_cpp_archive),
    ):
        actual = architectures(archive, runner)
        if actual != expected:
            raise IpadOsNativeError(
                f"{label} archive {archive} has {sorted(actual)}, expected {sorted(expected)}"
            )

    tet4d_members = _archive_members(tet4d_archive, runner)
    godot_cpp_members = _archive_members(godot_cpp_archive, runner)
    expected_members = tet4d_members + godot_cpp_members
    if not tet4d_members or not godot_cpp_members:
        raise IpadOsNativeError("both input archives must contain object members")

    tet4d_undefined = _symbols(tet4d_archive, "undefined", runner)
    godot_cpp_defined = _symbols(godot_cpp_archive, "defined", runner)
    required = tet4d_undefined & godot_cpp_defined
    if not required:
        raise IpadOsNativeError(
            "Tet4D archive exposes no dependency satisfied by the godot-cpp archive"
        )

    output_archive.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=output_archive.name + ".", suffix=".tmp", dir=output_archive.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    temporary.unlink()
    try:
        runner(
            [
                "xcrun",
                "libtool",
                "-static",
                str(tet4d_archive),
                str(godot_cpp_archive),
                "-o",
                str(temporary),
            ]
        )
        actual_members = _archive_members(temporary, runner)
        if actual_members != expected_members:
            missing = list((expected_members - actual_members).elements())[:5]
            extra = list((actual_members - expected_members).elements())[:5]
            raise IpadOsNativeError(
                f"combined archive member mismatch; missing={missing}, extra={extra}"
            )
        actual_architectures = architectures(temporary, runner)
        if actual_architectures != expected:
            raise IpadOsNativeError(
                f"combined archive has {sorted(actual_architectures)}, expected {sorted(expected)}"
            )
        combined_defined = _symbols(temporary, "defined", runner)
        missing_symbols = sorted(required - combined_defined)
        if missing_symbols:
            raise IpadOsNativeError(
                f"combined archive lost required godot-cpp symbols: {missing_symbols[:5]}"
            )
        unresolved = _symbols(temporary, "undefined", runner) - combined_defined
        unresolved_godot = sorted(
            symbol for symbol in unresolved if _is_godot_cpp_symbol(symbol)
        )
        if unresolved_godot:
            raise IpadOsNativeError(
                f"combined archive leaves godot-cpp symbols unresolved: {unresolved_godot[:5]}"
            )
        os.replace(temporary, output_archive)
    finally:
        temporary.unlink(missing_ok=True)

    return {
        "architecture": expected_architecture,
        "tet4d_members": sum(tet4d_members.values()),
        "godot_cpp_members": sum(godot_cpp_members.values()),
        "combined_members": sum(expected_members.values()),
        "required_godot_cpp_symbols": len(required),
    }


def _ios_slices(framework: Path) -> list[dict[str, object]]:
    plist_path = framework / "Info.plist"
    if not plist_path.is_file():
        raise IpadOsNativeError(f"XCFramework has no Info.plist: {framework}")
    with plist_path.open("rb") as handle:
        payload = plistlib.load(handle)
    slices = [
        item
        for item in payload.get("AvailableLibraries", [])
        if item.get("SupportedPlatform") == "ios"
    ]
    if not slices:
        raise IpadOsNativeError(f"XCFramework contains no iOS slices: {framework}")
    return slices


def _validate_godot_cpp_symbols(
    binary: Path, label: str, runner: CommandRunner
) -> None:
    defined = _symbols(binary, "defined", runner)
    unresolved = _symbols(binary, "undefined", runner) - defined
    unresolved_godot = sorted(
        symbol for symbol in unresolved if _is_godot_cpp_symbol(symbol)
    )
    godot_definitions = [symbol for symbol in defined if _is_godot_cpp_symbol(symbol)]
    if unresolved_godot:
        raise IpadOsNativeError(
            f"{label} leaves godot-cpp symbols unresolved: {unresolved_godot[:5]}"
        )
    if not godot_definitions:
        raise IpadOsNativeError(f"{label} contains no godot-cpp definitions")


def validate_xcframework(
    framework: Path,
    *,
    exact_device: frozenset[str] | None = None,
    exact_simulator: frozenset[str] | None = None,
    require_device: frozenset[str] = DEVICE_ARCHITECTURES,
    require_simulator: frozenset[str] = SIMULATOR_ARCHITECTURES,
    require_godot_cpp: bool = False,
    runner: CommandRunner = _run,
) -> dict[str, list[str]]:
    """Validate iOS XCFramework metadata against every contained binary."""
    observed: dict[str, list[str]] = {}
    variants: set[str] = set()
    for item in _ios_slices(framework):
        variant = (
            "simulator"
            if item.get("SupportedPlatformVariant") == "simulator"
            else "device"
        )
        if variant in variants:
            raise IpadOsNativeError(f"XCFramework has duplicate {variant} slices")
        variants.add(variant)
        identifier = str(item.get("LibraryIdentifier", ""))
        library_path = str(item.get("LibraryPath", ""))
        binary = framework / identifier / library_path
        if not binary.is_file():
            raise IpadOsNativeError(f"XCFramework slice binary is missing: {binary}")
        metadata = frozenset(
            str(value) for value in item.get("SupportedArchitectures", [])
        )
        actual = architectures(binary, runner)
        if metadata != actual:
            raise IpadOsNativeError(
                f"{framework.name} {variant} metadata {sorted(metadata)} "
                f"does not match binary {sorted(actual)}"
            )
        required = require_simulator if variant == "simulator" else require_device
        exact = exact_simulator if variant == "simulator" else exact_device
        if not required <= actual:
            raise IpadOsNativeError(
                f"{framework.name} {variant} lacks required architectures {sorted(required)}"
            )
        if exact is not None and actual != exact:
            raise IpadOsNativeError(
                f"{framework.name} {variant} has {sorted(actual)}, expected {sorted(exact)}"
            )
        if require_godot_cpp:
            _validate_godot_cpp_symbols(binary, f"{framework.name} {variant}", runner)
        observed[variant] = sorted(actual)
    if variants != {"device", "simulator"}:
        raise IpadOsNativeError(
            f"XCFramework must contain device and simulator slices, got {sorted(variants)}"
        )
    return observed


def normalize_pinned_godot_engine(
    framework: Path, runner: CommandRunner = _run
) -> dict[str, list[str]]:
    """Correct the pinned engine's inaccurate simulator slice metadata."""
    plist_path = framework / "Info.plist"
    with plist_path.open("rb") as handle:
        payload = plistlib.load(handle)
    simulator = next(
        (
            item
            for item in payload.get("AvailableLibraries", [])
            if item.get("SupportedPlatform") == "ios"
            and item.get("SupportedPlatformVariant") == "simulator"
        ),
        None,
    )
    if simulator is None:
        raise IpadOsNativeError("pinned Godot XCFramework has no iOS simulator slice")
    old_identifier = str(simulator["LibraryIdentifier"])
    library_path = str(simulator["LibraryPath"])
    old_directory = framework / old_identifier
    actual = architectures(old_directory / library_path, runner)
    if actual != SIMULATOR_ARCHITECTURES:
        raise IpadOsNativeError(
            f"pinned Godot simulator binary has {sorted(actual)}, expected x86_64"
        )
    new_identifier = "ios-x86_64-simulator"
    new_directory = framework / new_identifier
    if old_identifier != new_identifier:
        if new_directory.exists():
            raise IpadOsNativeError(
                f"normalized simulator directory already exists: {new_directory}"
            )
        old_directory.rename(new_directory)
    simulator["LibraryIdentifier"] = new_identifier
    simulator["SupportedArchitectures"] = sorted(SIMULATOR_ARCHITECTURES)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix="Info.plist.", suffix=".tmp", dir=framework
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with temporary.open("wb") as handle:
            plistlib.dump(payload, handle, sort_keys=False)
        os.replace(temporary, plist_path)
    finally:
        temporary.unlink(missing_ok=True)
    return validate_xcframework(
        framework,
        exact_device=DEVICE_ARCHITECTURES,
        exact_simulator=SIMULATOR_ARCHITECTURES,
        runner=runner,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    combine = subparsers.add_parser("combine")
    combine.add_argument("--tet4d", type=Path, required=True)
    combine.add_argument("--godot-cpp", type=Path, required=True)
    combine.add_argument("--output", type=Path, required=True)
    combine.add_argument("--architecture", choices=("arm64", "x86_64"), required=True)
    inspect = subparsers.add_parser("inspect-xcframework")
    inspect.add_argument("framework", type=Path)
    inspect.add_argument("--require-godot-cpp", action="store_true")
    normalize = subparsers.add_parser("normalize-godot-engine")
    normalize.add_argument("framework", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "combine":
            result = combine_archives(
                args.tet4d, args.godot_cpp, args.output, args.architecture
            )
        elif args.command == "normalize-godot-engine":
            result = normalize_pinned_godot_engine(args.framework)
        else:
            result = validate_xcframework(
                args.framework,
                exact_device=DEVICE_ARCHITECTURES,
                exact_simulator=SIMULATOR_ARCHITECTURES,
                require_godot_cpp=args.require_godot_cpp,
            )
    except (OSError, IpadOsNativeError, plistlib.InvalidFileException) as exc:
        parser.exit(1, f"iPadOS native artifact INVALID: {exc}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
