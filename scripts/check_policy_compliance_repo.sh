#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Standalone and always-on CI coverage includes extensions and both shared checks.
# Source the extension body so its governed environment is resolved once and
# supplies the exact interpreter/binding for the canonical shared checks below.
source ./scripts/check_policy_compliance_extensions_repo.sh

"$PYTHON_BIN" tools/governance/validate_project_contracts.py
"$PYTHON_BIN" tools/governance/scan_secrets.py
