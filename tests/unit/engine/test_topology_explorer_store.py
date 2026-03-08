from __future__ import annotations

import shutil
import unittest
from uuid import uuid4

from tet4d.engine.runtime.project_config import state_dir_path
from tet4d.engine.runtime.topology_explorer_store import (
    load_explorer_topology_profile,
    save_explorer_topology_profile,
)
from tet4d.engine.topology_explorer import (
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
)


class TestTopologyExplorerStore(unittest.TestCase):
    def test_round_trip_persists_profile_per_dimension(self) -> None:
        root = (
            state_dir_path() / "pytest_temp" / f"topology_explorer_store_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = ExplorerTopologyProfile(
                dimension=3,
                gluings=(
                    GluingDescriptor(
                        glue_id="wrap_x",
                        source=BoundaryRef(3, 0, "-"),
                        target=BoundaryRef(3, 0, "+"),
                        transform=BoundaryTransform(permutation=(0, 1), signs=(1, 1)),
                    ),
                ),
            )
            ok, message = save_explorer_topology_profile(profile, root_dir=root)
            self.assertTrue(ok, message)

            loaded = load_explorer_topology_profile(3, root_dir=root)
            untouched = load_explorer_topology_profile(4, root_dir=root)
            self.assertEqual(loaded, profile)
            self.assertEqual(untouched.gluings, ())
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
