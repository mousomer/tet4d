from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from tet4d.engine.runtime import topology_explorer_runtime


class TestTopologyExplorerRuntime(unittest.TestCase):
    def test_resolve_direct_explorer_launch_profile_prefers_override(self) -> None:
        override = SimpleNamespace(dimension=3, gluings=())
        with mock.patch.object(
            topology_explorer_runtime,
            "load_runtime_explorer_topology_profile",
        ) as load_profile:
            resolved_mode, edge_rules, profile = (
                topology_explorer_runtime.resolve_direct_explorer_launch_profile(
                    dimension=3,
                    gravity_axis=1,
                    topology_mode="wrap_all",
                    explorer_topology_profile_override=override,
                )
            )

        self.assertEqual(resolved_mode, "wrap_all")
        self.assertEqual(
            edge_rules,
            (("wrap", "wrap"), ("bounded", "bounded"), ("wrap", "wrap")),
        )
        self.assertIs(profile, override)
        load_profile.assert_not_called()

    def test_resolve_direct_explorer_launch_profile_uses_runtime_store(self) -> None:
        stored = SimpleNamespace(dimension=4, gluings=())
        with mock.patch.object(
            topology_explorer_runtime,
            "load_runtime_explorer_topology_profile",
            return_value=stored,
        ) as load_profile:
            resolved_mode, edge_rules, profile = (
                topology_explorer_runtime.resolve_direct_explorer_launch_profile(
                    dimension=4,
                    gravity_axis=1,
                    topology_mode="bounded",
                )
            )

        self.assertEqual(resolved_mode, "bounded")
        self.assertEqual(edge_rules, (("bounded", "bounded"),) * 4)
        self.assertIs(profile, stored)
        load_profile.assert_called_once_with(4)

    def test_export_stored_explorer_topology_preview_uses_runtime_loader(self) -> None:
        explorer_profile = SimpleNamespace(dimension=4, gluings=())
        with (
            mock.patch.object(
                topology_explorer_runtime,
                "load_runtime_explorer_topology_profile",
                return_value=explorer_profile,
            ) as load_profile,
            mock.patch.object(
                topology_explorer_runtime,
                "preview_dims_for_dimension",
                return_value=(8, 9, 7, 6),
            ) as preview_dims,
            mock.patch.object(
                topology_explorer_runtime,
                "export_explorer_topology_preview",
                return_value=(True, "ok", "preview.json"),
            ) as export_preview,
        ):
            result = topology_explorer_runtime.export_stored_explorer_topology_preview(
                4,
                source="stored_profile",
            )

        self.assertEqual(result, (True, "ok", "preview.json"))
        load_profile.assert_called_once_with(4)
        preview_dims.assert_called_once_with(4)
        export_preview.assert_called_once_with(
            explorer_profile,
            dims=(8, 9, 7, 6),
            source="stored_profile",
        )


if __name__ == "__main__":
    unittest.main()
