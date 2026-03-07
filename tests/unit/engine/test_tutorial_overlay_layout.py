from __future__ import annotations

import importlib.util
import unittest
from types import SimpleNamespace
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

    @staticmethod
    def _board_rect_3d(width: int, height: int, margin: int, side_panel: int) -> pygame.Rect:
        return pygame.Rect(
            margin,
            margin,
            width - side_panel - (3 * margin),
            height - (2 * margin),
        )

    @staticmethod
    def _layers_rect_4d(width: int, height: int, margin: int, side_panel: int) -> pygame.Rect:
        return pygame.Rect(
            margin,
            margin,
            width - side_panel - (3 * margin),
            height - (2 * margin),
        )

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

    def test_3d_overlay_panel_defaults_to_side_panel_lane_outside_board(self) -> None:
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

        board_rect = self._board_rect_3d(width, height, margin, side_panel)
        self.assertGreaterEqual(rect.left, board_rect.right)
        self.assertGreaterEqual(rect.y, margin + 8)
        self.assertLessEqual(rect.right, width - margin)
        self.assertLessEqual(rect.width, side_panel - 16)

    def test_4d_overlay_panel_defaults_to_side_panel_lane_outside_layers(self) -> None:
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

        layers_rect = self._layers_rect_4d(width, height, margin, side_panel)
        self.assertGreaterEqual(rect.left, layers_rect.right)
        self.assertGreaterEqual(rect.y, margin + 8)
        self.assertLessEqual(rect.right, width - margin)
        self.assertLessEqual(rect.width, side_panel - 16)

    def test_nd_panel_offsets_are_clamped_to_safe_lane(self) -> None:
        width, height = 1200, 700
        panel_h = 240
        cases = (
            (
                3,
                self._board_rect_3d,
                "front3d_render_margin",
                "front3d_render_side_panel",
            ),
            (
                4,
                self._layers_rect_4d,
                "front4d_render_margin",
                "front4d_render_side_panel",
            ),
        )
        for dimension, area_factory, margin_name, side_panel_name in cases:
            with self.subTest(dimension=dimension):
                with (
                    patch.object(tutorial_overlay.engine_api, margin_name, return_value=20),
                    patch.object(tutorial_overlay.engine_api, side_panel_name, return_value=360),
                ):
                    rect = tutorial_overlay._panel_rect_for_dimension(
                        width=width,
                        height=height,
                        dimension=dimension,
                        panel_h=panel_h,
                        panel_offset=(-5000, 4000),
                    )
            gameplay_rect = area_factory(width, height, 20, 360)
            self.assertGreaterEqual(rect.left, gameplay_rect.right)
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

    def test_draw_overlay_keychips_panel_stays_inside_screen_for_all_dimensions(
        self,
    ) -> None:
        payload = {
            "running": True,
            "lesson_title": "Tutorial",
            "progress_text": "Step 1/10",
            "segment_title": "Translations",
            "step_text": "Move to target",
            "step_hint": "Use staged key only",
            "highlights": ["target"],
            "key_prompts": ["move_x_neg"],
        }
        fonts = SimpleNamespace(
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 24),
        )
        screen = pygame.Surface((1280, 720))

        def _runtime_groups(dimension: int) -> dict[str, dict[str, tuple[int, ...]]]:
            if dimension == 2:
                return {"game": {"move_x_neg": (pygame.K_LEFT, pygame.K_RIGHT)}}
            return {
                "game": {"move_x_neg": (pygame.K_LEFT, pygame.K_RIGHT)},
                "camera": {"overlay_alpha_dec": (pygame.K_LEFTBRACKET,)},
                "system": {},
            }

        with (
            patch.object(
                tutorial_overlay.engine_api,
                "tutorial_runtime_overlay_payload_runtime",
                return_value=payload,
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "runtime_binding_groups_for_dimension",
                side_effect=_runtime_groups,
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "format_key_tuple",
                return_value="Page Up/Page Down",
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "binding_action_description",
                return_value="Move left",
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "front3d_render_margin",
                return_value=20,
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "front3d_render_side_panel",
                return_value=360,
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "front4d_render_margin",
                return_value=20,
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "front4d_render_side_panel",
                return_value=360,
            ),
        ):
            for dimension in (2, 3, 4):
                tutorial_overlay.draw_tutorial_overlay(
                    screen,
                    fonts,
                    dimension=dimension,
                    tutorial_session=object(),
                )
                rect = tutorial_overlay.tutorial_panel_last_rect(dimension)
                self.assertIsNotNone(rect)
                assert rect is not None
                self.assertGreaterEqual(rect.left, 0)
                self.assertGreaterEqual(rect.top, 0)
                self.assertLessEqual(rect.right, screen.get_width())
                self.assertLessEqual(rect.bottom, screen.get_height())


if __name__ == "__main__":
    unittest.main()
