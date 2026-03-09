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

    def test_build_explorer_launch_uses_source_settings_snapshot(self) -> None:
        settings = SimpleNamespace(
            width=11,
            height=17,
            depth=7,
            fourth=5,
            piece_set_index=3,
            speed_level=4,
            random_mode_index=1,
            game_seed=1234,
        )
        launch = build_explorer_playground_launch(
            dimension=4,
            source_settings=settings,
        )
        self.assertEqual(launch.settings_snapshot.board_dims, (11, 17, 7, 5))
        self.assertEqual(launch.settings_snapshot.piece_set_index, 3)
        self.assertEqual(launch.settings_snapshot.speed_level, 4)
        self.assertEqual(launch.settings_snapshot.random_mode_index, 1)
        self.assertEqual(launch.settings_snapshot.game_seed, 1234)

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
                settings_snapshot=build_explorer_playground_launch(
                    dimension=2,
                    source_settings=SimpleNamespace(
                        width=12, height=18, piece_set_index=2, speed_level=5, random_mode_index=1, game_seed=99
                    ),
                ).settings_snapshot,
            )
        self.assertIs(cfg, sentinel)
        settings_arg = build_cfg.call_args.args[0]
        self.assertEqual((settings_arg.width, settings_arg.height), (12, 18))
        self.assertEqual(settings_arg.piece_set_index, 2)
        self.assertEqual(settings_arg.speed_level, 5)
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
                settings_snapshot=build_explorer_playground_launch(
                    dimension=4,
                    source_settings=SimpleNamespace(
                        width=13, height=19, depth=8, fourth=6, piece_set_index=4, speed_level=6, random_mode_index=2, game_seed=77
                    ),
                ).settings_snapshot,
            )
        self.assertIs(cfg, sentinel)
        settings_arg = build_cfg.call_args.args[0]
        self.assertEqual((settings_arg.width, settings_arg.height, settings_arg.depth, settings_arg.fourth), (13, 19, 8, 6))
        self.assertEqual(settings_arg.piece_set_index, 4)
        self.assertEqual(settings_arg.speed_level, 6)
        self.assertEqual(build_cfg.call_args.args[1], 4)
        self.assertIs(build_cfg.call_args.kwargs["explorer_topology_profile_override"], profile)


if __name__ == "__main__":
    unittest.main()
