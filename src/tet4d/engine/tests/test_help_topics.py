from __future__ import annotations

import unittest

from tet4d.engine.help_topics import (
    clear_help_topic_caches,
    help_action_topic_registry,
    help_topics_for_context,
    help_topic_for_action,
    help_topics_registry,
    validate_help_topic_contract,
)
from tet4d.engine.keybindings_catalog import binding_action_ids


class TestHelpTopics(unittest.TestCase):
    def setUp(self) -> None:
        clear_help_topic_caches()

    def tearDown(self) -> None:
        clear_help_topic_caches()

    def test_help_topics_registry_loads(self) -> None:
        registry = help_topics_registry()
        self.assertGreaterEqual(registry["version"], 1)
        self.assertGreater(len(registry["topics"]), 0)
        self.assertEqual(len(registry["topic_ids"]), len(set(registry["topic_ids"])))

    def test_action_map_covers_all_known_actions(self) -> None:
        registry = help_action_topic_registry()
        mapped_actions = set(registry["action_topics"].keys())
        self.assertEqual(mapped_actions, set(binding_action_ids()))

    def test_topic_lookup_for_known_action_returns_existing_topic(self) -> None:
        topic_registry = help_topics_registry()
        topic_ids = set(topic_registry["topic_ids"])
        for action in binding_action_ids():
            topic_id = help_topic_for_action(action)
            self.assertIn(topic_id, topic_ids)

    def test_contract_validation_passes(self) -> None:
        ok, msg = validate_help_topic_contract()
        self.assertTrue(ok, msg)

    def test_help_topics_for_context_are_filtered_and_sorted(self) -> None:
        topics = help_topics_for_context(dimension=3, context_label="Pause Menu")
        self.assertGreater(len(topics), 0)
        self.assertTrue(all(3 in topic["dimensions"] for topic in topics))
        self.assertTrue(all("pause" in topic["contexts"] for topic in topics))
        priorities = [int(topic["priority"]) for topic in topics]
        self.assertEqual(priorities, sorted(priorities))

    def test_action_topics_prefer_quick_or_full_lanes(self) -> None:
        topics_registry = help_topics_registry()
        topic_lanes = {
            topic["id"]: topic["lane"] for topic in topics_registry["topics"]
        }
        action_registry = help_action_topic_registry()
        for action in binding_action_ids():
            with self.subTest(action=action):
                topic_id = action_registry["action_topics"][action]
                self.assertIn(topic_lanes[topic_id], {"quick", "full"})


if __name__ == "__main__":
    unittest.main()
