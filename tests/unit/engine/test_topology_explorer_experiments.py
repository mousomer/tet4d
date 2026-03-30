from __future__ import annotations

import json
import shutil
import unittest
from unittest import mock
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
        self.assertEqual(batch["recommendation"]["label"], "3-Torus")
        self.assertIn("boundary traversals", batch["recommendation"]["reason"])

    def test_export_parallel_explorer_experiments_uses_precompiled_batch(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_experiments_cached_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = ExplorerTopologyProfile(dimension=3, gluings=())
            batch = compile_parallel_explorer_experiments(
                profile,
                dims=(4, 4, 4),
                source="topology_lab_3d_experiments",
            )
            with mock.patch(
                "tet4d.engine.runtime.topology_explorer_experiments.compile_parallel_explorer_experiments"
            ) as compile_batch:
                ok, message, path = export_parallel_explorer_experiments(
                    profile,
                    dims=(4, 4, 4),
                    source="topology_lab_3d_experiments",
                    root_dir=root,
                    batch_payload=batch,
                )
            self.assertTrue(ok, message)
            compile_batch.assert_not_called()
            assert path is not None
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["source"], "topology_lab_3d_experiments")
            self.assertEqual(payload["experiment_count"], batch["experiment_count"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

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
