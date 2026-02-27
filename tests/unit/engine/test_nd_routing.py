from __future__ import annotations

import unittest

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - exercised without pygame-ce
    pygame = None

if pygame is None:  # pragma: no cover - exercised without pygame-ce
    raise unittest.SkipTest("pygame-ce is required for ND routing tests")

from tet4d.engine import frontend_nd
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.ui.pygame.keybindings import CAMERA_KEYS_4D, KEYS_3D, KEYS_4D, SYSTEM_KEYS


def _key_for(bindings: dict[str, tuple[int, ...]], action: str) -> int:
    keys = bindings.get(action, ())
    if not keys:
        raise AssertionError(f"missing key binding for action: {action}")
    return keys[0]


def _find_unbound_4d_key() -> int:
    reserved = set()
    for keyset in (*KEYS_4D.values(), *SYSTEM_KEYS.values()):
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


class _AxisCaptureState:
    def __init__(self, cfg: GameConfigND) -> None:
        self.config = cfg
        self.game_over = False
        self.moves: list[tuple[int, int]] = []

    def try_move_axis(self, axis: int, delta: int) -> None:
        self.moves.append((axis, delta))

    def try_rotate(self, _axis_a: int, _axis_b: int, _direction: int) -> None:
        return None

    def hard_drop(self) -> None:
        return None


class TestNdRouting(unittest.TestCase):
    def test_viewer_relative_routing_uses_yaw_for_3d(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6), gravity_axis=1, speed_level=1)
        state = _AxisCaptureState(cfg)

        result = frontend_nd.route_nd_keydown(
            _key_for(KEYS_3D, "move_x_pos"),
            state,
            yaw_deg_for_view_movement=90.0,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(state.moves, [(2, 1)])

        state.moves.clear()
        result_away = frontend_nd.route_nd_keydown(
            _key_for(KEYS_3D, "move_z_neg"),
            state,
            yaw_deg_for_view_movement=90.0,
        )
        self.assertEqual(result_away, "continue")
        self.assertEqual(state.moves, [(0, -1)])

    def test_viewer_relative_mapping_does_not_override_w_axis_actions(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = _AxisCaptureState(cfg)

        result = frontend_nd.route_nd_keydown(
            _key_for(KEYS_4D, "move_w_pos"),
            state,
            yaw_deg_for_view_movement=90.0,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(state.moves, [(3, 1)])

    def test_axis_override_precedence_over_viewer_relative_mapping(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = _AxisCaptureState(cfg)

        result = frontend_nd.route_nd_keydown(
            _key_for(KEYS_4D, "move_x_pos"),
            state,
            yaw_deg_for_view_movement=90.0,
            axis_overrides_by_action={"move_x_pos": (0, -1)},
        )

        self.assertEqual(result, "continue")
        self.assertEqual(state.moves, [(0, -1)])

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

    def test_bound_gameplay_key_takes_priority_over_view(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        sfx: list[str] = []
        view_calls: list[int] = []

        result = frontend_nd.route_nd_keydown(
            _key_for(KEYS_4D, "move_x_neg"),
            state,
            view_key_handler=lambda key: view_calls.append(key) or True,
            sfx_handler=sfx.append,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(view_calls, [])
        self.assertEqual(sfx, ["move"])

    def test_reserved_key_does_not_reach_view_when_game_over(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        state.game_over = True
        view_calls: list[int] = []

        result = frontend_nd.route_nd_keydown(
            _key_for(KEYS_4D, "move_x_neg"),
            state,
            view_key_handler=lambda key: view_calls.append(key) or True,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(view_calls, [])

    def test_unbound_key_can_drive_view_handler(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        sfx: list[str] = []
        view_calls: list[int] = []
        unbound_key = _find_unbound_4d_key()

        result = frontend_nd.route_nd_keydown(
            unbound_key,
            state,
            view_key_handler=lambda key: view_calls.append(key) or True,
            sfx_handler=sfx.append,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(view_calls, [unbound_key])
        self.assertEqual(sfx, ["menu_move"])

    def test_bound_camera_key_routes_to_view_handler(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        view_calls: list[int] = []
        sfx: list[str] = []
        camera_key = _key_for(CAMERA_KEYS_4D, "view_xw_pos")
        pos_before = (
            state.current_piece.pos if state.current_piece is not None else None
        )

        result = frontend_nd.route_nd_keydown(
            camera_key,
            state,
            view_key_handler=lambda key: view_calls.append(key) or True,
            sfx_handler=sfx.append,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(view_calls, [camera_key])
        self.assertEqual(sfx, ["menu_move"])
        if state.current_piece is not None and pos_before is not None:
            self.assertEqual(state.current_piece.pos, pos_before)

    def test_axis_override_routes_w_move_to_target_axis(self) -> None:
        cfg = GameConfigND(
            dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1, exploration_mode=True
        )
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
