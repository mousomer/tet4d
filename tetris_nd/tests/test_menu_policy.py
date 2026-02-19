from __future__ import annotations

import unittest

from tetris_nd import launcher_settings, menu_config


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

    def test_setup_fields_include_topology_mode_per_dimension(self) -> None:
        for dimension in (2, 3, 4):
            fields = menu_config.setup_fields_for_dimension(dimension, piece_set_max=5)
            attrs = {attr for _label, attr, _min_val, _max_val in fields}
            self.assertIn("topology_mode", attrs)
            self.assertIn("topology_advanced", attrs)
            self.assertIn("topology_profile_index", attrs)

    def test_launcher_pause_entrypoint_parity(self) -> None:
        launcher_actions = {action for action, _label in menu_config.launcher_menu_items()}
        pause_actions = set(menu_config.pause_menu_actions())
        required = {"settings", "keybindings", "help", "bot_options", "quit"}
        self.assertTrue(required.issubset(launcher_actions))
        self.assertTrue(required.issubset(pause_actions))

    def test_pause_rows_and_actions_stay_in_sync(self) -> None:
        self.assertEqual(
            len(menu_config.pause_menu_rows()),
            len(menu_config.pause_menu_actions()),
        )
