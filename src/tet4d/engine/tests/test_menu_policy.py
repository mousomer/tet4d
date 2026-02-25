from __future__ import annotations

import unittest

from tet4d.engine import launcher_settings
from tet4d.engine.runtime import menu_config


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
        ok, message = launcher_settings._validate_unified_layout_against_policy()
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

    def test_settings_hub_headers_align_with_top_level_categories(self) -> None:
        top_level = menu_config.settings_top_level_categories()
        expected = {entry["label"] for entry in top_level}
        headers = {
            label
            for kind, label, _row_key in menu_config.settings_hub_layout_rows()
            if kind == "header"
        }
        self.assertTrue(expected.issubset(headers))

    def test_setup_fields_include_topology_mode_per_dimension(self) -> None:
        for dimension in (2, 3, 4):
            fields = menu_config.setup_fields_for_dimension(dimension, piece_set_max=5)
            attrs = {attr for _label, attr, _min_val, _max_val in fields}
            self.assertIn("topology_mode", attrs)
            self.assertIn("topology_advanced", attrs)
            self.assertIn("topology_profile_index", attrs)

    def test_launcher_pause_entrypoint_parity(self) -> None:
        launcher_actions = set(
            menu_config.reachable_action_ids(menu_config.launcher_menu_id())
        )
        pause_actions = set(
            menu_config.reachable_action_ids(menu_config.pause_menu_id())
        )
        required = {"settings", "keybindings", "help", "bot_options", "quit"}
        self.assertTrue(required.issubset(launcher_actions))
        self.assertTrue(required.issubset(pause_actions))

    def test_pause_rows_and_actions_stay_in_sync(self) -> None:
        self.assertEqual(
            len(menu_config.pause_menu_rows()),
            len(menu_config.pause_menu_actions()),
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
            "bot_options",
            "menu",
            "quit",
        }
        self.assertTrue(expected.issubset(pause_actions))

    def test_menu_graph_root_labels_preserve_top_level_ia(self) -> None:
        root_items = menu_config.menu_items(menu_config.launcher_menu_id())
        labels = [item["label"] for item in root_items]
        self.assertEqual(
            labels, ["Play", "Continue", "Settings", "Controls", "Help", "Bot", "Quit"]
        )

    def test_play_menu_is_graph_defined_and_includes_future_routes(self) -> None:
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
        play_routes = {
            item["route_id"] for item in play_items if item["type"] == "route"
        }
        self.assertTrue({"play_2d", "play_3d", "play_4d"}.issubset(play_actions))
        self.assertTrue({"tutorials", "topology_lab"}.issubset(play_routes))
