# tests/test_game2d.py
import unittest
import random

from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.pieces2d import PieceShape2D, ActivePiece2D
from tet4d.engine.gameplay.pieces2d import PIECE_SET_2D_DEBUG, PIECE_SET_2D_RANDOM
from tet4d.engine.topology_explorer import MoveStep
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    mobius_strip_profile_2d,
    projective_plane_profile_2d,
)
from tet4d.engine.gameplay.topology import TOPOLOGY_INVERT_ALL, TOPOLOGY_WRAP_ALL
from tet4d.engine.core.rules.scoring import score_for_clear
from tests.unit.engine._translation_contract import (
    assert_repeated_translation_progress,
)


class TestGame2D(unittest.TestCase):
    def test_score_table(self):
        self.assertEqual(score_for_clear(0), 0)
        self.assertEqual(score_for_clear(1), 40)
        self.assertEqual(score_for_clear(2), 100)
        self.assertEqual(score_for_clear(3), 300)
        self.assertEqual(score_for_clear(4), 1200)
        self.assertEqual(score_for_clear(5), 1600)

    def make_empty_state(self, width=10, height=20) -> GameState:
        cfg = GameConfig(width=width, height=height)
        board = BoardND((cfg.width, cfg.height))
        # We pass current_piece=None so __post_init__ will spawn one from a random bag.
        # For tests that need precise control, we'll overwrite current_piece ourselves.
        state = GameState(config=cfg, board=board)
        return state

    def test_config_rejects_non_y_gravity_for_2d(self):
        with self.assertRaises(ValueError):
            GameConfig(width=10, height=20, gravity_axis=0)

    def test_spawn_uses_bag_if_provided(self):
        cfg = GameConfig(width=10, height=20)
        board = BoardND((cfg.width, cfg.height))
        # Make a custom one-block piece to control spawn precisely
        custom_shape = PieceShape2D("dot", [(0, 0)], color_id=99)
        # Provide a predefined bag with exactly one shape
        state = GameState(
            config=cfg,
            board=board,
            current_piece=None,
            next_bag=[custom_shape],
        )
        # After __post_init__, it should spawn that shape as the current piece
        self.assertIsNotNone(state.current_piece)
        self.assertEqual(state.current_piece.shape.name, "dot")
        self.assertEqual(state.current_piece.shape.color_id, 99)

    def test_lock_current_piece_and_clear_line(self):
        # Small board for easier reasoning
        cfg = GameConfig(width=4, height=4)
        board = BoardND((cfg.width, cfg.height))
        state = GameState(config=cfg, board=board)

        # Clear existing random piece and bag; we control current_piece manually
        state.board.cells.clear()

        # Pre-fill bottom row y=3 with three blocks at x=1,2,3
        for x in (1, 2, 3):
            state.board.cells[(x, 3)] = 1
        # Keep one remaining block so this is not a full-board clear.
        state.board.cells[(0, 2)] = 9

        # Create a 1x1 piece to fill (0,3) and complete the row
        dot = PieceShape2D("dot", [(0, 0)], color_id=2)
        state.current_piece = ActivePiece2D(shape=dot, pos=(0, 3), rotation=0)

        score_before = state.score
        lines_before = state.lines_cleared

        cleared = state.lock_current_piece()

        self.assertEqual(cleared, 1)
        self.assertEqual(state.lines_cleared, lines_before + 1)
        # lock_piece_points(5) + single-line clear(40)
        self.assertEqual(state.score, score_before + 45)

        # The survivor block from y=2 drops into y=3 after clear.
        self.assertEqual(state.board.cells, {(0, 3): 9})

    def test_lock_current_piece_and_clear_two_lines_scores_100(self):
        cfg = GameConfig(width=2, height=3)
        board = BoardND((cfg.width, cfg.height))
        state = GameState(config=cfg, board=board)
        state.board.cells.clear()

        # Leave one gap in each target row at x=1.
        state.board.cells[(0, 1)] = 1
        state.board.cells[(0, 2)] = 1
        # Keep one survivor so this does not trigger board-clear bonus.
        state.board.cells[(0, 0)] = 1

        domino = PieceShape2D("domino", [(0, 0), (0, 1)], color_id=2)
        state.current_piece = ActivePiece2D(shape=domino, pos=(1, 1), rotation=0)

        cleared = state.lock_current_piece()

        self.assertEqual(cleared, 2)
        self.assertEqual(state.lines_cleared, 2)
        self.assertEqual(state.score, 185)
        self.assertEqual(state.board.cells, {(0, 2): 1})

    def test_score_multiplier_scales_awarded_points(self):
        cfg = GameConfig(width=2, height=2)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        state.board.cells[(0, 1)] = 1
        state.board.cells[(0, 0)] = 9
        state.current_piece = ActivePiece2D(
            PieceShape2D("dot", [(0, 0)], color_id=2), pos=(1, 1), rotation=0
        )
        state.score_multiplier = 0.5
        cleared = state.lock_current_piece()
        self.assertEqual(cleared, 1)
        # round((5 + 40) * 0.5) = 22
        self.assertEqual(state.score, 22)

    def test_board_clear_applies_large_bonus(self):
        cfg = GameConfig(width=2, height=2)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        state.board.cells[(0, 1)] = 1
        state.current_piece = ActivePiece2D(
            PieceShape2D("dot", [(0, 0)], color_id=2),
            pos=(1, 1),
            rotation=0,
        )
        cleared = state.lock_current_piece()
        self.assertEqual(cleared, 1)
        self.assertEqual(state.board.cells, {})
        self.assertEqual(state.score, 1545)

    def test_hard_drop_places_piece_at_bottom(self):
        cfg = GameConfig(width=4, height=4)
        board = BoardND((cfg.width, cfg.height))
        state = GameState(config=cfg, board=board)

        # Wipe any existing piece
        state.board.cells.clear()

        # A simple 1x1 piece starting just above the visible area
        dot = PieceShape2D("dot", [(0, 0)], color_id=5)
        state.current_piece = ActivePiece2D(shape=dot, pos=(2, -1), rotation=0)

        state.hard_drop()

        # After hard_drop, the piece should be locked at the bottom (y = height - 1)
        bottom_y = cfg.height - 1
        self.assertIn((2, bottom_y), state.board.cells)
        self.assertEqual(state.board.cells[(2, bottom_y)], 5)

    def test_can_exist_rejects_out_of_bounds(self):
        cfg = GameConfig(width=4, height=4)
        board = BoardND((cfg.width, cfg.height))
        state = GameState(config=cfg, board=board)

        # Simple 1x1 piece
        dot = PieceShape2D("dot", [(0, 0)], color_id=1)

        # Place inside bounds
        inside_piece = ActivePiece2D(shape=dot, pos=(1, 1), rotation=0)
        self.assertTrue(state._can_exist(inside_piece))

        # Outside to the left, right, and below bottom
        left_piece = ActivePiece2D(shape=dot, pos=(-1, 1), rotation=0)
        right_piece = ActivePiece2D(shape=dot, pos=(cfg.width, 1), rotation=0)
        below_piece = ActivePiece2D(shape=dot, pos=(1, cfg.height), rotation=0)

        self.assertFalse(state._can_exist(left_piece))
        self.assertFalse(state._can_exist(right_piece))
        self.assertFalse(state._can_exist(below_piece))

    def test_random_piece_set_uses_configured_cell_count(self):
        cfg = GameConfig(
            width=10,
            height=20,
            piece_set=PIECE_SET_2D_RANDOM,
            random_cell_count=5,
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        self.assertIsNotNone(state.current_piece)
        self.assertEqual(len(state.current_piece.shape.blocks), 5)

    def test_debug_piece_set_does_not_immediately_game_over(self):
        cfg = GameConfig(
            width=10,
            height=20,
            piece_set=PIECE_SET_2D_DEBUG,
        )
        state = GameState(
            config=cfg,
            board=BoardND((cfg.width, cfg.height)),
            rng=random.Random(0),
        )
        for _ in range(6):
            self.assertFalse(state.game_over)
            state.hard_drop()
        self.assertFalse(state.game_over)

    def test_wrap_all_wraps_horizontal_edges(self):
        cfg = GameConfig(width=4, height=6, topology_mode=TOPOLOGY_WRAP_ALL)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        dot = PieceShape2D("dot", [(0, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape=dot, pos=(-1, 2), rotation=0)

        self.assertTrue(state._can_exist(state.current_piece))
        self.assertEqual(
            state.current_piece_cells_mapped(include_above=False), ((3, 2),)
        )

        state.lock_current_piece()
        self.assertIn((3, 2), state.board.cells)

    def test_wrap_all_keeps_gravity_axis_bounded(self):
        cfg = GameConfig(width=4, height=6, topology_mode=TOPOLOGY_WRAP_ALL)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        dot = PieceShape2D("dot", [(0, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape=dot, pos=(1, cfg.height), rotation=0)

        self.assertFalse(state._can_exist(state.current_piece))

    def test_invert_all_matches_wrap_behavior_in_2d(self):
        cfg = GameConfig(width=5, height=7, topology_mode=TOPOLOGY_INVERT_ALL)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        dot = PieceShape2D("dot", [(0, 0)], color_id=4)
        state.current_piece = ActivePiece2D(shape=dot, pos=(cfg.width, 3), rotation=0)

        self.assertTrue(state._can_exist(state.current_piece))
        self.assertEqual(
            state.current_piece_cells_mapped(include_above=False), ((0, 3),)
        )

    def test_square_rotation_stays_in_place_under_center_rotation(self):
        cfg = GameConfig(width=4, height=6)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        square = PieceShape2D("square", [(0, 0), (1, 0), (0, 1), (1, 1)], color_id=2)
        state.current_piece = ActivePiece2D(shape=square, pos=(2, 3), rotation=0)

        before = tuple(sorted(state.current_piece.cells()))
        state.try_rotate(1)

        self.assertEqual(tuple(sorted(state.current_piece.cells())), before)

    def test_even_span_line_rotation_can_kick_at_edge(self):
        cfg = GameConfig(width=4, height=6, kick_level="light")
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        line = PieceShape2D("I", [(-1, 0), (0, 0), (1, 0), (2, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape=line, pos=(2, 2), rotation=1)

        before_pos = tuple(state.current_piece.pos)
        before_rotation = state.current_piece.rotation
        state.try_rotate(1)

        self.assertNotEqual(state.current_piece.rotation, before_rotation)
        self.assertEqual(tuple(state.current_piece.pos), before_pos)
        mapped = state.current_piece_cells_mapped(include_above=False)
        self.assertEqual(len(mapped), 4)
        self.assertEqual(len(set(mapped)), 4)

    def test_wrap_topology_rotation_uses_topology_mapping_with_kicks(self):
        cfg = GameConfig(
            width=4,
            height=6,
            topology_mode=TOPOLOGY_WRAP_ALL,
            kick_level="standard",
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        line = PieceShape2D("I", [(-1, 0), (0, 0), (1, 0), (2, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape=line, pos=(-2, 4), rotation=0)

        self.assertTrue(state._can_exist(state.current_piece))
        state.try_rotate(1)

        self.assertEqual(state.current_piece.pos, (-2, 4))
        mapped = state.current_piece_cells_mapped(include_above=False)
        self.assertEqual(mapped, ((2, 5), (2, 4), (2, 3), (2, 2)))
        self.assertEqual(len(mapped), len(set(mapped)))

    def test_explorer_glue_runtime_wraps_live_2d_movement(self):
        cfg = GameConfig(
            width=4,
            height=6,
            exploration_mode=True,
            explorer_topology_profile=axis_wrap_profile(dimension=2, wrapped_axes=(0,)),
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        dot = PieceShape2D("dot", [(0, 0)], color_id=5)
        state.current_piece = ActivePiece2D(shape=dot, pos=(3, 3), rotation=0)

        state.try_move(1, 0)

        self.assertEqual(
            state.current_piece_cells_mapped(include_above=False),
            ((0, 3),),
        )

    def test_explorer_glue_runtime_wraps_live_2d_movement_in_actual_play(self):
        cfg = GameConfig(
            width=4,
            height=6,
            exploration_mode=False,
            explorer_topology_profile=axis_wrap_profile(dimension=2, wrapped_axes=(0,)),
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        dot = PieceShape2D("dot", [(0, 0)], color_id=5)
        state.current_piece = ActivePiece2D(shape=dot, pos=(3, 3), rotation=0)

        state.try_move(1, 0)

        self.assertEqual(
            state.current_piece_cells_mapped(include_above=False),
            ((0, 3),),
        )

    def test_actual_play_with_explorer_profile_spawns_piece_without_game_over(self):
        cfg = GameConfig(
            width=10,
            height=20,
            exploration_mode=False,
            explorer_topology_profile=axis_wrap_profile(dimension=2, wrapped_axes=(0,)),
        )

        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))

        self.assertIsNotNone(state.current_piece)
        self.assertFalse(state.game_over)
        self.assertTrue(any(y < 0 for _x, y in state.current_piece.cells()))

    def test_explorer_interior_translation_preserves_rotation_frame_2d(self):
        normal_cfg = GameConfig(width=10, height=10)
        explorer_cfg = GameConfig(
            width=10,
            height=10,
            exploration_mode=True,
            explorer_topology_profile=axis_wrap_profile(dimension=2, wrapped_axes=(0,)),
        )
        line = PieceShape2D("I", [(-1, 0), (0, 0), (1, 0), (2, 0)], color_id=3)
        normal_state = GameState(config=normal_cfg, board=BoardND((10, 10)))
        explorer_state = GameState(config=explorer_cfg, board=BoardND((10, 10)))
        normal_state.board.cells.clear()
        explorer_state.board.cells.clear()
        normal_state.current_piece = ActivePiece2D(shape=line, pos=(5, 4), rotation=1)
        explorer_state.current_piece = ActivePiece2D(shape=line, pos=(5, 4), rotation=1)

        normal_state.try_move(-1, 0)
        explorer_state.try_move(-1, 0)

        self.assertEqual(
            explorer_state.current_piece.rotation, normal_state.current_piece.rotation
        )
        self.assertEqual(
            tuple(sorted(explorer_state.current_piece.shape.blocks)),
            tuple(sorted(normal_state.current_piece.shape.blocks)),
        )

        normal_state.try_rotate(1)
        explorer_state.try_rotate(1)

        self.assertEqual(
            explorer_state.current_piece.rotation, normal_state.current_piece.rotation
        )
        self.assertEqual(
            explorer_state.current_piece.pos, normal_state.current_piece.pos
        )
        self.assertEqual(
            explorer_state.current_piece_cells_mapped(include_above=False),
            normal_state.current_piece_cells_mapped(include_above=False),
        )

    def test_explorer_mobius_seam_uses_shared_rigid_transform_2d(self):
        cfg = GameConfig(
            width=6,
            height=6,
            exploration_mode=True,
            explorer_topology_profile=mobius_strip_profile_2d(),
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        shape = PieceShape2D("domino", [(0, 0), (0, 1)], color_id=5)
        state.current_piece = ActivePiece2D(shape=shape, pos=(0, 1), rotation=0)

        expected = cfg.explorer_transport.resolve_piece_step(
            state.current_piece.cells(),
            MoveStep(axis=0, delta=-1),
        )

        self.assertEqual(expected.kind, "rigid_transform")
        self.assertIsNotNone(expected.frame_transform)
        state.try_move(-1, 0)

        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            tuple(sorted(expected.moved_cells)),
        )
        self.assertEqual(
            state.current_piece.pos,
            expected.frame_transform.apply_absolute((0, 1)),
        )
        self.assertEqual(
            tuple(sorted(state.current_piece.shape.blocks)),
            tuple(
                sorted(
                    expected.frame_transform.apply_linear(block)
                    for block in shape.blocks
                )
            ),
        )

    def test_projective_auto_mode_allows_cellwise_seam_move_for_non_flat_piece(self):
        cfg = GameConfig(
            width=4,
            height=4,
            exploration_mode=True,
            explorer_topology_profile=projective_plane_profile_2d(),
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        shape = PieceShape2D("pair2", [(0, 0), (1, 0)], color_id=5)
        state.current_piece = ActivePiece2D(shape=shape, pos=(0, 0), rotation=0)

        expected = cfg.explorer_transport.resolve_piece_step(
            state.current_piece.cells(),
            MoveStep(axis=0, delta=-1),
        )

        self.assertFalse(cfg.explorer_rigid_play_enabled)
        self.assertEqual(expected.kind, "cellwise_deformation")
        state.try_move(-1, 0)

        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            tuple(sorted(expected.moved_cells)),
        )

    def test_torus_chart_split_wrap_is_allowed_in_rigid_mode(self):
        cfg = GameConfig(
            width=4,
            height=4,
            exploration_mode=True,
            explorer_topology_profile=axis_wrap_profile(dimension=2, wrapped_axes=(1,)),
            explorer_rigid_play_enabled=True,
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        shape = PieceShape2D("domino", [(0, 0), (0, 1)], color_id=5)
        state.current_piece = ActivePiece2D(shape=shape, pos=(0, 0), rotation=0)

        expected = cfg.explorer_transport.resolve_piece_step(
            state.current_piece.cells(),
            MoveStep(axis=1, delta=-1),
        )

        self.assertTrue(cfg.explorer_rigid_play_enabled)
        self.assertEqual(expected.kind, "cellwise_deformation")
        self.assertTrue(expected.rigidly_coherent)
        state.try_move(0, -1)

        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            tuple(sorted(expected.moved_cells)),
        )

    def test_repeated_translation_contract_matches_main_and_explorer_2d(self):
        cases = (
            (
                "main_2d",
                GameConfig(width=6, height=6),
                PieceShape2D("dot", [(0, 0)], color_id=5),
                (4, 3),
                [((3, 3),), ((2, 3),), ((1, 3),)],
            ),
            (
                "explorer_2d",
                GameConfig(
                    width=6,
                    height=6,
                    exploration_mode=True,
                    explorer_topology_profile=axis_wrap_profile(
                        dimension=2, wrapped_axes=(0,)
                    ),
                ),
                PieceShape2D("dot", [(0, 0)], color_id=5),
                (1, 3),
                [((0, 3),), ((5, 3),), ((4, 3),)],
            ),
            (
                "main_2d_multicell",
                GameConfig(width=8, height=8),
                PieceShape2D("L", [(-1, 0), (0, 0), (1, 0), (1, 1)], color_id=6),
                (4, 3),
                [
                    ((2, 3), (3, 3), (4, 3), (4, 4)),
                    ((1, 3), (2, 3), (3, 3), (3, 4)),
                    ((0, 3), (1, 3), (2, 3), (2, 4)),
                ],
            ),
            (
                "explorer_2d_multicell",
                GameConfig(
                    width=8,
                    height=8,
                    exploration_mode=True,
                    explorer_topology_profile=axis_wrap_profile(
                        dimension=2, wrapped_axes=(0,)
                    ),
                ),
                PieceShape2D("L", [(-1, 0), (0, 0), (1, 0), (1, 1)], color_id=6),
                (4, 3),
                [
                    ((2, 3), (3, 3), (4, 3), (4, 4)),
                    ((1, 3), (2, 3), (3, 3), (3, 4)),
                    ((0, 3), (1, 3), (2, 3), (2, 4)),
                ],
            ),
        )
        for label, cfg, shape, start_pos, expected in cases:
            with self.subTest(mode=label):
                state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
                state.board.cells.clear()
                state.current_piece = ActivePiece2D(
                    shape=shape,
                    pos=start_pos,
                    rotation=0,
                )
                assert_repeated_translation_progress(
                    self,
                    step=lambda: state.try_move(-1, 0),
                    signature=lambda: state.current_piece_cells_mapped(
                        include_above=False
                    ),
                    expected_signatures=expected,
                    label=label,
                )

    def test_invert_topology_rotation_uses_topology_mapping_with_kicks(self):
        cfg = GameConfig(
            width=4,
            height=6,
            topology_mode=TOPOLOGY_INVERT_ALL,
            kick_level="standard",
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        line = PieceShape2D("I", [(-1, 0), (0, 0), (1, 0), (2, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape=line, pos=(-2, 4), rotation=0)

        self.assertTrue(state._can_exist(state.current_piece))
        state.try_rotate(1)

        self.assertEqual(state.current_piece.pos, (-2, 4))
        mapped = state.current_piece_cells_mapped(include_above=False)
        self.assertEqual(mapped, ((2, 5), (2, 4), (2, 3), (2, 2)))
        self.assertEqual(len(mapped), len(set(mapped)))

    def test_even_span_line_rotation_fails_cleanly_at_edge(self):
        cfg = GameConfig(width=4, height=6)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        line = PieceShape2D("I", [(-1, 0), (0, 0), (1, 0), (2, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape=line, pos=(2, 2), rotation=1)

        before_rotation = state.current_piece.rotation
        before_cells = tuple(sorted(state.current_piece.cells()))
        state.try_rotate(1)

        self.assertNotEqual(state.current_piece.rotation, before_rotation)
        self.assertNotEqual(tuple(sorted(state.current_piece.cells())), before_cells)

    def test_atomic_move_ignores_current_piece_source_cells(self):
        state = self.make_empty_state(width=5, height=5)
        state.board.cells.clear()
        domino = PieceShape2D("domino", [(0, 0), (1, 0)], color_id=2)
        state.current_piece = ActivePiece2D(shape=domino, pos=(1, 1), rotation=0)
        for coord in state.current_piece.cells():
            state.board.cells[coord] = 9

        state.try_move(1, 0)

        self.assertEqual(tuple(sorted(state.current_piece.cells())), ((2, 1), (3, 1)))

    def test_atomic_rotation_ignores_current_piece_source_cells(self):
        state = self.make_empty_state(width=5, height=5)
        state.board.cells.clear()
        domino = PieceShape2D("domino", [(0, 0), (1, 0)], color_id=2)
        state.current_piece = ActivePiece2D(shape=domino, pos=(1, 1), rotation=0)
        for coord in state.current_piece.cells():
            state.board.cells[coord] = 9

        before_rotation = state.current_piece.rotation
        before_cells = tuple(sorted(state.current_piece.cells()))
        state.try_rotate(1)

        self.assertNotEqual(state.current_piece.rotation, before_rotation)
        self.assertNotEqual(tuple(sorted(state.current_piece.cells())), before_cells)

    def test_atomic_move_still_rejects_genuine_collision(self):
        state = self.make_empty_state(width=5, height=5)
        state.board.cells.clear()
        domino = PieceShape2D("domino", [(0, 0), (1, 0)], color_id=2)
        state.current_piece = ActivePiece2D(shape=domino, pos=(1, 1), rotation=0)
        for coord in state.current_piece.cells():
            state.board.cells[coord] = 9
        state.board.cells[(3, 1)] = 4
        before = tuple(sorted(state.current_piece.cells()))

        state.try_move(1, 0)

        self.assertEqual(tuple(sorted(state.current_piece.cells())), before)


if __name__ == "__main__":
    unittest.main()
