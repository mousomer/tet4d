from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

import tet4d.engine.api as engine_api
from tet4d.engine import frontend_nd
from tet4d.engine.gameplay.pieces_nd import (
    PIECE_SET_4D_SIX,
    get_piece_shapes_nd,
    piece_set_options_for_dimension,
)
from tet4d.ui.pygame.launch import launcher_play
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings


class TestFront3DSetupDedup(unittest.TestCase):
    def test_launcher_play_run_menu_3d_delegates_dimension_3(self) -> None:
        sentinel = object()
        with mock.patch.object(
            engine_api,
            "front3d_setup_run_menu_nd",
            return_value=sentinel,
        ) as patched:
            result = engine_api.launcher_play_run_menu_3d("screen", "fonts")
        self.assertIs(result, sentinel)
        patched.assert_called_once_with("screen", "fonts", 3)

    def test_launcher_play_build_config_3d_delegates_dimension_3(self) -> None:
        sentinel = object()
        settings = frontend_nd.GameSettingsND()
        with mock.patch.object(
            engine_api,
            "front3d_setup_build_config_nd",
            return_value=sentinel,
        ) as patched:
            result = engine_api.launcher_play_build_config_3d(settings)
        self.assertIs(result, sentinel)
        patched.assert_called_once_with(settings, 3)

    def test_launcher_play_2d_passes_display_settings_to_game_loop(self) -> None:
        setup_screen = object()
        game_screen = object()
        return_screen = object()
        fonts_2d = object()
        cfg = SimpleNamespace(width=10, height=20)
        settings = SimpleNamespace(
            bot_mode_index=0,
            bot_speed_level=7,
            bot_algorithm_index=0,
            bot_profile_index=1,
            bot_budget_ms=12,
        )
        display_settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))

        with mock.patch.object(
            launcher_play,
            "open_display",
            side_effect=[setup_screen, game_screen, return_screen],
        ), mock.patch.object(
            launcher_play.front2d, "run_menu", return_value=settings
        ), mock.patch.object(
            launcher_play.front2d, "_config_from_settings", return_value=cfg
        ), mock.patch.object(
            launcher_play.front2d, "run_game_loop", return_value=True
        ) as run_game_loop_mock, mock.patch.object(
            launcher_play,
            "capture_windowed_display_settings",
            return_value=display_settings,
        ):
            result = launcher_play.launch_2d(
                screen=setup_screen,
                fonts_2d=fonts_2d,
                display_settings=display_settings,
            )

        self.assertTrue(result.keep_running)
        self.assertEqual(
            run_game_loop_mock.call_args.args,
            (game_screen, cfg, fonts_2d, display_settings),
        )

    def test_build_config_matches_shared_nd_builder(self) -> None:
        settings = frontend_nd.GameSettingsND(
            width=6,
            height=14,
            depth=5,
            fourth=9,
            speed_level=3,
            piece_set_index=0,
            random_mode_index=0,
            game_seed=4242,
            topology_mode=0,
            topology_advanced=0,
            topology_profile_index=0,
            bot_mode_index=0,
            bot_algorithm_index=0,
            bot_profile_index=1,
            bot_speed_level=7,
            bot_budget_ms=24,
            challenge_layers=2,
            exploration_mode=0,
        )

        cfg_adapter = frontend_nd.build_config(settings, 3)
        cfg_shared = frontend_nd.build_config(settings, 3)

        self.assertEqual(cfg_adapter.dims, cfg_shared.dims)
        self.assertEqual(cfg_adapter.gravity_axis, cfg_shared.gravity_axis)
        self.assertEqual(cfg_adapter.speed_level, cfg_shared.speed_level)
        self.assertEqual(cfg_adapter.piece_set_id, cfg_shared.piece_set_id)
        self.assertEqual(cfg_adapter.rng_mode, cfg_shared.rng_mode)
        self.assertEqual(cfg_adapter.rng_seed, cfg_shared.rng_seed)
        self.assertEqual(cfg_adapter.topology_mode, cfg_shared.topology_mode)
        self.assertEqual(
            cfg_adapter.topology_edge_rules, cfg_shared.topology_edge_rules
        )

    def test_gravity_interval_matches_shared_nd_builder(self) -> None:
        settings = frontend_nd.GameSettingsND(speed_level=4)
        cfg = frontend_nd.build_config(settings, 3)
        self.assertEqual(
            frontend_nd.gravity_interval_ms_from_config(cfg),
            frontend_nd.gravity_interval_ms_from_config(cfg),
        )

    def test_4d_setup_can_select_six_cell_piece_set(self) -> None:
        options_4d = piece_set_options_for_dimension(4)
        six_cell_index = options_4d.index(PIECE_SET_4D_SIX)
        settings = frontend_nd.GameSettingsND(piece_set_index=six_cell_index)
        cfg = frontend_nd.build_config(settings, 4)
        self.assertEqual(cfg.piece_set_id, PIECE_SET_4D_SIX)
        shapes = get_piece_shapes_nd(4, piece_set_id=cfg.piece_set_id)
        self.assertTrue(shapes)
        self.assertTrue(all(len(shape.blocks) == 6 for shape in shapes))


if __name__ == "__main__":
    unittest.main()
