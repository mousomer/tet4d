from __future__ import annotations

import unittest

from tet4d.engine.tutorial.schema import parse_tutorial_payload


def _base_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "lessons": [
            {
                "lesson_id": "lesson_2d",
                "title": "Lesson 2D",
                "mode": "2d",
                "steps": [
                    {
                        "id": "step_move",
                        "ui": {
                            "text": "Move once",
                            "hint": "Use move keys",
                            "highlights": ["piece"],
                            "key_prompts": ["move_x_neg", "move_x_pos"],
                        },
                        "gating": {
                            "allow": ["move_x_neg", "move_x_pos"],
                            "deny": [],
                        },
                        "setup": {
                            "rng_seed": 7,
                            "starter_piece_id": "L",
                            "spawn_min_visible_layer": 2,
                            "bottom_layers_min": 1,
                            "bottom_layers_max": 2,
                        },
                        "complete_when": {
                            "events": ["move_x_neg"],
                            "predicates": [],
                            "logic": "all",
                        },
                    }
                ],
            }
        ],
    }


class TutorialSchemaTests(unittest.TestCase):
    def test_parse_valid_payload(self) -> None:
        parsed = parse_tutorial_payload(_base_payload())
        self.assertEqual(parsed.schema_version, 1)
        self.assertEqual(len(parsed.lessons), 1)
        lesson = parsed.lessons[0]
        self.assertEqual(lesson.lesson_id, "lesson_2d")
        self.assertEqual(lesson.mode, "2d")
        self.assertEqual(lesson.steps[0].step_id, "step_move")
        self.assertEqual(lesson.steps[0].setup.starter_piece_id, "L")
        self.assertEqual(lesson.steps[0].setup.spawn_min_visible_layer, 2)
        self.assertEqual(lesson.steps[0].setup.bottom_layers_min, 1)
        self.assertEqual(lesson.steps[0].setup.bottom_layers_max, 2)

    def test_duplicate_lesson_id_raises(self) -> None:
        payload = _base_payload()
        lessons = list(payload["lessons"])  # type: ignore[index]
        lessons.append(dict(lessons[0]))
        payload["lessons"] = lessons
        with self.assertRaises(RuntimeError):
            parse_tutorial_payload(payload)

    def test_missing_completion_conditions_raises(self) -> None:
        payload = _base_payload()
        step = payload["lessons"][0]["steps"][0]  # type: ignore[index]
        step["complete_when"] = {"events": [], "predicates": [], "logic": "all"}
        with self.assertRaises(RuntimeError):
            parse_tutorial_payload(payload)

    def test_text_is_sanitized(self) -> None:
        payload = _base_payload()
        step = payload["lessons"][0]["steps"][0]  # type: ignore[index]
        step["ui"]["text"] = "Move\x00 now"  # type: ignore[index]
        parsed = parse_tutorial_payload(payload)
        self.assertEqual(parsed.lessons[0].steps[0].ui.text, "Move now")

    def test_setup_bottom_layer_bounds_validation(self) -> None:
        payload = _base_payload()
        step = payload["lessons"][0]["steps"][0]  # type: ignore[index]
        step["setup"]["bottom_layers_min"] = 2  # type: ignore[index]
        step["setup"]["bottom_layers_max"] = 1  # type: ignore[index]
        with self.assertRaises(RuntimeError):
            parse_tutorial_payload(payload)


if __name__ == "__main__":
    unittest.main()
