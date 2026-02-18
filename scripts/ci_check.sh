#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -n "${PYTHON_BIN:-}" ]; then
  :
elif [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  PYTHON_BIN="python3"
fi

run_module_or_command() {
  local module="$1"
  local command_name="$2"
  shift 2

  if "$PYTHON_BIN" -c "import ${module}" >/dev/null 2>&1; then
    "$PYTHON_BIN" -m "$module" "$@"
    return
  fi

  if command -v "$command_name" >/dev/null 2>&1; then
    "$command_name" "$@"
    return
  fi

  echo "Missing required tool: python module '${module}' or command '${command_name}'" >&2
  exit 1
}

"$PYTHON_BIN" tools/validate_project_contracts.py
"$PYTHON_BIN" tools/check_pygame_ce.py
run_module_or_command ruff ruff check .
run_module_or_command ruff ruff check --select C901 .
run_module_or_command pytest pytest -q
PYTHONPATH=. "$PYTHON_BIN" tools/check_playbot_stability.py --repeats 20 --seed-base 0
"$PYTHON_BIN" -m compileall -q front.py front2d.py front3d.py front4d.py tetris_nd
"$PYTHON_BIN" tools/bench_playbot.py --assert --record-trend
