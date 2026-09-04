#!/usr/bin/env bash
set -euo pipefail

# Android tablet Design Laboratory packaging.
#
#   --configuration-only   export and validate the Android resource pack and
#                          export configuration. Needs only the pinned Godot
#                          editor and the Android export templates, so it runs
#                          on any host and is what the verification gate calls.
#   (default)              additionally cross-compile the arm64 GDExtension and
#                          export the signed APK. Needs a Java SDK, the Android
#                          SDK (platform-tools and build-tools), and the NDK.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_DIR="$ROOT_DIR/godot/Tet4D.Godot"
ARTIFACT_DIR="$ROOT_DIR/artifacts/godot/android"
PRESET_NAME="Android Tablet"

CONFIGURATION_ONLY=0
if [[ "${1:-}" == "--configuration-only" ]]; then
  CONFIGURATION_ONLY=1
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

version="$("$PYTHON_BIN" -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])' 2>/dev/null || (cd "$ROOT_DIR" && "$PYTHON_BIN" -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])'))"

template_root="${GODOT_TEMPLATE_ROOT:-}"
if [[ -z "$template_root" ]]; then
  if [[ "$(uname -s)" == "Darwin" ]]; then
    template_root="$HOME/Library/Application Support/Godot/export_templates/4.7.2.stable"
  elif [[ -n "${APPDATA:-}" ]]; then
    template_root="$APPDATA/Godot/export_templates/4.7.2.stable"
  else
    template_root="$HOME/.local/share/godot/export_templates/4.7.2.stable"
  fi
fi
for member in android_debug.apk android_release.apk; do
  if [[ ! -f "$template_root/$member" ]]; then
    echo "Matching Godot 4.7.2 Android export template is missing at $template_root/$member" >&2
    exit 1
  fi
done

export_godot_bin="$GODOT_BIN"
staged_editor_root=""
staged_project_root=""
cleanup() {
  if [[ -n "$staged_editor_root" && -d "$staged_editor_root" ]]; then
    rm -rf "$staged_editor_root"
  fi
  if [[ -n "$staged_project_root" && -d "$staged_project_root" ]]; then
    rm -rf "$staged_project_root"
  fi
}
trap cleanup EXIT

# Godot has no command-line option for an arbitrary export-template root, so a
# temporary self-contained editor copy keeps packaging isolated from the user's
# editor state. Always stage it: the SDK paths and ephemeral debug/test key must
# never be written into a developer's editor settings.
staged_editor_root="$(mktemp -d "${TMPDIR:-/tmp}/tet4d-godot-editor.XXXXXX")"
case "$(uname -s)" in
  Darwin)
    app_bundle="$(cd "$(dirname "$GODOT_BIN")/../.." && pwd)"
    if [[ ! -d "$app_bundle/Contents/MacOS" ]]; then
      echo "GODOT_BIN is not inside a macOS Godot application bundle" >&2
      exit 1
    fi
    cp -R "$app_bundle" "$staged_editor_root/Godot.app"
    export_godot_bin="$staged_editor_root/Godot.app/Contents/MacOS/Godot"
    touch "$staged_editor_root/Godot.app/Contents/MacOS/_sc_"
    ;;
  *)
    export_godot_bin="$staged_editor_root/Godot"
    cp "$GODOT_BIN" "$export_godot_bin"
    touch "$staged_editor_root/_sc_"
    ;;
esac
# A self-contained macOS editor resolves editor_data beside the bundle.
staged_template_root="$staged_editor_root/editor_data/export_templates/4.7.2.stable"
mkdir -p "$staged_template_root"
cp "$template_root/android_debug.apk" "$template_root/android_release.apk" "$staged_template_root/"
if [[ -f "$template_root/android_source.zip" ]]; then
  cp "$template_root/android_source.zip" "$staged_template_root/"
fi

# Export from a disposable project copy. Godot 4.7 may synthesize `.uid`
# sidecars during import; packaging must never dirty the source checkout.
staged_project_root="$(mktemp -d "${TMPDIR:-/tmp}/tet4d-godot-project.XXXXXX")"
cp -R "$PROJECT_DIR/." "$staged_project_root/"
rm -rf "$staged_project_root/.godot"
"$PYTHON_BIN" "$ROOT_DIR/packaging/godot/stage_product_profile.py" \
  --repository-root "$ROOT_DIR" --staged-root "$staged_project_root" --product godot_designer

