# tetris_nd/frontend_nd.py
import random
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Optional, Tuple

import pygame

from .core.model import BoardND
from .challenge_mode import apply_challenge_prefill_nd
from .font_profiles import GfxFonts, init_fonts as init_fonts_for_profile
from .gameplay.game_nd import GameConfigND, GameStateND
from .ui_logic.key_dispatch import match_bound_action
from .keybindings import (
    KEYS_3D,
    KEYS_4D,
    SYSTEM_KEYS,
    active_key_profile,
    load_active_profile_bindings,
)
from .ui_logic.menu_controls import (
    FieldSpec,
    MenuAction,
    apply_menu_actions,
    gather_menu_actions,
)
from .runtime.menu_config import default_settings_payload, setup_fields_for_dimension
from .ui_logic.menu_keybinding_shortcuts import menu_binding_status_color
from .runtime.menu_settings_state import load_menu_settings, save_menu_settings
from .pieces_nd import piece_set_label, piece_set_options_for_dimension
from .exploration_mode import minimal_exploration_dims_nd
from .playbot import run_dry_run_nd
from .playbot.types import (
    bot_planner_algorithm_from_index,
    bot_planner_profile_from_index,
)
from .speed_curve import gravity_interval_ms
from .topology import topology_mode_from_index, topology_mode_label
from .topology_designer import (
    designer_profile_label_for_index,
    designer_profiles_for_dimension,
    export_resolved_topology_profile,
    resolve_topology_designer_selection,
)
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text
from .view_controls import viewer_relative_move_axis_delta


TEXT_COLOR = (230, 230, 230)
HIGHLIGHT_COLOR = (255, 215, 0)
DEFAULT_GAME_SEED = 1337
_DEFAULT_MODE_4D = default_settings_payload()["settings"]["4d"]


def init_fonts() -> GfxFonts:
    return init_fonts_for_profile("nd")


def draw_gradient_background(
    surface: pygame.Surface,
    top_color: Tuple[int, int, int],
    bottom_color: Tuple[int, int, int],
) -> None:
    draw_vertical_gradient(surface, top_color, bottom_color)


@dataclass
class GameSettingsND:
    width: int = _DEFAULT_MODE_4D["width"]
    height: int = _DEFAULT_MODE_4D["height"]
    depth: int = _DEFAULT_MODE_4D["depth"]
    fourth: int = _DEFAULT_MODE_4D["fourth"]
    speed_level: int = _DEFAULT_MODE_4D["speed_level"]
    piece_set_index: int = _DEFAULT_MODE_4D["piece_set_index"]
    topology_mode: int = _DEFAULT_MODE_4D["topology_mode"]
    topology_advanced: int = _DEFAULT_MODE_4D["topology_advanced"]
    topology_profile_index: int = _DEFAULT_MODE_4D["topology_profile_index"]
    bot_mode_index: int = _DEFAULT_MODE_4D["bot_mode_index"]
    bot_algorithm_index: int = _DEFAULT_MODE_4D["bot_algorithm_index"]
    bot_profile_index: int = _DEFAULT_MODE_4D["bot_profile_index"]
    bot_speed_level: int = _DEFAULT_MODE_4D["bot_speed_level"]
    bot_budget_ms: int = _DEFAULT_MODE_4D["bot_budget_ms"]
    challenge_layers: int = _DEFAULT_MODE_4D["challenge_layers"]
    exploration_mode: int = _DEFAULT_MODE_4D["exploration_mode"]


_PIECE_SET_CHOICES = {
    3: tuple(piece_set_options_for_dimension(3)),
    4: tuple(piece_set_options_for_dimension(4)),
}
_PIECE_SET_LABELS = {
    dimension: tuple(piece_set_label(piece_set_id) for piece_set_id in choices)
    for dimension, choices in _PIECE_SET_CHOICES.items()
}
_TOPOLOGY_PROFILE_LABELS = {
    dimension: tuple(
        profile.label for profile in designer_profiles_for_dimension(dimension)
    )
    for dimension in (2, 3, 4)
}


def _piece_set_index_to_id(dimension: int, index: int) -> str:
    choices = _PIECE_SET_CHOICES.get(dimension, _PIECE_SET_CHOICES[4])
    safe_index = max(0, min(len(choices) - 1, int(index)))
    return choices[safe_index]


def piece_set_4d_label(piece_set_4d: str) -> str:
    return piece_set_label(piece_set_4d)


