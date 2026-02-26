from __future__ import annotations

import unittest

import tet4d.engine.api as engine_api


class TestHelpTextRuntime(unittest.TestCase):
    def test_topic_block_lines_loaded_from_doc(self) -> None:
        compact_lines = engine_api.help_topic_block_lines_runtime(
            "overview", compact=True
        )
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


if __name__ == "__main__":
    unittest.main()
