#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT_CPP_DIR="$ROOT_DIR/native/third_party/godot-cpp"
CORE_DIR="$ROOT_DIR/native/tet4d_core"

if [[ ! -f "$GODOT_CPP_DIR/SConstruct" ]]; then
  git -C "$ROOT_DIR" submodule update --init --recursive native/third_party/godot-cpp
fi

if [[ -n "${SCONS:-}" ]]; then
  read -r -a SCONS_CMD <<< "$SCONS"
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]] && "$ROOT_DIR/.venv/bin/python" -c "import SCons" >/dev/null 2>&1; then
  SCONS_CMD=("$ROOT_DIR/.venv/bin/python" -m SCons)
elif [[ -x "$ROOT_DIR/.venv/bin/scons" ]]; then
  SCONS_CMD=("$ROOT_DIR/.venv/bin/scons")
elif command -v scons >/dev/null 2>&1; then
  SCONS_CMD=("$(command -v scons)")
else
  echo "scons not found. Install it with: .venv/bin/pip install scons" >&2
  exit 1
fi

platform="${SCONS_PLATFORM:-}"
if [[ -z "$platform" ]]; then
  case "$(uname -s)" in
    Darwin) platform="macos" ;;
    Linux) platform="linux" ;;
    MINGW*|MSYS*|CYGWIN*) platform="windows" ;;
    *) echo "Unsupported platform: $(uname -s)" >&2; exit 1 ;;
  esac
fi

arch="${SCONS_ARCH:-}"
if [[ -z "$arch" ]]; then
  case "$(uname -m)" in
    arm64|aarch64) arch="arm64" ;;
    x86_64|amd64) arch="x86_64" ;;
    *) arch="$(uname -m)" ;;
  esac
fi

target="${SCONS_TARGET:-template_debug}"
jobs="${SCONS_JOBS:-$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 2)}"

cd "$CORE_DIR"
"${SCONS_CMD[@]}" platform="$platform" target="$target" arch="$arch" -j "$jobs"
