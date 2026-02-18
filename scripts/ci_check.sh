#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

ruff check .
"$PYTHON_BIN" tools/validate_project_contracts.py
pytest -q
PYTHONPATH=. "$PYTHON_BIN" tools/check_playbot_stability.py --repeats 20 --seed-base 0
"$PYTHON_BIN" -m compileall -q front.py front2d.py front3d.py front4d.py tetris_nd
"$PYTHON_BIN" tools/bench_playbot.py --assert --record-trend
