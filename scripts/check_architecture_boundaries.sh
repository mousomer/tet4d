#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ENGINE_DIR="src/tet4d/engine"
TOOLS_BENCHMARKS_DIR="tools/benchmarks"

if [[ ! -d "$ENGINE_DIR" ]]; then
  exit 0
fi

fail() {
  echo "$1" >&2
  exit 2
}

iter_py_files() {
  local root
  for root in "$@"; do
    [[ -d "$root" ]] || continue
    find "$root" \
      -type f \
      -name '*.py' \
      ! -path '*/.git/*' \
      ! -path '*/.venv/*' \
      ! -path '*/__pycache__/*' \
      -print0
  done
}

collect_matches() {
  local pattern="$1"
  shift
  local file
  while IFS= read -r -d '' file; do
    grep -nE "$pattern" "$file" || true
  done < <(iter_py_files "$@")
}

check_forbidden_imports() {
  local message="$1"
  local pattern="$2"
  shift 2
  local lines
  lines="$(collect_matches "$pattern" "$@")"
  if [[ -n "$lines" ]]; then
    echo "$message" >&2
    printf '%s\n' "$lines" >&2
    fail "$message"
  fi
}

check_forbidden_imports \
  "Architecture violation: engine imports pygame." \
  '^\s*(import|from)\s+pygame(\.|(\s|$))' \
  "$ENGINE_DIR"

check_forbidden_imports \
  "Architecture violation: engine imports tet4d.ui." \
  '^\s*(import|from)\s+tet4d\.ui(\.|(\s|$))' \
  "$ENGINE_DIR"

check_forbidden_imports \
  "Architecture violation: engine imports tet4d.ai." \
  '^\s*(import|from)\s+tet4d\.ai(\.|(\s|$))' \
  "$ENGINE_DIR"

check_forbidden_imports \
  "Architecture violation: engine imports tet4d.replay." \
  '^\s*(import|from)\s+tet4d\.replay(\.|(\s|$))' \
  "$ENGINE_DIR"

check_forbidden_imports \
  "Architecture violation: engine imports tet4d.tools." \
  '^\s*(import|from)\s+tet4d\.tools(\.|(\s|$))' \
  "$ENGINE_DIR"

check_forbidden_imports \
  "Architecture violation: engine imports top-level tools." \
  '^\s*(import|from)\s+tools(\.|(\s|$))' \
  "$ENGINE_DIR"

# Upper layers may import engine modules directly. The enforced direction is that
# engine stays reusable and does not depend back on UI, AI, replay, or tools.

if [[ -d "$TOOLS_BENCHMARKS_DIR" ]]; then
  benchmark_ui_lines="$(collect_matches '^\s*(import|from)\s+tet4d\.ui(\.|(\s|$))' "$TOOLS_BENCHMARKS_DIR")"
  if [[ -n "$benchmark_ui_lines" ]]; then
    benchmark_ui_disallowed="$(printf '%s\n' "$benchmark_ui_lines" | grep -Ev \
      '^tools/benchmarks/profile_4d_render\.py:[0-9]+:\s*(import|from)\s+tet4d\.ui\.pygame(\.|(\s|$))' \
      || true)"
    if [[ -n "$benchmark_ui_disallowed" ]]; then
      echo "Architecture violation: benchmark tools import unsupported UI modules." >&2
      printf '%s\n' "$benchmark_ui_disallowed" >&2
      fail "Architecture violation: tools/benchmarks may only use tet4d.ui.pygame for renderer profiling."
    fi
  fi
fi

exit 0
