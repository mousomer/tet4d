from __future__ import annotations

import unittest

import pygame

from tet4d.engine import frontend_nd
from tet4d.ui.pygame import help_menu
from tet4d.ui.pygame.help_menu import help_topic_action_rows, paginate_help_lines


class TestHelpMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.fonts = frontend_nd.init_fonts()

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


if __name__ == "__main__":
    unittest.main()
