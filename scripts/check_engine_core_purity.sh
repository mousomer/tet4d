#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

CORE_DIR="src/tet4d/engine/core"
CORE_RNG_DIR="$CORE_DIR/rng"

if [[ ! -d "$CORE_DIR" ]]; then
  exit 0
fi

RG_BASE=(rg -n --hidden --glob '!.git/**' --glob '!.venv/**' --glob '!**/__pycache__/**')

fail() {
  echo "$1" >&2
  exit 2
}

collect_lines() {
  local pattern="$1"
  shift
  "${RG_BASE[@]}" "$pattern" "$@" || true
}

# 1) No pygame/UI/tools imports in engine/core.
forbidden_import_lines="$(
  {
    collect_lines '^\s*(import|from)\s+pygame(\.|(\s|$))' "$CORE_DIR"
    collect_lines '^\s*(import|from)\s+tet4d\.ui(\.|(\s|$))' "$CORE_DIR"
    collect_lines '^\s*(import|from)\s+tet4d\.tools(\.|(\s|$))' "$CORE_DIR"
    collect_lines '^\s*(import|from)\s+tools(\.|(\s|$))' "$CORE_DIR"
  } | sort -u
)"
if [[ -n "$forbidden_import_lines" ]]; then
  echo "Engine core purity violation: forbidden imports detected." >&2
  printf '%s\n' "$forbidden_import_lines" >&2
  fail "engine/core must not import pygame/ui/tools."
fi

# 2) No time/logging imports in engine/core.
side_effect_imports="$(
  {
    collect_lines '^\s*(import|from)\s+time(\.|(\s|$))' "$CORE_DIR"
    collect_lines '^\s*(import|from)\s+logging(\.|(\s|$))' "$CORE_DIR"
  } | sort -u
)"
if [[ -n "$side_effect_imports" ]]; then
  echo "Engine core purity violation: time/logging imports detected." >&2
  printf '%s\n' "$side_effect_imports" >&2
  fail "engine/core must not import time or logging."
fi

# 3) No random imports outside engine/core/rng.
random_imports="$(
  collect_lines '^\s*(import|from)\s+random(\.|(\s|$))' "$CORE_DIR" | sort -u
)"
if [[ -n "$random_imports" ]]; then
  random_outside_rng="$(
    printf '%s\n' "$random_imports" | grep -Ev "^\s*${CORE_RNG_DIR//\//\\/}/" || true
  )"
  if [[ -n "$random_outside_rng" ]]; then
    echo "Engine core purity violation: random imports outside core/rng detected." >&2
    printf '%s\n' "$random_outside_rng" >&2
    fail "engine/core random usage must be isolated to core/rng."
  fi
fi

# 4) No file I/O or console/logging calls in engine/core.
effect_calls="$(
  {
    collect_lines '\bprint\s*\(' "$CORE_DIR"
    collect_lines '\blogging\.' "$CORE_DIR"
    collect_lines '\bopen\s*\(' "$CORE_DIR"
    collect_lines '\.open\s*\(' "$CORE_DIR"
    collect_lines '\.read_text\s*\(' "$CORE_DIR"
    collect_lines '\.write_text\s*\(' "$CORE_DIR"
    collect_lines '\.read_bytes\s*\(' "$CORE_DIR"
    collect_lines '\.write_bytes\s*\(' "$CORE_DIR"
  } | sort -u
)"
if [[ -n "$effect_calls" ]]; then
  echo "Engine core purity violation: file I/O or logging/print calls detected." >&2
  printf '%s\n' "$effect_calls" >&2
  fail "engine/core must not perform file I/O or print/logging side effects."
fi

exit 0

