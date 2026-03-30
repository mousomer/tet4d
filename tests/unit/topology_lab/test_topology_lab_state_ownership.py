from __future__ import annotations

import unittest
from unittest.mock import patch

import pygame

from tet4d.engine.gameplay.topology_designer import GAMEPLAY_MODE_EXPLORER
from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.ui.pygame.launch import topology_lab_menu
from tet4d.ui.pygame.topology_lab import TopologyLabHitTarget
from tet4d.ui.pygame.topology_lab import workspace_shell as topology_lab_workspace_shell
from tet4d.ui.pygame.topology_lab.scene_state import (
    ExplorerPlaygroundSettings,
    current_probe_coord,
    current_probe_path,
    current_probe_trace,
    probe_neighbors_visible,
    replace_play_settings,
    replace_probe_state,
    sync_canonical_playground_state,
)
from tet4d.ui.pygame.topology_lab.state_ownership import (
    current_sandbox_focus_coord,
    current_sandbox_focus_path,
    ownership_snapshot,
    select_sandbox_projection_coord,
)


class TestTopologyLabStateOwnership(unittest.TestCase):
    def _state(self, dimension: int = 2) -> topology_lab_menu._TopologyLabState:
        return topology_lab_menu._initial_topology_lab_state(
            dimension,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            initial_explorer_profile=ExplorerTopologyProfile(
                dimension=dimension,
                gluings=(),
            ),
        )

    def test_ownership_snapshot_separates_inspector_and_sandbox_transients(self) -> None:
        state = self._state()
        replace_probe_state(
            state,
            coord=(1, 0),
            trace=["probe-step"],
            path=[(1, 0)],
            highlighted_glue_id=None,
        )
        select_sandbox_projection_coord(state, (3, 2))

        snapshot = ownership_snapshot(state)

        self.assertEqual(snapshot.inspector.probe_coord, (1, 0))
        self.assertEqual(snapshot.inspector.probe_trace, ("probe-step",))
        self.assertEqual(snapshot.sandbox.focus_coord, (3, 2))
        self.assertNotEqual(
            snapshot.inspector.probe_coord,
            snapshot.sandbox.focus_coord,
        )

    def test_projection_click_in_sandbox_does_not_overwrite_inspector_probe_state(self) -> None:
        state = self._state()
        replace_probe_state(
            state,
            coord=(1, 0),
            trace=["probe-step"],
            path=[(1, 0)],
            highlighted_glue_id=None,
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        target = TopologyLabHitTarget(
            kind="projection_cell",
            value=(4, 1),
            rect=pygame.Rect(0, 0, 16, 16),
        )

        handled = topology_lab_menu._handle_projection_cell_target(state, target)

        self.assertTrue(handled)
        self.assertEqual(current_probe_coord(state), (1, 0))
        self.assertEqual(current_probe_trace(state), ["probe-step"])
        self.assertEqual(current_probe_path(state), [(1, 0)])
        self.assertEqual(getattr(state, "sandbox_focus_coord", None), (4, 1))
        self.assertEqual(getattr(state, "sandbox_focus_path", None), [(4, 1)])

    def test_draw_explorer_scene_uses_sandbox_focus_overlay_when_active(self) -> None:
        state = self._state()
        replace_probe_state(
            state,
            coord=(0, 0),
            trace=[],
            path=[(0, 0)],
            highlighted_glue_id=None,
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        select_sandbox_projection_coord(state, (2, 3))
        boundaries = topology_lab_menu.boundaries_for_dimension(2)
        active_glue_ids = {boundary.label: "free" for boundary in boundaries}

        with patch.object(
            topology_lab_workspace_shell, "draw_scene_2d", return_value=[]
        ) as draw_scene:
            topology_lab_menu._draw_explorer_scene(
                pygame.Surface((320, 240)),
                fonts=None,
                state=state,
                area=pygame.Rect(0, 0, 100, 100),
                boundaries=boundaries,
                source_boundary=boundaries[0],
                target_boundary=boundaries[1],
                active_glue_ids=active_glue_ids,
                basis_arrows=[],
                preview_dims=topology_lab_menu._board_dims_for_state(state),
                sandbox_cells_payload=None,
                sandbox_ok=None,
                sandbox_message="",
            )

        kwargs = draw_scene.call_args.kwargs
        self.assertEqual(kwargs["probe_coord"], current_sandbox_focus_coord(state))
        self.assertEqual(kwargs["probe_path"], ())
        self.assertEqual(
            kwargs["neighbor_markers"],
            tuple(topology_lab_menu._active_workspace_neighbor_markers(state)),
        )

    def test_editor_probe_neighbor_overlay_uses_editor_probe_without_hiding_probe(self) -> None:
        state = self._state()
        replace_probe_state(
            state,
            coord=(1, 1),
            trace=["probe-step"],
            path=[(1, 1)],
            highlighted_glue_id=None,
        )
        topology_lab_menu._set_probe_neighbors_visible(state, True)
        boundaries = topology_lab_menu.boundaries_for_dimension(2)
        active_glue_ids = {boundary.label: "free" for boundary in boundaries}

        with patch.object(
            topology_lab_workspace_shell, "draw_scene_2d", return_value=[]
        ) as draw_scene:
            topology_lab_menu._draw_explorer_scene(
                pygame.Surface((320, 240)),
                fonts=None,
                state=state,
                area=pygame.Rect(0, 0, 100, 100),
                boundaries=boundaries,
                source_boundary=boundaries[0],
                target_boundary=boundaries[1],
                active_glue_ids=active_glue_ids,
                basis_arrows=[],
                preview_dims=topology_lab_menu._board_dims_for_state(state),
                sandbox_cells_payload=None,
                sandbox_ok=None,
                sandbox_message="",
            )

        kwargs = draw_scene.call_args.kwargs
        self.assertTrue(probe_neighbors_visible(state))
        self.assertEqual(kwargs["probe_coord"], current_probe_coord(state))
        self.assertTrue(kwargs["neighbor_markers"])
        self.assertEqual(kwargs["probe_path"], tuple(current_probe_path(state)))

    def test_sandbox_focus_tracks_visible_piece_cells_after_move(self) -> None:
        for dimension in (3, 4):
            with self.subTest(dimension=dimension):
                state = self._state(dimension=dimension)
                topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
                topology_lab_menu.ensure_piece_sandbox(state)
                current_cell = topology_lab_menu.sandbox_cells(state)[0]
                select_sandbox_projection_coord(state, current_cell)
                cells = topology_lab_menu.sandbox_cells(state)
                dims = topology_lab_menu._board_dims_for_state(state)
                step_label = next(
                    (
                        candidate
                        for candidate, axis, delta in (
                            ("x+", 0, 1),
                            ("x-", 0, -1),
                            ("y+", 1, 1),
                            ("y-", 1, -1),
                        )
                        if all(
                            0 <= cell[axis] + delta < dims[axis] for cell in cells
                        )
                    ),
                    None,
                )
                self.assertIsNotNone(step_label)
                ok, message = topology_lab_menu.move_sandbox_piece(
                    state,
                    topology_lab_menu._current_explorer_profile(state),
                    step_label,
                )
                self.assertTrue(ok, message)
                self.assertIn(
                    current_sandbox_focus_coord(state),
                    topology_lab_menu.sandbox_cells(state),
                )

    def test_canonical_topology_state_survives_tool_switches(self) -> None:
        state = self._state(dimension=3)
        sync_canonical_playground_state(state)
        assert state.canonical_state is not None
        expected_axis_sizes = state.canonical_state.axis_sizes
        expected_profile = state.canonical_state.explorer_profile
        expected_launch_settings = state.canonical_state.launch_settings

        for tool in (
            topology_lab_menu.TOOL_SANDBOX,
            topology_lab_menu.TOOL_PLAY,
            topology_lab_menu.TOOL_PROBE,
        ):
            topology_lab_menu.set_active_tool(state, tool)
            assert state.canonical_state is not None
            self.assertEqual(state.canonical_state.axis_sizes, expected_axis_sizes)
            self.assertEqual(state.canonical_state.explorer_profile, expected_profile)
            self.assertEqual(
                state.canonical_state.launch_settings,
                expected_launch_settings,
            )


    def test_sandbox_focus_rebinds_to_canonical_dims_after_board_change(self) -> None:
        state = self._state(dimension=3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        settings = state.play_settings
        assert settings is not None

        self.assertEqual(select_sandbox_projection_coord(state, (7, 1, 1)), (7, 1, 1))

        replace_play_settings(
            state,
            ExplorerPlaygroundSettings(
                board_dims=(5, 8, 8),
                piece_set_index=settings.piece_set_index,
                speed_level=settings.speed_level,
                random_mode_index=settings.random_mode_index,
                game_seed=settings.game_seed,
                rigid_play_mode=settings.rigid_play_mode,
            ),
        )

        assert state.canonical_state is not None
        self.assertEqual(state.canonical_state.axis_sizes, (5, 8, 8))
        self.assertEqual(current_sandbox_focus_coord(state), (2, 4, 4))
        self.assertEqual(current_sandbox_focus_path(state), [(2, 4, 4)])
        self.assertIsNone(select_sandbox_projection_coord(state, (7, 1, 1)))
        self.assertEqual(select_sandbox_projection_coord(state, (4, 1, 1)), (4, 1, 1))


if __name__ == "__main__":
    unittest.main()
