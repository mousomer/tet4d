from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


def _project_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "scripts" / "arch_metrics.py").exists():
            return candidate
    return here.parents[4]


PROJECT_ROOT = _project_root()
ARCH_METRICS_PATH = PROJECT_ROOT / "scripts" / "arch_metrics.py"


def _load_arch_metrics_module():
    spec = importlib.util.spec_from_file_location("tet4d_arch_metrics_script", ARCH_METRICS_PATH)
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
        self.assertEqual(
            self.mod._folder_balance_profile_for_folder("src/tet4d/engine/tests", leaf_folder=True),
            "tests_leaf",
        )
        self.assertEqual(
            self.mod._folder_balance_profile_for_folder("src/tet4d/engine/runtime", leaf_folder=True),
            "default_leaf",
        )
        self.assertIsNone(
            self.mod._folder_balance_profile_for_folder("src/tet4d/ui/pygame", leaf_folder=False)
        )

    def test_script_output_preserves_core_keys_and_adds_folder_balance_fields(self) -> None:
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

        folder_balance = data["folder_balance"]
        self.assertIn("gate", folder_balance)
        self.assertIn("heuristic", folder_balance)
        self.assertIn("profiles", folder_balance["heuristic"])

        runtime_row = next(
            row for row in folder_balance["folders"] if row["path"] == "src/tet4d/engine/runtime"
        )
        tests_row = next(
            row for row in folder_balance["folders"] if row["path"] == "src/tet4d/engine/tests"
        )
        ui_parent_row = next(
            row for row in folder_balance["folders"] if row["path"] == "src/tet4d/ui/pygame"
        )
        self.assertEqual(runtime_row["folder_profile"], "default_leaf")
        self.assertEqual(tests_row["folder_profile"], "tests_leaf")
        self.assertTrue(isinstance(runtime_row["gate_candidate"], bool))
        self.assertIsNone(ui_parent_row["folder_profile"])


if __name__ == "__main__":
    unittest.main()
