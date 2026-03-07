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
        current_ms = {"value": 0}
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
            patch(
                "tet4d.engine.tutorial.manager._now_ms",
                side_effect=lambda: current_ms["value"],
            ),
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
            for index, time_ms in enumerate((0, 700, 1400, 2100)):
                current_ms["value"] = time_ms
                loop.pointer_event_handler(
                    pygame.event.Event(
                        pygame.MOUSEMOTION,
                        {"pos": (306 + (index * 8), 260 + (index * 7))},
                    )
                )
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "mouse_zoom")

            for index, time_ms in enumerate((2200, 2900, 3600, 4300)):
                current_ms["value"] = time_ms
                loop.pointer_event_handler(
                    pygame.event.Event(pygame.MOUSEWHEEL, {"y": 1 if index % 2 == 0 else -1})
                )
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "zoom_in")

    def test_4d_mouse_orbit_and_zoom_steps_progress_from_pointer_events(self) -> None:
        current_ms = {"value": 0}
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
            patch(
                "tet4d.engine.tutorial.manager._now_ms",
                side_effect=lambda: current_ms["value"],
            ),
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
            for index, time_ms in enumerate((0, 700, 1400, 2100)):
                current_ms["value"] = time_ms
                loop.pointer_event_handler(
                    pygame.event.Event(
                        pygame.MOUSEMOTION,
                        {"pos": (327 + (index * 7), 280 + (index * 6))},
                    )
                )
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "mouse_zoom")

            for index, time_ms in enumerate((2200, 2900, 3600, 4300)):
                current_ms["value"] = time_ms
                loop.pointer_event_handler(
                    pygame.event.Event(pygame.MOUSEWHEEL, {"y": -1 if index % 2 == 0 else 1})
                )
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "toggle_grid")

    def test_3d_mouse_orbit_requires_fresh_drag_after_gate_opens(self) -> None:
        current_ms = {"value": 0}
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
            patch(
                "tet4d.engine.tutorial.manager._now_ms",
                side_effect=lambda: current_ms["value"],
            ),
        ):
            cfg = GameConfigND(dims=(6, 12, 6), gravity_axis=1, speed_level=1)
            loop = front3d_game.LoopContext3D.create(
                cfg,
                tutorial_lesson_id="tutorial_3d_core",
            )
            session = loop.tutorial_session
            self.assertIsNotNone(session)
            assert session is not None

            start_yaw = float(loop.camera.yaw_deg)
            start_pitch = float(loop.camera.pitch_deg)
            self.assertFalse(session.action_allowed("mouse_orbit"))
            loop.pointer_event_handler(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (260, 220)})
            )
            current_ms["value"] = 400
            loop.pointer_event_handler(
                pygame.event.Event(pygame.MOUSEMOTION, {"pos": (320, 280)})
            )
            self.assertFalse(loop.mouse_orbit.dragging)
            self.assertIsNone(loop.mouse_orbit.last_pos)
            self.assertEqual(float(loop.camera.yaw_deg), start_yaw)
            self.assertEqual(float(loop.camera.pitch_deg), start_pitch)

            self._advance_to_step(session, "mouse_orbit")
            current_ms["value"] = 900
            loop.pointer_event_handler(
                pygame.event.Event(pygame.MOUSEMOTION, {"pos": (330, 290)})
            )
            self.assertFalse(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "mouse_orbit")

            loop.pointer_event_handler(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (330, 290)})
            )
            for index, time_ms in enumerate((1000, 1600, 2200, 3100)):
                current_ms["value"] = time_ms
                loop.pointer_event_handler(
                    pygame.event.Event(
                        pygame.MOUSEMOTION,
                        {"pos": (344 + (index * 6), 300 + (index * 5))},
                    )
                )
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "mouse_zoom")

    def test_4d_mouse_orbit_requires_fresh_drag_after_gate_opens(self) -> None:
        current_ms = {"value": 0}
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
            patch(
                "tet4d.engine.tutorial.manager._now_ms",
                side_effect=lambda: current_ms["value"],
            ),
        ):
            cfg = GameConfigND(dims=(6, 12, 6, 4), gravity_axis=1, speed_level=1)
            loop = front4d_game.LoopContext4D.create(
                cfg,
                tutorial_lesson_id="tutorial_4d_core",
            )
            session = loop.tutorial_session
            self.assertIsNotNone(session)
            assert session is not None

            start_yaw = float(loop.view.yaw_deg)
            start_pitch = float(loop.view.pitch_deg)
            self.assertFalse(session.action_allowed("mouse_orbit"))
            loop.pointer_event_handler(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (280, 240)})
            )
            current_ms["value"] = 400
            loop.pointer_event_handler(
                pygame.event.Event(pygame.MOUSEMOTION, {"pos": (340, 300)})
            )
            self.assertFalse(loop.mouse_orbit.dragging)
            self.assertIsNone(loop.mouse_orbit.last_pos)
            self.assertEqual(float(loop.view.yaw_deg), start_yaw)
            self.assertEqual(float(loop.view.pitch_deg), start_pitch)

            self._advance_to_step(session, "mouse_orbit")
            current_ms["value"] = 900
            loop.pointer_event_handler(
                pygame.event.Event(pygame.MOUSEMOTION, {"pos": (350, 310)})
            )
            self.assertFalse(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "mouse_orbit")

            loop.pointer_event_handler(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (350, 310)})
            )
            for index, time_ms in enumerate((1000, 1600, 2200, 3100)):
                current_ms["value"] = time_ms
                loop.pointer_event_handler(
                    pygame.event.Event(
                        pygame.MOUSEMOTION,
                        {"pos": (362 + (index * 6), 320 + (index * 5))},
                    )
                )
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "mouse_zoom")

    def test_3d_mouse_zoom_requires_actual_zoom_change(self) -> None:
        current_ms = {"value": 0}
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
            patch(
                "tet4d.engine.tutorial.manager._now_ms",
                side_effect=lambda: current_ms["value"],
            ),
        ):
            cfg = GameConfigND(dims=(6, 12, 6), gravity_axis=1, speed_level=1)
            loop = front3d_game.LoopContext3D.create(
                cfg,
                tutorial_lesson_id="tutorial_3d_core",
            )
            session = loop.tutorial_session
            self.assertIsNotNone(session)
            assert session is not None

            self._advance_to_step(session, "mouse_zoom")
            loop.camera.zoom = 140.0
            current_ms["value"] = 500
            loop.pointer_event_handler(
                pygame.event.Event(pygame.MOUSEWHEEL, {"y": 1})
            )
            self.assertFalse(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "mouse_zoom")
            self.assertEqual(float(loop.camera.zoom), 140.0)

            for index, time_ms in enumerate((1000, 1700, 2400, 3100)):
                current_ms["value"] = time_ms
                loop.pointer_event_handler(
                    pygame.event.Event(pygame.MOUSEWHEEL, {"y": -1 if index % 2 == 0 else 1})
                )
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "zoom_in")

    def test_4d_mouse_zoom_requires_actual_zoom_change(self) -> None:
        current_ms = {"value": 0}
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
            patch(
                "tet4d.engine.tutorial.manager._now_ms",
                side_effect=lambda: current_ms["value"],
            ),
        ):
            cfg = GameConfigND(dims=(6, 12, 6, 4), gravity_axis=1, speed_level=1)
            loop = front4d_game.LoopContext4D.create(
                cfg,
                tutorial_lesson_id="tutorial_4d_core",
            )
            session = loop.tutorial_session
            self.assertIsNotNone(session)
            assert session is not None

            self._advance_to_step(session, "mouse_zoom")
            loop.view.zoom_scale = 2.6
            current_ms["value"] = 500
            loop.pointer_event_handler(
                pygame.event.Event(pygame.MOUSEWHEEL, {"y": 1})
            )
            self.assertFalse(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "mouse_zoom")
            self.assertEqual(float(loop.view.zoom_scale), 2.6)

            for index, time_ms in enumerate((1000, 1700, 2400, 3100)):
                current_ms["value"] = time_ms
                loop.pointer_event_handler(
                    pygame.event.Event(pygame.MOUSEWHEEL, {"y": -1 if index % 2 == 0 else 1})
                )
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload().get("step_id"), "toggle_grid")


if __name__ == "__main__":
    unittest.main()
