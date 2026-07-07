import unittest
import random

from tet4d.engine.core.model import BoardND
from tet4d.engine.core.rules.piece_placement import (
    build_candidate_piece_placement,
    validate_candidate_piece_placement,
)
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
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
    projective_space_profile_4d,
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

    def test_explorer_mode_allows_non_safe_seam_move_even_when_rigid_flag_is_on(self):
        cfg = GameConfigND(
            dims=(4, 4, 4, 4),
            gravity_axis=1,
            exploration_mode=True,
            explorer_topology_profile=projective_space_profile_4d(),
            explorer_rigid_play_enabled=True,
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND("pair4", ((0, 0, 0, 0), (1, 0, 0, 0)), color_id=5)
        state.current_piece = ActivePieceND.from_shape(shape, pos=(0, 0, 0, 0))

        expected = cfg.explorer_transport.resolve_piece_step(
            state.current_piece.cells(),
            MoveStep(axis=0, delta=-1),
        )

        self.assertTrue(cfg.explorer_rigid_play_enabled)
        self.assertEqual(expected.kind, "cellwise_deformation")
        self.assertFalse(expected.rigidly_coherent)
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
        """With new rotation algorithm, rotation succeeds without kick if piece fits."""
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, kick_level="standard")
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND(
            "tri4_center_rotation",
            ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)),
            color_id=8,
        )
        state.current_piece = ActivePieceND.from_shape(shape, pos=(2, 2, 2, 3))

        before_blocks = tuple(sorted(state.current_piece.rel_blocks))
        self.assertTrue(state.try_rotate(0, 3, 1))
        # New rotation algorithm doesn't re-center, so rotation succeeds in-place
        # Verify rotation happened (blocks changed)
        self.assertNotEqual(tuple(sorted(state.current_piece.rel_blocks)), before_blocks)

    def test_4d_xw_rotation_fails_cleanly_at_w_edge(self):
        """With new rotation algorithm, rotation succeeds if piece fits (no kick needed)."""
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
        # New rotation algorithm doesn't re-center, so this now succeeds
        self.assertTrue(state.try_rotate(0, 3, 1))
        # Verify rotation happened
        self.assertNotEqual(tuple(sorted(state.current_piece.rel_blocks)), before_blocks)


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


