from __future__ import annotations

import json
import shutil
import unittest
from uuid import uuid4

from tet4d.engine.gameplay.topology import EDGE_BOUNDED, EDGE_WRAP
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    validate_topology_profile_state,
)
from tet4d.engine.runtime.project_config import (
    state_dir_path,
    topology_profiles_file_default_path,
)
from tet4d.engine.runtime.topology_explorer_bridge import (
    explorer_profile_from_legacy_profile,
)
from tet4d.engine.runtime.topology_profile_store import (
    load_topology_profile,
    load_topology_profiles_payload,
    save_topology_profile,
)
from tet4d.engine.topology_explorer.canonical_contract import (
    canonical_topology_payload,
    topology_contract_identity,
)


class TestTopologyProfileStore(unittest.TestCase):
    def test_normal_and_explorer_profiles_are_saved_separately(self) -> None:
        root = (
            state_dir_path() / "pytest_temp" / f"topology_profile_store_{uuid4().hex}"
        )
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

            loaded_explorer = load_topology_profile(
                GAMEPLAY_MODE_EXPLORER, 4, root_dir=root
            )
            loaded_normal = load_topology_profile(
                GAMEPLAY_MODE_NORMAL, 4, root_dir=root
            )
            self.assertEqual(loaded_explorer.edge_rules[1], (EDGE_WRAP, EDGE_WRAP))
            self.assertEqual(loaded_normal.edge_rules[1], (EDGE_BOUNDED, EDGE_BOUNDED))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_normal_2d_profile_round_trips(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_profile_store_2d_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            normal = validate_topology_profile_state(
                gameplay_mode=GAMEPLAY_MODE_NORMAL,
                dimension=2,
                gravity_axis=1,
                topology_mode="bounded",
                edge_rules=(
                    (EDGE_WRAP, EDGE_WRAP),
                    (EDGE_BOUNDED, EDGE_BOUNDED),
                ),
            )
            ok, msg = save_topology_profile(normal, root_dir=root)
            self.assertTrue(ok, msg)
            loaded = load_topology_profile(GAMEPLAY_MODE_NORMAL, 2, root_dir=root)
            self.assertEqual(loaded.edge_rules[0], (EDGE_WRAP, EDGE_WRAP))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_valid_v1_document_round_trips_without_schema_drift(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_profile_store_v1_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            explorer = validate_topology_profile_state(
                gameplay_mode=GAMEPLAY_MODE_EXPLORER,
                dimension=2,
                gravity_axis=1,
                topology_mode="bounded",
                edge_rules=(
                    (EDGE_WRAP, EDGE_WRAP),
                    (EDGE_BOUNDED, EDGE_BOUNDED),
                ),
            )
            before = topology_contract_identity(
                canonical_topology_payload(
                    explorer_profile_from_legacy_profile(explorer),
                    (6, 10),
                )
            )

            ok, message = save_topology_profile(explorer, root_dir=root)
            self.assertTrue(ok, message)
            payload = load_topology_profiles_payload(root_dir=root)
            loaded = load_topology_profile(
                GAMEPLAY_MODE_EXPLORER,
                2,
                root_dir=root,
            )
            after = topology_contract_identity(
                canonical_topology_payload(
                    explorer_profile_from_legacy_profile(loaded),
                    (6, 10),
                )
            )

            self.assertEqual(set(payload), {"version", "topology_profiles"})
            self.assertEqual(payload["version"], 1)
            self.assertEqual(before, after)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_malformed_v1_document_falls_back_as_one_whole_document(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_profile_store_malformed_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            explorer = validate_topology_profile_state(
                gameplay_mode=GAMEPLAY_MODE_EXPLORER,
                dimension=2,
                gravity_axis=1,
                topology_mode="bounded",
                edge_rules=(
                    (EDGE_WRAP, EDGE_WRAP),
                    (EDGE_BOUNDED, EDGE_BOUNDED),
                ),
            )
            ok, message = save_topology_profile(explorer, root_dir=root)
            self.assertTrue(ok, message)
            path = topology_profiles_file_default_path(root_dir=root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["topology_profiles"][GAMEPLAY_MODE_NORMAL]["3d"]["edge_rules"][0][
                0
            ] = True
            path.write_text(json.dumps(payload), encoding="utf-8")

            loaded_explorer = load_topology_profile(
                GAMEPLAY_MODE_EXPLORER,
                2,
                root_dir=root,
            )
            loaded_normal = load_topology_profile(
                GAMEPLAY_MODE_NORMAL,
                3,
                root_dir=root,
            )

            self.assertEqual(
                loaded_explorer.edge_rules[0],
                (EDGE_BOUNDED, EDGE_BOUNDED),
            )
            self.assertEqual(
                loaded_normal.edge_rules[0],
                (EDGE_BOUNDED, EDGE_BOUNDED),
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_v1_document_rejects_version_and_shape_near_misses(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_profile_store_near_miss_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            path = topology_profiles_file_default_path(root_dir=root)
            path.parent.mkdir(parents=True, exist_ok=True)
            baseline = load_topology_profiles_payload(root_dir=root)
            cases = []
            for version in (True, 1.0, "1"):
                case = json.loads(json.dumps(baseline))
                case["version"] = version
                cases.append(case)
            partial = json.loads(json.dumps(baseline))
            del partial["topology_profiles"][GAMEPLAY_MODE_EXPLORER]["4d"]
            cases.append(partial)
            extra = json.loads(json.dumps(baseline))
            extra["unexpected"] = True
            cases.append(extra)

            for case in cases:
                path.write_text(json.dumps(case), encoding="utf-8")
                self.assertEqual(
                    load_topology_profiles_payload(root_dir=root),
                    baseline,
                )
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
