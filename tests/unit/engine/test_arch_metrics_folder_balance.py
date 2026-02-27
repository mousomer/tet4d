from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


def _project_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "scripts" / "arch_metrics.py").exists():
            return candidate
    return here.parents[4]


PROJECT_ROOT = _project_root()
ARCH_METRICS_PATH = PROJECT_ROOT / "scripts" / "arch_metrics.py"


def _load_arch_metrics_module():
    spec = importlib.util.spec_from_file_location(
        "tet4d_arch_metrics_script", ARCH_METRICS_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load arch_metrics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestArchMetricsFolderBalance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_arch_metrics_module()

    def test_margin_plateau_keeps_score_at_one(self) -> None:
        score_min_edge = self.mod._fuzzy_band_score(
            value=5,
            target_min=6,
            target_max=15,
            soft_min=2,
            soft_max=28,
            target_margin=1,
        )
        score_max_edge = self.mod._fuzzy_band_score(
            value=16,
            target_min=6,
            target_max=15,
            soft_min=2,
            soft_max=28,
            target_margin=1,
        )
        self.assertEqual(score_min_edge, 1.0)
        self.assertEqual(score_max_edge, 1.0)

    def test_decay_starts_after_margin(self) -> None:
        score = self.mod._fuzzy_band_score(
            value=17,
            target_min=6,
            target_max=15,
            soft_min=2,
            soft_max=28,
            target_margin=1,
        )
        self.assertLess(score, 1.0)
        self.assertGreater(score, 0.0)

    def test_soft_bound_clamps_to_zero(self) -> None:
        low_score = self.mod._fuzzy_band_score(
            value=2,
            target_min=6,
            target_max=15,
            soft_min=2,
            soft_max=28,
            target_margin=1,
        )
        high_score = self.mod._fuzzy_band_score(
            value=28,
            target_min=6,
            target_max=15,
            soft_min=2,
            soft_max=28,
            target_margin=1,
        )
        self.assertEqual(low_score, 0.0)
        self.assertEqual(high_score, 0.0)

    def test_profile_classification(self) -> None:
        cfg = self.mod._architecture_metrics_config()
        class_cfg = cfg.get("classification", {})
        class_to_profile = self.mod._folder_balance_class_to_profile()
        self.assertEqual(
            self.mod._folder_balance_profile_for_folder(
                "tests/unit/engine",
                leaf_folder=True,
                class_cfg=class_cfg,
                class_to_profile=class_to_profile,
            ),
            "tests_leaf",
        )
        self.assertEqual(
            self.mod._folder_balance_profile_for_folder(
                "src/tet4d/engine/runtime",
                leaf_folder=True,
                class_cfg=class_cfg,
                class_to_profile=class_to_profile,
            ),
            "default_leaf",
        )
        self.assertEqual(
            self.mod._folder_balance_profile_for_folder(
                "src/tet4d/engine/core/step",
                leaf_folder=True,
                class_cfg=class_cfg,
                class_to_profile=class_to_profile,
            ),
            "micro_leaf",
        )
        self.assertIsNone(
            self.mod._folder_balance_profile_for_folder(
                "src/tet4d/ui/pygame",
                leaf_folder=False,
                class_cfg=class_cfg,
                class_to_profile=class_to_profile,
            )
        )

    def test_keybinding_retention_signal_is_available(self) -> None:
        signal = self.mod._build_keybinding_retention_signal()
        self.assertTrue(signal["available"], signal.get("error"))
        self.assertGreater(signal["expected_count"], 0)
        self.assertGreaterEqual(signal["coverage_ratio"], 0.0)
        self.assertLessEqual(signal["coverage_ratio"], 1.0)
        self.assertIn(signal.get("source"), {"pygame_runtime", "pygame_stub"})

    def test_delivery_size_pressure_increases_with_higher_loc_and_files(self) -> None:
        low_metrics = {
            "stage_loc_logger": {
                "overall_python_loc": 1000,
                "overall_python_file_count": 20,
                "by_source_root_loc": {
                    "src/tet4d": 1000,
                    "tests": 0,
                    "tools": 0,
                    "scripts": 0,
                },
                "by_source_root_file_count": {
                    "src/tet4d": 20,
                    "tests": 0,
                    "tools": 0,
                    "scripts": 0,
                },
            }
        }
        high_metrics = {
            "stage_loc_logger": {
                "overall_python_loc": 30000,
                "overall_python_file_count": 190,
                "by_source_root_loc": {
                    "src/tet4d": 20000,
                    "tests": 8000,
                    "tools": 1500,
                    "scripts": 500,
                },
                "by_source_root_file_count": {
                    "src/tet4d": 120,
                    "tests": 50,
                    "tools": 15,
                    "scripts": 5,
                },
            }
        }
        with patch.object(self.mod, "_ci_gate_violations", return_value=([], [])):
            low_debt = self.mod._build_tech_debt(low_metrics)
            high_debt = self.mod._build_tech_debt(high_metrics)
        low_pressure = low_debt["components"]["delivery_size_pressure"]["pressure"]
        high_pressure = high_debt["components"]["delivery_size_pressure"]["pressure"]
        self.assertLess(low_pressure, high_pressure)
        self.assertLess(low_debt["score"], high_debt["score"])

    def test_backlog_debt_uses_canonical_json_only(self) -> None:
        with patch.object(
            self.mod,
            "BACKLOG_DEBT_PATH",
            PROJECT_ROOT / "config/project/backlog_debt.json",
        ):
            rows = self.mod._active_backlog_rows()
        self.assertIsInstance(rows, list)

    def test_backlog_debt_missing_json_raises(self) -> None:
        with patch.object(
            self.mod,
            "BACKLOG_DEBT_PATH",
            PROJECT_ROOT / "config/project/does_not_exist_backlog_debt.json",
        ):
            with self.assertRaises(RuntimeError):
                self.mod._active_backlog_rows()

    def test_script_output_preserves_core_keys_and_adds_folder_balance_fields(
        self,
    ) -> None:
        proc = subprocess.run(
            [sys.executable, str(ARCH_METRICS_PATH)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertIn("deep_imports", data)
        self.assertIn("engine_core_purity", data)
        self.assertIn("migration_debt_signals", data)
        self.assertIn("folder_balance", data)
        self.assertIn("tech_debt", data)

        folder_balance = data["folder_balance"]
        self.assertIn("gate", folder_balance)
        self.assertIn("heuristic", folder_balance)
        self.assertIn("profiles", folder_balance["heuristic"])
        self.assertIn("components", data["tech_debt"])
        self.assertIn("score", data["tech_debt"])
        self.assertIn("keybinding_retention", data["tech_debt"]["components"])
        self.assertIn("menu_simplification", data["tech_debt"]["components"])
        self.assertIn("delivery_size_pressure", data["tech_debt"]["components"])
        self.assertIn("weighted_component_contributions", data["tech_debt"])
        self.assertGreaterEqual(
            data["tech_debt"]["components"]["keybinding_retention"]["pressure"], 0.0
        )
        self.assertLessEqual(
            data["tech_debt"]["components"]["keybinding_retention"]["pressure"], 1.0
        )
        self.assertGreaterEqual(
            data["tech_debt"]["components"]["menu_simplification"]["pressure"], 0.0
        )
        self.assertLessEqual(
            data["tech_debt"]["components"]["menu_simplification"]["pressure"], 1.0
        )
        self.assertGreaterEqual(
            data["tech_debt"]["components"]["delivery_size_pressure"]["pressure"], 0.0
        )
        self.assertGreater(
            data["tech_debt"]["components"]["delivery_size_pressure"][
                "weighted_contribution"
            ],
            0.0,
        )
        self.assertTrue(
            all(
                float(value) >= 0.0
                for value in data["tech_debt"][
                    "weighted_component_contributions"
                ].values()
            )
        )

        runtime_row = next(
            row
            for row in folder_balance["folders"]
            if row["path"] == "src/tet4d/engine/runtime"
        )
        core_step_row = next(
            row
            for row in folder_balance["folders"]
            if row["path"] == "src/tet4d/engine/core/step"
        )
        core_rng_row = next(
            row
            for row in folder_balance["folders"]
            if row["path"] == "src/tet4d/engine/core/rng"
        )
        tests_row = next(
            row
            for row in folder_balance["folders"]
            if row["path"] == "tests/unit/engine"
        )
        ui_parent_row = next(
            row
            for row in folder_balance["folders"]
            if row["path"] == "src/tet4d/ui/pygame"
        )
        self.assertEqual(runtime_row["folder_profile"], "default_leaf")
        self.assertEqual(core_step_row["folder_profile"], "micro_leaf")
        self.assertEqual(core_rng_row["folder_profile"], "micro_leaf")
        self.assertEqual(tests_row["folder_profile"], "tests_leaf")
        self.assertEqual(core_step_row["folder_class"], "micro_core_leaf")
        self.assertEqual(core_rng_row["folder_class"], "micro_core_leaf")
        self.assertEqual(runtime_row["folder_class"], "code_default")
        self.assertEqual(tests_row["folder_class"], "tests_lenient")
        self.assertTrue(runtime_row["gate_eligible"])
        self.assertFalse(runtime_row["exclude_from_code_balance"])
        self.assertTrue(isinstance(runtime_row["gate_candidate"], bool))
        self.assertIn(
            "gate_eligible_leaf_fuzzy_weighted_balance_score_avg",
            folder_balance["summary"],
        )
        self.assertIsNone(ui_parent_row["folder_profile"])


if __name__ == "__main__":
    unittest.main()