@dataclass
class MenuState:
    settings: GameSettingsND = field(default_factory=GameSettingsND)
    selected_index: int = 0
    running: bool = True
    start_game: bool = False
    bindings_status: str = ""
    bindings_status_error: bool = False
    active_profile: str = field(default_factory=active_key_profile)
    rebind_mode: bool = False
    rebind_index: int = 0
    rebind_targets: list[tuple[str, str]] = field(default_factory=list)
    rebind_conflict_mode: str = "replace"
    run_dry_run: bool = False


def menu_fields_for_settings(
    settings: GameSettingsND, dimension: int
) -> list[FieldSpec]:
    choices = _PIECE_SET_CHOICES.get(dimension)
    piece_set_max = 0 if choices is None else max(0, len(choices) - 1)
    topology_profile_max = max(0, len(_TOPOLOGY_PROFILE_LABELS.get(dimension, ())) - 1)
    fields = setup_fields_for_dimension(
        dimension,
        piece_set_max=piece_set_max,
        topology_profile_max=topology_profile_max,
    )
    if int(settings.topology_advanced):
        return fields
    return [field for field in fields if field[1] != "topology_profile_index"]


_SETUP_BLOCKED_ACTIONS = {
    MenuAction.LOAD_BINDINGS,
    MenuAction.SAVE_BINDINGS,
    MenuAction.LOAD_SETTINGS,
    MenuAction.SAVE_SETTINGS,
    MenuAction.RESET_SETTINGS,
    MenuAction.PROFILE_PREV,
    MenuAction.PROFILE_NEXT,
    MenuAction.PROFILE_NEW,
    MenuAction.PROFILE_DELETE,
    MenuAction.REBIND_TOGGLE,
    MenuAction.REBIND_TARGET_NEXT,
    MenuAction.REBIND_TARGET_PREV,
    MenuAction.REBIND_CONFLICT_NEXT,
    MenuAction.RESET_BINDINGS,
}


def _menu_value_text(dimension: int, attr_name: str, value: object) -> str:
    if attr_name == "piece_set_index":
        labels = _PIECE_SET_LABELS.get(dimension, _PIECE_SET_LABELS[4])
        safe_index = max(0, min(len(labels) - 1, int(value)))
        return labels[safe_index]
    if attr_name == "topology_mode":
        return topology_mode_label(topology_mode_from_index(int(value)))
    if attr_name == "topology_advanced":
        return "ON" if int(value) else "OFF"
    if attr_name == "topology_profile_index":
        return designer_profile_label_for_index(dimension, int(value))
    if attr_name == "exploration_mode":
        return "ON" if int(value) else "OFF"
    return str(value)


