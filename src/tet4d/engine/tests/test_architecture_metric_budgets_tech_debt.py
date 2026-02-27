from __future__ import annotations

import unittest

from tools.governance.tech_debt_budget import evaluate_tech_debt_gate


def _base_metrics() -> dict:
    return {
        "arch_stage": 531,
        "tech_debt": {
            "score": 28.4,
            "status": "moderate",
        },
    }


def _base_gate_config() -> dict:
    return {
        "score_epsilon": 0.1,
        "status_order": {
            "low": 0,
            "moderate": 1,
            "high": 2,
            "critical": 3,
        },
        "baseline": {
            "arch_stage": 530,
            "score": 30.0,
            "status": "moderate",
        },
    }


class TestArchitectureMetricBudgetsTechDebt(unittest.TestCase):
    def test_passes_when_stage_advances_and_score_decreases(self) -> None:
        self.assertEqual(evaluate_tech_debt_gate(_base_metrics(), _base_gate_config()), [])

    def test_fails_when_stage_advances_without_strict_decrease(self) -> None:
        metrics = _base_metrics()
        metrics["tech_debt"]["score"] = 29.95
        violations = evaluate_tech_debt_gate(metrics, _base_gate_config())
        self.assertEqual(len(violations), 1)
        self.assertIn("must strictly decrease", violations[0])

    def test_fails_when_status_worsens(self) -> None:
        metrics = _base_metrics()
        metrics["tech_debt"]["status"] = "high"
        violations = evaluate_tech_debt_gate(metrics, _base_gate_config())
        self.assertEqual(len(violations), 1)
        self.assertIn("status worsened", violations[0])

    def test_fails_when_stage_regresses(self) -> None:
        metrics = _base_metrics()
        metrics["arch_stage"] = 529
        violations = evaluate_tech_debt_gate(metrics, _base_gate_config())
        self.assertEqual(len(violations), 1)
        self.assertIn("arch_stage regressed", violations[0])

    def test_fails_when_score_regresses_within_same_stage(self) -> None:
        metrics = _base_metrics()
        metrics["arch_stage"] = 530
        metrics["tech_debt"]["score"] = 30.3
        violations = evaluate_tech_debt_gate(metrics, _base_gate_config())
        self.assertEqual(len(violations), 1)
        self.assertIn("score regressed within baseline stage", violations[0])

    def test_reports_missing_tech_debt(self) -> None:
        metrics = {"arch_stage": 531}
        violations = evaluate_tech_debt_gate(metrics, _base_gate_config())
        self.assertEqual(len(violations), 2)
        self.assertIn("missing tech_debt.score", violations)
        self.assertIn("missing tech_debt.status", violations)


if __name__ == "__main__":
    unittest.main()

