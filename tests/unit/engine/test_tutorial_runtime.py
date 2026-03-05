from __future__ import annotations

import unittest
from unittest.mock import patch

from tet4d.engine.runtime.settings_schema import (
    OVERLAY_TRANSPARENCY_MAX,
    OVERLAY_TRANSPARENCY_MIN,
)
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

    @staticmethod
    def _assert_no_board_reset_fields(setup: dict[str, object]) -> None:
        forbidden = {
            "spawn_piece",
            "starter_piece_id",
            "board_preset",
            "rng_seed",
            "spawn_min_visible_layer",
            "bottom_layers_min",
            "bottom_layers_max",
        }
        for key in forbidden:
            if key in setup:
                raise AssertionError(f"unexpected board reset field in setup: {key}")

    @staticmethod
    def _complete_control_step(session: object, step_id: str) -> bool:
        step = session.manager.current_step()
        repeats = max(1, int(step.complete_when.event_count_required))
        action_id = "reset" if step_id == "camera_reset" else step_id
        if step_id == "overlay_alpha_dec":
            session.observe_action(action_id)
            target_percent = step.setup.overlay_target_percent
            if not isinstance(target_percent, int):
                target_percent = int(round(float(OVERLAY_TRANSPARENCY_MIN) * 100.0))
            target_percent = max(0, min(100, int(target_percent)))
            return bool(
                session.sync_and_advance(
                    lines_cleared=0,
                    overlay_transparency=float(target_percent) / 100.0,
                )
            )
        if step_id == "overlay_alpha_inc":
            session.observe_action(action_id)
            target_percent = step.setup.overlay_target_percent
            if not isinstance(target_percent, int):
                target_percent = int(round(float(OVERLAY_TRANSPARENCY_MAX) * 100.0))
            target_percent = max(0, min(100, int(target_percent)))
            return bool(
                session.sync_and_advance(
                    lines_cleared=0,
                    overlay_transparency=float(target_percent) / 100.0,
                )
            )
        for _ in range(repeats):
            session.observe_action(action_id)
        return bool(session.sync_and_advance(lines_cleared=0))

    def _assert_nd_control_sequence_has_no_board_reset(
        self,
        *,
        lesson_id: str,
        mode: str,
        step_sequence: tuple[str, ...],
    ) -> None:
        session = create_tutorial_runtime_session(
            lesson_id=lesson_id,
            mode=mode,
        )
        first_setup = session.consume_pending_setup()
        self.assertIsNotNone(first_setup)
        assert first_setup is not None
        self.assertIn("starter_piece_id", first_setup.get("setup", {}))
        for index in range(len(step_sequence) - 1):
            current_step = step_sequence[index]
            expected_next = step_sequence[index + 1]
            self.assertEqual(session.overlay_payload().get("step_id"), current_step)
            self.assertTrue(self._complete_control_step(session, current_step))
            next_setup = session.consume_pending_setup()
            self.assertIsNotNone(next_setup)
            assert next_setup is not None
            self.assertEqual(next_setup.get("step_id"), expected_next)
            setup = next_setup.get("setup")
            self.assertIsInstance(setup, dict)
            assert isinstance(setup, dict)
            self._assert_no_board_reset_fields(setup)

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
            self.assertEqual(payload["step_id"], "rotate_xy_pos")
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
            self.assertEqual(next_setup.get("setup"), {})
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
            self.assertTrue(session.completion_ready())
            with patch("tet4d.engine.tutorial.runtime._now_ms", return_value=100):
                self.assertFalse(session.sync_and_advance(lines_cleared=0))
            self.assertTrue(session.transition_pending())
            self.assertEqual(session.overlay_payload()["step_id"], "move_x_neg")
            self.assertIn("Next stage in 1s", session.overlay_payload()["status_message"])

            with patch("tet4d.engine.tutorial.runtime._now_ms", return_value=1099):
                self.assertFalse(session.sync_and_advance(lines_cleared=0))
            self.assertTrue(session.transition_pending())
            self.assertEqual(session.overlay_payload()["step_id"], "move_x_neg")

            with patch("tet4d.engine.tutorial.runtime._now_ms", return_value=1100):
                self.assertTrue(session.sync_and_advance(lines_cleared=0))
            self.assertFalse(session.transition_pending())
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
            self.assertEqual(session.overlay_payload()["step_id"], "rotate_xy_pos")

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
                self.assertEqual(session.overlay_payload()["step_id"], "rotate_xy_pos")

    def test_translation_stage_transition_keeps_continuous_setup_state(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_2d_core",
                mode="2d",
            )
            self.assertIsNotNone(session.consume_pending_setup())
            for _ in range(4):
                session.observe_action("move_x_neg")
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            setup_move_pos = session.consume_pending_setup()
            self.assertIsNotNone(setup_move_pos)
            assert setup_move_pos is not None
            self.assertEqual(setup_move_pos.get("setup"), {})

            for _ in range(4):
                session.observe_action("move_x_pos")
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            setup_rotate = session.consume_pending_setup()
            self.assertIsNotNone(setup_rotate)
            assert setup_rotate is not None
            self.assertEqual(setup_rotate.get("step_id"), "rotate_xy_pos")
            self.assertEqual(setup_rotate.get("setup"), {})

    def test_nd_translation_and_rotation_stages_keep_continuous_setup_state(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_3d_core",
                mode="3d",
            )
            first_setup = session.consume_pending_setup()
            self.assertIsNotNone(first_setup)
            assert first_setup is not None
            self.assertIn("starter_piece_id", first_setup.get("setup", {}))
            for _ in range(4):
                session.observe_action("move_x_neg")
            self.assertTrue(session.sync_and_advance(lines_cleared=0))
            second_setup = session.consume_pending_setup()
            self.assertIsNotNone(second_setup)
            assert second_setup is not None
            self.assertEqual(second_setup.get("setup"), {})

            for action_id, repeats in (
                ("move_x_pos", 4),
                ("move_z_neg", 4),
                ("move_z_pos", 4),
                ("rotate_xy_pos", 4),
                ("rotate_xy_neg", 4),
                ("rotate_xz_pos", 4),
                ("rotate_xz_neg", 4),
                ("rotate_yz_pos", 4),
                ("rotate_yz_neg", 4),
            ):
                for _ in range(repeats):
                    session.observe_action(action_id)
                self.assertTrue(session.sync_and_advance(lines_cleared=0))
                stage_setup = session.consume_pending_setup()
                self.assertIsNotNone(stage_setup)
                assert stage_setup is not None
                self.assertEqual(stage_setup.get("setup"), {})
            self.assertEqual(session.overlay_payload().get("step_id"), "soft_drop")

    def test_4d_translation_to_rotation_keeps_continuous_setup_state(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_4d_core",
                mode="4d",
            )
            first_setup = session.consume_pending_setup()
            self.assertIsNotNone(first_setup)
            assert first_setup is not None
            self.assertIn("starter_piece_id", first_setup.get("setup", {}))

            for action_id, repeats in (
                ("move_x_neg", 4),
                ("move_x_pos", 4),
                ("move_z_neg", 4),
                ("move_z_pos", 4),
                ("move_w_neg", 4),
                ("move_w_pos", 4),
                ("rotate_xy_pos", 4),
                ("rotate_xy_neg", 4),
                ("rotate_xz_pos", 4),
                ("rotate_xz_neg", 4),
                ("rotate_yz_pos", 4),
                ("rotate_yz_neg", 4),
                ("rotate_xw_pos", 4),
                ("rotate_xw_neg", 4),
                ("rotate_yw_pos", 4),
                ("rotate_yw_neg", 4),
                ("rotate_zw_pos", 4),
                ("rotate_zw_neg", 4),
            ):
                for _ in range(repeats):
                    session.observe_action(action_id)
                self.assertTrue(session.sync_and_advance(lines_cleared=0))
                stage_setup = session.consume_pending_setup()
                self.assertIsNotNone(stage_setup)
                assert stage_setup is not None
                self.assertEqual(stage_setup.get("setup"), {})
            self.assertEqual(session.overlay_payload().get("step_id"), "soft_drop")

    def test_3d_control_sequence_has_no_board_reset_until_grid(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            self._assert_nd_control_sequence_has_no_board_reset(
                lesson_id="tutorial_3d_core",
                mode="3d",
                step_sequence=(
                    "move_x_neg",
                    "move_x_pos",
                    "move_z_neg",
                    "move_z_pos",
                    "rotate_xy_pos",
                    "rotate_xy_neg",
                    "rotate_xz_pos",
                    "rotate_xz_neg",
                    "rotate_yz_pos",
                    "rotate_yz_neg",
                    "soft_drop",
                    "hard_drop",
                    "yaw_fine_neg",
                    "yaw_neg",
                    "yaw_pos",
                    "yaw_fine_pos",
                    "pitch_neg",
                    "pitch_pos",
                    "mouse_orbit",
                    "mouse_zoom",
                    "zoom_in",
                    "zoom_out",
                    "camera_reset",
                    "overlay_alpha_dec",
                    "overlay_alpha_inc",
                    "toggle_grid",
                ),
            )

    def test_4d_control_sequence_has_no_board_reset_until_grid(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            self._assert_nd_control_sequence_has_no_board_reset(
                lesson_id="tutorial_4d_core",
                mode="4d",
                step_sequence=(
                    "move_x_neg",
                    "move_x_pos",
                    "move_z_neg",
                    "move_z_pos",
                    "move_w_neg",
                    "move_w_pos",
                    "rotate_xy_pos",
                    "rotate_xy_neg",
                    "rotate_xz_pos",
                    "rotate_xz_neg",
                    "rotate_yz_pos",
                    "rotate_yz_neg",
                    "rotate_xw_pos",
                    "rotate_xw_neg",
                    "rotate_yw_pos",
                    "rotate_yw_neg",
                    "rotate_zw_pos",
                    "rotate_zw_neg",
                    "soft_drop",
                    "hard_drop",
                    "yaw_fine_neg",
                    "yaw_neg",
                    "yaw_pos",
                    "yaw_fine_pos",
                    "pitch_neg",
                    "pitch_pos",
                    "view_xw_neg",
                    "view_xw_pos",
                    "view_zw_neg",
                    "view_zw_pos",
                    "mouse_orbit",
                    "mouse_zoom",
                    "toggle_grid",
                    "zoom_in",
                    "zoom_out",
                    "camera_reset",
                    "overlay_alpha_dec",
                    "overlay_alpha_inc",
                ),
            )

    def test_mouse_camera_steps_require_mouse_events(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            for lesson_id, mode in (("tutorial_3d_core", "3d"), ("tutorial_4d_core", "4d")):
                session = create_tutorial_runtime_session(
                    lesson_id=lesson_id,
                    mode=mode,
                )
                while session.overlay_payload().get("step_id") != "mouse_orbit":
                    self.assertTrue(session.next_stage())
                self.assertIsNotNone(session.consume_pending_setup())

                self.assertTrue(session.action_allowed("mouse_orbit"))
                self.assertFalse(session.action_allowed("yaw_pos"))
                self.assertFalse(session.action_allowed("pitch_pos"))
                session.observe_action("yaw_pos")
                self.assertFalse(session.sync_and_advance(lines_cleared=0))
                session.observe_action("pitch_pos")
                self.assertFalse(session.sync_and_advance(lines_cleared=0))
                session.observe_action("mouse_orbit")
                self.assertTrue(session.sync_and_advance(lines_cleared=0))
                self.assertEqual(session.overlay_payload().get("step_id"), "mouse_zoom")

                self.assertIsNotNone(session.consume_pending_setup())
                self.assertTrue(session.action_allowed("mouse_zoom"))
                self.assertFalse(session.action_allowed("zoom_in"))
                self.assertFalse(session.action_allowed("zoom_out"))
                session.observe_action("zoom_in")
                self.assertFalse(session.sync_and_advance(lines_cleared=0))
                session.observe_action("zoom_out")
                self.assertFalse(session.sync_and_advance(lines_cleared=0))
                session.observe_action("mouse_zoom")
                self.assertTrue(session.sync_and_advance(lines_cleared=0))
                expected_next = "zoom_in" if mode == "3d" else "toggle_grid"
                self.assertEqual(session.overlay_payload().get("step_id"), expected_next)

    def test_overlay_stage_completion_uses_declared_exact_target(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime._overlay_range", return_value=(5, 77)),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_2d_core",
                mode="2d",
            )
            while session.overlay_payload().get("step_id") != "overlay_alpha_dec":
                self.assertTrue(session.next_stage())
            setup = session.consume_pending_setup()
            self.assertIsNotNone(setup)
            assert setup is not None
            self.assertEqual(
                setup.get("setup", {}).get("overlay_start_percent"),
                50,
            )
            self.assertFalse(
                session.sync_and_advance(lines_cleared=0, overlay_transparency=0.25)
            )
            session.observe_action("overlay_alpha_dec")
            self.assertTrue(
                session.sync_and_advance(lines_cleared=0, overlay_transparency=0.05)
            )
            self.assertEqual(session.overlay_payload().get("step_id"), "overlay_alpha_inc")
            self.assertIn("Goal: 77%", session.overlay_payload().get("step_hint", ""))
            session.observe_action("overlay_alpha_inc")
            self.assertTrue(
                session.sync_and_advance(lines_cleared=0, overlay_transparency=0.77)
            )

    def test_overlay_stages_reset_transparency_to_midpoint_for_following_stage(self) -> None:
        with (
            patch("tet4d.engine.tutorial.runtime._TUTORIAL_STAGE_DELAY_MS", 0),
            patch("tet4d.engine.tutorial.runtime._overlay_range", return_value=(0, 90)),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_started"),
            patch("tet4d.engine.tutorial.runtime.mark_tutorial_lesson_completed"),
        ):
            session = create_tutorial_runtime_session(
                lesson_id="tutorial_2d_core",
                mode="2d",
            )
            while session.overlay_payload().get("step_id") != "overlay_alpha_inc":
                self.assertTrue(session.next_stage())
                self.assertIsNotNone(session.consume_pending_setup())
            session.observe_action("overlay_alpha_inc")
            self.assertTrue(
                session.sync_and_advance(lines_cleared=0, overlay_transparency=0.90)
            )
            self.assertEqual(session.overlay_payload().get("step_id"), "line_fill")
            next_setup = session.consume_pending_setup()
            self.assertIsNotNone(next_setup)
            assert next_setup is not None
            self.assertEqual(
                next_setup.get("setup", {}).get("overlay_start_percent"),
                50,
            )

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
