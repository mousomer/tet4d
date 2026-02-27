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

tmp_json="$(mktemp -t tet4d_arch_metrics_soft.XXXXXX.json)"
trap 'rm -f "$tmp_json"' EXIT

PYGAME_HIDE_SUPPORT_PROMPT=1 "$PYTHON_BIN" scripts/arch_metrics.py >"$tmp_json"

"$PYTHON_BIN" - "$tmp_json" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.governance.architecture_metric_budget import evaluate_architecture_metric_budget_overages
from tools.governance.folder_balance_budget import evaluate_folder_balance_gate
from tools.governance.tech_debt_budget import evaluate_tech_debt_gate

metrics_path = Path(sys.argv[1])
metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

violations: list[str] = []

try:
    violations.extend(evaluate_architecture_metric_budget_overages(metrics))

    folder_cfg_path = Path("config/project/folder_balance_budgets.json")
    if folder_cfg_path.exists():
        folder_cfg = json.loads(folder_cfg_path.read_text(encoding="utf-8"))
        violations.extend(evaluate_folder_balance_gate(metrics, folder_cfg))

    tech_cfg_path = Path("config/project/tech_debt_budgets.json")
    if tech_cfg_path.exists():
        tech_cfg = json.loads(tech_cfg_path.read_text(encoding="utf-8"))
        violations.extend(evaluate_tech_debt_gate(metrics, tech_cfg))
except Exception as exc:
    print(f"ERROR: architecture metrics soft-gate runtime/schema failure: {exc}", file=sys.stderr)
    raise SystemExit(2)

folder_summary = metrics.get("folder_balance", {}).get("summary", {})
folder_class_counts = folder_summary.get("folder_class_counts", {})
eligible_count = folder_summary.get("gate_eligible_leaf_folder_count")
eligible_score = folder_summary.get("gate_eligible_leaf_fuzzy_weighted_balance_score_avg")

print("Architecture metrics soft gate summary:")
print(f"  - gate_eligible_leaf_folder_count: {eligible_count}")
print(f"  - gate_eligible_leaf_fuzzy_weighted_balance_score_avg: {eligible_score}")
print(f"  - folder_class_counts: {folder_class_counts}")

if violations:
    print("Architecture metrics soft gate warnings:", file=sys.stderr)
    for line in violations:
        print(f"  - {line}", file=sys.stderr)

raise SystemExit(0)
PY
