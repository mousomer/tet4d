from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch
import random

try:
    import pygame
except (
    ModuleNotFoundError
):  # pragma: no cover - exercised in environments without pygame-ce
    pygame = None

if pygame is None:  # pragma: no cover - exercised in environments without pygame-ce
    raise unittest.SkipTest("pygame-ce is required for gameplay replay tests")

from tet4d.ui.pygame import front2d_game as front2d
from tet4d.ui.pygame import frontend_nd_input, frontend_nd_state
from tet4d.ui.pygame import front3d_game
from tet4d.ui.pygame import front4d_game
from tet4d.engine.gameplay.game2d import Action, GameConfig
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.ui.pygame.keybindings import (
    CAMERA_KEYS_3D,
    CAMERA_KEYS_4D,
    EXPLORER_KEYS_2D,
    EXPLORER_KEYS_3D,
    EXPLORER_KEYS_4D,
    KEYS_2D,
    KEYS_3D,
    KEYS_4D,
    SYSTEM_KEYS,
)
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.topology_explorer.presets import axis_wrap_profile
from tet4d.ui.pygame.topology_lab.app import (
    build_explorer_playground_config,
    build_explorer_playground_launch,
)
from tests.unit.engine._translation_contract import (
    assert_repeated_translation_progress,
)


def _keydown(key: int) -> pygame.event.Event:
    if pygame is None:
        raise RuntimeError("pygame-ce is required for gameplay replay tests")
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def _state_signature_2d(state) -> tuple:
    board = tuple(sorted(state.board.cells.items()))
    if state.current_piece is None:
        piece = None
    else:
        piece = (
            state.current_piece.shape.name,
            state.current_piece.pos,
            state.current_piece.rotation,
            tuple(sorted(state.current_piece.cells())),
        )
    next_bag = tuple(shape.name for shape in state.next_bag)
    return (
        state.score,
        state.lines_cleared,
        state.game_over,
        board,
        piece,
        next_bag,
    )


def _state_signature_nd(state) -> tuple:
    board = tuple(sorted(state.board.cells.items()))
    if state.current_piece is None:
        piece = None
    else:
        piece = (
            state.current_piece.shape.name,
            state.current_piece.pos,
            tuple(sorted(state.current_piece.rel_blocks)),
            tuple(sorted(state.current_piece.cells())),
        )
    next_bag = tuple(shape.name for shape in state.next_bag)
    return (
        state.score,
        state.lines_cleared,
        state.game_over,
        board,
        piece,
        next_bag,
    )


