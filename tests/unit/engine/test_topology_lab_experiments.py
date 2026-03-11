from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tet4d.ui.pygame.launch import topology_lab_menu
from tet4d.ui.pygame.topology_lab import controls_panel


class TestTopologyLabExperiments(unittest.TestCase):
    def _explorer_state(self, dimension: int = 3):
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=dimension,
            entry_source="explorer",
        )
        return topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )

    def test_explorer_rows_include_experiment_pack(self) -> None:
        state = self._explorer_state(3)
        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]
        self.assertIn("experiments", row_keys)

    def test_action_buttons_include_experiments(self) -> None:
        state = self._explorer_state(3)
        labels = dict(topology_lab_menu._action_buttons_for_state(state))
        self.assertIn("experiments", labels)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        labels = dict(topology_lab_menu._action_buttons_for_state(state))
        self.assertIn("experiments", labels)

    def test_run_experiments_updates_batch_and_status(self) -> None:
        state = self._explorer_state(3)
        batch = {
            "experiment_count": 7,
            "valid_experiment_count": 7,
            "recommendation": {
                "label": "Wrap X,Y,Z",
                "reason": "1 component, 96 boundary traversals, no warnings",
            },
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
                return_value=(True, "Exported experiment pack to state/topology/explorer_experiments.json", Path("state/topology/explorer_experiments.json")),
            ),
            patch.object(controls_panel, "play_sfx") as play_sfx,
        ):
            controls_panel._run_experiments(state)
        self.assertIs(state.experiment_batch, batch)
        self.assertIn("Next: Wrap X,Y,Z", state.status)
        play_sfx.assert_called_once_with("menu_confirm")

    def test_workspace_preview_lines_include_experiment_recommendation(self) -> None:
        state = self._explorer_state(3)
        state.experiment_batch = {
            "experiment_count": 7,
            "valid_experiment_count": 6,
            "recommendation": {
                "label": "Wrap X,Y,Z",
                "reason": "1 component, 96 boundary traversals, no warnings",
            },
        }
        lines = topology_lab_menu._workspace_preview_lines(
            state,
            preview={
                "movement_graph": {
                    "cell_count": 1,
                    "directed_edge_count": 0,
                    "boundary_traversal_count": 0,
                    "component_count": 1,
                },
                "warnings": (),
                "sample_boundary_traversals": (),
            },
            preview_error=None,
        )
        self.assertIn("Experiments: 6/7 valid", lines)
        self.assertIn("Next: Wrap X,Y,Z", lines)


if __name__ == "__main__":
    unittest.main()