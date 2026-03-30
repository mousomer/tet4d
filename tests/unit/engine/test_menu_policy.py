from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

from tet4d.ui.pygame.launch import settings_hub_actions, settings_hub_model
from tet4d.engine.runtime import menu_config
from tet4d.engine.runtime.menu_structure_schema import validate_structure_payload
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings


class TestMenuPolicy(unittest.TestCase):
    @staticmethod
    def _structure_payload() -> dict[str, object]:
        path = (
            Path(__file__).resolve().parents[3] / "config" / "menu" / "structure.json"
        )
        return json.loads(path.read_text(encoding="utf-8"))

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
        self.assertEqual(
            [entry["label"] for entry in top_level],
            ["Audio", "Display", "Game"],
        )

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
        for expected_row_key in (
            "rotation_animation_mode",
            "kick_level_index",
            "rotation_animation_duration_ms_2d",
            "rotation_animation_duration_ms_nd",
            "translation_animation_duration_ms",
            "auto_speedup_enabled",
            "lines_per_level",
            "topology_cache_measure",
            "topology_cache_clear",
        ):
            self.assertTrue(
                any(
                    row_key == expected_row_key
                    for kind, _label, row_key in rows
                    if kind == "item"
                ),
                expected_row_key,
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

    def test_settings_sections_define_filtered_hub_contract(self) -> None:
        audio = menu_config.settings_section("audio")
        display = menu_config.settings_section("display")
        gameplay = menu_config.settings_section("gameplay")
        self.assertEqual(tuple(audio["headers"]), ("Audio",))
        self.assertEqual(tuple(display["headers"]), ("Display",))
        self.assertEqual(
            tuple(gameplay["headers"]),
            ("Game", "Advanced gameplay", "Analytics"),
        )
        self.assertIn("game_seed", gameplay["row_keys"])
        self.assertIn("rotation_animation_mode", gameplay["row_keys"])
        self.assertIn("analytics_score_logging", gameplay["row_keys"])
        self.assertIn("save", gameplay["row_keys"])
        self.assertIn("reset", gameplay["row_keys"])
        self.assertIn("back", gameplay["row_keys"])

    def test_launcher_settings_routes_are_config_driven(self) -> None:
        gameplay_route = menu_config.launcher_settings_route("settings")
        audio_route = menu_config.launcher_settings_route("settings_audio")
        display_route = menu_config.launcher_settings_route("settings_display")

        self.assertEqual(
            gameplay_route,
            {"section_id": "gameplay", "initial_row_key": "game_seed"},
        )
        self.assertEqual(
            audio_route,
            {"section_id": "audio", "initial_row_key": "audio_master"},
        )
        self.assertEqual(
            display_route,
            {"section_id": "display", "initial_row_key": "display_fullscreen"},
        )
        settings_actions = {
            item["action_id"]
            for item in menu_config.menu_definition("launcher_settings_root")["items"]
            if item["type"] == "action"
        }
        self.assertTrue(
            set(menu_config.launcher_settings_routes()).issubset(settings_actions)
        )

    def test_settings_sections_fail_validation_on_unknown_layout_header(self) -> None:
        payload = self._structure_payload()
        payload["settings_sections"]["audio"]["headers"] = ["Missing Header"]
        with self.assertRaisesRegex(RuntimeError, "unknown layout headers"):
            validate_structure_payload(payload)

    def test_settings_sections_fail_validation_on_unknown_layout_row_key(self) -> None:
        payload = self._structure_payload()
        payload["settings_sections"]["audio"]["row_keys"] = ["missing_row"]
        with self.assertRaisesRegex(RuntimeError, "unknown layout row keys"):
            validate_structure_payload(payload)

    def test_launcher_settings_routes_fail_validation_on_unknown_action(self) -> None:
        payload = self._structure_payload()
        payload["launcher_settings_routes"]["settings_audo"] = {
            "section_id": "audio",
            "initial_row_key": "audio_master",
        }
        with self.assertRaisesRegex(
            RuntimeError, "unknown launcher settings action"
        ):
            validate_structure_payload(payload)

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
                "Topology Playground",
                "Settings",
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
            {
                "play_2d",
                "play_3d",
                "play_4d",
                "play_last_custom_topology",
                "bot_options",
                "leaderboard",
            }.issubset(play_actions)
        )
        self.assertNotIn("topology_lab", play_actions)

    def test_play_menu_is_minimal_launcher(self) -> None:
        launcher_play = menu_config.menu_definition("launcher_play")
        self.assertIn(
            "play-adjacent tools",
            menu_config.launcher_subtitles()["launcher_play"],
        )
        self.assertIn(
            "play_last_custom_topology",
            {
                item["action_id"]
                for item in launcher_play["items"]
                if item["type"] == "action"
            },
        )
        self.assertIn(
            "bot_options",
            {
                item["action_id"]
                for item in launcher_play["items"]
                if item["type"] == "action"
            },
        )
        self.assertIn(
            "leaderboard",
            {
                item["action_id"]
                for item in launcher_play["items"]
                if item["type"] == "action"
            },
        )

    def test_topology_playground_is_root_launcher_entry(self) -> None:
        root_items = menu_config.menu_items(menu_config.launcher_menu_id())
        topology_item = next(
            item for item in root_items if item.get("action_id") == "topology_lab"
        )
        self.assertEqual(topology_item["label"], "Topology Playground")

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
        self.assertIn("launcher_tutorials", subtitles)
        self.assertIn("launcher_tutorials_interactive", subtitles)
        self.assertIn("launcher_settings_root", subtitles)
        self.assertIn("default", subtitles)
        self.assertTrue(
            all(isinstance(text, str) and text for text in subtitles.values())
        )

    def test_tutorials_menu_structure_matches_learning_support_split(self) -> None:
        tutorials = menu_config.menu_definition("launcher_tutorials")
        labels = [item["label"] for item in tutorials["items"]]
        self.assertEqual(
            labels,
            [
                "Interactive Tutorials",
                "How to Play",
                "Controls Reference",
                "Help / FAQ",
            ],
        )
        interactive = tutorials["items"][0]
        self.assertEqual(interactive["type"], "submenu")
        self.assertEqual(interactive["menu_id"], "launcher_tutorials_interactive")

        interactive_menu = menu_config.menu_definition("launcher_tutorials_interactive")
        interactive_actions = [item["action_id"] for item in interactive_menu["items"]]
        self.assertEqual(
            interactive_actions,
            ["tutorial_2d", "tutorial_3d", "tutorial_4d"],
        )

    def test_settings_menu_structure_matches_requested_sections(self) -> None:
        settings_menu = menu_config.menu_definition("launcher_settings_root")
        labels = [item["label"] for item in settings_menu["items"]]
        self.assertEqual(
            labels,
            [
                "Game",
                "Display",
                "Audio",
                "Controls",
                "Profiles",
                "Legacy Topology Editor Menu",
            ],
        )
        self.assertEqual(
            [item["type"] for item in settings_menu["items"]],
            ["action", "action", "action", "action", "action", "action"],
        )
        self.assertEqual(
            settings_menu["items"][-1]["action_id"],
            "settings_legacy_topology_editor",
        )

    def test_topology_playground_has_no_legacy_topology_entry(self) -> None:
        root_items = menu_config.menu_items(menu_config.launcher_menu_id())
        topology_item = next(
            item for item in root_items if item.get("action_id") == "topology_lab"
        )
        self.assertEqual(topology_item["type"], "action")
        self.assertNotIn("menu_id", topology_item)
        reachable = set(menu_config.reachable_action_ids(menu_config.launcher_menu_id()))
        self.assertIn("settings_legacy_topology_editor", reachable)
        self.assertNotIn("legacy_topology_editor_menu", reachable)

    def test_controls_settings_and_reference_use_distinct_destinations(self) -> None:
        tutorials = menu_config.menu_definition("launcher_tutorials")
        controls_reference = next(
            item
            for item in tutorials["items"]
            if item["label"] == "Controls Reference"
        )
        settings_menu = menu_config.menu_definition("launcher_settings_root")
        controls_settings = next(
            item for item in settings_menu["items"] if item["label"] == "Controls"
        )
        self.assertEqual(controls_reference["action_id"], "tutorial_controls_reference")
        self.assertEqual(controls_settings["action_id"], "keybindings")
        self.assertNotEqual(
            controls_reference["action_id"], controls_settings["action_id"]
        )

    def test_help_is_available_from_tutorials_not_only_settings(self) -> None:
        tutorials = menu_config.menu_definition("launcher_tutorials")
        tutorial_actions = {
            item["action_id"] for item in tutorials["items"] if item["type"] == "action"
        }
        settings_menu = menu_config.menu_definition("launcher_settings_root")
        settings_labels = [item["label"] for item in settings_menu["items"]]
        self.assertIn("help", tutorial_actions)
        self.assertNotIn("Help", settings_labels)

    def test_leaderboard_is_play_adjacent_not_in_settings(self) -> None:
        play_menu = menu_config.menu_definition("launcher_play")
        play_actions = {
            item["action_id"] for item in play_menu["items"] if item["type"] == "action"
        }
        settings_menu = menu_config.menu_definition("launcher_settings_root")
        settings_actions = {
            item["action_id"]
            for item in settings_menu["items"]
            if item["type"] == "action"
        }
        self.assertIn("leaderboard", play_actions)
        self.assertNotIn("leaderboard", settings_actions)

    def test_bot_is_play_adjacent_not_in_settings(self) -> None:
        play_menu = menu_config.menu_definition("launcher_play")
        play_actions = {
            item["action_id"] for item in play_menu["items"] if item["type"] == "action"
        }
        settings_menu = menu_config.menu_definition("launcher_settings_root")
        settings_actions = {
            item["action_id"]
            for item in settings_menu["items"]
            if item["type"] == "action"
        }
        self.assertIn("bot_options", play_actions)
        self.assertNotIn("bot_options", settings_actions)

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

    def test_unified_gameplay_rows_include_advanced_value_text(self) -> None:
        state = settings_hub_model.build_unified_settings_state(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
        )
        state.rotation_animation_mode = "rigid_piece_rotation"
        state.kick_level_index = 2
        state.auto_speedup_enabled = 1
        state.lines_per_level = 14
        state.rotation_animation_duration_ms_2d = 300
        state.rotation_animation_duration_ms_nd = 340
        state.translation_animation_duration_ms = 120
        self.assertEqual(
            settings_hub_model._unified_value_text(state, "rotation_animation_mode"),
            "Rigid piece rotation",
        )
        self.assertEqual(
            settings_hub_model._unified_value_text(state, "kick_level_index"),
            "Standard",
        )
        self.assertEqual(
            settings_hub_model._unified_value_text(
                state, "rotation_animation_duration_ms_2d"
            ),
            "300 ms",
        )

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

    def test_measure_topology_cache_updates_status_without_dirtying_settings(self) -> None:
        state = SimpleNamespace(
            topology_cache_file_count=0,
            topology_cache_size_bytes=None,
            status="",
            status_error=False,
            saved=True,
        )
        with (
            mock.patch.object(
                settings_hub_actions,
                "topology_cache_usage",
                return_value=(3, 2048),
            ),
            mock.patch.object(settings_hub_actions, "play_sfx"),
        ):
            self.assertTrue(settings_hub_actions._measure_topology_cache(state))
        self.assertEqual(state.topology_cache_file_count, 3)
        self.assertEqual(state.topology_cache_size_bytes, 2048)
        self.assertIn("3 files", state.status)
        self.assertTrue(state.saved)

    def test_clear_topology_cache_action_clears_disk_and_runtime_caches(self) -> None:
        state = SimpleNamespace(
            topology_cache_file_count=4,
            topology_cache_size_bytes=4096,
            status="",
            status_error=False,
            saved=True,
        )
        with (
            mock.patch.object(
                settings_hub_actions,
                "clear_topology_cache",
                return_value=(4, 4096),
            ),
            mock.patch.object(
                settings_hub_actions.movement_graph_module._build_movement_graph_rows,
                "cache_clear",
            ) as clear_graph_cache,
            mock.patch.object(
                settings_hub_actions.build_explorer_transport_resolver,
                "cache_clear",
            ) as clear_resolver_cache,
            mock.patch.object(settings_hub_actions, "play_sfx"),
        ):
            self.assertTrue(settings_hub_actions._clear_topology_cache_action(state))
        clear_graph_cache.assert_called_once_with()
        clear_resolver_cache.assert_called_once_with()
        self.assertEqual(state.topology_cache_file_count, 0)
        self.assertEqual(state.topology_cache_size_bytes, 0)
        self.assertIn("Cleared topology cache", state.status)
