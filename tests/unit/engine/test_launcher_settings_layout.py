from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest import mock

import pygame

from tet4d.engine.runtime.menu_config import menu_item_id, setup_fields_for_settings
from tet4d.ui.pygame.frontend_nd_setup import GameSettingsND, _menu_value_text
from tet4d.ui.pygame.launch import (
    bot_options_menu,
    launcher_menu_view,
    launcher_settings,
    leaderboard_menu,
    settings_hub_model,
)
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
            "settings_gameplay",
            "settings_endgame_gameplay",
            "settings_explosion_defaults_2d",
            "settings_explosion_defaults_3d",
            "settings_explosion_defaults_4d",
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
        for field in setup_fields_for_settings(4):
            if not field.uses_slider():
                continue
            value = getattr(settings, field.attr_name)
            value_text = _menu_value_text(field, value)
            with self.subTest(label=field.label):
                self._assert_slider_layout_fits(
                    font=fonts.menu_font,
                    label=field.label,
                    value=value_text,
                    total_width=total_width,
                )

    def test_setup_enum_rows_use_selector_controls_not_sliders(self) -> None:
        fields = {field.attr_name: field for field in setup_fields_for_settings(4)}
        self.assertEqual(fields["piece_set_index"].semantic_type, "enum")
        self.assertEqual(fields["piece_set_index"].control_family, "selector")
        self.assertFalse(fields["piece_set_index"].uses_slider())
        self.assertEqual(fields["topology_mode"].semantic_type, "enum")
        self.assertEqual(fields["topology_mode"].control_family, "selector")
        self.assertFalse(fields["topology_mode"].uses_slider())

    def test_setup_discrete_numeric_rows_prefer_steppers(self) -> None:
        fields = {field.attr_name: field for field in setup_fields_for_settings(4)}
        self.assertEqual(fields["width"].control_family, "stepper")
        self.assertEqual(fields["height"].control_family, "stepper")
        self.assertEqual(fields["depth"].control_family, "stepper")
        self.assertEqual(fields["fourth"].control_family, "stepper")
        self.assertEqual(fields["challenge_layers"].control_family, "stepper")
        self.assertEqual(fields["speed_level"].control_family, "slider")

    def test_gameplay_slider_rows_fit_compact_supported_width(self) -> None:
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

        for item in settings_hub_model.settings_page_items("settings_gameplay"):
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

    def test_settings_pages_split_gameplay_from_setup_and_endgame(self) -> None:
        gameplay_keys = {
            menu_item_id(item)
            for item in settings_hub_model.settings_page_items("settings_gameplay")
            if item["type"] != "section"
        }
        self.assertTrue(
            {
                "game_seed",
                "game_random_mode",
                "analytics_score_logging",
                "rotation_animation_mode",
                "kick_level_index",
                "rotation_animation_duration_ms_2d",
                "rotation_animation_duration_ms_nd",
                "translation_animation_duration_ms",
                "auto_speedup_enabled",
                "lines_per_level",
                "save",
                "reset",
                "back",
            }.issubset(gameplay_keys)
        )
        self.assertNotIn("audio_master", gameplay_keys)
        self.assertNotIn("display_fullscreen", gameplay_keys)
        self.assertNotIn("endgame_preset_id", gameplay_keys)
        self.assertNotIn("game_topology_advanced", gameplay_keys)

        board_defaults_keys = {
            menu_item_id(item)
            for item in settings_hub_model.settings_page_items("settings_board_setup_defaults")
            if item["type"] != "section"
        }
        self.assertTrue(
            {
                "game_topology_advanced",
                "topology_cache_measure",
                "topology_cache_clear",
                "settings_legacy_topology_editor",
                "save",
                "reset",
                "back",
            }.issubset(board_defaults_keys)
        )
        self.assertNotIn("game_seed", board_defaults_keys)
        self.assertNotIn("endgame_preset_id", board_defaults_keys)

        endgame_keys = {
            menu_item_id(item)
            for item in settings_hub_model.settings_page_items("settings_endgame_gameplay")
            if item["type"] != "section"
        }
        self.assertTrue(
            {
                "endgame_preset_id",
                "endgame_boundary_response",
                "endgame_particle_collisions",
                "endgame_relic_speed_percent",
                "endgame_shatter_speed_percent",
                "save",
                "reset",
                "back",
            }.issubset(endgame_keys)
        )
        self.assertNotIn("audio_master", endgame_keys)
        self.assertNotIn("game_seed", endgame_keys)

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
            initial_page_id="settings_explosion_defaults_4d",
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

    def test_keybindings_binding_rows_use_menu_font_metrics(self) -> None:
        fonts = self._fonts()
        state = KeybindingsMenuState(scope="all", section_mode=False)
        rendered_rows, binding_rows = rows_for_scope("all")
        state.selected_binding = max(0, len(binding_rows) - 1)
        screen = pygame.Surface((640, 360), pygame.SRCALPHA)
        panel_rect = keybindings_menu_view._panel_geometry(screen)
        viewport_rect = pygame.Rect(
            panel_rect.x + 16,
            panel_rect.y + 12,
            panel_rect.width - 32,
            panel_rect.height - 20,
        )
        row_h = fonts.menu_font.get_height() + fonts.hint_font.get_height() + 12
        selected_render_index = keybindings_menu_view._selected_render_index(
            state,
            rendered_rows,
            binding_rows,
        )
        expected = ensure_scroll_offset_visible(
            0,
            item_top=selected_render_index * row_h,
            item_bottom=((selected_render_index + 1) * row_h),
            viewport_height=viewport_rect.height,
            content_height=len(rendered_rows) * row_h,
        )
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
        self.assertEqual(state.scroll_offset, expected)

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

    def test_bot_options_menu_uses_shared_shell_and_overflow_scroll(self) -> None:
        fonts = self._fonts()
        screen = pygame.Surface((640, 360), pygame.SRCALPHA)
        loop = bot_options_menu._BotMenuState(payload={}, selected=8)
        with (
            mock.patch.object(
                bot_options_menu,
                "draw_tron_panel",
                wraps=bot_options_menu.draw_tron_panel,
            ) as draw_panel,
            mock.patch.object(
                bot_options_menu,
                "draw_corner_chip",
                wraps=bot_options_menu.draw_corner_chip,
            ) as draw_chip,
        ):
            bot_options_menu._draw_bot_options_menu(screen, fonts, loop)
        draw_panel.assert_called_once()
        draw_chip.assert_called_once()
        self.assertGreater(loop.scroll_offset, 0)

    def test_leaderboard_menu_uses_shared_shell_primitives(self) -> None:
        fonts = self._fonts()
        screen = pygame.Surface((960, 640), pygame.SRCALPHA)
        with (
            mock.patch.object(
                leaderboard_menu,
                "draw_tron_panel",
                wraps=leaderboard_menu.draw_tron_panel,
            ) as draw_panel,
            mock.patch.object(
                leaderboard_menu,
                "draw_corner_chip",
                wraps=leaderboard_menu.draw_corner_chip,
            ) as draw_chip,
        ):
            leaderboard_menu._draw_leaderboard(
                screen,
                fonts,
                leaderboard_menu._LeaderboardState(),
                (),
            )
        draw_panel.assert_called_once()
        draw_chip.assert_called_once()

    def test_launcher_menu_falls_back_when_action_group_hint_copy_is_missing(self) -> None:
        fonts = self._fonts()
        screen = pygame.Surface((960, 640), pygame.SRCALPHA)
        items = (
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
        )
        launcher_copy = {
            "info_active_profile_template": "Active key profile: {profile}",
            "info_continue_mode_template": "Continue mode: {mode}",
            "controls_hint_template": "Up/Down select   Enter open   {escape_hint}",
            "controls_hint_template_tiny": "I/K select   Enter open   {escape_hint}",
            "escape_hint_back": "Backspace back",
            "escape_hint_quit": "Esc exit",
        }
        with mock.patch.object(
            launcher_menu_view,
            "active_key_profile",
            return_value="default",
        ):
            launcher_menu_view.draw_main_menu(
                screen,
                fonts,
                menu_title="Choose Mode",
                items=items,
                selected_index=0,
                selected_action_indexes={"play_2d_row": 0},
                stack_depth=2,
                status="",
                status_error=False,
                last_mode="2d",
                launcher_copy=launcher_copy,
                signature_author="author",
                signature_message="message",
                bg_top=(0, 0, 0),
                bg_bottom=(0, 0, 0),
                text_color=(255, 255, 255),
                highlight_color=(255, 224, 128),
                muted_color=(192, 200, 228),
            )

    def test_settings_hub_escape_cancels_numeric_text_mode(self) -> None:
        state = settings_hub_model.build_unified_settings_state(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
            initial_page_id="settings_display",
        )
        launcher_settings._start_unified_numeric_text_mode(state, "display_width")
        self.assertTrue(state.text_mode_row_key)
        self.assertTrue(state.text_mode_buffer)

        screen = pygame.Surface((640, 480))
        out = launcher_settings._dispatch_unified_text_mode_key(screen, state, pygame.K_ESCAPE)
        self.assertIs(out, screen)
        self.assertEqual(state.text_mode_row_key, "")

    def test_settings_hub_backspace_in_numeric_text_mode_edits_buffer_not_navigation(self) -> None:
        state = settings_hub_model.build_unified_settings_state(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
            initial_page_id="settings_root",
        )
        launcher_settings._push_page(state, "settings_display")
        launcher_settings._start_unified_numeric_text_mode(state, "display_width")
        self.assertTrue(state.text_mode_row_key)
        original_stack_depth = len(state.page_stack)
        original_buffer = state.text_mode_buffer
        self.assertGreater(len(original_buffer), 1)

        screen = pygame.Surface((640, 480))
        out = launcher_settings._dispatch_unified_key(screen, self._fonts(), state, pygame.K_BACKSPACE)
        self.assertIs(out, screen)
        self.assertEqual(len(state.page_stack), original_stack_depth)
        self.assertTrue(state.running)
        self.assertEqual(state.text_mode_buffer, original_buffer[:-1])

    def test_settings_hub_q_does_not_exit_application_loop_even_in_numeric_text_mode(self) -> None:
        state = settings_hub_model.build_unified_settings_state(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
            initial_page_id="settings_display",
        )
        launcher_settings._start_unified_numeric_text_mode(state, "display_width")
        self.assertTrue(state.text_mode_row_key)

        screen = pygame.Surface((640, 480))
        out = launcher_settings._dispatch_unified_key(screen, self._fonts(), state, pygame.K_q)
        self.assertIs(out, screen)
        self.assertTrue(state.running)
        self.assertTrue(state.keep_running)
        self.assertEqual(state.text_mode_row_key, "display_width")

    def test_settings_hub_backspace_pops_page_stack_but_escape_does_not(self) -> None:
        state = settings_hub_model.build_unified_settings_state(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
            initial_page_id="settings_root",
        )
        launcher_settings._push_page(state, "settings_gameplay")
        self.assertEqual(len(state.page_stack), 2)

        screen = pygame.Surface((640, 480))
        out = launcher_settings._handle_unified_navigation_key(
            screen,
            state,
            key=pygame.K_ESCAPE,
            selectable_count=1,
        )
        self.assertIs(out, screen)
        self.assertEqual(len(state.page_stack), 2)

        out = launcher_settings._handle_unified_navigation_key(
            screen,
            state,
            key=pygame.K_BACKSPACE,
            selectable_count=1,
        )
        self.assertIs(out, screen)
        self.assertEqual(len(state.page_stack), 1)
