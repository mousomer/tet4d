#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# CODEX_MODE=1 reduces token-heavy runtime while preserving core correctness checks.
CODEX_MODE="${CODEX_MODE:-0}"
QUIET="${QUIET:-1}"
KEEP_VERIFY_STATE="${KEEP_VERIFY_STATE:-0}"

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

VERIFY_LOCK_DIR="state/.verify.lock"
VERIFY_STATE_ROOT_OWNED=0
VERIFY_STATE_ROOT_VALUE=""
VERIFY_LOG_DIR=""
VERIFY_RUN_ID=""

cleanup_verify_runtime() {
  local status=$?
  if [[ -d "$VERIFY_LOCK_DIR" ]]; then
    rm -rf "$VERIFY_LOCK_DIR"
  fi
  if [[ "$VERIFY_STATE_ROOT_OWNED" == "1" && -n "$VERIFY_STATE_ROOT_VALUE" && -d "$VERIFY_STATE_ROOT_VALUE" ]]; then
    if [[ "$status" == "0" && "$KEEP_VERIFY_STATE" != "1" ]]; then
      rm -rf "$VERIFY_STATE_ROOT_VALUE"
    else
      echo "verify state preserved at $VERIFY_STATE_ROOT_VALUE" >&2
    fi
  fi
  exit "$status"
}

prepare_verify_runtime() {
  mkdir -p state
  if ! mkdir "$VERIFY_LOCK_DIR" 2>/dev/null; then
    echo "Another verify/ci_check run is active. Wait for it to finish before starting a second full gate." >&2
    echo "Lock path: $VERIFY_LOCK_DIR" >&2
    exit 1
  fi
  printf '%s\n' "$$" > "$VERIFY_LOCK_DIR/pid"
  VERIFY_RUN_ID="$(date +%Y%m%dT%H%M%S)_$$"
  if [[ -z "${TET4D_STATE_ROOT:-}" ]]; then
    export TET4D_STATE_ROOT="state/verify_runs/$VERIFY_RUN_ID"
    VERIFY_STATE_ROOT_OWNED=1
  fi
  VERIFY_STATE_ROOT_VALUE="$TET4D_STATE_ROOT"
  VERIFY_LOG_DIR="$VERIFY_STATE_ROOT_VALUE/verify_logs"
  mkdir -p "$VERIFY_STATE_ROOT_VALUE" "$VERIFY_LOG_DIR"
  export TET4D_PYTEST_TMP_WORKAROUND=1
}

trap cleanup_verify_runtime EXIT INT TERM
prepare_verify_runtime

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
  tmp="$(mktemp "$VERIFY_LOG_DIR/${name}.XXXXXX.log")"

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

run_step "policy_compliance" ./scripts/check_policy_compliance.sh
run_step "policy_compliance_repo" ./scripts/check_policy_compliance_repo.sh
run_step "git_sanitation_repo" ./scripts/check_git_sanitation_repo.sh

run_step "contracts"      "$PYTHON_BIN" tools/governance/validate_project_contracts.py
run_step "config_reference" "$PYTHON_BIN" tools/governance/generate_configuration_reference.py --check
run_step "maintenance_docs" "$PYTHON_BIN" tools/governance/generate_maintenance_docs.py --check
run_step "risk_gates"     "$PYTHON_BIN" tools/governance/check_risk_gates.py
run_step "policy_runtime_rules" "$PYTHON_BIN" tools/governance/check_policy_runtime_rules.py
run_step "wheel_reuse_rules" "$PYTHON_BIN" tools/governance/check_wheel_reuse_rules.py
run_step "loc_guidance"   "$PYTHON_BIN" tools/governance/check_loc_guidance.py
run_step "dedup_dead_code_rules" "$PYTHON_BIN" tools/governance/check_dedup_dead_code_rules.py
run_step "secret_scan"    "$PYTHON_BIN" tools/governance/scan_secrets.py
run_step "pygame_ce"      "$PYTHON_BIN" tools/governance/check_pygame_ce.py

run_step "ruff"           run_module ruff check .
run_step "ruff_format"    run_module ruff format --check scripts tools
run_step "ruff_c901"      run_module ruff check --select C901 .
run_step "arch_metrics"   "$PYTHON_BIN" scripts/arch_metrics.py
run_step "arch_metrics_soft_gate" env PYTHON_BIN="$PYTHON_BIN" ./scripts/check_architecture_metrics_soft_gate.sh
run_step "arch_metrics_budgets" env PYTHON_BIN="$PYTHON_BIN" ./scripts/check_architecture_metric_budgets.sh

# Keep pytest quiet and bounded in interactive mode
PYTEST_ARGS=(-q --maxfail=1 --disable-warnings)
if [[ "$CODEX_MODE" == "1" ]]; then
  PYTEST_ARGS+=(--basetemp="$TET4D_STATE_ROOT/pytest_basetemp" -p no:cacheprovider -p no:tmpdir)
fi

run_step "pytest"         run_module pytest "${PYTEST_ARGS[@]}"

run_step "playbot_stability"   env PYTHONPATH=. "$PYTHON_BIN" tools/stability/check_playbot_stability.py --repeats "$STABILITY_REPEATS" --seed-base "$STABILITY_SEED_BASE"

run_step "compileall"     "$PYTHON_BIN" -m compileall -q front.py cli/__init__.py cli/front.py cli/front2d.py cli/front3d.py cli/front4d.py src/tet4d src/tet4d/engine
run_step "bench_playbot"  "$PYTHON_BIN" tools/benchmarks/bench_playbot.py --assert --record-trend

echo "verify: OK"
