from __future__ import annotations

import unittest

import tet4d.engine.api as engine_api
from tet4d.engine.help_text import validate_help_text_contract


class TestHelpTextRuntime(unittest.TestCase):
    def test_topic_block_lines_loaded_from_content_asset(self) -> None:
        compact_lines = engine_api.help_topic_block_lines_runtime("overview", compact=True)
        self.assertIn("## Context: {context_label}", compact_lines)
        self.assertIn("- Help key: {help_key}", compact_lines)

    def test_topic_compact_metadata_loaded_from_doc(self) -> None:
        self.assertEqual(engine_api.help_topic_compact_limit_runtime("overview"), 5)
        self.assertEqual(
            engine_api.help_topic_compact_overflow_line_runtime("overview"),
            "- ... and {extra_count} more topics",
        )

    def test_fallback_topic_loaded_from_doc(self) -> None:
        topic = engine_api.help_fallback_topic_runtime()
        self.assertEqual(topic["id"], "overview")
        self.assertEqual(topic["title"], "Help Overview")
        self.assertTrue(topic["sections"])

    def test_layout_payload_loaded_from_layout_asset(self) -> None:
        layout = engine_api.help_layout_payload_runtime()
        self.assertEqual(layout["topic_rules"]["controls_topic_id"], "movement_rotation")
        self.assertEqual(layout["topic_media_placement"]["default"]["mode"], "text")
        self.assertEqual(layout["topic_media_placement"]["movement_rotation"]["mode"], "controls")

    def test_layout_media_rule_defaults(self) -> None:
        known = engine_api.help_topic_media_rule_runtime("movement_rotation")
        self.assertEqual(known["mode"], "controls")
        unknown = engine_api.help_topic_media_rule_runtime("unknown_topic")
        self.assertEqual(unknown["mode"], "text")

    def test_help_text_contract_validation_passes(self) -> None:
        ok, msg = validate_help_text_contract()
        self.assertTrue(ok, msg)


if __name__ == "__main__":
    unittest.main()
