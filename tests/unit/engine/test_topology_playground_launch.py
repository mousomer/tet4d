from __future__ import annotations

import inspect
import unittest
from unittest import mock

from tet4d.engine.gameplay.api import (
    piece_set_2d_options_gameplay,
    piece_set_options_for_dimension_gameplay,
)
from tet4d.engine.gameplay.game2d import GameConfig
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.engine.gameplay.topology_designer import GAMEPLAY_MODE_NORMAL
from tet4d.engine.runtime import topology_playground_launch
from tet4d.engine.runtime.topology_playground_launch import (
    build_gameplay_config_from_topology_playground_state,
)
from tet4d.engine.runtime.topology_playground_state import (
    default_topology_playground_state,
)
from tet4d.ui.pygame.topology_lab.play_launch import (
    launch_playground_state_gameplay,
)


class TestTopologyPlaygroundLaunchConfig(unittest.TestCase):
    def test_module_stays_ui_free(self) -> None:
        source = inspect.getsource(topology_playground_launch)
        self.assertNotIn("pygame", source)
        self.assertNotIn("tet4d.ui", source)

    def test_build_2d_config_uses_canonical_axis_sizes_and_launch_settings(self) -> None:
        state = default_topology_playground_state(
            dimension=2,
            axis_sizes=(12, 18),
        )
        piece_options = piece_set_2d_options_gameplay()
        piece_index = min(2, len(piece_options) - 1)
        state.launch_settings.piece_set_index = piece_index
        state.launch_settings.speed_level = 5
        state.launch_settings.random_mode_index = 1
        state.launch_settings.game_seed = 99

        cfg = build_gameplay_config_from_topology_playground_state(state)

        self.assertIsInstance(cfg, GameConfig)
        self.assertEqual((cfg.width, cfg.height), (12, 18))
        self.assertEqual(cfg.piece_set, piece_options[piece_index])
        self.assertEqual(cfg.speed_level, 5)
        self.assertTrue(cfg.exploration_mode)
        self.assertIs(cfg.explorer_topology_profile, state.explorer_profile)
        self.assertEqual(cfg.topology_mode, state.transport_policy.base_policy.mode)
        self.assertEqual(
            cfg.topology_edge_rules,
            state.transport_policy.base_policy.edge_rules,
        )
        self.assertEqual(cfg.rng_seed, 99)

    def test_build_4d_config_uses_canonical_axis_sizes_and_explorer_profile(self) -> None:
        state = default_topology_playground_state(
            dimension=4,
            axis_sizes=(13, 19, 8, 6),
        )
        piece_options = piece_set_options_for_dimension_gameplay(4)
        piece_index = min(1, len(piece_options) - 1)
        state.launch_settings.piece_set_index = piece_index
        state.launch_settings.speed_level = 6
        state.launch_settings.random_mode_index = 2
        state.launch_settings.game_seed = 1234

        cfg = build_gameplay_config_from_topology_playground_state(state)

        self.assertIsInstance(cfg, GameConfigND)
        self.assertEqual(cfg.dims, (13, 19, 8, 6))
        self.assertEqual(cfg.piece_set_id, piece_options[piece_index])
        self.assertEqual(cfg.speed_level, 6)
        self.assertTrue(cfg.exploration_mode)
        self.assertIs(cfg.explorer_topology_profile, state.explorer_profile)
        self.assertEqual(cfg.topology_mode, state.transport_policy.base_policy.mode)
        self.assertEqual(
            cfg.topology_edge_rules,
            state.transport_policy.base_policy.edge_rules,
        )
        self.assertEqual(cfg.rng_seed, 1234)

    def test_builder_rejects_non_explorer_playground_state(self) -> None:
        state = default_topology_playground_state(
            dimension=3,
            axis_sizes=(6, 12, 6),
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
        )

        with self.assertRaisesRegex(ValueError, "Explorer gameplay mode"):
            build_gameplay_config_from_topology_playground_state(state)


class TestTopologyLabPlayLaunch(unittest.TestCase):
    def test_launch_gameplay_routes_2d_state_to_front2d(self) -> None:
        state = default_topology_playground_state(
            dimension=2,
            axis_sizes=(8, 16),
        )
        screen = object()
        fonts_nd = object()
        fonts_2d = object()
        display_settings = object()
        cfg = object()
        reopened_screen = object()

        with (
            mock.patch(
                "tet4d.ui.pygame.topology_lab.play_launch."
                "build_gameplay_config_from_topology_playground_state",
                return_value=cfg,
            ) as build_cfg,
            mock.patch("tet4d.ui.pygame.front2d_game.run_game_loop") as run_game,
            mock.patch(
                "tet4d.ui.pygame.runtime_ui.app_runtime."
                "capture_windowed_display_settings",
                return_value="captured",
            ) as capture_display,
            mock.patch(
                "tet4d.ui.pygame.runtime_ui.app_runtime.open_display",
                return_value=reopened_screen,
            ) as open_display,
        ):
            returned_screen, returned_display = launch_playground_state_gameplay(
                state,
                screen,
                fonts_nd,
                return_caption="Explorer Playground",
                fonts_2d=fonts_2d,
                display_settings=display_settings,
            )

        build_cfg.assert_called_once_with(state)
        run_game.assert_called_once_with(screen, cfg, fonts_2d, display_settings)
        capture_display.assert_called_once_with(display_settings)
        open_display.assert_called_once_with("captured", caption="Explorer Playground")
        self.assertIs(returned_screen, reopened_screen)
        self.assertEqual(returned_display, "captured")

    def test_launch_gameplay_routes_4d_state_to_front4d(self) -> None:
        state = default_topology_playground_state(
            dimension=4,
            axis_sizes=(8, 16, 6, 4),
        )
        screen = object()
        fonts_nd = object()
        cfg = object()

        with (
            mock.patch(
                "tet4d.ui.pygame.topology_lab.play_launch."
                "build_gameplay_config_from_topology_playground_state",
                return_value=cfg,
            ) as build_cfg,
            mock.patch("tet4d.ui.pygame.front2d_game.run_game_loop") as run_2d,
            mock.patch("tet4d.ui.pygame.front3d_game.run_game_loop") as run_3d,
            mock.patch("tet4d.ui.pygame.front4d_game.run_game_loop") as run_4d,
        ):
            returned_screen, returned_display = launch_playground_state_gameplay(
                state,
                screen,
                fonts_nd,
                return_caption="Explorer Playground",
                display_settings=None,
            )

        build_cfg.assert_called_once_with(state)
        run_2d.assert_not_called()
        run_3d.assert_not_called()
        run_4d.assert_called_once_with(screen, cfg, fonts_nd)
        self.assertIs(returned_screen, screen)
        self.assertIsNone(returned_display)


if __name__ == "__main__":
    unittest.main()
