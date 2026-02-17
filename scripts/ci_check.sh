#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ruff check .
pytest -q
python3 tools/bench_playbot.py --assert
