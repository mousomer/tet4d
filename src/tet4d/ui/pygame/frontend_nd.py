from __future__ import annotations

import random
from collections.abc import Callable, Mapping

import pygame

from tet4d.engine.core.model import BoardND
from tet4d.engine.core.rng import RNG_MODE_TRUE_RANDOM
from tet4d.engine.gameplay.challenge_mode import apply_challenge_prefill_nd
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.ui.pygame.input.key_dispatch import match_bound_action
from tet4d.ui.pygame.input.view_controls import viewer_relative_move_axis_delta
from tet4d.ui.pygame.keybindings import KEYS_3D, KEYS_4D, SYSTEM_KEYS

from . import frontend_nd_setup as _setup

GfxFonts = _setup.GfxFonts
GameSettingsND = _setup.GameSettingsND
MenuState = _setup.MenuState
build_config = _setup.build_config
draw_gradient_background = _setup.draw_gradient_background
draw_menu = _setup.draw_menu
gravity_interval_ms_from_config = _setup.gravity_interval_ms_from_config
init_fonts = _setup.init_fonts
menu_fields_for_settings = _setup.menu_fields_for_settings
piece_set_4d_label = _setup.piece_set_4d_label
run_menu = _setup.run_menu


def create_initial_state(cfg: GameConfigND) -> GameStateND:
    board = BoardND(cfg.dims)
    if cfg.rng_mode == RNG_MODE_TRUE_RANDOM:
        rng = random.Random()
    else:
        rng = random.Random(cfg.rng_seed)
    state = GameStateND(config=cfg, board=board, rng=rng)
    if not cfg.exploration_mode:
        apply_challenge_prefill_nd(state, layers=cfg.challenge_layers)
    return state


_SYSTEM_ACTIONS = ("quit", "menu", "restart", "toggle_grid", "help")
_GAMEPLAY_ACTIONS_3D = (
    "move_x_neg",
    "move_x_pos",
    "move_y_neg",
    "move_y_pos",
    "soft_drop",
    "hard_drop",
    "rotate_xy_pos",
    "rotate_xy_neg",
    "move_z_neg",
    "move_z_pos",
    "rotate_xz_pos",
    "rotate_xz_neg",
    "rotate_yz_pos",
    "rotate_yz_neg",
)
_GAMEPLAY_ACTIONS_4D = (
    *_GAMEPLAY_ACTIONS_3D,
    "move_w_neg",
    "move_w_pos",
    "rotate_xw_pos",
    "rotate_xw_neg",
    "rotate_yw_pos",
    "rotate_yw_neg",
    "rotate_zw_pos",
    "rotate_zw_neg",
)
_SYSTEM_SFX = {
    "menu": "menu_confirm",
    "restart": "menu_confirm",
    "toggle_grid": "menu_move",
    "help": "menu_move",
}
_VIEWER_RELATIVE_INTENT_BY_ACTION = {
    "move_x_neg": "left",
    "move_x_pos": "right",
    "move_z_neg": "away",
    "move_z_pos": "closer",
}
_ROTATION_ACTION_TO_LOCAL_AXES = {
    "rotate_xy_pos": ("x", "y", 1),
    "rotate_xy_neg": ("x", "y", -1),
    "rotate_xz_pos": ("x", "z", 1),
    "rotate_xz_neg": ("x", "z", -1),
    "rotate_yz_pos": ("y", "z", 1),
    "rotate_yz_neg": ("y", "z", -1),
    "rotate_xw_pos": ("x", "w", 1),
    "rotate_xw_neg": ("x", "w", -1),
    "rotate_yw_pos": ("y", "w", 1),
    "rotate_yw_neg": ("y", "w", -1),
    "rotate_zw_pos": ("z", "w", 1),
    "rotate_zw_neg": ("z", "w", -1),
}
AxisOverride = tuple[int, int] | tuple[int, int, int]


def system_key_action(key: int) -> str | None:
    return match_bound_action(key, SYSTEM_KEYS, _SYSTEM_ACTIONS)


