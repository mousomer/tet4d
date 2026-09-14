#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# A drive designator is a path only when it begins at a token boundary. This
# keeps serialized escapes such as ``Total:\\nLine2`` and ``Rate:\\ttab`` out
# of scope, while accepting every valid drive-rooted path (including one-part
# roots such as ``C:\\projects``) and JSON-escaped backslashes.
absolute_path_pattern='(/'"Users/"'|/'"home/"'|(^|[^A-Za-z0-9_])[A-Za-z]:[\\/]+)'
relative_parent_pattern='\.\./'

rg_usable() {
  command -v rg >/dev/null 2>&1 && rg --version >/dev/null 2>&1
}

search_repo_text() {
  local pattern="$1"
  # The governance validator must contain the literal forms it rejects.
  local validator_literal_path='tools/workspace_governance/validators/core.py'
  if rg_usable; then
    rg -n -I --hidden \
      --glob '!**/.git' \
      --glob '!**/.git/**' \
      --glob '!**/.claude/**' \
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
      --glob '!native/third_party/**' \
      --glob '!**/artifacts/**' \
      --glob '!**/context-*.instructions.md' \
      --glob '!**/check_git_sanitation.sh' \
      --glob '!**/check_git_sanitation_repo.sh' \
      --glob "!${validator_literal_path}" \
      "$pattern" .
    return
  fi
  grep -RInE \
    --exclude=.git \
    --exclude-dir=.git \
    --exclude-dir=.claude \
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
    --exclude-dir=third_party \
    --exclude-dir=artifacts \
    --exclude='context-*.instructions.md' \
    --exclude=check_git_sanitation.sh \
    --exclude=check_git_sanitation_repo.sh \
    --binary-files=without-match \
    "$pattern" . | grep -v "^./${validator_literal_path}:"
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

ignored_tracked_paths=()
while IFS= read -r -d '' ignored_tracked_path; do
  ignored_tracked_paths+=("$ignored_tracked_path")
done < <(
  # Repository sanitation uses repository-owned .gitignore files only; user/global
  # excludes and .git/info/exclude must not determine repository cleanliness.
  git ls-files -ci --exclude-per-directory=.gitignore -z
)

if ((${#ignored_tracked_paths[@]} > 0)); then
  echo "Tracked files matched by repository ignore rules:" >&2
  printf '  %q\n' "${ignored_tracked_paths[@]}" >&2
  exit 2
fi

space_name="$({ git ls-files; git ls-files --others --exclude-standard; } | awk '/ /' | head -n 1)"

if [[ -n "$space_name" ]]; then
  echo "Filenames with spaces detected: ${space_name}" >&2
  exit 2
fi


required_exec_paths=(
  "gov"
  "scripts/bootstrap_env.sh"
  "scripts/check_architecture_boundaries.sh"
  "scripts/check_architecture_metric_budgets.sh"
  "scripts/check_architecture_metrics_soft_gate.sh"
  "scripts/check_engine_core_purity.sh"
  "scripts/check_git_sanitation.sh"
  "scripts/check_git_sanitation_repo.sh"
  "scripts/check_policy_compliance.sh"
  "scripts/check_policy_compliance_repo.sh"
  "scripts/check_policy_template_drift.sh"
  "scripts/ci_check.sh"
  "scripts/ci_preflight.sh"
  "scripts/install_git_hooks.sh"
  "scripts/resolve_bootstrap_python.sh"
  "scripts/resolve_python_env.sh"
  "scripts/update_policy_template_hashes.sh"
  "scripts/verify.sh"
  "scripts/verify_local.sh"
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
