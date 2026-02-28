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

from tools.governance.architecture_metric_budget import (
    evaluate_architecture_metric_budget_overages,
)
from tools.governance.folder_balance_budget import evaluate_folder_balance_gate
from tools.governance.tech_debt_budget import evaluate_tech_debt_gate

path = Path(sys.argv[1])
metrics = json.loads(path.read_text(encoding="utf-8"))
violations = evaluate_architecture_metric_budget_overages(metrics)

gate_cfg_path = Path("config/project/folder_balance_budgets.json")
if gate_cfg_path.exists():
    gate_cfg = json.loads(gate_cfg_path.read_text(encoding="utf-8"))
    violations.extend(evaluate_folder_balance_gate(metrics, gate_cfg))

tech_debt_cfg_path = Path("config/project/policy/manifests/tech_debt_budgets.json")
if tech_debt_cfg_path.exists():
    tech_debt_cfg = json.loads(tech_debt_cfg_path.read_text(encoding="utf-8"))
    violations.extend(evaluate_tech_debt_gate(metrics, tech_debt_cfg))

if violations:
    print("Architecture metric budget violations:", file=sys.stderr)
    for line in violations:
        print(f"  - {line}", file=sys.stderr)
    raise SystemExit(2)
PY
