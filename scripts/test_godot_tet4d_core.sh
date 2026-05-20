#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORE_DIR="$ROOT_DIR/native/tet4d_core"
BUILD_DIR="$CORE_DIR/build/tests"
TEST_BIN="$BUILD_DIR/plain_2d_core_tests"

if [[ -n "${CXX:-}" ]]; then
  CXX_BIN="$CXX"
elif command -v clang++ >/dev/null 2>&1; then
  CXX_BIN="$(command -v clang++)"
elif command -v c++ >/dev/null 2>&1; then
  CXX_BIN="$(command -v c++)"
else
  echo "C++ compiler not found. Install clang++ or set CXX." >&2
  exit 1
fi

mkdir -p "$BUILD_DIR"
"$CXX_BIN" -std=c++17 -Wall -Wextra -Werror \
  -I"$CORE_DIR/include" \
  "$CORE_DIR/src/core/core_api.cpp" \
  "$CORE_DIR/src/core/plain_2d.cpp" \
  "$CORE_DIR/src/core/plain_2d_trace.cpp" \
  "$CORE_DIR/src/core/sha256.cpp" \
  "$CORE_DIR/tests/plain_2d_core_tests.cpp" \
  -o "$TEST_BIN"

"$TEST_BIN" "$@"
