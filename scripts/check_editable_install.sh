#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -n "${PYTHON_BIN:-}" ]]; then
  :
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "No Python runtime found. Set PYTHON_BIN or install python3." >&2
  exit 1
fi

"$PYTHON_BIN" -c "from pathlib import Path; import tet4d; repo = Path.cwd().resolve(); pkg_root = Path(tet4d.__file__).resolve().parent; expected = repo / 'src' / 'tet4d'; raise SystemExit(0 if pkg_root == expected else f'Expected editable install from {expected}, got {pkg_root}')"
