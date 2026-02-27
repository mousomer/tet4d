from __future__ import annotations

import unittest

try:
    import pygame
except (
    ModuleNotFoundError
):  # pragma: no cover - exercised in environments without pygame-ce
    pygame = None

if pygame is None:  # pragma: no cover - exercised in environments without pygame-ce
    raise unittest.SkipTest("pygame-ce is required for gameplay replay tests")

from cli import front2d
from tet4d.engine import frontend_nd
from tet4d.ui.pygame import front3d_game
from tet4d.ui.pygame import front4d_game
from tet4d.engine.gameplay.game2d import Action, GameConfig
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.ui.pygame.keybindings import (
    CAMERA_KEYS_3D,
    CAMERA_KEYS_4D,
    KEYS_2D,
    KEYS_3D,
    KEYS_4D,
    SYSTEM_KEYS,
)
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND


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

        move_up = self._key_for(KEYS_2D, "move_y_neg")
        self.assertEqual(
            front2d.handle_game_keydown(_keydown(move_up), state, cfg), "continue"
        )
        if state.current_piece is not None and y_before is not None:
            self.assertEqual(state.current_piece.pos[1], y_before - 1)

        move_down = self._key_for(KEYS_2D, "move_y_pos")
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

    def test_exploration_mode_disables_gravity_and_locking_nd(self) -> None:
        cfg = GameConfigND(
            dims=(8, 8, 8, 8), gravity_axis=1, speed_level=1, exploration_mode=True
        )
        state = frontend_nd.create_initial_state(cfg)
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

        move_up = self._key_for(KEYS_4D, "move_y_neg")
        self.assertEqual(
            frontend_nd.handle_game_keydown(_keydown(move_up), state), "continue"
        )
        if state.current_piece is not None and pos_before is not None:
            self.assertEqual(state.current_piece.pos[1], pos_before[1] - 1)

        move_down = self._key_for(KEYS_4D, "move_y_pos")
        self.assertEqual(
            frontend_nd.handle_game_keydown(_keydown(move_down), state), "continue"
        )
        if state.current_piece is not None and pos_before is not None:
            self.assertEqual(state.current_piece.pos[1], pos_before[1])

        hard_drop = self._key_for(KEYS_4D, "hard_drop")
        self.assertEqual(
            frontend_nd.handle_game_keydown(_keydown(hard_drop), state), "continue"
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
            state = frontend_nd.create_initial_state(cfg)
            for key in script:
                result = frontend_nd.handle_game_keydown(_keydown(key), state)
                self.assertEqual(result, "continue")
                state.step_gravity()
            return _state_signature_nd(state)

        self.assertEqual(run_once(), run_once())

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

        self.assertEqual(
            front2d.handle_game_keydown(
                _keydown(self._key_for(SYSTEM_KEYS, "quit")), state, cfg
            ),
            "quit",
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
        state = frontend_nd.create_initial_state(cfg)
        state.board.cells.clear()
        state.current_piece = ActivePieceND.from_shape(
            PieceShapeND(
                "tri4",
                ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)),
                color_id=8,
            ),
            pos=(3, 2, 3, 2),
        )

        move_z_neg = self._key_for(KEYS_4D, "move_z_neg")
        move_w_pos = self._key_for(KEYS_4D, "move_w_pos")
        rotate_xw = self._key_for(KEYS_4D, "rotate_xw_pos")
        hard_drop = self._key_for(KEYS_4D, "hard_drop")

        before_blocks = tuple(sorted(state.current_piece.rel_blocks))
        self.assertEqual(
            frontend_nd.handle_game_keydown(_keydown(move_z_neg), state), "continue"
        )
        self.assertEqual(state.current_piece.pos, (3, 2, 2, 2))
        self.assertEqual(tuple(sorted(state.current_piece.rel_blocks)), before_blocks)

        self.assertEqual(
            frontend_nd.handle_game_keydown(_keydown(move_w_pos), state), "continue"
        )
        self.assertEqual(state.current_piece.pos, (3, 2, 2, 3))

        self.assertEqual(
            frontend_nd.handle_game_keydown(_keydown(rotate_xw), state), "continue"
        )
        self.assertNotEqual(
            tuple(sorted(state.current_piece.rel_blocks)), before_blocks
        )

        self.assertEqual(
            frontend_nd.handle_game_keydown(_keydown(hard_drop), state), "continue"
        )
        self.assertGreater(len(state.board.cells), 0)

        self.assertEqual(
            frontend_nd.handle_game_keydown(
                _keydown(self._key_for(SYSTEM_KEYS, "toggle_grid")), state
            ),
            "toggle_grid",
        )
        self.assertEqual(
            frontend_nd.handle_game_keydown(
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
            state = frontend_nd.create_initial_state(cfg)
            view = front4d_game.LayerView3D()
            for idx, key in enumerate(game_script):
                result = frontend_nd.handle_game_keydown(_keydown(key), state)
                self.assertEqual(result, "continue")
                if with_view_turns:
                    view_key = view_script[idx % len(view_script)]
                    frontend_nd.route_nd_keydown(
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
