from __future__ import annotations

import unittest

from tet4d.engine.tutorial.manager import TutorialManager
from tet4d.engine.tutorial.schema import parse_tutorial_payload


def _manager_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "lessons": [
            {
                "lesson_id": "lesson_2d",
                "title": "Lesson 2D",
                "mode": "2d",
                "steps": [
                    {
                        "id": "step_one",
                        "ui": {
                            "text": "Move both directions",
                            "hint": None,
                            "highlights": [],
                            "key_prompts": [],
                        },
                        "gating": {
                            "allow": ["move_x_neg", "move_x_pos", "menu"],
                            "deny": ["rotate_xy_pos"],
                        },
                        "setup": {},
                        "complete_when": {
                            "events": ["move_x_neg", "move_x_pos"],
                            "predicates": [],
                            "logic": "all",
                        },
                    },
                    {
                        "id": "step_two",
                        "ui": {
                            "text": "Clear a line",
                            "hint": None,
                            "highlights": [],
                            "key_prompts": [],
                        },
                        "gating": {"allow": [], "deny": []},
                        "setup": {},
                        "complete_when": {
                            "events": [],
                            "predicates": ["line_cleared"],
                            "logic": "all",
                        },
                    },
                ],
            }
        ],
    }


class TutorialManagerTests(unittest.TestCase):
    def _manager(self) -> TutorialManager:
        payload = parse_tutorial_payload(_manager_payload())
        return TutorialManager.from_payload(payload)

    def test_step_progression_is_deterministic(self) -> None:
        manager = self._manager()
        manager.start("lesson_2d")
        self.assertEqual(manager.snapshot().step_id, "step_one")
        manager.record_event("move_x_neg")
        self.assertFalse(manager.advance_if_complete())
        manager.record_event("move_x_pos")
        self.assertTrue(manager.advance_if_complete())
        self.assertEqual(manager.snapshot().step_id, "step_two")
        manager.set_predicate("line_cleared", True)
        self.assertTrue(manager.advance_if_complete())
        snapshot = manager.snapshot()
        self.assertEqual(snapshot.status, "completed")
        self.assertIsNone(snapshot.lesson_id)

    def test_gate_respects_allow_and_deny(self) -> None:
        manager = self._manager()
        manager.start("lesson_2d")
        self.assertTrue(manager.is_action_allowed("move_x_neg"))
        self.assertFalse(manager.is_action_allowed("rotate_xy_pos"))
        self.assertFalse(manager.is_action_allowed("soft_drop"))

    def test_restart_returns_to_first_step(self) -> None:
        manager = self._manager()
        manager.start("lesson_2d")
        manager.record_event("move_x_neg")
        manager.record_event("move_x_pos")
        self.assertTrue(manager.advance_if_complete())
        self.assertEqual(manager.snapshot().step_id, "step_two")
        self.assertTrue(manager.restart())
        self.assertEqual(manager.snapshot().step_id, "step_one")

    def test_skip_marks_skipped_status(self) -> None:
        manager = self._manager()
        manager.start("lesson_2d")
        self.assertTrue(manager.skip())
        self.assertEqual(manager.snapshot().status, "skipped")
        self.assertIsNone(manager.snapshot().lesson_id)


if __name__ == "__main__":
    unittest.main()
