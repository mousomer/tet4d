from __future__ import annotations

import importlib.util
import unittest
from unittest.mock import patch

if importlib.util.find_spec("pygame") is None:  # pragma: no cover - env guard
    raise unittest.SkipTest("pygame-ce is required for tutorial overlay layout tests")

import pygame

from tet4d.ui.pygame.runtime_ui import tutorial_overlay


class TestTutorialOverlayLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_2d_overlay_panel_stays_top_left(self) -> None:
        width, height = 1280, 720
        panel_h = 220

        rect = tutorial_overlay._panel_rect_for_dimension(
            width=width,
            height=height,
            dimension=2,
            panel_h=panel_h,
        )

        self.assertEqual(rect.x, 12)
        self.assertEqual(rect.y, 12)
        self.assertEqual(rect.width, min(760, max(420, int(width * 0.52))))

    def test_3d_overlay_panel_is_inside_hud_column(self) -> None:
        width, height = 1400, 900
        margin = 20
        side_panel = 360

        with (
            patch.object(tutorial_overlay.engine_api, "front3d_render_margin", return_value=margin),
            patch.object(tutorial_overlay.engine_api, "front3d_render_side_panel", return_value=side_panel),
        ):
            rect = tutorial_overlay._panel_rect_for_dimension(
                width=width,
                height=height,
                dimension=3,
                panel_h=220,
            )

        hud_x = width - side_panel - margin
        board_right = width - side_panel - (2 * margin)
        self.assertGreaterEqual(rect.left, hud_x)
        self.assertGreater(rect.left, board_right)
        self.assertLessEqual(rect.right, width - 12)
        self.assertLessEqual(rect.width, side_panel)

    def test_4d_overlay_panel_is_inside_hud_column(self) -> None:
        width, height = 1600, 920
        margin = 16
        side_panel = 360

        with (
            patch.object(tutorial_overlay.engine_api, "front4d_render_margin", return_value=margin),
            patch.object(tutorial_overlay.engine_api, "front4d_render_side_panel", return_value=side_panel),
        ):
            rect = tutorial_overlay._panel_rect_for_dimension(
                width=width,
                height=height,
                dimension=4,
                panel_h=220,
            )

        hud_x = width - side_panel - margin
        board_right = width - side_panel - (2 * margin)
        self.assertGreaterEqual(rect.left, hud_x)
        self.assertGreater(rect.left, board_right)
        self.assertLessEqual(rect.right, width - 12)
        self.assertLessEqual(rect.width, side_panel)

    def test_panel_offsets_are_clamped_to_screen_bounds(self) -> None:
        width, height = 1200, 700
        panel_h = 240
        with (
            patch.object(tutorial_overlay.engine_api, "front3d_render_margin", return_value=20),
            patch.object(tutorial_overlay.engine_api, "front3d_render_side_panel", return_value=360),
        ):
            rect = tutorial_overlay._panel_rect_for_dimension(
                width=width,
                height=height,
                dimension=3,
                panel_h=panel_h,
                panel_offset=(-5000, 4000),
            )

        self.assertGreaterEqual(rect.left, 0)
        self.assertGreaterEqual(rect.top, 0)
        self.assertLessEqual(rect.right, width)
        self.assertLessEqual(rect.bottom, height)

    def test_wrap_text_line_breaks_long_content(self) -> None:
        font = pygame.font.Font(None, 24)
        line = (
            "F5/F6: Prev/Next stage | F7: Redo | "
            "F8: Main menu | F9: Restart"
        )

        wrapped = tutorial_overlay._wrap_text_line(font, line, max_width=220)

        self.assertGreater(len(wrapped), 1)
        for item in wrapped:
            self.assertLessEqual(font.size(item)[0], 220)


if __name__ == "__main__":
    unittest.main()
