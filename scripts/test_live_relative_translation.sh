#!/usr/bin/env bash
# Fast, isolated production-scene regression; canonical acceptance still runs
# tests/run_tests.gd through verify_godot_4_7.sh.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${GODOT_BIN:?Set GODOT_BIN to the pinned Godot executable}"
eval "$(cd "$ROOT_DIR" && ./gov env)"
expected_version="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1]))["governance"]["godot_toolchain"]["build_identifier"])' "$ROOT_DIR/config/project/policy_pack.json")"
[[ "$("$GODOT_BIN" --version)" == "$expected_version" ]] || { echo "Pinned Godot version required" >&2; exit 1; }
mutation=""
if [[ $# -gt 0 ]]; then
  [[ $# -eq 2 && "$1" == "--mutation" ]] || { echo "Usage: $0 [--mutation A|B-basis|B-local|C]" >&2; exit 2; }
  mutation="$2"
fi
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/tet4d-relative.XXXXXX")"
trap 'rm -rf "$TEST_ROOT"' EXIT
cp -R "$ROOT_DIR/godot/Tet4D.Godot" "$TEST_ROOT/project"
if [[ -n "$mutation" ]]; then
  # Break only the disposable copy. The checkout never needs restoration.
  "$PYTHON_BIN" - "$TEST_ROOT/project" "$mutation" <<'PY'
from pathlib import Path
import sys

root, mutation = Path(sys.argv[1]), sys.argv[2]
path = root / "scripts/presentation/control_frame_mapping.gd"
changes = {
    "A": ("return new(null, yaw_radians, 3)", "return new(null, 0.0, 3)"),
    "B-basis": ("return new(basis, yaw_radians, 4)", "return new(null, yaw_radians, 4)"),
    "B-local": ("return new(basis, yaw_radians, 4)", "return new(basis, 0.0, 4)"),
    "C": (
        "if normalize_frame(frame) == FRAME_ABSOLUTE:",
        "if normalize_frame(frame) in [FRAME_ABSOLUTE, FRAME_RELATIVE]:",
    ),
}
if mutation not in changes:
    raise SystemExit("Unknown mutation: " + mutation)
before, after = changes[mutation]
source = path.read_text()
expected_count = 2 if mutation == "C" else 1
if source.count(before) != expected_count:
    raise SystemExit("Mutation anchor drift: " + mutation)
path.write_text(source.replace(before, after, 1))
print("Applied isolated mutation " + mutation)
PY
fi
mkdir -p "$TEST_ROOT/home" "$TEST_ROOT/config" "$TEST_ROOT/cache" "$TEST_ROOT/data"
run_godot() {
  env HOME="$TEST_ROOT/home" XDG_CONFIG_HOME="$TEST_ROOT/config" \
    XDG_CACHE_HOME="$TEST_ROOT/cache" XDG_DATA_HOME="$TEST_ROOT/data" \
    "$GODOT_BIN" --headless --path "$TEST_ROOT/project" "$@"
}
run_godot --editor --quit >"$TEST_ROOT/import.log" 2>&1
status=0
run_godot --quit-after 6000 --script tests/run_live_relative_translation.gd >"$TEST_ROOT/test.log" 2>&1 || status=$?
cat "$TEST_ROOT/test.log"
if rg -q 'SCRIPT ERROR' "$TEST_ROOT/import.log" "$TEST_ROOT/test.log"; then
  cat "$TEST_ROOT/import.log" >&2
  exit 1
fi
if ! rg -q 'Live relative translation focused runner passed' "$TEST_ROOT/test.log"; then
  exit 1
fi
exit "$status"
