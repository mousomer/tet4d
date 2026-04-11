from __future__ import annotations

import unittest

import pygame

from tet4d.engine.runtime.menu_config import setup_fields_for_settings
from tet4d.ui.pygame.launch import launcher_settings
from tet4d.ui.pygame.launch import settings_hub_model
from tet4d.ui.pygame.frontend_nd_setup import GameSettingsND, _menu_value_text
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings
from tet4d.ui.pygame.ui_utils import (
    compute_slider_row_layout,
    menu_slider_row_min_total_width,
    text_fits,
)


class TestLauncherSettingsLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def _fonts(self):
        return type(
            "_Fonts",
            (),
            {
                "title_font": pygame.font.Font(None, 34),
                "menu_font": pygame.font.Font(None, 26),
                "hint_font": pygame.font.Font(None, 20),
            },
        )()

    def _assert_slider_layout_fits(
        self,
        *,
        font: pygame.font.Font,
        label: str,
        value: str,
        total_width: int,
    ) -> None:
        layout = compute_slider_row_layout(
            font,
            label=label,
            value=value,
            total_width=total_width,
        )
        self.assertGreaterEqual(layout.slider_height, 12)
        self.assertGreaterEqual(layout.slider_width, 176)
        self.assertGreater(layout.row_height, font.get_height() + layout.slider_height)
        consumed_width = (
            layout.label_width
            + layout.slider_width
            + layout.slider_gap
            + (
                layout.value_width + layout.text_gap
                if layout.value_width > 0
                else 0
            )
        )
        self.assertLessEqual(consumed_width, total_width)
        for line in layout.label_lines:
            self.assertTrue(text_fits(font, line, layout.label_width))
        for line in layout.value_lines:
            self.assertTrue(text_fits(font, line, layout.value_width))

    def test_shared_slider_layout_uses_larger_geometry(self) -> None:
        fonts = self._fonts()
        layout = compute_slider_row_layout(
            fonts.menu_font,
            label="Locked-cell transparency",
            value="25%",
            total_width=520,
        )
        self.assertGreaterEqual(layout.slider_width, 176)
        self.assertEqual(layout.slider_height, 12)
        self.assertGreaterEqual(layout.row_height, 54)

    def test_unified_settings_slider_rows_fit_compact_supported_width(self) -> None:
        fonts = self._fonts()
        state = settings_hub_model.build_unified_settings_state(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
        )
        width = 960
        panel_w = min(width - 40, 760)
        total_width = panel_w - 44

        for row_kind, label, row_key in settings_hub_model._UNIFIED_SETTINGS_ROWS:
            if row_kind != "item":
                continue
            if launcher_settings._slider_fraction_for_row(state, row_key) is None:
                continue
            value = launcher_settings._unified_value_text(state, row_key)
            with self.subTest(label=label):
                self._assert_slider_layout_fits(
                    font=fonts.menu_font,
                    label=label,
                    value=value,
                    total_width=total_width,
                )

    def test_setup_slider_rows_fit_compact_supported_width(self) -> None:
        fonts = self._fonts()
        settings = GameSettingsND()
        width = 960
        panel_w = min(
            width - 24,
            max(
                360,
                int(width * 0.65),
                min(menu_slider_row_min_total_width() + 76, width - 24),
            ),
        )
        total_width = panel_w - 48
        for label, attr_name, min_value, max_value in setup_fields_for_settings(4):
            if max_value <= min_value:
                continue
            value = getattr(settings, attr_name)
            if not isinstance(value, int):
                continue
            value_text = _menu_value_text(4, attr_name, value)
            with self.subTest(label=label):
                self._assert_slider_layout_fits(
                    font=fonts.menu_font,
                    label=label,
                    value=value_text,
                    total_width=total_width,
                )

    def test_inline_game_settings_slider_rows_fit_compact_supported_width(self) -> None:
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
        panel_w = min(
            width - 24,
            max(
                max(340, int(width * 0.6)),
                min(menu_slider_row_min_total_width() + 84, width - 24),
            ),
        )
        total_width = panel_w - 56
        for kind, label, row_key in settings_hub_model.settings_rows_for_category("gameplay"):
            if kind != "item":
                continue
            if launcher_settings._slider_fraction_for_row(state, row_key) is None:
                continue
            value = launcher_settings._unified_value_text(state, row_key)
            with self.subTest(label=label):
                self._assert_slider_layout_fits(
                    font=fonts.menu_font,
                    label=label,
                    value=value,
                    total_width=total_width,
                )

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
