#!/usr/bin/env bash
set -euo pipefail
GOVERNANCE_REPO_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$GOVERNANCE_REPO_ROOT"
if GOVERNED_ENV="$(./gov env 2>/dev/null)"; then
  :
else
  GOV_ENV_STATUS=$?
  printf 'environment_resolution: failed (exit=%s); review the declared interpreter and machine overlay through the owning resolver.\n' "$GOV_ENV_STATUS" >&2
  exit "$GOV_ENV_STATUS"
fi
eval "$GOVERNED_ENV"
export GOVERNANCE_PYTHON="$PYTHON_BIN"

run_governance_check() {
  local name="$1"; shift
  "$PYTHON_BIN" tools/workspace_governance/diagnostics.py --checker "$name" --run "$@"
}

run_governance_check environment ./gov doctor --json
run_governance_check workspace_check ./gov check --generated --summary --json
run_governance_check policy_compliance bash scripts/check_policy_compliance.sh .
run_governance_check git_sanitation bash scripts/check_git_sanitation.sh .
run_governance_check template_drift bash scripts/check_policy_template_drift.sh .
run_governance_check pack_sanitation "$PYTHON_BIN" tools/workspace_governance/sanitation.py --root .
run_governance_check governance_inventory "$PYTHON_BIN" tools/governance/export_governance_inventory.py --check
