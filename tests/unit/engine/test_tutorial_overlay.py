from __future__ import annotations

import unittest
from unittest.mock import patch

from tet4d.ui.pygame.runtime_ui import tutorial_overlay


def _base_payload(*, action_id: str) -> dict[str, object]:
    return {
        "lesson_title": "Tutorial",
        "progress_text": "Step 1/10",
        "step_text": "Do action",
        "step_hint": "Hint",
        "next_step_text": "",
        "highlights": [],
        "key_prompts": [action_id],
    }


class TutorialOverlayKeyPromptTests(unittest.TestCase):
    def test_parse_key_action_line_extracts_tokens_and_action(self) -> None:
        parsed = tutorial_overlay._parse_key_action_line("KEY: Left/Right  Move x")
        self.assertEqual(parsed, (("Left", "Right"), "Move x"))

    def test_parse_key_action_line_supports_single_token(self) -> None:
        parsed = tutorial_overlay._parse_key_action_line("KEY: F10  ACTION: pause menu")
        self.assertEqual(parsed, (("F10",), "pause menu"))

    def test_overlay_action_label_uses_short_system_labels(self) -> None:
        with patch.object(
            tutorial_overlay,
            "binding_action_description",
            return_value="unused",
        ):
            self.assertEqual(tutorial_overlay._overlay_action_label("help"), "HELP")
            self.assertEqual(tutorial_overlay._overlay_action_label("menu"), "pause MENU")
            self.assertEqual(tutorial_overlay._overlay_action_label("restart"), "restart")
            self.assertEqual(tutorial_overlay._overlay_action_label("quit"), "main menu")

    def test_mouse_overlay_prompt_uses_explicit_mouse_key_labels(self) -> None:
        orbit_lines = tutorial_overlay._overlay_lines_running(
            _base_payload(action_id="mouse_orbit"),
            dimension=3,
        )
        self.assertTrue(
            any(
                "KEY: RMB + Move Mouse  rotate board" in text
                for text, *_ in orbit_lines
            )
        )

        zoom_lines = tutorial_overlay._overlay_lines_running(
            _base_payload(action_id="mouse_zoom"),
            dimension=3,
        )
        self.assertTrue(
            any(
                "KEY: Mouse Wheel Scroll  zoom board" in text
                for text, *_ in zoom_lines
            )
        )

    def test_overlay_does_not_render_next_step_text(self) -> None:
        payload = _base_payload(action_id="move_x_neg")
        payload["next_step_text"] = "Should not render"
        lines = tutorial_overlay._overlay_lines_running(payload, dimension=2)
        self.assertFalse(any(str(text).startswith("Next:") for text, *_ in lines))
        self.assertTrue(any(str(text).startswith("Goal: ") for text, *_ in lines))
        self.assertFalse(any(str(text).startswith("Task: ") for text, *_ in lines))
        self.assertFalse(any(str(text).startswith("How: ") for text, *_ in lines))
        self.assertFalse(any(str(text).startswith("Focus: ") for text, *_ in lines))

    def test_overlay_prompt_uses_live_runtime_bindings(self) -> None:
        payload = _base_payload(action_id="move_x_neg")
        current_key = {"value": 97}

        def _runtime_groups(dimension: int) -> dict[str, dict[str, tuple[int, ...]]]:
            if dimension == 2:
                return {
                    "game": {"move_x_neg": (current_key["value"],)},
                    "system": {},
                }
            return {"camera": {}, "system": {}}

        def _format_key_tuple(keys: tuple[int, ...]) -> str:
            return f"K{keys[0]}"

        with (
            patch.object(
                tutorial_overlay,
                "runtime_binding_groups_for_dimension",
                side_effect=_runtime_groups,
            ),
            patch.object(
                tutorial_overlay,
                "format_key_tuple",
                side_effect=_format_key_tuple,
            ),
            patch.object(
                tutorial_overlay,
                "binding_action_description",
                return_value="Move left",
            ),
        ):
            lines_a = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertTrue(
                any("KEY: K97  Move left" in text for text, *_ in lines_a)
            )

            current_key["value"] = 98
            lines_b = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertTrue(
                any("KEY: K98  Move left" in text for text, *_ in lines_b)
            )

    def test_2d_overlay_transparency_prompt_uses_camera_fallback_binding(self) -> None:
        payload = _base_payload(action_id="overlay_alpha_dec")

        def _runtime_groups(dimension: int) -> dict[str, dict[str, tuple[int, ...]]]:
            if dimension == 2:
                return {"game": {}, "system": {}}
            if dimension == 3:
                return {"camera": {"overlay_alpha_dec": (91,)}, "system": {}}
            return {"camera": {}, "system": {}}

        with (
            patch.object(
                tutorial_overlay,
                "runtime_binding_groups_for_dimension",
                side_effect=_runtime_groups,
            ),
            patch.object(
                tutorial_overlay,
                "format_key_tuple",
                return_value="[,",
            ),
            patch.object(
                tutorial_overlay,
                "binding_action_description",
                return_value="Lower locked-cell transparency",
            ),
        ):
            lines = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertTrue(
                any(
                    "KEY: [,  ACTION: Lower locked-cell transparency" in text
                    or "KEY: [,  Lower locked-cell transparency" in text
                    for text, *_ in lines
                )
            )

    def test_overlay_system_controls_line_is_not_rendered(self) -> None:
        payload = _base_payload(action_id="move_x_neg")

        def _runtime_groups(dimension: int) -> dict[str, dict[str, tuple[int, ...]]]:
            if dimension == 2:
                return {
                    "game": {"move_x_neg": (97,)},
                    "system": {"help": (104,)},
                }
            return {"camera": {}, "system": {}}

        def _format_key_tuple(keys: tuple[int, ...]) -> str:
            return f"K{keys[0]}"

        def _label(action_id: str) -> str:
            labels = {
                "move_x_neg": "Move left",
                "help": "Help",
            }
            return labels.get(action_id, action_id)

        with (
            patch.object(
                tutorial_overlay,
                "runtime_binding_groups_for_dimension",
                side_effect=_runtime_groups,
            ),
            patch.object(
                tutorial_overlay,
                "format_key_tuple",
                side_effect=_format_key_tuple,
            ),
            patch.object(
                tutorial_overlay,
                "binding_action_description",
                side_effect=_label,
            ),
        ):
            lines = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertFalse(
                any(str(text).startswith("System (not staged):") for text, *_ in lines)
            )


if __name__ == "__main__":
    unittest.main()