def gameplay_action_for_key(key: int, cfg: GameConfigND) -> str | None:
    gameplay_keys = KEYS_4D if cfg.ndim >= 4 else KEYS_3D
    action_order = _GAMEPLAY_ACTIONS_4D if cfg.ndim >= 4 else _GAMEPLAY_ACTIONS_3D
    if not cfg.exploration_mode:
        action_order = tuple(
            action
            for action in action_order
            if action not in {"move_y_neg", "move_y_pos"}
        )
    return match_bound_action(key, gameplay_keys, action_order)


def apply_nd_gameplay_action(state: GameStateND, action: str) -> bool:
    cfg = state.config
    ndim = cfg.ndim
    gameplay_handlers = {
        "move_x_neg": lambda: state.try_move_axis(0, -1),
        "move_x_pos": lambda: state.try_move_axis(0, 1),
        "move_y_neg": lambda: state.try_move_axis(cfg.gravity_axis, -1),
        "move_y_pos": lambda: state.try_move_axis(cfg.gravity_axis, 1),
        "soft_drop": lambda: state.try_move_axis(cfg.gravity_axis, 1),
        "hard_drop": state.hard_drop,
        "rotate_xy_pos": lambda: state.try_rotate(0, cfg.gravity_axis, 1),
        "rotate_xy_neg": lambda: state.try_rotate(0, cfg.gravity_axis, -1),
        "move_z_neg": lambda: state.try_move_axis(2, -1),
        "move_z_pos": lambda: state.try_move_axis(2, 1),
        "rotate_xz_pos": lambda: state.try_rotate(0, 2, 1),
        "rotate_xz_neg": lambda: state.try_rotate(0, 2, -1),
        "rotate_yz_pos": lambda: state.try_rotate(cfg.gravity_axis, 2, 1),
        "rotate_yz_neg": lambda: state.try_rotate(cfg.gravity_axis, 2, -1),
    }
    if ndim >= 4:
        gameplay_handlers.update(
            {
                "move_w_neg": lambda: state.try_move_axis(3, -1),
                "move_w_pos": lambda: state.try_move_axis(3, 1),
                "rotate_xw_pos": lambda: state.try_rotate(0, 3, 1),
                "rotate_xw_neg": lambda: state.try_rotate(0, 3, -1),
                "rotate_yw_pos": lambda: state.try_rotate(cfg.gravity_axis, 3, 1),
                "rotate_yw_neg": lambda: state.try_rotate(cfg.gravity_axis, 3, -1),
                "rotate_zw_pos": lambda: state.try_rotate(2, 3, 1),
                "rotate_zw_neg": lambda: state.try_rotate(2, 3, -1),
            }
        )
    handler = gameplay_handlers.get(action)
    if handler is None:
        return False
    if action in {"move_y_neg", "move_y_pos"} and not cfg.exploration_mode:
        return False
    handler()
    return True


def _playback_sfx_for_gameplay_action(action: str) -> str:
    if action.startswith("rotate_"):
        return "rotate"
    if action == "hard_drop":
        return "drop"
    return "move"


def _binding_contains_key(bindings: Mapping[str, tuple[int, ...]], key: int) -> bool:
    return any(key in keys for keys in bindings.values())


def _is_reserved_nd_key(key: int, cfg: GameConfigND) -> bool:
    gameplay_keys = KEYS_4D if cfg.ndim >= 4 else KEYS_3D
    if _binding_contains_key(gameplay_keys, key):
        return True
    return _binding_contains_key(SYSTEM_KEYS, key)


def _emit_sfx(sfx_handler: Callable[[str], None] | None, cue: str | None) -> None:
    if cue is None or sfx_handler is None:
        return
    sfx_handler(cue)