class TestStage35GameplaySemantics(unittest.TestCase):
    def test_direct_board_occupancy_agrees_with_candidate_legality(self) -> None:
        board = BoardND((4, 5))
        board.cells[(2, 2)] = 9
        cases = (
            ("open", ((0, 1), (1, 1))),
            ("occupied", ((1, 2), (2, 2))),
            ("duplicate", ((1, 1), (1, 1))),
            ("out_of_bounds", ((3, 4), (4, 4))),
        )

        for label, cells in cases:
            with self.subTest(case=label):
                candidate = build_candidate_piece_placement(object(), cells)

                self.assertEqual(
                    validate_candidate_piece_placement(
                        candidate,
                        board.cells,
                        coord_validator=board.inside_bounds,
                    ),
                    board.can_place(cells),
                )

    def test_2d_and_embedded_nd_translation_reject_same_occupied_final_cells(
        self,
    ) -> None:
        shape_2d = PieceShape2D("pair", [(0, 0), (1, 0)], color_id=4)
        shape_nd = PieceShapeND("pair", ((0, 0, 0), (1, 0, 0)), color_id=4)
        state_2d = GameState(
            config=GameConfig(width=4, height=5),
            board=BoardND((4, 5)),
        )
        state_nd = GameStateND(
            config=GameConfigND(dims=(4, 5, 1), gravity_axis=1),
            board=BoardND((4, 5, 1)),
        )
        state_2d.board.cells.clear()
        state_nd.board.cells.clear()
        state_2d.current_piece = ActivePiece2D(shape_2d, pos=(1, 2), rotation=0)
        state_nd.current_piece = ActivePieceND.from_shape(shape_nd, pos=(1, 2, 0))
        state_2d.board.cells[(3, 2)] = 8
        state_nd.board.cells[(3, 2, 0)] = 8

        self.assertFalse(state_2d.try_move(1, 0))
        self.assertFalse(state_nd.try_move_axis(0, 1))
        self.assertEqual(
            tuple(sorted(state_2d.current_piece.cells())),
            ((1, 2), (2, 2)),
        )
        self.assertEqual(
            tuple(sorted(state_nd.current_piece.cells())),
            ((1, 2, 0), (2, 2, 0)),
        )

    def test_2d_and_embedded_nd_translation_reject_same_boundary_exit(self) -> None:
        shape_2d = PieceShape2D("pair", [(0, 0), (1, 0)], color_id=4)
        shape_nd = PieceShapeND("pair", ((0, 0, 0), (1, 0, 0)), color_id=4)
        state_2d = GameState(
            config=GameConfig(width=4, height=5),
            board=BoardND((4, 5)),
        )
        state_nd = GameStateND(
            config=GameConfigND(dims=(4, 5, 1), gravity_axis=1),
            board=BoardND((4, 5, 1)),
        )
        state_2d.board.cells.clear()
        state_nd.board.cells.clear()
        state_2d.current_piece = ActivePiece2D(shape_2d, pos=(2, 2), rotation=0)
        state_nd.current_piece = ActivePieceND.from_shape(shape_nd, pos=(2, 2, 0))

        self.assertFalse(state_2d.try_move(1, 0))
        self.assertFalse(state_nd.try_move_axis(0, 1))
        self.assertEqual(
            tuple(sorted(state_2d.current_piece.cells())),
            ((2, 2), (3, 2)),
        )
        self.assertEqual(
            tuple(sorted(state_nd.current_piece.cells())),
            ((2, 2, 0), (3, 2, 0)),
        )

    def test_2d_and_embedded_nd_rotation_reject_same_occupied_final_cells(self) -> None:
        blocks_2d = [(0, 0), (1, 0), (0, 1)]
        shape_2d = PieceShape2D("corner", blocks_2d, color_id=5)
        shape_nd = PieceShapeND(
            "corner",
            tuple((x, y, 0) for x, y in blocks_2d),
            color_id=5,
        )
        state_2d = GameState(
            config=GameConfig(width=5, height=6, kick_level="off"),
            board=BoardND((5, 6)),
        )
        state_nd = GameStateND(
            config=GameConfigND(dims=(5, 6, 1), gravity_axis=1, kick_level="off"),
            board=BoardND((5, 6, 1)),
        )
        state_2d.board.cells.clear()
        state_nd.board.cells.clear()
        state_2d.current_piece = ActivePiece2D(shape_2d, pos=(2, 2), rotation=0)
        state_nd.current_piece = ActivePieceND.from_shape(shape_nd, pos=(2, 2, 0))
        state_2d.board.cells[(3, 3)] = 9
        state_nd.board.cells[(3, 3, 0)] = 9

        state_2d.try_rotate(1)
        nd_rotated = state_nd.try_rotate(0, 1, 1)

        self.assertFalse(nd_rotated)
        self.assertEqual(
            tuple(sorted(state_2d.current_piece.cells())),
            ((2, 2), (2, 3), (3, 2)),
        )
        self.assertEqual(
            tuple(sorted(state_nd.current_piece.cells())),
            ((2, 2, 0), (2, 3, 0), (3, 2, 0)),
        )

    def test_hard_drop_matches_repeated_soft_drop_then_lock_in_2d_and_nd(self) -> None:
        shape_2d = PieceShape2D("dot", [(0, 0)], color_id=6)
        shape_nd = PieceShapeND("dot", ((0, 0, 0),), color_id=6)

        hard_2d = GameState(config=GameConfig(width=4, height=5), board=BoardND((4, 5)))
        repeated_2d = GameState(
            config=GameConfig(width=4, height=5),
            board=BoardND((4, 5)),
        )
        for state in (hard_2d, repeated_2d):
            state.board.cells.clear()
            state.current_piece = ActivePiece2D(shape_2d, pos=(1, -1), rotation=0)
        hard_2d.hard_drop()
        while repeated_2d.try_soft_drop():
            pass
        repeated_2d.lock_current_piece()

        self.assertEqual(hard_2d.board.cells, repeated_2d.board.cells)

        hard_nd = GameStateND(
            config=GameConfigND(dims=(4, 5, 1), gravity_axis=1),
            board=BoardND((4, 5, 1)),
        )
        repeated_nd = GameStateND(
            config=GameConfigND(dims=(4, 5, 1), gravity_axis=1),
            board=BoardND((4, 5, 1)),
        )
        for state in (hard_nd, repeated_nd):
            state.board.cells.clear()
            state.current_piece = ActivePieceND.from_shape(shape_nd, pos=(1, -1, 0))
        hard_nd.hard_drop()
        while repeated_nd.try_soft_drop():
            pass
        repeated_nd.lock_current_piece()

        self.assertEqual(hard_nd.board.cells, repeated_nd.board.cells)

    def test_spawn_validity_rejects_occupied_spawn_cells_in_2d_and_nd(self) -> None:
        shape_2d = PieceShape2D("visible_spawn", [(0, 0), (0, 3)], color_id=3)
        cfg_2d = GameConfig(width=5, height=6)
        board_2d = BoardND((cfg_2d.width, cfg_2d.height))
        board_2d.cells[(2, 1)] = 9
        state_2d = GameState(
            config=cfg_2d,
            board=board_2d,
            current_piece=None,
            next_bag=[shape_2d],
        )

        shape_nd = PieceShapeND("visible_spawn", ((0, 0, 0), (0, 3, 0)), color_id=3)
        cfg_nd = GameConfigND(dims=(5, 6, 1), gravity_axis=1)
        board_nd = BoardND(cfg_nd.dims)
        board_nd.cells[(2, 1, 0)] = 9
        state_nd = GameStateND(
            config=cfg_nd,
            board=board_nd,
            current_piece=None,
            next_bag=[shape_nd],
        )

        self.assertTrue(state_2d.game_over)
        self.assertTrue(state_nd.game_over)


if __name__ == "__main__":
    unittest.main()
