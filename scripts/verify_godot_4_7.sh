#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POLICY_PACK="$ROOT_DIR/config/project/policy_pack.json"
GODOT_PROJECT="$ROOT_DIR/godot/Tet4D.Godot"
GODOT_CPP_DIR="$ROOT_DIR/native/third_party/godot-cpp"

cd "$ROOT_DIR"
eval "$(./gov env)"

if [[ -z "${GODOT_BIN:-}" ]]; then
  echo "Set GODOT_BIN to the exact supported Godot executable." >&2
  exit 1
fi
if [[ ! -x "$GODOT_BIN" ]]; then
  echo "Godot executable is not executable: $GODOT_BIN" >&2
  exit 1
fi

manifest_value() {
  "$PYTHON_BIN" -c \
    'import json,sys; data=json.load(open(sys.argv[1])); value=data["governance"]["godot_toolchain"]; print(value[sys.argv[2]])' \
    "$POLICY_PACK" "$1"
}

expected_version="$(manifest_value build_identifier)"
actual_version="$("$GODOT_BIN" --version)"
if [[ "$actual_version" != "$expected_version" ]]; then
  echo "Godot version mismatch: expected $expected_version, got $actual_version" >&2
  exit 1
fi

expected_godot_cpp="$("$PYTHON_BIN" -c \
  'import json,sys; data=json.load(open(sys.argv[1])); print(data["governance"]["godot_toolchain"]["godot_cpp"]["selected_commit"])' \
  "$POLICY_PACK")"
actual_godot_cpp="$(git -C "$GODOT_CPP_DIR" rev-parse HEAD)"
if [[ "$actual_godot_cpp" != "$expected_godot_cpp" ]]; then
  echo "godot-cpp mismatch: expected $expected_godot_cpp, got $actual_godot_cpp" >&2
  exit 1
fi

"$PYTHON_BIN" - "$POLICY_PACK" "$ROOT_DIR" <<'PY'
import json
import sys
from pathlib import Path

policy_path = Path(sys.argv[1])
root = Path(sys.argv[2])
toolchain = json.loads(policy_path.read_text(encoding="utf-8"))["governance"][
    "godot_toolchain"
]
project_text = (root / "godot/Tet4D.Godot/project.godot").read_text(
    encoding="utf-8"
)
descriptor_text = (
    root / "godot/Tet4D.Godot/addons/tet4d_core/tet4d_core.gdextension"
).read_text(encoding="utf-8")
build_text = (root / "scripts/build_godot_tet4d_core.sh").read_text(
    encoding="utf-8"
)

expected_target = toolchain["selected_supported_version"]
expected_api = toolchain["godot_cpp"]["api_version"]
expected_minimum = toolchain["gdextension"]["compatibility_minimum"]
checks = {
    "project target version": (
        f'config/tet4d_target_godot_version="{expected_target}"' in project_text
    ),
    "project feature version": (
        f'config/features=PackedStringArray("{expected_api}")' in project_text
    ),
    "GDExtension compatibility minimum": (
        f'compatibility_minimum = "{expected_minimum}"' in descriptor_text
    ),
    "native API version": f"api_version={expected_api}" in build_text,
}
failed = [label for label, passed in checks.items() if not passed]
if failed:
    raise SystemExit("Godot toolchain declaration drift: " + ", ".join(failed))
PY

VERIFY_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/tet4d-godot-4.7.XXXXXX")"
cleanup() {
  rm -rf "$VERIFY_ROOT"
}
trap cleanup EXIT INT TERM

PROJECT_COPY="$VERIFY_ROOT/Tet4D.Godot"
HOME_DIR="$VERIFY_ROOT/home"
CONFIG_DIR="$VERIFY_ROOT/config"
CACHE_DIR="$VERIFY_ROOT/cache"
DATA_DIR="$VERIFY_ROOT/data"
API_DIR="$VERIFY_ROOT/api"
mkdir -p "$HOME_DIR" "$CONFIG_DIR" "$CACHE_DIR" "$DATA_DIR" "$API_DIR"
cp -R "$GODOT_PROJECT" "$PROJECT_COPY"

GODOT_ENV=(
  "HOME=$HOME_DIR"
  "XDG_CONFIG_HOME=$CONFIG_DIR"
  "XDG_CACHE_HOME=$CACHE_DIR"
  "XDG_DATA_HOME=$DATA_DIR"
)
# A stalled Godot step must fail the gate rather than block it until a CI
# timeout: a test that loops forever is a defect, not an absence of evidence.
GODOT_STEP_TIMEOUT_SECONDS="${GODOT_STEP_TIMEOUT_SECONDS:-900}"

