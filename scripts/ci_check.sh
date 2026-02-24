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

require_repo_package() {
  if "$PYTHON_BIN" -c "import tet4d" >/dev/null 2>&1; then
    return
  fi
  echo "Missing repo package 'tet4d' in ${PYTHON_BIN}." >&2
  echo "Run: ${PYTHON_BIN} -m pip install -e '.[dev]'" >&2
  exit 1
}

require_module ruff ruff
require_module pytest pytest
require_repo_package

"$PYTHON_BIN" tools/governance/validate_project_contracts.py
"$PYTHON_BIN" tools/governance/lint_menu_graph.py
"$PYTHON_BIN" tools/governance/scan_secrets.py
"$PYTHON_BIN" tools/governance/check_pygame_ce.py
run_module ruff check . --quiet
run_module ruff check --quiet --select C901 .
"$PYTHON_BIN" scripts/arch_metrics.py
run_module pytest -q --disable-warnings --maxfail=1
PYTHONPATH=. "$PYTHON_BIN" tools/stability/check_playbot_stability.py --repeats 20 --seed-base 0
"$PYTHON_BIN" -m compileall -q front.py front2d.py front3d.py front4d.py cli/front.py cli/front2d.py cli/front3d.py cli/front4d.py src/tet4d src/tet4d/engine
"$PYTHON_BIN" tools/benchmarks/bench_playbot.py --assert --record-trend
