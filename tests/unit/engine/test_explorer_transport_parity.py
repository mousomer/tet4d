from __future__ import annotations

import unittest

from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    default_topology_profile_state,
)
from tet4d.engine.runtime.topology_explorer_preview import advance_explorer_probe
from tet4d.engine.runtime.topology_playground_sandbox import (
    move_sandbox_piece,
    sandbox_cells,
)
from tet4d.engine.runtime.topology_playground_state import (
    TOOL_SANDBOX,
    TopologyPlaygroundSandboxPieceState,
    TopologyPlaygroundState,
    TopologyPlaygroundTopologyConfig,
)
from tet4d.engine.topology_explorer import MoveStep, build_explorer_transport_resolver
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    projective_plane_profile_2d,
    swap_xw_profile_4d,
    swapped_xz_profile_3d,
)


class TestExplorerTransportParity(unittest.TestCase):
    def _sandbox_state(
        self,
        dimension: int,
        *,
        axis_sizes: tuple[int, ...],
        explorer_profile,
        origin: tuple[int, ...],
        local_blocks: tuple[tuple[int, ...], ...],
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

    def test_preview_sandbox_and_gameplay_agree_on_dot_transport(self) -> None:
        cases = (
            (
                2,
                (4, 4),
                projective_plane_profile_2d(),
                (0, 1),
                MoveStep(axis=0, delta=-1),
            ),
            (
                2,
                (4, 4),
                projective_plane_profile_2d(),
                (2, 0),
                MoveStep(axis=1, delta=-1),
            ),
            (
                3,
                (4, 4, 4),
                swapped_xz_profile_3d(),
                (0, 1, 2),
                MoveStep(axis=0, delta=-1),
            ),
            (
                4,
                (4, 4, 4, 4),
                swap_xw_profile_4d(),
                (0, 1, 2, 1),
                MoveStep(axis=0, delta=-1),
            ),
        )

        for dimension, dims, profile, coord, step in cases:
            with self.subTest(dimension=dimension, coord=coord, step=step.label):
                preview_target, preview_result = advance_explorer_probe(
                    profile,
                    dims=dims,
                    coord=coord,
                    step_label=step.label,
                )
                sandbox_state = self._sandbox_state(
                    dimension,
                    axis_sizes=dims,
                    explorer_profile=profile,
                    origin=coord,
                    local_blocks=(tuple(0 for _ in dims),),
                )
                sandbox_ok, sandbox_message = move_sandbox_piece(
                    sandbox_state,
                    step.label,
                )
                self.assertTrue(sandbox_ok, sandbox_message)
                sandbox_target = sandbox_cells(sandbox_state)[0]

                if dimension == 2:
                    cfg = GameConfig(
                        width=dims[0],
                        height=dims[1],
                        exploration_mode=True,
                        explorer_topology_profile=profile,
                    )
                    gameplay_state = GameState(config=cfg, board=BoardND(dims))
                    gameplay_state.board.cells.clear()
                    gameplay_state.current_piece = ActivePiece2D(
                        shape=PieceShape2D("dot", [(0, 0)], color_id=1),
                        pos=coord,
                        rotation=0,
                    )
                    gameplay_state.try_move(
                        step.delta if step.axis == 0 else 0,
                        step.delta if step.axis == 1 else 0,
                    )
                    gameplay_target = gameplay_state.current_piece.cells()[0]
                else:
                    cfg = GameConfigND(
                        dims=dims,
                        gravity_axis=1,
                        exploration_mode=True,
                        explorer_topology_profile=profile,
                    )
                    gameplay_state = GameStateND(config=cfg, board=BoardND(dims))
                    gameplay_state.board.cells.clear()
                    gameplay_state.current_piece = ActivePieceND.from_shape(
                        PieceShapeND(
                            "dot",
                            (tuple(0 for _ in dims),),
                            color_id=1,
                        ),
                        pos=coord,
                    )
                    self.assertTrue(gameplay_state.try_move_axis(step.axis, step.delta))
                    gameplay_target = gameplay_state.current_piece.cells()[0]

                self.assertEqual(preview_target, sandbox_target)
                self.assertEqual(preview_target, gameplay_target)
                self.assertEqual(
                    preview_result["traversal"]["glue_id"],
                    build_explorer_transport_resolver(profile, dims)
                    .resolve_cell_step(coord, step)
                    .traversal.glue_id,
                )

    def test_projective_cellwise_piece_matches_resolver_sandbox_and_gameplay_auto_mode(
        self,
    ) -> None:
        cases = (
            (
                2,
                (4, 4),
                projective_plane_profile_2d(),
                (0, 0),
                ((0, 0), (1, 0)),
            ),
        )

        for dimension, dims, profile, origin, blocks in cases:
            with self.subTest(dimension=dimension, dims=dims):
                resolver = build_explorer_transport_resolver(profile, dims)
                source_cells = tuple(
                    tuple(origin[axis] + block[axis] for axis in range(len(dims)))
                    for block in blocks
                )
                expected = resolver.resolve_piece_step(
                    source_cells,
                    MoveStep(axis=0, delta=-1),
                )
                self.assertEqual(expected.kind, "cellwise_deformation")

                sandbox_state = self._sandbox_state(
                    dimension,
                    axis_sizes=dims,
                    explorer_profile=profile,
                    origin=origin,
                    local_blocks=blocks,
                )
                sandbox_ok, sandbox_message = move_sandbox_piece(
                    sandbox_state,
                    "x-",
                )
                self.assertTrue(sandbox_ok, sandbox_message)

                cfg = GameConfig(
                    width=dims[0],
                    height=dims[1],
                    exploration_mode=True,
                    explorer_topology_profile=profile,
                )
                self.assertFalse(cfg.explorer_rigid_play_enabled)
                gameplay_state = GameState(config=cfg, board=BoardND(dims))
                gameplay_state.board.cells.clear()
                gameplay_state.current_piece = ActivePiece2D(
                    shape=PieceShape2D("pair2", list(blocks), color_id=4),
                    pos=origin,
                    rotation=0,
                )

                gameplay_state.try_move(-1, 0)

                expected_cells = tuple(sorted(expected.moved_cells))
                self.assertEqual(
                    tuple(sorted(sandbox_cells(sandbox_state))),
                    expected_cells,
                )
                self.assertEqual(
                    tuple(sorted(gameplay_state.current_piece.cells())),
                    expected_cells,
                )

    def test_resolver_sandbox_and_gameplay_agree_on_rigid_cross_axis_pair(self) -> None:
        profile = swap_xw_profile_4d()
        dims = (4, 4, 4, 4)
        step = MoveStep(axis=0, delta=-1)
        resolver = build_explorer_transport_resolver(profile, dims)
        expected = resolver.resolve_piece_step(
            ((0, 1, 2, 1), (0, 2, 2, 1)),
            step,
        )

        sandbox_state = self._sandbox_state(
            4,
            axis_sizes=dims,
            explorer_profile=profile,
            origin=(0, 1, 2, 1),
            local_blocks=((0, 0, 0, 0), (0, 1, 0, 0)),
        )
        sandbox_ok, sandbox_message = move_sandbox_piece(sandbox_state, step.label)
        self.assertTrue(sandbox_ok, sandbox_message)

        cfg = GameConfigND(
            dims=dims,
            gravity_axis=1,
            exploration_mode=True,
            explorer_topology_profile=profile,
        )
        gameplay_state = GameStateND(config=cfg, board=BoardND(dims))
        gameplay_state.board.cells.clear()
        shape = PieceShapeND("pair4", ((0, 0, 0, 0), (0, 1, 0, 0)), color_id=7)
        gameplay_state.current_piece = ActivePieceND.from_shape(shape, pos=(0, 1, 2, 1))

        self.assertEqual(expected.kind, "rigid_transform")
        self.assertTrue(gameplay_state.try_move_axis(step.axis, step.delta))
        self.assertEqual(
            tuple(sorted(expected.moved_cells)),
            tuple(sorted(sandbox_cells(sandbox_state))),
        )
        self.assertEqual(
            tuple(sorted(expected.moved_cells)),
            tuple(sorted(gameplay_state.current_piece.cells())),
        )
        self.assertEqual(
            tuple(sorted(gameplay_state.current_piece.rel_blocks)),
            tuple(
                sorted(
                    expected.frame_transform.apply_linear(block)
                    for block in shape.blocks
                )
            ),
        )

    def test_atomic_seam_move_matches_explorer_sandbox_and_gameplay_2d(self) -> None:
        profile = axis_wrap_profile(dimension=2, wrapped_axes=(0,))
        dims = (4, 4)
        step = MoveStep(axis=0, delta=1)
        resolver = build_explorer_transport_resolver(profile, dims)
        expected = resolver.resolve_piece_step(((3, 1), (3, 2)), step)

        self.assertEqual(expected.kind, "plain_translation")
        self.assertEqual(tuple(sorted(expected.moved_cells)), ((0, 1), (0, 2)))

        sandbox_state = self._sandbox_state(
            2,
            axis_sizes=dims,
            explorer_profile=profile,
            origin=(3, 1),
            local_blocks=((0, 0), (0, 1)),
        )
        sandbox_ok, sandbox_message = move_sandbox_piece(sandbox_state, step.label)
        self.assertTrue(sandbox_ok, sandbox_message)

        cfg = GameConfig(
            width=dims[0],
            height=dims[1],
            exploration_mode=True,
            explorer_topology_profile=profile,
        )
        gameplay_state = GameState(config=cfg, board=BoardND(dims))
        gameplay_state.board.cells.clear()
        shape = PieceShape2D("pair2", [(0, 0), (0, 1)], color_id=5)
        gameplay_state.current_piece = ActivePiece2D(
            shape=shape, pos=(3, 1), rotation=0
        )

        gameplay_state.try_move(1, 0)

        self.assertEqual(
            tuple(sorted(expected.moved_cells)),
            tuple(sorted(sandbox_cells(sandbox_state))),
        )
        self.assertEqual(
            tuple(sorted(expected.moved_cells)),
            tuple(sorted(gameplay_state.current_piece.cells())),
        )

    def test_atomic_seam_move_matches_explorer_sandbox_and_gameplay_nd(self) -> None:
        profile = axis_wrap_profile(dimension=3, wrapped_axes=(0,))
        dims = (4, 4, 4)
        step = MoveStep(axis=0, delta=1)
        resolver = build_explorer_transport_resolver(profile, dims)
        expected = resolver.resolve_piece_step(((3, 1, 1), (3, 2, 1)), step)

        self.assertEqual(expected.kind, "plain_translation")
        self.assertEqual(tuple(sorted(expected.moved_cells)), ((0, 1, 1), (0, 2, 1)))

        sandbox_state = self._sandbox_state(
            3,
            axis_sizes=dims,
            explorer_profile=profile,
            origin=(3, 1, 1),
            local_blocks=((0, 0, 0), (0, 1, 0)),
        )
        sandbox_ok, sandbox_message = move_sandbox_piece(sandbox_state, step.label)
        self.assertTrue(sandbox_ok, sandbox_message)

        cfg = GameConfigND(
            dims=dims,
            gravity_axis=1,
            exploration_mode=True,
            explorer_topology_profile=profile,
        )
        gameplay_state = GameStateND(config=cfg, board=BoardND(dims))
        gameplay_state.board.cells.clear()
        shape = PieceShapeND("pair3", ((0, 0, 0), (0, 1, 0)), color_id=5)
        gameplay_state.current_piece = ActivePieceND.from_shape(shape, pos=(3, 1, 1))

        self.assertTrue(gameplay_state.try_move_axis(step.axis, step.delta))
        self.assertEqual(
            tuple(sorted(expected.moved_cells)),
            tuple(sorted(sandbox_cells(sandbox_state))),
        )
        self.assertEqual(
            tuple(sorted(expected.moved_cells)),
            tuple(sorted(gameplay_state.current_piece.cells())),
        )

    def test_torus_chart_split_piece_matches_resolver_sandbox_and_gameplay_rigid_mode(
        self,
    ) -> None:
        profile = axis_wrap_profile(dimension=2, wrapped_axes=(1,))
        dims = (4, 4)
        step = MoveStep(axis=1, delta=-1)
        resolver = build_explorer_transport_resolver(profile, dims)
        expected = resolver.resolve_piece_step(((0, 0), (0, 1)), step)

        self.assertEqual(expected.kind, "cellwise_deformation")
        self.assertTrue(expected.rigidly_coherent)

        sandbox_state = self._sandbox_state(
            2,
            axis_sizes=dims,
            explorer_profile=profile,
            origin=(0, 0),
            local_blocks=((0, 0), (0, 1)),
        )
        sandbox_state.launch_settings.rigid_play_mode = "on"
        sandbox_ok, sandbox_message = move_sandbox_piece(sandbox_state, step.label)
        self.assertTrue(sandbox_ok, sandbox_message)

        cfg = GameConfig(
            width=dims[0],
            height=dims[1],
            exploration_mode=True,
            explorer_topology_profile=profile,
            explorer_rigid_play_enabled=True,
        )
        gameplay_state = GameState(config=cfg, board=BoardND(dims))
        gameplay_state.board.cells.clear()
        shape = PieceShape2D("pair2", [(0, 0), (0, 1)], color_id=5)
        gameplay_state.current_piece = ActivePiece2D(
            shape=shape, pos=(0, 0), rotation=0
        )

        gameplay_state.try_move(0, -1)

        self.assertEqual(
            tuple(sorted(expected.moved_cells)),
            tuple(sorted(sandbox_cells(sandbox_state))),
        )
        self.assertEqual(
            tuple(sorted(expected.moved_cells)),
            tuple(sorted(gameplay_state.current_piece.cells())),
        )


if __name__ == "__main__":
    unittest.main()
