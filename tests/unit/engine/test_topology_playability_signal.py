from __future__ import annotations

import unittest

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    default_topology_profile_state,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    compile_explorer_topology_preview,
)
from tet4d.engine.runtime.topology_playability_signal import (
    derive_topology_playability_analysis,
)
from tet4d.engine.runtime.topology_playground_state import (
    EXPLORER_USABILITY_BLOCKED,
    EXPLORER_USABILITY_CELLWISE,
    PLAYABILITY_STATUS_BLOCKED,
    PLAYABILITY_STATUS_PLAYABLE,
    PLAYABILITY_STATUS_WARNING,
    RIGID_PLAYABILITY_BLOCKED,
    RIGID_PLAYABILITY_PLAYABLE,
    TOPOLOGY_VALIDITY_INVALID,
    TOPOLOGY_VALIDITY_VALID,
    TopologyPlaygroundState,
    TopologyPlaygroundTopologyConfig,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    projective_plane_profile_2d,
    sphere_profile_2d,
)


class TestTopologyPlayabilitySignal(unittest.TestCase):
    def _state(
        self,
        dimension: int,
        *,
        axis_sizes: tuple[int, ...],
        explorer_profile,
    ) -> TopologyPlaygroundState:
        legacy_profile = default_topology_profile_state(
            dimension=dimension,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        return TopologyPlaygroundState(
            dimension=dimension,
            axis_sizes=axis_sizes,
            topology_config=TopologyPlaygroundTopologyConfig(
                legacy_profile=legacy_profile,
                explorer_profile=explorer_profile,
            ),
        )

    def test_bounded_topology_is_valid_explorable_and_rigid_playable(self) -> None:
        state = self._state(
            2,
            axis_sizes=(4, 4),
            explorer_profile=ExplorerTopologyProfile(dimension=2, gluings=()),
        )
        preview = compile_explorer_topology_preview(
            state.explorer_profile,
            dims=state.axis_sizes,
            source="playability_signal_test",
        )

        analysis = derive_topology_playability_analysis(state, preview=preview)

        self.assertEqual(analysis.status, PLAYABILITY_STATUS_PLAYABLE)
        self.assertEqual(analysis.validity, TOPOLOGY_VALIDITY_VALID)
        self.assertEqual(analysis.explorer_usability, EXPLORER_USABILITY_CELLWISE)
        self.assertEqual(analysis.rigid_playability, RIGID_PLAYABILITY_PLAYABLE)
        self.assertEqual(
            analysis.summary, "Valid. Cellwise explorable. Rigid-playable."
        )
        self.assertEqual(analysis.movement_summary.component_count, 1)

    def test_torus_chart_split_piece_stays_rigid_playable(self) -> None:
        state = self._state(
            2,
            axis_sizes=(4, 4),
            explorer_profile=axis_wrap_profile(dimension=2, wrapped_axes=(1,)),
        )
        preview = compile_explorer_topology_preview(
            state.explorer_profile,
            dims=state.axis_sizes,
            source="playability_signal_test",
        )

        analysis = derive_topology_playability_analysis(state, preview=preview)

        self.assertEqual(analysis.status, PLAYABILITY_STATUS_PLAYABLE)
        self.assertEqual(analysis.validity, TOPOLOGY_VALIDITY_VALID)
        self.assertEqual(analysis.explorer_usability, EXPLORER_USABILITY_CELLWISE)
        self.assertEqual(analysis.rigid_playability, RIGID_PLAYABILITY_PLAYABLE)

    def test_projective_topology_is_valid_explorable_but_not_rigid_playable(
        self,
    ) -> None:
        state = self._state(
            2,
            axis_sizes=(4, 4),
            explorer_profile=projective_plane_profile_2d(),
        )
        preview = compile_explorer_topology_preview(
            state.explorer_profile,
            dims=state.axis_sizes,
            source="playability_signal_test",
        )

        analysis = derive_topology_playability_analysis(state, preview=preview)

        self.assertEqual(analysis.status, PLAYABILITY_STATUS_WARNING)
        self.assertEqual(analysis.validity, TOPOLOGY_VALIDITY_VALID)
        self.assertEqual(analysis.explorer_usability, EXPLORER_USABILITY_CELLWISE)
        self.assertEqual(analysis.rigid_playability, RIGID_PLAYABILITY_BLOCKED)
        self.assertEqual(
            analysis.summary,
            "Valid. Cellwise explorable. Not rigid-playable.",
        )
        self.assertIn("Rigid transport fails", analysis.rigid_reason)
        self.assertIn("single-cell traversal", analysis.explorer_reason)

    def test_invalid_sphere_dims_are_not_explorable_or_rigid_playable(self) -> None:
        state = self._state(
            2,
            axis_sizes=(5, 4),
            explorer_profile=sphere_profile_2d(),
        )

        analysis = derive_topology_playability_analysis(state)

        self.assertEqual(analysis.status, PLAYABILITY_STATUS_BLOCKED)
        self.assertEqual(analysis.validity, TOPOLOGY_VALIDITY_INVALID)
        self.assertEqual(analysis.explorer_usability, EXPLORER_USABILITY_BLOCKED)
        self.assertEqual(analysis.rigid_playability, RIGID_PLAYABILITY_BLOCKED)
        self.assertEqual(analysis.summary, "Invalid for current board dimensions.")
        self.assertIn(
            "unsupported for current board dimensions", analysis.validity_reason
        )
        self.assertTrue(analysis.errors)


if __name__ == "__main__":
    unittest.main()
