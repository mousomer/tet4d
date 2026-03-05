from __future__ import annotations

import random
import unittest

from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.pieces_nd import PIECE_SET_3D_STANDARD, PIECE_SET_4D_STANDARD
from tet4d.engine.tutorial.setup_apply import (
    apply_tutorial_step_setup_2d,
    apply_tutorial_step_setup_nd,
)


def _new_state_2d() -> tuple[GameConfig, GameState]:
    cfg = GameConfig(
        width=10,
        height=20,
        gravity_axis=1,
        piece_set="classic",
        challenge_layers=0,
        rng_seed=1337,
    )
    state = GameState(
        config=cfg,
        board=BoardND((cfg.width, cfg.height)),
        rng=random.Random(cfg.rng_seed),
    )
    return cfg, state


def _new_state_3d() -> tuple[GameConfigND, GameStateND]:
    cfg = GameConfigND(
        dims=(6, 18, 6),
        gravity_axis=1,
        piece_set_id=PIECE_SET_3D_STANDARD,
        challenge_layers=0,
        rng_seed=1337,
    )
    state = GameStateND(
        config=cfg,
        board=BoardND(cfg.dims),
        rng=random.Random(cfg.rng_seed),
    )
    return cfg, state


def _new_state_4d() -> tuple[GameConfigND, GameStateND]:
    cfg = GameConfigND(
        dims=(10, 20, 6, 4),
        gravity_axis=1,
        piece_set_id=PIECE_SET_4D_STANDARD,
        challenge_layers=0,
        rng_seed=1337,
    )
    state = GameStateND(
        config=cfg,
        board=BoardND(cfg.dims),
        rng=random.Random(cfg.rng_seed),
    )
    return cfg, state


