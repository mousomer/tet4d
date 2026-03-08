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

    def test_parse_key_action_line_supports_use_rows_without_action(self) -> None:
        parsed = tutorial_overlay._parse_key_action_line("USE: Left/Right")
        self.assertEqual(parsed, (("Left", "Right"), ""))

    def test_mouse_overlay_prompt_uses_explicit_mouse_key_labels(self) -> None:
        orbit_lines = tutorial_overlay._overlay_lines_running(
            _base_payload(action_id="mouse_orbit"),
            dimension=3,
        )
        self.assertTrue(any("USE: RMB + Move Mouse" in text for text, *_ in orbit_lines))

        zoom_lines = tutorial_overlay._overlay_lines_running(
            _base_payload(action_id="mouse_zoom"),
            dimension=3,
        )
        self.assertTrue(any("USE: Mouse Wheel Scroll" in text for text, *_ in zoom_lines))

    def test_overlay_does_not_render_next_step_text(self) -> None:
        payload = _base_payload(action_id="move_x_neg")
        payload["next_step_text"] = "Should not render"
        lines = tutorial_overlay._overlay_lines_running(payload, dimension=2)
        self.assertFalse(any(str(text).startswith("Next:") for text, *_ in lines))
        self.assertTrue(any(str(text).startswith("Do this: ") for text, *_ in lines))
        self.assertTrue(any(str(text).startswith("Tip: ") for text, *_ in lines))
        self.assertFalse(any(str(text).startswith("Goal: ") for text, *_ in lines))
        self.assertFalse(any(str(text).startswith("ACTION: ") for text, *_ in lines))

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
        ):
            lines_a = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertTrue(any("USE: K97" in text for text, *_ in lines_a))

            current_key["value"] = 98
            lines_b = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertTrue(any("USE: K98" in text for text, *_ in lines_b))

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
        ):
            lines = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertTrue(any("USE: [," in text for text, *_ in lines))

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
        ):
            lines = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertFalse(
                any(str(text).startswith("System (not staged):") for text, *_ in lines)
            )


if __name__ == "__main__":
    unittest.main()