mkdir -p "$ARTIFACT_DIR"
pack_path="$ARTIFACT_DIR/Tet4D-Designer-$version-android-arm64.pck"
rm -f "$pack_path"
"$export_godot_bin" --headless --path "$staged_project_root" \
  --export-pack "$PRESET_NAME" "$pack_path"
"$PYTHON_BIN" "$ROOT_DIR/packaging/godot/validate_android_export.py" --pack "$pack_path"

if [[ "$CONFIGURATION_ONLY" == "1" ]]; then
  echo "Android export configuration validated: $pack_path"
  exit 0
fi

missing_toolchain=()
if ! java -version >/dev/null 2>&1; then
  missing_toolchain+=("a working Java SDK (java -version must succeed)")
fi
if ! command -v keytool >/dev/null 2>&1; then
  missing_toolchain+=("a Java SDK containing keytool")
fi
android_home="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
if [[ -z "$android_home" || ! -d "$android_home/platform-tools" || ! -d "$android_home/build-tools" ]]; then
  missing_toolchain+=("the Android SDK with platform-tools and build-tools (ANDROID_HOME)")
fi
if [[ -z "${ANDROID_NDK_ROOT:-}" && ( -z "$android_home" || ! -d "$android_home/ndk" ) ]]; then
  missing_toolchain+=("the Android NDK (ANDROID_NDK_ROOT)")
fi
if [[ ${#missing_toolchain[@]} -gt 0 ]]; then
  echo "Cannot build the Android APK. Godot 4.7.2 requires, unconditionally:" >&2
  for item in "${missing_toolchain[@]}"; do
    echo "  - $item" >&2
  done
  echo "Re-run with --configuration-only to validate the export configuration alone." >&2
  exit 1
fi

# Godot's SDK and debug-keystore paths are editor settings. The same ephemeral
# test key is injected into the release fields of the staged export preset,
# because --export-release does not use debug-only signing configuration.
test_keystore="$staged_editor_root/test-release.keystore"
keytool -keyalg RSA -genkeypair -alias androiddebugkey \
  -keypass android -keystore "$test_keystore" -storepass android \
  -dname "CN=Tet4D Test Release,O=Tet4D,C=IE" -validity 1 \
  -deststoretype pkcs12 >/dev/null 2>&1
java_home="${JAVA_HOME:-$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")}"
cat > "$staged_editor_root/editor_data/editor_settings-4.7.tres" <<TRES
[gd_resource type="EditorSettings" format=3]

[resource]
export/android/android_sdk_path = "$android_home"
export/android/java_sdk_path = "$java_home"
export/android/debug_keystore = "$test_keystore"
export/android/debug_keystore_user = "androiddebugkey"
export/android/debug_keystore_pass = "android"
TRES

"$PYTHON_BIN" "$ROOT_DIR/packaging/godot/stage_android_export_preset.py" \
  "$PROJECT_DIR/export_presets.cfg" \
  "$staged_project_root/export_presets.cfg" \
  "$test_keystore"

SCONS_PLATFORM=android SCONS_ARCH=arm64 SCONS_TARGET=template_release \
  "$ROOT_DIR/scripts/build_godot_tet4d_core.sh"

native_so="$PROJECT_DIR/addons/tet4d_core/bin/libtet4d_core.android.template_release.arm64.so"
if [[ ! -f "$native_so" ]]; then
  echo "Android release GDExtension was not produced" >&2
  exit 1
fi
mkdir -p "$staged_project_root/addons/tet4d_core/bin"
cp "$native_so" "$staged_project_root/addons/tet4d_core/bin/"

apk_path="$ARTIFACT_DIR/Tet4D-Designer-$version-android-arm64.apk"
rm -f "$apk_path"
"$export_godot_bin" --headless --path "$staged_project_root" \
  --export-release "$PRESET_NAME" "$apk_path"

"$PYTHON_BIN" "$ROOT_DIR/packaging/godot/validate_android_package.py" "$apk_path"
echo "Android Godot package: $apk_path"
