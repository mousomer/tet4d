from __future__ import annotations

import unittest

from tet4d.engine import api as engine_api
from tet4d.engine.ui_logic.keybindings_catalog import binding_action_ids
from tet4d.engine.tutorial import content


class TutorialContentTests(unittest.TestCase):
    def setUp(self) -> None:
        content.clear_tutorial_content_cache()

    def tearDown(self) -> None:
        content.clear_tutorial_content_cache()

    def test_lessons_file_loads(self) -> None:
        payload = content.load_tutorial_payload()
        self.assertEqual(payload.schema_version, 1)
        lesson_ids = {lesson.lesson_id for lesson in payload.lessons}
        self.assertIn("tutorial_2d_core", lesson_ids)
        self.assertIn("tutorial_3d_core", lesson_ids)
        self.assertIn("tutorial_4d_core", lesson_ids)

    def test_api_exposes_tutorial_payload(self) -> None:
        payload = engine_api.tutorial_lessons_payload_runtime()
        lesson_ids = engine_api.tutorial_lesson_ids_runtime()
        self.assertEqual(payload["schema_version"], 1)
        self.assertTrue(any(lesson_id == "tutorial_2d_core" for lesson_id in lesson_ids))
        self.assertTrue(any(lesson_id == "tutorial_3d_core" for lesson_id in lesson_ids))
        self.assertTrue(any(lesson_id == "tutorial_4d_core" for lesson_id in lesson_ids))

    def test_lessons_cover_expected_movement_rotation_and_camera_actions(self) -> None:
        payload = content.load_tutorial_payload()
        lessons = {lesson.lesson_id: lesson for lesson in payload.lessons}

        def _event_set(lesson_id: str) -> set[str]:
            lesson = lessons[lesson_id]
            return {
                event
                for step in lesson.steps
                for event in step.complete_when.events
            }

        expected_2d = {
            "move_x_neg",
            "move_x_pos",
            "soft_drop",
            "hard_drop",
            "rotate_xy_pos",
            "rotate_xy_neg",
        }
        expected_3d = expected_2d | {
            "move_z_neg",
            "move_z_pos",
            "rotate_xz_pos",
            "rotate_xz_neg",
            "rotate_yz_pos",
            "rotate_yz_neg",
            "yaw_fine_neg",
            "yaw_neg",
            "yaw_pos",
            "yaw_fine_pos",
            "pitch_neg",
            "pitch_pos",
            "zoom_in",
            "zoom_out",
            "cycle_projection",
            "reset",
        }
        expected_4d = expected_3d | {
            "move_w_neg",
            "move_w_pos",
            "rotate_xw_pos",
            "rotate_xw_neg",
            "rotate_yw_pos",
            "rotate_yw_neg",
            "rotate_zw_pos",
            "rotate_zw_neg",
            "view_xw_neg",
            "view_xw_pos",
            "view_zw_neg",
            "view_zw_pos",
        }

        self.assertTrue(expected_2d.issubset(_event_set("tutorial_2d_core")))
        self.assertTrue(expected_3d.issubset(_event_set("tutorial_3d_core")))
        self.assertTrue(expected_4d.issubset(_event_set("tutorial_4d_core")))

    def test_key_prompt_and_gating_actions_are_known(self) -> None:
        known = set(binding_action_ids()) | {"menu", "help", "restart", "quit"}
        payload = content.load_tutorial_payload()
        for lesson in payload.lessons:
            for step in lesson.steps:
                for action in step.ui.key_prompts:
                    self.assertIn(action, known)
                for action in step.gating.allow:
                    self.assertIn(action, known)
                for action in step.gating.deny:
                    self.assertIn(action, known)


if __name__ == "__main__":
    unittest.main()
