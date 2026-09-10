#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BOOTSTRAP_BIN="${PYTHON_BOOTSTRAP_BIN:-python3}"
VENV_PATH="${VENV_PATH:-.venv}"
VENV_PYTHON="${VENV_PATH}/bin/python"

if [ ! -x "${VENV_PYTHON}" ]; then
  if ! "${PYTHON_BOOTSTRAP_BIN}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "ENVIRONMENT_INVALID: bootstrap Python 3.11 or newer is required." >&2
    exit 1
  fi
  "${PYTHON_BOOTSTRAP_BIN}" -m venv "${VENV_PATH}"
fi

PIP_ARGS=(--disable-pip-version-check --no-input)
"${VENV_PYTHON}" -m pip install "${PIP_ARGS[@]}" --upgrade pip
"${VENV_PYTHON}" -m pip install "${PIP_ARGS[@]}" -e ".[dev]"

./scripts/install_git_hooks.sh

echo "Environment bootstrap complete: ${VENV_PATH}"
echo "No activation is required; governed scripts resolve ${VENV_PYTHON} directly."
