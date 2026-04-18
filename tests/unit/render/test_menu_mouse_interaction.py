from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from tet4d.ui.pygame.launch import leaderboard_menu
from tet4d.ui.pygame.launch import launcher_settings, settings_hub_model
from tet4d.ui.pygame.menu import menu_runner
from tet4d.ui.pygame.menu.menu_runner import ActionRegistry, MenuRunner
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings
from tet4d.ui.pygame.runtime_ui import pause_menu


class TestMenuMouseInteraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def _fonts(self):
        return SimpleNamespace(
            title_font=pygame.font.Font(None, 34),
            menu_font=pygame.font.Font(None, 26),
            hint_font=pygame.font.Font(None, 20),
        )

    def test_menu_runner_click_uses_pointer_target_not_keyboard_selection(self) -> None:
        menus = {
            "root": {
                "title": "Root",
                "items": (
                    {"type": "action", "label": "First", "action_id": "first"},
                    {"type": "action", "label": "Second", "action_id": "second"},
                ),
            }
        }
        registry = ActionRegistry()
        calls = {"first": 0, "second": 0}
        registry.register(
            "first",
            lambda: calls.__setitem__("first", calls["first"] + 1) or False,
        )
        registry.register(
            "second",
            lambda: calls.__setitem__("second", calls["second"] + 1) or True,
        )

        def _render_menu(
            _menu_id,
            _title,
            _items,
            _selected,
            _depth,
            _selected_action_indexes,
            _hovered_target,
            _pressed_target,
        ):
            return (
                menu_runner.MenuPointerTarget(
                    kind="item",
                    rect=pygame.Rect(30, 40, 180, 32),
                    item_index=0,
                ),
                menu_runner.MenuPointerTarget(
                    kind="item",
                    rect=pygame.Rect(30, 84, 180, 32),
                    item_index=1,
                ),
            )

        runner = MenuRunner(
            menus=menus,
            start_menu_id="root",
            action_registry=registry,
            render_menu=_render_menu,
            initial_selected={"root": 0},
        )

        with patch.object(
            pygame.event,
            "get",
            return_value=[
                pygame.event.Event(pygame.MOUSEMOTION, {"pos": (40, 92)}),
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (40, 92)}),
                pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (40, 92)}),
            ],
        ):
            runner.run()

        self.assertEqual(calls["first"], 0)
        self.assertEqual(calls["second"], 1)

    def test_menu_runner_release_outside_pressed_item_cancels_activation(self) -> None:
        menus = {
            "root": {
                "title": "Root",
                "items": (
                    {"type": "action", "label": "Only", "action_id": "only"},
                ),
            }
        }
        registry = ActionRegistry()
        calls = {"only": 0, "root_escape": 0}
        registry.register(
            "only",
            lambda: calls.__setitem__("only", calls["only"] + 1) or False,
        )

        def _render_menu(
            _menu_id,
            _title,
            _items,
            _selected,
            _depth,
            _selected_action_indexes,
            _hovered_target,
            _pressed_target,
        ):
            return (
                menu_runner.MenuPointerTarget(
                    kind="item",
                    rect=pygame.Rect(30, 40, 180, 32),
                    item_index=0,
                ),
            )

        runner = MenuRunner(
            menus=menus,
            start_menu_id="root",
            action_registry=registry,
            render_menu=_render_menu,
            on_root_escape=lambda: calls.__setitem__("root_escape", calls["root_escape"] + 1)
            or True,
        )

        with patch.object(
            pygame.event,
            "get",
            side_effect=[
                [
                    pygame.event.Event(pygame.MOUSEMOTION, {"pos": (40, 48)}),
                    pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (40, 48)}),
                    pygame.event.Event(pygame.MOUSEMOTION, {"pos": (260, 160)}),
                    pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (260, 160)}),
                ],
                [pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})],
            ],
        ):
            runner.run()

        self.assertEqual(calls["only"], 0)
        self.assertEqual(calls["root_escape"], 1)

    def test_pause_menu_mouse_click_activates_hovered_row(self) -> None:
        fonts = self._fonts()
        screen = pygame.Surface((960, 640))
        preview_state = pause_menu._PauseState(
            selected=pause_menu._PAUSE_ACTION_CODES.index("leaderboard")
        )
        targets = pause_menu._draw_pause_menu(
            screen,
            fonts,
            preview_state,
            dimension=3,
            title="Pause Menu",
        )
        leaderboard_target = next(
            target
            for target in targets
            if target.kind == "item"
            and target.item_index == pause_menu._PAUSE_ACTION_CODES.index("leaderboard")
        )

        with (
            patch(
                "tet4d.ui.pygame.runtime_ui.pause_menu.run_leaderboard_menu",
                return_value=screen,
            ) as run_lb,
            patch.object(
                pygame.event,
                "get",
                side_effect=[
                    [
                        pygame.event.Event(
                            pygame.MOUSEMOTION,
                            {"pos": leaderboard_target.rect.center},
                        ),
                        pygame.event.Event(
                            pygame.MOUSEBUTTONDOWN,
                            {"button": 1, "pos": leaderboard_target.rect.center},
                        ),
                        pygame.event.Event(
                            pygame.MOUSEBUTTONUP,
                            {"button": 1, "pos": leaderboard_target.rect.center},
                        ),
                    ],
                    [pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})],
                ],
            ),
            patch.object(pygame.display, "flip", return_value=None),
        ):
            decision, out_screen = pause_menu.run_pause_menu(
                screen,
                fonts,
                dimension=3,
            )

        self.assertEqual(decision, "resume")
        self.assertIs(out_screen, screen)
        run_lb.assert_called_once()

    def test_settings_hub_mouse_click_activates_hovered_row(self) -> None:
        fonts = self._fonts()
        screen = pygame.Surface((960, 640))
        preview_state = settings_hub_model.build_unified_settings_state(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
            initial_page_id="settings_game_root",
            initial_item_id="save",
        )
        launcher_settings._draw_unified_settings_menu(screen, fonts, preview_state)
        selectable_index_by_item = settings_hub_model.selectable_index_by_item_id_for_items(
            launcher_settings._current_items(preview_state)
        )
        target_selectable_index = selectable_index_by_item["save"]
        targets = launcher_settings._current_unified_pointer_targets(
            screen,
            fonts,
            preview_state,
        )
        save_target = next(
            target
            for target in targets
            if target.kind == "item"
            and target.selectable_index == target_selectable_index
        )

        with (
            patch.object(
                pygame.event,
                "get",
                side_effect=[
                    [
                        pygame.event.Event(
                            pygame.MOUSEMOTION,
                            {"pos": save_target.rect.center},
                        ),
                        pygame.event.Event(
                            pygame.MOUSEBUTTONDOWN,
                            {"button": 1, "pos": save_target.rect.center},
                        ),
                        pygame.event.Event(
                            pygame.MOUSEBUTTONUP,
                            {"button": 1, "pos": save_target.rect.center},
                        ),
                    ],
                    [pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})],
                    [pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})],
                ],
            ),
            patch.object(
                launcher_settings,
                "_save_unified_settings",
                side_effect=lambda current_screen, _state: current_screen,
            ) as save_settings,
            patch.object(pygame.display, "flip", return_value=None),
        ):
            result = launcher_settings.run_settings_hub_menu(
                screen,
                fonts,
                audio_settings=AudioSettings(),
                display_settings=DisplaySettings(),
                initial_page_id="settings_game_root",
                initial_item_id="save",
            )

        self.assertTrue(result.keep_running)
        save_settings.assert_called_once()

    def test_name_prompt_mouse_hover_tracks_button_hitbox(self) -> None:
        fonts = self._fonts()
        screen = pygame.Surface((960, 640))
        state = leaderboard_menu._NamePromptState(name="Player")
        layout = leaderboard_menu._name_prompt_layout(screen, fonts)

        leaderboard_menu._handle_name_prompt_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": layout.submit_rect.center},
            ),
            state,
            layout=layout,
        )

        self.assertEqual(state.hovered_button, "submit")

    def test_name_prompt_submit_button_click_accepts_name(self) -> None:
        fonts = self._fonts()
        screen = pygame.Surface((960, 640))
        layout = leaderboard_menu._name_prompt_layout(screen, fonts)

        with (
            patch.object(
                pygame.event,
                "get",
                return_value=[
                    pygame.event.Event(
                        pygame.MOUSEMOTION,
                        {"pos": layout.submit_rect.center},
                    ),
                    pygame.event.Event(
                        pygame.MOUSEBUTTONDOWN,
                        {"button": 1, "pos": layout.submit_rect.center},
                    ),
                    pygame.event.Event(
                        pygame.MOUSEBUTTONUP,
                        {"button": 1, "pos": layout.submit_rect.center},
                    ),
                ],
            ),
            patch.object(pygame.display, "flip", return_value=None),
        ):
            name = leaderboard_menu.prompt_leaderboard_player_name(
                screen,
                fonts,
                rank=3,
            )

        self.assertEqual(name, "Player")

    def test_name_prompt_cancel_button_click_returns_none(self) -> None:
        fonts = self._fonts()
        screen = pygame.Surface((960, 640))
        layout = leaderboard_menu._name_prompt_layout(screen, fonts)

        with (
            patch.object(
                pygame.event,
                "get",
                return_value=[
                    pygame.event.Event(
                        pygame.MOUSEMOTION,
                        {"pos": layout.cancel_rect.center},
                    ),
                    pygame.event.Event(
                        pygame.MOUSEBUTTONDOWN,
                        {"button": 1, "pos": layout.cancel_rect.center},
                    ),
                    pygame.event.Event(
                        pygame.MOUSEBUTTONUP,
                        {"button": 1, "pos": layout.cancel_rect.center},
                    ),
                ],
            ),
            patch.object(pygame.display, "flip", return_value=None),
        ):
            name = leaderboard_menu.prompt_leaderboard_player_name(
                screen,
                fonts,
                rank=3,
            )

        self.assertIsNone(name)

    def test_leaderboard_back_chip_click_exits_menu(self) -> None:
        fonts = self._fonts()
        screen = pygame.Surface((960, 640))
        layout = leaderboard_menu._LeaderboardLayout(
            back_rect=pygame.Rect(
                18,
                18,
                fonts.hint_font.size("Back")[0] + 18,
                fonts.hint_font.get_height() + 10,
            )
        )

        with (
            patch.object(
                pygame.event,
                "get",
                return_value=[
                    pygame.event.Event(
                        pygame.MOUSEMOTION,
                        {"pos": layout.back_rect.center},
                    ),
                    pygame.event.Event(
                        pygame.MOUSEBUTTONDOWN,
                        {"button": 1, "pos": layout.back_rect.center},
                    ),
                    pygame.event.Event(
                        pygame.MOUSEBUTTONUP,
                        {"button": 1, "pos": layout.back_rect.center},
                    ),
                ],
            ),
            patch.object(
                leaderboard_menu,
                "leaderboard_top_entries",
                return_value=(),
            ),
            patch.object(pygame.display, "flip", return_value=None),
        ):
            out_screen = leaderboard_menu.run_leaderboard_menu(screen, fonts)

        self.assertIs(out_screen, screen)
