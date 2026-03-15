#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

absolute_path_pattern='(/'"Users/"'|/'"home/"'|[A-Za-z]:\\)'
relative_parent_pattern='\.\./'

rg_usable() {
  command -v rg >/dev/null 2>&1 && rg --version >/dev/null 2>&1
}

search_repo_text() {
  local pattern="$1"
  if rg_usable; then
    rg -n -I --hidden \
      --glob '!**/.git/**' \
      --glob '!**/.venv/**' \
      --glob '!**/.idea/**' \
      --glob '!**/__pycache__/**' \
      --glob '!**/.pytest_cache/**' \
      --glob '!**/.pytest_tmp/**' \
      --glob '!**/.tmp_pytest/**' \
      --glob '!**/.tmp_pytest_run/**' \
      --glob '!**/.tmp_pytest_contracts/**' \
      --glob '!**/.tmp_test_leaderboard/**' \
      --glob '!**/state/**' \
      --glob '!**/dist/**' \
      --glob '!**/build/**' \
      --glob '!**/artifacts/**' \
      --glob '!**/context-*.instructions.md' \
      --glob '!**/check_git_sanitation.sh' \
      --glob '!**/check_git_sanitation_repo.sh' \
      "$pattern" .
    return
  fi
  grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=.idea \
    --exclude-dir=__pycache__ \
    --exclude-dir=.pytest_cache \
    --exclude-dir=.pytest_tmp \
    --exclude-dir=.tmp_pytest \
    --exclude-dir=.tmp_pytest_run \
    --exclude-dir=.tmp_pytest_contracts \
    --exclude-dir=.tmp_test_leaderboard \
    --exclude-dir=state \
    --exclude-dir=dist \
    --exclude-dir=build \
    --exclude-dir=artifacts \
    --exclude='context-*.instructions.md' \
    --exclude=check_git_sanitation.sh \
    --exclude=check_git_sanitation_repo.sh \
    --binary-files=without-match \
    "$pattern" .
}

search_docs_and_config_text() {
  local pattern="$1"
  if rg_usable; then
    rg -n -I "$pattern" config docs
    return
  fi
  grep -RInE --binary-files=without-match "$pattern" config docs
}

if search_repo_text "$absolute_path_pattern"; then
  echo "Absolute filesystem paths detected." >&2
  exit 2
fi

if search_docs_and_config_text "$relative_parent_pattern"; then
  echo "Potential unsafe path traversal patterns detected in docs/ or config/." >&2
  exit 2
fi

space_name="$({ git ls-files; git ls-files --others --exclude-standard; } | awk '/ /' | head -n 1)"

if [[ -n "$space_name" ]]; then
  echo "Filenames with spaces detected: ${space_name}" >&2
  exit 2
fi


required_exec_paths=(
  "scripts/bootstrap_env.sh"
  "scripts/check_architecture_boundaries.sh"
  "scripts/check_architecture_metric_budgets.sh"
  "scripts/check_architecture_metrics_soft_gate.sh"
  "scripts/check_editable_install.sh"
  "scripts/check_engine_core_purity.sh"
  "scripts/check_git_sanitation.sh"
  "scripts/check_git_sanitation_repo.sh"
  "scripts/check_policy_compliance.sh"
  "scripts/check_policy_compliance_repo.sh"
  "scripts/check_policy_template_drift.sh"
  "scripts/ci_check.sh"
  "scripts/ci_preflight.sh"
  "scripts/install_git_hooks.sh"
  "scripts/update_policy_template_hashes.sh"
  "scripts/verify.sh"
  "scripts/verify_focus.sh"
  ".githooks/pre-push"
)

for exec_path in "${required_exec_paths[@]}"; do
  mode_line="$(git ls-files --stage -- "$exec_path")"
  if [[ -z "$mode_line" ]]; then
    echo "Required executable entrypoint missing from git index: $exec_path" >&2
    exit 2
  fi
  mode="${mode_line%% *}"
  if [[ "$mode" != "100755" ]]; then
    echo "Executable bit missing for direct-run shell entrypoint: $exec_path (mode $mode)" >&2
    exit 2
  fi
done
