from __future__ import annotations

import json
import shutil
import unittest
from uuid import uuid4

from tet4d.engine.runtime.project_config import (
    explorer_topology_experiments_file_default_path,
    state_dir_path,
)
from tet4d.engine.runtime.topology_explorer_experiments import (
    compile_parallel_explorer_experiments,
    export_parallel_explorer_experiments,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile


class TestTopologyExplorerExperiments(unittest.TestCase):
    def test_compile_parallel_explorer_experiments_recommends_full_wrap_for_3d(self) -> None:
        batch = compile_parallel_explorer_experiments(
            ExplorerTopologyProfile(dimension=3, gluings=()),
            dims=(4, 4, 4),
            source="unit_test",
        )

        self.assertEqual(batch["dimension"], 3)
        self.assertEqual(batch["experiment_count"], 7)
        self.assertEqual(batch["valid_experiment_count"], 7)
        self.assertEqual(batch["experiments"][0]["id"], "current_draft")
        self.assertEqual(batch["recommendation"]["label"], "Wrap X,Y,Z")
        self.assertIn("boundary traversals", batch["recommendation"]["reason"])

    def test_export_parallel_explorer_experiments_writes_runtime_payload(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_experiments_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            ok, message, path = export_parallel_explorer_experiments(
                ExplorerTopologyProfile(dimension=4, gluings=()),
                dims=(4, 4, 4, 4),
                source="unit_test",
                root_dir=root,
            )
            self.assertTrue(ok, message)
            self.assertEqual(
                path,
                explorer_topology_experiments_file_default_path(root_dir=root),
            )
            assert path is not None
            self.assertTrue(path.exists())
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["dimension"], 4)
            self.assertGreaterEqual(payload["valid_experiment_count"], 1)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
