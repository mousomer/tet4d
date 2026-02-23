#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

required_files=(
  "AGENTS.md"
  "config/project/policy_manifest.json"
  "scripts/verify.sh"
)

missing=0
for f in "${required_files[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing required policy file: $f" >&2
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  exit 2
fi

python3 tools/validate_project_contracts.py
python3 tools/scan_secrets.py
