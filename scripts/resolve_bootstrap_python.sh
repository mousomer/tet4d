#!/usr/bin/env bash
set -euo pipefail

# Bootstrap interpreter selection.
#
# This runs before a project environment is guaranteed to exist, so it must not
# import project code. It is deliberately separate from the certification chain
# owned by `gov doctor`: this only decides what may *start* governance, never
# what gets verified.
#
# System Python on PATH is never an approved bootstrap. A bare `python3` is not
# a declared toolchain, and accepting one silently changes what every later
# check runs against. Priority is explicit override, then the workspace venv,
# then the repository venv. There is no fallback: an unusable candidate fails.

cd "$(dirname "$0")/.."

candidates=()
if [[ -n "${GOVERNANCE_PYTHON:-}" ]]; then
  candidates+=("$GOVERNANCE_PYTHON")
fi
if [[ -n "${WORKSPACE_VENV:-}" ]]; then
  candidates+=("${WORKSPACE_VENV%/}/bin/python")
fi
candidates+=(".venv/bin/python")

for candidate in "${candidates[@]}"; do
  if [[ -x "$candidate" ]]; then
    printf '%s/%s\n' \
      "$(cd "$(dirname "$candidate")" && pwd)" "$(basename "$candidate")"
    exit 0
  fi
done

printf '%s\n' '{"status":"ENVIRONMENT_INVALID","diagnostics":[{"code":"ENVIRONMENT_MISMATCH","fact":"bootstrap.interpreter","owner":"environment","sources":["GOVERNANCE_PYTHON","WORKSPACE_VENV",".venv/bin/python"],"reason":"no approved bootstrap Python is executable; system Python on PATH is not an approved bootstrap","repair":"export WORKSPACE_VENV, set GOVERNANCE_PYTHON or PYTHON_BOOTSTRAP_BIN, or create .venv with ./scripts/bootstrap_env.sh"}]}' >&2
exit 1
