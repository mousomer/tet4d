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

    def test_camera_only_setup_does_not_mutate_board_or_piece_nd(self) -> None:
        cfg, state = _new_state_3d()
        before_cells = dict(state.board.cells)
        before_piece = tuple(state.current_piece_cells_mapped(include_above=True))
        apply_tutorial_step_setup_nd(
            state,
            cfg,
            {"camera_preset": "tutorial_3d_default", "rng_seed": 2001},
            lesson_id="tutorial_3d_core",
            step_id="camera_controls",
        )
        self.assertEqual(before_cells, state.board.cells)
        self.assertEqual(
            before_piece,
            tuple(state.current_piece_cells_mapped(include_above=True)),
        )


if __name__ == "__main__":
    unittest.main()
