#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BOOTSTRAP_BIN="${PYTHON_BOOTSTRAP_BIN:-python3}"
VENV_PATH="${VENV_PATH:-.venv}"
VENV_PYTHON="${VENV_PATH}/bin/python"

if [ ! -x "${VENV_PYTHON}" ]; then
  "${PYTHON_BOOTSTRAP_BIN}" -m venv "${VENV_PATH}"
fi

PIP_ARGS=(--disable-pip-version-check --no-input)
"${VENV_PYTHON}" -m pip install "${PIP_ARGS[@]}" --upgrade pip
"${VENV_PYTHON}" -m pip install "${PIP_ARGS[@]}" -e ".[dev]"

echo "Environment bootstrap complete: ${VENV_PATH}"
echo "Use it with: source ${VENV_PATH}/bin/activate"
