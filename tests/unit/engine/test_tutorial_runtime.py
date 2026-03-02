from __future__ import annotations

import unittest
from unittest.mock import patch

from tet4d.engine.tutorial.runtime import create_tutorial_runtime_session


class TutorialRuntimeTests(unittest.TestCase):
    def test_runtime_session_progression_2d(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_2d_core",
                mode="2d",
            )
            self.assertTrue(session.is_running())
            self.assertTrue(session.action_allowed("move_x_neg"))
            self.assertFalse(session.action_allowed("rotate_xy_pos"))

            session.observe_action("move_x_neg")
            self.assertFalse(session.sync_and_advance(lines_cleared=0))
            session.observe_action("move_x_pos")
            self.assertFalse(session.sync_and_advance(lines_cleared=0))
            session.observe_action("soft_drop")
            self.assertFalse(session.sync_and_advance(lines_cleared=0))
            session.observe_action("hard_drop")
            self.assertTrue(session.sync_and_advance(lines_cleared=0))

            payload = session.overlay_payload()
            self.assertTrue(payload["running"])
            self.assertEqual(payload["step_id"], "rotate_xy")
            self.assertIsInstance(payload.get("highlights"), list)

            session.observe_action("rotate_xy_pos")
            self.assertFalse(session.sync_and_advance(lines_cleared=0))
            session.observe_action("rotate_xy_neg")
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            payload = session.overlay_payload()
            self.assertEqual(payload["step_id"], "clear_line")

            self.assertTrue(session.sync_and_advance(lines_cleared=1))
            payload = session.overlay_payload()
            self.assertFalse(payload["running"])
            self.assertEqual(payload["status"], "completed")
            self.assertFalse(session.is_running())

    def test_runtime_restart_and_skip(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_3d_core",
                mode="3d",
            )
            self.assertTrue(session.skip())
            self.assertEqual(session.overlay_payload()["status"], "skipped")
            self.assertFalse(session.restart())

            session = create_tutorial_runtime_session(
                lesson_id="tutorial_3d_core",
                mode="3d",
            )
            self.assertTrue(session.restart())
            self.assertEqual(session.overlay_payload()["step_id"], "camera_controls")

    def test_pending_setup_lifecycle(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_2d_core",
                mode="2d",
            )
            initial_setup = session.consume_pending_setup()
            self.assertIsNotNone(initial_setup)
            assert initial_setup is not None
            self.assertEqual(initial_setup.get("step_id"), "move_xy")
            self.assertIsNone(session.consume_pending_setup())

            session.observe_action("move_x_neg")
            session.observe_action("move_x_pos")
            session.observe_action("soft_drop")
            session.observe_action("hard_drop")
            self.assertTrue(session.sync_and_advance(lines_cleared=0))

            next_setup = session.consume_pending_setup()
            self.assertIsNotNone(next_setup)
            assert next_setup is not None
            self.assertEqual(next_setup.get("step_id"), "rotate_xy")
            self.assertIsNone(session.consume_pending_setup())

            self.assertTrue(session.restart())
            restarted_setup = session.consume_pending_setup()
            self.assertIsNotNone(restarted_setup)
            assert restarted_setup is not None
            self.assertEqual(restarted_setup.get("step_id"), "move_xy")


if __name__ == "__main__":
    unittest.main()