class TestGameplayReplay(unittest.TestCase):
    def _assert_continue(self, result, _index: int) -> None:
        self.assertEqual(result, "continue")

    def _key_for(self, bindings: dict[str, tuple[int, ...]], action: str) -> int:
        keys = bindings.get(action, ())
        self.assertTrue(keys, f"missing key binding for action: {action}")
        return keys[0]

    def test_replay_determinism_2d(self):
        cfg = GameConfig(width=10, height=20, gravity_axis=1, speed_level=1)
        script = [
            self._key_for(KEYS_2D, action)
            for action in (
                "move_x_neg",
                "rotate_xy_pos",
                "soft_drop",
                "move_x_pos",
                "rotate_xy_neg",
                "hard_drop",
                "move_x_pos",
                "soft_drop",
                "hard_drop",
            )
        ] * 5

        def run_once() -> tuple:
            state = front2d.create_initial_state(cfg)
            for key in script:
                result = front2d.handle_game_keydown(_keydown(key), state, cfg)
                self.assertEqual(result, "continue")
                state.step(Action.NONE)
            return _state_signature_2d(state)

        self.assertEqual(run_once(), run_once())

    def test_create_initial_state_2d_rng_mode_routing(self):
        fixed_cfg = GameConfig(
            width=10,
            height=20,
            gravity_axis=1,
            speed_level=1,
            rng_mode="fixed_seed",
            rng_seed=4242,
        )
        with patch("tet4d.ui.pygame.front2d_session.random.Random", side_effect=random.Random) as ctor:
            state = front2d.create_initial_state(fixed_cfg)
        self.assertIsNotNone(state.current_piece)
        ctor.assert_called_once_with(4242)

        true_random_cfg = GameConfig(
            width=10,
            height=20,
            gravity_axis=1,
            speed_level=1,
            rng_mode="true_random",
            rng_seed=4242,
        )
        with patch("tet4d.ui.pygame.front2d_session.random.Random", side_effect=random.Random) as ctor:
            state = front2d.create_initial_state(true_random_cfg)
        self.assertIsNotNone(state.current_piece)
        ctor.assert_called_once_with()

    def test_replay_determinism_3d(self):
        cfg = GameConfigND(dims=(6, 14, 6), gravity_axis=1, speed_level=1)
        script = [
            self._key_for(KEYS_3D, action)
            for action in (
                "move_x_neg",
                "move_z_neg",
                "rotate_xy_pos",
                "soft_drop",
                "rotate_xz_pos",
                "move_x_pos",
                "rotate_yz_neg",
                "hard_drop",
                "move_z_pos",
                "hard_drop",
            )
        ] * 4

        def run_once() -> tuple:
            state = front3d_game.create_initial_state(cfg)
            for key in script:
                result = front3d_game.handle_game_keydown(_keydown(key), state, cfg)
                self.assertEqual(result, "continue")
                state.step_gravity()
            return _state_signature_nd(state)

        self.assertEqual(run_once(), run_once())

    def test_create_initial_state_nd_rng_mode_routing(self):
        fixed_cfg = GameConfigND(
            dims=(6, 14, 6),
            gravity_axis=1,
            speed_level=1,
            rng_mode="fixed_seed",
            rng_seed=2024,
        )
        with patch(
            "tet4d.ui.pygame.frontend_nd_state.random.Random", side_effect=random.Random
        ) as ctor:
            state = frontend_nd_state.create_initial_state(fixed_cfg)
        self.assertIsNotNone(state.current_piece)
        ctor.assert_called_once_with(2024)

        true_random_cfg = GameConfigND(
            dims=(6, 14, 6),
            gravity_axis=1,
            speed_level=1,
            rng_mode="true_random",
            rng_seed=2024,
        )
        with patch(
            "tet4d.ui.pygame.frontend_nd_state.random.Random", side_effect=random.Random
        ) as ctor:
            state = frontend_nd_state.create_initial_state(true_random_cfg)
        self.assertIsNotNone(state.current_piece)
        ctor.assert_called_once_with()

    def test_exploration_mode_disables_gravity_and_locking_2d(self) -> None:
        cfg = GameConfig(
            width=8, height=8, gravity_axis=1, speed_level=1, exploration_mode=True
        )
        state = front2d.create_initial_state(cfg)
        self.assertFalse(state.game_over)
        piece_before = state.current_piece
        y_before = (
            state.current_piece.pos[1] if state.current_piece is not None else None
        )

        # Gravity ticks do nothing in exploration mode.
        state.step(Action.NONE)
        self.assertEqual(len(state.board.cells), 0)
        self.assertEqual(state.lines_cleared, 0)
        self.assertEqual(state.score, 0)

        move_up = self._key_for(EXPLORER_KEYS_2D, "move_up")
        self.assertEqual(
            front2d.handle_game_keydown(_keydown(move_up), state, cfg), "continue"
        )
        if state.current_piece is not None and y_before is not None:
            self.assertEqual(state.current_piece.pos[1], y_before - 1)

        move_down = self._key_for(EXPLORER_KEYS_2D, "move_down")
        self.assertEqual(
            front2d.handle_game_keydown(_keydown(move_down), state, cfg), "continue"
        )
        if state.current_piece is not None and y_before is not None:
            self.assertEqual(state.current_piece.pos[1], y_before)

        # Hard drop cycles to next piece without locking into board.
        hard_drop = self._key_for(KEYS_2D, "hard_drop")
        self.assertEqual(
            front2d.handle_game_keydown(_keydown(hard_drop), state, cfg), "continue"
        )
        self.assertEqual(len(state.board.cells), 0)
        self.assertEqual(state.lines_cleared, 0)
        self.assertEqual(state.score, 0)
        self.assertIsNot(state.current_piece, piece_before)

    def test_exploration_mode_2d_up_arrow_moves_up_instead_of_rotating(self) -> None:
        cfg = GameConfig(
            width=8, height=8, gravity_axis=1, speed_level=1, exploration_mode=True
        )
        state = front2d.create_initial_state(cfg)
        self.assertIsNotNone(state.current_piece)
        assert state.current_piece is not None
        pos_before = state.current_piece.pos
        cells_before = tuple(sorted(state.current_piece.cells()))

        self.assertEqual(
            front2d.handle_game_keydown(_keydown(pygame.K_UP), state, cfg), "continue"
        )

        assert state.current_piece is not None
        self.assertEqual(state.current_piece.pos, (pos_before[0], pos_before[1] - 1))
        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            tuple((x, y - 1) for x, y in cells_before),
        )

    def test_exploration_mode_3d_live_move_up_uses_real_handler(self) -> None:
        cfg = GameConfigND(
            dims=(8, 8, 8), gravity_axis=1, speed_level=1, exploration_mode=True
        )
        state = front3d_game.create_initial_state(cfg)
        self.assertIsNotNone(state.current_piece)
        assert state.current_piece is not None
        pos_before = state.current_piece.pos

        move_up = self._key_for(EXPLORER_KEYS_3D, "move_up")
        self.assertEqual(
            front3d_game.handle_game_keydown(_keydown(move_up), state, cfg),
            "continue",
        )

        assert state.current_piece is not None
        self.assertEqual(state.current_piece.pos[1], pos_before[1] - 1)

    def test_exploration_mode_4d_live_move_up_uses_real_handler(self) -> None:
        cfg = GameConfigND(
            dims=(8, 8, 8, 8), gravity_axis=1, speed_level=1, exploration_mode=True
        )
        loop = front4d_game.LoopContext4D.create(cfg)
        self.assertIsNotNone(loop.state.current_piece)
        assert loop.state.current_piece is not None
        pos_before = loop.state.current_piece.pos

        move_up = self._key_for(EXPLORER_KEYS_4D, "move_up")
        self.assertEqual(loop.keydown_handler(_keydown(move_up)), "continue")

        assert loop.state.current_piece is not None
        self.assertEqual(loop.state.current_piece.pos[1], pos_before[1] - 1)

    def test_exploration_mode_disables_gravity_and_locking_nd(self) -> None:
        cfg = GameConfigND(
            dims=(8, 8, 8, 8), gravity_axis=1, speed_level=1, exploration_mode=True
        )
        state = frontend_nd_state.create_initial_state(cfg)
        self.assertFalse(state.game_over)
        piece_before = state.current_piece
        pos_before = (
            state.current_piece.pos if state.current_piece is not None else None
        )

        state.step_gravity()
        self.assertEqual(len(state.board.cells), 0)
        self.assertEqual(state.lines_cleared, 0)
        self.assertEqual(state.score, 0)
        if state.current_piece is not None:
            self.assertEqual(state.current_piece.pos, pos_before)

        move_up = self._key_for(EXPLORER_KEYS_4D, "move_up")
        self.assertEqual(
            frontend_nd_input.handle_game_keydown(_keydown(move_up), state), "continue"
        )
        if state.current_piece is not None and pos_before is not None:
            self.assertEqual(state.current_piece.pos[1], pos_before[1] - 1)

        move_down = self._key_for(EXPLORER_KEYS_4D, "move_down")
        self.assertEqual(
            frontend_nd_input.handle_game_keydown(_keydown(move_down), state), "continue"
        )
        if state.current_piece is not None and pos_before is not None:
            self.assertEqual(state.current_piece.pos[1], pos_before[1])

        hard_drop = self._key_for(KEYS_4D, "hard_drop")
        self.assertEqual(
            frontend_nd_input.handle_game_keydown(_keydown(hard_drop), state), "continue"
        )
        self.assertEqual(len(state.board.cells), 0)
        self.assertEqual(state.lines_cleared, 0)
        self.assertEqual(state.score, 0)
        self.assertIsNot(state.current_piece, piece_before)

    def test_replay_determinism_4d(self):
        cfg = GameConfigND(dims=(6, 12, 6, 4), gravity_axis=1, speed_level=1)
        script = [
            self._key_for(KEYS_4D, action)
            for action in (
                "move_x_neg",
                "move_z_neg",
                "move_w_pos",
                "rotate_xy_pos",
                "rotate_xz_neg",
                "rotate_xw_pos",
                "rotate_yw_neg",
                "soft_drop",
                "hard_drop",
                "move_w_neg",
                "hard_drop",
            )
        ] * 4

        def run_once() -> tuple:
            state = frontend_nd_state.create_initial_state(cfg)
            for key in script:
                result = frontend_nd_input.handle_game_keydown(_keydown(key), state)
                self.assertEqual(result, "continue")
                state.step_gravity()
            return _state_signature_nd(state)

        self.assertEqual(run_once(), run_once())

    def test_repeated_translation_contract_matches_main_and_explorer_2d(self):
        cases = (
            (
                "main_2d_keys",
                GameConfig(width=8, height=8, gravity_axis=1, speed_level=1),
                PieceShape2D("dot", [(0, 0)], color_id=4),
                (4, 3),
                self._key_for(KEYS_2D, "move_x_neg"),
                [((3, 3),), ((2, 3),), ((1, 3),)],
            ),
            (
                "explorer_2d_keys",
                GameConfig(
                    width=8,
                    height=8,
                    gravity_axis=1,
                    speed_level=1,
                    exploration_mode=True,
                ),
                PieceShape2D("dot", [(0, 0)], color_id=4),
                (4, 3),
                self._key_for(KEYS_2D, "move_x_neg"),
                [((3, 3),), ((2, 3),), ((1, 3),)],
            ),
            (
                "main_2d_keys_multicell",
                GameConfig(width=8, height=8, gravity_axis=1, speed_level=1),
                PieceShape2D("L", [(-1, 0), (0, 0), (1, 0), (1, 1)], color_id=6),
                (4, 3),
                self._key_for(KEYS_2D, "move_x_neg"),
                [
                    ((2, 3), (3, 3), (4, 3), (4, 4)),
                    ((1, 3), (2, 3), (3, 3), (3, 4)),
                    ((0, 3), (1, 3), (2, 3), (2, 4)),
                ],
            ),
            (
                "explorer_2d_keys_multicell",
                GameConfig(
                    width=8,
                    height=8,
                    gravity_axis=1,
                    speed_level=1,
                    exploration_mode=True,
                ),
                PieceShape2D("L", [(-1, 0), (0, 0), (1, 0), (1, 1)], color_id=6),
                (4, 3),
                self._key_for(KEYS_2D, "move_x_neg"),
                [
                    ((2, 3), (3, 3), (4, 3), (4, 4)),
                    ((1, 3), (2, 3), (3, 3), (3, 4)),
                    ((0, 3), (1, 3), (2, 3), (2, 4)),
                ],
            ),
        )
        for label, cfg, shape, start_pos, key, expected in cases:
            with self.subTest(mode=label):
                state = front2d.create_initial_state(cfg)
                state.board.cells.clear()
                state.current_piece = ActivePiece2D(shape, pos=start_pos, rotation=0)
                assert_repeated_translation_progress(
                    self,
                    step=lambda: front2d.handle_game_keydown(_keydown(key), state, cfg),
                    signature=lambda: state.current_piece_cells_mapped(include_above=False),
                    expected_signatures=expected,
                    label=label,
                    result_assertion=lambda case, result, index: case._assert_continue(result, index),
                )

    def test_repeated_translation_contract_matches_main_and_explorer_nd(self):
        cases = (
            (
                "main_3d_keys",
                GameConfigND(dims=(8, 8, 8), gravity_axis=1, speed_level=1),
                PieceShapeND("dot3", ((0, 0, 0),), color_id=6),
                (4, 3, 4),
                self._key_for(KEYS_3D, "move_z_neg"),
                [((4, 3, 3),), ((4, 3, 2),), ((4, 3, 1),)],
            ),
            (
                "explorer_3d_keys",
                GameConfigND(
                    dims=(8, 8, 8),
                    gravity_axis=1,
                    speed_level=1,
                    exploration_mode=True,
                ),
                PieceShapeND("dot3", ((0, 0, 0),), color_id=6),
                (4, 3, 4),
                self._key_for(KEYS_3D, "move_z_neg"),
                [((4, 3, 3),), ((4, 3, 2),), ((4, 3, 1),)],
            ),
            (
                "explorer_3d_keys_multicell",
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
                self._key_for(KEYS_3D, "move_z_neg"),
                [
                    ((3, 3, 3), (4, 3, 3), (5, 3, 3), (5, 4, 3)),
                    ((3, 3, 2), (4, 3, 2), (5, 3, 2), (5, 4, 2)),
                    ((3, 3, 1), (4, 3, 1), (5, 3, 1), (5, 4, 1)),
                ],
            ),
            (
                "main_4d_keys",
                GameConfigND(dims=(8, 8, 8, 6), gravity_axis=1, speed_level=1),
                PieceShapeND("dot4", ((0, 0, 0, 0),), color_id=7),
                (4, 3, 4, 2),
                self._key_for(KEYS_4D, "move_w_pos"),
                [((4, 3, 4, 3),), ((4, 3, 4, 4),), ((4, 3, 4, 5),)],
            ),
            (
                "explorer_4d_keys",
                GameConfigND(
                    dims=(8, 8, 8, 6),
                    gravity_axis=1,
                    speed_level=1,
                    exploration_mode=True,
                ),
                PieceShapeND("dot4", ((0, 0, 0, 0),), color_id=7),
                (4, 3, 4, 2),
                self._key_for(KEYS_4D, "move_w_pos"),
                [((4, 3, 4, 3),), ((4, 3, 4, 4),), ((4, 3, 4, 5),)],
            ),
            (
                "explorer_4d_keys_multicell",
                GameConfigND(
                    dims=(8, 8, 8, 6),
                    gravity_axis=1,
                    speed_level=1,
                    exploration_mode=True,
                ),
                PieceShapeND(
                    "el4",
                    ((-1, 0, 0, 0), (0, 0, 0, 0), (1, 0, 0, 0), (1, 0, 0, 1)),
                    color_id=8,
                ),
                (4, 3, 4, 2),
                self._key_for(KEYS_4D, "move_w_pos"),
                [
                    ((3, 3, 4, 3), (4, 3, 4, 3), (5, 3, 4, 3), (5, 3, 4, 4)),
                    ((3, 3, 4, 4), (4, 3, 4, 4), (5, 3, 4, 4), (5, 3, 4, 5)),
                ],
            ),
        )
        for label, cfg, shape, start_pos, key, expected in cases:
            with self.subTest(mode=label):
                state = frontend_nd_state.create_initial_state(cfg)
                state.board.cells.clear()
                state.current_piece = ActivePieceND.from_shape(shape, pos=start_pos)
                assert_repeated_translation_progress(
                    self,
                    step=lambda: frontend_nd_input.handle_game_keydown(_keydown(key), state),
                    signature=lambda: state.current_piece_cells_mapped(include_above=False),
                    expected_signatures=expected,
                    label=label,
                    result_assertion=lambda case, result, index: case._assert_continue(result, index),
                )

    def test_2d_controls_smoke(self):
        cfg = GameConfig(width=8, height=16, gravity_axis=1, speed_level=1)
        state = front2d.create_initial_state(cfg)
        state.board.cells.clear()
        state.current_piece = ActivePiece2D(
            PieceShape2D("tri", [(0, 0), (1, 0), (0, 1)], color_id=8),
            pos=(4, 1),
            rotation=0,
        )

        move_left = self._key_for(KEYS_2D, "move_x_neg")
        rotate = self._key_for(KEYS_2D, "rotate_xy_pos")
        hard_drop = self._key_for(KEYS_2D, "hard_drop")

        self.assertEqual(
            front2d.handle_game_keydown(_keydown(move_left), state, cfg), "continue"
        )
        self.assertEqual(state.current_piece.pos, (3, 1))

        before_cells = tuple(sorted(state.current_piece.cells()))
        self.assertEqual(
            front2d.handle_game_keydown(_keydown(rotate), state, cfg), "continue"
        )
        self.assertNotEqual(tuple(sorted(state.current_piece.cells())), before_cells)

        self.assertEqual(
            front2d.handle_game_keydown(_keydown(hard_drop), state, cfg), "continue"
        )
        self.assertGreater(len(state.board.cells), 0)

        quit_key = self._key_for(SYSTEM_KEYS, "quit")
        expected_quit_result = (
            "menu" if int(quit_key) == int(pygame.K_ESCAPE) else "quit"
        )
        self.assertEqual(
            front2d.handle_game_keydown(_keydown(quit_key), state, cfg),
            expected_quit_result,
        )
        self.assertEqual(
            front2d.handle_game_keydown(
                _keydown(self._key_for(SYSTEM_KEYS, "menu")), state, cfg
            ),
            "menu",
        )
        self.assertEqual(
            front2d.handle_game_keydown(
                _keydown(self._key_for(SYSTEM_KEYS, "restart")), state, cfg
            ),
            "restart",
        )
        self.assertEqual(
            front2d.handle_game_keydown(
                _keydown(self._key_for(SYSTEM_KEYS, "help")), state, cfg
            ),
            "help",
        )
        self.assertEqual(
            front2d.handle_game_keydown(
                _keydown(self._key_for(SYSTEM_KEYS, "toggle_grid")), state, cfg
            ),
            "toggle_grid",
        )

    def test_explorer_3d_frontend_repeated_left_translation_live(self):
        cfg = GameConfigND(
            dims=(6, 10, 4),
            gravity_axis=1,
            speed_level=1,
            exploration_mode=True,
            explorer_topology_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
        )
        state = front3d_game.create_initial_state(cfg)
        state.board.cells.clear()
        state.current_piece = ActivePieceND.from_shape(
            PieceShapeND("bar3", ((0, 0, 0), (1, 0, 0), (2, 0, 0)), color_id=8),
            pos=(2, 2, 1),
        )
        camera = front3d_game.Camera3D()
        camera.yaw_deg = 0.0
        move_x_neg = self._key_for(KEYS_3D, "move_x_neg")
        start_cells = tuple(sorted(state.current_piece.cells()))
        expected = [
            tuple(sorted((x - 1, y, z) for x, y, z in start_cells)),
            tuple(sorted((x - 2, y, z) for x, y, z in start_cells)),
        ]

        assert_repeated_translation_progress(
            self,
            step=lambda: front3d_game.handle_game_keydown(
                _keydown(move_x_neg), state, camera
            ),
            signature=lambda: tuple(sorted(state.current_piece.cells())),
            expected_signatures=expected,
            label="explorer_3d_frontend_left",
            result_assertion=lambda case, result, index: case._assert_continue(result, index),
        )

    def test_explorer_4d_frontend_repeated_left_translation_live(self):
        cfg = GameConfigND(
            dims=(6, 10, 6, 4),
            gravity_axis=1,
            speed_level=1,
            exploration_mode=True,
            explorer_topology_profile=axis_wrap_profile(dimension=4, wrapped_axes=(0,)),
        )
        state = frontend_nd_state.create_initial_state(cfg)
        state.board.cells.clear()
        state.current_piece = ActivePieceND.from_shape(
            PieceShapeND("bar4", ((0, 0, 0, 0), (1, 0, 0, 0), (2, 0, 0, 0)), color_id=8),
            pos=(2, 2, 1, 1),
        )
        loop = front4d_game.LoopContext4D.create(cfg)
        loop.state = state
        loop.view.yaw_deg = 0.0
        move_x_neg = self._key_for(KEYS_4D, "move_x_neg")
        start_cells = tuple(sorted(loop.state.current_piece.cells()))
        expected = [
            tuple(sorted((x - 1, y, z, w) for x, y, z, w in start_cells)),
            tuple(sorted((x - 2, y, z, w) for x, y, z, w in start_cells)),
        ]

        assert_repeated_translation_progress(
            self,
            step=lambda: loop.keydown_handler(_keydown(move_x_neg)),
            signature=lambda: tuple(sorted(loop.state.current_piece.cells())),
            expected_signatures=expected,
            label="explorer_4d_frontend_left",
            result_assertion=lambda case, result, index: case._assert_continue(result, index),
        )

    def test_explorer_3d_playground_launch_repeated_left_translation_live(self):
        profile = axis_wrap_profile(dimension=3, wrapped_axes=(0,))
        launch = build_explorer_playground_launch(
            dimension=3,
            explorer_profile=profile,
            source_settings=SimpleNamespace(
                width=6,
                height=10,
                depth=4,
                piece_set_index=0,
                speed_level=1,
                random_mode_index=0,
                game_seed=1337,
            ),
        )
        cfg = build_explorer_playground_config(
            dimension=3,
            explorer_profile=profile,
            settings_snapshot=launch.settings_snapshot,
        )
        state = front3d_game.create_initial_state(cfg)
        state.board.cells.clear()
        state.current_piece = ActivePieceND.from_shape(
            PieceShapeND("bar3", ((0, 0, 0), (1, 0, 0), (2, 0, 0)), color_id=8),
            pos=(2, 2, 1),
        )
        camera = front3d_game.Camera3D()
        camera.yaw_deg = 0.0
        move_x_neg = self._key_for(KEYS_3D, "move_x_neg")
        start_cells = tuple(sorted(state.current_piece.cells()))
        expected = [
            tuple(sorted((x - 1, y, z) for x, y, z in start_cells)),
            tuple(sorted((x - 2, y, z) for x, y, z in start_cells)),
        ]

        assert_repeated_translation_progress(
            self,
            step=lambda: front3d_game.handle_game_keydown(_keydown(move_x_neg), state, camera),
            signature=lambda: tuple(sorted(state.current_piece.cells())),
            expected_signatures=expected,
            label="explorer_3d_playground_left",
            result_assertion=lambda case, result, index: case._assert_continue(result, index),
        )

    def test_explorer_4d_playground_launch_repeated_left_translation_live(self):
        profile = axis_wrap_profile(dimension=4, wrapped_axes=(0,))
        launch = build_explorer_playground_launch(
            dimension=4,
            explorer_profile=profile,
            source_settings=SimpleNamespace(
                width=6,
                height=10,
                depth=6,
                fourth=4,
                piece_set_index=0,
                speed_level=1,
                random_mode_index=0,
                game_seed=1337,
            ),
        )
        cfg = build_explorer_playground_config(
            dimension=4,
            explorer_profile=profile,
            settings_snapshot=launch.settings_snapshot,
        )
        loop = front4d_game.LoopContext4D.create(cfg)
        loop.state.board.cells.clear()
        loop.state.current_piece = ActivePieceND.from_shape(
            PieceShapeND("bar4", ((0, 0, 0, 0), (1, 0, 0, 0), (2, 0, 0, 0)), color_id=8),
            pos=(2, 2, 1, 1),
        )
        loop.view.yaw_deg = 0.0
        move_x_neg = self._key_for(KEYS_4D, "move_x_neg")
        start_cells = tuple(sorted(loop.state.current_piece.cells()))
        expected = [
            tuple(sorted((x - 1, y, z, w) for x, y, z, w in start_cells)),
            tuple(sorted((x - 2, y, z, w) for x, y, z, w in start_cells)),
        ]

        assert_repeated_translation_progress(
            self,
            step=lambda: loop.keydown_handler(_keydown(move_x_neg)),
            signature=lambda: tuple(sorted(loop.state.current_piece.cells())),
            expected_signatures=expected,
            label="explorer_4d_playground_left",
            result_assertion=lambda case, result, index: case._assert_continue(result, index),
        )

    def test_3d_controls_and_camera_smoke(self):
        cfg = GameConfigND(dims=(6, 10, 6), gravity_axis=1, speed_level=1)
        state = front3d_game.create_initial_state(cfg)
        state.board.cells.clear()
        state.current_piece = ActivePieceND.from_shape(
            PieceShapeND("tri3", ((0, 0, 0), (1, 0, 0), (0, 1, 0)), color_id=8),
            pos=(3, 2, 3),
        )

        move_z_neg = self._key_for(KEYS_3D, "move_z_neg")
        rotate_xz = self._key_for(KEYS_3D, "rotate_xz_pos")
        hard_drop = self._key_for(KEYS_3D, "hard_drop")

        self.assertEqual(
            front3d_game.handle_game_keydown(_keydown(move_z_neg), state, cfg),
            "continue",
        )
        self.assertEqual(state.current_piece.pos, (3, 2, 4))

        before_blocks = tuple(sorted(state.current_piece.rel_blocks))
        self.assertEqual(
            front3d_game.handle_game_keydown(_keydown(rotate_xz), state, cfg),
            "continue",
        )
        self.assertNotEqual(
            tuple(sorted(state.current_piece.rel_blocks)), before_blocks
        )

        self.assertEqual(
            front3d_game.handle_game_keydown(_keydown(hard_drop), state, cfg),
            "continue",
        )
        self.assertGreater(len(state.board.cells), 0)

        self.assertEqual(
            front3d_game.handle_game_keydown(
                _keydown(self._key_for(SYSTEM_KEYS, "toggle_grid")), state, cfg
            ),
            "toggle_grid",
        )
        self.assertEqual(
            front3d_game.handle_game_keydown(
                _keydown(self._key_for(SYSTEM_KEYS, "help")), state, cfg
            ),
            "help",
        )

        camera = front3d_game.Camera3D()
        yaw_pos = self._key_for(CAMERA_KEYS_3D, "yaw_pos")
        self.assertTrue(front3d_game.handle_camera_keydown(_keydown(yaw_pos), camera))
        self.assertTrue(camera.animating)
        camera.step_animation(1000)
        self.assertFalse(camera.animating)
        overlay_dec = self._key_for(CAMERA_KEYS_3D, "overlay_alpha_dec")
        overlay_dec_hits: list[int] = []
        self.assertTrue(
            front3d_game.handle_camera_key(
                overlay_dec,
                camera,
                on_overlay_alpha_dec=lambda: overlay_dec_hits.append(1),
            )
        )
        self.assertEqual(len(overlay_dec_hits), 1)

    def test_4d_controls_and_view_smoke(self):
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd_state.create_initial_state(cfg)
        state.board.cells.clear()
        state.current_piece = ActivePieceND.from_shape(
            PieceShapeND(
                "tri4",
                ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)),
                color_id=8,
            ),
            pos=(2, 2, 3, 1),
        )

        move_z_neg = self._key_for(KEYS_4D, "move_z_neg")
        move_w_pos = self._key_for(KEYS_4D, "move_w_pos")
        rotate_xw = self._key_for(KEYS_4D, "rotate_xw_pos")
        hard_drop = self._key_for(KEYS_4D, "hard_drop")

        before_blocks = tuple(sorted(state.current_piece.rel_blocks))
        self.assertEqual(
            frontend_nd_input.handle_game_keydown(_keydown(move_z_neg), state), "continue"
        )
        self.assertEqual(state.current_piece.pos, (2, 2, 2, 1))
        self.assertEqual(tuple(sorted(state.current_piece.rel_blocks)), before_blocks)

        self.assertEqual(
            frontend_nd_input.handle_game_keydown(_keydown(move_w_pos), state), "continue"
        )
        self.assertEqual(state.current_piece.pos, (2, 2, 2, 2))

        self.assertEqual(
            frontend_nd_input.handle_game_keydown(_keydown(rotate_xw), state), "continue"
        )
        self.assertNotEqual(
            tuple(sorted(state.current_piece.rel_blocks)), before_blocks
        )

        self.assertEqual(
            frontend_nd_input.handle_game_keydown(_keydown(hard_drop), state), "continue"
        )
        self.assertGreater(len(state.board.cells), 0)

        self.assertEqual(
            frontend_nd_input.handle_game_keydown(
                _keydown(self._key_for(SYSTEM_KEYS, "toggle_grid")), state
            ),
            "toggle_grid",
        )
        self.assertEqual(
            frontend_nd_input.handle_game_keydown(
                _keydown(self._key_for(SYSTEM_KEYS, "help")), state
            ),
            "help",
        )

        view = front4d_game.LayerView3D()
        pitch_neg = self._key_for(CAMERA_KEYS_4D, "pitch_neg")
        self.assertTrue(front4d_game.handle_view_keydown(_keydown(pitch_neg), view))
        self.assertTrue(view.animating)
        view.step_animation(1000)
        self.assertFalse(view.animating)

        view_xw_pos = self._key_for(CAMERA_KEYS_4D, "view_xw_pos")
        self.assertTrue(front4d_game.handle_view_keydown(_keydown(view_xw_pos), view))
        self.assertTrue(view.hyper_animating)
        view.step_animation(1000)
        self.assertFalse(view.hyper_animating)
        self.assertAlmostEqual(view.xw_deg, 90.0, places=3)

        view_zw_neg = self._key_for(CAMERA_KEYS_4D, "view_zw_neg")
        self.assertTrue(front4d_game.handle_view_keydown(_keydown(view_zw_neg), view))
        self.assertTrue(view.hyper_animating)
        view.step_animation(1000)
        self.assertFalse(view.hyper_animating)
        self.assertAlmostEqual(view.zw_deg, 270.0, places=3)

        reset = self._key_for(CAMERA_KEYS_4D, "reset")
        self.assertTrue(front4d_game.handle_view_keydown(_keydown(reset), view))
        self.assertAlmostEqual(view.xw_deg, 0.0, places=3)
        self.assertAlmostEqual(view.zw_deg, 0.0, places=3)
        overlay_inc = self._key_for(CAMERA_KEYS_4D, "overlay_alpha_inc")
        overlay_inc_hits: list[int] = []
        self.assertTrue(
            front4d_game.handle_view_key(
                overlay_inc,
                view,
                on_overlay_alpha_inc=lambda: overlay_inc_hits.append(1),
            )
        )
        self.assertEqual(len(overlay_inc_hits), 1)

    def test_4d_replay_invariance_with_view_only_turns(self):
        cfg = GameConfigND(dims=(6, 12, 6, 4), gravity_axis=1, speed_level=1)
        game_script = [
            self._key_for(KEYS_4D, action)
            for action in (
                "move_x_neg",
                "move_z_neg",
                "move_w_pos",
                "rotate_xy_pos",
                "rotate_xz_neg",
                "rotate_xw_pos",
                "soft_drop",
                "hard_drop",
                "move_w_neg",
                "hard_drop",
            )
        ] * 3
        view_script = [
            self._key_for(CAMERA_KEYS_4D, "view_xw_pos"),
            self._key_for(CAMERA_KEYS_4D, "view_zw_neg"),
            self._key_for(CAMERA_KEYS_4D, "view_xw_neg"),
            self._key_for(CAMERA_KEYS_4D, "view_zw_pos"),
        ]

        def run_once(*, with_view_turns: bool) -> tuple:
            state = frontend_nd_state.create_initial_state(cfg)
            view = front4d_game.LayerView3D()
            for idx, key in enumerate(game_script):
                result = frontend_nd_input.handle_game_keydown(_keydown(key), state)
                self.assertEqual(result, "continue")
                if with_view_turns:
                    view_key = view_script[idx % len(view_script)]
                    frontend_nd_input.route_nd_keydown(
                        view_key,
                        state,
                        view_key_handler=lambda raw_key: front4d_game.handle_view_key(
                            raw_key, view
                        ),
                    )
                    view.step_animation(120.0)
                state.step_gravity()
            return _state_signature_nd(state)

        self.assertEqual(
            run_once(with_view_turns=False), run_once(with_view_turns=True)
        )


if __name__ == "__main__":
    unittest.main()


