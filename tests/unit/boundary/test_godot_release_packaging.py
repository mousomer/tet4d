"""Release-boundary contracts for the current Godot package."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECT_FILE = ROOT / "godot/Tet4D.Godot/project.godot"
EXPORT_PRESETS = ROOT / "godot/Tet4D.Godot/export_presets.cfg"
BUILD_SCRIPT = ROOT / "packaging/godot/build_macos.sh"
SMOKE_SCRIPT = ROOT / "packaging/godot/smoke_macos.sh"


def _project_version() -> str:
    payload = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(payload["project"]["version"])


def test_godot_release_metadata_is_consistent() -> None:
    version = _project_version()
    project = PROJECT_FILE.read_text(encoding="utf-8")
    preset = EXPORT_PRESETS.read_text(encoding="utf-8")

    assert 'config/name="Tet4D"' in project
    assert f'config/version="{version}"' in project
    assert 'config/use_custom_user_dir=true' in project
    assert 'config/custom_user_dir_name="Tet4D"' in project
    assert 'textures/vram_compression/import_etc2_astc=true' in project
    assert 'name="macOS Universal"' in preset
    assert 'platform="macOS"' in preset
    assert 'binary_format/architecture="universal"' in preset
    assert 'application/bundle_identifier="io.github.mousomer.tet4d"' in preset
    assert f'application/short_version="{version}"' in preset
    assert f'application/version="{version}"' in preset
    assert 'application/min_macos_version_x86_64="13.0"' in preset
    assert 'application/min_macos_version_arm64="13.0"' in preset
    assert 'exclude_filter="tests/*"' in preset


def test_godot_macos_build_checks_release_boundary() -> None:
    script = BUILD_SCRIPT.read_text(encoding="utf-8")

    for token in [
        "SCONS_ARCH=universal",
        "SCONS_TARGET=template_release",
        "SCONS_MACOS_DEPLOYMENT_TARGET=13.0",
        "GODOT_EXPORT_TEMPLATE_DIR",
        'env HOME="$build_home"',
        "rsync -a --exclude '/.godot/'",
        '--path "$export_project"',
        "framework_plist=",
        "CFBundleSupportedPlatforms",
        'LSMinimumSystemVersion -string "13.0"',
        '--export-release "macOS Universal"',
        "libtet4d_core.macos.template_release.framework",
        "CFBundleIdentifier",
        "CFBundleShortVersionString",
        "codesign --verify --deep --strict",
        "ditto -c -k --sequesterRsrc --keepParent",
        "packaging/godot/smoke_macos.sh",
    ]:
        assert token in script
    assert ("/" + "Users/") not in script
    assert not re.search(r"[A-Za-z]:\\\\", script)


def test_exported_app_smoke_is_outside_tree_and_isolated() -> None:
    script = SMOKE_SCRIPT.read_text(encoding="utf-8")

    for token in [
        'mktemp -d "/private/tmp/tet4d-release-smoke.',
        'ditto "$APP_PATH" "$staged_app"',
        "for run_number in 1 2",
        'HOME="$user_root/home"',
        'XDG_CACHE_HOME="$user_root/cache"',
        'XDG_CONFIG_HOME="$user_root/config"',
        'XDG_DATA_HOME="$user_root/data"',
        "--headless --quit-after 8",
        "SCRIPT ERROR|ERROR:",
    ]:
        assert token in script
    assert ("/" + "Users/") not in script
    assert not re.search(r"[A-Za-z]:\\\\", script)
