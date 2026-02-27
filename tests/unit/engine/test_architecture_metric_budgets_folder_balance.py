from __future__ import annotations

import unittest

from tools.governance.folder_balance_budget import evaluate_folder_balance_gate


def _base_metrics() -> dict:
    return {
        "folder_balance": {
            "folders": [
                {
                    "path": "src/tet4d/engine/runtime",
                    "leaf_folder": True,
                    "folder_profile": "default_leaf",
                    "balancer": {
                        "fuzzy_weighted_score": 0.71,
                        "fuzzy_weighted_status": "watch",
                    },
                },
                {
                    "path": "tests/unit/engine",
                    "leaf_folder": True,
                    "folder_profile": "tests_leaf",
                    "balancer": {
                        "fuzzy_weighted_score": 1.0,
                        "fuzzy_weighted_status": "balanced",
                    },
                },
            ]
        }
    }


def _base_gate_config() -> dict:
    return {
        "score_epsilon": 0.02,
        "status_order": {
            "balanced": 0,
            "watch": 1,
            "skewed": 2,
            "rebalance_signal": 3,
        },
        "tracked_leaf_folders": [
            {
                "path": "src/tet4d/engine/runtime",
                "profile": "default_leaf",
                "baseline_score": 0.71,
                "baseline_status": "watch",
            }
        ],
    }


class TestArchitectureMetricBudgetsFolderBalance(unittest.TestCase):
    def test_passes_when_score_and_status_match_baseline(self) -> None:
        self.assertEqual(evaluate_folder_balance_gate(_base_metrics(), _base_gate_config()), [])

    def test_passes_when_score_drops_within_epsilon(self) -> None:
        metrics = _base_metrics()
        metrics["folder_balance"]["folders"][0]["balancer"]["fuzzy_weighted_score"] = 0.70
        self.assertEqual(evaluate_folder_balance_gate(metrics, _base_gate_config()), [])

    def test_fails_when_status_worsens_even_if_score_close(self) -> None:
        metrics = _base_metrics()
        metrics["folder_balance"]["folders"][0]["balancer"]["fuzzy_weighted_score"] = 0.70
        metrics["folder_balance"]["folders"][0]["balancer"]["fuzzy_weighted_status"] = "skewed"
        violations = evaluate_folder_balance_gate(metrics, _base_gate_config())
        self.assertEqual(len(violations), 1)
        self.assertIn("status worsened", violations[0])

    def test_fails_when_score_drops_beyond_epsilon(self) -> None:
        metrics = _base_metrics()
        metrics["folder_balance"]["folders"][0]["balancer"]["fuzzy_weighted_score"] = 0.68
        violations = evaluate_folder_balance_gate(metrics, _base_gate_config())
        self.assertEqual(len(violations), 1)
        self.assertIn("score regressed", violations[0])

    def test_fails_when_tracked_folder_missing(self) -> None:
        metrics = {"folder_balance": {"folders": []}}
        violations = evaluate_folder_balance_gate(metrics, _base_gate_config())
        self.assertEqual(len(violations), 1)
        self.assertIn("folder missing", violations[0])

    def test_fails_when_tracked_folder_is_non_leaf(self) -> None:
        metrics = _base_metrics()
        metrics["folder_balance"]["folders"][0]["leaf_folder"] = False
        violations = evaluate_folder_balance_gate(metrics, _base_gate_config())
        self.assertEqual(len(violations), 1)
        self.assertIn("not a leaf_folder", violations[0])

    def test_fails_on_profile_mismatch(self) -> None:
        metrics = _base_metrics()
        metrics["folder_balance"]["folders"][0]["folder_profile"] = "tests_leaf"
        violations = evaluate_folder_balance_gate(metrics, _base_gate_config())
        self.assertEqual(len(violations), 1)
        self.assertIn("profile mismatch", violations[0])


if __name__ == "__main__":
    unittest.main()
