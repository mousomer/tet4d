from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.ui.pygame.topology_lab.app import (
    build_explorer_playground_config,
    build_explorer_playground_launch,
)
from tet4d.ui.pygame.topology_lab.scene_state import TOOL_CREATE, TOOL_PROBE


class TestTopologyLabApp(unittest.TestCase):
    def test_build_explorer_launch_defaults_to_probe_for_explorer_entry(self) -> None:
        profile = ExplorerTopologyProfile(dimension=3, gluings=())
        launch = build_explorer_playground_launch(
            dimension=3,
            explorer_profile=profile,
        )
        self.assertEqual(launch.dimension, 3)
        self.assertEqual(launch.gameplay_mode, GAMEPLAY_MODE_EXPLORER)
        self.assertEqual(launch.initial_tool, TOOL_PROBE)
        self.assertEqual(launch.entry_source, "explorer")
        self.assertIs(launch.explorer_profile, profile)

    def test_build_lab_launch_defaults_to_create_for_lab_entry(self) -> None:
        launch = build_explorer_playground_launch(
            dimension=4,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
            entry_source="lab",
        )
        self.assertEqual(launch.dimension, 4)
        self.assertEqual(launch.gameplay_mode, GAMEPLAY_MODE_NORMAL)
        self.assertEqual(launch.initial_tool, TOOL_CREATE)
        self.assertEqual(launch.entry_source, "lab")

    def test_build_explorer_playground_config_uses_2d_builder(self) -> None:
        profile = ExplorerTopologyProfile(dimension=2, gluings=())
        sentinel = SimpleNamespace(width=8, height=8)
        with mock.patch(
            "tet4d.ui.pygame.front2d_setup.config_from_settings",
            return_value=sentinel,
        ) as build_cfg:
            cfg = build_explorer_playground_config(
                dimension=2,
                explorer_profile=profile,
            )
        self.assertIs(cfg, sentinel)
        self.assertIs(build_cfg.call_args.kwargs["explorer_topology_profile_override"], profile)

    def test_build_explorer_playground_config_uses_nd_builder(self) -> None:
        profile = ExplorerTopologyProfile(dimension=4, gluings=())
        sentinel = SimpleNamespace(dims=(8, 9, 7, 6))
        with mock.patch(
            "tet4d.ui.pygame.frontend_nd_setup.build_config",
            return_value=sentinel,
        ) as build_cfg:
            cfg = build_explorer_playground_config(
                dimension=4,
                explorer_profile=profile,
            )
        self.assertIs(cfg, sentinel)
        self.assertEqual(build_cfg.call_args.args[1], 4)
        self.assertIs(build_cfg.call_args.kwargs["explorer_topology_profile_override"], profile)


if __name__ == "__main__":
    unittest.main()