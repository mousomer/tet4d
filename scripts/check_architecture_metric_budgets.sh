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

tmp_json="$(mktemp -t tet4d_arch_metrics.XXXXXX.json)"
trap 'rm -f "$tmp_json"' EXIT

"$PYTHON_BIN" scripts/arch_metrics.py >"$tmp_json"

"$PYTHON_BIN" - "$tmp_json" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
metrics = json.loads(path.read_text(encoding="utf-8"))


def get(metric_path: str) -> int:
    node = metrics
    for part in metric_path.split("."):
        node = node[part]
    if not isinstance(node, int):
        raise TypeError(f"{metric_path} is not an int: {node!r}")
    return node


# Stage 21 baseline budgets (non-increasing debt lock).
budgets = {
    "engine_core_purity.violation_count": 0,
    "deep_imports.engine_core_to_engine_non_core_imports.count": 0,
    "deep_imports.ui_to_engine_non_api.count": 0,
    "deep_imports.replay_to_engine_non_api.count": 0,
    "deep_imports.ai_to_engine_non_api.count": 0,
    "deep_imports.tools_stability_to_engine_non_api.count": 0,
    "deep_imports.tools_benchmarks_to_engine_non_api.count": 0,
    "deep_imports.external_callers_to_engine_playbot.count": 0,
    "migration_debt_signals.core_step_state_method_calls.count": 0,
    "migration_debt_signals.core_step_private_state_method_calls.count": 0,
    "migration_debt_signals.core_step_state_field_assignments.count": 0,
    "migration_debt_signals.core_rules_private_state_method_calls.count": 0,
    "migration_debt_signals.pygame_imports_non_test.count": 39,
    "migration_debt_signals.file_io_calls_non_test.count": 16,
    "migration_debt_signals.random_imports_non_test.count": 11,
    "migration_debt_signals.time_imports_non_test.count": 3,
}

violations: list[str] = []
for metric_path, budget in budgets.items():
    value = get(metric_path)
    if value > budget:
        violations.append(f"{metric_path}: {value} > budget {budget}")

if violations:
    print("Architecture metric budget violations:", file=sys.stderr)
    for line in violations:
        print(f"  - {line}", file=sys.stderr)
    raise SystemExit(2)
PY