def _viewer_axis_map_for_yaw(
    yaw_deg: float,
    *,
    cfg: GameConfigND,
    viewer_axes_by_label: Mapping[str, tuple[int, int]] | None = None,
) -> dict[str, tuple[int, int]]:
    quarter_turn = int(round(float(yaw_deg) / 90.0)) % 4
    if quarter_turn == 0:
        local_map = {"x": (0, 1), "z": (2, 1)}
    elif quarter_turn == 1:
        local_map = {"x": (2, 1), "z": (0, -1)}
    elif quarter_turn == 2:
        local_map = {"x": (0, -1), "z": (2, -1)}
    else:
        local_map = {"x": (2, -1), "z": (0, 1)}
    resolved: dict[str, tuple[int, int]] = {}
    for label in ("x", "z"):
        local_axis, local_sign = local_map[label]
        if viewer_axes_by_label is None:
            resolved[label] = (local_axis, local_sign)
            continue
        source_label = "x" if int(local_axis) == 0 else "z"
        target = viewer_axes_by_label.get(source_label)
        if target is None:
            resolved[label] = (local_axis, local_sign)
            continue
        world_axis, world_sign = target
        if not (0 <= int(world_axis) < cfg.ndim):
            continue
        resolved[label] = (int(world_axis), int(local_sign) * int(world_sign))
    return resolved


def _rotation_override_from_view(
    *,
    action: str,
    cfg: GameConfigND,
    yaw_deg_for_view_movement: float | None,
    viewer_axes_by_label: Mapping[str, tuple[int, int]] | None,
) -> tuple[int, int, int] | None:
    rotation_spec = _ROTATION_ACTION_TO_LOCAL_AXES.get(action)
    if rotation_spec is None or yaw_deg_for_view_movement is None:
        return None
    axis_a_label, axis_b_label, local_direction = rotation_spec
    view_axis_map = _viewer_axis_map_for_yaw(
        yaw_deg_for_view_movement,
        cfg=cfg,
        viewer_axes_by_label=viewer_axes_by_label,
    )
    w_axis = (
        viewer_axes_by_label.get("w")
        if viewer_axes_by_label is not None
        else None
    )
    if w_axis is None:
        w_axis = (3, 1)
    w_world_axis, w_world_sign = int(w_axis[0]), int(w_axis[1])
    if not (0 <= w_world_axis < cfg.ndim):
        w_world_axis, w_world_sign = 3, 1
    axis_options = {
        "x": view_axis_map.get("x"),
        "y": (cfg.gravity_axis, 1),
        "z": view_axis_map.get("z"),
        "w": (w_world_axis, w_world_sign),
    }
    a = axis_options.get(axis_a_label)
    b = axis_options.get(axis_b_label)
    if a is None or b is None:
        return None
    axis_a, sign_a = a
    axis_b, sign_b = b
    if axis_a == axis_b:
        return None
    direction = int(local_direction) * int(sign_a) * int(sign_b)
    return int(axis_a), int(axis_b), int(direction)


def _apply_action_override(
    state: GameStateND,
    *,
    override: AxisOverride,
) -> bool:
    if len(override) == 2:
        axis, delta = override
        state.try_move_axis(int(axis), int(delta))
        return True
    axis_a, axis_b, delta = override
    state.try_rotate(int(axis_a), int(axis_b), int(delta))
    return True


def _candidate_from_axis_override(
    piece: object,
    *,
    override: AxisOverride,
    ndim: int,
) -> object:
    if len(override) == 2:
        axis, delta = int(override[0]), int(override[1])
        vector = [0] * int(ndim)
        vector[axis] = delta
        return piece.moved(tuple(vector))
    axis_a, axis_b, direction = (
        int(override[0]),
        int(override[1]),
        int(override[2]),
    )
    return piece.rotated(axis_a, axis_b, direction)


