from __future__ import annotations

import unittest

import pygame

from tet4d.ui.pygame.launch import launcher_settings
from tet4d.ui.pygame.launch import settings_hub_model
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings
from tet4d.ui.pygame.ui_utils import text_fits, wrapped_label_value_layout


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
                wrapped_label_value_layout(
                    fonts.menu_font,
                    label=label,
                    value=value,
                    total_width=panel_w,
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

    def test_inline_game_settings_advanced_rows_fit_compact_supported_width(self) -> None:
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
        advanced_rows = {
            "rotation_animation_mode",
            "kick_level_index",
            "rotation_animation_duration_ms_2d",
            "rotation_animation_duration_ms_nd",
            "translation_animation_duration_ms",
            "auto_speedup_enabled",
            "lines_per_level",
            "topology_cache_measure",
            "topology_cache_clear",
        }
        for kind, label, row_key in settings_hub_model.settings_rows_for_category("gameplay"):
            if kind != "item" or row_key not in advanced_rows:
                continue
            value = launcher_settings._unified_value_text(state, row_key)
            label_lines, value_lines, _row_height = wrapped_label_value_layout(
                fonts.menu_font,
                label=label,
                value=value,
                total_width=panel_w,
            )
            with self.subTest(label=label):
                self.assertGreater(len(label_lines), 0)
                for line in label_lines:
                    self.assertTrue(text_fits(fonts.menu_font, line, panel_w - 44))
                for line in value_lines:
                    self.assertTrue(text_fits(fonts.menu_font, line, value_width))

    def test_audio_category_rows_exclude_other_settings_sections(self) -> None:
        rows = settings_hub_model.settings_rows_for_category("audio")
        labels = [label for kind, label, _row_key in rows if kind == "header"]
        row_keys = [row_key for kind, _label, row_key in rows if kind == "item"]

        self.assertEqual(labels, ["Audio"])
        self.assertIn("audio_master", row_keys)
        self.assertIn("audio_sfx", row_keys)
        self.assertIn("audio_mute", row_keys)
        self.assertNotIn("display_fullscreen", row_keys)
        self.assertNotIn("game_seed", row_keys)
        self.assertTrue({"save", "reset", "back"}.issubset(set(row_keys)))

    def test_game_category_rows_keep_analytics_with_game_settings(self) -> None:
        rows = settings_hub_model.settings_rows_for_category("gameplay")
        labels = [label for kind, label, _row_key in rows if kind == "header"]
        row_keys = [row_key for kind, _label, row_key in rows if kind == "item"]

        self.assertEqual(labels, ["Game", "Advanced gameplay", "Analytics"])
        self.assertIn("game_seed", row_keys)
        self.assertIn("game_random_mode", row_keys)
        self.assertIn("rotation_animation_mode", row_keys)
        self.assertIn("kick_level_index", row_keys)
        self.assertIn("analytics_score_logging", row_keys)
        self.assertNotIn("audio_master", row_keys)
        self.assertNotIn("display_fullscreen", row_keys)
