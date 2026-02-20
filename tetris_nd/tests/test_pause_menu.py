from __future__ import annotations

import unittest
from unittest.mock import patch

import pygame

from tetris_nd.audio import AudioSettings
from tetris_nd.display import DisplaySettings
from tetris_nd.launcher_settings import SettingsHubResult
from tetris_nd import pause_menu


class TestPauseMenuSettingsRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_settings_action_routes_to_shared_settings_hub(self) -> None:
        screen = pygame.Surface((640, 480))
        state = pause_menu._PauseState(selected=pause_menu._PAUSE_ACTION_CODES.index("settings"))

        with patch("tetris_nd.pause_menu.run_settings_hub_menu") as run_hub:
            run_hub.return_value = SettingsHubResult(
                screen=screen,
                audio_settings=AudioSettings(),
                display_settings=DisplaySettings(),
                keep_running=True,
            )
            out_screen, keep_running = pause_menu._handle_pause_row(
                screen,
                object(),
                state,
                dimension=4,
            )

        self.assertTrue(keep_running)
        self.assertIs(out_screen, screen)
        self.assertEqual(state.status, "Returned from settings")
        self.assertFalse(state.status_error)
        run_hub.assert_called_once()

    def test_settings_action_propagates_quit_when_hub_requests_stop(self) -> None:
        screen = pygame.Surface((640, 480))
        state = pause_menu._PauseState(selected=pause_menu._PAUSE_ACTION_CODES.index("settings"))

        with patch("tetris_nd.pause_menu.run_settings_hub_menu") as run_hub:
            run_hub.return_value = SettingsHubResult(
                screen=screen,
                audio_settings=AudioSettings(),
                display_settings=DisplaySettings(),
                keep_running=False,
            )
            out_screen, keep_running = pause_menu._handle_pause_row(
                screen,
                object(),
                state,
                dimension=3,
            )

        self.assertFalse(keep_running)
        self.assertIs(out_screen, screen)
        self.assertTrue(state.status_error)
        self.assertIn("Settings exited", state.status)
        run_hub.assert_called_once()

    def test_pause_values_show_analytics_in_settings_summary(self) -> None:
        values = pause_menu._pause_menu_values(4)
        self.assertEqual(values[2], "Audio + Display + Analytics")