def _candidate_for_base_nd_action(
    state: GameStateND,
    action: str,
) -> object | None:
    piece = state.current_piece
    if piece is None:
        return None
    gravity_axis = int(state.config.gravity_axis)
    if action == "soft_drop":
        vector = [0] * int(state.config.ndim)
        vector[gravity_axis] = 1
        return piece.moved(tuple(vector))
    move_vectors = {
        "move_x_neg": (0, -1),
        "move_x_pos": (0, 1),
        "move_y_neg": (gravity_axis, -1),
        "move_y_pos": (gravity_axis, 1),
        "move_z_neg": (2, -1),
        "move_z_pos": (2, 1),
        "move_w_neg": (3, -1),
        "move_w_pos": (3, 1),
    }
    move_spec = move_vectors.get(action)
    if move_spec is not None:
        axis, delta = move_spec
        if not (0 <= int(axis) < int(state.config.ndim)):
            return None
        vector = [0] * int(state.config.ndim)
        vector[int(axis)] = int(delta)
        return piece.moved(tuple(vector))
    rotation_specs = {
        "rotate_xy_pos": (0, gravity_axis, 1),
        "rotate_xy_neg": (0, gravity_axis, -1),
        "rotate_xz_pos": (0, 2, 1),
        "rotate_xz_neg": (0, 2, -1),
        "rotate_yz_pos": (gravity_axis, 2, 1),
        "rotate_yz_neg": (gravity_axis, 2, -1),
        "rotate_xw_pos": (0, 3, 1),
        "rotate_xw_neg": (0, 3, -1),
        "rotate_yw_pos": (gravity_axis, 3, 1),
        "rotate_yw_neg": (gravity_axis, 3, -1),
        "rotate_zw_pos": (2, 3, 1),
        "rotate_zw_neg": (2, 3, -1),
    }
    rotation_spec = rotation_specs.get(action)
    if rotation_spec is None:
        return None
    axis_a, axis_b, direction = rotation_spec
    if not (
        0 <= int(axis_a) < int(state.config.ndim)
        and 0 <= int(axis_b) < int(state.config.ndim)
    ):
        return None
    return piece.rotated(int(axis_a), int(axis_b), int(direction))


def _candidate_from_action_override(
    *,
    piece: object,
    action: str,
    ndim: int,
    axis_overrides_by_action: Mapping[str, AxisOverride] | None,
) -> object | None:
    if axis_overrides_by_action is None:
        return None
    override = axis_overrides_by_action.get(action)
    if override is None:
        return None
    return _candidate_from_axis_override(piece, override=override, ndim=ndim)


def _candidate_from_rotation_override(
    *,
    piece: object,
    action: str,
    cfg: GameConfigND,
    ndim: int,
    yaw_deg_for_view_movement: float | None,
    viewer_axes_by_label: Mapping[str, tuple[int, int]] | None,
) -> object | None:
    override = _rotation_override_from_view(
        action=action,
        cfg=cfg,
        yaw_deg_for_view_movement=yaw_deg_for_view_movement,
        viewer_axes_by_label=viewer_axes_by_label,
    )
    if override is None:
        return None
    return _candidate_from_axis_override(piece, override=override, ndim=ndim)


def _viewer_relative_move_candidate(
    *,
    piece: object,
    action: str,
    ndim: int,
    yaw_deg_for_view_movement: float | None,
    viewer_axes_by_label: Mapping[str, tuple[int, int]] | None,
) -> tuple[object | None, bool]:
    if yaw_deg_for_view_movement is None:
        return None, False
    intent = _VIEWER_RELATIVE_INTENT_BY_ACTION.get(action)
    if intent is None:
        return None, False
    local_axis, local_delta = viewer_relative_move_axis_delta(
        yaw_deg_for_view_movement,
        intent,
    )
    mapped_axis = int(local_axis)
    mapped_delta = int(local_delta)
    if viewer_axes_by_label is not None:
        key = "x" if int(local_axis) == 0 else "z"
        target_axis = viewer_axes_by_label.get(key)
        if target_axis is not None:
            mapped_axis = int(target_axis[0])
            mapped_delta = int(local_delta) * int(target_axis[1])
    if not (0 <= mapped_axis < int(ndim)):
        return None, True
    vector = [0] * int(ndim)
    vector[mapped_axis] = mapped_delta
    return piece.moved(tuple(vector)), True


