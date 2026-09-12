#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT_CPP_DIR="$ROOT_DIR/native/third_party/godot-cpp"
CORE_DIR="$ROOT_DIR/native/tet4d_core"

if [[ ! -f "$GODOT_CPP_DIR/SConstruct" ]]; then
  git -C "$ROOT_DIR" submodule update --init --recursive native/third_party/godot-cpp
fi

# SCons is an exactly pinned dev dependency, so it comes from the approved
# interpreter rather than whatever `scons` happens to be on PATH.
if [[ -n "${SCONS:-}" ]]; then
  read -r -a SCONS_CMD <<< "$SCONS"
else
  eval "$("$ROOT_DIR/gov" env)"
  SCONS_PYTHON="$PYTHON_BIN"
  if ! "$SCONS_PYTHON" -c "import SCons" >/dev/null 2>&1; then
    echo "SCons is missing from the approved environment: $SCONS_PYTHON" >&2
    echo "Install it with: $SCONS_PYTHON -m pip install -e \".[dev]\"" >&2
    exit 1
  fi
  SCONS_CMD=("$SCONS_PYTHON" -m SCons)
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
scons_args=(api_version=4.7 platform="$platform" target="$target" arch="$arch")
if [[ -n "${SCONS_DEBUG_SYMBOLS:-}" ]]; then
  scons_args+=(debug_symbols="$SCONS_DEBUG_SYMBOLS")
fi
if [[ "$platform" == "macos" && -n "${SCONS_MACOS_DEPLOYMENT_TARGET:-}" ]]; then
  scons_args+=(macos_deployment_target="$SCONS_MACOS_DEPLOYMENT_TARGET")
fi
if [[ "$platform" == "ios" && -n "${SCONS_IOS_SIMULATOR:-}" ]]; then
  scons_args+=(ios_simulator="$SCONS_IOS_SIMULATOR")
fi
if [[ "$platform" == "windows" && -n "${SCONS_MINGW_PREFIX:-}" ]]; then
  scons_args+=(mingw_prefix="$SCONS_MINGW_PREFIX" use_mingw=yes)
fi

cd "$CORE_DIR"
"${SCONS_CMD[@]}" "${scons_args[@]}" -j "$jobs"
