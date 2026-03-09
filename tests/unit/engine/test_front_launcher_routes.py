from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cli import front
from tet4d.engine.gameplay.topology_designer import GAMEPLAY_MODE_NORMAL
from tet4d.ui.pygame.menu.menu_runner import ActionRegistry


class TestFrontLauncherRoutes(unittest.TestCase):
    def test_topology_lab_action_updates_status(self) -> None:
        state = front.MainMenuState(last_mode="3d")
        session = SimpleNamespace(
            screen=object(),
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )

        with (
            patch.object(front, "_persist_session_status"),
            patch.object(
                front,
                "run_topology_lab_menu",
                return_value=(True, "Topology lab saved"),
            ) as run_lab,
        ):
            close = front._menu_action_topology_lab(
                state,
                session,
                object(),
            )

        self.assertFalse(close)
        self.assertEqual(state.status, "Topology lab saved")
        self.assertFalse(state.status_error)
        run_lab.assert_called_once()
        launch = run_lab.call_args.kwargs["launch"]
        self.assertEqual(launch.dimension, 3)
        self.assertEqual(launch.entry_source, "lab")
        self.assertEqual(launch.gameplay_mode, GAMEPLAY_MODE_NORMAL)

    def test_non_tutorial_route_uses_registry_dispatch(self) -> None:
        state = front.MainMenuState(last_mode="2d")
        session = SimpleNamespace(
            screen=object(),
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )
        registry = ActionRegistry()
        handler = Mock(return_value=False)
        registry.register("help", handler)

        with patch.dict(front._LAUNCHER_ROUTE_ACTIONS, {"custom_route": "help"}, clear=False):
            close = front._handle_launcher_route(
                "custom_route",
                state,
                registry,
                session,
                fonts_nd=object(),
                fonts_2d=object(),
            )

        self.assertFalse(close)
        handler.assert_called_once()

    def test_tutorial_action_launches_lesson(self) -> None:
        state = front.MainMenuState(last_mode="3d")
        session = SimpleNamespace(
            screen=object(),
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )

        with (
            patch.object(
                front,
                "tutorial_lesson_ids_runtime",
                return_value=(
                    "tutorial_2d_core",
                    "tutorial_3d_core",
                    "tutorial_4d_core",
                ),
            ),
            patch.object(front, "_launch_mode") as launch_mode,
        ):
            close = front._menu_action_tutorial_dimension(
                "2d",
                state,
                session,
                fonts_nd=object(),
                fonts_2d=object(),
            )

        self.assertFalse(close)
        launch_mode.assert_called_once()

    def test_unknown_route_sets_error_status(self) -> None:
        state = front.MainMenuState(last_mode="2d")
        session = SimpleNamespace(
            screen=object(),
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )
        registry = ActionRegistry()

        close = front._handle_launcher_route(
            "missing_route",
            state,
            registry,
            session,
            fonts_nd=object(),
            fonts_2d=object(),
        )

        self.assertFalse(close)
        self.assertTrue(state.status_error)
        self.assertIn("No action mapped", state.status)

    def test_leaderboard_action_opens_menu(self) -> None:
        state = front.MainMenuState(last_mode="2d")
        screen = object()
        session = SimpleNamespace(
            screen=screen,
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )

        with patch.object(front, "run_leaderboard_menu", return_value=screen) as run_lb:
            close = front._menu_action_leaderboard(state, session, object())

        self.assertFalse(close)
        run_lb.assert_called_once()


if __name__ == "__main__":
    unittest.main()
