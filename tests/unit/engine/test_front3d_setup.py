from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from tet4d.engine.gameplay.api import runtime_collect_cleared_ghost_cells
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.engine.gameplay.pieces_nd import (
    PIECE_SET_4D_SIX,
    get_piece_shapes_nd,
    piece_set_options_for_dimension,
)
from tet4d.ui.pygame import front2d_setup, front3d_game, frontend_nd_setup
from tet4d.ui.pygame.launch import launcher_play
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings


class TestFront3DSetupDedup(unittest.TestCase):
    def test_launch_3d_uses_dimension_3_frontend_helpers(self) -> None:
        sentinel = object()
        display_settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        with mock.patch.object(
            launcher_play,
            "_launch_mode_flow",
            return_value=sentinel,
        ) as patched:
            result = launcher_play.launch_3d(
                screen=object(),
                fonts_nd=object(),
                display_settings=display_settings,
            )

        self.assertIs(result, sentinel)
        kwargs = patched.call_args.kwargs
        self.assertEqual(kwargs["default_budget_ms"], 24)
        self.assertEqual(kwargs["mode_key"], "3d")
        self.assertEqual(
            kwargs["setup_caption"], launcher_play.setup_caption_for_dimension(3)
        )
        self.assertEqual(
            kwargs["game_caption"], launcher_play.game_caption_for_dimension(3)
        )
        self.assertIs(kwargs["suggested_size_fn"], front3d_game.suggested_window_size)
        self.assertIs(kwargs["run_game_loop_fn"], front3d_game.run_game_loop)

        with mock.patch.object(
            frontend_nd_setup, "run_menu", return_value="menu"
        ) as run_menu:
            self.assertEqual(kwargs["run_menu_fn"]("screen", "fonts"), "menu")
        run_menu.assert_called_once_with("screen", "fonts", 3)

        with mock.patch.object(
            frontend_nd_setup, "build_play_menu_config", return_value="cfg"
        ) as build_config:
            self.assertEqual(kwargs["build_cfg_fn"]("settings"), "cfg")
        build_config.assert_called_once_with("settings", 3)

    def test_launch_4d_uses_dimension_4_frontend_helpers(self) -> None:
        sentinel = object()
        display_settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        with mock.patch.object(
            launcher_play,
            "_launch_mode_flow",
            return_value=sentinel,
        ) as patched:
            result = launcher_play.launch_4d(
                screen=object(),
                fonts_nd=object(),
                display_settings=display_settings,
            )

        self.assertIs(result, sentinel)
        kwargs = patched.call_args.kwargs
        self.assertEqual(kwargs["default_budget_ms"], 36)
        self.assertEqual(kwargs["mode_key"], "4d")

        with mock.patch.object(
            frontend_nd_setup, "run_menu", return_value="menu"
        ) as run_menu:
            self.assertEqual(kwargs["run_menu_fn"]("screen", "fonts"), "menu")
        run_menu.assert_called_once_with("screen", "fonts", 4)

        with mock.patch.object(
            frontend_nd_setup, "build_play_menu_config", return_value="cfg"
        ) as build_config:
            self.assertEqual(kwargs["build_cfg_fn"]("settings"), "cfg")
        build_config.assert_called_once_with("settings", 4)

    def test_launcher_play_2d_passes_display_settings_to_game_loop(self) -> None:
        from tet4d.ui.pygame import front2d_game

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

        with (
            mock.patch.object(
                launcher_play,
                "open_display",
                side_effect=[setup_screen, game_screen, return_screen],
            ),
            mock.patch.object(front2d_game, "run_menu", return_value=settings),
            mock.patch.object(front2d_game, "_config_from_settings", return_value=cfg),
            mock.patch.object(
                front2d_game, "run_game_loop", return_value=True
            ) as run_game_loop_mock,
            mock.patch.object(
                launcher_play,
                "capture_windowed_display_settings",
                return_value=display_settings,
            ),
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

    def test_tutorial_launch_2d_uses_game_settings_dataclass(self) -> None:
        from tet4d.ui.pygame import front2d_game

        display_settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        original_build = front2d_setup.build_play_menu_config
        captured: dict[str, front2d_setup.GameSettings] = {}

        def build_cfg(settings):
            self.assertIsInstance(settings, front2d_setup.GameSettings)
            captured["settings"] = settings
            return original_build(settings)

        with (
            mock.patch.object(
                launcher_play,
                "load_app_settings_payload",
                return_value={
                    "settings": {
                        "2d": {
                            "width": 9,
                            "height": 21,
                            "bot_budget_ms": 44,
                        }
                    }
                },
            ),
            mock.patch.object(
                launcher_play,
                "open_display",
                side_effect=[object(), object()],
            ),
            mock.patch.object(
                front2d_game,
                "_config_from_settings",
                side_effect=build_cfg,
            ),
            mock.patch.object(
                front2d_game,
                "run_game_loop",
                return_value=True,
            ) as run_game_loop_mock,
            mock.patch.object(
                launcher_play,
                "capture_windowed_display_settings",
                return_value=display_settings,
            ),
        ):
            result = launcher_play.launch_2d(
                screen=object(),
                fonts_2d=object(),
                display_settings=display_settings,
                tutorial_lesson_id="tutorial_2d_core",
            )

        self.assertTrue(result.keep_running)
        self.assertEqual(captured["settings"].width, 9)
        self.assertEqual(captured["settings"].height, 21)
        self.assertEqual(run_game_loop_mock.call_args.kwargs["bot_budget_ms"], 44)
        self.assertEqual(
            run_game_loop_mock.call_args.kwargs["tutorial_lesson_id"],
            "tutorial_2d_core",
        )

    def test_tutorial_launch_3d_uses_nd_settings_dataclass(self) -> None:
        display_settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        original_build = frontend_nd_setup.build_play_menu_config
        captured: dict[str, frontend_nd_setup.GameSettingsND] = {}

        def build_cfg(settings, dimension):
            self.assertIsInstance(settings, frontend_nd_setup.GameSettingsND)
            self.assertEqual(dimension, 3)
            captured["settings"] = settings
            return original_build(settings, dimension)

        with (
            mock.patch.object(
                launcher_play,
                "load_app_settings_payload",
                return_value={
                    "settings": {
                        "3d": {
                            "width": 7,
                            "height": 19,
                            "depth": 8,
                            "bot_budget_ms": 33,
                        }
                    }
                },
            ),
            mock.patch.object(
                launcher_play,
                "open_display",
                side_effect=[object(), object()],
            ),
            mock.patch.object(
                frontend_nd_setup,
                "build_play_menu_config",
                side_effect=build_cfg,
            ),
            mock.patch.object(
                front3d_game,
                "run_game_loop",
                return_value=True,
            ) as run_game_loop_mock,
            mock.patch.object(
                launcher_play,
                "capture_windowed_display_settings",
                return_value=display_settings,
            ),
        ):
            result = launcher_play.launch_3d(
                screen=object(),
                fonts_nd=object(),
                display_settings=display_settings,
                tutorial_lesson_id="tutorial_3d_core",
            )

        self.assertTrue(result.keep_running)
        self.assertEqual(captured["settings"].width, 7)
        self.assertEqual(captured["settings"].height, 19)
        self.assertEqual(captured["settings"].depth, 8)
        self.assertEqual(run_game_loop_mock.call_args.kwargs["bot_budget_ms"], 33)
        self.assertEqual(
            run_game_loop_mock.call_args.kwargs["tutorial_lesson_id"],
            "tutorial_3d_core",
        )

    def test_tutorial_launch_4d_uses_nd_settings_dataclass(self) -> None:
        from tet4d.ui.pygame import front4d_game

        display_settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        original_build = frontend_nd_setup.build_play_menu_config
        captured: dict[str, frontend_nd_setup.GameSettingsND] = {}

        def build_cfg(settings, dimension):
            self.assertIsInstance(settings, frontend_nd_setup.GameSettingsND)
            self.assertEqual(dimension, 4)
            captured["settings"] = settings
            return original_build(settings, dimension)

        with (
            mock.patch.object(
                launcher_play,
                "load_app_settings_payload",
                return_value={
                    "settings": {
                        "4d": {
                            "width": 6,
                            "height": 20,
                            "depth": 7,
                            "fourth": 5,
                            "bot_budget_ms": 52,
                        }
                    }
                },
            ),
            mock.patch.object(
                launcher_play,
                "open_display",
                side_effect=[object(), object()],
            ),
            mock.patch.object(
                frontend_nd_setup,
                "build_play_menu_config",
                side_effect=build_cfg,
            ),
            mock.patch.object(
                front4d_game,
                "run_game_loop",
                return_value=True,
            ) as run_game_loop_mock,
            mock.patch.object(
                launcher_play,
                "capture_windowed_display_settings",
                return_value=display_settings,
            ),
        ):
            result = launcher_play.launch_4d(
                screen=object(),
                fonts_nd=object(),
                display_settings=display_settings,
                tutorial_lesson_id="tutorial_4d_core",
            )

        self.assertTrue(result.keep_running)
        self.assertEqual(captured["settings"].width, 6)
        self.assertEqual(captured["settings"].height, 20)
        self.assertEqual(captured["settings"].depth, 7)
        self.assertEqual(captured["settings"].fourth, 5)
        self.assertEqual(run_game_loop_mock.call_args.kwargs["bot_budget_ms"], 52)
        self.assertEqual(
            run_game_loop_mock.call_args.kwargs["tutorial_lesson_id"],
            "tutorial_4d_core",
        )

    def test_tutorial_loop_context_uses_exact_3d_board_profile(self) -> None:
        cfg = GameConfigND(dims=(12, 30, 9), gravity_axis=1, speed_level=1)
        with mock.patch.object(
            front3d_game, "tutorial_runtime_create_session", return_value=object()
        ):
            loop = front3d_game.LoopContext3D.create(
                cfg,
                tutorial_lesson_id="tutorial_3d_core",
            )

        self.assertEqual(loop.cfg.dims, (6, 18, 6))
        self.assertEqual(loop.state.config.dims, (6, 18, 6))
        self.assertEqual(loop.state.board.dims, (6, 18, 6))

    def test_build_config_matches_shared_nd_builder(self) -> None:
        settings = frontend_nd_setup.GameSettingsND(
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

        cfg_adapter = frontend_nd_setup.build_config(settings, 3)
        cfg_shared = frontend_nd_setup.build_config(settings, 3)

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
        settings = frontend_nd_setup.GameSettingsND(speed_level=4)
        cfg = frontend_nd_setup.build_config(settings, 3)
        self.assertEqual(
            frontend_nd_setup.gravity_interval_ms_from_config(cfg),
            frontend_nd_setup.gravity_interval_ms_from_config(cfg),
        )

    def test_4d_setup_can_select_six_cell_piece_set(self) -> None:
        options_4d = piece_set_options_for_dimension(4)
        six_cell_index = options_4d.index(PIECE_SET_4D_SIX)
        settings = frontend_nd_setup.GameSettingsND(piece_set_index=six_cell_index)
        cfg = frontend_nd_setup.build_config(settings, 4)
        self.assertEqual(cfg.piece_set_id, PIECE_SET_4D_SIX)
        shapes = get_piece_shapes_nd(4, piece_set_id=cfg.piece_set_id)
        self.assertTrue(shapes)
        self.assertTrue(all(len(shape.blocks) == 6 for shape in shapes))

    def test_4d_exploration_mode_uses_fixed_compact_board_profile(self) -> None:
        settings = frontend_nd_setup.GameSettingsND(
            width=14,
            height=26,
            depth=9,
            fourth=8,
            exploration_mode=1,
        )
        cfg = frontend_nd_setup.build_config(settings, 4)
        self.assertEqual(cfg.dims, (8, 9, 7, 6))

    def test_nd_build_config_uses_mode_specific_topology_profiles(self) -> None:
        normal_profile = mock.Mock(
            topology_mode="bounded", edge_rules=(("bounded", "bounded"),) * 4
        )
        explorer_profile = SimpleNamespace(dimension=4, gluings=())
        with (
            mock.patch.object(
                frontend_nd_setup,
                "load_topology_profile",
                return_value=normal_profile,
            ) as load_profile,
            mock.patch.object(
                frontend_nd_setup,
                "resolve_direct_explorer_launch_profile",
                return_value=(
                    "bounded",
                    (("bounded", "bounded"),) * 4,
                    explorer_profile,
                ),
            ) as resolve_explorer,
            mock.patch.object(
                frontend_nd_setup,
                "build_explorer_transport_resolver",
                return_value=SimpleNamespace(dims=(8, 9, 7, 6)),
            ) as build_transport,
        ):
            normal_cfg = frontend_nd_setup.build_config(
                frontend_nd_setup.GameSettingsND(
                    topology_advanced=1, exploration_mode=0
                ),
                4,
            )
            explorer_cfg = frontend_nd_setup.build_config(
                frontend_nd_setup.GameSettingsND(
                    topology_advanced=0, exploration_mode=1
                ),
                4,
            )

        self.assertEqual(load_profile.call_args_list[0].args, ("normal", 4))
        self.assertEqual(resolve_explorer.call_args_list[0].kwargs["dimension"], 4)
        self.assertNotIn("topology_advanced", resolve_explorer.call_args_list[0].kwargs)
        self.assertNotIn("profile_index", resolve_explorer.call_args_list[0].kwargs)
        self.assertEqual(normal_cfg.topology_edge_rules[1], ("bounded", "bounded"))
        self.assertIs(explorer_cfg.explorer_topology_profile, explorer_profile)
        self.assertEqual(explorer_cfg.explorer_transport.dims, (8, 9, 7, 6))
        build_transport.assert_called_once_with(explorer_profile, (8, 9, 7, 6))

    def test_runtime_collect_cleared_ghost_cells_accepts_mixed_args_kwargs(
        self,
    ) -> None:
        state = SimpleNamespace(
            board=SimpleNamespace(
                last_cleared_cells=[
                    ((1, 2, 3), 6),
                    ((0, 1), 4),
                ]
            )
        )
        ghost_cells = runtime_collect_cleared_ghost_cells(
            state,
            expected_coord_len=3,
            color_for_cell=lambda cell_id: (cell_id, cell_id, cell_id),
        )
        self.assertEqual(ghost_cells, (((1, 2, 3), (6, 6, 6)),))

    def test_build_play_menu_config_forces_safe_topology_launch(self) -> None:
        with mock.patch.object(
            frontend_nd_setup,
            "build_config",
            return_value="cfg",
        ) as build_config:
            cfg = frontend_nd_setup.build_play_menu_config(
                frontend_nd_setup.GameSettingsND(
                    topology_advanced=1,
                    topology_profile_index=4,
                    exploration_mode=1,
                ),
                4,
            )

        self.assertEqual(cfg, "cfg")
        forwarded = build_config.call_args.args[0]
        self.assertEqual(forwarded.exploration_mode, 0)
        self.assertEqual(forwarded.topology_advanced, 0)
        self.assertEqual(forwarded.topology_profile_index, 0)
        self.assertEqual(build_config.call_args.args[1], 4)

    def test_nd_menu_fields_keep_only_safe_topology_controls(self) -> None:
        attrs = {
            attr_name
            for _label, attr_name, _min_val, _max_val in frontend_nd_setup.menu_fields_for_settings(
                frontend_nd_setup.GameSettingsND(
                    exploration_mode=0, topology_advanced=1
                ),
                4,
            )
        }
        self.assertIn("topology_mode", attrs)
        self.assertNotIn("topology_profile_index", attrs)
        self.assertNotIn("exploration_mode", attrs)
        self.assertNotIn("topology_advanced", attrs)

    def test_nd_export_uses_safe_topology_preset(self) -> None:
        state = frontend_nd_setup.MenuState(
            settings=frontend_nd_setup.GameSettingsND(
                exploration_mode=1, topology_advanced=1
            )
        )
        with mock.patch.object(
            frontend_nd_setup,
            "export_resolved_topology_profile",
        ) as export_profile:
            frontend_nd_setup._export_topology_profile(state, 4)

        export_profile.assert_called_once_with(
            dimension=4,
            gravity_axis=1,
            topology_mode="bounded",
            topology_advanced=False,
            profile_index=0,
        )


if __name__ == "__main__":
    unittest.main()
