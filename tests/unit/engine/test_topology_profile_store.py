from __future__ import annotations

import unittest
from uuid import uuid4

from tet4d.engine.runtime.project_config import state_dir_path

from tet4d.engine.gameplay.topology import EDGE_BOUNDED, EDGE_WRAP
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    validate_topology_profile_state,
)
from tet4d.engine.runtime.topology_profile_store import load_topology_profile, save_topology_profile


class TestTopologyProfileStore(unittest.TestCase):
    def test_normal_and_explorer_profiles_are_saved_separately(self) -> None:
        root = state_dir_path() / "pytest_temp" / f"topology_profile_store_{uuid4().hex}"
        root.mkdir(parents=True, exist_ok=False)
        try:
            explorer = validate_topology_profile_state(
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
            ok, msg = save_topology_profile(explorer, root_dir=root)
            self.assertTrue(ok, msg)

            loaded_explorer = load_topology_profile(GAMEPLAY_MODE_EXPLORER, 4, root_dir=root)
            loaded_normal = load_topology_profile(GAMEPLAY_MODE_NORMAL, 4, root_dir=root)
            self.assertEqual(loaded_explorer.edge_rules[1], (EDGE_WRAP, EDGE_WRAP))
            self.assertEqual(loaded_normal.edge_rules[1], (EDGE_BOUNDED, EDGE_BOUNDED))
        finally:
            import shutil
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
