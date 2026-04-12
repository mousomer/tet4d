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

    def test_mouse_click_back_hitbox_uses_root_escape_handler(self) -> None:
        menus = {
            "root": {
                "title": "Root",
                "items": ({"type": "action", "label": "Resume", "action_id": "resume"},),
            }
        }
        registry = ActionRegistry()
        registry.register("resume", lambda: False)
        calls = {"root_escape": 0}

        runner = MenuRunner(
            menus=menus,
            start_menu_id="root",
            action_registry=registry,
            render_menu=lambda *_args: None,
            on_root_escape=lambda: calls.__setitem__("root_escape", calls["root_escape"] + 1)
            or True,
        )

        with patch.object(
            pygame.event,
            "get",
            return_value=[
                pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN,
                    {"button": 1, "pos": (24, 24)},
                )
            ],
        ):
            runner.run()

        self.assertEqual(calls["root_escape"], 1)

    def test_action_group_left_right_changes_subaction_before_enter(self) -> None:
        menus = {
            "root": {
                "title": "Root",
                "items": (
                    {
                        "id": "play_2d_row",
                        "type": "action_group",
                        "label": "2D",
                        "default_action_id": "play",
                        "actions": (
                            {"id": "play", "label": "Play", "action_id": "play_2d"},
                            {"id": "setup", "label": "Setup", "action_id": "setup_2d"},
                        ),
                    },
                ),
            }
        }
        registry = ActionRegistry()
        calls = {"play": 0, "setup": 0}
        registry.register(
            "play_2d",
            lambda: calls.__setitem__("play", calls["play"] + 1) or False,
        )
        registry.register(
            "setup_2d",
            lambda: calls.__setitem__("setup", calls["setup"] + 1) or True,
        )

        runner = MenuRunner(
            menus=menus,
            start_menu_id="root",
            action_registry=registry,
            render_menu=lambda *_args: None,
        )

        with patch.object(
            pygame.event,
            "get",
            side_effect=[
                [pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})],
                [pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})],
            ],
        ):
            runner.run()

        self.assertEqual(calls["play"], 0)
        self.assertEqual(calls["setup"], 1)


if __name__ == "__main__":
    unittest.main()
