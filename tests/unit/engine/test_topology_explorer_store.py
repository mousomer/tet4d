from __future__ import annotations

import shutil
import unittest
from uuid import uuid4

from tet4d.engine.runtime.project_config import (
    explorer_topology_profiles_file_default_path,
    state_dir_path,
)
from tet4d.engine.runtime.settings_schema import write_json_object
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
    def test_malformed_persistence_scalars_fall_back_without_domain_coercion(
        self,
    ) -> None:
        valid_gluing = {
            "id": "wrap_x",
            "enabled": True,
            "source": {"axis": "x", "side": "-"},
            "target": {"axis": "x", "side": "+"},
            "transform": {"permutation": [0], "signs": [1]},
        }
        mutations = (
            ("string boolean", ("enabled",), "false"),
            ("numeric boolean", ("enabled",), 1),
            ("numeric axis string", ("source", "axis"), "0"),
            ("fractional permutation", ("transform", "permutation"), [0.9]),
            ("fractional sign", ("transform", "signs"), [1.8]),
            ("non-string side", ("source", "side"), -1),
            ("non-string id", ("id",), 7),
        )
        for label, path, malformed_value in mutations:
            with self.subTest(case=label):
                root = (
                    state_dir_path()
                    / "pytest_temp"
                    / f"topology_explorer_store_malformed_{uuid4().hex}"
                )
                root.mkdir(parents=True, exist_ok=False)
                try:
                    gluing = {
                        **valid_gluing,
                        "source": dict(valid_gluing["source"]),
                        "target": dict(valid_gluing["target"]),
                        "transform": dict(valid_gluing["transform"]),
                    }
                    owner = gluing
                    for key in path[:-1]:
                        owner = owner[key]
                    owner[path[-1]] = malformed_value
                    write_json_object(
                        explorer_topology_profiles_file_default_path(root_dir=root),
                        {
                            "version": 1,
                            "explorer_topology_profiles": {
                                "2d": {"dimension": 2, "gluings": [gluing]},
                            },
                        },
                    )

                    loaded = load_explorer_topology_profile(2, root_dir=root)
                    self.assertEqual(loaded, ExplorerTopologyProfile(2, ()))
                finally:
                    shutil.rmtree(root, ignore_errors=True)

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
            also_empty_2d = load_explorer_topology_profile(2, root_dir=root)
            self.assertEqual(loaded, profile)
            self.assertEqual(untouched.gluings, ())
            self.assertEqual(also_empty_2d.gluings, ())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_round_trip_persists_profile_per_dimension_including_2d(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_store_2d_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = ExplorerTopologyProfile(
                dimension=2,
                gluings=(
                    GluingDescriptor(
                        glue_id="wrap_x",
                        source=BoundaryRef(2, 0, "-"),
                        target=BoundaryRef(2, 0, "+"),
                        transform=BoundaryTransform(permutation=(0,), signs=(1,)),
                    ),
                ),
            )
            ok, message = save_explorer_topology_profile(profile, root_dir=root)
            self.assertTrue(ok, message)

            loaded = load_explorer_topology_profile(2, root_dir=root)
            untouched = load_explorer_topology_profile(3, root_dir=root)
            self.assertEqual(loaded, profile)
            self.assertEqual(untouched.gluings, ())
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
