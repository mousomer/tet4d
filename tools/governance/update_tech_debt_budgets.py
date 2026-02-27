#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


REPO_ROOT = _repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.governance.tech_debt_budget import refresh_tech_debt_budgets  # noqa: E402


def main() -> int:
    budgets_path = REPO_ROOT / "config" / "project" / "tech_debt_budgets.json"
    if not budgets_path.exists():
        print(f"Missing config: {budgets_path}", file=sys.stderr)
        return 1

    metrics_proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "arch_metrics.py")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if metrics_proc.returncode != 0:
        print(metrics_proc.stdout, end="", file=sys.stderr)
        print(metrics_proc.stderr, end="", file=sys.stderr)
        return metrics_proc.returncode

    metrics = json.loads(metrics_proc.stdout)
    gate_config = json.loads(budgets_path.read_text(encoding="utf-8"))
    updated = refresh_tech_debt_budgets(metrics, gate_config)
    budgets_path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    baseline = updated.get("baseline", {})
    if isinstance(baseline, dict):
        print(
            f"arch_stage={baseline.get('arch_stage')} "
            f"score={baseline.get('score')} status={baseline.get('status')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

