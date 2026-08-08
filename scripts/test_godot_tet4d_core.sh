#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORE_DIR="$ROOT_DIR/native/tet4d_core"
BUILD_DIR="$CORE_DIR/build/tests"
TEST_2D_BIN="$BUILD_DIR/plain_2d_core_tests"
TEST_ND_BIN="$BUILD_DIR/plain_nd_core_tests"
TEST_GEOMETRY_BIN="$BUILD_DIR/geometry_core_tests"
TEST_QUERY_BIN="$BUILD_DIR/query_core_tests"
TEST_TRACE_METADATA_BIN="$BUILD_DIR/trace_metadata_identity_digest_tests"
TEST_TOPOLOGY_CONTRACT_BIN="$BUILD_DIR/topology_contract_foundation_tests"
TEST_TOPOLOGY_TRANSPORT_BIN="$BUILD_DIR/topology_transport_tests"
TEST_BOARD_EXTENT_BIN="$BUILD_DIR/board_extent_contract_tests"

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
  "$CORE_DIR/src/core/plain_game_setup.cpp" \
  "$CORE_DIR/src/core/plain_2d.cpp" \
  "$CORE_DIR/src/core/plain_2d_session.cpp" \
  "$CORE_DIR/src/core/plain_2d_trace.cpp" \
  "$CORE_DIR/src/core/plain_nd.cpp" \
  "$CORE_DIR/src/core/plain_piece_catalog.cpp" \
  "$CORE_DIR/src/core/board_extent_contract.cpp" \
  "$CORE_DIR/src/core/geometry.cpp" \
  "$CORE_DIR/src/core/query.cpp" \
  "$CORE_DIR/src/core/topology_transport.cpp" \
  "$CORE_DIR/src/core/sha256.cpp" \
  "$CORE_DIR/tests/plain_2d_core_tests.cpp" \
  -o "$TEST_2D_BIN"

"$CXX_BIN" -std=c++17 -Wall -Wextra -Werror \
  -I"$CORE_DIR/include" \
  "$CORE_DIR/src/core/core_api.cpp" \
  "$CORE_DIR/src/core/geometry.cpp" \
  "$CORE_DIR/src/core/plain_nd.cpp" \
  "$CORE_DIR/tests/geometry_core_tests.cpp" \
  -o "$TEST_GEOMETRY_BIN"

"$CXX_BIN" -std=c++17 -Wall -Wextra -Werror \
  -I"$CORE_DIR/include" \
  "$CORE_DIR/src/core/core_api.cpp" \
  "$CORE_DIR/src/core/geometry.cpp" \
  "$CORE_DIR/src/core/plain_nd.cpp" \
  "$CORE_DIR/src/core/query.cpp" \
  "$CORE_DIR/tests/query_core_tests.cpp" \
  -o "$TEST_QUERY_BIN"

"$CXX_BIN" -std=c++17 -Wall -Wextra -Werror \
  -I"$CORE_DIR/include" \
  "$CORE_DIR/src/core/core_api.cpp" \
  "$CORE_DIR/src/core/plain_game_setup.cpp" \
  "$CORE_DIR/src/core/plain_nd.cpp" \
  "$CORE_DIR/src/core/plain_nd_session.cpp" \
  "$CORE_DIR/src/core/plain_nd_trace.cpp" \
  "$CORE_DIR/src/core/plain_2d.cpp" \
  "$CORE_DIR/src/core/plain_piece_catalog.cpp" \
  "$CORE_DIR/src/core/board_extent_contract.cpp" \
  "$CORE_DIR/src/core/geometry.cpp" \
  "$CORE_DIR/src/core/query.cpp" \
  "$CORE_DIR/src/core/topology_transport.cpp" \
  "$CORE_DIR/src/core/sha256.cpp" \
  "$CORE_DIR/tests/plain_nd_core_tests.cpp" \
  -o "$TEST_ND_BIN"

