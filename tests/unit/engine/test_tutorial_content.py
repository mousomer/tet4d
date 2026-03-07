from __future__ import annotations

import unittest

from tet4d.engine import api as engine_api
from tet4d.engine.gameplay.pieces2d import PIECE_SET_2D_CLASSIC, get_piece_bag_2d
from tet4d.engine.gameplay.pieces_nd import (
    PIECE_SET_3D_STANDARD,
    PIECE_SET_4D_STANDARD,
    get_piece_shapes_nd,
)
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
        self.assertEqual(payload.board_profiles.dims_2d, (10, 20))
        self.assertEqual(payload.board_profiles.dims_3d, (6, 18, 6))
        self.assertEqual(payload.board_profiles.dims_4d, (10, 20, 6, 6))
        lesson_ids = {lesson.lesson_id for lesson in payload.lessons}
        self.assertIn("tutorial_2d_core", lesson_ids)
        self.assertIn("tutorial_3d_core", lesson_ids)
        self.assertIn("tutorial_4d_core", lesson_ids)

    def test_api_exposes_tutorial_payload(self) -> None:
        payload = engine_api.tutorial_lessons_payload_runtime()
        lesson_ids = engine_api.tutorial_lesson_ids_runtime()
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["board_profiles"]["2d"], {"width": 10, "height": 20})
        self.assertEqual(payload["board_profiles"]["3d"], {"x": 6, "y": 18, "z": 6})
        self.assertEqual(payload["board_profiles"]["4d"], {"x": 10, "y": 20, "z": 6, "w": 6})
        self.assertTrue(any(lesson_id == "tutorial_2d_core" for lesson_id in lesson_ids))
        self.assertTrue(any(lesson_id == "tutorial_3d_core" for lesson_id in lesson_ids))
        self.assertTrue(any(lesson_id == "tutorial_4d_core" for lesson_id in lesson_ids))

    def test_api_exposes_tutorial_board_dims_runtime(self) -> None:
        self.assertEqual(engine_api.tutorial_board_dims_runtime("2d"), (10, 20))
        self.assertEqual(engine_api.tutorial_board_dims_runtime("3d"), (6, 18, 6))
        self.assertEqual(engine_api.tutorial_board_dims_runtime("4d"), (10, 20, 6, 6))

    def test_tutorial_plan_file_loads(self) -> None:
        payload = content.load_tutorial_plan_payload()
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["plan_id"], "interactive_tutorials_v1")
        self.assertGreaterEqual(len(payload["stages"]), 1)

    def test_api_exposes_tutorial_plan_payload(self) -> None:
        payload = engine_api.tutorial_plan_payload_runtime()
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["plan_id"], "interactive_tutorials_v1")
        self.assertGreaterEqual(len(payload["stages"]), 1)

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
            "toggle_grid",
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
            "mouse_orbit",
            "mouse_zoom",
            "zoom_in",
            "zoom_out",
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
        known = set(binding_action_ids()) | {
            "menu",
            "help",
            "restart",
            "quit",
            "mouse_orbit",
            "mouse_zoom",
        }
        payload = content.load_tutorial_payload()
        for lesson in payload.lessons:
            for step in lesson.steps:
                for action in step.ui.key_prompts:
                    self.assertIn(action, known)
                for action in step.gating.allow:
                    self.assertIn(action, known)
                for action in step.gating.deny:
                    self.assertIn(action, known)

    def test_plan_actions_and_order_are_valid(self) -> None:
        known = set(binding_action_ids()) | {
            "menu",
            "help",
            "restart",
            "quit",
            "mouse_orbit",
            "mouse_zoom",
        }
        payload = content.load_tutorial_plan_payload()
        stages = payload["stages"]
        self.assertGreaterEqual(len(stages), 1)
        last_order = 0
        for stage in stages:
            order = int(stage["order"])
            self.assertGreater(order, last_order)
            last_order = order
            action = stage.get("action_id")
            if action:
                self.assertIn(action, known)

    def test_board_goal_steps_require_clear_predicates(self) -> None:
        payload = content.load_tutorial_payload()
        lessons = {lesson.lesson_id: lesson for lesson in payload.lessons}
        expected_predicates = {
            "tutorial_2d_core": ("line_cleared",),
            "tutorial_3d_core": ("layer_cleared",),
            "tutorial_4d_core": ("hyper_layer_cleared",),
        }
        for lesson_id, expected in expected_predicates.items():
            lesson = lessons[lesson_id]
            target_step = next(
                step for step in lesson.steps if step.step_id == "target_drop"
            )
            self.assertEqual(target_step.complete_when.predicates, expected)

    def test_system_control_stages_are_non_interactive_guidance_only(self) -> None:
        payload = content.load_tutorial_payload()
        for lesson in payload.lessons:
            step_ids = {step.step_id for step in lesson.steps}
            self.assertNotIn("menu_button", step_ids)
            self.assertNotIn("help_button", step_ids)
            self.assertNotIn("restart_button", step_ids)

    def test_move_and_rotation_stages_require_four_actions(self) -> None:
        camera_rotation_ids = {
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
        }
        camera_zoom_ids = {
            "zoom_in",
            "zoom_out",
        }
        payload = content.load_tutorial_payload()
        for lesson in payload.lessons:
            for step in lesson.steps:
                if (
                    step.step_id.startswith("move_")
                    or step.step_id.startswith("rotate_")
                    or step.step_id in camera_rotation_ids
                    or step.step_id in camera_zoom_ids
                ):
                    self.assertEqual(step.complete_when.event_count_required, 4)

    def test_mouse_camera_steps_are_mouse_only(self) -> None:
        payload = content.load_tutorial_payload()
        lessons = {lesson.lesson_id: lesson for lesson in payload.lessons}
        for lesson_id in ("tutorial_3d_core", "tutorial_4d_core"):
            lesson = lessons[lesson_id]
            orbit = next(step for step in lesson.steps if step.step_id == "mouse_orbit")
            zoom = next(step for step in lesson.steps if step.step_id == "mouse_zoom")

            self.assertEqual(orbit.complete_when.logic, "all")
            self.assertEqual(orbit.complete_when.events, ("mouse_orbit",))
            self.assertEqual(orbit.complete_when.event_count_required, 4)
            self.assertEqual(orbit.complete_when.event_span_min_ms, 2000)
            self.assertIn("2 seconds", orbit.ui.hint or "")
            self.assertIn("mouse_orbit", orbit.gating.allow)
            self.assertNotIn("yaw_pos", orbit.gating.allow)
            self.assertNotIn("pitch_pos", orbit.gating.allow)
            self.assertNotIn("yaw_neg", orbit.gating.allow)
            self.assertNotIn("pitch_neg", orbit.gating.allow)

            self.assertEqual(zoom.complete_when.logic, "all")
            self.assertEqual(zoom.complete_when.events, ("mouse_zoom",))
            self.assertEqual(zoom.complete_when.event_count_required, 4)
            self.assertEqual(zoom.complete_when.event_span_min_ms, 2000)
            self.assertIn("2 seconds", zoom.ui.hint or "")
            self.assertIn("mouse_zoom", zoom.gating.allow)
            self.assertNotIn("zoom_in", zoom.gating.allow)
            self.assertNotIn("zoom_out", zoom.gating.allow)
            self.assertNotIn("cycle_projection", zoom.gating.allow)

    def test_nd_move_and_rotation_steps_use_asymmetric_starters(self) -> None:
        payload = content.load_tutorial_payload()
        lessons = {lesson.lesson_id: lesson for lesson in payload.lessons}
        expected = {
            "tutorial_3d_core": "SCREW3",
            "tutorial_4d_core": "SKEW4_A",
        }
        for lesson_id, starter_piece in expected.items():
            lesson = lessons[lesson_id]
            for step in lesson.steps:
                if not (
                    step.step_id.startswith("move_")
                    or step.step_id.startswith("rotate_")
                ):
                    continue
                self.assertEqual(step.setup.starter_piece_id, starter_piece)

    def test_layer_clear_steps_use_solvable_board_presets(self) -> None:
        payload = content.load_tutorial_payload()
        lessons = {lesson.lesson_id: lesson for lesson in payload.lessons}
        lesson_3d = lessons["tutorial_3d_core"]
        lesson_4d = lessons["tutorial_4d_core"]
        for step_id in ("target_drop", "layer_fill"):
            step = next(step for step in lesson_3d.steps if step.step_id == step_id)
            self.assertEqual(step.setup.board_preset, "3d_almost_layer_screw3")
        for step_id in ("target_drop", "hyper_layer_fill"):
            step = next(step for step in lesson_4d.steps if step.step_id == step_id)
            self.assertEqual(step.setup.board_preset, "4d_almost_hyper_layer_skew4")

    def test_full_clear_goal_requires_board_cleared_predicate(self) -> None:
        payload = content.load_tutorial_payload()
        for lesson in payload.lessons:
            full_clear_step = next(
                step for step in lesson.steps if step.step_id == "full_clear_bonus"
            )
            self.assertIn("board_cleared", full_clear_step.complete_when.predicates)

    def test_2d_line_and_full_clear_goals_do_not_require_grid_toggle(self) -> None:
        payload = content.load_tutorial_payload()
        lesson_2d = next(
            lesson for lesson in payload.lessons if lesson.lesson_id == "tutorial_2d_core"
        )
        line_fill = next(step for step in lesson_2d.steps if step.step_id == "line_fill")
        full_clear = next(
            step for step in lesson_2d.steps if step.step_id == "full_clear_bonus"
        )
        self.assertNotIn("grid_enabled", line_fill.complete_when.predicates)
        self.assertNotIn("grid_enabled", full_clear.complete_when.predicates)

    def test_2d_line_fill_uses_i_piece_target_preset(self) -> None:
        payload = content.load_tutorial_payload()
        lesson_2d = next(
            lesson for lesson in payload.lessons if lesson.lesson_id == "tutorial_2d_core"
        )
        line_fill = next(step for step in lesson_2d.steps if step.step_id == "line_fill")
        self.assertEqual(line_fill.setup.starter_piece_id, "I")
        self.assertEqual(line_fill.setup.board_preset, "2d_almost_line_i")

    def test_overlay_transparency_stages_have_declared_start_and_targets(self) -> None:
        payload = content.load_tutorial_payload()
        for lesson in payload.lessons:
            dec_step = next(
                step for step in lesson.steps if step.step_id == "overlay_alpha_dec"
            )
            inc_step = next(
                step for step in lesson.steps if step.step_id == "overlay_alpha_inc"
            )
            self.assertEqual(dec_step.setup.overlay_start_percent, 50)
            self.assertIsNone(dec_step.setup.overlay_target_percent)
            self.assertEqual(inc_step.setup.overlay_start_percent, 50)
            self.assertIsNone(inc_step.setup.overlay_target_percent)

    def test_grid_tutorial_step_cycles_all_grid_types(self) -> None:
        payload = content.load_tutorial_payload()
        for lesson in payload.lessons:
            grid_step = next(step for step in lesson.steps if step.step_id == "toggle_grid")
            self.assertEqual(grid_step.complete_when.event_count_required, 4)
            hint = (grid_step.ui.hint or "").lower()
            self.assertIn("edge", hint)
            self.assertIn("full", hint)
            self.assertIn("helper", hint)
            self.assertIn("off", hint)

    def test_nd_control_sequence_order_is_continuous(self) -> None:
        payload = content.load_tutorial_payload()
        lessons = {lesson.lesson_id: lesson for lesson in payload.lessons}

        lesson_2d = lessons["tutorial_2d_core"]
        order_2d = [step.step_id for step in lesson_2d.steps]
        self.assertLess(order_2d.index("move_x_pos"), order_2d.index("rotate_xy_pos"))
        self.assertLess(order_2d.index("rotate_xy_neg"), order_2d.index("soft_drop"))
        self.assertLess(order_2d.index("soft_drop"), order_2d.index("hard_drop"))
        self.assertLess(order_2d.index("toggle_grid"), order_2d.index("overlay_alpha_dec"))
        self.assertLess(
            order_2d.index("overlay_alpha_dec"),
            order_2d.index("overlay_alpha_inc"),
        )
        self.assertLess(order_2d.index("overlay_alpha_inc"), order_2d.index("line_fill"))
        self.assertLess(order_2d.index("line_fill"), order_2d.index("full_clear_bonus"))
        self.assertLess(order_2d.index("full_clear_bonus"), order_2d.index("target_drop"))

        lesson_3d = lessons["tutorial_3d_core"]
        order_3d = [step.step_id for step in lesson_3d.steps]
        translations_3d = (
            "move_x_neg",
            "move_x_pos",
            "move_z_neg",
            "move_z_pos",
        )
        piece_rotations_3d = (
            "rotate_xy_pos",
            "rotate_xy_neg",
            "rotate_xz_pos",
            "rotate_xz_neg",
            "rotate_yz_pos",
            "rotate_yz_neg",
        )
        drop_controls_3d = ("soft_drop", "hard_drop")
        camera_rotations_3d = (
            "yaw_fine_neg",
            "yaw_neg",
            "yaw_pos",
            "yaw_fine_pos",
            "pitch_neg",
            "pitch_pos",
        )
        camera_mouse_3d = (
            "mouse_orbit",
            "mouse_zoom",
        )
        self.assertLess(
            max(order_3d.index(step_id) for step_id in translations_3d),
            min(order_3d.index(step_id) for step_id in piece_rotations_3d),
        )
        self.assertLess(
            max(order_3d.index(step_id) for step_id in piece_rotations_3d),
            min(order_3d.index(step_id) for step_id in drop_controls_3d),
        )
        self.assertLess(
            max(order_3d.index(step_id) for step_id in drop_controls_3d),
            min(order_3d.index(step_id) for step_id in camera_rotations_3d),
        )
        self.assertLess(
            max(order_3d.index(step_id) for step_id in camera_rotations_3d),
            min(order_3d.index(step_id) for step_id in camera_mouse_3d),
        )
        self.assertLess(
            max(order_3d.index(step_id) for step_id in camera_mouse_3d),
            order_3d.index("toggle_grid"),
        )
        camera_controls_3d = (
            "zoom_in",
            "zoom_out",
            "camera_reset",
        )
        self.assertLess(
            max(order_3d.index(step_id) for step_id in camera_controls_3d),
            order_3d.index("toggle_grid"),
        )
        self.assertLess(
            max(order_3d.index(step_id) for step_id in camera_controls_3d),
            order_3d.index("overlay_alpha_dec"),
        )
        self.assertLess(
            order_3d.index("overlay_alpha_dec"),
            order_3d.index("overlay_alpha_inc"),
        )
        self.assertLess(order_3d.index("overlay_alpha_inc"), order_3d.index("toggle_grid"))

        lesson_4d = lessons["tutorial_4d_core"]
        order_4d = [step.step_id for step in lesson_4d.steps]
        translations_4d = (
            "move_x_neg",
            "move_x_pos",
            "move_z_neg",
            "move_z_pos",
            "move_w_neg",
            "move_w_pos",
        )
        piece_rotations_4d = (
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
        )
        drop_controls_4d = ("soft_drop", "hard_drop")
        camera_rotations_4d = (
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
        )
        camera_mouse_4d = (
            "mouse_orbit",
            "mouse_zoom",
        )
        self.assertLess(
            max(order_4d.index(step_id) for step_id in translations_4d),
            min(order_4d.index(step_id) for step_id in piece_rotations_4d),
        )
        self.assertLess(
            max(order_4d.index(step_id) for step_id in piece_rotations_4d),
            min(order_4d.index(step_id) for step_id in drop_controls_4d),
        )
        self.assertLess(
            max(order_4d.index(step_id) for step_id in drop_controls_4d),
            min(order_4d.index(step_id) for step_id in camera_rotations_4d),
        )
        self.assertLess(
            max(order_4d.index(step_id) for step_id in camera_rotations_4d),
            min(order_4d.index(step_id) for step_id in camera_mouse_4d),
        )
        self.assertLess(
            max(order_4d.index(step_id) for step_id in camera_mouse_4d),
            order_4d.index("toggle_grid"),
        )
        camera_controls_4d = (
            "toggle_grid",
            "zoom_in",
            "zoom_out",
            "camera_reset",
        )
        self.assertLess(
            max(order_4d.index(step_id) for step_id in camera_controls_4d),
            order_4d.index("overlay_alpha_dec"),
        )
        self.assertLess(
            order_4d.index("overlay_alpha_dec"),
            order_4d.index("overlay_alpha_inc"),
        )

    def test_starter_piece_ids_match_lesson_dimension(self) -> None:
        piece_ids_by_mode = {
            "2d": {
                shape.name
                for shape in get_piece_bag_2d(
                    PIECE_SET_2D_CLASSIC,
                    board_dims=(10, 20),
                )
            },
            "3d": {
                shape.name
                for shape in get_piece_shapes_nd(
                    3,
                    piece_set_id=PIECE_SET_3D_STANDARD,
                    board_dims=(6, 18, 6),
                )
            },
            "4d": {
                shape.name
                for shape in get_piece_shapes_nd(
                    4,
                    piece_set_id=PIECE_SET_4D_STANDARD,
                    board_dims=(10, 20, 6, 6),
                )
            },
        }
        payload = content.load_tutorial_payload()
        for lesson in payload.lessons:
            allowed_ids = piece_ids_by_mode[lesson.mode]
            for step in lesson.steps:
                starter_piece_id = step.setup.starter_piece_id
                if starter_piece_id is None:
                    continue
                self.assertIn(
                    starter_piece_id,
                    allowed_ids,
                    (
                        "invalid starter piece for lesson mode: "
                        f"{lesson.lesson_id}:{step.step_id} -> {starter_piece_id}"
                    ),
                )


if __name__ == "__main__":
    unittest.main()
