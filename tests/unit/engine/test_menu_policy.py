from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest import mock

from tet4d.ui.pygame.launch import settings_hub_actions, settings_hub_model
from tet4d.engine.runtime import menu_config
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings


class TestMenuPolicy(unittest.TestCase):
    def test_settings_split_metrics_cover_documented_categories(self) -> None:
        docs = menu_config.settings_category_docs()
        metrics = menu_config.settings_category_metrics()
        documented_ids = {entry["id"] for entry in docs}
        self.assertTrue(documented_ids)
        self.assertTrue(set(metrics).issubset(documented_ids))

    def test_top_level_categories_match_hub_rows(self) -> None:
        top_level = menu_config.settings_top_level_categories()
        hub_rows = set(menu_config.settings_hub_rows())
        for entry in top_level:
            self.assertIn(entry["label"], hub_rows)

    def test_launcher_settings_layout_matches_policy(self) -> None:
        ok, message = settings_hub_model._validate_unified_layout_against_policy()
        self.assertTrue(ok, message)

    def test_settings_hub_layout_rows_include_item_and_headers(self) -> None:
        rows = menu_config.settings_hub_layout_rows()
        self.assertTrue(rows)
        kinds = {kind for kind, _label, _row_key in rows}
        self.assertIn("header", kinds)
        self.assertIn("item", kinds)
        self.assertTrue(
            any(row_key == "save" for kind, _label, row_key in rows if kind == "item")
        )
        self.assertTrue(
            any(row_key == "reset" for kind, _label, row_key in rows if kind == "item")
        )
        self.assertTrue(
            any(
                row_key == "game_seed"
                for kind, _label, row_key in rows
                if kind == "item"
            )
        )
        self.assertTrue(
            any(
                row_key == "game_random_mode"
                for kind, _label, row_key in rows
                if kind == "item"
            )
        )
        self.assertFalse(
            any(
                row_key == "game_topology_advanced"
                for kind, _label, row_key in rows
                if kind == "item"
            )
        )
        self.assertTrue(
            any(
                row_key == "gameplay_advanced"
                for kind, _label, row_key in rows
                if kind == "item"
            )
        )

    def test_settings_hub_headers_align_with_top_level_categories(self) -> None:
        top_level = menu_config.settings_top_level_categories()
        expected = {entry["label"] for entry in top_level}
        headers = {
            label
            for kind, label, _row_key in menu_config.settings_hub_layout_rows()
            if kind == "header"
        }
        self.assertTrue(expected.issubset(headers))

    def test_setup_fields_include_only_safe_topology_preset_controls(self) -> None:
        for dimension in (2, 3, 4):
            fields = menu_config.setup_fields_for_dimension(dimension, piece_set_max=5)
            attrs = {attr for _label, attr, _min_val, _max_val in fields}
            self.assertIn("topology_mode", attrs)
            self.assertNotIn("topology_profile_index", attrs)
            self.assertNotIn("exploration_mode", attrs)
            self.assertNotIn("topology_advanced", attrs)
            self.assertNotIn("random_mode_index", attrs)
            self.assertNotIn("game_seed", attrs)

    def test_explorer_setup_fields_hide_topology_editor_rows(self) -> None:
        for dimension in (2, 3, 4):
            fields = menu_config.setup_fields_for_settings(
                dimension,
                piece_set_max=5,
                topology_profile_max=5,
                topology_advanced=True,
                exploration_mode=True,
            )
            attrs = {attr for _label, attr, _min_val, _max_val in fields}
            self.assertNotIn("topology_mode", attrs)
            self.assertNotIn("topology_advanced", attrs)
            self.assertNotIn("topology_profile_index", attrs)
            self.assertNotIn("exploration_mode", attrs)

    def test_setup_hints_defined_for_all_dimensions(self) -> None:
        for dimension in (2, 3, 4):
            hints = menu_config.setup_hints_for_dimension(dimension)
            self.assertTrue(hints)
            self.assertTrue(all(isinstance(line, str) and line for line in hints))

    def test_launcher_pause_entrypoint_parity(self) -> None:
        launcher_actions = set(
            menu_config.reachable_action_ids(menu_config.launcher_menu_id())
        )
        pause_actions = set(
            menu_config.reachable_action_ids(menu_config.pause_menu_id())
        )
        required = {"settings", "keybindings", "help", "bot_options", "quit"}
        required.add("leaderboard")
        self.assertTrue(required.issubset(launcher_actions))
        self.assertTrue(required.issubset(pause_actions))

    def test_pause_rows_and_actions_stay_in_sync(self) -> None:
        self.assertEqual(
            len(menu_config.pause_menu_rows()),
            len(menu_config.pause_menu_actions()),
        )

    def test_pause_copy_is_config_driven(self) -> None:
        pause_copy = menu_config.pause_copy()
        self.assertIn("subtitle_template", pause_copy)
        self.assertIn("{dimension}", pause_copy["subtitle_template"])
        self.assertTrue(pause_copy["hints"])
        self.assertTrue(
            all(isinstance(line, str) and line for line in pause_copy["hints"])
        )

    def test_launcher_rehaul_actions_include_play_and_continue(self) -> None:
        launcher_actions = {
            action for action, _label in menu_config.launcher_menu_items()
        }
        self.assertIn("play", launcher_actions)
        self.assertIn("continue", launcher_actions)

    def test_pause_menu_rehaul_core_actions(self) -> None:
        pause_actions = set(menu_config.pause_menu_actions())
        expected = {
            "resume",
            "restart",
            "settings",
            "keybindings",
            "help",
            "leaderboard",
            "bot_options",
            "menu",
            "quit",
        }
        self.assertTrue(expected.issubset(pause_actions))

    def test_menu_graph_root_labels_preserve_top_level_ia(self) -> None:
        root_items = menu_config.menu_items(menu_config.launcher_menu_id())
        labels = [item["label"] for item in root_items]
        self.assertEqual(
            labels,
            [
                "Play",
                "Continue",
                "Tutorials",
                "Settings",
                "Controls",
                "Help",
                "Leaderboard",
                "Bot",
                "Quit",
            ],
        )

    def test_play_menu_is_graph_defined(self) -> None:
        root_items = menu_config.menu_items(menu_config.launcher_menu_id())
        play_links = [
            item
            for item in root_items
            if item["type"] == "submenu" and item["label"] == "Play"
        ]
        self.assertEqual(len(play_links), 1)
        play_menu_id = play_links[0]["menu_id"]

        play_items = menu_config.menu_items(play_menu_id)
        play_actions = {
            item["action_id"] for item in play_items if item["type"] == "action"
        }
        self.assertTrue(
            {"play_2d", "play_3d", "play_4d", "play_last_custom_topology", "topology_lab"}.issubset(play_actions)
        )

    def test_play_menu_is_minimal_launcher(self) -> None:
        launcher_play = menu_config.menu_definition("launcher_play")
        detached_item = next(
            item for item in launcher_play["items"] if item.get("action_id") == "topology_lab"
        )
        self.assertEqual(detached_item["label"], "Open Explorer Playground")
        self.assertIn("Minimal play launcher", menu_config.launcher_subtitles()["launcher_play"])
        self.assertIn(
            "play_last_custom_topology",
            {item["action_id"] for item in launcher_play["items"] if item["type"] == "action"},
        )

    def test_launcher_route_actions_cover_launcher_routes(self) -> None:
        pending = [menu_config.launcher_menu_id()]
        seen: set[str] = set()
        route_ids: set[str] = set()
        while pending:
            menu_id = pending.pop()
            if menu_id in seen:
                continue
            seen.add(menu_id)
            for item in menu_config.menu_items(menu_id):
                if item["type"] == "route":
                    route_ids.add(item["route_id"])
                if item["type"] == "submenu":
                    pending.append(item["menu_id"])
        route_actions = menu_config.launcher_route_actions()
        self.assertEqual(route_ids, set(route_actions))
        launcher_actions = set(
            menu_config.reachable_action_ids(menu_config.launcher_menu_id())
        )
        self.assertTrue(set(route_actions.values()).issubset(launcher_actions))

    def test_launcher_subtitles_are_config_driven(self) -> None:
        subtitles = menu_config.launcher_subtitles()
        self.assertIn("launcher_root", subtitles)
        self.assertIn("launcher_play", subtitles)
        self.assertIn("default", subtitles)
        self.assertTrue(
            all(isinstance(text, str) and text for text in subtitles.values())
        )

    def test_branding_copy_is_config_driven(self) -> None:
        branding = menu_config.branding_copy()
        self.assertIn("game_title", branding)
        self.assertIn("signature_author", branding)
        self.assertIn("signature_message", branding)
        self.assertTrue(
            all(isinstance(text, str) and text for text in branding.values())
        )

    def test_ui_copy_sections_are_config_driven(self) -> None:
        ui_copy = menu_config.ui_copy_payload()
        self.assertTrue(isinstance(ui_copy, dict))
        required_sections = (
            "launcher",
            "settings_hub",
            "keybindings_menu",
            "bot_options",
            "setup_menu",
        )
        for section in required_sections:
            payload = menu_config.ui_copy_section(section)
            self.assertIn(section, ui_copy)
            self.assertTrue(isinstance(payload, dict))
            self.assertTrue(payload)

    def test_settings_option_labels_require_random_mode_labels(self) -> None:
        labels = menu_config.settings_option_labels()
        self.assertIn("game_random_mode", labels)
        self.assertGreaterEqual(len(labels["game_random_mode"]), 2)
        self.assertIn("game_kick_level", labels)
        self.assertGreaterEqual(len(labels["game_kick_level"]), 2)
        self.assertIn("game_rotation_animation_mode", labels)
        self.assertEqual(len(labels["game_rotation_animation_mode"]), 2)

    def test_build_unified_settings_state_uses_persisted_analytics_state(self) -> None:
        with (
            mock.patch.object(
                settings_hub_model,
                "get_analytics_settings",
                return_value={"score_logging_enabled": True},
            ),
            mock.patch.object(
                settings_hub_model,
                "default_analytics_settings",
                return_value={"score_logging_enabled": False},
            ),
        ):
            state = settings_hub_model.build_unified_settings_state(
                audio_settings=AudioSettings(),
                display_settings=DisplaySettings(),
            )

        self.assertTrue(state.score_logging_enabled)
        self.assertTrue(state.original_score_logging_enabled)

    def test_reset_unified_settings_restores_analytics_defaults(self) -> None:
        with (
            mock.patch.object(
                settings_hub_model,
                "get_analytics_settings",
                return_value={"score_logging_enabled": True},
            ),
            mock.patch.object(
                settings_hub_model,
                "default_analytics_settings",
                return_value={"score_logging_enabled": False},
            ),
        ):
            state = settings_hub_model.build_unified_settings_state(
                audio_settings=AudioSettings(),
                display_settings=DisplaySettings(),
            )

        screen = object()
        with (
            mock.patch.object(settings_hub_actions, "_audio_defaults", return_value=AudioSettings()),
            mock.patch.object(settings_hub_actions, "_display_defaults", return_value=DisplaySettings()),
            mock.patch.object(
                settings_hub_actions,
                "default_display_settings",
                return_value={"overlay_transparency": 0.25},
            ),
            mock.patch.object(settings_hub_actions, "_analytics_defaults", return_value=False),
            mock.patch.object(settings_hub_actions, "_sync_audio_preview"),
            mock.patch.object(settings_hub_actions, "_sync_analytics_preview"),
            mock.patch.object(settings_hub_actions, "apply_display_mode", return_value=screen),
            mock.patch.object(settings_hub_actions, "play_sfx"),
        ):
            returned = settings_hub_actions._reset_unified_settings(screen, state)

        self.assertIs(returned, screen)
        self.assertFalse(state.score_logging_enabled)

    def test_unified_settings_manual_numeric_edit_applies_large_values(self) -> None:
        state = SimpleNamespace(
            display_settings=DisplaySettings(
                fullscreen=False,
                windowed_size=(1200, 760),
            ),
            game_seed=1337,
            text_mode_row_key="display_width",
            text_mode_buffer="10000",
            text_mode_replace_on_type=False,
            saved=True,
            status="",
            status_error=False,
            pending_reset_confirm=False,
        )
        self.assertTrue(settings_hub_actions._apply_unified_numeric_text_value(state))
        self.assertEqual(state.display_settings.windowed_size[0], 10000)

    def test_unified_gameplay_summary_includes_animation_durations(self) -> None:
        state = SimpleNamespace(
            rotation_animation_mode="rigid_piece_rotation",
            kick_level_index=2,
            auto_speedup_enabled=1,
            lines_per_level=14,
            rotation_animation_duration_ms_2d=300,
            rotation_animation_duration_ms_nd=340,
            translation_animation_duration_ms=120,
            text_mode_row_key="",
            text_mode_buffer="",
        )
        summary = settings_hub_model._unified_value_text(state, "gameplay_advanced")
        self.assertIn("Rigid piece rotation", summary)
        self.assertIn("Standard", summary)
        self.assertIn("rot2d 300 ms", summary)
        self.assertIn("rotnd 340 ms", summary)
        self.assertIn("move 120 ms", summary)

    def test_reset_unified_settings_restores_animation_defaults(self) -> None:
        state = SimpleNamespace(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
            overlay_transparency=0.4,
            game_seed=999,
            random_mode_index=1,
            topology_advanced=1,
            kick_level_index=2,
            auto_speedup_enabled=0,
            lines_per_level=22,
            rotation_animation_mode="cellwise_sliding",
            rotation_animation_duration_ms_2d=40,
            rotation_animation_duration_ms_nd=60,
            translation_animation_duration_ms=60,
            score_logging_enabled=True,
            pending_reset_confirm=False,
            saved=False,
            status="",
            status_error=False,
        )
        screen = object()
        with (
            mock.patch.object(settings_hub_actions, "_audio_defaults", return_value=AudioSettings()),
            mock.patch.object(settings_hub_actions, "_display_defaults", return_value=DisplaySettings()),
            mock.patch.object(
                settings_hub_actions,
                "default_display_settings",
                return_value={"overlay_transparency": 0.25},
            ),
            mock.patch.object(settings_hub_actions, "_analytics_defaults", return_value=False),
            mock.patch.object(settings_hub_actions, "_sync_audio_preview"),
            mock.patch.object(settings_hub_actions, "_sync_analytics_preview"),
            mock.patch.object(settings_hub_actions, "apply_display_mode", return_value=screen),
            mock.patch.object(settings_hub_actions, "play_sfx"),
        ):
            settings_hub_actions._reset_unified_settings(screen, state)

        self.assertEqual(
            state.rotation_animation_duration_ms_2d,
            settings_hub_model._ROTATION_ANIMATION_DURATION_2D_DEFAULT,
        )
        self.assertEqual(
            state.rotation_animation_duration_ms_nd,
            settings_hub_model._ROTATION_ANIMATION_DURATION_ND_DEFAULT,
        )
        self.assertEqual(
            state.translation_animation_duration_ms,
            settings_hub_model._TRANSLATION_ANIMATION_DURATION_DEFAULT,
        )
        self.assertEqual(
            state.rotation_animation_mode,
            settings_hub_model._ROTATION_ANIMATION_MODE_DEFAULT,
        )

    def test_advanced_gameplay_adjusts_animation_rows(self) -> None:
        state = SimpleNamespace(
            kick_level_index=0,
            auto_speedup_enabled=1,
            lines_per_level=10,
            rotation_animation_mode="rigid_piece_rotation",
            rotation_animation_duration_ms_2d=300,
            rotation_animation_duration_ms_nd=340,
            translation_animation_duration_ms=120,
            saved=True,
            status="",
            status_error=False,
        )
        self.assertTrue(
            settings_hub_actions._adjust_advanced_gameplay_value(
                state,
                "rotation_animation_duration_ms_2d",
                -1,
            )
        )
        self.assertEqual(state.rotation_animation_duration_ms_2d, 280)
        self.assertTrue(
            settings_hub_actions._adjust_advanced_gameplay_value(
                state,
                "rotation_animation_duration_ms_nd",
                1,
            )
        )
        self.assertEqual(state.rotation_animation_duration_ms_nd, 360)
        self.assertTrue(
            settings_hub_actions._adjust_advanced_gameplay_value(
                state,
                "translation_animation_duration_ms",
                1,
            )
        )
        self.assertEqual(state.translation_animation_duration_ms, 140)
        self.assertTrue(
            settings_hub_actions._adjust_advanced_gameplay_value(
                state,
                "rotation_animation_mode",
                1,
            )
        )
        self.assertEqual(state.rotation_animation_mode, "cellwise_sliding")
