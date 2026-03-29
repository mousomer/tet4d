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
            value_width = int(panel_w * 0.34) if value else 0
            value_draw_width = (
                min(fonts.menu_font.size(value)[0], value_width) if value else 0
            )
            value_x = label_right - value_draw_width
            label_width = max(
                80,
                value_x - label_left - 10 if value else panel_w - 44,
            )
            with self.subTest(label=label):
                self.assertTrue(text_fits(fonts.menu_font, label, label_width))
