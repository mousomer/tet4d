from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

from tet4d.ui.pygame.launch import settings_hub_actions, settings_hub_model
from tet4d.engine.runtime import menu_config
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
        self.assertEqual(
            [entry["label"] for entry in top_level],
            [
                "Game",
                "Display",
                "Audio",
            ],
        )

    def test_launcher_settings_layout_matches_policy(self) -> None:
        ok, message = settings_hub_model._validate_unified_layout_against_policy()
        self.assertTrue(ok, message)

    def test_canonical_menu_config_replaces_retired_split_settings_keys(self) -> None:
        payload = self._structure_payload()
        self.assertNotIn("settings_hub_rows", payload)
        self.assertNotIn("settings_hub_layout_rows", payload)
        self.assertNotIn("settings_sections", payload)
        self.assertNotIn("launcher_settings_routes", payload)

    def test_canonical_menu_config_supports_required_item_types(self) -> None:
        item_types = {
            item["type"]
            for menu in menu_config.authored_menu_graph().values()
            for item in menu["items"]
        }
        self.assertTrue(
            {
                "action",
                "action_group",
                "submenu",
                "section",
                "info",
                "toggle",
                "selector",
                "slider",
                "keybinding_group",
                "legacy_dispatch",
            }.issubset(item_types)
        )

    def test_authored_settings_root_declares_flat_game_page_and_direct_controls(self) -> None:
        settings_menu = menu_config.authored_menu_definition(menu_config.settings_menu_id())
        self.assertEqual(
            [item["label"] for item in settings_menu["items"]],
            [
                "Game",
                "Display",
                "Audio",
                "Keyboard Bindings",
                "Legacy Topology Editor Menu",
                "Back",
            ],
        )
        self.assertEqual(
            [item["type"] for item in settings_menu["items"]],
            ["submenu", "submenu", "submenu", "action", "legacy_dispatch", "action"],
        )

        game_menu = menu_config.authored_menu_definition("settings_game_root")
        self.assertEqual(
            game_menu["title"],
            "Game",
        )
        self.assertEqual(
            [item["label"] for item in game_menu["items"] if item["type"] == "section"],
            [
                "Gameplay",
                "Board / Geometry",
                "Movement / Rotation",
                "Endgame Effects",
                "Difficulty / Pace",
            ],
        )
        item_ids = [item["id"] for item in game_menu["items"]]
        self.assertIn("display_overlay_transparency", item_ids)
        self.assertIn("endgame_preset_id", item_ids)
        self.assertIn("save", item_ids)
        self.assertIn("reset", item_ids)
        self.assertIn("back", item_ids)
        self.assertNotIn(
            "settings_game_gameplay",
            menu_config.authored_menu_graph(),
        )
        self.assertNotIn(
            "settings_endgame_effects",
            menu_config.authored_menu_graph(),
        )

    def test_runtime_settings_root_collapses_singleton_wrappers(self) -> None:
        settings_menu = menu_config.menu_definition(menu_config.settings_menu_id())
        self.assertEqual(
            [item["label"] for item in settings_menu["items"]],
            [
                "Game",
                "Display",
                "Audio",
                "Keyboard Bindings",
                "Legacy Topology Editor Menu",
                "Back",
            ],
        )
        self.assertEqual(
            [item["type"] for item in settings_menu["items"]],
            ["submenu", "submenu", "submenu", "action", "legacy_dispatch", "action"],
        )
        self.assertNotIn("settings_controls", menu_config.menu_graph())
        self.assertNotIn("settings_legacy", menu_config.menu_graph())
        self.assertNotIn("settings_game_visual_animation", menu_config.menu_graph())
        self.assertNotIn("settings_game_gameplay", menu_config.menu_graph())
        self.assertNotIn("settings_game_board_geometry", menu_config.menu_graph())
        self.assertNotIn("settings_game_movement_rotation", menu_config.menu_graph())
        self.assertNotIn("settings_game_difficulty_pace", menu_config.menu_graph())
        self.assertNotIn("settings_endgame_effects", menu_config.menu_graph())

        game_menu = menu_config.menu_definition("settings_game_root")
        item_ids = [item["id"] for item in game_menu["items"]]
        self.assertIn("display_overlay_transparency", item_ids)
        self.assertIn("endgame_preset_id", item_ids)
        self.assertIn("topology_cache_measure", item_ids)
        self.assertIn("save", item_ids)

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
        required = {"settings", "help", "bot_options", "quit", "leaderboard"}
        self.assertTrue(required.issubset(launcher_actions))
        self.assertTrue(required.issubset(pause_actions))
        settings_actions = set(
            menu_config.reachable_action_ids(menu_config.settings_menu_id())
        )
        self.assertIn("keybindings", settings_actions)
        self.assertIn("settings_legacy_topology_editor", settings_actions)

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
                "Explosion Simulator",
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
        play_actions: set[str] = {
            item["action_id"] for item in play_items if item["type"] == "action"
        }
        for item in play_items:
            if item["type"] != "action_group":
                continue
            play_actions.update(
                action["action_id"] for action in item.get("actions", ())
            )
        self.assertTrue(
            {
                "play_2d",
                "play_3d",
                "play_4d",
                "setup_2d",
                "setup_3d",
                "setup_4d",
                "play_last_custom_topology",
                "bot_options",
                "leaderboard",
            }.issubset(play_actions)
        )
        self.assertNotIn("topology_lab", play_actions)

    def test_play_menu_uses_action_groups_for_direct_play_and_setup(self) -> None:
        play_menu = menu_config.authored_menu_definition("launcher_play")
        dimension_rows = tuple(play_menu["items"][:3])
        self.assertTrue(all(item["type"] == "action_group" for item in dimension_rows))
        self.assertEqual([item["label"] for item in dimension_rows], ["2D", "3D", "4D"])
        for item, play_action_id, setup_action_id in (
            (dimension_rows[0], "play_2d", "setup_2d"),
            (dimension_rows[1], "play_3d", "setup_3d"),
            (dimension_rows[2], "play_4d", "setup_4d"),
        ):
            self.assertEqual(item["default_action_id"], "play")
            self.assertEqual(
                tuple(action["action_id"] for action in item["actions"]),
                (play_action_id, setup_action_id),
            )

    def test_play_menu_is_minimal_launcher(self) -> None:
        launcher_play = menu_config.menu_definition("launcher_play")
        self.assertIn(
            "switch between Play and Setup",
            menu_config.launcher_subtitles()["launcher_play"],
        )
        action_ids: set[str] = {
            item["action_id"] for item in launcher_play["items"] if item["type"] == "action"
        }
        for item in launcher_play["items"]:
            if item["type"] != "action_group":
                continue
            action_ids.update(action["action_id"] for action in item["actions"])
        self.assertIn("play_last_custom_topology", action_ids)
        self.assertIn("bot_options", action_ids)
        self.assertIn("leaderboard", action_ids)

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
        settings_menu = menu_config.menu_definition("settings_root")
        labels = [item["label"] for item in settings_menu["items"]]
        self.assertEqual(
            labels,
            [
                "Game",
                "Display",
                "Audio",
                "Keyboard Bindings",
                "Legacy Topology Editor Menu",
                "Back",
            ],
        )
        self.assertEqual(
            [item["type"] for item in settings_menu["items"]],
            ["submenu", "submenu", "submenu", "action", "legacy_dispatch", "action"],
        )

    def test_keybindings_scopes_are_declared_in_canonical_menu_config(self) -> None:
        keybindings_menu = menu_config.menu_definition(menu_config.keybindings_menu_id())
        self.assertEqual(
            [item["label"] for item in keybindings_menu["items"]],
            ["General", "2D", "3D", "4D", "All"],
        )
        self.assertTrue(
            all(item["type"] == "submenu" for item in keybindings_menu["items"])
        )

    def test_topology_playground_has_no_legacy_topology_entry(self) -> None:
        root_items = menu_config.menu_items(menu_config.launcher_menu_id())
        topology_item = next(
            item for item in root_items if item.get("action_id") == "topology_lab"
        )
        self.assertEqual(topology_item["type"], "action")
        self.assertNotIn("menu_id", topology_item)
        launcher_actions = set(
            item["action_id"]
            for item in root_items
            if item["type"] == "action"
        )
        self.assertNotIn("settings_legacy_topology_editor", launcher_actions)
        settings_actions = set(
            menu_config.reachable_action_ids(menu_config.settings_menu_id())
        )
        self.assertIn("settings_legacy_topology_editor", settings_actions)

    def test_controls_settings_and_reference_use_distinct_destinations(self) -> None:
        tutorials = menu_config.menu_definition("launcher_tutorials")
        controls_reference = next(
            item for item in tutorials["items"] if item["label"] == "Controls Reference"
        )
        settings_menu = menu_config.menu_definition("settings_root")
        controls_settings = next(
            item for item in settings_menu["items"] if item["label"] == "Keyboard Bindings"
        )
        self.assertEqual(controls_reference["action_id"], "tutorial_controls_reference")
        self.assertEqual(controls_settings["action_id"], "keybindings")
        self.assertNotEqual(
            controls_reference["action_id"], controls_settings["action_id"]
        )

    def test_runtime_menu_resolution_maps_collapsed_authored_pages(self) -> None:
        self.assertEqual(
            menu_config.resolve_runtime_menu_id(
                "settings_legacy",
                item_id="settings_legacy_topology_editor",
            ),
            "settings_root",
        )
        self.assertEqual(
            menu_config.resolve_runtime_menu_id(
                "settings_game_movement_rotation",
                item_id="rotation_animation_mode",
            ),
            "settings_game_root",
        )
        self.assertEqual(
            menu_config.resolve_runtime_menu_id(
                "settings_endgame_effects",
                item_id="endgame_preset_id",
            ),
            "settings_game_root",
        )

    def test_runtime_menu_graph_avoids_unary_wrappers_and_duplicate_setting_paths(
        self,
    ) -> None:
        runtime_graph = menu_config.menu_graph()
        seen_setting_ids: dict[str, str] = {}
        for menu_id, menu in runtime_graph.items():
            items = tuple(menu["items"])
            nonutility = [
                item
                for item in items
                if item["type"]
                in {
                    "submenu",
                    "toggle",
                    "selector",
                    "slider",
                    "action",
                    "action_group",
                    "legacy_dispatch",
                }
                and item.get("action_id") not in {"back", "save", "reset", "display_apply"}
            ]
            submenu_count = sum(1 for item in nonutility if item["type"] == "submenu")
            setting_count = sum(
                1 for item in nonutility if item["type"] in {"toggle", "selector", "slider"}
            )
            if menu_id not in {
                menu_config.launcher_menu_id(),
                menu_config.pause_menu_id(),
                menu_config.settings_menu_id(),
                menu_config.keybindings_menu_id(),
            } and not any(item["type"] == "keybinding_group" for item in items):
                self.assertFalse(
                    submenu_count == 1 and len(nonutility) == 1,
                    msg=f"{menu_id} retained a unary submenu wrapper",
                )
                self.assertFalse(
                    setting_count == 1 and len(nonutility) == 1,
                    msg=f"{menu_id} retained a single-setting wrapper",
                )
            for item in items:
                if item["type"] not in {"toggle", "selector", "slider"}:
                    continue
                setting_id = item["setting_id"]
                owner = seen_setting_ids.setdefault(setting_id, menu_id)
                self.assertEqual(
                    owner,
                    menu_id,
                    msg=f"{setting_id} drifted into multiple runtime pages",
                )

    def test_runtime_menu_depth_stays_shallow(self) -> None:
        runtime_graph = menu_config.menu_graph()
        exempt_depth_ids = {menu_config.keybindings_menu_id()}
        pending = [
            (menu_config.launcher_menu_id(), 1),
            (menu_config.pause_menu_id(), 1),
            (menu_config.settings_menu_id(), 1),
            (menu_config.keybindings_menu_id(), 1),
        ]
        seen: set[tuple[str, int]] = set()
        while pending:
            menu_id, depth = pending.pop()
            if (menu_id, depth) in seen:
                continue
            seen.add((menu_id, depth))
            self.assertLessEqual(
                depth,
                3,
                msg=f"{menu_id} exceeded normalized runtime depth budget",
            )
            for item in runtime_graph.get(menu_id, {}).get("items", ()):
                if item["type"] != "submenu":
                    continue
                target = item["menu_id"]
                next_depth = depth + 1
                if menu_id in exempt_depth_ids:
                    next_depth = min(next_depth, 3)
                pending.append((target, next_depth))

    def test_help_is_available_from_tutorials_not_only_settings(self) -> None:
        tutorials = menu_config.menu_definition("launcher_tutorials")
        tutorial_actions = {
            item["action_id"] for item in tutorials["items"] if item["type"] == "action"
        }
        settings_menu = menu_config.menu_definition("settings_root")
        settings_labels = [item["label"] for item in settings_menu["items"]]
        self.assertIn("help", tutorial_actions)
        self.assertNotIn("Help", settings_labels)

    def test_leaderboard_is_play_adjacent_not_in_settings(self) -> None:
        play_menu = menu_config.menu_definition("launcher_play")
        play_actions: set[str] = {
            item["action_id"] for item in play_menu["items"] if item["type"] == "action"
        }
        for item in play_menu["items"]:
            if item["type"] != "action_group":
                continue
            play_actions.update(action["action_id"] for action in item["actions"])
        settings_actions = set(
            menu_config.reachable_action_ids(menu_config.settings_menu_id())
        )
        self.assertIn("leaderboard", play_actions)
        self.assertNotIn("leaderboard", settings_actions)

    def test_bot_is_play_adjacent_not_in_settings(self) -> None:
        play_menu = menu_config.menu_definition("launcher_play")
        play_actions: set[str] = {
            item["action_id"] for item in play_menu["items"] if item["type"] == "action"
        }
        for item in play_menu["items"]:
            if item["type"] != "action_group":
                continue
            play_actions.update(action["action_id"] for action in item["actions"])
        settings_actions = set(
            menu_config.reachable_action_ids(menu_config.settings_menu_id())
        )
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
        self.assertIn("game_endgame_preset", labels)
        self.assertEqual(len(labels["game_endgame_preset"]), 4)
        self.assertIn("game_endgame_boundary_response", labels)
        self.assertEqual(len(labels["game_endgame_boundary_response"]), 2)
        self.assertIn("game_endgame_particle_collisions", labels)
        self.assertEqual(len(labels["game_endgame_particle_collisions"]), 2)

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
            mock.patch.object(
                settings_hub_actions, "_audio_defaults", return_value=AudioSettings()
            ),
            mock.patch.object(
                settings_hub_actions,
                "_display_defaults",
                return_value=DisplaySettings(),
            ),
            mock.patch.object(
                settings_hub_actions,
                "default_display_settings",
                return_value={"overlay_transparency": 0.25},
            ),
            mock.patch.object(
                settings_hub_actions, "_analytics_defaults", return_value=False
            ),
            mock.patch.object(settings_hub_actions, "_sync_audio_preview"),
            mock.patch.object(settings_hub_actions, "_sync_analytics_preview"),
            mock.patch.object(
                settings_hub_actions, "apply_display_mode", return_value=screen
            ),
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

    def test_unified_settings_manual_numeric_edit_applies_animation_timing(
        self,
    ) -> None:
        state = SimpleNamespace(
            display_settings=DisplaySettings(
                fullscreen=False,
                windowed_size=(1200, 760),
            ),
            game_seed=1337,
            rotation_animation_duration_ms_2d=120,
            rotation_animation_duration_ms_nd=140,
            translation_animation_duration_ms=80,
            text_mode_row_key="translation_animation_duration_ms",
            text_mode_buffer="215",
            text_mode_replace_on_type=False,
            saved=True,
            status="",
            status_error=False,
            pending_reset_confirm=False,
            flash_row_key="",
            flash_frames=0,
        )
        self.assertTrue(settings_hub_actions._apply_unified_numeric_text_value(state))
        self.assertEqual(state.translation_animation_duration_ms, 215)
        self.assertEqual(state.flash_row_key, "translation_animation_duration_ms")
        self.assertEqual(state.flash_frames, 12)

    def test_unified_gameplay_rows_include_advanced_value_text(self) -> None:
        state = settings_hub_model.build_unified_settings_state(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
        )
        state.endgame_preset_id = "sphere"
        state.endgame_boundary_response = "bounce"
        state.endgame_particle_collisions = "on"
        state.endgame_relic_speed_percent = 145
        state.endgame_shatter_speed_percent = 85
        state.rotation_animation_mode = "rigid_piece_rotation"
        state.kick_level_index = 2
        state.auto_speedup_enabled = 1
        state.lines_per_level = 14
        state.rotation_animation_duration_ms_2d = 300
        state.rotation_animation_duration_ms_nd = 340
        state.translation_animation_duration_ms = 120
        self.assertEqual(
            settings_hub_model._unified_value_text(state, "endgame_preset_id"),
            "Sphere",
        )
        self.assertEqual(
            settings_hub_model._unified_value_text(
                state, "endgame_boundary_response"
            ),
            "Bounce",
        )
        self.assertEqual(
            settings_hub_model._unified_value_text(
                state, "endgame_particle_collisions"
            ),
            "On",
        )
        self.assertEqual(
            settings_hub_model._unified_value_text(
                state, "endgame_relic_speed_percent"
            ),
            "145%",
        )
        self.assertEqual(
            settings_hub_model._unified_value_text(
                state, "endgame_shatter_speed_percent"
            ),
            "85%",
        )
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
            endgame_preset_id="sphere",
            endgame_boundary_response="bounce",
            endgame_particle_collisions="on",
            endgame_relic_speed_percent=140,
            endgame_shatter_speed_percent=80,
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
            mock.patch.object(
                settings_hub_actions, "_audio_defaults", return_value=AudioSettings()
            ),
            mock.patch.object(
                settings_hub_actions,
                "_display_defaults",
                return_value=DisplaySettings(),
            ),
            mock.patch.object(
                settings_hub_actions,
                "default_display_settings",
                return_value={"overlay_transparency": 0.25},
            ),
            mock.patch.object(
                settings_hub_actions, "_analytics_defaults", return_value=False
            ),
            mock.patch.object(settings_hub_actions, "_sync_audio_preview"),
            mock.patch.object(settings_hub_actions, "_sync_analytics_preview"),
            mock.patch.object(
                settings_hub_actions, "apply_display_mode", return_value=screen
            ),
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
        self.assertEqual(
            state.endgame_preset_id,
            settings_hub_model._ENDGAME_PRESET_DEFAULT,
        )
        self.assertEqual(
            state.endgame_boundary_response,
            settings_hub_model._ENDGAME_BOUNDARY_RESPONSE_DEFAULT,
        )
        self.assertEqual(
            state.endgame_particle_collisions,
            settings_hub_model._ENDGAME_PARTICLE_COLLISIONS_DEFAULT,
        )
        self.assertEqual(
            state.endgame_relic_speed_percent,
            settings_hub_model._ENDGAME_RELIC_SPEED_DEFAULT,
        )
        self.assertEqual(
            state.endgame_shatter_speed_percent,
            settings_hub_model._ENDGAME_SHATTER_SPEED_DEFAULT,
        )

    def test_advanced_gameplay_adjusts_animation_rows(self) -> None:
        state = SimpleNamespace(
            kick_level_index=0,
            endgame_preset_id="default_orbit",
            endgame_boundary_response="escape",
            endgame_particle_collisions="off",
            endgame_relic_speed_percent=100,
            endgame_shatter_speed_percent=100,
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
            settings_hub_actions._adjust_unified_gameplay_row(
                state,
                "endgame_preset_id",
                1,
            )
        )
        self.assertEqual(state.endgame_preset_id, "wrap_all")
        self.assertTrue(
            settings_hub_actions._adjust_unified_gameplay_row(
                state,
                "endgame_boundary_response",
                1,
            )
        )
        self.assertEqual(state.endgame_boundary_response, "bounce")
        self.assertTrue(
            settings_hub_actions._adjust_unified_gameplay_row(
                state,
                "endgame_particle_collisions",
                1,
            )
        )
        self.assertEqual(state.endgame_particle_collisions, "on")
        self.assertTrue(
            settings_hub_actions._adjust_unified_gameplay_row(
                state,
                "endgame_relic_speed_percent",
                1,
            )
        )
        self.assertEqual(state.endgame_relic_speed_percent, 105)
        self.assertTrue(
            settings_hub_actions._adjust_unified_gameplay_row(
                state,
                "endgame_shatter_speed_percent",
                -1,
            )
        )
        self.assertEqual(state.endgame_shatter_speed_percent, 95)
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

    def test_measure_topology_cache_updates_status_without_dirtying_settings(
        self,
    ) -> None:
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