"$CXX_BIN" -std=c++17 -Wall -Wextra -Werror \
  -I"$CORE_DIR/include" \
  "$CORE_DIR/src/core/sha256.cpp" \
  "$CORE_DIR/tests/trace_metadata_identity_digest_tests.cpp" \
  -o "$TEST_TRACE_METADATA_BIN"

"$CXX_BIN" -std=c++17 -Wall -Wextra -Werror \
  -I"$CORE_DIR/include" \
  "$CORE_DIR/tests/topology_contract_foundation_tests.cpp" \
  -o "$TEST_TOPOLOGY_CONTRACT_BIN"

"$CXX_BIN" -std=c++17 -Wall -Wextra -Werror \
  -I"$CORE_DIR/include" \
  "$CORE_DIR/src/core/core_api.cpp" \
  "$CORE_DIR/src/core/geometry.cpp" \
  "$CORE_DIR/src/core/plain_nd.cpp" \
  "$CORE_DIR/src/core/query.cpp" \
  "$CORE_DIR/src/core/topology_transport.cpp" \
  "$CORE_DIR/tests/topology_transport_tests.cpp" \
  -o "$TEST_TOPOLOGY_TRANSPORT_BIN"

"$CXX_BIN" -std=c++17 -Wall -Wextra -Werror \
  -I"$CORE_DIR/include" \
  "$CORE_DIR/src/core/core_api.cpp" \
  "$CORE_DIR/src/core/plain_game_setup.cpp" \
  "$CORE_DIR/src/core/plain_2d.cpp" \
  "$CORE_DIR/src/core/plain_2d_session.cpp" \
  "$CORE_DIR/src/core/plain_nd.cpp" \
  "$CORE_DIR/src/core/plain_nd_session.cpp" \
  "$CORE_DIR/src/core/plain_piece_catalog.cpp" \
  "$CORE_DIR/src/core/board_extent_contract.cpp" \
  "$CORE_DIR/src/core/geometry.cpp" \
  "$CORE_DIR/src/core/query.cpp" \
  "$CORE_DIR/src/core/topology_transport.cpp" \
  "$CORE_DIR/src/core/sha256.cpp" \
  "$CORE_DIR/tests/board_extent_contract_tests.cpp" \
  -o "$TEST_BOARD_EXTENT_BIN"

if [[ "${1:-}" == "--export-plain-2d-trace" ]]; then
  "$TEST_2D_BIN" "$@"
elif [[ "${1:-}" == "--export-plain-nd-trace" ]]; then
  "$TEST_ND_BIN" "$@"
elif [[ "${1:-}" == "--export-plain-setup" ]]; then
  if [[ "${2:-}" == *"_2d_"* ]]; then
    "$TEST_2D_BIN" "$@"
  else
    "$TEST_ND_BIN" "$@"
  fi
elif [[ "${1:-}" == "--pilot-stable-hash" ]]; then
  "$TEST_2D_BIN" "$@"
elif [[ "${1:-}" == "--geometry-parity" ]]; then
  "$TEST_GEOMETRY_BIN" "$@"
elif [[ "${1:-}" == "--query-parity" ]]; then
  "$TEST_QUERY_BIN" "$@"
elif [[ "${1:-}" == "--trace-metadata-identity-digest" ]]; then
  "$TEST_TRACE_METADATA_BIN" "$@"
elif [[ "${1:-}" == "--topology-contract-metadata" ]]; then
  "$TEST_TOPOLOGY_CONTRACT_BIN" --contract-metadata
else
  "$TEST_2D_BIN" "$@"
  "$TEST_ND_BIN"
  "$TEST_GEOMETRY_BIN"
  "$TEST_QUERY_BIN"
  "$TEST_TOPOLOGY_CONTRACT_BIN"
  "$TEST_TOPOLOGY_TRANSPORT_BIN"
	"$TEST_BOARD_EXTENT_BIN"
fi
