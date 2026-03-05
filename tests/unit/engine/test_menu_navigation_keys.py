from __future__ import annotations

import unittest
from unittest.mock import patch

import pygame

from tet4d.ui.pygame.launch import bot_options_menu
from tet4d.ui.pygame.menu import keybindings_menu, menu_navigation_keys


class TestMenuNavigationKeys(unittest.TestCase):
    def test_q_does_not_map_to_escape_for_non_tiny_profiles(self) -> None:
        with patch.object(menu_navigation_keys, "active_key_profile", return_value="small"):
            self.assertEqual(
                menu_navigation_keys.normalize_menu_navigation_key(pygame.K_q),
                pygame.K_q,
            )

    def test_q_does_not_map_to_escape_for_tiny_profile(self) -> None:
        with patch.object(
            menu_navigation_keys,
            "active_key_profile",
            return_value=menu_navigation_keys.PROFILE_TINY,
        ):
            self.assertEqual(
                menu_navigation_keys.normalize_menu_navigation_key(pygame.K_q),
                pygame.K_q,
            )

    def test_tiny_profile_still_maps_ikjl_navigation(self) -> None:
        with patch.object(
            menu_navigation_keys,
            "active_key_profile",
            return_value=menu_navigation_keys.PROFILE_TINY,
        ):
            self.assertEqual(
                menu_navigation_keys.normalize_menu_navigation_key(pygame.K_i),
                pygame.K_UP,
            )
            self.assertEqual(
                menu_navigation_keys.normalize_menu_navigation_key(pygame.K_k),
                pygame.K_DOWN,
            )
            self.assertEqual(
                menu_navigation_keys.normalize_menu_navigation_key(pygame.K_j),
                pygame.K_LEFT,
            )
            self.assertEqual(
                menu_navigation_keys.normalize_menu_navigation_key(pygame.K_l),
                pygame.K_RIGHT,
            )

    def test_q_exits_bot_options_menu(self) -> None:
        state = bot_options_menu._BotMenuState(payload={})

        bot_options_menu._handle_bot_menu_key(state, pygame.K_q)

        self.assertFalse(state.running)

    def test_q_exits_keybindings_binding_menu(self) -> None:
        state = keybindings_menu.KeybindingsMenuState(
            section_mode=False,
            allow_scope_sections=True,
        )

        should_exit = keybindings_menu._run_binding_mode_action(
            state,
            pygame.K_q,
            menu_navigation_keys.normalize_menu_navigation_key(pygame.K_q),
            rows=[],
        )

        self.assertTrue(should_exit)
        self.assertFalse(state.section_mode)

    def test_q_exits_keybindings_section_menu(self) -> None:
        state = keybindings_menu.KeybindingsMenuState(section_mode=True)

        should_exit = keybindings_menu._handle_section_key(
            state,
            pygame.K_q,
            menu_navigation_keys.normalize_menu_navigation_key(pygame.K_q),
        )

        self.assertTrue(should_exit)


if __name__ == "__main__":
    unittest.main()
