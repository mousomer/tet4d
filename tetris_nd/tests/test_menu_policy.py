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

