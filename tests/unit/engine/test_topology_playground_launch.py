from __future__ import annotations

import inspect
import unittest
from unittest import mock

from tet4d.engine.gameplay.api import (
    piece_set_2d_options_gameplay,
    piece_set_options_for_dimension_gameplay,
)
from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game2d import GameConfig
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.topology_designer import GAMEPLAY_MODE_NORMAL
from tet4d.engine.runtime import topology_playground_launch
from tet4d.engine.runtime.topology_explorer_preview import advance_explorer_probe
from tet4d.engine.runtime.topology_playground_launch import (
    build_gameplay_config_from_topology_playground_state,
)
from tet4d.engine.runtime.topology_playground_state import (
    RIGID_PLAY_MODE_OFF,
    RIGID_PLAY_MODE_ON,
    default_topology_playground_state,
)
from tet4d.engine.topology_explorer import MoveStep
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    projective_plane_profile_2d,
    projective_space_profile_3d,
    swap_xw_profile_4d,
)
from tet4d.ui.pygame import frontend_nd_input
from tet4d.ui.pygame.keybindings import EXPLORER_KEYS_3D, KEYS_3D
from tet4d.ui.pygame.topology_lab.play_launch import (
    launch_playground_state_gameplay,
)


class TestTopologyPlaygroundLaunchConfig(unittest.TestCase):
    def test_module_stays_ui_free(self) -> None:
        source = inspect.getsource(topology_playground_launch)
        self.assertNotIn("pygame", source)
        self.assertNotIn("tet4d.ui", source)

    def test_build_2d_config_uses_canonical_axis_sizes_and_launch_settings(
        self,
    ) -> None:
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
        self.assertFalse(cfg.exploration_mode)
        self.assertIs(cfg.explorer_topology_profile, state.explorer_profile)
        self.assertIsNotNone(cfg.explorer_transport)
        self.assertEqual(cfg.explorer_transport.dims, (12, 18))
        self.assertEqual(cfg.topology_mode, state.transport_policy.base_policy.mode)
        self.assertEqual(
            cfg.topology_edge_rules,
            state.transport_policy.base_policy.edge_rules,
        )
        self.assertEqual(cfg.rng_seed, 99)

    def test_build_4d_config_uses_canonical_axis_sizes_and_explorer_profile(
        self,
    ) -> None:
        state = default_topology_playground_state(
            dimension=4,
            axis_sizes=(6, 6, 6, 6),
        )
        state.topology_config.explorer_profile = swap_xw_profile_4d()
        piece_options = piece_set_options_for_dimension_gameplay(4)
        piece_index = min(1, len(piece_options) - 1)
        state.launch_settings.piece_set_index = piece_index
        state.launch_settings.speed_level = 6
        state.launch_settings.random_mode_index = 2
        state.launch_settings.game_seed = 1234

        cfg = build_gameplay_config_from_topology_playground_state(state)

        self.assertIsInstance(cfg, GameConfigND)
        self.assertEqual(cfg.dims, (6, 6, 6, 6))
        self.assertEqual(cfg.piece_set_id, piece_options[piece_index])
        self.assertEqual(cfg.speed_level, 6)
        self.assertFalse(cfg.exploration_mode)
        self.assertIs(cfg.explorer_topology_profile, state.explorer_profile)
        self.assertIsNotNone(cfg.explorer_transport)
        self.assertEqual(cfg.explorer_transport.dims, (6, 6, 6, 6))
        self.assertEqual(cfg.topology_mode, state.transport_policy.base_policy.mode)
        self.assertEqual(
            cfg.topology_edge_rules,
            state.transport_policy.base_policy.edge_rules,
        )
        self.assertEqual(cfg.rng_seed, 1234)
        transport_result = cfg.explorer_transport.resolve_cell_step(
            (0, 1, 2, 1),
            MoveStep(axis=0, delta=-1),
        )
        self.assertEqual(transport_result.target, (3, 1, 1, 5))
        self.assertEqual(transport_result.traversal.glue_id, "swap_xw_4d")

    def test_launch_preserves_exact_explorer_transport_mapping(self) -> None:
        state = default_topology_playground_state(
            dimension=2,
            axis_sizes=(4, 4),
        )
        state.topology_config.explorer_profile = projective_plane_profile_2d()

        cfg = build_gameplay_config_from_topology_playground_state(state)
        probe_target, probe_result = advance_explorer_probe(
            state.explorer_profile,
            dims=state.axis_sizes,
            coord=(0, 0),
            step_label="x-",
        )
        transport_result = cfg.explorer_transport.resolve_cell_step(
            (0, 0),
            MoveStep(axis=0, delta=-1),
        )

        self.assertFalse(cfg.explorer_rigid_play_enabled)
        self.assertEqual(transport_result.target, probe_target)
        self.assertEqual(transport_result.target, (3, 3))
        self.assertEqual(
            transport_result.traversal.glue_id,
            probe_result["traversal"]["glue_id"],
        )
        self.assertEqual(
            transport_result.traversal.source_boundary.label,
            probe_result["traversal"]["source_boundary"],
        )
        self.assertEqual(
            transport_result.traversal.target_boundary.label,
            probe_result["traversal"]["target_boundary"],
        )

    def test_launch_rigid_play_setting_can_force_rigid_or_cellwise_transport(self) -> None:
        state = default_topology_playground_state(
            dimension=2,
            axis_sizes=(4, 4),
        )
        state.topology_config.explorer_profile = projective_plane_profile_2d()

        state.launch_settings.rigid_play_mode = RIGID_PLAY_MODE_ON
        rigid_cfg = build_gameplay_config_from_topology_playground_state(state)
        self.assertTrue(rigid_cfg.explorer_rigid_play_enabled)

        state.launch_settings.rigid_play_mode = RIGID_PLAY_MODE_OFF
        cellwise_cfg = build_gameplay_config_from_topology_playground_state(state)
        self.assertFalse(cellwise_cfg.explorer_rigid_play_enabled)

    def test_launch_config_uses_gameplay_bindings_instead_of_explorer_traversal(self) -> None:
        state = default_topology_playground_state(
            dimension=3,
            axis_sizes=(6, 12, 6),
        )
        state.topology_config.explorer_profile = axis_wrap_profile(
            dimension=3,
            wrapped_axes=(0,),
        )

        cfg = build_gameplay_config_from_topology_playground_state(state)

        self.assertEqual(
            frontend_nd_input.gameplay_action_for_key(KEYS_3D["move_x_pos"][0], cfg),
            "move_x_pos",
        )
        self.assertIsNone(
            frontend_nd_input.gameplay_action_for_key(
                EXPLORER_KEYS_3D["move_up"][0],
                cfg,
            )
        )

    def test_launch_config_spawns_playable_piece_above_gravity_axis(self) -> None:
        state = default_topology_playground_state(
            dimension=3,
            axis_sizes=(6, 12, 6),
        )
        state.topology_config.explorer_profile = axis_wrap_profile(
            dimension=3,
            wrapped_axes=(0,),
        )

        cfg = build_gameplay_config_from_topology_playground_state(state)
        gameplay_state = GameStateND(config=cfg, board=BoardND(cfg.dims))

        self.assertIsNotNone(gameplay_state.current_piece)
        self.assertFalse(gameplay_state.game_over)
        self.assertTrue(
            any(coord[cfg.gravity_axis] < 0 for coord in gameplay_state.current_piece.cells())
        )


    def test_launch_preserves_full_projective_directed_seam_family(self) -> None:
        cases = (
            (2, (4, 4), projective_plane_profile_2d(), {"x-", "x+", "y-", "y+"}),
            (
                3,
                (5, 4, 6),
                projective_space_profile_3d(),
                {"x-", "x+", "y-", "y+", "z-", "z+"},
            ),
        )

        for dimension, dims, profile, expected_sources in cases:
            with self.subTest(dimension=dimension, dims=dims):
                state = default_topology_playground_state(
                    dimension=dimension,
                    axis_sizes=dims,
                )
                state.topology_config.explorer_profile = profile

                cfg = build_gameplay_config_from_topology_playground_state(state)

                self.assertEqual(
                    len(cfg.explorer_transport.directed_seams),
                    2 * len(state.explorer_profile.active_gluings()),
                )
                self.assertEqual(
                    {
                        seam.source_boundary.label
                        for seam in cfg.explorer_transport.directed_seams
                    },
                    expected_sources,
                )

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