# The step's output is both shown and kept: an operator watching the terminal
# needs progress as it happens, and the checks below need the whole log.
run_godot_step() {
  local label="$1"
  local log_path="$2"
  local visibility="$3"
  shift 3
  : >"$log_path"
  "$@" >"$log_path" 2>&1 &
  local step_pid=$!
  local tail_pid=""
  if [[ "$visibility" == "stream" ]]; then
    tail -f "$log_path" 2>/dev/null &
    tail_pid=$!
  fi
  local waited=0
  local status=0
  while kill -0 "$step_pid" 2>/dev/null; do
    if ((waited >= GODOT_STEP_TIMEOUT_SECONDS)); then
      kill -9 "$step_pid" 2>/dev/null || true
      wait "$step_pid" 2>/dev/null || true
      stop_follower "$tail_pid"
      echo "Godot step '$label' exceeded ${GODOT_STEP_TIMEOUT_SECONDS}s; terminated." >&2
      return 124
    fi
    sleep 5
    waited=$((waited + 5))
  done
  wait "$step_pid" || status=$?
  stop_follower "$tail_pid"
  return "$status"
}

stop_follower() {
  local tail_pid="$1"
  [[ -n "$tail_pid" ]] || return 0
  # Let the follower drain the final lines before it is stopped.
  sleep 1
  kill "$tail_pid" 2>/dev/null || true
  wait "$tail_pid" 2>/dev/null || true
}

# The GDScript runner prints its own success line, and an aborted test function
# leaves only a SCRIPT ERROR behind, so the log is evidence in its own right.
assert_no_script_error() {
  local label="$1"
  local log_path="$2"
  if grep -q "SCRIPT ERROR" "$log_path"; then
    echo "Godot step '$label' reported SCRIPT ERROR; a test aborted mid-run:" >&2
    grep -n -m 5 "SCRIPT ERROR" "$log_path" >&2
    return 1
  fi
}

# The fixture cleanup established a zero-leak baseline for these shutdown
# signatures. Keep the editor's separate ObjectDB snapshot-directory advisory
# visible; it is not an exit-time ObjectDB leak.
assert_no_teardown_leak() {
  local label="$1"
  local log_path="$2"
  local leak_pattern='^(WARNING: [0-9]+ RIDs of type ".*" were leaked\.|WARNING: [0-9]+ ObjectDB instances were leaked at exit|ERROR: [0-9]+ resources still in use at exit|ERROR: Pages in use exist at exit in PagedAllocator:|ERROR: [0-9]+ RID allocations of type .* were leaked at exit\.)'
  if grep -Eq "$leak_pattern" "$log_path"; then
    echo "Godot step '$label' reported an unexpected teardown leak:" >&2
    grep -nE "$leak_pattern" "$log_path" >&2
    return 1
  fi
}

(
  cd "$API_DIR"
  env "${GODOT_ENV[@]}" "$GODOT_BIN" --headless --dump-extension-api
)
"$PYTHON_BIN" -c \
  'import json,sys; engine=json.load(open(sys.argv[1])); binding=json.load(open(sys.argv[2])); engine.pop("header"); binding.pop("header"); raise SystemExit(0 if engine == binding else "Godot and godot-cpp extension APIs differ")' \
  "$API_DIR/extension_api.json" "$GODOT_CPP_DIR/gdextension/extension_api.json"

EDITOR_IMPORT_LOG="$VERIFY_ROOT/editor_import.log"
run_godot_step "editor import" "$EDITOR_IMPORT_LOG" stream env "${GODOT_ENV[@]}" "$GODOT_BIN" \
  --headless --editor --path "$PROJECT_COPY" --quit
assert_no_teardown_leak "editor import" "$EDITOR_IMPORT_LOG"
REPLAY_TEST_LOG="$VERIFY_ROOT/run_tests.log"
run_godot_step "replay tests" "$REPLAY_TEST_LOG" stream env "${GODOT_ENV[@]}" "$GODOT_BIN" \
  --headless --path "$PROJECT_COPY" --script tests/run_tests.gd
assert_no_script_error "replay tests" "$REPLAY_TEST_LOG"
assert_no_teardown_leak "replay tests" "$REPLAY_TEST_LOG"
TOPOLOGY_TRANSPORT_PARITY_LOG="$VERIFY_ROOT/topology_transport_parity.log"
run_godot_step "topology transport parity" "$TOPOLOGY_TRANSPORT_PARITY_LOG" quiet \
  env "${GODOT_ENV[@]}" "$GODOT_BIN" \
  --headless --path "$PROJECT_COPY" --script tests/run_topology_transport_parity.gd
assert_no_script_error "topology transport parity" "$TOPOLOGY_TRANSPORT_PARITY_LOG"
assert_no_teardown_leak "topology transport parity" "$TOPOLOGY_TRANSPORT_PARITY_LOG"
"$PYTHON_BIN" \
  "$ROOT_DIR/tools/migration/compare_topology_transport.py" \
  --native-output "$TOPOLOGY_TRANSPORT_PARITY_LOG"
BOOT_LOG="$VERIFY_ROOT/boot.log"
run_godot_step "headless boot" "$BOOT_LOG" stream env "${GODOT_ENV[@]}" "$GODOT_BIN" \
  --headless --path "$PROJECT_COPY" --quit-after 5
assert_no_script_error "headless boot" "$BOOT_LOG"
assert_no_teardown_leak "headless boot" "$BOOT_LOG"

echo "Godot 4.7.2 verification passed."
