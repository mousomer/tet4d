from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cli import front
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

    def test_non_topology_route_uses_registry_dispatch(self) -> None:
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

        close = front._handle_launcher_route(
            "tutorials",
            state,
            registry,
            session,
            fonts_nd=object(),
        )

        self.assertFalse(close)
        handler.assert_called_once()

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
