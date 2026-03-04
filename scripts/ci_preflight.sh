#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Local preflight defaults to quiet + Codex mode to keep output bounded.
QUIET="${QUIET:-1}"
CODEX_MODE="${CODEX_MODE:-1}"

export QUIET
export CODEX_MODE

scripts/check_git_sanitation.sh
scripts/check_policy_compliance.sh
if [[ "${CI_PREFLIGHT_STRICT_TEMPLATE:-0}" == "1" ]]; then
  scripts/check_policy_template_drift.sh
elif [[ -f ".policy/policy_template_hashes.json" ]]; then
  # Local policy-kit hash drift is informative but should not block CI preflight.
  scripts/check_policy_template_drift.sh || {
    echo "WARN: policy template drift detected (non-blocking in local preflight)." >&2
  }
fi
scripts/check_git_sanitation_repo.sh
scripts/check_policy_compliance_repo.sh
exec ./scripts/ci_check.sh
