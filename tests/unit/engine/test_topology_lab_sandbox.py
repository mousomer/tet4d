from __future__ import annotations

import unittest

import pygame

from tet4d.ui.pygame.launch import topology_lab_menu
from tet4d.ui.pygame.keybindings import KEYS_3D, KEYS_4D

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    default_topology_profile_state,
)
from tet4d.engine.runtime.project_config import explorer_topology_preview_dims
from tet4d.engine.topology_explorer.presets import torus_profile_2d, axis_wrap_profile
from tet4d.ui.pygame.topology_lab.piece_sandbox import (
    ensure_piece_sandbox,
    move_sandbox_piece,
    reset_sandbox_piece,
    sandbox_cells,
    sandbox_lines,
    sandbox_shapes_for_state,
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

    def test_sandbox_piece_crosses_safe_torus_seam(self) -> None:
        state = self._state()
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        dims = explorer_topology_preview_dims(2)
        current = sandbox_cells(state)
        max_x = max(cell[0] for cell in current)
        min_y = min(cell[1] for cell in current)
        state.sandbox.origin = (
            state.sandbox.origin[0] + (dims[0] - 1 - max_x),
            state.sandbox.origin[1] - min_y,
        )
        ok, message = move_sandbox_piece(state, torus_profile_2d(), "x+")
        self.assertTrue(ok, message)
        self.assertTrue(state.sandbox.seam_crossings)
        self.assertEqual(state.sandbox.invalid_message, "")


    def test_sandbox_spawn_action_creates_piece_in_shell(self) -> None:
        state = self._state()
        self.assertIsNone(state.sandbox)
        topology_lab_menu._activate_action(state, "sandbox_spawn")
        self.assertIsNotNone(state.sandbox)
        assert state.sandbox is not None
        self.assertTrue(state.sandbox.enabled)
        self.assertEqual(state.sandbox.trace, ())
        self.assertEqual(state.sandbox.seam_crossings, ())

    def test_sandbox_records_seam_cross_preview(self) -> None:
        state = self._state()
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.local_blocks = ((0, 0),)
        dims = explorer_topology_preview_dims(2)
        state.sandbox.origin = (dims[0] - 1, 1)
        ok, message = move_sandbox_piece(state, torus_profile_2d(), "x+")
        self.assertTrue(ok, message)
        self.assertTrue(state.sandbox.seam_crossings)
        self.assertIn("->", state.sandbox.seam_crossings[0])
        self.assertIn("x+ -> x-", state.sandbox.seam_crossings[0])
        lines = sandbox_lines(state, torus_profile_2d())
        self.assertIn("Seam crossings", lines)

    def test_reset_sandbox_piece_clears_trace_and_invalid_message(self) -> None:
        state = self._state()
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.trace = ["x+: [1, 1] -> [2, 1]"]
        state.sandbox.invalid_message = "bad"
        reset_sandbox_piece(state)
        self.assertEqual(state.sandbox.trace, ())
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

    def _first_rotatable_shape_index(self, state: TopologyLabState, action: str) -> int:
        topology_lab_menu.ensure_piece_sandbox(state)
        assert state.sandbox is not None
        for index, shape in enumerate(sandbox_shapes_for_state(state)):
            state.sandbox.piece_index = index
            state.sandbox.local_blocks = shape.blocks
            from tet4d.ui.pygame.topology_lab.piece_sandbox import _rotate_blocks_for_action
            result = _rotate_blocks_for_action(state, shape.blocks, action=action)
            if result is not None and tuple(sorted(result)) != tuple(sorted(shape.blocks)):
                return index
        raise AssertionError(f"no rotatable sandbox shape for {action}")

    def test_sandbox_rotation_binding_changes_3d_piece(self) -> None:
        profile = default_topology_profile_state(
            dimension=3,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        state = TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=3,
            profile=profile,
            explorer_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.piece_index = self._first_rotatable_shape_index(state, "rotate_xz_pos")
        state.sandbox.local_blocks = sandbox_shapes_for_state(state)[state.sandbox.piece_index].blocks
        before = tuple(sorted(sandbox_cells(state)))
        topology_lab_menu._dispatch_key(state, KEYS_3D["rotate_xz_pos"][0])
        after = tuple(sorted(sandbox_cells(state)))
        self.assertNotEqual(before, after)

    def test_sandbox_rotation_binding_changes_4d_piece(self) -> None:
        profile = default_topology_profile_state(
            dimension=4,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        state = TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=4,
            profile=profile,
            explorer_profile=axis_wrap_profile(dimension=4, wrapped_axes=(0,)),
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.piece_index = self._first_rotatable_shape_index(state, "rotate_xw_pos")
        state.sandbox.local_blocks = sandbox_shapes_for_state(state)[state.sandbox.piece_index].blocks
        before = tuple(sorted(sandbox_cells(state)))
        topology_lab_menu._dispatch_key(state, KEYS_4D["rotate_xw_pos"][0])
        after = tuple(sorted(sandbox_cells(state)))
        self.assertNotEqual(before, after)

    def test_sandbox_xy_rotation_binding_changes_3d_piece(self) -> None:
        profile = default_topology_profile_state(
            dimension=3,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        state = TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=3,
            profile=profile,
            explorer_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.piece_index = self._first_rotatable_shape_index(state, "rotate_xy_pos")
        state.sandbox.local_blocks = sandbox_shapes_for_state(state)[state.sandbox.piece_index].blocks
        before = tuple(sorted(sandbox_cells(state)))
        topology_lab_menu._dispatch_key(state, KEYS_3D["rotate_xy_pos"][0])
        after = tuple(sorted(sandbox_cells(state)))
        self.assertNotEqual(before, after)

    def test_sandbox_xy_rotation_binding_changes_4d_piece(self) -> None:
        profile = default_topology_profile_state(
            dimension=4,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        state = TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=4,
            profile=profile,
            explorer_profile=axis_wrap_profile(dimension=4, wrapped_axes=(0,)),
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.piece_index = self._first_rotatable_shape_index(state, "rotate_xy_neg")
        state.sandbox.local_blocks = sandbox_shapes_for_state(state)[state.sandbox.piece_index].blocks
        before = tuple(sorted(sandbox_cells(state)))
        topology_lab_menu._dispatch_key(state, KEYS_4D["rotate_xy_neg"][0])
        after = tuple(sorted(sandbox_cells(state)))
        self.assertNotEqual(before, after)

    def test_repeated_sandbox_translation_progresses_through_dispatch(self) -> None:
        state = self._state()
        state.explorer_profile = torus_profile_2d()
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.piece_index = 1
        state.sandbox.local_blocks = sandbox_shapes_for_state(state)[1].blocks
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

    def test_repeated_sandbox_translation_progresses_through_dispatch_3d(self) -> None:
        profile = default_topology_profile_state(
            dimension=3,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        state = TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=3,
            profile=profile,
            explorer_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.piece_index = next(
            index
            for index, shape in enumerate(sandbox_shapes_for_state(state))
            if shape.name == "O3"
        )
        state.sandbox.local_blocks = sandbox_shapes_for_state(state)[state.sandbox.piece_index].blocks
        state.sandbox.origin = (3, 3, 3)
        start_cells = tuple(sorted(sandbox_cells(state)))
        expected = [
            tuple(sorted((x - 1, y, z) for x, y, z in start_cells)),
            tuple(sorted((x - 2, y, z) for x, y, z in start_cells)),
        ]
        assert_repeated_translation_progress(
            self,
            step=lambda: topology_lab_menu._dispatch_key(state, pygame.K_LEFT),
            signature=lambda: tuple(sorted(sandbox_cells(state))),
            expected_signatures=expected,
            label="explorer_sandbox_left_3d",
        )

    def test_repeated_sandbox_translation_progresses_through_dispatch_4d(self) -> None:
        profile = default_topology_profile_state(
            dimension=4,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        state = TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=4,
            profile=profile,
            explorer_profile=axis_wrap_profile(dimension=4, wrapped_axes=(0,)),
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.piece_index = next(
            index
            for index, shape in enumerate(sandbox_shapes_for_state(state))
            if shape.name == "CROSS4"
        )
        state.sandbox.local_blocks = sandbox_shapes_for_state(state)[state.sandbox.piece_index].blocks
        state.sandbox.origin = (3, 3, 3, 2)
        start_cells = tuple(sorted(sandbox_cells(state)))
        expected = [
            tuple(sorted((x - 1, y, z, w) for x, y, z, w in start_cells)),
            tuple(sorted((x - 2, y, z, w) for x, y, z, w in start_cells)),
        ]
        assert_repeated_translation_progress(
            self,
            step=lambda: topology_lab_menu._dispatch_key(state, pygame.K_LEFT),
            signature=lambda: tuple(sorted(sandbox_cells(state))),
            expected_signatures=expected,
            label="explorer_sandbox_left_4d",
        )

    def test_sandbox_spawn_uses_canonical_playground_state(self) -> None:
        state = self._state()

        topology_lab_menu._activate_action(state, 'sandbox_spawn')

        assert state.canonical_state is not None
        assert state.sandbox is not None
        self.assertIs(state.sandbox, state.canonical_state.sandbox_piece_state)
        self.assertTrue(state.canonical_state.sandbox_piece_state.enabled)
        self.assertIsNotNone(state.canonical_state.sandbox_piece_state.local_blocks)

    def test_sandbox_move_updates_canonical_playground_state(self) -> None:
        state = self._state()
        state.explorer_profile = torus_profile_2d()
        topology_lab_menu._sync_canonical_playground_state(state)
        ensure_piece_sandbox(state)
        assert state.canonical_state is not None
        assert state.sandbox is not None
        state.sandbox.local_blocks = ((0, 0),)
        dims = explorer_topology_preview_dims(2)
        state.sandbox.origin = (dims[0] - 1, 1)

        ok, message = move_sandbox_piece(state, torus_profile_2d(), 'x+')

        self.assertTrue(ok, message)
        self.assertIs(state.sandbox, state.canonical_state.sandbox_piece_state)
        self.assertEqual(
            state.canonical_state.sandbox_piece_state.origin,
            state.sandbox.origin,
        )
        self.assertTrue(state.canonical_state.sandbox_piece_state.seam_crossings)

    def test_sandbox_rotation_updates_canonical_playground_state(self) -> None:
        profile = default_topology_profile_state(
            dimension=3,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        state = TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=3,
            profile=profile,
            explorer_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        ensure_piece_sandbox(state)
        assert state.canonical_state is not None
        assert state.sandbox is not None
        state.sandbox.piece_index = self._first_rotatable_shape_index(state, 'rotate_xz_pos')
        state.sandbox.local_blocks = sandbox_shapes_for_state(state)[state.sandbox.piece_index].blocks
        before = state.canonical_state.sandbox_piece_state.local_blocks

        topology_lab_menu._dispatch_key(state, KEYS_3D['rotate_xz_pos'][0])

        self.assertIs(state.sandbox, state.canonical_state.sandbox_piece_state)
        self.assertNotEqual(before, state.canonical_state.sandbox_piece_state.local_blocks)


if __name__ == "__main__":
    unittest.main()
