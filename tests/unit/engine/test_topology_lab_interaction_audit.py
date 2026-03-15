from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from tet4d.ui.pygame.launch import topology_lab_menu
from tet4d.ui.pygame.topology_lab import controls_panel, piece_sandbox
from tet4d.ui.pygame.topology_lab.interaction_audit import latest_span_for_phase


class TestTopologyLabInteractionAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def _explorer_state(self, dimension: int = 3):
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=dimension,
            entry_source="explorer",
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        state.interaction_audit.events.clear()
        state.interaction_audit.spans.clear()
        return state

    def test_preset_change_records_handler_and_preview_compile(self) -> None:
        state = self._explorer_state(3)

        controls_panel._cycle_explorer_preset(state, 1)

        handler_span = latest_span_for_phase(
            state,
            action="preset_change",
            phase="handler",
        )
        preview_span = latest_span_for_phase(
            state,
            action="preset_change",
            phase="preview_compile",
        )
        self.assertIsNotNone(handler_span)
        self.assertIsNotNone(preview_span)
        handler_events = [
            event.kind
            for event in state.interaction_audit.events
            if event.action == "preset_change" and event.phase == "handler"
        ]
        self.assertEqual(handler_events, ["start", "end"])

    def test_dimension_change_records_handler_and_preview_compile(self) -> None:
        state = self._explorer_state(3)

        controls_panel._cycle_dimension(state, 1)

        self.assertIsNotNone(
            latest_span_for_phase(
                state,
                action="dimension_change",
                phase="handler",
            )
        )
        self.assertIsNotNone(
            latest_span_for_phase(
                state,
                action="dimension_change",
                phase="preview_compile",
            )
        )

    def test_dimension_change_records_one_canonical_sync_and_scene_refresh(self) -> None:
        state = self._explorer_state(3)

        controls_panel._cycle_dimension(state, 1)

        canonical_sync_spans = [
            span
            for span in state.interaction_audit.spans
            if span.action == "dimension_change" and span.phase == "canonical_sync"
        ]
        scene_refresh_spans = [
            span
            for span in state.interaction_audit.spans
            if span.action == "dimension_change" and span.phase == "scene_refresh"
        ]
        self.assertEqual(len(canonical_sync_spans), 1)
        self.assertEqual(len(scene_refresh_spans), 1)

    def test_probe_move_records_handler_span(self) -> None:
        state = self._explorer_state(3)

        controls_panel._apply_probe_step(state, "x+")

        self.assertIsNotNone(
            latest_span_for_phase(
                state,
                action="probe_move",
                phase="handler",
            )
        )

    def test_sandbox_move_records_handler_span(self) -> None:
        state = self._explorer_state(3)
        profile = controls_panel.current_explorer_profile(state)
        assert profile is not None

        piece_sandbox.move_sandbox_piece(state, profile, "x+")

        self.assertIsNotNone(
            latest_span_for_phase(
                state,
                action="sandbox_move",
                phase="handler",
            )
        )

    def test_experiment_pack_records_compile_and_export_phases(self) -> None:
        state = self._explorer_state(3)
        batch = {
            "experiment_count": 2,
            "valid_experiment_count": 2,
            "recommendation": {"label": "Wrap X,Y,Z", "reason": "demo"},
        }

        with (
            patch.object(
                controls_panel,
                "compile_runtime_explorer_experiments",
                return_value=batch,
            ),
            patch.object(
                controls_panel,
                "export_runtime_explorer_experiments",
                return_value=(True, "ok", None),
            ),
            patch.object(controls_panel, "play_sfx"),
        ):
            controls_panel._run_experiments(state)

        self.assertIsNotNone(
            latest_span_for_phase(
                state,
                action="experiment_pack_generation",
                phase="handler",
            )
        )
        self.assertIsNotNone(
            latest_span_for_phase(
                state,
                action="experiment_pack_generation",
                phase="experiment_compile",
            )
        )
        self.assertIsNotNone(
            latest_span_for_phase(
                state,
                action="experiment_pack_generation",
                phase="experiment_export",
            )
        )

    def test_play_preview_records_launch_phase(self) -> None:
        state = self._explorer_state(2)
        state.scene_preview_error = None
        screen = pygame.Surface((32, 32))

        with patch.object(
            controls_panel,
            "launch_playground_state_gameplay",
            return_value=(screen, None),
        ):
            next_screen, _display_settings = controls_panel._launch_play_preview(
                state,
                screen,
                SimpleNamespace(),
            )

        self.assertIs(next_screen, screen)
        self.assertIsNotNone(
            latest_span_for_phase(
                state,
                action="play_preview_launch",
                phase="handler",
            )
        )
        self.assertIsNotNone(
            latest_span_for_phase(
                state,
                action="play_preview_launch",
                phase="play_launch",
            )
        )


if __name__ == "__main__":
    unittest.main()
