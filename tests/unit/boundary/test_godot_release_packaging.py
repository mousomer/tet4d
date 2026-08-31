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
RELEASE_WORKFLOW = ROOT / ".github/workflows/release-packaging.yml"
PRESENTATION_PROFILE = (
    ROOT / "godot/Tet4D.Godot/scripts/presentation/presentation_profile.gd"
)
DISPOSABLE_PLATFORM_BUILD_SCRIPTS = (
    ROOT / "packaging/godot/build_windows.sh",
    ROOT / "packaging/godot/build_android.sh",
    ROOT / "packaging/godot/build_ipados.sh",
)
NATIVE_SCONSTRUCT = ROOT / "native/tet4d_core/SConstruct"


def _project_version() -> str:
    payload = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(payload["project"]["version"])


def test_godot_release_metadata_is_consistent() -> None:
    version = _project_version()
    project = PROJECT_FILE.read_text(encoding="utf-8")
    preset = EXPORT_PRESETS.read_text(encoding="utf-8")

    assert 'config/name="Tet4D"' in project
    assert f'config/version="{version}"' in project
    assert "config/use_custom_user_dir=true" in project
    assert 'config/custom_user_dir_name="Tet4D"' in project
    assert "textures/vram_compression/import_etc2_astc=true" in project
    assert 'name="macOS Universal"' in preset
    assert 'platform="macOS"' in preset
    assert 'binary_format/architecture="universal"' in preset
    assert 'application/bundle_identifier="io.github.mousomer.tet4d"' in preset
    assert f'application/short_version="{version}"' in preset
    assert f'application/version="{version}"' in preset
    assert 'application/min_macos_version_x86_64="13.0"' in preset
    assert 'application/min_macos_version_arm64="13.0"' in preset
    assert preset.count('exclude_filter=".godot/*,tests/*"') == 4
    assert 'exclude_filter="tests/*"' not in preset


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


def test_presentation_profile_construction_is_independent_of_generated_class_cache() -> (
    None
):
    script = PRESENTATION_PROFILE.read_text(encoding="utf-8")

    assert "PresentationProfile.new()" not in script
    assert (
        'const SCRIPT_PATH := "res://scripts/presentation/presentation_profile.gd"'
        in script
    )
    assert "return load(SCRIPT_PATH).new()" in script


def test_windows_template_output_is_one_absolute_7zip_argument() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "$templateOutput = (Resolve-Path .godot-templates).Path" in workflow
    assert '"-o$templateOutput"' in workflow
    assert " -o.godot-templates " not in workflow


def test_windows_native_build_sanitizes_compiler_and_linker_debug_paths() -> None:
    build = NATIVE_SCONSTRUCT.read_text(encoding="utf-8")

    assert 'if ARGUMENTS.get("use_mingw") == "yes":' in build
    for flag in ["-ffile-prefix-map", "-fdebug-prefix-map", "-fmacro-prefix-map"]:
        assert flag in build
    assert 'CCFLAGS=["/pathmap:{}=.".format(repository_root)]' in build
    assert 'LINKFLAGS=["/PDBALTPATH:%_PDB%"]' in build


def test_android_and_linux_native_archives_use_response_files() -> None:
    build = NATIVE_SCONSTRUCT.read_text(encoding="utf-8")

    assert 'ARGUMENTS.get("platform") in ("android", "linux")' in build
    assert 'bootstrap_env["ARCOM_POSIX"] = bootstrap_env["ARCOM"]' in build
    assert (
        'bootstrap_env["ARCOM"] = "${TEMPFILE(ARCOM_POSIX, ARCOMSTR)}"'
        in build
    )
    response_file_branch = build.split('elif ARGUMENTS.get("platform") == "windows":', 1)[0]
    assert '"windows"' not in response_file_branch