def can_apply_nd_gameplay_action_with_view(
    state: GameStateND,
    action: str,
    *,
    yaw_deg_for_view_movement: float | None = None,
    axis_overrides_by_action: Mapping[str, AxisOverride] | None = None,
    viewer_axes_by_label: Mapping[str, tuple[int, int]] | None = None,
) -> bool:
    piece = state.current_piece
    if piece is None or state.game_over:
        return False
    if action == "hard_drop":
        return True
    ndim = int(state.config.ndim)
    candidate = _candidate_from_action_override(
        piece=piece,
        action=action,
        ndim=ndim,
        axis_overrides_by_action=axis_overrides_by_action,
    )
    if candidate is not None:
        return bool(state._can_exist(candidate))
    candidate = _candidate_from_rotation_override(
        piece=piece,
        action=action,
        cfg=state.config,
        ndim=ndim,
        yaw_deg_for_view_movement=yaw_deg_for_view_movement,
        viewer_axes_by_label=viewer_axes_by_label,
    )
    if candidate is not None:
        return bool(state._can_exist(candidate))
    candidate, is_view_relative = _viewer_relative_move_candidate(
        piece=piece,
        action=action,
        ndim=ndim,
        yaw_deg_for_view_movement=yaw_deg_for_view_movement,
        viewer_axes_by_label=viewer_axes_by_label,
    )
    if is_view_relative:
        return bool(candidate is not None and state._can_exist(candidate))
    candidate = _candidate_for_base_nd_action(state, action)
    if candidate is None:
        return True
    return bool(state._can_exist(candidate))


def apply_nd_gameplay_action_with_view(
    state: GameStateND,
    action: str,
    *,
    yaw_deg_for_view_movement: float | None = None,
    axis_overrides_by_action: Mapping[str, AxisOverride] | None = None,
    viewer_axes_by_label: Mapping[str, tuple[int, int]] | None = None,
) -> bool:
    if axis_overrides_by_action is not None:
        override = axis_overrides_by_action.get(action)
        if override is not None:
            return _apply_action_override(state, override=override)
    rotation_override = _rotation_override_from_view(
        action=action,
        cfg=state.config,
        yaw_deg_for_view_movement=yaw_deg_for_view_movement,
        viewer_axes_by_label=viewer_axes_by_label,
    )
    if rotation_override is not None:
        return _apply_action_override(state, override=rotation_override)
    if yaw_deg_for_view_movement is not None:
        intent = _VIEWER_RELATIVE_INTENT_BY_ACTION.get(action)
        if intent is not None:
            local_axis, local_delta = viewer_relative_move_axis_delta(
                yaw_deg_for_view_movement,
                intent,
            )
            if viewer_axes_by_label is not None:
                key = "x" if int(local_axis) == 0 else "z"
                target_axis = viewer_axes_by_label.get(key)
                if target_axis is not None:
                    mapped_axis, mapped_sign = target_axis
                    state.try_move_axis(
                        int(mapped_axis),
                        int(local_delta) * int(mapped_sign),
                    )
                    return True
            state.try_move_axis(int(local_axis), int(local_delta))
            return True
    return apply_nd_gameplay_action(state, action)


def dispatch_nd_gameplay_key(
    key: int,
    state: GameStateND,
    *,
    yaw_deg_for_view_movement: float | None = None,
    axis_overrides_by_action: Mapping[str, AxisOverride] | None = None,
    viewer_axes_by_label: Mapping[str, tuple[int, int]] | None = None,
) -> str | None:
    action = gameplay_action_for_key(key, state.config)
    if action is None:
        return None
    apply_nd_gameplay_action_with_view(
        state,
        action,
        yaw_deg_for_view_movement=yaw_deg_for_view_movement,
        axis_overrides_by_action=axis_overrides_by_action,
        viewer_axes_by_label=viewer_axes_by_label,
    )
    return action


