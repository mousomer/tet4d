from __future__ import annotations

import unittest

import pygame

from tet4d.ui.pygame.launch import launcher_settings
from tet4d.ui.pygame.launch import settings_hub_model
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings
from tet4d.ui.pygame.ui_utils import text_fits


class TestLauncherSettingsLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_unified_settings_rows_fit_compact_supported_width(self) -> None:
        fonts = type(
            "_Fonts",
            (),
            {
                "title_font": pygame.font.Font(None, 34),
                "menu_font": pygame.font.Font(None, 26),
                "hint_font": pygame.font.Font(None, 20),
            },
        )()
        state = settings_hub_model.build_unified_settings_state(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
        )
        width = 960
        panel_w = min(700, max(360, width - 40))
        panel_x = (width - panel_w) // 2
        label_left = panel_x + 22
        label_right = panel_x + panel_w - 22

        for row_kind, label, row_key in settings_hub_model._UNIFIED_SETTINGS_ROWS:
            if row_kind != "item":
                continue
            value = launcher_settings._unified_value_text(state, row_key)
            label_lines, value_lines, _row_height = (
                launcher_settings._wrapped_settings_row_layout(
                    fonts.menu_font,
                    label=label,
                    value=value,
                    panel_w=panel_w,
                )
            )
            value_draw_width = (
                max(fonts.menu_font.size(line)[0] for line in value_lines)
                if value_lines
                else 0
            )
            value_x = label_right - value_draw_width
            label_width = max(80, value_x - label_left - 10 if value else panel_w - 44)
            with self.subTest(label=label):
                self.assertGreater(len(label_lines), 0)
                for line in label_lines:
                    self.assertTrue(text_fits(fonts.menu_font, line, label_width))
                for line in value_lines:
                    self.assertTrue(text_fits(fonts.menu_font, line, int(panel_w * 0.34)))

    def test_advanced_gameplay_rows_fit_compact_supported_width(self) -> None:
        fonts = type(
            "_Fonts",
            (),
            {
                "title_font": pygame.font.Font(None, 34),
                "menu_font": pygame.font.Font(None, 26),
                "hint_font": pygame.font.Font(None, 20),
            },
        )()
        state = settings_hub_model.build_unified_settings_state(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
        )
        width = 960
        panel_w = min(760, max(420, width - 40))
        value_width = int(panel_w * 0.34)
        for row_key, label in launcher_settings._ADVANCED_GAMEPLAY_ROWS:
            value = launcher_settings._advanced_gameplay_value_text(state, row_key)
            label_lines, value_lines, _row_height = launcher_settings._wrapped_settings_row_layout(
                fonts.menu_font,
                label=label,
                value=value,
                panel_w=panel_w,
            )
            with self.subTest(label=label):
                self.assertGreater(len(label_lines), 0)
                for line in label_lines:
                    self.assertTrue(text_fits(fonts.menu_font, line, panel_w - 44))
                for line in value_lines:
                    self.assertTrue(text_fits(fonts.menu_font, line, value_width))
