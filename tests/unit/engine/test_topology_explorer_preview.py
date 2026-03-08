from __future__ import annotations

import shutil
import unittest
from uuid import uuid4

from tet4d.engine.gameplay.topology import EDGE_BOUNDED, EDGE_WRAP
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    validate_topology_profile_state,
)
from tet4d.engine.runtime.project_config import (
    explorer_topology_preview_dims,
    explorer_topology_preview_file_default_path,
    state_dir_path,
)
from tet4d.engine.runtime.topology_explorer_bridge import (
    explorer_profile_from_legacy_profile,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    compile_explorer_topology_preview,
    export_explorer_topology_preview,
)


class TestTopologyExplorerPreview(unittest.TestCase):
    def test_bridge_converts_symmetric_wrap_profile(self) -> None:
        legacy = validate_topology_profile_state(
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=3,
            gravity_axis=1,
            topology_mode="bounded",
            edge_rules=(
                (EDGE_WRAP, EDGE_WRAP),
                (EDGE_BOUNDED, EDGE_BOUNDED),
                (EDGE_BOUNDED, EDGE_BOUNDED),
            ),
        )
        profile = explorer_profile_from_legacy_profile(legacy)
        preview = compile_explorer_topology_preview(
            profile,
            dims=(4, 4, 4),
            source="legacy_edge_rules_bridge",
        )
        self.assertEqual(preview["glue_count"], 1)
        self.assertEqual(preview["movement_graph"]["cell_count"], 64)
        self.assertGreater(preview["movement_graph"]["boundary_traversal_count"], 0)

    def test_bridge_rejects_asymmetric_legacy_profile(self) -> None:
        legacy = validate_topology_profile_state(
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=3,
            gravity_axis=1,
            topology_mode="bounded",
            edge_rules=(
                (EDGE_WRAP, EDGE_BOUNDED),
                (EDGE_BOUNDED, EDGE_BOUNDED),
                (EDGE_BOUNDED, EDGE_BOUNDED),
            ),
        )
        with self.assertRaises(ValueError):
            explorer_profile_from_legacy_profile(legacy)

    def test_export_writes_preview_payload_to_runtime_path(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_preview_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            legacy = validate_topology_profile_state(
                gameplay_mode=GAMEPLAY_MODE_EXPLORER,
                dimension=4,
                gravity_axis=1,
                topology_mode="bounded",
                edge_rules=(
                    (EDGE_BOUNDED, EDGE_BOUNDED),
                    (EDGE_WRAP, EDGE_WRAP),
                    (EDGE_BOUNDED, EDGE_BOUNDED),
                    (EDGE_BOUNDED, EDGE_BOUNDED),
                ),
            )
            profile = explorer_profile_from_legacy_profile(legacy)
            dims = explorer_topology_preview_dims(4)
            ok, message, path = export_explorer_topology_preview(
                profile,
                dims=dims,
                source="legacy_edge_rules_bridge",
                root_dir=root,
            )
            self.assertTrue(ok, message)
            self.assertEqual(
                path, explorer_topology_preview_file_default_path(root_dir=root)
            )
            self.assertTrue(path.exists())
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
