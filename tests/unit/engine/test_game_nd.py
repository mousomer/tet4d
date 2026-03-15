import unittest
import random

from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.pieces_nd import (
    ActivePieceND,
    PIECE_SET_3D_DEBUG,
    PIECE_SET_3D_EMBED_2D,
    PIECE_SET_3D_RANDOM,
    PIECE_SET_4D_DEBUG,
    PIECE_SET_4D_EMBED_3D,
    PIECE_SET_4D_RANDOM,
    PIECE_SET_4D_SIX,
    PieceShapeND,
)
from tet4d.engine.gameplay.topology import TOPOLOGY_INVERT_ALL, TOPOLOGY_WRAP_ALL
from tet4d.engine.topology_explorer import MoveStep
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    projective_space_profile_3d,
    swap_xw_profile_4d,
)
from tet4d.engine.core.rules.scoring import score_for_clear
from tests.unit.engine._translation_contract import (
    assert_repeated_translation_progress,
)


class TestGameND(unittest.TestCase):
    def test_score_table(self):
        self.assertEqual(score_for_clear(0), 0)
        self.assertEqual(score_for_clear(1), 40)
        self.assertEqual(score_for_clear(2), 100)
        self.assertEqual(score_for_clear(3), 300)
        self.assertEqual(score_for_clear(4), 1200)
        self.assertEqual(score_for_clear(5), 1600)

    def test_spawn_piece_matches_config_dimension(self):
        cfg = GameConfigND(dims=(6, 12, 4), gravity_axis=1)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))

        self.assertIsNotNone(state.current_piece)
        self.assertEqual(len(state.current_piece.pos), 3)
        for coord in state.current_piece.cells():
            self.assertEqual(len(coord), 3)

    def test_move_along_extra_axis(self):
        cfg = GameConfigND(dims=(5, 10, 3), gravity_axis=1)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=9)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(2, 0, 1))

        self.assertTrue(state.try_move_axis(2, 1))
        self.assertEqual(state.current_piece.pos, (2, 0, 2))
        self.assertFalse(state.try_move_axis(2, 1))

    def test_hard_drop_locks_to_bottom_along_gravity_axis(self):
        cfg = GameConfigND(dims=(4, 5, 3), gravity_axis=1)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=5)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(1, -1, 2))

        state.hard_drop()

        self.assertIn((1, 4, 2), state.board.cells)
        self.assertEqual(state.board.cells[(1, 4, 2)], 5)

    def test_lock_piece_clears_full_3d_plane(self):
        cfg = GameConfigND(dims=(2, 3, 2), gravity_axis=1)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()

        # Fill full bottom plane y=2 except one hole at (0, 2, 0)
        for x in range(cfg.dims[0]):
            for z in range(cfg.dims[2]):
                if (x, z) != (0, 0):
                    state.board.cells[(x, 2, z)] = 1

        # One block above; should drop after clear.
        state.board.cells[(1, 1, 1)] = 2

        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=3)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(0, 2, 0))

        cleared = state.lock_current_piece()

        self.assertEqual(cleared, 1)
        self.assertEqual(state.lines_cleared, 1)
        self.assertEqual(state.score, 45)
        self.assertEqual(state.board.cells.get((1, 2, 1)), 2)

    def test_lock_piece_can_clear_two_planes_and_score_100(self):
        cfg = GameConfigND(
            dims=(2, 5, 1),
            gravity_axis=1,
            piece_set_id=PIECE_SET_3D_EMBED_2D,
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        state.score = 0
        state.lines_cleared = 0

        state.board.cells[(0, 3, 0)] = 7
        state.board.cells[(0, 4, 0)] = 8
        state.board.cells[(0, 0, 0)] = 6
        two_blocks = PieceShapeND("double", ((0, 0, 0), (0, 1, 0)), color_id=5)
        state.current_piece = ActivePieceND.from_shape(two_blocks, pos=(1, 3, 0))

        cleared = state.lock_current_piece()

        self.assertEqual(cleared, 2)
        self.assertEqual(state.lines_cleared, 2)
        self.assertEqual(state.score, 185)

    def test_score_multiplier_scales_awarded_points(self):
        cfg = GameConfigND(
            dims=(2, 3, 1), gravity_axis=1, piece_set_id=PIECE_SET_3D_EMBED_2D
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        state.board.cells[(0, 2, 0)] = 1
        state.board.cells[(0, 1, 0)] = 9
        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=2)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(1, 2, 0))
        state.score_multiplier = 0.5

        cleared = state.lock_current_piece()
        self.assertEqual(cleared, 1)
        self.assertEqual(state.score, 22)

    def test_board_clear_applies_large_bonus(self):
        cfg = GameConfigND(
            dims=(2, 3, 1),
            gravity_axis=1,
            piece_set_id=PIECE_SET_3D_EMBED_2D,
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        state.board.cells[(0, 2, 0)] = 1
        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=2)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(1, 2, 0))

        cleared = state.lock_current_piece()
        self.assertEqual(cleared, 1)
        self.assertEqual(state.board.cells, {})
        self.assertEqual(state.score, 1545)

    def test_4d_config_can_use_six_cell_piece_set(self):
        cfg = GameConfigND(
            dims=(5, 10, 5, 4), gravity_axis=1, piece_set_4d=PIECE_SET_4D_SIX
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))

        self.assertIsNotNone(state.current_piece)
        self.assertEqual(len(state.current_piece.shape.blocks), 6)

    def test_3d_config_can_use_embedded_2d_piece_set(self):
        cfg = GameConfigND(
            dims=(6, 12, 6), gravity_axis=1, piece_set_id=PIECE_SET_3D_EMBED_2D
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))

        self.assertIsNotNone(state.current_piece)
        self.assertTrue(
            all(block[2] == 0 for block in state.current_piece.shape.blocks)
        )

    def test_4d_config_can_use_embedded_3d_piece_set(self):
        cfg = GameConfigND(
            dims=(6, 12, 6, 4), gravity_axis=1, piece_set_id=PIECE_SET_4D_EMBED_3D
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))

        self.assertIsNotNone(state.current_piece)
        self.assertTrue(
            all(block[3] == 0 for block in state.current_piece.shape.blocks)
        )

    def test_random_piece_set_respects_random_cell_count(self):
        cfg = GameConfigND(
            dims=(6, 12, 6),
            gravity_axis=1,
            piece_set_id=PIECE_SET_3D_RANDOM,
            random_cell_count=6,
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))

        self.assertIsNotNone(state.current_piece)
        self.assertEqual(len(state.current_piece.shape.blocks), 6)

    def test_4d_random_piece_set_does_not_game_over_after_few_drops(self):
        for seed in range(20):
            cfg = GameConfigND(
                dims=(8, 20, 8, 6),
                gravity_axis=1,
                piece_set_id=PIECE_SET_4D_RANDOM,
                random_cell_count=5,
            )
            state = GameStateND(
                config=cfg,
                board=BoardND(cfg.dims),
                rng=random.Random(seed),
            )

            for _ in range(10):
                self.assertFalse(state.game_over, f"premature game-over at seed={seed}")
                state.hard_drop()
            self.assertFalse(state.game_over, f"premature game-over at seed={seed}")

    def test_3d_debug_piece_set_does_not_immediately_game_over(self):
        cfg = GameConfigND(
            dims=(10, 20, 6),
            gravity_axis=1,
            piece_set_id=PIECE_SET_3D_DEBUG,
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims), rng=random.Random(0))
        for _ in range(5):
            self.assertFalse(state.game_over)
            state.hard_drop()
        self.assertFalse(state.game_over)

    def test_4d_debug_piece_set_does_not_immediately_game_over(self):
        cfg = GameConfigND(
            dims=(10, 20, 6, 4),
            gravity_axis=1,
            piece_set_id=PIECE_SET_4D_DEBUG,
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims), rng=random.Random(0))
        for _ in range(4):
            self.assertFalse(state.game_over)
            state.hard_drop()
        self.assertFalse(state.game_over)

    def test_invalid_4d_piece_set_rejected_by_config(self):
        with self.assertRaises(ValueError):
            GameConfigND(dims=(5, 10, 5, 4), gravity_axis=1, piece_set_4d="invalid")

    def test_wrap_all_wraps_non_gravity_axes_3d(self):
        cfg = GameConfigND(
            dims=(4, 8, 4),
            gravity_axis=1,
            topology_mode=TOPOLOGY_WRAP_ALL,
            piece_set_id=PIECE_SET_3D_EMBED_2D,
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=9)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(-1, 3, cfg.dims[2]))

        self.assertTrue(state._can_exist(state.current_piece))
        self.assertEqual(
            state.current_piece_cells_mapped(include_above=False), ((3, 3, 0),)
        )

    def test_wrap_all_keeps_gravity_axis_bounded_3d(self):
        cfg = GameConfigND(
            dims=(4, 6, 4),
            gravity_axis=1,
            topology_mode=TOPOLOGY_WRAP_ALL,
            piece_set_id=PIECE_SET_3D_EMBED_2D,
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=9)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(1, cfg.dims[1], 1))

        self.assertFalse(state._can_exist(state.current_piece))

    def test_explorer_glue_runtime_wraps_live_nd_movement(self):
        cfg = GameConfigND(
            dims=(4, 8, 4),
            gravity_axis=1,
            exploration_mode=True,
            explorer_topology_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=9)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(3, 3, 2))

        self.assertTrue(state.try_move_axis(0, 1))
        self.assertEqual(
            state.current_piece_cells_mapped(include_above=False), ((0, 3, 2),)
        )

    def test_explorer_glue_runtime_wraps_live_nd_movement_in_actual_play(self):
        cfg = GameConfigND(
            dims=(4, 8, 4),
            gravity_axis=1,
            exploration_mode=False,
            explorer_topology_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=9)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(3, 3, 2))

        self.assertTrue(state.try_move_axis(0, 1))
        self.assertEqual(
            state.current_piece_cells_mapped(include_above=False), ((0, 3, 2),)
        )

    def test_actual_play_with_explorer_profile_spawns_piece_without_game_over(self):
        cfg = GameConfigND(
            dims=(6, 12, 6),
            gravity_axis=1,
            exploration_mode=False,
            explorer_topology_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
        )

        state = GameStateND(config=cfg, board=BoardND(cfg.dims))

        self.assertIsNotNone(state.current_piece)
        self.assertFalse(state.game_over)
        self.assertTrue(
            any(coord[cfg.gravity_axis] < 0 for coord in state.current_piece.cells())
        )

    def test_explorer_interior_translation_preserves_rotation_frame_nd(self):
        normal_cfg = GameConfigND(dims=(10, 10, 10), gravity_axis=1)
        explorer_cfg = GameConfigND(
            dims=(10, 10, 10),
            gravity_axis=1,
            exploration_mode=True,
            explorer_topology_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
        )
        shape = PieceShapeND(
            "el3",
            ((-1, 0, 0), (0, 0, 0), (1, 0, 0), (1, 1, 0)),
            color_id=5,
        )
        seeded_piece = ActivePieceND.from_shape(shape, pos=(5, 4, 5)).rotated(0, 2, 1)
        normal_state = GameStateND(config=normal_cfg, board=BoardND(normal_cfg.dims))
        explorer_state = GameStateND(
            config=explorer_cfg, board=BoardND(explorer_cfg.dims)
        )
        normal_state.board.cells.clear()
        explorer_state.board.cells.clear()
        normal_state.current_piece = seeded_piece
        explorer_state.current_piece = seeded_piece

        self.assertTrue(normal_state.try_move_axis(0, -1))
        self.assertTrue(explorer_state.try_move_axis(0, -1))
        self.assertEqual(
            tuple(sorted(explorer_state.current_piece.rel_blocks)),
            tuple(sorted(normal_state.current_piece.rel_blocks)),
        )

        self.assertTrue(normal_state.try_rotate(1, 2, 1))
        self.assertTrue(explorer_state.try_rotate(1, 2, 1))
        self.assertEqual(
            explorer_state.current_piece.pos, normal_state.current_piece.pos
        )
        self.assertEqual(
            tuple(sorted(explorer_state.current_piece.rel_blocks)),
            tuple(sorted(normal_state.current_piece.rel_blocks)),
        )
        self.assertEqual(
            explorer_state.current_piece_cells_mapped(include_above=False),
            normal_state.current_piece_cells_mapped(include_above=False),
        )

    def test_explorer_cross_axis_seam_uses_shared_rigid_transform_4d(self):
        cfg = GameConfigND(
            dims=(4, 4, 4, 4),
            gravity_axis=1,
            exploration_mode=True,
            explorer_topology_profile=swap_xw_profile_4d(),
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND("pair4", ((0, 0, 0, 0), (0, 1, 0, 0)), color_id=7)
        state.current_piece = ActivePieceND.from_shape(shape, pos=(0, 1, 2, 1))

        expected = cfg.explorer_transport.resolve_piece_step(
            state.current_piece.cells(),
            MoveStep(axis=0, delta=-1),
        )

        self.assertEqual(expected.kind, "rigid_transform")
        self.assertIsNotNone(expected.frame_transform)
        self.assertTrue(state.try_move_axis(0, -1))
        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            tuple(sorted(expected.moved_cells)),
        )
        self.assertEqual(
            tuple(sorted(state.current_piece.rel_blocks)),
            tuple(
                sorted(
                    expected.frame_transform.apply_linear(block)
                    for block in shape.blocks
                )
            ),
        )

    def test_projective_auto_mode_allows_cellwise_seam_move_for_non_flat_piece(self):
        cfg = GameConfigND(
            dims=(4, 4, 4),
            gravity_axis=1,
            exploration_mode=True,
            explorer_topology_profile=projective_space_profile_3d(),
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND("pair3", ((0, 0, 0), (1, 0, 0)), color_id=5)
        state.current_piece = ActivePieceND.from_shape(shape, pos=(0, 0, 0))

        expected = cfg.explorer_transport.resolve_piece_step(
            state.current_piece.cells(),
            MoveStep(axis=0, delta=-1),
        )

        self.assertFalse(cfg.explorer_rigid_play_enabled)
        self.assertEqual(expected.kind, "cellwise_deformation")
        self.assertTrue(state.try_move_axis(0, -1))

        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            tuple(sorted(expected.moved_cells)),
        )

    def test_repeated_translation_contract_matches_main_and_explorer_3d(self):
        cases = (
            (
                "main_3d",
                GameConfigND(dims=(6, 8, 6), gravity_axis=1),
                PieceShapeND("dot", ((0, 0, 0),), color_id=9),
                (4, 3, 2),
                [((3, 3, 2),), ((2, 3, 2),), ((1, 3, 2),)],
            ),
            (
                "explorer_3d",
                GameConfigND(
                    dims=(6, 8, 6),
                    gravity_axis=1,
                    exploration_mode=True,
                    explorer_topology_profile=axis_wrap_profile(
                        dimension=3, wrapped_axes=(0,)
                    ),
                ),
                PieceShapeND("dot", ((0, 0, 0),), color_id=9),
                (1, 3, 2),
                [((0, 3, 2),), ((5, 3, 2),), ((4, 3, 2),)],
            ),
            (
                "main_3d_multicell",
                GameConfigND(dims=(8, 8, 8), gravity_axis=1),
                PieceShapeND(
                    "el3",
                    ((-1, 0, 0), (0, 0, 0), (1, 0, 0), (1, 1, 0)),
                    color_id=5,
                ),
                (4, 3, 4),
                [
                    ((2, 3, 4), (3, 3, 4), (4, 3, 4), (4, 4, 4)),
                    ((1, 3, 4), (2, 3, 4), (3, 3, 4), (3, 4, 4)),
                    ((0, 3, 4), (1, 3, 4), (2, 3, 4), (2, 4, 4)),
                ],
            ),
            (
                "explorer_3d_multicell",
                GameConfigND(
                    dims=(8, 8, 8),
                    gravity_axis=1,
                    speed_level=1,
                    exploration_mode=True,
                ),
                PieceShapeND(
                    "el3",
                    ((-1, 0, 0), (0, 0, 0), (1, 0, 0), (1, 1, 0)),
                    color_id=5,
                ),
                (4, 3, 4),
                [
                    ((2, 3, 4), (3, 3, 4), (4, 3, 4), (4, 4, 4)),
                    ((1, 3, 4), (2, 3, 4), (3, 3, 4), (3, 4, 4)),
                    ((0, 3, 4), (1, 3, 4), (2, 3, 4), (2, 4, 4)),
                ],
            ),
        )
        for label, cfg, shape, start_pos, expected in cases:
            with self.subTest(mode=label):
                state = GameStateND(config=cfg, board=BoardND(cfg.dims))
                state.board.cells.clear()
                state.current_piece = ActivePieceND.from_shape(shape, pos=start_pos)
                assert_repeated_translation_progress(
                    self,
                    step=lambda: state.try_move_axis(0, -1),
                    signature=lambda: state.current_piece_cells_mapped(
                        include_above=False
                    ),
                    expected_signatures=expected,
                    label=label,
                    result_assertion=lambda case, result, _index: case.assertTrue(
                        result
                    ),
                )

    def test_repeated_translation_contract_matches_main_and_explorer_4d_w_axis(self):
        cases = (
            (
                "main_4d_w",
                GameConfigND(dims=(6, 8, 6, 4), gravity_axis=1),
                PieceShapeND("dot", ((0, 0, 0, 0),), color_id=7),
                (2, 3, 2, 1),
                [((2, 3, 2, 2),), ((2, 3, 2, 3),)],
            ),
            (
                "explorer_4d_w",
                GameConfigND(
                    dims=(6, 8, 6, 4),
                    gravity_axis=1,
                    exploration_mode=True,
                    explorer_topology_profile=axis_wrap_profile(
                        dimension=4, wrapped_axes=(3,)
                    ),
                ),
                PieceShapeND("dot", ((0, 0, 0, 0),), color_id=7),
                (2, 3, 2, 2),
                [((2, 3, 2, 3),), ((2, 3, 2, 0),), ((2, 3, 2, 1),)],
            ),
            (
                "main_4d_w_multicell",
                GameConfigND(dims=(8, 8, 8, 6), gravity_axis=1),
                PieceShapeND(
                    "el4",
                    ((-1, 0, 0, 0), (0, 0, 0, 0), (1, 0, 0, 0), (1, 0, 0, 1)),
                    color_id=8,
                ),
                (4, 3, 4, 2),
                [
                    ((3, 3, 4, 3), (4, 3, 4, 3), (5, 3, 4, 3), (5, 3, 4, 4)),
                    ((3, 3, 4, 4), (4, 3, 4, 4), (5, 3, 4, 4), (5, 3, 4, 5)),
                ],
            ),
            (
                "explorer_4d_w_multicell",
                GameConfigND(
                    dims=(8, 8, 8, 6),
                    gravity_axis=1,
                    exploration_mode=True,
                ),
                PieceShapeND(
                    "el4",
                    ((-1, 0, 0, 0), (0, 0, 0, 0), (1, 0, 0, 0), (1, 0, 0, 1)),
                    color_id=8,
                ),
                (4, 3, 4, 2),
                [
                    ((3, 3, 4, 3), (4, 3, 4, 3), (5, 3, 4, 3), (5, 3, 4, 4)),
                    ((3, 3, 4, 4), (4, 3, 4, 4), (5, 3, 4, 4), (5, 3, 4, 5)),
                ],
            ),
        )
        for label, cfg, shape, start_pos, expected in cases:
            with self.subTest(mode=label):
                state = GameStateND(config=cfg, board=BoardND(cfg.dims))
                state.board.cells.clear()
                state.current_piece = ActivePieceND.from_shape(shape, pos=start_pos)
                assert_repeated_translation_progress(
                    self,
                    step=lambda: state.try_move_axis(3, 1),
                    signature=lambda: state.current_piece_cells_mapped(
                        include_above=False
                    ),
                    expected_signatures=expected,
                    label=label,
                    result_assertion=lambda case, result, _index: case.assertTrue(
                        result
                    ),
                )

    def test_invert_all_mirrors_other_wrapped_axis_3d(self):
        cfg = GameConfigND(
            dims=(4, 8, 4),
            gravity_axis=1,
            topology_mode=TOPOLOGY_INVERT_ALL,
            piece_set_id=PIECE_SET_3D_EMBED_2D,
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=9)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(-1, 3, 1))

        # Crossing x edge mirrors z for invert_all.
        self.assertEqual(
            state.current_piece_cells_mapped(include_above=False), ((3, 3, 2),)
        )

    def test_invert_all_straddling_w_seam_can_move(self):
        cfg = GameConfigND(
            dims=(6, 14, 4, 3),
            gravity_axis=1,
            topology_mode=TOPOLOGY_INVERT_ALL,
            piece_set_id=PIECE_SET_4D_EMBED_3D,
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        fork4 = PieceShapeND(
            "fork4_regression",
            ((0, 0, 0, 0), (-1, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 1), (0, 0, 1, 1)),
            color_id=7,
        )
        state.current_piece = ActivePieceND.from_shape(fork4, pos=(0, 1, 3, 1))
        self.assertTrue(state._can_exist(state.current_piece))
        self.assertTrue(state.try_move_axis(3, 1))
        mapped = state.current_piece_cells_mapped(include_above=False)
        self.assertEqual(len(mapped), len(set(mapped)))

    def test_wrap_topology_rotation_uses_topology_mapping_with_kicks(self):
        cfg = GameConfigND(
            dims=(6, 10, 6, 4),
            gravity_axis=1,
            topology_mode=TOPOLOGY_WRAP_ALL,
            kick_level="standard",
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND(
            "tri4_center_rotation",
            ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)),
            color_id=8,
        )
        state.current_piece = ActivePieceND.from_shape(shape, pos=(-1, 8, 2, 3))

        self.assertTrue(state._can_exist(state.current_piece))
        self.assertTrue(state.try_rotate(0, 3, 1))
        self.assertEqual(state.current_piece.pos, (-1, 8, 2, 3))
        mapped = state.current_piece_cells_mapped(include_above=False)
        self.assertEqual(len(mapped), len(set(mapped)))
        self.assertIn((5, 8, 2, 3), mapped)

    def test_invert_topology_rotation_uses_topology_mapping_with_kicks(self):
        cfg = GameConfigND(
            dims=(6, 10, 6, 4),
            gravity_axis=1,
            topology_mode=TOPOLOGY_INVERT_ALL,
            kick_level="standard",
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND(
            "tri4_center_rotation",
            ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)),
            color_id=8,
        )
        state.current_piece = ActivePieceND.from_shape(shape, pos=(-1, 8, 2, 3))

        self.assertTrue(state._can_exist(state.current_piece))
        self.assertTrue(state.try_rotate(0, 3, 1))
        self.assertEqual(state.current_piece.pos, (-1, 8, 2, 3))
        mapped = state.current_piece_cells_mapped(include_above=False)
        self.assertEqual(len(mapped), len(set(mapped)))
        self.assertIn((5, 8, 3, 0), mapped)

    def test_4d_xw_rotation_succeeds_in_bounds_under_center_rotation(self):
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND(
            "tri4_center_rotation",
            ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)),
            color_id=8,
        )
        state.current_piece = ActivePieceND.from_shape(shape, pos=(2, 2, 2, 2))

        before_blocks = tuple(sorted(state.current_piece.rel_blocks))
        self.assertTrue(state.try_rotate(0, 3, 1))
        self.assertNotEqual(
            tuple(sorted(state.current_piece.rel_blocks)), before_blocks
        )

    def test_4d_xw_rotation_can_kick_at_w_edge(self):
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, kick_level="standard")
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND(
            "tri4_center_rotation",
            ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)),
            color_id=8,
        )
        state.current_piece = ActivePieceND.from_shape(shape, pos=(2, 2, 2, 3))

        before_pos = tuple(state.current_piece.pos)
        self.assertTrue(state.try_rotate(0, 3, 1))
        self.assertNotEqual(tuple(state.current_piece.pos), before_pos)

    def test_4d_xw_rotation_fails_cleanly_at_w_edge(self):
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND(
            "tri4_center_rotation",
            ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)),
            color_id=8,
        )
        state.current_piece = ActivePieceND.from_shape(shape, pos=(2, 2, 2, 3))

        before_blocks = tuple(sorted(state.current_piece.rel_blocks))
        self.assertFalse(state.try_rotate(0, 3, 1))
        self.assertEqual(tuple(sorted(state.current_piece.rel_blocks)), before_blocks)


    def test_atomic_move_ignores_current_piece_source_cells(self):
        cfg = GameConfigND(dims=(5, 5, 5), gravity_axis=1)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        pair = PieceShapeND("pair", ((0, 0, 0), (1, 0, 0)), color_id=2)
        state.current_piece = ActivePieceND.from_shape(pair, pos=(1, 1, 1))
        for coord in state.current_piece.cells():
            state.board.cells[coord] = 9

        self.assertTrue(state.try_move((1, 0, 0)))
        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            ((2, 1, 1), (3, 1, 1)),
        )


if __name__ == "__main__":
    unittest.main()
