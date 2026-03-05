from __future__ import annotations

import unittest
from unittest.mock import patch

import pygame

from tet4d.ui.pygame.menu.menu_runner import ActionRegistry, MenuRunner


class TestMenuRunnerNavigationPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_q_uses_quit_handler_not_root_escape(self) -> None:
        menus = {
            "root": {
                "title": "Root",
                "items": ({"type": "action", "label": "Resume", "action_id": "resume"},),
            }
        }
        registry = ActionRegistry()
        registry.register("resume", lambda: False)
        calls = {"quit": 0, "root_escape": 0}

        runner = MenuRunner(
            menus=menus,
            start_menu_id="root",
            action_registry=registry,
            render_menu=lambda *_args: None,
            on_root_escape=lambda: calls.__setitem__("root_escape", calls["root_escape"] + 1)
            or True,
            on_quit_event=lambda: calls.__setitem__("quit", calls["quit"] + 1) or True,
        )

        with patch.object(
            pygame.event,
            "get",
            return_value=[pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_q})],
        ):
            runner.run()

        self.assertEqual(calls["quit"], 1)
        self.assertEqual(calls["root_escape"], 0)

    def test_escape_at_root_uses_root_escape_handler(self) -> None:
        menus = {
            "root": {
                "title": "Root",
                "items": ({"type": "action", "label": "Resume", "action_id": "resume"},),
            }
        }
        registry = ActionRegistry()
        registry.register("resume", lambda: False)
        calls = {"quit": 0, "root_escape": 0}

        runner = MenuRunner(
            menus=menus,
            start_menu_id="root",
            action_registry=registry,
            render_menu=lambda *_args: None,
            on_root_escape=lambda: calls.__setitem__("root_escape", calls["root_escape"] + 1)
            or True,
            on_quit_event=lambda: calls.__setitem__("quit", calls["quit"] + 1) or True,
        )

        with patch.object(
            pygame.event,
            "get",
            return_value=[pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})],
        ):
            runner.run()

        self.assertEqual(calls["root_escape"], 1)
        self.assertEqual(calls["quit"], 0)


if __name__ == "__main__":
    unittest.main()
