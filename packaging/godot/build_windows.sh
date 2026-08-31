#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_DIR="$ROOT_DIR/godot/Tet4D.Godot"
ARTIFACT_DIR="$ROOT_DIR/artifacts/godot/windows"
APP_DIR="$ARTIFACT_DIR/Tet4D Designer"

if [[ -z "${GODOT_BIN:-}" || ! -x "$GODOT_BIN" ]]; then
  echo "GODOT_BIN must name the exact pinned Godot editor executable" >&2
  exit 1
fi

actual_version="$($GODOT_BIN --version | head -n 1 | tr -d '\r')"
if [[ "$actual_version" != "4.7.2.stable.official.ed1daf0bf" ]]; then
  echo "Expected Godot 4.7.2.stable.official.ed1daf0bf, got $actual_version" >&2
  exit 1
fi

version="$(cd "$ROOT_DIR" && python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"

if [[ "$(uname -s)" == "Darwin" && -z "${SCONS_MINGW_PREFIX:-}" ]]; then
  if command -v x86_64-w64-mingw32-g++ >/dev/null 2>&1; then
    compiler_path="$(command -v x86_64-w64-mingw32-g++)"
    SCONS_MINGW_PREFIX="$(cd "$(dirname "$compiler_path")/.." && pwd)"
    export SCONS_MINGW_PREFIX
  else
    echo "A MinGW-w64 cross compiler is required for a Windows release DLL" >&2
    exit 1
  fi
fi

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
if [[ ! -f "$template_root/windows_release_x86_64.exe" ]]; then
  echo "Matching Godot 4.7.2 Windows export template is missing at $template_root" >&2
  exit 1
fi

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

# Godot has no command-line option for an arbitrary export-template root. On
# macOS, keep local/CI packaging isolated from the user's editor state by
# running a temporary self-contained copy of the pinned editor.
if [[ -n "${GODOT_TEMPLATE_ROOT:-}" ]]; then
  staged_editor_root="$(mktemp -d "${TMPDIR:-/tmp}/tet4d-godot-editor.XXXXXX")"
  case "$(uname -s)" in
    Darwin)
      app_bundle="$(cd "$(dirname "$GODOT_BIN")/../.." && pwd)"
      if [[ ! -d "$app_bundle/Contents/MacOS" ]]; then
        echo "GODOT_BIN is not inside a macOS Godot application bundle" >&2
        exit 1
      fi
      cp -R "$app_bundle" "$staged_editor_root/Godot.app"
      staged_bin_dir="$staged_editor_root/Godot.app/Contents/MacOS"
      export_godot_bin="$staged_bin_dir/Godot"
      ;;
    MINGW*|MSYS*|CYGWIN*)
      staged_bin_dir="$staged_editor_root"
      export_godot_bin="$staged_bin_dir/Godot.exe"
      cp "$GODOT_BIN" "$export_godot_bin"
      ;;
    *)
      staged_bin_dir="$staged_editor_root"
      export_godot_bin="$staged_bin_dir/Godot"
      cp "$GODOT_BIN" "$export_godot_bin"
      ;;
  esac
  touch "$staged_bin_dir/_sc_"
  staged_template_root="$staged_editor_root/editor_data/export_templates/4.7.2.stable"
  mkdir -p "$staged_template_root"
  cp "$template_root/windows_debug_x86_64.exe" \
    "$template_root/windows_release_x86_64.exe" "$staged_template_root/"
fi

SCONS_PLATFORM=windows SCONS_ARCH=x86_64 SCONS_TARGET=template_release \
  "$ROOT_DIR/scripts/build_godot_tet4d_core.sh"

native_dll="$PROJECT_DIR/addons/tet4d_core/bin/libtet4d_core.windows.template_release.x86_64.dll"
if [[ ! -f "$native_dll" ]]; then
  echo "Windows release GDExtension was not produced" >&2
  exit 1
fi

# Export from a disposable project copy. Godot 4.7 may synthesize `.uid`
# sidecars during import; packaging must never dirty the source checkout.
staged_project_root="$(mktemp -d "${TMPDIR:-/tmp}/tet4d-godot-project.XXXXXX")"
cp -R "$PROJECT_DIR/." "$staged_project_root/"
rm -rf "$staged_project_root/.godot"

rm -rf "$ARTIFACT_DIR"
mkdir -p "$APP_DIR"
"$export_godot_bin" --headless --path "$staged_project_root" \
  --export-release "Windows x86_64" "$APP_DIR/Tet4DDesigner.exe"

zip_path="$ARTIFACT_DIR/Tet4D-Designer-$version-windows-x86_64.zip"
python3 - "$APP_DIR" "$zip_path" <<'PY'
from pathlib import Path
import sys
import zipfile

app_dir = Path(sys.argv[1])
zip_path = Path(sys.argv[2])
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(app_dir.rglob("*")):
        if path.is_file():
            archive.write(path, Path(app_dir.name) / path.relative_to(app_dir))
PY

python3 "$ROOT_DIR/packaging/godot/validate_windows_package.py" "$zip_path"
echo "Windows Godot package: $zip_path"
