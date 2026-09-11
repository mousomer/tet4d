#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 0 ]]; then
  echo 'Usage: ./scripts/resolve_python_env.sh (prints interpreter only)' >&2
  exit 2
fi
cd "$(dirname "$0")/.."

# PYTHON_BIN is a compatibility output alias only. The governance resolver owns
# priority, local-overlay interpretation, requirement parsing, and diagnostics.
exec ./gov doctor --print-interpreter
