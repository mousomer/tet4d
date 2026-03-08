from __future__ import annotations

import unittest

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - exercised without pygame-ce
    pygame = None

if pygame is None:  # pragma: no cover - exercised without pygame-ce
    raise unittest.SkipTest("pygame-ce is required for ND routing tests")

from tet4d.ui.pygame import frontend_nd_input, frontend_nd_state
from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.topology_explorer.presets import axis_wrap_profile
from tet4d.ui.pygame.keybindings import CAMERA_KEYS_4D, EXPLORER_KEYS_3D, EXPLORER_KEYS_4D, KEYS_3D, KEYS_4D, SYSTEM_KEYS


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
        self.rotations: list[tuple[int, int, int]] = []

    def try_move_axis(self, axis: int, delta: int) -> None:
        self.moves.append((axis, delta))

    def try_rotate(self, axis_a: int, axis_b: int, direction: int) -> None:
        self.rotations.append((axis_a, axis_b, direction))

    def hard_drop(self) -> None:
        return None


class TestNdRouting(unittest.TestCase):
    def test_explorer_move_up_is_available_only_in_exploration_mode(self) -> None:
        explorer_cfg = GameConfigND(
            dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1, exploration_mode=True
        )
        explorer_state = _AxisCaptureState(explorer_cfg)
        result = frontend_nd_input.route_nd_keydown(
            _key_for(EXPLORER_KEYS_4D, "move_up"),
            explorer_state,
        )
        self.assertEqual(result, "continue")
        self.assertEqual(explorer_state.moves, [(1, -1)])

        normal_cfg = GameConfigND(
            dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1, exploration_mode=False
        )
        normal_state = _AxisCaptureState(normal_cfg)
        result_normal = frontend_nd_input.route_nd_keydown(
            _key_for(EXPLORER_KEYS_4D, "move_up"),
            normal_state,
        )
        self.assertEqual(result_normal, "continue")
        self.assertEqual(normal_state.moves, [])

    def test_explorer_move_down_is_available_in_3d_exploration_mode(self) -> None:
        cfg = GameConfigND(
            dims=(6, 10, 6), gravity_axis=1, speed_level=1, exploration_mode=True
        )
        state = _AxisCaptureState(cfg)
        result = frontend_nd_input.route_nd_keydown(
            _key_for(EXPLORER_KEYS_3D, "move_down"),
            state,
        )
        self.assertEqual(result, "continue")
        self.assertEqual(state.moves, [(1, 1)])

    def test_viewer_relative_routing_uses_yaw_for_3d(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6), gravity_axis=1, speed_level=1)
        state = _AxisCaptureState(cfg)

        result = frontend_nd_input.route_nd_keydown(
            _key_for(KEYS_3D, "move_x_pos"),
            state,
            yaw_deg_for_view_movement=90.0,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(state.moves, [(2, 1)])

        state.moves.clear()
        result_away = frontend_nd_input.route_nd_keydown(
            _key_for(KEYS_3D, "move_z_neg"),
            state,
            yaw_deg_for_view_movement=90.0,
        )
        self.assertEqual(result_away, "continue")
        self.assertEqual(state.moves, [(0, -1)])

    def test_viewer_relative_mapping_does_not_override_w_axis_actions(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = _AxisCaptureState(cfg)

        result = frontend_nd_input.route_nd_keydown(
            _key_for(KEYS_4D, "move_w_pos"),
            state,
            yaw_deg_for_view_movement=90.0,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(state.moves, [(3, 1)])

    def test_axis_override_precedence_over_viewer_relative_mapping(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = _AxisCaptureState(cfg)

        result = frontend_nd_input.route_nd_keydown(
            _key_for(KEYS_4D, "move_x_pos"),
            state,
            yaw_deg_for_view_movement=90.0,
            axis_overrides_by_action={"move_x_pos": (0, -1)},
        )

        self.assertEqual(result, "continue")
        self.assertEqual(state.moves, [(0, -1)])

    def test_viewer_axes_mapping_tracks_yaw_local_axis(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = _AxisCaptureState(cfg)

        result = frontend_nd_input.route_nd_keydown(
            _key_for(KEYS_4D, "move_x_pos"),
            state,
            yaw_deg_for_view_movement=90.0,
            viewer_axes_by_label={"x": (3, 1), "z": (0, -1), "w": (2, 1)},
        )

        self.assertEqual(result, "continue")
        self.assertEqual(state.moves, [(0, -1)])

    def test_rotation_with_w_axis_tracks_viewer_axes(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = _AxisCaptureState(cfg)

        result = frontend_nd_input.route_nd_keydown(
            _key_for(KEYS_4D, "rotate_xw_pos"),
            state,
            yaw_deg_for_view_movement=90.0,
            viewer_axes_by_label={"x": (3, 1), "z": (0, -1), "w": (2, 1)},
        )

        self.assertEqual(result, "continue")
        self.assertEqual(state.rotations, [(0, 2, -1)])

    def test_system_action_emits_sfx(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6), gravity_axis=1, speed_level=1)
        state = frontend_nd_state.create_initial_state(cfg)
        sfx: list[str] = []

        result = frontend_nd_input.route_nd_keydown(
            _key_for(SYSTEM_KEYS, "menu"),
            state,
            sfx_handler=sfx.append,
        )

        self.assertEqual(result, "menu")
        self.assertEqual(sfx, ["menu_confirm"])

        sfx.clear()
        result_help = frontend_nd_input.route_nd_keydown(
            _key_for(SYSTEM_KEYS, "help"),
            state,
            sfx_handler=sfx.append,
        )
        self.assertEqual(result_help, "help")
        self.assertEqual(sfx, ["menu_move"])

    def test_escape_quit_binding_routes_to_menu(self) -> None:
        quit_key = _key_for(SYSTEM_KEYS, "quit")
        if int(quit_key) != int(pygame.K_ESCAPE):
            self.skipTest("system quit key is not bound to escape in this profile")
        cfg = GameConfigND(dims=(6, 10, 6), gravity_axis=1, speed_level=1)
        state = frontend_nd_state.create_initial_state(cfg)
        sfx: list[str] = []

        result = frontend_nd_input.route_nd_keydown(
            quit_key,
            state,
            sfx_handler=sfx.append,
        )

        self.assertEqual(result, "menu")
        self.assertEqual(sfx, ["menu_confirm"])

    def test_bound_gameplay_key_takes_priority_over_view(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd_state.create_initial_state(cfg)
        sfx: list[str] = []
        view_calls: list[int] = []

        result = frontend_nd_input.route_nd_keydown(
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
        state = frontend_nd_state.create_initial_state(cfg)
        state.game_over = True
        view_calls: list[int] = []

        result = frontend_nd_input.route_nd_keydown(
            _key_for(KEYS_4D, "move_x_neg"),
            state,
            view_key_handler=lambda key: view_calls.append(key) or True,
        )

        self.assertEqual(result, "continue")
        self.assertEqual(view_calls, [])

    def test_unbound_key_can_drive_view_handler(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd_state.create_initial_state(cfg)
        sfx: list[str] = []
        view_calls: list[int] = []
        unbound_key = _find_unbound_4d_key()

        result = frontend_nd_input.route_nd_keydown(
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
        state = frontend_nd_state.create_initial_state(cfg)
        view_calls: list[int] = []
        sfx: list[str] = []
        camera_key = _key_for(CAMERA_KEYS_4D, "view_xw_pos")
        pos_before = (
            state.current_piece.pos if state.current_piece is not None else None
        )

        result = frontend_nd_input.route_nd_keydown(
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
        state = frontend_nd_state.create_initial_state(cfg)
        piece = state.current_piece
        if piece is None:
            self.fail("expected active piece")
        start_pos = tuple(piece.pos)
        key = _key_for(KEYS_4D, "move_w_pos")

        result = frontend_nd_input.route_nd_keydown(
            key,
            state,
            axis_overrides_by_action={"move_w_pos": (0, 1), "move_w_neg": (0, -1)},
        )

        self.assertEqual(result, "continue")
        self.assertEqual(state.current_piece.pos[0], start_pos[0] + 1)
        self.assertEqual(state.current_piece.pos[3], start_pos[3])

    def test_action_filter_blocks_bound_gameplay_action(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6), gravity_axis=1, speed_level=1)
        state = _AxisCaptureState(cfg)
        blocked = frontend_nd_input.route_nd_keydown(
            _key_for(KEYS_3D, "move_x_neg"),
            state,
            action_filter=lambda action: action != "move_x_neg",
        )
        self.assertEqual(blocked, "continue")
        self.assertEqual(state.moves, [])

    def test_action_observer_receives_view_action_lookup(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd_state.create_initial_state(cfg)
        seen: list[str] = []
        camera_key = _key_for(CAMERA_KEYS_4D, "view_xw_pos")
        result = frontend_nd_input.route_nd_keydown(
            camera_key,
            state,
            view_key_handler=lambda _key: True,
            view_action_lookup=lambda key: (
                "view_xw_pos" if key == camera_key else None
            ),
            action_observer=seen.append,
        )
        self.assertEqual(result, "continue")
        self.assertEqual(seen, ["view_xw_pos"])

    def test_can_apply_nd_action_matches_viewer_relative_move_constraints(self) -> None:
        cfg = GameConfigND(
            dims=(6, 10, 6),
            gravity_axis=1,
            speed_level=1,
            exploration_mode=True,
            rng_seed=1234,
        )
        state = frontend_nd_state.create_initial_state(cfg)
        while state.try_move_axis(0, -1):
            pass
        self.assertFalse(
            frontend_nd_input.can_apply_nd_gameplay_action_with_view(
                state,
                "move_z_neg",
                yaw_deg_for_view_movement=90.0,
            )
        )
        self.assertTrue(
            frontend_nd_input.can_apply_nd_gameplay_action_with_view(
                state,
                "move_z_pos",
                yaw_deg_for_view_movement=90.0,
            )
        )

    def test_can_apply_nd_action_respects_axis_overrides(self) -> None:
        cfg = GameConfigND(
            dims=(6, 10, 6, 4),
            gravity_axis=1,
            speed_level=1,
            exploration_mode=True,
            rng_seed=1234,
        )
        state = frontend_nd_state.create_initial_state(cfg)
        while state.try_move_axis(0, 1):
            pass
        self.assertFalse(
            frontend_nd_input.can_apply_nd_gameplay_action_with_view(
                state,
                "move_w_pos",
                axis_overrides_by_action={"move_w_pos": (0, 1)},
            )
        )
        self.assertTrue(
            frontend_nd_input.can_apply_nd_gameplay_action_with_view(
                state,
                "move_w_neg",
                axis_overrides_by_action={"move_w_neg": (0, -1)},
            )
        )

    def test_can_apply_nd_action_respects_explorer_glue_wraps(self) -> None:
        cfg = GameConfigND(
            dims=(4, 8, 4),
            gravity_axis=1,
            speed_level=1,
            exploration_mode=True,
            explorer_topology_profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
            rng_seed=1234,
        )
        state = frontend_nd_state.create_initial_state(cfg)
        state.board = BoardND(cfg.dims)
        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=9)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(3, 3, 2))

        self.assertTrue(
            frontend_nd_input.can_apply_nd_gameplay_action_with_view(
                state,
                "move_x_pos",
            )
        )


if __name__ == "__main__":
    unittest.main()


