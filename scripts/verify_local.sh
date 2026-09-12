#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# A convenience launcher for the canonical gate, and nothing else. It used to
# own a worktree `.venv` -- creating it, installing the project editable into
# it, and repairing that install -- which made verification a process that could
# change the environment it was about to verify. Environment mutation now has
# one owner, `bootstrap_env.sh`, and this only reports when the environment is
# not ready.
#
# `--rebuild-venv` is gone with the venv it rebuilt. It has no meaning here now:
# nothing in this path creates or replaces an environment.

if [[ "$#" -ne 0 ]]; then
  echo "Usage: ./scripts/verify_local.sh" >&2
  exit 2
fi

if ! ./gov doctor >/dev/null 2>&1; then
  echo "local verify: the governed environment is not ready" >&2
  ./gov doctor >&2 || true
  echo "local verify: prepare it with ./scripts/bootstrap_env.sh" >&2
  exit 1
fi

exec env CODEX_MODE="${CODEX_MODE:-1}" QUIET="${QUIET:-1}" ./scripts/verify.sh
