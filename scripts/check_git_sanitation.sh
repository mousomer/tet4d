#!/usr/bin/env bash
set -euo pipefail

REPO_PATH="${1:-.}"
TET4D_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SANITATION_PYTHON="$("$TET4D_ROOT/scripts/resolve_python_env.sh")"
cd "$REPO_PATH"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: $REPO_PATH is not a git repository" >&2
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "Running git sanitation checks..."
warn_count=0

filter_references() {
  "$SANITATION_PYTHON" "$TET4D_ROOT/tools/governance/filter_sanitation_findings.py" \
    "$REPO_ROOT" "$1"
}

# Limit baseline scanning to git-visible files to avoid noisy ignored/untracked trees
# (for example local virtual environments) and use -I/-F for binary-safe fixed-string scans.
unix_abs_paths="$( { git grep -nIF '/home/' -- . ':!*.png' ':!*.jpg' ':!*.jpeg' ':!*.gif' ':!*.pdf' ':!scripts/check_git_sanitation.sh' || true; } | filter_references absolute-unix)"
windows_abs_paths="$( { git grep -nIF 'C:\' -- . ':!*.png' ':!*.jpg' ':!*.jpeg' ':!*.gif' ':!*.pdf' ':!scripts/check_git_sanitation.sh' || true; } | filter_references absolute-windows)"
traversal_patterns="$( { git grep -nIF '../' -- . ':!*.png' ':!*.jpg' ':!*.jpeg' ':!*.gif' ':!*.pdf' ':!scripts/check_git_sanitation.sh' || true; } | filter_references parent-traversal)"
spaced_names="$({ git ls-files; git ls-files --others --exclude-standard; } | awk '/ /')"

if [[ -n "$unix_abs_paths" ]]; then
  echo "WARN: absolute Unix paths found in git-visible text files"
  echo "$unix_abs_paths"
  warn_count=$((warn_count + 1))
fi
if [[ -n "$windows_abs_paths" ]]; then
  echo "WARN: absolute Windows paths found in git-visible text files"
  echo "$windows_abs_paths"
  warn_count=$((warn_count + 1))
fi
if [[ -n "$traversal_patterns" ]]; then
  echo "WARN: '../' patterns found in git-visible text files"
  echo "$traversal_patterns"
  warn_count=$((warn_count + 1))
fi
if [[ -n "$spaced_names" ]]; then
  echo "WARN: filenames with spaces detected (tracked or untracked, excluding ignored)"
  echo "$spaced_names"
  warn_count=$((warn_count + 1))
fi

if [[ "$warn_count" -gt 0 ]]; then
  echo "WARN: sanitation checks reported $warn_count issue class(es)"
fi

echo "Sanitation check complete."