class TutorialSetupApplyTests(unittest.TestCase):
    def test_apply_setup_2d_enforces_piece_visibility_and_layers(self) -> None:
        cfg, state = _new_state_2d()
        setup = {
            "rng_seed": 1001,
            "starter_piece_id": "L",
            "spawn_min_visible_layer": 2,
            "bottom_layers_min": 1,
            "bottom_layers_max": 2,
        }
        apply_tutorial_step_setup_2d(
            state,
            cfg,
            setup,
            lesson_id="tutorial_2d_core",
            step_id="move_xy",
        )
        assert state.current_piece is not None
        self.assertEqual(state.current_piece.shape.name, "L")
        mapped = state.current_piece_cells_mapped(include_above=True)
        self.assertTrue(mapped)
        self.assertTrue(all(y >= 0 for _, y in mapped))
        self.assertGreaterEqual(min(y for _, y in mapped), 2)
        gravity_levels = {coord[1] for coord in state.board.cells.keys()}
        self.assertIn(len(gravity_levels), {1, 2})
        self.assertTrue(all(level >= cfg.height - 2 for level in gravity_levels))

    def test_apply_setup_nd_enforces_piece_visibility_and_layers(self) -> None:
        cfg3, state3 = _new_state_3d()
        setup3 = {
            "rng_seed": 2001,
            "starter_piece_id": "SCREW3",
            "spawn_min_visible_layer": 2,
            "bottom_layers_min": 1,
            "bottom_layers_max": 2,
        }
        apply_tutorial_step_setup_nd(
            state3,
            cfg3,
            setup3,
            lesson_id="tutorial_3d_core",
            step_id="camera_controls",
        )
        assert state3.current_piece is not None
        self.assertEqual(state3.current_piece.shape.name, "SCREW3")
        mapped3 = state3.current_piece_cells_mapped(include_above=True)
        self.assertTrue(mapped3)
        self.assertTrue(all(coord[cfg3.gravity_axis] >= 0 for coord in mapped3))
        self.assertGreaterEqual(min(coord[cfg3.gravity_axis] for coord in mapped3), 2)
        gravity_levels3 = {
            coord[cfg3.gravity_axis] for coord in state3.board.cells.keys()
        }
        self.assertIn(len(gravity_levels3), {1, 2})
        self.assertTrue(
            all(level >= cfg3.dims[cfg3.gravity_axis] - 2 for level in gravity_levels3)
        )

        cfg4, state4 = _new_state_4d()
        setup4 = {
            "rng_seed": 3001,
            "starter_piece_id": "SKEW4_A",
            "spawn_min_visible_layer": 2,
            "bottom_layers_min": 1,
            "bottom_layers_max": 2,
        }
        apply_tutorial_step_setup_nd(
            state4,
            cfg4,
            setup4,
            lesson_id="tutorial_4d_core",
            step_id="slice_navigation",
        )
        assert state4.current_piece is not None
        self.assertEqual(state4.current_piece.shape.name, "SKEW4_A")
        mapped4 = state4.current_piece_cells_mapped(include_above=True)
        self.assertTrue(mapped4)
        self.assertTrue(all(coord[cfg4.gravity_axis] >= 0 for coord in mapped4))
        self.assertGreaterEqual(min(coord[cfg4.gravity_axis] for coord in mapped4), 2)
        gravity_levels4 = {
            coord[cfg4.gravity_axis] for coord in state4.board.cells.keys()
        }
        self.assertIn(len(gravity_levels4), {1, 2})
        self.assertTrue(
            all(level >= cfg4.dims[cfg4.gravity_axis] - 2 for level in gravity_levels4)
        )

    def test_apply_setup_is_deterministic_for_same_seed(self) -> None:
        setup = {
            "rng_seed": 1001,
            "starter_piece_id": "L",
            "spawn_min_visible_layer": 2,
            "bottom_layers_min": 1,
            "bottom_layers_max": 2,
        }
        cfg_a, state_a = _new_state_2d()
        cfg_b, state_b = _new_state_2d()
        apply_tutorial_step_setup_2d(
            state_a,
            cfg_a,
            setup,
            lesson_id="tutorial_2d_core",
            step_id="move_xy",
        )
        apply_tutorial_step_setup_2d(
            state_b,
            cfg_b,
            setup,
            lesson_id="tutorial_2d_core",
            step_id="move_xy",
        )
        self.assertEqual(state_a.board.cells, state_b.board.cells)
        self.assertEqual(
            tuple(state_a.current_piece_cells_mapped(include_above=True)),
            tuple(state_b.current_piece_cells_mapped(include_above=True)),
        )

    def test_2d_move_stage_spawn_supports_back_and_forth(self) -> None:
        cfg, state = _new_state_2d()
        apply_tutorial_step_setup_2d(
            state,
            cfg,
            {
                "rng_seed": 1001,
                "starter_piece_id": "L",
                "spawn_min_visible_layer": 2,
                "bottom_layers_min": 1,
                "bottom_layers_max": 2,
                "required_event_count": 4,
            },
            lesson_id="tutorial_2d_core",
            step_id="move_x_neg",
        )
        self.assertIsNotNone(state.current_piece)
        assert state.current_piece is not None
        probe = state.current_piece
        for _ in range(4):
            probe = probe.moved(-1, 0)
            self.assertTrue(state._can_exist(probe))
        for _ in range(4):
            probe = probe.moved(1, 0)
            self.assertTrue(state._can_exist(probe))

    def test_nd_move_stage_spawn_supports_sequential_axis_translations(self) -> None:
        cfg3 = GameConfigND(
            dims=(10, 20, 10),
            gravity_axis=1,
            piece_set_id=PIECE_SET_3D_STANDARD,
            challenge_layers=0,
            rng_seed=1337,
        )
        state3 = GameStateND(
            config=cfg3,
            board=BoardND(cfg3.dims),
            rng=random.Random(cfg3.rng_seed),
        )
        apply_tutorial_step_setup_nd(
            state3,
            cfg3,
            {
                "rng_seed": 2100,
                "starter_piece_id": "SCREW3",
                "spawn_min_visible_layer": 2,
                "bottom_layers_min": 1,
                "bottom_layers_max": 2,
                "required_event_count": 4,
            },
            lesson_id="tutorial_3d_core",
            step_id="move_x_neg",
        )
        self.assertIsNotNone(state3.current_piece)
        assert state3.current_piece is not None
        mapped3 = state3.current_piece_cells_mapped(include_above=True)
        max_x3 = max(coord[0] for coord in mapped3)
        min_z3 = min(coord[2] for coord in mapped3)
        self.assertEqual(max_x3, cfg3.dims[0] - 2)
        self.assertEqual(min_z3, 1)
        probe3 = state3.current_piece
        for delta in ((-1, 0, 0), (1, 0, 0), (0, 0, 1), (0, 0, -1)):
            for _ in range(4):
                probe3 = probe3.moved(delta)
                self.assertTrue(state3._can_exist(probe3))

        cfg4 = GameConfigND(
            dims=(10, 20, 8, 8),
            gravity_axis=1,
            piece_set_id=PIECE_SET_4D_STANDARD,
            challenge_layers=0,
            rng_seed=1337,
        )
        state4 = GameStateND(
            config=cfg4,
            board=BoardND(cfg4.dims),
            rng=random.Random(cfg4.rng_seed),
        )
        apply_tutorial_step_setup_nd(
            state4,
            cfg4,
            {
                "rng_seed": 3100,
                "starter_piece_id": "SKEW4_A",
                "spawn_min_visible_layer": 2,
                "bottom_layers_min": 1,
                "bottom_layers_max": 2,
                "required_event_count": 4,
            },
            lesson_id="tutorial_4d_core",
            step_id="move_x_neg",
        )
        self.assertIsNotNone(state4.current_piece)
        assert state4.current_piece is not None
        mapped4 = state4.current_piece_cells_mapped(include_above=True)
        max_x4 = max(coord[0] for coord in mapped4)
        min_z4 = min(coord[2] for coord in mapped4)
        max_w4 = max(coord[3] for coord in mapped4)
        self.assertEqual(max_x4, cfg4.dims[0] - 2)
        self.assertEqual(min_z4, 1)
        self.assertEqual(max_w4, cfg4.dims[3] - 2)
        probe4 = state4.current_piece
        for delta in (
            (-1, 0, 0, 0),
            (1, 0, 0, 0),
            (0, 0, 1, 0),
            (0, 0, -1, 0),
            (0, 0, 0, -1),
            (0, 0, 0, 1),
        ):
            for _ in range(4):
                probe4 = probe4.moved(delta)
                self.assertTrue(state4._can_exist(probe4))

    def test_nd_move_z_neg_spawn_is_feasible_for_four_away_moves(self) -> None:
        cfg3 = GameConfigND(
            dims=(10, 20, 10),
            gravity_axis=1,
            piece_set_id=PIECE_SET_3D_STANDARD,
            challenge_layers=0,
            rng_seed=1337,
        )
        state3 = GameStateND(
            config=cfg3,
            board=BoardND(cfg3.dims),
            rng=random.Random(cfg3.rng_seed),
        )
        apply_tutorial_step_setup_nd(
            state3,
            cfg3,
            {
                "rng_seed": 2102,
                "starter_piece_id": "SCREW3",
                "spawn_min_visible_layer": 2,
                "required_event_count": 4,
            },
            lesson_id="tutorial_3d_core",
            step_id="move_z_neg",
        )
        assert state3.current_piece is not None
        probe3 = state3.current_piece
        for _ in range(4):
            probe3 = probe3.moved((0, 0, 1))
            self.assertTrue(state3._can_exist(probe3))

        cfg4 = GameConfigND(
            dims=(10, 20, 8, 8),
            gravity_axis=1,
            piece_set_id=PIECE_SET_4D_STANDARD,
            challenge_layers=0,
            rng_seed=1337,
        )
        state4 = GameStateND(
            config=cfg4,
            board=BoardND(cfg4.dims),
            rng=random.Random(cfg4.rng_seed),
        )
        apply_tutorial_step_setup_nd(
            state4,
            cfg4,
            {
                "rng_seed": 3102,
                "starter_piece_id": "SKEW4_A",
                "spawn_min_visible_layer": 2,
                "required_event_count": 4,
            },
            lesson_id="tutorial_4d_core",
            step_id="move_z_neg",
        )
        assert state4.current_piece is not None
        probe4 = state4.current_piece
        for _ in range(4):
            probe4 = probe4.moved((0, 0, 1, 0))
            self.assertTrue(state4._can_exist(probe4))

    def test_apply_setup_2d_falls_back_when_piece_set_lacks_starter(self) -> None:
        cfg = GameConfig(
            width=10,
            height=20,
            gravity_axis=1,
            piece_set="random_cells_2d",
            challenge_layers=0,
            rng_seed=1337,
        )
        state = GameState(
            config=cfg,
            board=BoardND((cfg.width, cfg.height)),
            rng=random.Random(cfg.rng_seed),
        )
        setup = {
            "rng_seed": 1001,
            "starter_piece_id": "L",
            "spawn_min_visible_layer": 2,
            "bottom_layers_min": 1,
            "bottom_layers_max": 2,
        }
        apply_tutorial_step_setup_2d(
            state,
            cfg,
            setup,
            lesson_id="tutorial_2d_core",
            step_id="move_xy",
        )
        assert state.current_piece is not None
        self.assertEqual(state.current_piece.shape.name, "L")

    def test_apply_setup_2d_board_preset_creates_almost_full_line(self) -> None:
        cfg, state = _new_state_2d()
        setup = {
            "rng_seed": 1003,
            "starter_piece_id": "L",
            "spawn_min_visible_layer": 2,
            "board_preset": "2d_almost_line",
        }
        apply_tutorial_step_setup_2d(
            state,
            cfg,
            setup,
            lesson_id="tutorial_2d_core",
            step_id="clear_line",
        )
        y = cfg.height - 1
        occupied = [coord for coord in state.board.cells if coord[1] == y]
        self.assertEqual(len(occupied), cfg.width - 1)

    def test_apply_setup_2d_line_i_preset_creates_four_gap_target(self) -> None:
        cfg, state = _new_state_2d()
        apply_tutorial_step_setup_2d(
            state,
            cfg,
            {
                "rng_seed": 1011,
                "starter_piece_id": "I",
                "spawn_min_visible_layer": 2,
                "board_preset": "2d_almost_line_i",
            },
            lesson_id="tutorial_2d_core",
            step_id="line_fill",
        )
        y = cfg.height - 1
        empty = [x for x in range(cfg.width) if (x, y) not in state.board.cells]
        self.assertEqual(len(empty), 4)
        self.assertEqual(empty, list(range(empty[0], empty[0] + 4)))

    def test_goal_stages_spawn_piece_three_layers_above_target_2d(self) -> None:
        cfg, state = _new_state_2d()
        apply_tutorial_step_setup_2d(
            state,
            cfg,
            {
                "rng_seed": 1011,
                "starter_piece_id": "I",
                "spawn_min_visible_layer": 2,
                "board_preset": "2d_almost_line_i",
            },
            lesson_id="tutorial_2d_core",
            step_id="line_fill",
        )
        assert state.current_piece is not None
        mapped_line = state.current_piece_cells_mapped(include_above=True)
        self.assertEqual(min(y for _, y in mapped_line), cfg.height - 4)

        cfg2, state2 = _new_state_2d()
        apply_tutorial_step_setup_2d(
            state2,
            cfg2,
            {
                "rng_seed": 1012,
                "starter_piece_id": "O",
                "spawn_min_visible_layer": 2,
                "board_preset": "2d_almost_full_clear_o",
            },
            lesson_id="tutorial_2d_core",
            step_id="full_clear_bonus",
        )
        assert state2.current_piece is not None
        mapped_full = state2.current_piece_cells_mapped(include_above=True)
        self.assertEqual(min(y for _, y in mapped_full), cfg2.height - 5)

    def test_full_clear_bonus_presets_assign_expected_starter_piece(self) -> None:
        cfg2, state2 = _new_state_2d()
        apply_tutorial_step_setup_2d(
            state2,
            cfg2,
            {
                "rng_seed": 1012,
                "starter_piece_id": "O",
                "spawn_min_visible_layer": 2,
                "board_preset": "2d_almost_full_clear_o",
            },
            lesson_id="tutorial_2d_core",
            step_id="full_clear_bonus",
        )
        assert state2.current_piece is not None
        self.assertEqual(state2.current_piece.shape.name, "O")
        filled_levels_2d = {coord[1] for coord in state2.board.cells}
        self.assertEqual(filled_levels_2d, {cfg2.height - 2, cfg2.height - 1})
        self.assertEqual(len(state2.board.cells), (cfg2.width * 2) - 4)

        cfg3, state3 = _new_state_3d()
        apply_tutorial_step_setup_nd(
            state3,
            cfg3,
            {
                "rng_seed": 2012,
                "starter_piece_id": "O3",
                "spawn_min_visible_layer": 2,
                "board_preset": "3d_almost_full_clear_o3",
            },
            lesson_id="tutorial_3d_core",
            step_id="full_clear_bonus",
        )
        assert state3.current_piece is not None
        self.assertEqual(state3.current_piece.shape.name, "O3")
        filled_levels_3d = {coord[cfg3.gravity_axis] for coord in state3.board.cells}
        self.assertEqual(filled_levels_3d, {cfg3.dims[1] - 2, cfg3.dims[1] - 1})
        layer_cell_count_3d = cfg3.dims[0] * cfg3.dims[2]
        self.assertEqual(len(state3.board.cells), (2 * layer_cell_count_3d) - 4)

        cfg4, state4 = _new_state_4d()
        apply_tutorial_step_setup_nd(
            state4,
            cfg4,
            {
                "rng_seed": 3012,
                "starter_piece_id": "CROSS4",
                "spawn_min_visible_layer": 2,
                "board_preset": "4d_almost_full_clear_cross4",
            },
            lesson_id="tutorial_4d_core",
            step_id="full_clear_bonus",
        )
        assert state4.current_piece is not None
        self.assertEqual(state4.current_piece.shape.name, "CROSS4")

    def test_goal_stages_spawn_piece_three_layers_above_target_nd(self) -> None:
        cfg3, state3 = _new_state_3d()
        apply_tutorial_step_setup_nd(
            state3,
            cfg3,
            {
                "rng_seed": 2201,
                "starter_piece_id": "SCREW3",
                "spawn_min_visible_layer": 2,
                "board_preset": "3d_almost_layer_screw3",
            },
            lesson_id="tutorial_3d_core",
            step_id="layer_fill",
        )
        assert state3.current_piece is not None
        mapped3 = state3.current_piece_cells_mapped(include_above=True)
        self.assertEqual(
            min(coord[cfg3.gravity_axis] for coord in mapped3),
            cfg3.dims[cfg3.gravity_axis] - 4,
        )

        cfg4, state4 = _new_state_4d()
        apply_tutorial_step_setup_nd(
            state4,
            cfg4,
            {
                "rng_seed": 3301,
                "starter_piece_id": "SKEW4_A",
                "spawn_min_visible_layer": 2,
                "board_preset": "4d_almost_hyper_layer_skew4",
            },
            lesson_id="tutorial_4d_core",
            step_id="hyper_layer_fill",
        )
        assert state4.current_piece is not None
        mapped4 = state4.current_piece_cells_mapped(include_above=True)
        self.assertEqual(
            min(coord[cfg4.gravity_axis] for coord in mapped4),
            cfg4.dims[cfg4.gravity_axis] - 4,
        )

    def test_camera_only_setup_keeps_board_and_forces_visible_piece_nd(self) -> None:
        cfg, state = _new_state_3d()
        before_cells = dict(state.board.cells)
        apply_tutorial_step_setup_nd(
            state,
            cfg,
            {"camera_preset": "tutorial_3d_default", "rng_seed": 2001},
            lesson_id="tutorial_3d_core",
            step_id="camera_controls",
        )
        self.assertEqual(before_cells, state.board.cells)
        mapped = state.current_piece_cells_mapped(include_above=True)
        self.assertTrue(mapped)
        self.assertTrue(all(coord[cfg.gravity_axis] >= 0 for coord in mapped))
        self.assertGreaterEqual(min(coord[cfg.gravity_axis] for coord in mapped), 2)

    def test_layer_clear_presets_leave_expected_hole_counts(self) -> None:
        cfg3, state3 = _new_state_3d()
        apply_tutorial_step_setup_nd(
            state3,
            cfg3,
            {
                "rng_seed": 2010,
                "starter_piece_id": "SCREW3",
                "spawn_min_visible_layer": 2,
                "board_preset": "3d_almost_layer_screw3",
            },
            lesson_id="tutorial_3d_core",
            step_id="target_drop",
        )
        target_level_3d = cfg3.dims[cfg3.gravity_axis] - 1
        filled_top_3d = [
            coord
            for coord in state3.board.cells
            if coord[cfg3.gravity_axis] == target_level_3d
        ]
        layer_size_3d = cfg3.dims[0] * cfg3.dims[2]
        self.assertEqual(len(filled_top_3d), layer_size_3d - 2)

        cfg4, state4 = _new_state_4d()
        apply_tutorial_step_setup_nd(
            state4,
            cfg4,
            {
                "rng_seed": 3010,
                "starter_piece_id": "SKEW4_A",
                "spawn_min_visible_layer": 2,
                "board_preset": "4d_almost_hyper_layer_skew4",
            },
            lesson_id="tutorial_4d_core",
            step_id="target_drop",
        )
        target_level_4d = cfg4.dims[cfg4.gravity_axis] - 1
        filled_top_4d = [
            coord
            for coord in state4.board.cells
            if coord[cfg4.gravity_axis] == target_level_4d
        ]
        layer_size_4d = cfg4.dims[0] * cfg4.dims[2] * cfg4.dims[3]
        self.assertEqual(len(filled_top_4d), layer_size_4d - 3)

    def test_4d_move_w_steps_spawn_piece_with_legal_w_move(self) -> None:
        for step_id, expected_delta in (("move_w_neg", -1), ("move_w_pos", 1)):
            cfg, state = _new_state_4d()
            apply_tutorial_step_setup_nd(
                state,
                cfg,
                {
                    "rng_seed": 3104 if expected_delta < 0 else 3105,
                    "starter_piece_id": "SKEW4_A",
                    "spawn_min_visible_layer": 2,
                    "bottom_layers_min": 1,
                    "bottom_layers_max": 2,
                },
                lesson_id="tutorial_4d_core",
                step_id=step_id,
            )
            self.assertIsNotNone(state.current_piece)
            assert state.current_piece is not None
            moved = state.current_piece.moved((0, 0, 0, expected_delta))
            self.assertTrue(state._can_exist(moved), msg=f"{step_id} not legal from spawn")


if __name__ == "__main__":
    unittest.main()
