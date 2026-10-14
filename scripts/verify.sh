#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

VERBOSE=0
if [[ "${1:-}" == "--verbose" ]]; then
  VERBOSE=1
  shift
fi
if [[ "$#" -ne 0 ]]; then
  echo "Usage: ./scripts/verify.sh [--verbose]" >&2
  exit 2
fi

# CODEX_MODE=1 reduces token-heavy runtime while preserving core correctness checks.
CODEX_MODE="${CODEX_MODE:-0}"
if [[ "$VERBOSE" == "1" ]]; then
  QUIET=0
  export GOV_ENV_VERBOSE=1
else
  QUIET="${QUIET:-1}"
fi
KEEP_VERIFY_STATE="${KEEP_VERIFY_STATE:-0}"

# Reduce stability repeats in CODEX_MODE to keep logs/time bounded.
if [[ "$CODEX_MODE" == "1" ]]; then
  STABILITY_REPEATS="${STABILITY_REPEATS:-5}"
else
  STABILITY_REPEATS="${STABILITY_REPEATS:-20}"
fi
STABILITY_SEED_BASE="${STABILITY_SEED_BASE:-0}"

# Resolve once. Every Python subprocess receives this exact interpreter, and in
# source mode the binding that decides which checkout it imports. Both come from
# the governance resolver rather than being reconstructed here: a gate that
# derived its own binding could verify a different environment than `gov doctor`
# certified. Before that interpreter exists, failures use a fixed bootstrap
# classification without echoing arbitrary resolver output.
if GOVERNED_ENV="$(./gov env 2>/dev/null)"; then
  :
else
  GOV_ENV_STATUS=$?
  printf 'environment_resolution: failed (exit=%s); review the declared interpreter and machine overlay through the owning resolver.\n' "$GOV_ENV_STATUS" >&2
  exit "$GOV_ENV_STATUS"
fi
eval "$GOVERNED_ENV"

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

# Both gates read their Ruff scope from one authority. Carrying separate target
# lists is how repository-wide formatting drift stayed invisible to whichever
# list was narrower.
static_analysis_scope() {
  "$PYTHON_BIN" - "$1" <<'SCOPE'
import json
import pathlib
import sys

rules = json.loads(pathlib.Path("config/project/policy_pack.json").read_text())
print(" ".join(rules["code_rules"]["static_analysis"][sys.argv[1]]))
SCOPE
}


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
  local tmp status
  tmp="$(mktemp "$VERIFY_LOG_DIR/${name}.XXXXXX.log")"

  if [[ "$QUIET" == "1" ]]; then
    if "$@" >"$tmp" 2>&1; then
      :
    else
      status=$?
      echo "== FAILED: ${name} ==" >&2
      cat "$tmp" >&2
      rm -f "$tmp"
      exit "$status"
    fi
    rm -f "$tmp"
  else
    echo "== ${name} =="
    "$@"
  fi
}

# These invocations are the shell-owned governance/policy enforcement graph.
# The provenance validator derives family names from these real calls.
run_governance_step() {
  local name="$1"; shift
  # Only scanners that can echo matched content need bounded classifications.
  # Keep ordinary checker diagnostics and the named provenance graph intact.
  case "$name" in
    git_sanitation_baseline|git_sanitation_repo|pack_sanitation|secret_scan)
      "$PYTHON_BIN" tools/workspace_governance/diagnostics.py --checker "$name" --run "$@"
      ;;
    *) run_step "$name" "$@" ;;
  esac
}

# Minimal output verification steps (same intent as ci_check.sh)
require_module ruff ruff
require_module pytest pytest
require_repo_package

# BEGIN workspace-governance managed verification
# Native integration preserves the actual named governance graph after setup.
run_governance_step "environment_doctor" ./gov doctor --json
run_governance_step "config_reference" ./gov check --generated --summary --json
run_governance_step "governance_inventory" "$PYTHON_BIN" tools/governance/export_governance_inventory.py --check
run_governance_step "git_sanitation_baseline" bash scripts/check_git_sanitation.sh .
run_governance_step "template_drift" bash scripts/check_policy_template_drift.sh .
run_governance_step "pack_sanitation" "$PYTHON_BIN" tools/workspace_governance/sanitation.py --root .
# END workspace-governance managed verification
run_governance_step "policy_compliance" ./scripts/check_policy_compliance.sh
run_governance_step "policy_compliance_repo" ./scripts/check_policy_compliance_extensions_repo.sh
run_governance_step "git_sanitation_repo" ./scripts/check_git_sanitation_repo.sh
run_governance_step "topology_contract_codegen" "$PYTHON_BIN" tools/codegen/generate_topology_contract.py --check

run_governance_step "governance" "$PYTHON_BIN" tools/governance/validate_governance.py
run_governance_step "maintenance_docs" "$PYTHON_BIN" tools/governance/generate_maintenance_docs.py --check
run_governance_step "secret_scan" "$PYTHON_BIN" tools/governance/scan_secrets.py
run_governance_step "pygame_ce" "$PYTHON_BIN" tools/governance/check_pygame_ce.py
run_governance_step "godot_settings_externalization" "$PYTHON_BIN" tools/governance/check_godot_settings_externalization.py

read -r -a RUFF_CHECK_SCOPE <<<"$(static_analysis_scope ruff_check_scope)"
read -r -a RUFF_FORMAT_SCOPE <<<"$(static_analysis_scope ruff_format_scope)"
run_governance_step "ruff" run_module ruff check "${RUFF_CHECK_SCOPE[@]}"
run_governance_step "ruff_format" run_module ruff format --check "${RUFF_FORMAT_SCOPE[@]}"
run_governance_step "ruff_c901" run_module ruff check --select C901 "${RUFF_CHECK_SCOPE[@]}"
run_step "arch_metrics"   "$PYTHON_BIN" scripts/arch_metrics.py
run_governance_step "arch_metrics_soft_gate" ./scripts/check_architecture_metrics_soft_gate.sh
run_governance_step "arch_metrics_budgets" ./scripts/check_architecture_metric_budgets.sh

# Keep pytest quiet and bounded in interactive mode
PYTEST_ARGS=(-q --maxfail=1 --disable-warnings)
if [[ "$CODEX_MODE" == "1" ]]; then
  PYTEST_ARGS+=(--basetemp="$TET4D_STATE_ROOT/pytest_basetemp" -p no:cacheprovider -p no:tmpdir)
fi

run_step "pytest"         run_module pytest "${PYTEST_ARGS[@]}"

run_step "playbot_stability" "$PYTHON_BIN" tools/stability/check_playbot_stability.py --repeats "$STABILITY_REPEATS" --seed-base "$STABILITY_SEED_BASE"

run_step "compileall"     "$PYTHON_BIN" -m compileall -q front.py cli/__init__.py cli/front.py cli/front2d.py cli/front3d.py cli/front4d.py src/tet4d src/tet4d/engine
run_step "bench_playbot"  "$PYTHON_BIN" tools/benchmarks/bench_playbot.py --assert --record-trend

echo "verify: OK"
