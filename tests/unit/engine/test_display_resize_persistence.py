from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import pygame

from tet4d.ui.pygame import front2d_game as front2d
from tet4d.ui.pygame import front2d_frame, front2d_results
from tet4d.engine.gameplay.game2d import GameConfig
from tet4d.ui.pygame.launch import launcher_nd_runner
from tet4d.ui.pygame.runtime_ui import app_runtime, loop_runner_nd
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.engine.topology_explorer import ExplorerTopologyProfile


class RuntimeResizePersistenceTests(unittest.TestCase):
    def test_capture_windowed_display_settings_from_event_persists_resize(self) -> None:
        settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        event = pygame.event.Event(pygame.VIDEORESIZE, {"w": 1400, "h": 900})

        with patch.object(app_runtime, "save_display_settings") as save_mock:
            updated = app_runtime.capture_windowed_display_settings_from_event(
                settings,
                event=event,
            )

        self.assertEqual(updated.windowed_size, (1400, 900))
        save_mock.assert_called_once_with(windowed_size=(1400, 900))

    def test_capture_windowed_display_settings_from_event_ignores_fullscreen(
        self,
    ) -> None:
        settings = DisplaySettings(fullscreen=True, windowed_size=(1200, 760))
        event = pygame.event.Event(pygame.VIDEORESIZE, {"w": 1500, "h": 920})

        with patch.object(app_runtime, "save_display_settings") as save_mock:
            updated = app_runtime.capture_windowed_display_settings_from_event(
                settings,
                event=event,
            )

        self.assertEqual(updated, settings)
        save_mock.assert_not_called()

    def test_capture_windowed_display_settings_from_event_uses_surface_fallback(
        self,
    ) -> None:
        settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        event = pygame.event.Event(pygame.VIDEORESIZE, {})
        surface = Mock()
        surface.get_size.return_value = (300, 200)

        with (
            patch.object(app_runtime, "save_display_settings") as save_mock,
            patch("pygame.display.get_surface", return_value=surface),
        ):
            updated = app_runtime.capture_windowed_display_settings_from_event(
                settings,
                event=event,
            )

        self.assertEqual(updated.windowed_size, (640, 480))
        save_mock.assert_called_once_with(windowed_size=(640, 480))

    def test_launcher_nd_runner_captures_windowed_size_on_quit(self) -> None:
        display_settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        capture_result = DisplaySettings(fullscreen=False, windowed_size=(1360, 820))

        with (
            patch.object(
                launcher_nd_runner, "open_display", return_value=Mock()
            ) as open_display_mock,
            patch.object(
                launcher_nd_runner,
                "capture_windowed_display_settings",
                return_value=capture_result,
            ) as capture_mock,
        ):
            launcher_nd_runner.run_nd_mode_launcher(
                display_settings=display_settings,
                fonts=object(),
                setup_caption="setup",
                game_caption="game",
                run_menu=lambda *_args: object(),
                build_config=lambda _settings: object(),
                suggested_window_size=lambda _cfg: (1200, 760),
                run_game=lambda *_args: False,
            )

        self.assertEqual(open_display_mock.call_count, 2)
        capture_mock.assert_called_once_with(display_settings)

    def test_launcher_nd_runner_routes_explorer_modes_into_playground(self) -> None:
        display_settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        capture_result = DisplaySettings(fullscreen=False, windowed_size=(1360, 820))
        cfg = SimpleNamespace(exploration_mode=True, ndim=3)
        with (
            patch.object(
                launcher_nd_runner,
                "open_display",
                side_effect=[Mock(), Mock(), Mock()],
            ) as open_display_mock,
            patch.object(
                launcher_nd_runner,
                "capture_windowed_display_settings",
                return_value=capture_result,
            ) as capture_mock,
        ):
            run_game = Mock(return_value=False)
            run_explorer = Mock(return_value=True)
            launcher_nd_runner.run_nd_mode_launcher(
                display_settings=display_settings,
                fonts=object(),
                setup_caption="setup",
                game_caption="game",
                run_menu=Mock(side_effect=[object(), None]),
                build_config=lambda _settings: cfg,
                suggested_window_size=lambda _cfg: (1200, 760),
                run_game=run_game,
                run_explorer=run_explorer,
            )

        self.assertEqual(open_display_mock.call_count, 3)
        run_explorer.assert_called_once()
        run_game.assert_not_called()
        capture_mock.assert_called_once_with(display_settings)

    def test_launcher_nd_runner_default_explorer_path_builds_shared_launch(
        self,
    ) -> None:
        display_settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        capture_result = DisplaySettings(fullscreen=False, windowed_size=(1360, 820))
        explorer_profile = ExplorerTopologyProfile(dimension=4, gluings=())
        cfg = SimpleNamespace(
            exploration_mode=True, ndim=4, explorer_topology_profile=explorer_profile
        )
        with (
            patch.object(
                launcher_nd_runner,
                "open_display",
                side_effect=[Mock(), Mock(), Mock()],
            ),
            patch.object(
                launcher_nd_runner,
                "capture_windowed_display_settings",
                return_value=capture_result,
            ),
            patch.object(
                launcher_nd_runner,
                "run_explorer_playground",
                return_value=(True, "ok"),
            ) as run_playground,
        ):
            launcher_nd_runner.run_nd_mode_launcher(
                display_settings=display_settings,
                fonts=object(),
                setup_caption="setup",
                game_caption="game",
                run_menu=Mock(side_effect=[object(), None]),
                build_config=lambda _settings: cfg,
                suggested_window_size=lambda _cfg: (1200, 760),
                run_game=Mock(return_value=False),
            )

        run_playground.assert_called_once()
        launch = run_playground.call_args.kwargs["launch"]
        self.assertEqual(launch.dimension, 4)
        self.assertEqual(launch.entry_source, "explorer")
        self.assertIs(launch.explorer_profile, explorer_profile)

    def test_launcher_nd_runner_default_explorer_path_ignores_playground_status_failures(
        self,
    ) -> None:
        display_settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        capture_result = DisplaySettings(fullscreen=False, windowed_size=(1360, 820))
        explorer_profile = ExplorerTopologyProfile(dimension=4, gluings=())
        cfg = SimpleNamespace(
            exploration_mode=True, ndim=4, explorer_topology_profile=explorer_profile
        )
        run_game = Mock(return_value=False)

        with (
            patch.object(
                launcher_nd_runner,
                "open_display",
                side_effect=[Mock(), Mock(), Mock()],
            ) as open_display_mock,
            patch.object(
                launcher_nd_runner,
                "capture_windowed_display_settings",
                return_value=capture_result,
            ),
            patch.object(
                launcher_nd_runner,
                "run_explorer_playground",
                return_value=(False, "recoverable playground status"),
            ) as run_playground,
        ):
            launcher_nd_runner.run_nd_mode_launcher(
                display_settings=display_settings,
                fonts=object(),
                setup_caption="setup",
                game_caption="game",
                run_menu=Mock(side_effect=[object(), None]),
                build_config=lambda _settings: cfg,
                suggested_window_size=lambda _cfg: (1200, 760),
                run_game=run_game,
            )

        run_playground.assert_called_once()
        run_game.assert_not_called()
        self.assertEqual(open_display_mock.call_count, 3)

    def test_front2d_run_routes_explorer_launch_into_topology_playground(self) -> None:
        display_settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        runtime = SimpleNamespace(display_settings=display_settings)
        settings = SimpleNamespace(exploration_mode=1)
        cfg = SimpleNamespace(
            exploration_mode=True,
            explorer_topology_profile=ExplorerTopologyProfile(dimension=2, gluings=()),
        )
        with (
            patch.object(front2d, "initialize_runtime", return_value=runtime),
            patch.object(front2d, "init_fonts", return_value=object()),
            patch.object(front2d, "open_display", side_effect=[Mock(), Mock(), Mock()]),
            patch.object(front2d, "run_menu", side_effect=[settings, None]),
            patch.object(front2d, "_config_from_settings", return_value=cfg),
            patch.object(
                front2d, "run_explorer_playground", return_value=(True, "ok")
            ) as run_playground,
            patch.object(front2d, "run_game_loop") as run_game_loop,
            patch.object(
                front2d,
                "capture_windowed_display_settings",
                return_value=display_settings,
            ),
            patch.object(front2d.pygame, "quit"),
            patch.object(front2d.sys, "exit"),
        ):
            front2d.run()

        run_playground.assert_called_once()
        launch = run_playground.call_args.kwargs["launch"]
        self.assertEqual(launch.dimension, 2)
        self.assertEqual(launch.entry_source, "explorer")
        self.assertIs(launch.explorer_profile, cfg.explorer_topology_profile)
        run_game_loop.assert_not_called()

    def test_run_nd_loop_forwards_non_key_event_handler(self) -> None:
        resize_event = pygame.event.Event(pygame.VIDEORESIZE, {"w": 1280, "h": 800})
        observed: list[int] = []

        loop = SimpleNamespace(
            gravity_accumulator=0,
            refresh_score_multiplier=lambda: None,
            keydown_handler=lambda _event: "continue",
            on_restart=lambda: None,
            on_toggle_grid=lambda: None,
        )

        def fake_process_game_events(**kwargs):
            handler = kwargs.get("event_handler")
            if handler is not None:
                handler(resize_event)
            return "quit"

        with patch.object(
            loop_runner_nd, "process_game_events", side_effect=fake_process_game_events
        ):
            result = loop_runner_nd.run_nd_loop(
                screen=Mock(),
                fonts=object(),
                loop=loop,
                gravity_interval_from_config=lambda _cfg: 500,
                pause_dimension=3,
                run_pause_menu=lambda *_args, **_kwargs: ("continue", Mock()),
                run_help_menu=lambda *_args, **_kwargs: Mock(),
                spawn_clear_animation=lambda *_args, **_kwargs: (None, 0),
                step_view=lambda _dt: None,
                draw_frame=lambda _screen, _overlay: None,
                play_clear_sfx=lambda: None,
                play_game_over_sfx=lambda: None,
                event_handler=lambda event: observed.append(event.type),
            )

        self.assertFalse(result)
        self.assertEqual(observed, [resize_event.type])

    def test_front2d_run_game_loop_handles_resize_events(self) -> None:
        resize_event = pygame.event.Event(pygame.VIDEORESIZE, {"w": 1333, "h": 777})
        display_settings = DisplaySettings(fullscreen=False, windowed_size=(1200, 760))
        loop = SimpleNamespace(
            gravity_accumulator=0,
            refresh_score_multiplier=lambda: None,
            keydown_handler=lambda _event: "continue",
            on_restart=lambda: None,
            on_toggle_grid=lambda: None,
        )

        def fake_process_game_events(**kwargs):
            handler = kwargs.get("event_handler")
            if handler is not None:
                handler(resize_event)
            return "quit"

        with (
            patch.object(front2d.LoopContext2D, "create", return_value=loop),
            patch.object(front2d_frame, "_configure_game_loop", return_value=500),
            patch.object(
                front2d_frame,
                "capture_windowed_display_settings_from_event",
                return_value=DisplaySettings(
                    fullscreen=False,
                    windowed_size=(1333, 777),
                ),
            ) as capture_event_mock,
            patch.object(
                front2d_frame,
                "process_game_events",
                side_effect=fake_process_game_events,
            ),
        ):
            result = front2d.run_game_loop(
                screen=Mock(),
                cfg=SimpleNamespace(exploration_mode=False),
                fonts=object(),
                display_settings=display_settings,
            )

        self.assertFalse(result)
        capture_event_mock.assert_called_once()

    def test_loop_context_2d_uses_exact_tutorial_board_profile(self) -> None:
        cfg = GameConfig(width=4, height=8, gravity_axis=1, speed_level=1)
        loop = front2d.LoopContext2D.create(
            cfg,
            tutorial_lesson_id="tutorial_2d_core",
        )

        self.assertEqual((loop.cfg.width, loop.cfg.height), (10, 20))
        self.assertEqual(
            (loop.state.config.width, loop.state.config.height),
            (10, 20),
        )
        self.assertEqual(loop.state.board.dims, (10, 20))

    def test_front2d_menu_restart_triggers_loop_restart(self) -> None:
        loop = SimpleNamespace(on_restart=Mock())
        screen = Mock()
        next_screen = Mock()

        with patch.object(
            front2d_results,
            "run_pause_menu",
            return_value=("restart", next_screen),
        ):
            status, returned_screen = front2d._resolve_loop_decision(
                decision="menu",
                screen=screen,
                fonts=object(),
                loop=loop,
            )

        self.assertEqual(status, "restart")
        self.assertIs(returned_screen, next_screen)
        loop.on_restart.assert_called_once()

    def test_nd_menu_restart_triggers_loop_restart(self) -> None:
        loop = SimpleNamespace(on_restart=Mock())
        screen = Mock()
        next_screen = Mock()

        status, returned_screen = loop_runner_nd._resolve_menu_decision(
            decision="menu",
            screen=screen,
            fonts=object(),
            loop=loop,
            pause_dimension=4,
            run_pause_menu=lambda *_args, **_kwargs: ("restart", next_screen),
        )

        self.assertEqual(status, "restart")
        self.assertIs(returned_screen, next_screen)
        loop.on_restart.assert_called_once()


if __name__ == "__main__":
    unittest.main()
