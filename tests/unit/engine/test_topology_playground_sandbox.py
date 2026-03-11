from __future__ import annotations

import inspect
import unittest

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    default_topology_profile_state,
)
from tet4d.engine.runtime import topology_playground_sandbox
from tet4d.engine.runtime.topology_playground_sandbox import (
    move_sandbox_piece,
    rotate_sandbox_piece_action,
    spawn_sandbox_piece,
)
from tet4d.engine.runtime.topology_playground_state import (
    TOOL_SANDBOX,
    TopologyPlaygroundSandboxPieceState,
    TopologyPlaygroundState,
    TopologyPlaygroundTopologyConfig,
)
from tet4d.engine.topology_explorer.presets import axis_wrap_profile, torus_profile_2d


class TestTopologyPlaygroundSandbox(unittest.TestCase):
    def test_module_stays_ui_free(self) -> None:
        source = inspect.getsource(topology_playground_sandbox)
        self.assertNotIn('pygame', source)
        self.assertNotIn('tet4d.ui', source)

    def _state_2d(self) -> TopologyPlaygroundState:
        legacy_profile = default_topology_profile_state(
            dimension=2,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        return TopologyPlaygroundState(
            dimension=2,
            axis_sizes=(4, 4),
            topology_config=TopologyPlaygroundTopologyConfig(
                legacy_profile=legacy_profile,
                explorer_profile=torus_profile_2d(),
            ),
            active_tool=TOOL_SANDBOX,
        )

    def test_spawn_enables_piece_in_canonical_state(self) -> None:
        state = self._state_2d()

        spawn_sandbox_piece(state)

        self.assertTrue(state.sandbox_piece_state.enabled)
        self.assertIsNotNone(state.sandbox_piece_state.origin)
        self.assertIsNotNone(state.sandbox_piece_state.local_blocks)
        self.assertEqual(state.sandbox_piece_state.trace, ())
        self.assertEqual(state.sandbox_piece_state.seam_crossings, ())

    def test_move_records_seam_crossing_in_canonical_state(self) -> None:
        state = self._state_2d()
        state.sandbox_piece_state = TopologyPlaygroundSandboxPieceState(
            enabled=True,
            piece_index=0,
            origin=(3, 1),
            local_blocks=((0, 0),),
        )

        ok, message = move_sandbox_piece(state, 'x+')

        self.assertTrue(ok, message)
        self.assertEqual(state.sandbox_piece_state.origin, (0, 1))
        self.assertTrue(state.sandbox_piece_state.seam_crossings)
        self.assertIn('x+ -> x-', state.sandbox_piece_state.seam_crossings[0])

    def test_rotate_updates_canonical_piece_blocks(self) -> None:
        legacy_profile = default_topology_profile_state(
            dimension=3,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        state = TopologyPlaygroundState(
            dimension=3,
            axis_sizes=(6, 6, 6),
            topology_config=TopologyPlaygroundTopologyConfig(
                legacy_profile=legacy_profile,
                explorer_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
            ),
            active_tool=TOOL_SANDBOX,
            sandbox_piece_state=TopologyPlaygroundSandboxPieceState(
                enabled=True,
                piece_index=0,
                origin=(2, 2, 2),
                local_blocks=((0, 0, 0), (1, 0, 0), (0, 1, 0)),
            ),
        )

        ok, message = rotate_sandbox_piece_action(state, 'rotate_xz_pos')

        self.assertTrue(ok, message)
        self.assertNotEqual(
            state.sandbox_piece_state.local_blocks,
            ((0, 0, 0), (1, 0, 0), (0, 1, 0)),
        )
        self.assertIn('rotate_xz_pos', state.sandbox_piece_state.trace)


if __name__ == '__main__':
    unittest.main()
