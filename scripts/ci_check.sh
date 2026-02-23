#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -n "${PYTHON_BIN:-}" ]; then
  :
elif [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "No Python runtime found. Set PYTHON_BIN or install python3." >&2
  exit 1
fi

require_module() {
  local module="$1"
  local package_name="$2"
  if "$PYTHON_BIN" -c "import ${module}" >/dev/null 2>&1; then
    return
  fi
  echo "Missing python module '${module}' in ${PYTHON_BIN}." >&2
  echo "Install it with: ${PYTHON_BIN} -m pip install ${package_name}" >&2
  exit 1
}

run_module() {
  local module="$1"
  shift
  "$PYTHON_BIN" -m "$module" "$@"
}

require_module ruff ruff
require_module pytest pytest

"$PYTHON_BIN" tools/validate_project_contracts.py
"$PYTHON_BIN" tools/lint_menu_graph.py
"$PYTHON_BIN" tools/scan_secrets.py
"$PYTHON_BIN" tools/check_pygame_ce.py
run_module ruff check .
run_module ruff check --select C901 .
run_module pytest -q
PYTHONPATH=. "$PYTHON_BIN" tools/check_playbot_stability.py --repeats 20 --seed-base 0
"$PYTHON_BIN" -m compileall -q front.py front2d.py front3d.py front4d.py tetris_nd
"$PYTHON_BIN" tools/bench_playbot.py --assert --record-trend
