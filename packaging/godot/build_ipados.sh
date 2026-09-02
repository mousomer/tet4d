#!/usr/bin/env bash
set -euo pipefail

# iPadOS Design Laboratory packaging.
#
#   --configuration-only   export and validate the Xcode project without the
#                          iOS GDExtension. Needs only the pinned Godot editor
#                          and the iOS export template, so it runs on any macOS
#                          host and is what the verification gate calls. The
#                          exported project is structurally complete but the
#                          application cannot run without its native core.
#   (default)              additionally cross-compile the iOS GDExtension and
#                          build the exported project. Needs full Xcode with
#                          the iPhoneOS SDK; Command Line Tools alone are not
#                          enough.
#
# Signing material is never committed. Set TET4D_IOS_TEAM_ID to your own Apple
# Developer team identifier to replace the repository placeholder; device
# signing additionally needs a provisioning profile configured in Xcode.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_DIR="$ROOT_DIR/godot/Tet4D.Godot"
ARTIFACT_BASE_DIR="$ROOT_DIR/artifacts/godot/ipad"
PRESET_NAME="iPadOS"
PLACEHOLDER_TEAM_ID="0000000000"

CONFIGURATION_ONLY=0
if [[ "${1:-}" == "--configuration-only" ]]; then
  CONFIGURATION_ONLY=1
fi
if [[ "$CONFIGURATION_ONLY" == "1" ]]; then
  ARTIFACT_MODE="configuration"
else
  ARTIFACT_MODE="release"
fi
ARTIFACT_DIR="$ARTIFACT_BASE_DIR/$ARTIFACT_MODE-export"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "The iPadOS target can only be exported from macOS" >&2
  exit 1
fi

if [[ -z "${GODOT_BIN:-}" || ! -x "$GODOT_BIN" ]]; then
  echo "GODOT_BIN must name the exact pinned Godot editor executable" >&2
  exit 1
fi

actual_version="$($GODOT_BIN --version | head -n 1 | tr -d '\r')"
if [[ "$actual_version" != "4.7.2.stable.official.ed1daf0bf" ]]; then
  echo "Expected Godot 4.7.2.stable.official.ed1daf0bf, got $actual_version" >&2
  exit 1
fi

if [[ -n "${PYTHON_BIN:-}" ]]; then
  :
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

version="$(cd "$ROOT_DIR" && "$PYTHON_BIN" -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"

template_root="${GODOT_TEMPLATE_ROOT:-$HOME/Library/Application Support/Godot/export_templates/4.7.2.stable}"
if [[ ! -f "$template_root/ios.zip" ]]; then
  echo "Matching Godot 4.7.2 iOS export template is missing at $template_root/ios.zip" >&2
  exit 1
fi

staged_editor_root=""
staged_native_root=""
staged_project_root=""
export_godot_bin="$GODOT_BIN"
cleanup() {
  if [[ -n "$staged_editor_root" && -d "$staged_editor_root" ]]; then
    rm -rf "$staged_editor_root"
  fi
  if [[ -n "$staged_project_root" && -d "$staged_project_root" ]]; then
    rm -rf "$staged_project_root"
  fi
  if [[ -n "$staged_native_root" && -d "$staged_native_root" ]]; then
    rm -rf "$staged_native_root"
  fi
}
trap cleanup EXIT

if [[ -n "${GODOT_TEMPLATE_ROOT:-}" ]]; then
  staged_editor_root="$(mktemp -d "${TMPDIR:-/tmp}/tet4d-godot-editor.XXXXXX")"
  app_bundle="$(cd "$(dirname "$GODOT_BIN")/../.." && pwd)"
  if [[ ! -d "$app_bundle/Contents/MacOS" ]]; then
    echo "GODOT_BIN is not inside a macOS Godot application bundle" >&2
    exit 1
  fi
  cp -R "$app_bundle" "$staged_editor_root/Godot.app"
  export_godot_bin="$staged_editor_root/Godot.app/Contents/MacOS/Godot"
  touch "$staged_editor_root/Godot.app/Contents/MacOS/_sc_"
  staged_template_root="$staged_editor_root/editor_data/export_templates/4.7.2.stable"
  mkdir -p "$staged_template_root"
  cp "$template_root/ios.zip" "$staged_template_root/"
  if [[ -f "$template_root/version.txt" ]]; then
    cp "$template_root/version.txt" "$staged_template_root/"
  fi
