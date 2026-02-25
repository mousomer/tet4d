#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# CI/local CI wrapper delegates to the canonical verification pipeline.
QUIET="${QUIET:-1}"
CODEX_MODE="${CODEX_MODE:-0}"

export QUIET
export CODEX_MODE

exec ./scripts/verify.sh
