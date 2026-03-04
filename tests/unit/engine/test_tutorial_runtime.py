from __future__ import annotations

import unittest
from unittest.mock import patch

from tet4d.engine.tutorial.runtime import create_tutorial_runtime_session


class TutorialRuntimeTests(unittest.TestCase):
    _LESSON_CASES = (
        ("tutorial_2d_core", "2d"),
        ("tutorial_3d_core", "3d"),
        ("tutorial_4d_core", "4d"),
    )

    @staticmethod
    def _complete_step_with_repeats(session: object, action_id: str, repeats: int = 4) -> bool:
        for _ in range(max(1, repeats)):
            session.observe_action(action_id)
        return bool(session.sync_and_advance(lines_cleared=0))

    def test_runtime_session_progression_2d(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
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
            payload = session.overlay_payload()
            self.assertEqual(payload.get("segment_title"), "Translations")
            self.assertIn("System controls", str(payload.get("system_controls_text", "")))

            self.assertTrue(self._complete_step_with_repeats(session, "move_x_neg"))
            payload = session.overlay_payload()
            self.assertEqual(payload["step_id"], "move_x_pos")

            self.assertTrue(self._complete_step_with_repeats(session, "move_x_pos"))
            payload = session.overlay_payload()
            self.assertTrue(payload["running"])
            self.assertEqual(payload["step_id"], "soft_drop")
            self.assertIsInstance(payload.get("highlights"), list)

    def test_runtime_restart_and_skip(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
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
            self.assertEqual(session.overlay_payload()["step_id"], "move_x_neg")

    def test_pending_setup_lifecycle(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
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
            self.assertEqual(initial_setup.get("step_id"), "move_x_neg")
            self.assertIsNone(session.consume_pending_setup())

            self.assertTrue(self._complete_step_with_repeats(session, "move_x_neg"))

            next_setup = session.consume_pending_setup()
            self.assertIsNotNone(next_setup)
            assert next_setup is not None
            self.assertEqual(next_setup.get("step_id"), "move_x_pos")
            self.assertIsNone(session.consume_pending_setup())

            self.assertTrue(session.restart())
            restarted_setup = session.consume_pending_setup()
            self.assertIsNotNone(restarted_setup)
            assert restarted_setup is not None
            self.assertEqual(restarted_setup.get("step_id"), "move_x_neg")

    def test_redo_stage_restarts_current_step(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_2d_core",
                mode="2d",
            )
            session.consume_pending_setup()
            self.assertTrue(self._complete_step_with_repeats(session, "move_x_neg"))
            self.assertEqual(session.overlay_payload()["step_id"], "move_x_pos")

            self.assertTrue(session.redo_stage())
            redo_setup = session.consume_pending_setup()
            self.assertIsNotNone(redo_setup)
            assert redo_setup is not None
            self.assertEqual(redo_setup.get("step_id"), "move_x_pos")

    def test_allowed_actions_reflect_current_step_gate(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_2d_core",
                mode="2d",
            )
            self.assertIn("move_x_neg", session.allowed_actions())
            self.assertTrue(self._complete_step_with_repeats(session, "move_x_neg"))
            self.assertIn("move_x_pos", session.allowed_actions())

    def test_soft_drop_is_always_allowed(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_2d_core",
                mode="2d",
            )
            self.assertTrue(session.action_allowed("soft_drop"))

    def test_sync_supports_board_cell_count_predicate_input(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_2d_core",
                mode="2d",
            )
            progressed = session.sync_and_advance(
                lines_cleared=0,
                board_cell_count=0,
            )
            self.assertFalse(progressed)

    def test_step_transition_waits_for_configured_delay(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 1000),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_2d_core",
                mode="2d",
            )
            for _ in range(4):
                session.observe_action("move_x_neg")
            with patch("tet4d.engine.tutorial.runtime._now_ms", return_value=100):
                self.assertFalse(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload()["step_id"], "move_x_neg")
            self.assertIn("Next stage in 1s", session.overlay_payload()["status_message"])

            with patch("tet4d.engine.tutorial.runtime._now_ms", return_value=1099):
                self.assertFalse(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload()["step_id"], "move_x_neg")

            with patch("tet4d.engine.tutorial.runtime._now_ms", return_value=1100):
                self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload()["step_id"], "move_x_pos")

    def test_4d_w_axis_stages_progress_in_order(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_4d_core",
                mode="4d",
            )
            guard = 0
            while session.overlay_payload().get("step_id") != "move_w_neg":
                moved = session.next_stage()
                self.assertTrue(moved)
                guard += 1
                self.assertLess(guard, 200)

            self.assertEqual(session.required_action(), "move_w_neg")
            self.assertTrue(session.action_allowed("move_w_neg"))
            self.assertFalse(session.action_allowed("move_w_pos"))
            for _ in range(4):
                session.observe_action("move_w_neg")
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload()["step_id"], "move_w_pos")

            self.assertEqual(session.required_action(), "move_w_pos")
            self.assertTrue(session.action_allowed("move_w_pos"))
            self.assertFalse(session.action_allowed("move_w_neg"))
            for _ in range(4):
                session.observe_action("move_w_pos")
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload()["step_id"], "soft_drop")

    def test_restart_redo_prev_next_sequencing_is_deterministic_all_modes(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            for lesson_id, mode in self._LESSON_CASES:
                session = create_tutorial_runtime_session(
                    lesson_id=lesson_id,
                    mode=mode,
                )
                self.assertEqual(session.overlay_payload()["step_id"], "move_x_neg")
                self.assertEqual(session.required_action(), "move_x_neg")
                self.assertIsNotNone(session.consume_pending_setup())
                self.assertIsNone(session.consume_pending_setup())

                self.assertTrue(session.next_stage())
                self.assertEqual(session.overlay_payload()["step_id"], "move_x_pos")
                self.assertEqual(session.required_action(), "move_x_pos")
                self.assertIsNotNone(session.consume_pending_setup())

                self.assertTrue(session.previous_stage())
                self.assertEqual(session.overlay_payload()["step_id"], "move_x_neg")
                self.assertEqual(session.required_action(), "move_x_neg")
                self.assertIsNotNone(session.consume_pending_setup())

                self.assertTrue(session.redo_stage())
                self.assertEqual(session.overlay_payload()["step_id"], "move_x_neg")
                self.assertEqual(session.required_action(), "move_x_neg")
                self.assertIsNotNone(session.consume_pending_setup())

                self.assertTrue(session.restart())
                self.assertEqual(session.overlay_payload()["step_id"], "move_x_neg")
                self.assertEqual(session.required_action(), "move_x_neg")
                self.assertIsNotNone(session.consume_pending_setup())

    def test_4d_w_axis_progression_is_stable_across_restarts(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_4d_core",
                mode="4d",
            )
            for _ in range(3):
                self.assertTrue(session.restart())
                guard = 0
                while session.overlay_payload().get("step_id") != "move_w_neg":
                    self.assertTrue(session.next_stage())
                    guard += 1
                    self.assertLess(guard, 200)
                self.assertIsNotNone(session.consume_pending_setup())

                for _ in range(4):
                    session.observe_action("move_w_neg")
                self.assertTrue(session.sync_and_advance(lines_cleared=0))
                self.assertEqual(session.overlay_payload()["step_id"], "move_w_pos")

                for _ in range(4):
                    session.observe_action("move_w_pos")
                self.assertTrue(session.sync_and_advance(lines_cleared=0))
                self.assertEqual(session.overlay_payload()["step_id"], "soft_drop")

    def test_step_transition_delay_respects_nonzero_duration(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 1500),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_2d_core",
                mode="2d",
            )
            for _ in range(4):
                session.observe_action("move_x_neg")
            with patch("tet4d.engine.tutorial.runtime._now_ms", return_value=100):
                self.assertFalse(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload()["step_id"], "move_x_neg")

            with patch("tet4d.engine.tutorial.runtime._now_ms", return_value=1599):
                self.assertFalse(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload()["step_id"], "move_x_neg")

            with patch("tet4d.engine.tutorial.runtime._now_ms", return_value=1600):
                self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertEqual(session.overlay_payload()["step_id"], "move_x_pos")


if __name__ == "__main__":
    unittest.main()