def route_nd_keydown(
    key: int,
    state: GameStateND,
    *,
    yaw_deg_for_view_movement: float | None = None,
    axis_overrides_by_action: Mapping[str, AxisOverride] | None = None,
    viewer_axes_by_label: Mapping[str, tuple[int, int]] | None = None,
    view_key_handler: Callable[[int], bool] | None = None,
    view_action_lookup: Callable[[int], str | None] | None = None,
    sfx_handler: Callable[[str], None] | None = None,
    allow_gameplay: bool = True,
    action_filter: Callable[[str], bool] | None = None,
    action_observer: Callable[[str], None] | None = None,
) -> str:
    system_result = _route_nd_system_action(
        key,
        sfx_handler=sfx_handler,
        action_filter=action_filter,
        action_observer=action_observer,
    )
    if system_result is not None:
        return system_result

    if allow_gameplay and not state.game_over:
        if _route_nd_gameplay_action(
            key,
            state,
            yaw_deg_for_view_movement=yaw_deg_for_view_movement,
            axis_overrides_by_action=axis_overrides_by_action,
            viewer_axes_by_label=viewer_axes_by_label,
            sfx_handler=sfx_handler,
            action_filter=action_filter,
            action_observer=action_observer,
        ):
            return "continue"

    _route_nd_view_action(
        key,
        state=state,
        view_key_handler=view_key_handler,
        view_action_lookup=view_action_lookup,
        sfx_handler=sfx_handler,
        action_filter=action_filter,
        action_observer=action_observer,
    )
    return "continue"


def _route_nd_system_action(
    key: int,
    *,
    sfx_handler: Callable[[str], None] | None,
    action_filter: Callable[[str], bool] | None,
    action_observer: Callable[[str], None] | None,
) -> str | None:
    system_action = system_key_action(key)
    if system_action is None:
        return None
    resolved_action = (
        "menu"
        if system_action == "quit" and int(key) == int(pygame.K_ESCAPE)
        else system_action
    )
    if action_filter is not None and not action_filter(resolved_action):
        return "continue"
    _emit_sfx(sfx_handler, _SYSTEM_SFX.get(resolved_action))
    if action_observer is not None:
        action_observer(resolved_action)
    return resolved_action


def _route_nd_gameplay_action(
    key: int,
    state: GameStateND,
    *,
    yaw_deg_for_view_movement: float | None,
    axis_overrides_by_action: Mapping[str, AxisOverride] | None,
    viewer_axes_by_label: Mapping[str, tuple[int, int]] | None,
    sfx_handler: Callable[[str], None] | None,
    action_filter: Callable[[str], bool] | None,
    action_observer: Callable[[str], None] | None,
) -> bool:
    gameplay_action = gameplay_action_for_key(key, state.config)
    if gameplay_action is None:
        return False
    if action_filter is not None and not action_filter(gameplay_action):
        return True
    apply_nd_gameplay_action_with_view(
        state,
        gameplay_action,
        yaw_deg_for_view_movement=yaw_deg_for_view_movement,
        axis_overrides_by_action=axis_overrides_by_action,
        viewer_axes_by_label=viewer_axes_by_label,
    )
    _emit_sfx(sfx_handler, _playback_sfx_for_gameplay_action(gameplay_action))
    if action_observer is not None:
        action_observer(gameplay_action)
    return True


def _route_nd_view_action(
    key: int,
    *,
    state: GameStateND,
    view_key_handler: Callable[[int], bool] | None,
    view_action_lookup: Callable[[int], str | None] | None,
    sfx_handler: Callable[[str], None] | None,
    action_filter: Callable[[str], bool] | None,
    action_observer: Callable[[str], None] | None,
) -> None:
    if view_key_handler is None:
        return
    if _is_reserved_nd_key(key, state.config):
        return
    view_action = None
    if view_action_lookup is not None:
        view_action = view_action_lookup(key)
        if view_action is None:
            return
        if action_filter is not None and not action_filter(view_action):
            return
    if view_key_handler(key):
        _emit_sfx(sfx_handler, "menu_move")
        if action_observer is not None and view_action is not None:
            action_observer(view_action)


def handle_game_keydown(event: pygame.event.Event, state: GameStateND) -> str:
    return route_nd_keydown(
        event.key,
        state,
    )


