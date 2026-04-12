from __future__ import annotations

from types import SimpleNamespace
import unittest

import pygame

from tet4d.engine.runtime.menu_config import menu_item_id, setup_fields_for_settings
from tet4d.ui.pygame.frontend_nd_setup import GameSettingsND, _menu_value_text
from tet4d.ui.pygame.launch import launcher_settings, settings_hub_model
from tet4d.ui.pygame.menu import keybindings_menu_view
from tet4d.ui.pygame.menu.keybindings_menu import KeybindingsMenuState
from tet4d.ui.pygame.menu.keybindings_menu_model import SECTION_MENU, rows_for_scope
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings
from tet4d.ui.pygame.ui_utils import (
    compute_slider_row_layout,
    compute_vertical_scroll_metrics,
    ensure_scroll_offset_visible,
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
        return SimpleNamespace(
            title_font=pygame.font.Font(None, 34),
            menu_font=pygame.font.Font(None, 26),
            panel_font=pygame.font.Font(None, 24),
            hint_font=pygame.font.Font(None, 20),
        )

    def _settings_slider_items(self):
        menu_ids = (
            "settings_audio",
            "settings_display",
            "settings_game_root",
            "settings_game_gameplay",
            "settings_game_movement_rotation",
            "settings_game_difficulty_pace",
            "settings_endgame_effects",
        )
        for menu_id in menu_ids:
            for item in settings_hub_model.settings_page_items(menu_id):
                if item["type"] == "slider":
                    yield menu_id, item

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
            + (layout.value_width + layout.text_gap if layout.value_width > 0 else 0)
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

        for _menu_id, item in self._settings_slider_items():
            row_key = menu_item_id(item)
            if launcher_settings._slider_fraction_for_row(state, row_key) is None:
                continue
            value = launcher_settings._unified_value_text(state, row_key)
            with self.subTest(label=item["label"]):
                self._assert_slider_layout_fits(
                    font=fonts.menu_font,
                    label=item["label"],
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

    def test_split_game_settings_slider_rows_fit_compact_supported_width(self) -> None:
        fonts = self._fonts()
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

        for menu_id in (
            "settings_game_gameplay",
            "settings_game_movement_rotation",
            "settings_game_difficulty_pace",
            "settings_endgame_effects",
        ):
            for item in settings_hub_model.settings_page_items(menu_id):
                if item["type"] != "slider":
                    continue
                row_key = menu_item_id(item)
                if launcher_settings._slider_fraction_for_row(state, row_key) is None:
                    continue
                value = launcher_settings._unified_value_text(state, row_key)
                with self.subTest(label=item["label"]):
                    self._assert_slider_layout_fits(
                        font=fonts.menu_font,
                        label=item["label"],
                        value=value,
                        total_width=total_width,
                    )

    def test_audio_page_rows_exclude_other_settings_sections(self) -> None:
        row_keys = {
            menu_item_id(item)
            for item in settings_hub_model.settings_page_items("settings_audio")
            if item["type"] != "section"
        }
        self.assertIn("audio_master", row_keys)
        self.assertIn("audio_sfx", row_keys)
        self.assertIn("audio_mute", row_keys)
        self.assertNotIn("display_fullscreen", row_keys)
        self.assertNotIn("game_seed", row_keys)
        self.assertTrue({"save", "reset", "back"}.issubset(row_keys))

    def test_game_settings_are_split_across_coherent_subpages(self) -> None:
        gameplay_keys = {
            menu_item_id(item)
            for item in settings_hub_model.settings_page_items("settings_game_gameplay")
            if item["type"] != "section"
        }
        game_root_keys = {
            menu_item_id(item)
            for item in settings_hub_model.settings_page_items("settings_game_root")
            if item["type"] != "section"
        }
        board_keys = {
            menu_item_id(item)
            for item in settings_hub_model.settings_page_items(
                "settings_game_board_geometry"
            )
            if item["type"] != "section"
        }
        movement_keys = {
            menu_item_id(item)
            for item in settings_hub_model.settings_page_items(
                "settings_game_movement_rotation"
            )
            if item["type"] != "section"
        }
        difficulty_keys = {
            menu_item_id(item)
            for item in settings_hub_model.settings_page_items(
                "settings_game_difficulty_pace"
            )
            if item["type"] != "section"
        }
        endgame_keys = {
            menu_item_id(item)
            for item in settings_hub_model.settings_page_items("settings_endgame_effects")
            if item["type"] != "section"
        }

        self.assertIn("game_seed", gameplay_keys)
        self.assertIn("game_random_mode", gameplay_keys)
        self.assertIn("display_overlay_transparency", game_root_keys)
        self.assertIn("game_topology_advanced", board_keys)
        self.assertIn("rotation_animation_mode", movement_keys)
        self.assertIn("kick_level_index", movement_keys)
        self.assertIn("lines_per_level", difficulty_keys)
        self.assertIn("endgame_preset_id", endgame_keys)
        self.assertIn("endgame_interaction_mode", endgame_keys)
        self.assertNotIn(
            "audio_master",
            gameplay_keys | game_root_keys | board_keys | movement_keys,
        )

    def test_overflow_metrics_hide_scrollbar_when_content_fits(self) -> None:
        metrics = compute_vertical_scroll_metrics(
            viewport_rect=pygame.Rect(10, 10, 320, 240),
            content_height=180,
            scroll_offset=0,
        )
        self.assertFalse(metrics.shows_scrollbar)
        self.assertEqual(metrics.reserved_width, 0)

    def test_overflow_metrics_show_scrollbar_when_content_exceeds_viewport(self) -> None:
        metrics = compute_vertical_scroll_metrics(
            viewport_rect=pygame.Rect(10, 10, 320, 180),
            content_height=520,
            scroll_offset=40,
        )
        self.assertTrue(metrics.shows_scrollbar)
        self.assertGreater(metrics.reserved_width, 0)
        self.assertGreater(metrics.track_rect.height, metrics.handle_rect.height)

    def test_selected_row_visibility_updates_scroll_offset(self) -> None:
        adjusted = ensure_scroll_offset_visible(
            0,
            item_top=220,
            item_bottom=280,
            viewport_height=160,
            content_height=520,
        )
        self.assertGreater(adjusted, 0)

    def test_settings_menu_auto_scroll_keeps_selection_visible(self) -> None:
        fonts = self._fonts()
        state = settings_hub_model.build_unified_settings_state(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
            initial_page_id="settings_game_movement_rotation",
            initial_item_id="back",
        )
        screen = pygame.Surface((640, 360), pygame.SRCALPHA)
        launcher_settings._draw_unified_settings_menu(screen, fonts, state)
        self.assertGreater(state.scroll_offset, 0)

    def test_keybindings_menu_uses_shared_overflow_scroll(self) -> None:
        fonts = self._fonts()
        state = KeybindingsMenuState(scope="all", section_mode=False)
        rendered_rows, binding_rows = rows_for_scope("all")
        state.selected_binding = max(0, len(binding_rows) - 1)
        screen = pygame.Surface((640, 360), pygame.SRCALPHA)
        keybindings_menu_view.draw_binding_menu(
            screen,
            fonts,
            state,
            rendered_rows=rendered_rows,
            binding_rows=binding_rows,
            scope_label_fn=lambda scope: scope,
            scope_file_hint_fn=lambda _scope: "",
            text_mode_label_fn=lambda mode: mode,
        )
        self.assertGreater(state.scroll_offset, 0)

    def test_keybindings_section_menu_uses_shared_overflow_scroll(self) -> None:
        fonts = self._fonts()
        state = KeybindingsMenuState(section_mode=True)
        state.selected_section = len(SECTION_MENU) - 1
        screen = pygame.Surface((640, 360), pygame.SRCALPHA)
        keybindings_menu_view.draw_section_menu(
            screen,
            fonts,
            state,
            section_menu=SECTION_MENU,
            scope_label_fn=lambda scope: scope,
            text_mode_label_fn=lambda mode: mode,
        )
        self.assertGreaterEqual(state.scroll_offset, 0)