fi

# Export from a disposable project copy. Godot 4.7 may synthesize `.uid`
# sidecars during import; packaging must never dirty the source checkout.
staged_project_root="$(mktemp -d "${TMPDIR:-/tmp}/tet4d-godot-project.XXXXXX")"
cp -R "$PROJECT_DIR/." "$staged_project_root/"
rm -rf "$staged_project_root/.godot"
# Never let a stale or pre-combination iOS archive from the ignored source bin
# enter the disposable export project.
staged_native_bin="$staged_project_root/addons/tet4d_core/bin"
if [[ -d "$staged_native_bin" ]]; then
  find "$staged_native_bin" -maxdepth 1 \
    -name 'libtet4d_core.ios.*' -exec rm -rf {} +
fi

if [[ -n "${TET4D_IOS_TEAM_ID:-}" ]]; then
  "$PYTHON_BIN" - "$staged_project_root/export_presets.cfg" "$PLACEHOLDER_TEAM_ID" "$TET4D_IOS_TEAM_ID" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
path.write_text(
    path.read_text(encoding="utf-8").replace(
        f'application/app_store_team_id="{sys.argv[2]}"',
        f'application/app_store_team_id="{sys.argv[3]}"',
    ),
    encoding="utf-8",
)
PY
fi

if [[ "$CONFIGURATION_ONLY" == "1" ]]; then
  # Without the iPhoneOS SDK the iOS GDExtension cannot be compiled, and Godot
  # treats a declared-but-absent library as a hard export error. Drop the iOS
  # entries from the disposable copy only, so the committed descriptor keeps
  # declaring them and the gap stays visible in the validator output.
  "$PYTHON_BIN" - "$staged_project_root/addons/tet4d_core/tet4d_core.gdextension" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
path.write_text(
    "".join(
        line for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
        if not line.startswith("ios.")
    ),
    encoding="utf-8",
)
PY
else
  if ! xcodebuild -version >/dev/null 2>&1; then
    echo "Building the iPadOS application needs full Xcode; Command Line Tools alone" >&2
    echo "cannot provide the iPhoneOS SDK. Install Xcode, run" >&2
    echo "  sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer" >&2
    echo "or re-run with --configuration-only to export and validate the Xcode project." >&2
    exit 1
  fi
  native_device_archive="$PROJECT_DIR/addons/tet4d_core/bin/libtet4d_core.ios.template_release.a"
  native_simulator_archive="$PROJECT_DIR/addons/tet4d_core/bin/libtet4d_core.ios.template_release.simulator.a"
  native_xcframework="$PROJECT_DIR/addons/tet4d_core/bin/libtet4d_core.ios.template_release.xcframework"
  godot_cpp_device_archive="$ROOT_DIR/native/third_party/godot-cpp/bin/libgodot-cpp.ios.template_release.arm64.a"
  godot_cpp_simulator_archive="$ROOT_DIR/native/third_party/godot-cpp/bin/libgodot-cpp.ios.template_release.x86_64.simulator.a"
  staged_native_root="$(mktemp -d "${TMPDIR:-/tmp}/tet4d-ipados-native.XXXXXX")"
  tet4d_device_archive="$staged_native_root/libtet4d_core.ios.template_release.tet4d-only.a"
  tet4d_simulator_archive="$staged_native_root/libtet4d_core.ios.template_release.tet4d-only.simulator.a"
  rm -f "$native_device_archive" "$native_simulator_archive"
  rm -rf "$native_xcframework"
  SCONS_PLATFORM=ios SCONS_ARCH=arm64 SCONS_TARGET=template_release \
    SCONS_IOS_SIMULATOR=no "$ROOT_DIR/scripts/build_godot_tet4d_core.sh"
  if [[ ! -f "$native_device_archive" || ! -f "$godot_cpp_device_archive" ]]; then
    echo "iPadOS device Tet4D and godot-cpp archives were not produced" >&2
    exit 1
  fi
  mv "$native_device_archive" "$tet4d_device_archive"
  "$PYTHON_BIN" "$ROOT_DIR/packaging/godot/ipados_native.py" combine \
    --tet4d "$tet4d_device_archive" \
    --godot-cpp "$godot_cpp_device_archive" \
    --output "$native_device_archive" \
    --architecture arm64

  SCONS_PLATFORM=ios SCONS_ARCH=x86_64 SCONS_TARGET=template_release \
    SCONS_IOS_SIMULATOR=yes "$ROOT_DIR/scripts/build_godot_tet4d_core.sh"
  if [[ ! -f "$native_simulator_archive" || ! -f "$godot_cpp_simulator_archive" ]]; then
    echo "iPadOS simulator Tet4D and godot-cpp archives were not produced" >&2
    exit 1
  fi
  mv "$native_simulator_archive" "$tet4d_simulator_archive"
  "$PYTHON_BIN" "$ROOT_DIR/packaging/godot/ipados_native.py" combine \
    --tet4d "$tet4d_simulator_archive" \
    --godot-cpp "$godot_cpp_simulator_archive" \
    --output "$native_simulator_archive" \
    --architecture x86_64

  xcodebuild -create-xcframework \
    -library "$native_device_archive" \
    -library "$native_simulator_archive" \
    -output "$native_xcframework"
  if [[ ! -d "$native_xcframework" ]]; then
    echo "iPadOS release GDExtension was not produced" >&2
    exit 1
  fi
  "$PYTHON_BIN" "$ROOT_DIR/packaging/godot/ipados_native.py" \
    inspect-xcframework "$native_xcframework" --require-godot-cpp
  mkdir -p "$staged_project_root/addons/tet4d_core/bin"
  cp -R "$native_xcframework" "$staged_project_root/addons/tet4d_core/bin/"
