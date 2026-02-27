from __future__ import annotations

import unittest

from tools.governance.architecture_metric_budget import (
    evaluate_architecture_metric_budget_overages,
)


class TestArchitectureMetricBudgetCore(unittest.TestCase):
    def test_reports_over_budget_path(self) -> None:
        metrics = {
            "engine_core_purity": {"violation_count": 1},
            "deep_imports": {
                "engine_core_to_engine_non_core_imports": {"count": 0},
                "ui_to_engine_non_api": {"count": 0},
                "replay_to_engine_non_api": {"count": 0},
                "ai_to_engine_non_api": {"count": 0},
                "tools_stability_to_engine_non_api": {"count": 0},
                "tools_benchmarks_to_engine_non_api": {"count": 0},
                "external_callers_to_engine_playbot": {"count": 0},
            },
            "migration_debt_signals": {
                "core_step_state_method_calls": {"count": 0},
                "core_step_private_state_method_calls": {"count": 0},
                "core_step_state_field_assignments": {"count": 0},
                "core_rules_private_state_method_calls": {"count": 0},
                "pygame_imports_non_test": {"count": 0},
                "file_io_calls_non_test": {"count": 0},
                "random_imports_non_test": {"count": 0},
                "time_imports_non_test": {"count": 0},
            },
        }
        violations = evaluate_architecture_metric_budget_overages(metrics)
        self.assertEqual(len(violations), 1)
        self.assertIn("engine_core_purity.violation_count", violations[0])


if __name__ == "__main__":
    unittest.main()
