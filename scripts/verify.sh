#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# ----------------------------
# Configuration (Codex-friendly)
# ----------------------------
# CODEX_MODE=1 reduces token-heavy output and runtime while preserving core correctness checks.
CODEX_MODE="${CODEX_MODE:-0}"

# If you want verify to be quiet by default (good for Codex), leave QUIET=1 default.
QUIET="${QUIET:-1}"

# In CODEX_MODE, reduce stability repeats to limit log volume.
if [[ "$CODEX_MODE" == "1" ]]; then
  STABILITY_REPEATS="${STABILITY_REPEATS:-5}"
else
  STABILITY_REPEATS="${STABILITY_REPEATS:-20}"
fi

STABILITY_SEED_BASE="${STABILITY_SEED_BASE:-0}"

# ----------------------------
# Python selection (mirrors ci_check.sh)
# ----------------------------
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

run_module() {
  local module="$1"; shift
  "$PYTHON_BIN" -m "$module" "$@"
}

# ----------------------------
# Pass-quiet / fail-loud runner
# ----------------------------
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

# ----------------------------
# Verify steps (same intent as ci_check, quieter)
# ----------------------------
require_module ruff ruff
require_module pytest pytest

# Governance/contract checks (keep these; they’re high signal)
run_step "contracts" "$PYTHON_BIN" tools/validate_project_contracts.py
run_step "secret_scan" "$PYTHON_BIN" tools/scan_secrets.py
run_step "pygame_ce_check" "$PYTHON_BIN" tools/check_pygame_ce.py

# Lint + complexity
run_step "ruff" run_module ruff check .
run_step "ruff_c901" run_module ruff check --select C901 .

# Tests: already quiet
run_step "pytest" run_module pytest -q

# Stability sweep (token-heavy). In CODEX_MODE defaults to fewer repeats.
run_step "playbot_stability" \
  "$PYTHON_BIN" tools/check_playbot_stability.py --repeats "$STABILITY_REPEATS" --seed-base "$STABILITY_SEED_BASE"

# Compileall: already quiet
run_step "compileall" "$PYTHON_BIN" -m compileall -q front.py front2d.py front3d.py front4d.py tetris_nd

# Bench assertions: keep, but keep output quiet unless failing
run_step "bench_playbot" "$PYTHON_BIN" tools/bench_playbot.py --assert --record-trend

echo "verify: OK"