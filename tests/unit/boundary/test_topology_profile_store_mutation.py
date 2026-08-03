from __future__ import annotations

import json
import shutil
import unittest
from unittest import mock
from uuid import uuid4

from tet4d.engine.gameplay.topology import EDGE_BOUNDED, EDGE_WRAP
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    validate_topology_profile_state,
)
from tet4d.engine.runtime import topology_profile_store as profile_store_module
from tet4d.engine.runtime.project_config import (
    state_dir_path,
    topology_profiles_file_default_path,
)
from tet4d.engine.runtime.topology_profile_store import (
    TopologyProfileStoreStatus,
    load_topology_profile,
    load_topology_profile_store,
    load_topology_profiles_payload,
    save_topology_profile,
)


class TestTopologyProfileStoreMutationBoundary(unittest.TestCase):
    @staticmethod
    def _explorer_2d_wrap_profile():
        return validate_topology_profile_state(
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=2,
            gravity_axis=1,
            topology_mode="bounded",
            edge_rules=(
                (EDGE_WRAP, EDGE_WRAP),
                (EDGE_BOUNDED, EDGE_BOUNDED),
            ),
        )

    def test_missing_store_state_and_first_save_are_explicit(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_profile_store_missing_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            missing = load_topology_profile_store(root_dir=root)
            self.assertIs(missing.status, TopologyProfileStoreStatus.MISSING)
            self.assertIsNotNone(missing.payload)
            self.assertEqual(missing.diagnostics, ())

            ok, message = save_topology_profile(
                self._explorer_2d_wrap_profile(), root_dir=root
            )
            self.assertTrue(ok, message)
            loaded = load_topology_profile_store(root_dir=root)
            self.assertIs(loaded.status, TopologyProfileStoreStatus.VALID)
            self.assertEqual(loaded.payload["version"], 1)
            self.assertIsNotNone(loaded.source_digest)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_malformed_json_blocks_save_and_preserves_exact_bytes(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_profile_store_invalid_json_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            path = topology_profiles_file_default_path(root_dir=root)
            path.parent.mkdir(parents=True, exist_ok=True)
            original = b'{"version": 1, not-json\n'
            path.write_bytes(original)

            result = load_topology_profile_store(root_dir=root)
            self.assertIs(result.status, TopologyProfileStoreStatus.INVALID)
            self.assertIsNone(result.payload)
            self.assertTrue(result.diagnostics)
            ok, message = save_topology_profile(
                self._explorer_2d_wrap_profile(), root_dir=root
            )

            self.assertFalse(ok)
            self.assertIn("Refusing to overwrite invalid", message)
            self.assertEqual(path.read_bytes(), original)
            self.assertFalse(path.with_suffix(path.suffix + ".tmp").exists())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_structurally_invalid_documents_block_save_without_replacement(
        self,
    ) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_profile_store_invalid_shape_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            path = topology_profiles_file_default_path(root_dir=root)
            path.parent.mkdir(parents=True, exist_ok=True)
            baseline = load_topology_profiles_payload(root_dir=root)
            cases = []

            wrong_version = json.loads(json.dumps(baseline))
            wrong_version["version"] = 2
            cases.append(wrong_version)

            boolean_version = json.loads(json.dumps(baseline))
            boolean_version["version"] = True
            cases.append(boolean_version)

            wrong_profiles_type = json.loads(json.dumps(baseline))
            wrong_profiles_type["topology_profiles"] = []
            cases.append(wrong_profiles_type)

            unknown_slot_field = json.loads(json.dumps(baseline))
            unknown_slot_field["topology_profiles"][GAMEPLAY_MODE_EXPLORER]["2d"][
                "unknown"
            ] = True
            cases.append(unknown_slot_field)

            malformed_slot = json.loads(json.dumps(baseline))
            malformed_slot["topology_profiles"][GAMEPLAY_MODE_NORMAL]["3d"][
                "edge_rules"
            ][0] = True
            cases.append(malformed_slot)

            for document in cases:
                original = json.dumps(document, separators=(",", ":")).encode()
                path.write_bytes(original)
                result = load_topology_profile_store(root_dir=root)
                self.assertIs(result.status, TopologyProfileStoreStatus.INVALID)
                ok, _ = save_topology_profile(
                    self._explorer_2d_wrap_profile(), root_dir=root
                )
                self.assertFalse(ok)
                self.assertEqual(path.read_bytes(), original)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_invalid_read_only_fallback_cannot_authorize_replacement(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_profile_store_safe_view_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            path = topology_profiles_file_default_path(root_dir=root)
            path.parent.mkdir(parents=True, exist_ok=True)
            original = b"[]\n"
            path.write_bytes(original)

            fallback_profile = load_topology_profile(
                GAMEPLAY_MODE_EXPLORER,
                2,
                root_dir=root,
            )
            result = load_topology_profile_store(root_dir=root)
            ok, _ = save_topology_profile(fallback_profile, root_dir=root)

            self.assertEqual(
                fallback_profile.edge_rules[0],
                (EDGE_BOUNDED, EDGE_BOUNDED),
            )
            self.assertIs(result.status, TopologyProfileStoreStatus.INVALID)
            self.assertFalse(ok)
            self.assertEqual(path.read_bytes(), original)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_save_reloads_external_valid_change_and_preserves_it(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_profile_store_external_reload_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            path = topology_profiles_file_default_path(root_dir=root)
            self.assertTrue(
                save_topology_profile(
                    validate_topology_profile_state(
                        gameplay_mode=GAMEPLAY_MODE_NORMAL,
                        dimension=2,
                        gravity_axis=1,
                        topology_mode="bounded",
                        edge_rules=(
                            (EDGE_BOUNDED, EDGE_BOUNDED),
                            (EDGE_BOUNDED, EDGE_BOUNDED),
                        ),
                    ),
                    root_dir=root,
                )[0]
            )
            stale_result = load_topology_profile_store(root_dir=root)
            external = stale_result.payload
            assert external is not None
            external["topology_profiles"][GAMEPLAY_MODE_EXPLORER]["2d"] = {
                "topology_mode": "bounded",
                "preset_id": None,
                "edge_rules": [
                    [EDGE_WRAP, EDGE_WRAP],
                    [EDGE_BOUNDED, EDGE_BOUNDED],
                ],
            }
            path.write_text(json.dumps(external), encoding="utf-8")

            ok, message = save_topology_profile(
                validate_topology_profile_state(
                    gameplay_mode=GAMEPLAY_MODE_NORMAL,
                    dimension=2,
                    gravity_axis=1,
                    topology_mode="bounded",
                    edge_rules=(
                        (EDGE_WRAP, EDGE_WRAP),
                        (EDGE_BOUNDED, EDGE_BOUNDED),
                    ),
                ),
                root_dir=root,
            )
            self.assertTrue(ok, message)
            self.assertEqual(
                load_topology_profile(
                    GAMEPLAY_MODE_EXPLORER, 2, root_dir=root
                ).edge_rules[0],
                (EDGE_WRAP, EDGE_WRAP),
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_save_refuses_internal_load_write_race(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_profile_store_race_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = self._explorer_2d_wrap_profile()
            self.assertTrue(save_topology_profile(profile, root_dir=root)[0])
            path = topology_profiles_file_default_path(root_dir=root)
            external_bytes = b'{"external":"replacement"}\n'
            real_source_matches = profile_store_module._store_source_matches

            def replace_before_compare(candidate_path, load_result):
                candidate_path.write_bytes(external_bytes)
                return real_source_matches(candidate_path, load_result)

            with mock.patch(
                "tet4d.engine.runtime.topology_profile_store._store_source_matches",
                side_effect=replace_before_compare,
            ):
                ok, message = save_topology_profile(profile, root_dir=root)

            self.assertFalse(ok)
            self.assertIn("changed while saving", message)
            self.assertEqual(path.read_bytes(), external_bytes)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
