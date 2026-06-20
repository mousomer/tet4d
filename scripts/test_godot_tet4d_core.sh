#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORE_DIR="$ROOT_DIR/native/tet4d_core"
BUILD_DIR="$CORE_DIR/build/tests"
TEST_2D_BIN="$BUILD_DIR/plain_2d_core_tests"
TEST_ND_BIN="$BUILD_DIR/plain_nd_core_tests"
TEST_TRACE_METADATA_BIN="$BUILD_DIR/trace_metadata_identity_digest_tests"

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
  "$CORE_DIR/src/core/plain_2d_session.cpp" \
  "$CORE_DIR/src/core/plain_2d_trace.cpp" \
  "$CORE_DIR/src/core/sha256.cpp" \
  "$CORE_DIR/tests/plain_2d_core_tests.cpp" \
  -o "$TEST_2D_BIN"

"$CXX_BIN" -std=c++17 -Wall -Wextra -Werror \
  -I"$CORE_DIR/include" \
  "$CORE_DIR/src/core/core_api.cpp" \
  "$CORE_DIR/src/core/plain_nd.cpp" \
  "$CORE_DIR/src/core/plain_nd_session.cpp" \
  "$CORE_DIR/src/core/plain_nd_trace.cpp" \
  "$CORE_DIR/src/core/sha256.cpp" \
  "$CORE_DIR/tests/plain_nd_core_tests.cpp" \
  -o "$TEST_ND_BIN"

"$CXX_BIN" -std=c++17 -Wall -Wextra -Werror \
  -I"$CORE_DIR/include" \
  "$CORE_DIR/src/core/sha256.cpp" \
  "$CORE_DIR/tests/trace_metadata_identity_digest_tests.cpp" \
  -o "$TEST_TRACE_METADATA_BIN"

if [[ "${1:-}" == "--export-plain-2d-trace" ]]; then
  "$TEST_2D_BIN" "$@"
elif [[ "${1:-}" == "--export-plain-nd-trace" ]]; then
  "$TEST_ND_BIN" "$@"
elif [[ "${1:-}" == "--pilot-stable-hash" ]]; then
  "$TEST_2D_BIN" "$@"
elif [[ "${1:-}" == "--trace-metadata-identity-digest" ]]; then
  "$TEST_TRACE_METADATA_BIN" "$@"
else
  "$TEST_2D_BIN" "$@"
  "$TEST_ND_BIN"
fi