def test_disposable_platform_projects_drop_copied_editor_cache() -> None:
    copy_command = 'cp -R "$PROJECT_DIR/." "$staged_project_root/"'
    cache_removal = 'rm -rf "$staged_project_root/.godot"'

    for path in DISPOSABLE_PLATFORM_BUILD_SCRIPTS:
        script = path.read_text(encoding="utf-8")
        assert copy_command in script
        assert cache_removal in script
        assert script.index(copy_command) < script.index(cache_removal)


def test_android_release_installs_the_binding_owned_ndk_pin() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert 'Path("native/third_party/godot-cpp/tools/android.py")' in workflow
    assert 'values["GODOT_CPP_ANDROID_NDK_VERSION"]' in workflow
    assert (
        'sdkmanager_bin="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"'
        in workflow
    )
    assert 'test -x "$sdkmanager_bin"' in workflow
    assert 'ndk_root="$ANDROID_HOME/ndk/$GODOT_CPP_ANDROID_NDK_VERSION"' in workflow
    assert (
        '"$sdkmanager_bin" "ndk;$GODOT_CPP_ANDROID_NDK_VERSION" >/dev/null'
        in workflow
    )
    assert "yes |" not in workflow
    assert 'test -x "$ndk_root/toolchains/llvm/prebuilt/linux-x86_64/bin/clang"' in workflow
    assert 'ls -d "$ANDROID_HOME"/ndk/*' not in workflow


def test_android_release_creates_native_staging_directory_before_copy() -> None:
    builder = (ROOT / "packaging/godot/build_android.sh").read_text(encoding="utf-8")
    mkdir = 'mkdir -p "$staged_project_root/addons/tet4d_core/bin"'
    copy = 'cp "$native_so" "$staged_project_root/addons/tet4d_core/bin/"'

    assert mkdir in builder
    assert copy in builder
    assert builder.index(mkdir) < builder.index(copy)


def test_ipados_release_assembles_device_and_simulator_xcframework() -> None:
    wrapper = (ROOT / "scripts/build_godot_tet4d_core.sh").read_text(
        encoding="utf-8"
    )
    builder = (ROOT / "packaging/godot/build_ipados.sh").read_text(
        encoding="utf-8"
    )

    assert 'scons_args+=(ios_simulator="$SCONS_IOS_SIMULATOR")' in wrapper
    assert "SCONS_ARCH=arm64 SCONS_TARGET=template_release \\" in builder
    assert 'SCONS_IOS_SIMULATOR=no "$ROOT_DIR/scripts/build_godot_tet4d_core.sh"' in builder
    assert "SCONS_ARCH=universal SCONS_TARGET=template_release \\" in builder
    assert 'SCONS_IOS_SIMULATOR=yes "$ROOT_DIR/scripts/build_godot_tet4d_core.sh"' in builder
    assert 'xcodebuild -create-xcframework \\' in builder
    assert '-library "$native_device_archive"' in builder
    assert '-library "$native_simulator_archive"' in builder
    assert '-output "$native_xcframework"' in builder


def test_ipados_release_creates_native_staging_directory_before_copy() -> None:
    builder = (ROOT / "packaging/godot/build_ipados.sh").read_text(encoding="utf-8")
    mkdir = 'mkdir -p "$staged_project_root/addons/tet4d_core/bin"'
    copy = 'cp -R "$native_xcframework" "$staged_project_root/addons/tet4d_core/bin/"'

    assert mkdir in builder
    assert copy in builder
    assert builder.index(mkdir) < builder.index(copy)


def test_tablet_build_steps_use_unambiguous_shell_blocks() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    for script in ["build_android.sh", "build_ipados.sh"]:
        command = (
            'GODOT_BIN="$GODOT_BIN" '
            'GODOT_TEMPLATE_ROOT="$GODOT_TEMPLATE_ROOT" '
            f"packaging/godot/{script}"
        )
        assert f"run: |\n          {command}" in workflow
        assert f'GODOT_TEMPLATE_ROOT="$GODOT_TEMPLATE_ROOT" \\\n          packaging/godot/{script}' not in workflow
