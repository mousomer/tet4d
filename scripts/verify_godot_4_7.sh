#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POLICY_PACK="$ROOT_DIR/config/project/policy_pack.json"
GODOT_PROJECT="$ROOT_DIR/godot/Tet4D.Godot"
GODOT_CPP_DIR="$ROOT_DIR/native/third_party/godot-cpp"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  :
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "Python is required to read the canonical Godot toolchain manifest." >&2
  exit 1
fi

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

(
  cd "$API_DIR"
  env "${GODOT_ENV[@]}" "$GODOT_BIN" --headless --dump-extension-api
)
"$PYTHON_BIN" -c \
  'import json,sys; engine=json.load(open(sys.argv[1])); binding=json.load(open(sys.argv[2])); engine.pop("header"); binding.pop("header"); raise SystemExit(0 if engine == binding else "Godot and godot-cpp extension APIs differ")' \
  "$API_DIR/extension_api.json" "$GODOT_CPP_DIR/gdextension/extension_api.json"

env "${GODOT_ENV[@]}" "$GODOT_BIN" \
  --headless --editor --path "$PROJECT_COPY" --quit
env "${GODOT_ENV[@]}" "$GODOT_BIN" \
  --headless --path "$PROJECT_COPY" --script tests/run_tests.gd
TOPOLOGY_TRANSPORT_PARITY_LOG="$VERIFY_ROOT/topology_transport_parity.log"
env "${GODOT_ENV[@]}" "$GODOT_BIN" \
  --headless --path "$PROJECT_COPY" --script tests/run_topology_transport_parity.gd \
  >"$TOPOLOGY_TRANSPORT_PARITY_LOG" 2>&1
PYTHONPATH="$ROOT_DIR/src" "$PYTHON_BIN" \
  "$ROOT_DIR/tools/migration/compare_topology_transport.py" \
  --native-output "$TOPOLOGY_TRANSPORT_PARITY_LOG"
env "${GODOT_ENV[@]}" "$GODOT_BIN" \
  --headless --path "$PROJECT_COPY" --quit-after 5

echo "Godot 4.7.2 verification passed."
