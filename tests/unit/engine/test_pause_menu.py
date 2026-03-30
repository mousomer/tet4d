from __future__ import annotations

import unittest
from unittest.mock import patch

import pygame

from tet4d.ui.pygame.runtime_ui.audio import AudioSettings
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.launch.settings_hub_model import SettingsHubResult
from tet4d.ui.pygame.runtime_ui import pause_menu
from tet4d.ui.pygame.ui_utils import text_fits


class TestPauseMenuSettingsRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_settings_action_routes_to_shared_settings_hub(self) -> None:
        screen = pygame.Surface((640, 480))
        state = pause_menu._PauseState(
            selected=pause_menu._PAUSE_ACTION_CODES.index("settings")
        )

        with patch(
            "tet4d.ui.pygame.runtime_ui.pause_menu.run_settings_hub_menu"
        ) as run_hub:
            run_hub.return_value = SettingsHubResult(
                screen=screen,
                audio_settings=AudioSettings(),
                display_settings=DisplaySettings(),
                keep_running=True,
            )
            action = pause_menu._PAUSE_ACTION_CODES[state.selected]
            out_screen, keep_running = pause_menu._handle_pause_action(
                action,
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
        state = pause_menu._PauseState(
            selected=pause_menu._PAUSE_ACTION_CODES.index("settings")
        )

        with patch(
            "tet4d.ui.pygame.runtime_ui.pause_menu.run_settings_hub_menu"
        ) as run_hub:
            run_hub.return_value = SettingsHubResult(
                screen=screen,
                audio_settings=AudioSettings(),
                display_settings=DisplaySettings(),
                keep_running=False,
            )
            action = pause_menu._PAUSE_ACTION_CODES[state.selected]
            out_screen, keep_running = pause_menu._handle_pause_action(
                action,
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
        settings_index = pause_menu._PAUSE_ACTION_CODES.index("settings")
        self.assertEqual(values[settings_index], "Audio + Display + Analytics")

    def test_restart_action_sets_restart_decision(self) -> None:
        screen = pygame.Surface((640, 480))
        state = pause_menu._PauseState(
            selected=pause_menu._PAUSE_ACTION_CODES.index("restart")
        )

        action = pause_menu._PAUSE_ACTION_CODES[state.selected]
        out_screen, keep_running = pause_menu._handle_pause_action(
            action,
            screen,
            object(),
            state,
            dimension=2,
        )

        self.assertTrue(keep_running)
        self.assertIs(out_screen, screen)
        self.assertEqual(state.decision, "restart")
        self.assertFalse(state.running)

    def test_leaderboard_action_routes_to_leaderboard_menu(self) -> None:
        screen = pygame.Surface((640, 480))
        state = pause_menu._PauseState(
            selected=pause_menu._PAUSE_ACTION_CODES.index("leaderboard")
        )

        with patch(
            "tet4d.ui.pygame.runtime_ui.pause_menu.run_leaderboard_menu",
            return_value=screen,
        ) as run_lb:
            action = pause_menu._PAUSE_ACTION_CODES[state.selected]
            out_screen, keep_running = pause_menu._handle_pause_action(
                action,
                screen,
                object(),
                state,
                dimension=3,
            )

        self.assertTrue(keep_running)
        self.assertIs(out_screen, screen)
        self.assertEqual(state.status, "Returned from leaderboard")
        self.assertFalse(state.status_error)
        run_lb.assert_called_once()

    def test_pause_menu_does_not_expose_tutorial_skip_action(self) -> None:
        self.assertNotIn("tutorial_skip", pause_menu._PAUSE_ACTION_CODES)

    def test_pause_menu_does_not_expose_tutorial_restart_action(self) -> None:
        self.assertNotIn("tutorial_restart", pause_menu._PAUSE_ACTION_CODES)

    def test_pause_menu_keydown_escape_returns_resume(self) -> None:
        state = pause_menu._PauseState()
        callback_hits = {"count": 0}

        def _on_escape_back() -> None:
            callback_hits["count"] += 1

        consumed = pause_menu._pause_menu_keydown(
            state,
            key=pygame.K_ESCAPE,
            stack_depth=1,
            on_escape_back=_on_escape_back,
        )

        self.assertTrue(consumed)
        self.assertEqual(state.decision, "resume")
        self.assertFalse(state.running)
        self.assertEqual(callback_hits["count"], 1)

    def test_pause_menu_keydown_q_exits(self) -> None:
        state = pause_menu._PauseState()
        callback_hits = {"count": 0}

        def _on_escape_back() -> None:
            callback_hits["count"] += 1

        consumed = pause_menu._pause_menu_keydown(
            state,
            key=pygame.K_q,
            stack_depth=1,
            on_escape_back=_on_escape_back,
        )

        self.assertTrue(consumed)
        self.assertEqual(state.decision, "quit")
        self.assertFalse(state.running)
        self.assertEqual(callback_hits["count"], 0)

    def test_run_pause_menu_escape_closes_as_resume(self) -> None:
        class _Fonts:
            title_font = pygame.font.Font(None, 32)
            menu_font = pygame.font.Font(None, 26)
            hint_font = pygame.font.Font(None, 20)

        screen = pygame.Surface((640, 480))
        esc_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})

        with (
            patch.object(pygame.event, "get", return_value=[esc_event]),
            patch.object(pygame.display, "flip", return_value=None),
        ):
            decision, _next_screen = pause_menu.run_pause_menu(
                screen,
                _Fonts(),
                dimension=2,
            )

        self.assertEqual(decision, "resume")

    def test_run_pause_menu_q_closes_as_quit(self) -> None:
        class _Fonts:
            title_font = pygame.font.Font(None, 32)
            menu_font = pygame.font.Font(None, 26)
            hint_font = pygame.font.Font(None, 20)

        screen = pygame.Surface((640, 480))
        quit_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_q})

        with (
            patch.object(pygame.event, "get", return_value=[quit_event]),
            patch.object(pygame.display, "flip", return_value=None),
        ):
            decision, _next_screen = pause_menu.run_pause_menu(
                screen,
                _Fonts(),
                dimension=2,
            )

        self.assertEqual(decision, "quit")

    def test_pause_menu_compact_panel_keeps_required_rows_visible(self) -> None:
        fonts = type(
            "_Fonts",
            (),
            {
                "title_font": pygame.font.Font(None, 32),
                "menu_font": pygame.font.Font(None, 26),
                "hint_font": pygame.font.Font(None, 20),
            },
        )()
        width = 960
        panel_w = min(660, max(320, width - 40))
        label_left = ((width - panel_w) // 2) + 20
        label_right = ((width - panel_w) // 2) + panel_w - 20
        value_width = int(panel_w * 0.34)

        for row, value_text in zip(
            pause_menu._PAUSE_ROWS,
            pause_menu._pause_menu_values(4),
            strict=True,
        ):
            value_draw_width = (
                fonts.menu_font.size(value_text)[0] if value_text else 0
            )
            value_x = label_right - min(value_draw_width, value_width)
            label_width = max(
                64,
                value_x - label_left - 10 if value_text else panel_w - 52,
            )
            with self.subTest(row=row):
                self.assertTrue(text_fits(fonts.menu_font, row, label_width))