fi

rm -rf "$ARTIFACT_DIR"
mkdir -p "$ARTIFACT_DIR"
"$export_godot_bin" --headless --path "$staged_project_root" \
  --export-release "$PRESET_NAME" "$ARTIFACT_DIR/Tet4DDesigner.xcodeproj"

if [[ "$CONFIGURATION_ONLY" != "1" ]]; then
  # Godot 4.7.2 labels its simulator engine slice arm64+x86_64 even though the
  # shipped libgodot.a is x86_64-only. Make the exported artifact truthful
  # before validation and Xcode slice selection.
  "$PYTHON_BIN" "$ROOT_DIR/packaging/godot/ipados_native.py" \
    normalize-godot-engine "$ARTIFACT_DIR/Tet4DDesigner.xcframework"
fi

validator_args=("$ARTIFACT_DIR" "--artifact-mode" "$ARTIFACT_MODE")
"$PYTHON_BIN" "$ROOT_DIR/packaging/godot/validate_ipados_project.py" "${validator_args[@]}"

if [[ "$CONFIGURATION_ONLY" == "1" ]]; then
  echo "iPadOS configuration export generated and validated: $ARTIFACT_DIR"
  echo "This is configuration evidence, not a release payload."
  echo "Open Tet4DDesigner.xcodeproj in Xcode to build, sign, and install."
  exit 0
fi

# An unsigned simulator build proves the exported project compiles without
# requiring any signing credential.
XCODE_DERIVED_DATA_DIR="$ARTIFACT_BASE_DIR/xcode-derived-data"
rm -rf "$XCODE_DERIVED_DATA_DIR"
xcodebuild -project "$ARTIFACT_DIR/Tet4DDesigner.xcodeproj" \
  -scheme Tet4DDesigner -sdk iphonesimulator -configuration Release \
  -derivedDataPath "$XCODE_DERIVED_DATA_DIR" \
  ARCHS=x86_64 ONLY_ACTIVE_ARCH=YES CODE_SIGNING_ALLOWED=NO build

archive_path="$ARTIFACT_BASE_DIR/Tet4D-Designer-$version-ipados-xcodeproject.zip"
rm -f "$archive_path"
"$PYTHON_BIN" - "$ARTIFACT_DIR" "$archive_path" <<'PY'
from pathlib import Path
import sys
import zipfile

project_dir = Path(sys.argv[1])
archive_path = Path(sys.argv[2])
with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(project_dir.rglob("*")):
        if path.is_file() and path != archive_path:
            archive.write(path, Path("Tet4D-Designer-iPadOS") / path.relative_to(project_dir))
PY
echo "iPadOS Xcode project: $archive_path"
