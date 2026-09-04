#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_DIR="$ROOT_DIR/godot/Tet4D.Godot"
POLICY_PACK="$ROOT_DIR/config/project/policy_pack.json"
OUTPUT_DIR="$ROOT_DIR/artifacts/godot/macos"
APP_PATH="$OUTPUT_DIR/Tet4D.app"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  :
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

if [[ -z "${GODOT_BIN:-}" ]]; then
  GODOT_BIN="$(command -v godot || true)"
fi
if [[ -z "$GODOT_BIN" || ! -x "$GODOT_BIN" ]]; then
  echo "Set GODOT_BIN to the exact supported Godot 4.7.2 executable." >&2
  exit 1
fi

read -r expected_engine project_version template_version <<EOF
$($PYTHON_BIN - "$POLICY_PACK" "$ROOT_DIR/pyproject.toml" <<'PY'
import json
import sys
import tomllib
from pathlib import Path

policy = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
project = tomllib.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
toolchain = policy["governance"]["godot_toolchain"]
print(
    toolchain["build_identifier"],
    project["project"]["version"],
    toolchain["export_templates"]["version_directory"],
)
PY
)
EOF

actual_engine="$($GODOT_BIN --version)"
if [[ "$actual_engine" != "$expected_engine" ]]; then
  echo "Godot version mismatch: expected $expected_engine, got $actual_engine" >&2
  exit 1
fi

SCONS_PLATFORM=macos \
SCONS_ARCH=universal \
SCONS_TARGET=template_release \
SCONS_MACOS_DEPLOYMENT_TARGET=13.0 \
  "$ROOT_DIR/scripts/build_godot_tet4d_core.sh"

release_framework="$PROJECT_DIR/addons/tet4d_core/bin/libtet4d_core.macos.template_release.framework"
release_library="$release_framework/libtet4d_core.macos.template_release"
if [[ ! -f "$release_library" ]]; then
  echo "Release GDExtension was not created: $release_library" >&2
  exit 1
fi
architectures="$(lipo -archs "$release_library")"
if [[ "$architectures" != *arm64* || "$architectures" != *x86_64* ]]; then
  echo "Release GDExtension must be universal; found: $architectures" >&2
  exit 1
fi

framework_plist="$release_framework/Resources/Info.plist"
mkdir -p "$(dirname "$framework_plist")"
plutil -create xml1 "$framework_plist"
plutil -insert CFBundleExecutable -string "$(basename "$release_library")" "$framework_plist"
plutil -insert CFBundleIdentifier -string "io.github.mousomer.tet4d.framework.core" "$framework_plist"
plutil -insert CFBundleInfoDictionaryVersion -string "6.0" "$framework_plist"
plutil -insert CFBundleName -string "Tet4D Core" "$framework_plist"
plutil -insert CFBundlePackageType -string "FMWK" "$framework_plist"
plutil -insert CFBundleShortVersionString -string "$project_version" "$framework_plist"
plutil -insert CFBundleSupportedPlatforms -json '["MacOSX"]' "$framework_plist"
plutil -insert CFBundleVersion -string "$project_version" "$framework_plist"
plutil -insert LSMinimumSystemVersion -string "13.0" "$framework_plist"

mkdir -p "$OUTPUT_DIR"
rm -rf "$APP_PATH"
rm -f "$OUTPUT_DIR/Tet4D-$project_version-macos-universal.zip"

template_source="${GODOT_EXPORT_TEMPLATE_DIR:-$HOME/Library/Application Support/Godot/export_templates/$template_version}"
if [[ ! -f "$template_source/macos.zip" ]]; then
  echo "Godot macOS export template is missing: $template_source/macos.zip" >&2
  exit 1
fi
build_home="$(mktemp -d "/private/tmp/tet4d-release-build.XXXXXX")"
trap 'rm -rf "$build_home"' EXIT
isolated_template_dir="$build_home/Library/Application Support/Godot/export_templates/$template_version"
mkdir -p "$(dirname "$isolated_template_dir")"
ln -s "$template_source" "$isolated_template_dir"
export_project="$build_home/Tet4D.Godot"
mkdir -p "$export_project"
# Import/export against a disposable project copy. A clean Godot 4.7 cache can
# create UID sidecars while scanning; release builds must not dirty the source
# checkout or consume its editor-local .godot state.
rsync -a --exclude '/.godot/' "$PROJECT_DIR/" "$export_project/"
"$PYTHON_BIN" "$ROOT_DIR/packaging/godot/stage_product_profile.py" \
  --repository-root "$ROOT_DIR" --staged-root "$export_project" --product godot_game
grep -Fqx 'run/main_scene="res://scenes/game_bootstrap.tscn"' "$export_project/project.godot"
grep -Fqx 'config/tet4d_product_id="godot_game"' "$export_project/project.godot"

env HOME="$build_home" \
  XDG_CACHE_HOME="$build_home/.cache" \
  XDG_CONFIG_HOME="$build_home/.config" \
  XDG_DATA_HOME="$build_home/.local/share" \
  "$GODOT_BIN" --headless --path "$export_project" \
  --export-release "macOS Universal" "$APP_PATH"

app_binary="$APP_PATH/Contents/MacOS/Tet4D"
info_plist="$APP_PATH/Contents/Info.plist"
packaged_extension="$APP_PATH/Contents/Frameworks/libtet4d_core.macos.template_release.framework/libtet4d_core.macos.template_release"
for required_path in "$app_binary" "$info_plist" "$packaged_extension"; do
  if [[ ! -e "$required_path" ]]; then
    echo "Exported app is missing required path: $required_path" >&2
    exit 1
  fi
done

if [[ "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$info_plist")" != "io.github.mousomer.tet4d" ]]; then
  echo "Exported bundle identifier is incorrect." >&2
  exit 1
fi
if [[ "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleName' "$info_plist")" != "Tet4D" ]]; then
  echo "Exported application name is not the Godot game profile." >&2
  exit 1
fi
if [[ "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$info_plist")" != "$project_version" ]]; then
  echo "Exported bundle version does not match pyproject.toml." >&2
  exit 1
fi
if [[ "$(lipo -archs "$packaged_extension")" != *arm64* || "$(lipo -archs "$packaged_extension")" != *x86_64* ]]; then
  echo "Packaged GDExtension is not universal." >&2
  exit 1
fi

codesign --verify --deep --strict "$APP_PATH"
archive_path="$OUTPUT_DIR/Tet4D-$project_version-macos-universal.zip"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$archive_path"
"$ROOT_DIR/packaging/godot/smoke_macos.sh" "$APP_PATH"

echo "Created $APP_PATH"
echo "Created $archive_path"
