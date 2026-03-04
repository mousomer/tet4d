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
                tutorial_overlay.engine_api,
                "runtime_binding_groups_for_dimension",
                side_effect=_runtime_groups,
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "format_key_tuple",
                side_effect=_format_key_tuple,
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "binding_action_description",
                return_value="Move left",
            ),
        ):
            lines_a = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertTrue(
                any("KEY: K97  ACTION: Move left" in text for text, *_ in lines_a)
            )

            current_key["value"] = 98
            lines_b = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertTrue(
                any("KEY: K98  ACTION: Move left" in text for text, *_ in lines_b)
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
                tutorial_overlay.engine_api,
                "runtime_binding_groups_for_dimension",
                side_effect=_runtime_groups,
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "format_key_tuple",
                return_value="[,",
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "binding_action_description",
                return_value="Lower locked-cell transparency",
            ),
        ):
            lines = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertTrue(
                any(
                    "KEY: [,  ACTION: Lower locked-cell transparency" in text
                    for text, *_ in lines
                )
            )

    def test_overlay_system_controls_use_live_bindings(self) -> None:
        payload = _base_payload(action_id="move_x_neg")
        current_help_key = {"value": 104}

        def _runtime_groups(dimension: int) -> dict[str, dict[str, tuple[int, ...]]]:
            if dimension == 2:
                return {
                    "game": {"move_x_neg": (97,)},
                    "system": {"help": (current_help_key["value"],)},
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
                tutorial_overlay.engine_api,
                "runtime_binding_groups_for_dimension",
                side_effect=_runtime_groups,
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "format_key_tuple",
                side_effect=_format_key_tuple,
            ),
            patch.object(
                tutorial_overlay.engine_api,
                "binding_action_description",
                side_effect=_label,
            ),
        ):
            lines_a = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertTrue(
                any("System (not staged): Help: K104" in text for text, *_ in lines_a)
            )

            current_help_key["value"] = 105
            lines_b = tutorial_overlay._overlay_lines_running(payload, dimension=2)
            self.assertTrue(
                any("System (not staged): Help: K105" in text for text, *_ in lines_b)
            )


if __name__ == "__main__":
    unittest.main()
