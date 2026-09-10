#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# PYTHON_BIN is a compatibility output alias only. The governance resolver owns
# priority, local-overlay interpretation, requirement parsing, and diagnostics.
exec ./gov doctor --print-interpreter
