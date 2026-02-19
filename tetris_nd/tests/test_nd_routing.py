from __future__ import annotations

import unittest

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - exercised without pygame-ce
    pygame = None

if pygame is None:  # pragma: no cover - exercised without pygame-ce
    raise unittest.SkipTest("pygame-ce is required for ND routing tests")

from tetris_nd import frontend_nd
from tetris_nd.game_nd import GameConfigND
from tetris_nd.keybindings import CAMERA_KEYS_4D, KEYS_4D, SLICE_KEYS_4D, SYSTEM_KEYS


def _key_for(bindings: dict[str, tuple[int, ...]], action: str) -> int:
    keys = bindings.get(action, ())
    if not keys:
        raise AssertionError(f"missing key binding for action: {action}")
    return keys[0]


def _find_unbound_4d_key() -> int:
    reserved = set()
    for keyset in (*KEYS_4D.values(), *SLICE_KEYS_4D.values(), *SYSTEM_KEYS.values()):
        reserved.update(keyset)
    for candidate in (
        pygame.K_F1,
        pygame.K_F2,
        pygame.K_F3,
        pygame.K_HOME,
        pygame.K_END,
        pygame.K_PAGEUP,
        pygame.K_PAGEDOWN,
    ):
        if candidate not in reserved:
            return candidate
    raise AssertionError("could not find an unbound 4D key candidate")


class TestNdRouting(unittest.TestCase):
    def test_system_action_emits_sfx(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        sfx: list[str] = []

        result = frontend_nd.route_nd_keydown(
            _key_for(SYSTEM_KEYS, "menu"),
            state,
            sfx_handler=sfx.append,
        )

        self.assertEqual(result, "menu")
        self.assertEqual(sfx, ["menu_confirm"])

        sfx.clear()
        result_help = frontend_nd.route_nd_keydown(
            _key_for(SYSTEM_KEYS, "help"),
            state,
            sfx_handler=sfx.append,
        )
        self.assertEqual(result_help, "help")
        self.assertEqual(sfx, ["menu_move"])

    def test_slice_action_takes_priority_over_view(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        slice_state = frontend_nd.create_initial_slice_state(cfg)
        sfx: list[str] = []
        view_calls: list[int] = []
        start_z = slice_state.axis_values[2]

        result = frontend_nd.route_nd_keydown(
            _key_for(SLICE_KEYS_4D, "slice_z_neg"),
            state,
            slice_state=slice_state,
            view_key_handler=lambda key: view_calls.append(key) or True,
            sfx_handler=sfx.append,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(slice_state.axis_values[2], max(0, start_z - 1))
        self.assertEqual(view_calls, [])
        self.assertEqual(sfx, ["menu_move"])

    def test_reserved_key_does_not_reach_view_when_game_over(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        state.game_over = True
        slice_state = frontend_nd.create_initial_slice_state(cfg)
        view_calls: list[int] = []

        result = frontend_nd.route_nd_keydown(
            _key_for(KEYS_4D, "move_x_neg"),
            state,
            slice_state=slice_state,
            view_key_handler=lambda key: view_calls.append(key) or True,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(view_calls, [])

    def test_unbound_key_can_drive_view_handler(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        slice_state = frontend_nd.create_initial_slice_state(cfg)
        sfx: list[str] = []
        view_calls: list[int] = []
        unbound_key = _find_unbound_4d_key()

        result = frontend_nd.route_nd_keydown(
            unbound_key,
            state,
            slice_state=slice_state,
            view_key_handler=lambda key: view_calls.append(key) or True,
            sfx_handler=sfx.append,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(view_calls, [unbound_key])
        self.assertEqual(sfx, ["menu_move"])

    def test_bound_camera_key_routes_to_view_handler(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        slice_state = frontend_nd.create_initial_slice_state(cfg)
        view_calls: list[int] = []
        sfx: list[str] = []
        camera_key = _key_for(CAMERA_KEYS_4D, "view_xw_pos")
        pos_before = state.current_piece.pos if state.current_piece is not None else None

        result = frontend_nd.route_nd_keydown(
            camera_key,
            state,
            slice_state=slice_state,
            view_key_handler=lambda key: view_calls.append(key) or True,
            sfx_handler=sfx.append,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(view_calls, [camera_key])
        self.assertEqual(sfx, ["menu_move"])
        if state.current_piece is not None and pos_before is not None:
            self.assertEqual(state.current_piece.pos, pos_before)

    def test_axis_override_routes_w_move_to_target_axis(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1, exploration_mode=True)
        state = frontend_nd.create_initial_state(cfg)
        piece = state.current_piece
        if piece is None:
            self.fail("expected active piece")
        start_pos = tuple(piece.pos)
        key = _key_for(KEYS_4D, "move_w_pos")

        result = frontend_nd.route_nd_keydown(
            key,
            state,
            axis_overrides_by_action={"move_w_pos": (0, 1), "move_w_neg": (0, -1)},
        )

        self.assertEqual(result, "continue")
        self.assertEqual(state.current_piece.pos[0], start_pos[0] + 1)
        self.assertEqual(state.current_piece.pos[3], start_pos[3])


if __name__ == "__main__":
    unittest.main()
