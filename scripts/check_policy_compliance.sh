#!/usr/bin/env bash
set -euo pipefail

echo "Checking required files and directories..."

REQUIRED_FILES=(
  "scripts/verify.sh"
  "scripts/check_git_sanitation.sh"
  "scripts/check_policy_compliance.sh"
  "scripts/check_policy_template_drift.sh"
)

REQUIRED_DIRS=(
  "docs"
  "scripts"
  ".policy"
)

FAILED=0

for file in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    echo "Missing required file: $file"
    FAILED=1
  fi
done

# Optional workspace policy-kit markers may exist locally but are not required in
# a fresh public-repo clone (for example GitHub CI checkout).
OPTIONAL_WORKSPACE_FILES=(
  ".workspace_policy_version.json"
  ".policy/policy_template_hashes.json"
)

for file in "${OPTIONAL_WORKSPACE_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    continue
  fi
done

for dir in "${REQUIRED_DIRS[@]}"; do
  if [ ! -d "$dir" ]; then
    echo "Missing required directory: $dir"
    FAILED=1
  fi
done

if [ "$FAILED" -ne 0 ]; then
  echo "Policy compliance check failed."
  exit 1
fi

./scripts/check_text_formatting.sh

echo "Policy compliance check complete."