def draw_menu(
    screen: pygame.Surface, fonts: GfxFonts, state: MenuState, dimension: int
) -> None:
    draw_gradient_background(screen, (15, 15, 60), (2, 2, 20))
    width, height = screen.get_size()
    fields = menu_fields_for_settings(state.settings, dimension)

    title_text = f"{dimension}D Tetris - Setup"
    subtitle_text = fit_text(
        fonts.hint_font,
        "Use Up/Down to select, Left/Right to change, Enter to start.",
        width - 28,
    )

    title_surf = fonts.title_font.render(title_text, True, TEXT_COLOR)
    subtitle_surf = fonts.hint_font.render(subtitle_text, True, (200, 200, 220))

    title_y = 48
    title_x = (width - title_surf.get_width()) // 2
    screen.blit(title_surf, (title_x, title_y))
    subtitle_y = title_y + title_surf.get_height() + 8
    subtitle_x = (width - subtitle_surf.get_width()) // 2
    screen.blit(subtitle_surf, (subtitle_x, subtitle_y))

    panel_w = min(max(360, int(width * 0.65)), width - 24)
    hint_line_h = fonts.hint_font.get_height() + 4
    bottom_lines = 4 + (1 if state.bindings_status else 0)
    panel_top = subtitle_y + subtitle_surf.get_height() + 12
    panel_max_h = max(140, height - panel_top - (bottom_lines * hint_line_h) - 10)
    row_h = min(
        44,
        max(
            fonts.menu_font.get_height() + 8, (panel_max_h - 40) // max(1, len(fields))
        ),
    )
    panel_h = min(panel_max_h, 40 + len(fields) * row_h)
    panel_x = (width - panel_w) // 2
    panel_y = max(
        panel_top,
        min(
            (height - panel_h) // 2, height - panel_h - (bottom_lines * hint_line_h) - 8
        ),
    )

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(
        panel_surf, (0, 0, 0, 140), panel_surf.get_rect(), border_radius=16
    )
    screen.blit(panel_surf, (panel_x, panel_y))

    y = panel_y + 20
    option_x = panel_x + 24
    option_w = panel_w - 48
    option_bottom = panel_y + panel_h - 10
    for idx, (label, attr_name, _, _) in enumerate(fields):
        if y + fonts.menu_font.get_height() > option_bottom:
            break
        value = getattr(state.settings, attr_name)
        value_text = _menu_value_text(dimension, attr_name, value)
        text = f"{label}: {value_text}"
        selected = idx == state.selected_index
        txt_color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        text_fit = fit_text(fonts.menu_font, text, option_w - 6)
        text_surf = fonts.menu_font.render(text_fit, True, txt_color)
        text_rect = text_surf.get_rect(topleft=(option_x, y))
        if selected:
            highlight_rect = pygame.Rect(
                option_x - 8, y - 4, option_w + 16, text_rect.height + 10
            )
            highlight_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                highlight_surf,
                (255, 255, 255, 40),
                highlight_surf.get_rect(),
                border_radius=10,
            )
            screen.blit(highlight_surf, highlight_rect.topleft)
        screen.blit(text_surf, text_rect.topleft)
        y += row_h

    hint_lines = [
        "Esc = quit",
        "F7 dry-run verify (bot, no graphics)",
        "Use Main Menu -> Bot Options / Keybindings for shared controls.",
        "Controls are shown in-game on the side panel.",
    ]
    hint_y = panel_y + panel_h + 8
    max_hint_lines = max(1, (height - hint_y - 6) // max(1, hint_line_h))
    hint_budget = max(1, max_hint_lines - (1 if state.bindings_status else 0))
    for line in hint_lines[:hint_budget]:
        line_fit = fit_text(fonts.hint_font, line, width - 28)
        surf = fonts.hint_font.render(line_fit, True, (210, 210, 230))
        hint_x = (width - surf.get_width()) // 2
        screen.blit(surf, (hint_x, hint_y))
        hint_y += surf.get_height() + 4

    if state.bindings_status and hint_y + hint_line_h <= height - 6:
        status_color = menu_binding_status_color(state.bindings_status_error)
        status_text = fit_text(fonts.hint_font, state.bindings_status, width - 28)
        status_surf = fonts.hint_font.render(status_text, True, status_color)
        status_x = (width - status_surf.get_width()) // 2
        screen.blit(status_surf, (status_x, hint_y))


def run_menu(
    screen: pygame.Surface, fonts: GfxFonts, dimension: int
) -> Optional[GameSettingsND]:
    clock = pygame.time.Clock()
    load_active_profile_bindings()
    state = MenuState()
    ok, msg = load_menu_settings(state, dimension, include_profile=True)
    if not ok:
        state.bindings_status = msg
        state.bindings_status_error = True

    while state.running and not state.start_game:
        _dt = clock.tick(60)
        actions = gather_menu_actions(state, dimension)
        fields = menu_fields_for_settings(state.settings, dimension)
        if state.selected_index >= len(fields):
            state.selected_index = max(0, len(fields) - 1)
        apply_menu_actions(
            state,
            actions,
            fields,
            dimension,
            blocked_actions=_SETUP_BLOCKED_ACTIONS,
        )
        if state.run_dry_run:
            if bool(state.settings.exploration_mode):
                state.bindings_status = "Dry-run is disabled in exploration mode"
                state.bindings_status_error = False
            else:
                report = run_dry_run_nd(
                    build_config(state.settings, dimension),
                    planner_profile=bot_planner_profile_from_index(
                        state.settings.bot_profile_index
                    ),
                    planning_budget_ms=state.settings.bot_budget_ms,
                    planner_algorithm=bot_planner_algorithm_from_index(
                        state.settings.bot_algorithm_index
                    ),
                )
                state.bindings_status = report.reason
                state.bindings_status_error = not report.passed
        draw_menu(screen, fonts, state, dimension)
        pygame.display.flip()

    if state.start_game and state.running:
        ok, msg = save_menu_settings(state, dimension)
        if not ok:
            state.bindings_status = msg
            state.bindings_status_error = True
        else:
            topology_mode = topology_mode_from_index(state.settings.topology_mode)
            export_resolved_topology_profile(
                dimension=dimension,
                gravity_axis=1,
                topology_mode=topology_mode,
                topology_advanced=bool(state.settings.topology_advanced),
                profile_index=state.settings.topology_profile_index,
            )
        return state.settings
    # Autosave setup/session state on exit as well (without explicit Save action).
    save_menu_settings(state, dimension)
    return None


def build_config(settings: GameSettingsND, dimension: int) -> GameConfigND:
    piece_set_id = _piece_set_index_to_id(dimension, settings.piece_set_index)
    topology_mode = topology_mode_from_index(settings.topology_mode)
    resolved_mode, topology_edge_rules, _profile = resolve_topology_designer_selection(
        dimension=dimension,
        gravity_axis=1,
        topology_mode=topology_mode,
        topology_advanced=bool(settings.topology_advanced),
        profile_index=settings.topology_profile_index,
    )
    exploration_enabled = bool(settings.exploration_mode)
    dims = [settings.width, settings.height]
    if dimension >= 3:
        dims.append(settings.depth)
    if dimension >= 4:
        dims.append(settings.fourth)
    if exploration_enabled:
        dims = list(minimal_exploration_dims_nd(dimension, piece_set_id))
    return GameConfigND(
        dims=tuple(dims),
        gravity_axis=1,
        speed_level=settings.speed_level,
        topology_mode=resolved_mode,
        topology_edge_rules=topology_edge_rules,
        piece_set_id=piece_set_id,
        challenge_layers=0 if exploration_enabled else settings.challenge_layers,
        exploration_mode=exploration_enabled,
    )


def gravity_interval_ms_from_config(cfg: GameConfigND) -> int:
    return gravity_interval_ms(cfg.speed_level, dimension=max(2, cfg.ndim))


def create_initial_state(cfg: GameConfigND) -> GameStateND:
    board = BoardND(cfg.dims)
    state = GameStateND(config=cfg, board=board, rng=random.Random(DEFAULT_GAME_SEED))
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


def apply_nd_gameplay_action_with_view(
    state: GameStateND,
    action: str,
    *,
    yaw_deg_for_view_movement: float | None = None,
    axis_overrides_by_action: Mapping[str, tuple[int, int]] | None = None,
) -> bool:
    if axis_overrides_by_action is not None:
        override = axis_overrides_by_action.get(action)
        if override is not None:
            axis, delta = override
            state.try_move_axis(axis, delta)
            return True
    if yaw_deg_for_view_movement is not None:
        intent = _VIEWER_RELATIVE_INTENT_BY_ACTION.get(action)
        if intent is not None:
            axis, delta = viewer_relative_move_axis_delta(
                yaw_deg_for_view_movement, intent
            )
            state.try_move_axis(axis, delta)
            return True
    return apply_nd_gameplay_action(state, action)


def dispatch_nd_gameplay_key(
    key: int,
    state: GameStateND,
    *,
    yaw_deg_for_view_movement: float | None = None,
    axis_overrides_by_action: Mapping[str, tuple[int, int]] | None = None,
) -> str | None:
    action = gameplay_action_for_key(key, state.config)
    if action is None:
        return None
    apply_nd_gameplay_action_with_view(
        state,
        action,
        yaw_deg_for_view_movement=yaw_deg_for_view_movement,
        axis_overrides_by_action=axis_overrides_by_action,
    )
    return action


def route_nd_keydown(
    key: int,
    state: GameStateND,
    *,
    yaw_deg_for_view_movement: float | None = None,
    axis_overrides_by_action: Mapping[str, tuple[int, int]] | None = None,
    view_key_handler: Callable[[int], bool] | None = None,
    sfx_handler: Callable[[str], None] | None = None,
    allow_gameplay: bool = True,
) -> str:
    cfg = state.config
    system_action = system_key_action(key)
    if system_action is not None:
        _emit_sfx(sfx_handler, _SYSTEM_SFX.get(system_action))
        return system_action

    gameplay_action = None
    if allow_gameplay and not state.game_over:
        gameplay_action = dispatch_nd_gameplay_key(
            key,
            state,
            yaw_deg_for_view_movement=yaw_deg_for_view_movement,
            axis_overrides_by_action=axis_overrides_by_action,
        )
        if gameplay_action is not None:
            _emit_sfx(sfx_handler, _playback_sfx_for_gameplay_action(gameplay_action))
            return "continue"

    if view_key_handler is None:
        return "continue"

    if _is_reserved_nd_key(key, cfg):
        return "continue"
    if view_key_handler(key):
        _emit_sfx(sfx_handler, "menu_move")
    return "continue"


def handle_game_keydown(event: pygame.event.Event, state: GameStateND) -> str:
    return route_nd_keydown(
        event.key,
        state,
    )
