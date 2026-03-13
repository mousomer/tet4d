from __future__ import annotations

import inspect
import unittest

from tet4d.engine.topology_explorer.transport_resolver import (
    CELLWISE_DEFORMATION,
    build_explorer_transport_resolver,
)
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    default_topology_profile_state,
)
from tet4d.engine.runtime import topology_playground_sandbox
from tet4d.engine.runtime.topology_playground_sandbox import (
    move_sandbox_piece,
    rotate_sandbox_piece_action,
    sandbox_cells,
    spawn_sandbox_piece,
)
from tet4d.engine.runtime.topology_playground_state import (
    RIGID_PLAY_MODE_ON,
    TOOL_SANDBOX,
    TopologyPlaygroundSandboxPieceState,
    TopologyPlaygroundState,
    TopologyPlaygroundTopologyConfig,
)
from tet4d.engine.topology_explorer.glue_model import MoveStep
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    mobius_strip_profile_2d,
    projective_plane_profile_2d,
    projective_space_profile_3d,
    projective_space_profile_4d,
    sphere_profile_2d,
    sphere_profile_3d,
    sphere_profile_4d,
    swap_xw_profile_4d,
    torus_profile_2d,
)


class TestTopologyPlaygroundSandbox(unittest.TestCase):
    def test_module_stays_ui_free(self) -> None:
        source = inspect.getsource(topology_playground_sandbox)
        self.assertNotIn("pygame", source)
        self.assertNotIn("tet4d.ui", source)

    def _explorer_state(
        self,
        dimension: int,
        *,
        axis_sizes: tuple[int, ...],
        explorer_profile,
        origin: tuple[int, ...] | None = None,
        local_blocks: tuple[tuple[int, ...], ...] | None = None,
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
            active_tool=TOOL_SANDBOX,
            sandbox_piece_state=TopologyPlaygroundSandboxPieceState(
                enabled=True,
                piece_index=0,
                origin=origin,
                local_blocks=local_blocks,
            ),
        )

    def _state_2d(self) -> TopologyPlaygroundState:
        return self._explorer_state(
            2,
            axis_sizes=(4, 4),
            explorer_profile=torus_profile_2d(),
        )

    def _expected_move_outcome(
        self,
        state: TopologyPlaygroundState,
        *,
        step: MoveStep,
    ):
        outcome = build_explorer_transport_resolver(
            state.explorer_profile,
            state.axis_sizes,
        ).resolve_piece_step(sandbox_cells(state), step)
        if outcome.moved_cells is None:
            raise AssertionError("expected sandbox move to stay connected")
        return outcome.moved_cells, outcome

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

        ok, message = move_sandbox_piece(state, "x+")

        self.assertTrue(ok, message)
        self.assertEqual(state.sandbox_piece_state.origin, (0, 1))
        self.assertTrue(state.sandbox_piece_state.seam_crossings)
        self.assertIn("x+ -> x-", state.sandbox_piece_state.seam_crossings[0])

    def test_rotate_updates_canonical_piece_blocks(self) -> None:
        state = self._explorer_state(
            3,
            axis_sizes=(6, 6, 6),
            explorer_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
            origin=(2, 2, 2),
            local_blocks=((0, 0, 0), (1, 0, 0), (0, 1, 0)),
        )

        ok, message = rotate_sandbox_piece_action(state, "rotate_xz_pos")

        self.assertTrue(ok, message)
        self.assertNotEqual(
            state.sandbox_piece_state.local_blocks,
            ((0, 0, 0), (1, 0, 0), (0, 1, 0)),
        )
        self.assertIn("rotate_xz_pos", state.sandbox_piece_state.trace)

    def test_failed_rotation_leaves_sandbox_piece_unchanged(self) -> None:
        state = self._explorer_state(
            3,
            axis_sizes=(2, 2, 1),
            explorer_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
            origin=(0, 0, 0),
            local_blocks=((0, 0, 0), (1, 0, 0), (0, 1, 0)),
        )
        before_origin = state.sandbox_piece_state.origin
        before_blocks = state.sandbox_piece_state.local_blocks

        ok, message = rotate_sandbox_piece_action(state, "rotate_xz_pos")

        self.assertFalse(ok)
        self.assertEqual(message, "sandbox rotation leaves preview bounds")
        self.assertEqual(state.sandbox_piece_state.origin, before_origin)
        self.assertEqual(state.sandbox_piece_state.local_blocks, before_blocks)

    def test_sandbox_allows_gameplay_rigid_moves_across_safe_and_unsafe_cases(
        self,
    ) -> None:
        cases = (
            (
                "mobius_2d",
                self._explorer_state(
                    2,
                    axis_sizes=(4, 4),
                    explorer_profile=mobius_strip_profile_2d(),
                    origin=(0, 0),
                    local_blocks=((0, 0), (0, 1)),
                ),
                MoveStep(axis=0, delta=-1),
            ),
            (
                "projective_2d",
                self._explorer_state(
                    2,
                    axis_sizes=(4, 4),
                    explorer_profile=projective_plane_profile_2d(),
                    origin=(0, 0),
                    local_blocks=((0, 0), (0, 1)),
                ),
                MoveStep(axis=0, delta=-1),
            ),
            (
                "projective_3d",
                self._explorer_state(
                    3,
                    axis_sizes=(4, 4, 4),
                    explorer_profile=projective_space_profile_3d(),
                    origin=(0, 0, 0),
                    local_blocks=((0, 0, 0), (0, 1, 0)),
                ),
                MoveStep(axis=0, delta=-1),
            ),
            (
                "sphere_3d",
                self._explorer_state(
                    3,
                    axis_sizes=(4, 4, 4),
                    explorer_profile=sphere_profile_3d(),
                    origin=(0, 0, 0),
                    local_blocks=((0, 0, 0), (0, 0, 1)),
                ),
                MoveStep(axis=0, delta=-1),
            ),
            (
                "projective_4d",
                self._explorer_state(
                    4,
                    axis_sizes=(4, 4, 4, 4),
                    explorer_profile=projective_space_profile_4d(),
                    origin=(0, 0, 0, 0),
                    local_blocks=((0, 0, 0, 0), (0, 1, 0, 0)),
                ),
                MoveStep(axis=0, delta=-1),
            ),
            (
                "sphere_4d",
                self._explorer_state(
                    4,
                    axis_sizes=(4, 4, 4, 4),
                    explorer_profile=sphere_profile_4d(),
                    origin=(0, 0, 0, 0),
                    local_blocks=((0, 0, 0, 0), (0, 0, 1, 0)),
                ),
                MoveStep(axis=0, delta=-1),
            ),
            (
                "swap_xw_4d",
                self._explorer_state(
                    4,
                    axis_sizes=(4, 4, 4, 4),
                    explorer_profile=swap_xw_profile_4d(),
                    origin=(0, 1, 2, 3),
                    local_blocks=((0, 0, 0, 0), (0, 1, 0, 0)),
                ),
                MoveStep(axis=0, delta=-1),
            ),
        )

        for label, state, step in cases:
            with self.subTest(case=label):
                expected_cells, outcome = self._expected_move_outcome(state, step=step)
                self.assertNotEqual(outcome.kind, CELLWISE_DEFORMATION)

                ok, message = move_sandbox_piece(state, step.label)

                self.assertTrue(ok, message)
                self.assertEqual(sandbox_cells(state), expected_cells)

    def test_sandbox_matches_shared_cross_axis_transport_4d(self) -> None:
        state = self._explorer_state(
            4,
            axis_sizes=(4, 4, 4, 4),
            explorer_profile=swap_xw_profile_4d(),
            origin=(0, 1, 2, 1),
            local_blocks=((0, 0, 0, 0), (0, 1, 0, 0)),
        )
        expected = build_explorer_transport_resolver(
            state.explorer_profile,
            state.axis_sizes,
        ).resolve_piece_step(
            sandbox_cells(state),
            MoveStep(axis=0, delta=-1),
        )

        ok, message = move_sandbox_piece(state, "x-")

        self.assertTrue(ok, message)
        self.assertEqual(expected.kind, "rigid_transform")
        self.assertEqual(
            tuple(sorted(sandbox_cells(state))), tuple(sorted(expected.moved_cells))
        )
        self.assertIn("swap_xw_4d", state.sandbox_piece_state.seam_crossings[0])

    def test_sandbox_auto_mode_allows_cellwise_projective_cases_across_dimensions(
        self,
    ) -> None:
        cases = (
            (
                "projective_2d",
                self._explorer_state(
                    2,
                    axis_sizes=(4, 4),
                    explorer_profile=projective_plane_profile_2d(),
                    origin=(0, 0),
                    local_blocks=((0, 0), (1, 0)),
                ),
            ),
            (
                "projective_3d",
                self._explorer_state(
                    3,
                    axis_sizes=(4, 4, 4),
                    explorer_profile=projective_space_profile_3d(),
                    origin=(0, 0, 0),
                    local_blocks=((0, 0, 0), (1, 0, 0)),
                ),
            ),
            (
                "projective_4d",
                self._explorer_state(
                    4,
                    axis_sizes=(4, 4, 4, 4),
                    explorer_profile=projective_space_profile_4d(),
                    origin=(0, 0, 0, 0),
                    local_blocks=((0, 0, 0, 0), (1, 0, 0, 0)),
                ),
            ),
        )

        for label, state in cases:
            with self.subTest(case=label):
                expected_cells, outcome = self._expected_move_outcome(
                    state,
                    step=MoveStep(axis=0, delta=-1),
                )
                self.assertEqual(outcome.kind, CELLWISE_DEFORMATION)
                self.assertEqual(len(expected_cells), 2)

                ok, message = move_sandbox_piece(state, "x-")

                self.assertTrue(ok, message)
                self.assertEqual(tuple(sorted(sandbox_cells(state))), tuple(sorted(expected_cells)))

    def test_sandbox_forced_rigid_mode_blocks_cellwise_projective_cases_across_dimensions(
        self,
    ) -> None:
        cases = (
            (
                "projective_2d",
                self._explorer_state(
                    2,
                    axis_sizes=(4, 4),
                    explorer_profile=projective_plane_profile_2d(),
                    origin=(0, 0),
                    local_blocks=((0, 0), (1, 0)),
                ),
            ),
            (
                "projective_3d",
                self._explorer_state(
                    3,
                    axis_sizes=(4, 4, 4),
                    explorer_profile=projective_space_profile_3d(),
                    origin=(0, 0, 0),
                    local_blocks=((0, 0, 0), (1, 0, 0)),
                ),
            ),
            (
                "projective_4d",
                self._explorer_state(
                    4,
                    axis_sizes=(4, 4, 4, 4),
                    explorer_profile=projective_space_profile_4d(),
                    origin=(0, 0, 0, 0),
                    local_blocks=((0, 0, 0, 0), (1, 0, 0, 0)),
                ),
            ),
        )

        for label, state in cases:
            with self.subTest(case=label):
                state.launch_settings.rigid_play_mode = RIGID_PLAY_MODE_ON
                expected_cells, outcome = self._expected_move_outcome(
                    state,
                    step=MoveStep(axis=0, delta=-1),
                )
                self.assertEqual(outcome.kind, CELLWISE_DEFORMATION)
                self.assertEqual(len(expected_cells), 2)

                ok, message = move_sandbox_piece(state, "x-")

                self.assertFalse(ok)
                self.assertEqual(
                    message,
                    "sandbox piece cannot remain rigid across seam crossing",
                )

    def test_sandbox_surfaces_invalid_non_bijective_unsafe_dims_across_dimensions(
        self,
    ) -> None:
        cases = (
            (
                "sphere_2d",
                self._explorer_state(
                    2,
                    axis_sizes=(5, 4),
                    explorer_profile=sphere_profile_2d(),
                    origin=(0, 0),
                    local_blocks=((0, 0),),
                ),
            ),
            (
                "sphere_3d",
                self._explorer_state(
                    3,
                    axis_sizes=(4, 5, 6),
                    explorer_profile=sphere_profile_3d(),
                    origin=(0, 0, 0),
                    local_blocks=((0, 0, 0),),
                ),
            ),
            (
                "sphere_4d",
                self._explorer_state(
                    4,
                    axis_sizes=(4, 5, 6, 7),
                    explorer_profile=sphere_profile_4d(),
                    origin=(0, 0, 0, 0),
                    local_blocks=((0, 0, 0, 0),),
                ),
            ),
        )

        for label, state in cases:
            with self.subTest(case=label):
                ok, message = move_sandbox_piece(state, "x-")

                self.assertFalse(ok)
                self.assertEqual(state.sandbox_piece_state.invalid_message, message)
                self.assertIn("unsupported for current board dimensions", message)


if __name__ == "__main__":
    unittest.main()
