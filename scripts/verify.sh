#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# CODEX_MODE=1 reduces token-heavy runtime while preserving core correctness checks.
CODEX_MODE="${CODEX_MODE:-0}"
QUIET="${QUIET:-1}"

# Reduce stability repeats in CODEX_MODE to keep logs/time bounded.
if [[ "$CODEX_MODE" == "1" ]]; then
  STABILITY_REPEATS="${STABILITY_REPEATS:-5}"
else
  STABILITY_REPEATS="${STABILITY_REPEATS:-20}"
fi
STABILITY_SEED_BASE="${STABILITY_SEED_BASE:-0}"

# Select python
if [[ -n "${PYTHON_BIN:-}" ]]; then
  :
elif [[ -x ".venv/bin/python" ]]; then
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
    return 0
  fi
  echo "Missing python module '${module}' in ${PYTHON_BIN}." >&2
  echo "Install it with: ${PYTHON_BIN} -m pip install ${package_name}" >&2
  exit 1
}

run_module() { "$PYTHON_BIN" -m "$@"; }

require_repo_package() {
  if "$PYTHON_BIN" -c "import tet4d" >/dev/null 2>&1; then
    return 0
  fi
  echo "Missing repo package 'tet4d' in ${PYTHON_BIN}." >&2
  echo "Run: ${PYTHON_BIN} -m pip install -e '.[dev]'" >&2
  exit 1
}

run_step() {
  local name="$1"; shift
  local tmp
  tmp="$(mktemp -t tet4d_verify_${name}.XXXXXX.log)"

  if [[ "$QUIET" == "1" ]]; then
    if ! "$@" >"$tmp" 2>&1; then
      echo "== FAILED: ${name} ==" >&2
      cat "$tmp" >&2
      rm -f "$tmp"
      exit 1
    fi
    rm -f "$tmp"
  else
    echo "== ${name} =="
    "$@"
  fi
}

# Minimal output verification steps (same intent as ci_check.sh)
require_module ruff ruff
require_module pytest pytest
require_repo_package

run_step "contracts"      "$PYTHON_BIN" tools/governance/validate_project_contracts.py
run_step "secret_scan"    "$PYTHON_BIN" tools/governance/scan_secrets.py
run_step "pygame_ce"      "$PYTHON_BIN" tools/governance/check_pygame_ce.py

run_step "ruff"           run_module ruff check .
run_step "ruff_c901"      run_module ruff check --select C901 .
run_step "arch_metrics"   "$PYTHON_BIN" scripts/arch_metrics.py
run_step "arch_metric_budgets" env PYTHON_BIN="$PYTHON_BIN" ./scripts/check_architecture_metric_budgets.sh

# Keep pytest quiet and bounded in interactive mode
run_step "pytest"         run_module pytest -q --maxfail=1 --disable-warnings

run_step "playbot_stability" \
  env PYTHONPATH=. "$PYTHON_BIN" tools/stability/check_playbot_stability.py --repeats "$STABILITY_REPEATS" --seed-base "$STABILITY_SEED_BASE"

run_step "compileall"     "$PYTHON_BIN" -m compileall -q front.py cli/__init__.py cli/front.py cli/front2d.py cli/front3d.py cli/front4d.py src/tet4d src/tet4d/engine
run_step "bench_playbot"  "$PYTHON_BIN" tools/benchmarks/bench_playbot.py --assert --record-trend

echo "verify: OK"
