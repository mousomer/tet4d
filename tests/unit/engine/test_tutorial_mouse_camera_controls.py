from __future__ import annotations

import unittest
from unittest.mock import patch

import pygame

from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.ui.pygame import front3d_game, front4d_game


class TutorialMouseCameraControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    @staticmethod
    def _advance_to_step(session: object, step_id: str) -> None:
        guard = 0
        while session.overlay_payload().get("step_id") != step_id:
            moved = session.next_stage()
            if not moved:
                raise AssertionError(f"failed to reach tutorial step: {step_id}")
            guard += 1
            if guard > 240:
                raise AssertionError(f"step navigation guard exceeded for: {step_id}")

    def test_3d_mouse_orbit_and_zoom_steps_progress_from_pointer_events(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            cfg = GameConfigND(dims=(6, 12, 6), gravity_axis=1, speed_level=1)
            loop = front3d_game.LoopContext3D.create(
                cfg,
                tutorial_lesson_id="tutorial_3d_core",
            )
            session = loop.tutorial_session
            self.assertIsNotNone(session)
            assert session is not None

            self._advance_to_step(session, "mouse_orbit")
            loop.pointer_event_handler(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (300, 260)})
            )
            for index in range(4):
                loop.pointer_event_handler(
                    pygame.event.Event(
                        pygame.MOUSEMOTION,
                        {"pos": (306 + index, 260 + index)},
                    )
                )
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "mouse_zoom")

            for _ in range(4):
                loop.pointer_event_handler(
                    pygame.event.Event(pygame.MOUSEWHEEL, {"y": 1})
                )
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "overlay_alpha_dec")

    def test_4d_mouse_orbit_and_zoom_steps_progress_from_pointer_events(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            cfg = GameConfigND(dims=(6, 12, 6, 4), gravity_axis=1, speed_level=1)
            loop = front4d_game.LoopContext4D.create(
                cfg,
                tutorial_lesson_id="tutorial_4d_core",
            )
            session = loop.tutorial_session
            self.assertIsNotNone(session)
            assert session is not None

            self._advance_to_step(session, "mouse_orbit")
            loop.pointer_event_handler(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (320, 280)})
            )
            for index in range(4):
                loop.pointer_event_handler(
                    pygame.event.Event(
                        pygame.MOUSEMOTION,
                        {"pos": (327 + index, 280 + index)},
                    )
                )
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "mouse_zoom")

            for _ in range(4):
                loop.pointer_event_handler(
                    pygame.event.Event(pygame.MOUSEWHEEL, {"y": -1})
                )
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "overlay_alpha_dec")


if __name__ == "__main__":
    unittest.main()
