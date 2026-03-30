from __future__ import annotations

import unittest

import pygame

from tet4d.ui.pygame import frontend_nd_setup
from tet4d.ui.pygame.runtime_ui import help_menu
from tet4d.ui.pygame.runtime_ui.help_menu import (
    help_topic_action_rows,
    paginate_help_lines,
)
from tet4d.ui.pygame.ui_utils import text_fits


class TestHelpMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.fonts = frontend_nd_setup.init_fonts()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_paginate_help_lines_preserves_all_lines(self) -> None:
        lines = tuple(f"line-{idx}" for idx in range(23))
        pages = paginate_help_lines(lines, rows_per_page=7)
        self.assertEqual(len(pages), 4)
        flattened = tuple(item for page in pages for item in page)
        self.assertEqual(flattened, lines)

    def test_topic_action_rows_include_mapped_actions_for_dimension(self) -> None:
        rows = help_topic_action_rows(
            topic_id="movement_rotation", dimension=4, include_all=False
        )
        actions = {action for _group, action, _keys in rows}
        self.assertIn("move_x_neg", actions)
        self.assertIn("rotate_xw_pos", actions)
        self.assertNotIn("menu", actions)

    def test_topic_action_rows_include_all_groups_for_key_reference(self) -> None:
        rows = help_topic_action_rows(
            topic_id="key_reference", dimension=4, include_all=True
        )
        groups = {group for group, _action, _keys in rows}
        self.assertTrue({"system", "game", "camera"}.issubset(groups))
        self.assertNotIn("slice", groups)

    def test_key_reference_lines_split_gameplay_into_translation_and_rotation(
        self,
    ) -> None:
        lines = help_menu.help_topic_action_lines(
            topic_id="key_reference", dimension=4, include_all=True
        )
        text = "\n".join(lines)
        self.assertIn("-- Gameplay / Translation", text)
        self.assertIn("-- Gameplay / Rotation", text)
        self.assertNotIn("slice_", text)

    def test_compact_mode_detection_thresholds(self) -> None:
        self.assertTrue(help_menu.is_compact_help_view(width=640, height=600))
        self.assertTrue(help_menu.is_compact_help_view(width=900, height=420))
        self.assertFalse(help_menu.is_compact_help_view(width=1200, height=760))

    def test_draw_help_handles_compact_windows(self) -> None:
        contexts = ("Launcher", "Pause Menu")
        sizes = ((640, 420), (520, 340), (420, 300))
        for size in sizes:
            for context in contexts:
                with self.subTest(size=size, context=context):
                    screen = pygame.Surface(size, pygame.SRCALPHA)
                    state = help_menu._HelpState(dimension=4, page=0, subpage=0)
                    help_menu._draw_help(screen, self.fonts, state, context)
                    self.assertGreaterEqual(state.subpage, 0)
                    self.assertGreater(screen.get_bounding_rect().width, 0)

    def test_initial_topic_selection_targets_requested_topic(self) -> None:
        state = help_menu._HelpState(dimension=4)
        help_menu._set_initial_topic(
            state,
            context_label="Launcher",
            topic_id="key_reference",
        )
        topic, _topics = help_menu._current_topic(state, "Launcher")
        self.assertEqual(topic["id"], "key_reference")

    def test_topology_playground_seam_topic_renders_current_edit_flow(self) -> None:
        state = help_menu._HelpState(dimension=4)
        help_menu._set_initial_topic(
            state,
            context_label="Launcher",
            topic_id="topology_playground_seams",
        )
        topic, topics = help_menu._current_topic(state, "Launcher")
        lines = help_menu._topic_text_lines(
            topic=topic,
            state=state,
            context_label="Launcher",
            topics=topics,
            compact=False,
        )
        text = "\n".join(lines)
        self.assertIn("Open Topology Playground, switch to Editor, and set Tool to Edit.", text)
        self.assertIn("Press Apply to commit the seam.", text)
        self.assertIn("Press Remove only after the seam is selected.", text)

    def test_help_header_text_fits_compact_window_budget(self) -> None:
        screen = pygame.Surface((640, 420), pygame.SRCALPHA)
        frame_rect, header_rect, _content_rect, footer_rect = help_menu._help_layout_zones(
            screen, self.fonts
        )
        self.assertGreater(frame_rect.width, 0)
        self.assertGreater(footer_rect.width, 0)

        title_text = help_menu._format_help_line(
            help_menu._HELP_TITLE_TEMPLATE,
            context_label="Pause Menu",
            dimension=4,
            help_key="F1",
        )
        subtitle_text = help_menu._format_help_line(
            help_menu._HELP_SUBTITLE_COMPACT_TEMPLATE,
            context_label="Pause Menu",
            dimension=4,
            help_key="F1",
        )
        title_budget = max(40, header_rect.width - (help_menu._HELP_CONTENT_PAD_X * 2))
        self.assertTrue(text_fits(self.fonts.title_font, title_text, title_budget))
        self.assertTrue(text_fits(self.fonts.hint_font, subtitle_text, title_budget))


if __name__ == "__main__":
    unittest.main()
