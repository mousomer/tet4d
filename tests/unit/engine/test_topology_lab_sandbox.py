from __future__ import annotations

import unittest

import pygame

from tet4d.ui.pygame.launch import topology_lab_menu

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    default_topology_profile_state,
)
from tet4d.engine.runtime.project_config import explorer_topology_preview_dims
from tet4d.engine.topology_explorer.presets import torus_profile_2d
from tet4d.ui.pygame.topology_lab.piece_sandbox import (
    ensure_piece_sandbox,
    move_sandbox_piece,
    reset_sandbox_piece,
    sandbox_cells,
)
from tet4d.ui.pygame.topology_lab.scene_state import TopologyLabState
from tests.unit.engine._translation_contract import (
    assert_repeated_translation_progress,
)


class TestTopologyLabSandbox(unittest.TestCase):
    def _state(self) -> TopologyLabState:
        profile = default_topology_profile_state(
            dimension=2,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        return TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=2,
            profile=profile,
        )

    def test_sandbox_piece_moves_rigidly_interior(self) -> None:
        state = self._state()
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        dims = explorer_topology_preview_dims(2)
        current = sandbox_cells(state)
        min_x = min(cell[0] for cell in current)
        min_y = min(cell[1] for cell in current)
        state.sandbox.origin = (state.sandbox.origin[0] + (1 - min_x), state.sandbox.origin[1] + (1 - min_y))
        shifted = sandbox_cells(state)
        self.assertLess(max(cell[1] for cell in shifted), dims[1] - 1)
        before = shifted
        ok, message = move_sandbox_piece(state, torus_profile_2d(), "y+")
        self.assertTrue(ok, message)
        after = sandbox_cells(state)
        self.assertNotEqual(before, after)
        self.assertEqual(state.sandbox.invalid_message, "")

    def test_sandbox_piece_reports_nonrigid_seam_crossing(self) -> None:
        state = self._state()
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        dims = explorer_topology_preview_dims(2)
        current = sandbox_cells(state)
        max_x = max(cell[0] for cell in current)
        min_y = min(cell[1] for cell in current)
        state.sandbox.origin = (state.sandbox.origin[0] + (dims[0] - 1 - max_x), state.sandbox.origin[1] - min_y)
        start_origin = tuple(state.sandbox.origin)
        ok, message = move_sandbox_piece(state, torus_profile_2d(), "x+")
        self.assertFalse(ok)
        self.assertIn("cannot remain rigid", message)
        self.assertEqual(tuple(state.sandbox.origin), start_origin)

    def test_reset_sandbox_piece_clears_trace_and_invalid_message(self) -> None:
        state = self._state()
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.trace = ["x+: [1, 1] -> [2, 1]"]
        state.sandbox.invalid_message = "bad"
        reset_sandbox_piece(state)
        self.assertEqual(state.sandbox.trace, [])
        self.assertEqual(state.sandbox.invalid_message, "")

    def test_sandbox_trace_toggle_action_flips_visibility(self) -> None:
        state = self._state()
        topology_lab_menu.ensure_piece_sandbox(state)
        assert state.sandbox is not None
        self.assertTrue(state.sandbox.show_trace)
        topology_lab_menu._activate_action(state, "sandbox_trace")
        self.assertFalse(state.sandbox.show_trace)
        topology_lab_menu._activate_action(state, "sandbox_trace")
        self.assertTrue(state.sandbox.show_trace)

    def test_repeated_sandbox_translation_progresses_through_dispatch(self) -> None:
        state = self._state()
        state.explorer_profile = torus_profile_2d()
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.piece_index = 1
        state.sandbox.origin = (2, 1)
        start_cells = tuple(sorted(sandbox_cells(state)))
        expected = [
            tuple(sorted((x - 1, y) for x, y in start_cells)),
            tuple(sorted((x - 2, y) for x, y in start_cells)),
        ]
        assert_repeated_translation_progress(
            self,
            step=lambda: topology_lab_menu._dispatch_key(state, pygame.K_LEFT),
            signature=lambda: tuple(sorted(sandbox_cells(state))),
            expected_signatures=expected,
            label="explorer_sandbox_left",
        )


if __name__ == "__main__":
    unittest.main()
