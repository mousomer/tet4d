#!/usr/bin/env python3
"""Create and validate a staged Android release-signing export preset.

The canonical preset must remain credential-free. Automated packaging copies
that preset into its disposable Godot project and injects the ephemeral test
keystore only into that staged copy.
"""

from __future__ import annotations

import argparse
import configparser
import shutil
from pathlib import Path

PRESET_NAME = "Android Tablet"
RELEASE_SIGNING_OPTIONS = (
    "keystore/release",
    "keystore/release_user",
    "keystore/release_password",
)
TEST_KEYSTORE_ALIAS = "androiddebugkey"
TEST_KEYSTORE_PASSWORD = "android"


class AndroidSigningStageError(ValueError):
    """The staged preset does not carry valid ephemeral release signing."""


def _load_options(path: Path) -> tuple[configparser.ConfigParser, str]:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    with path.open(encoding="utf-8") as handle:
        parser.read_file(handle)
    for section in parser.sections():
        if parser[section].get("name", "").strip('"') == PRESET_NAME:
            options_section = f"{section}.options"
            if options_section not in parser:
                raise AndroidSigningStageError(
                    f"export preset {PRESET_NAME!r} has no options section"
                )
            return parser, options_section
    raise AndroidSigningStageError(f"export preset {PRESET_NAME!r} is not defined")


def validate_staged_release_signing(
    staged_preset: Path,
    keystore: Path,
    alias: str,
    password: str,
) -> None:
    """Require all release fields; debug-only editor configuration is insufficient."""
    parser, options_section = _load_options(staged_preset)
    options = parser[options_section]
    expected = {
        "keystore/release": str(keystore),
        "keystore/release_user": alias,
        "keystore/release_password": password,
    }
    for option in RELEASE_SIGNING_OPTIONS:
        actual = options.get(option, "").strip('"')
        if actual != expected[option]:
            raise AndroidSigningStageError(
                f"staged Android release export requires {option}; got {actual!r}"
            )


def stage_release_signing(
    source_preset: Path,
    staged_preset: Path,
    keystore: Path,
    alias: str = TEST_KEYSTORE_ALIAS,
    password: str = TEST_KEYSTORE_PASSWORD,
) -> None:
    """Copy the canonical preset and inject test release signing into the copy."""
    if source_preset.resolve() == staged_preset.resolve():
        raise AndroidSigningStageError("refusing to modify the canonical export preset")
    if not keystore.is_file():
        raise AndroidSigningStageError(
            f"ephemeral test keystore is missing: {keystore}"
        )

    source_parser, source_options_section = _load_options(source_preset)
    source_options = source_parser[source_options_section]
    committed = [
        option
        for option in RELEASE_SIGNING_OPTIONS
        if source_options.get(option, "").strip('"')
    ]
    if committed:
        raise AndroidSigningStageError(
            f"canonical Android preset contains release signing material: {committed}"
        )

    staged_preset.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_preset, staged_preset)
    parser, options_section = _load_options(staged_preset)
    options = parser[options_section]
    options["keystore/release"] = f'"{keystore}"'
    options["keystore/release_user"] = f'"{alias}"'
    options["keystore/release_password"] = f'"{password}"'
    with staged_preset.open("w", encoding="utf-8", newline="\n") as handle:
        parser.write(handle, space_around_delimiters=False)
    validate_staged_release_signing(staged_preset, keystore, alias, password)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_preset", type=Path)
    parser.add_argument("staged_preset", type=Path)
    parser.add_argument("keystore", type=Path)
    args = parser.parse_args()
    try:
        stage_release_signing(
            args.source_preset.resolve(),
            args.staged_preset.resolve(),
            args.keystore.resolve(),
        )
    except (OSError, AndroidSigningStageError) as exc:
        print(f"Android staged release signing INVALID: {exc}")
        return 1
    print(
        "Android staged release signing VALID: ephemeral test keystore fields injected"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
