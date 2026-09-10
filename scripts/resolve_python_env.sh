#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -n "${TET4D_PYTHON:-}" ]]; then
  candidate="$TET4D_PYTHON"
  reason="explicit override TET4D_PYTHON"
elif [[ -n "${PYTHON_BIN:-}" ]]; then
  candidate="$PYTHON_BIN"
  reason="legacy approved override PYTHON_BIN"
else
  candidate=".venv/bin/python"
  reason="repository-local environment"
fi

if [[ ! -x "$candidate" ]]; then
  echo "ENVIRONMENT_INVALID: approved Python is not executable: $candidate" >&2
  echo "Create .venv with ./scripts/bootstrap_env.sh or set TET4D_PYTHON." >&2
  exit 1
fi

candidate="$($candidate -c 'from pathlib import Path; import sys; print(Path(sys.executable).absolute())')"
required_version="$(sed -n 's/^requires-python = ">=\([0-9][0-9]*\)\.\([0-9][0-9]*\)"/\1.\2/p' pyproject.toml | head -n 1)"
if [[ -z "$required_version" ]]; then
  echo "ENVIRONMENT_INVALID: cannot resolve project.requires-python from pyproject.toml" >&2
  exit 1
fi
if ! "$candidate" -c "import sys; required=tuple(map(int, '$required_version'.split('.'))); raise SystemExit(0 if sys.version_info[:2] >= required else 1)"; then
  echo "ENVIRONMENT_INVALID: Python $required_version or newer is required: $candidate" >&2
  exit 1
fi

if [[ "${GOV_ENV_VERBOSE:-0}" == "1" ]]; then
  echo "environment: $reason -> $candidate" >&2
fi
printf '%s\n' "$candidate"
