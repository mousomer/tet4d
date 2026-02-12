# tetris_nd/frontend_nd.py
import random
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import pygame

from .board import BoardND
from .game_nd import GameConfigND, GameStateND
from .key_dispatch import dispatch_bound_action, match_bound_action
from .keybindings import (
    KEYS_3D,
    KEYS_4D,
    PROFILE_SMALL,
    SLICE_KEYS_3D,
    SLICE_KEYS_4D,
    SYSTEM_KEYS,
    active_key_profile,
    keybinding_file_label,
    load_active_profile_bindings,
    set_active_key_profile,
)
from .menu_controls import FieldSpec, apply_menu_actions, gather_menu_actions
from .menu_keybinding_shortcuts import menu_binding_hint_line, menu_binding_status_color
from .menu_settings_state import load_menu_settings
from .pieces_nd import PIECE_SET_4D_SIX, PIECE_SET_4D_STANDARD


TEXT_COLOR = (230, 230, 230)
HIGHLIGHT_COLOR = (255, 215, 0)
DEFAULT_GAME_SEED = 1337


@dataclass
class GfxFonts:
    title_font: pygame.font.Font
    menu_font: pygame.font.Font
    hint_font: pygame.font.Font
    panel_font: pygame.font.Font


def init_fonts() -> GfxFonts:
    try:
        return GfxFonts(
            title_font=pygame.font.SysFont("consolas", 36, bold=True),
            menu_font=pygame.font.SysFont("consolas", 24),
            hint_font=pygame.font.SysFont("consolas", 18),
            panel_font=pygame.font.SysFont("consolas", 17),
        )
    except (pygame.error, OSError):
        return GfxFonts(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 24),
            hint_font=pygame.font.Font(None, 18),
            panel_font=pygame.font.Font(None, 17),
        )


def draw_gradient_background(surface: pygame.Surface,
                             top_color: Tuple[int, int, int],
                             bottom_color: Tuple[int, int, int]) -> None:
    width, height = surface.get_size()
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))


@dataclass
class GameSettingsND:
    width: int = 10
    height: int = 20
    depth: int = 6
    fourth: int = 4
    speed_level: int = 1
    piece_set_index: int = 0


_PIECE_SET_4D_CHOICES = (
    PIECE_SET_4D_STANDARD,
    PIECE_SET_4D_SIX,
)
_PIECE_SET_4D_LABELS = (
    "True 4D (5-cell)",
    "True 4D (6-cell)",
)


def _piece_set_index_to_id(index: int) -> str:
    safe_index = max(0, min(len(_PIECE_SET_4D_CHOICES) - 1, index))
    return _PIECE_SET_4D_CHOICES[safe_index]


def piece_set_4d_label(piece_set_4d: str) -> str:
    if piece_set_4d == PIECE_SET_4D_SIX:
        return _PIECE_SET_4D_LABELS[1]
    return _PIECE_SET_4D_LABELS[0]


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


def menu_fields_for_dimension(dimension: int) -> list[FieldSpec]:
    fields: list[FieldSpec] = [
        ("Board width", "width", 6, 16),
        ("Board height", "height", 12, 30),
    ]
    if dimension >= 3:
        fields.append(("Board depth (z)", "depth", 4, 12))
    if dimension >= 4:
        fields.append(("Board axis w", "fourth", 3, 10))
        fields.append(("4D piece set", "piece_set_index", 0, len(_PIECE_SET_4D_CHOICES) - 1))
    fields.append(("Speed level", "speed_level", 1, 10))
    return fields


def draw_menu(screen: pygame.Surface,
              fonts: GfxFonts,
              state: MenuState,
              dimension: int) -> None:
    draw_gradient_background(screen, (15, 15, 60), (2, 2, 20))
    width, _ = screen.get_size()
    fields = menu_fields_for_dimension(dimension)

    title_text = f"{dimension}D Tetris – Setup"
    subtitle_text = "Use Up/Down to select, Left/Right to change, Enter to start."

    title_surf = fonts.title_font.render(title_text, True, TEXT_COLOR)
    subtitle_surf = fonts.hint_font.render(subtitle_text, True, (200, 200, 220))

    title_x = (width - title_surf.get_width()) // 2
    screen.blit(title_surf, (title_x, 60))
    subtitle_x = (width - subtitle_surf.get_width()) // 2
    screen.blit(subtitle_surf, (subtitle_x, 108))

    panel_w = int(width * 0.65)
    panel_h = 90 + len(fields) * 44
    panel_x = (width - panel_w) // 2
    panel_y = 160

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (0, 0, 0, 140), panel_surf.get_rect(), border_radius=16)
    screen.blit(panel_surf, (panel_x, panel_y))

    y = panel_y + 28
    for idx, (label, attr_name, _, _) in enumerate(fields):
        value = getattr(state.settings, attr_name)
        if attr_name == "piece_set_index":
            safe_index = max(0, min(len(_PIECE_SET_4D_LABELS) - 1, int(value)))
            value_text = _PIECE_SET_4D_LABELS[safe_index]
        else:
            value_text = str(value)
        text = f"{label}: {value_text}"
        selected = idx == state.selected_index
        txt_color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        text_surf = fonts.menu_font.render(text, True, txt_color)
        text_rect = text_surf.get_rect(topleft=(panel_x + 36, y))
        if selected:
            highlight_rect = text_rect.inflate(20, 10)
            highlight_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(highlight_surf, (255, 255, 255, 40), highlight_surf.get_rect(), border_radius=10)
            screen.blit(highlight_surf, highlight_rect.topleft)
        screen.blit(text_surf, text_rect.topleft)
        y += 44

    rebind_target = "-"
    if state.rebind_targets:
        group, action_name = state.rebind_targets[state.rebind_index % len(state.rebind_targets)]
        rebind_target = f"{group}.{action_name}"

    hint_lines = [
        "Esc = quit",
        menu_binding_hint_line(dimension),
        f"Profile: {state.active_profile}   [ / ] cycle   N new   Backspace delete custom",
        "F5 save settings   F9 load settings   F8 reset defaults",
        f"B rebind {'ON' if state.rebind_mode else 'OFF'}   target: {rebind_target}   Tab/` target",
        f"Profile file: {keybinding_file_label(dimension)}",
        "Controls are shown in-game on the side panel.",
    ]
    hint_y = panel_y + panel_h + 24
    for line in hint_lines:
        surf = fonts.hint_font.render(line, True, (210, 210, 230))
        hint_x = (width - surf.get_width()) // 2
        screen.blit(surf, (hint_x, hint_y))
        hint_y += surf.get_height() + 4

    if state.bindings_status:
        status_color = menu_binding_status_color(state.bindings_status_error)
        status_surf = fonts.hint_font.render(state.bindings_status, True, status_color)
        status_x = (width - status_surf.get_width()) // 2
        screen.blit(status_surf, (status_x, hint_y))


def run_menu(screen: pygame.Surface,
             fonts: GfxFonts,
             dimension: int) -> Optional[GameSettingsND]:
    clock = pygame.time.Clock()
    set_ok, _ = set_active_key_profile(PROFILE_SMALL)
    if set_ok:
        load_active_profile_bindings()
    state = MenuState()
    ok, msg = load_menu_settings(state, dimension, include_profile=False)
    if not ok:
        state.bindings_status = msg
        state.bindings_status_error = True

    while state.running and not state.start_game:
        _dt = clock.tick(60)
        actions = gather_menu_actions(state, dimension)
        fields = menu_fields_for_dimension(dimension)
        apply_menu_actions(state, actions, fields, dimension)
        draw_menu(screen, fonts, state, dimension)
        pygame.display.flip()

    if state.start_game and state.running:
        return state.settings
    return None


def build_config(settings: GameSettingsND, dimension: int) -> GameConfigND:
    dims = [settings.width, settings.height]
    if dimension >= 3:
        dims.append(settings.depth)
    if dimension >= 4:
        dims.append(settings.fourth)
    piece_set_4d = _piece_set_index_to_id(settings.piece_set_index)
    return GameConfigND(
        dims=tuple(dims),
        gravity_axis=1,
        speed_level=settings.speed_level,
        piece_set_4d=piece_set_4d,
    )


def gravity_interval_ms_from_config(cfg: GameConfigND) -> int:
    interval = 1000 // max(1, min(10, cfg.speed_level))
    return max(80, interval)


def create_initial_state(cfg: GameConfigND) -> GameStateND:
    board = BoardND(cfg.dims)
    return GameStateND(config=cfg, board=board, rng=random.Random(DEFAULT_GAME_SEED))


@dataclass
class SliceState:
    axis_values: Dict[int, int] = field(default_factory=dict)


def create_initial_slice_state(cfg: GameConfigND) -> SliceState:
    values: Dict[int, int] = {}
    for axis, size in enumerate(cfg.dims):
        if axis in (0, cfg.gravity_axis):
            continue
        values[axis] = size // 2
    return SliceState(axis_values=values)


def adjust_slice_axis(slice_state: SliceState,
                      cfg: GameConfigND,
                      axis: int,
                      delta: int) -> None:
    if axis not in slice_state.axis_values:
        return
    size = cfg.dims[axis]
    curr = slice_state.axis_values[axis]
    slice_state.axis_values[axis] = max(0, min(size - 1, curr + delta))


_SYSTEM_ACTIONS = ("quit", "menu", "restart", "toggle_grid")


def system_key_action(key: int) -> str | None:
    return match_bound_action(key, SYSTEM_KEYS, _SYSTEM_ACTIONS)


def dispatch_nd_gameplay_key(key: int, state: GameStateND) -> None:
    cfg = state.config
    ndim = cfg.ndim
    gameplay_keys = KEYS_4D if ndim >= 4 else KEYS_3D
    gameplay_handlers = {
        "move_x_neg": lambda: state.try_move_axis(0, -1),
        "move_x_pos": lambda: state.try_move_axis(0, 1),
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
        gameplay_handlers.update({
            "move_w_neg": lambda: state.try_move_axis(3, -1),
            "move_w_pos": lambda: state.try_move_axis(3, 1),
            "rotate_xw_pos": lambda: state.try_rotate(0, 3, 1),
            "rotate_xw_neg": lambda: state.try_rotate(0, 3, -1),
            "rotate_yw_pos": lambda: state.try_rotate(cfg.gravity_axis, 3, 1),
            "rotate_yw_neg": lambda: state.try_rotate(cfg.gravity_axis, 3, -1),
            "rotate_zw_pos": lambda: state.try_rotate(2, 3, 1),
            "rotate_zw_neg": lambda: state.try_rotate(2, 3, -1),
        })
    dispatch_bound_action(key, gameplay_keys, gameplay_handlers)


def _dispatch_slice_key(key: int, cfg: GameConfigND, slice_state: SliceState) -> bool:
    ndim = cfg.ndim
    slice_bindings = SLICE_KEYS_4D if ndim >= 4 else SLICE_KEYS_3D
    slice_handlers = {
        "slice_z_neg": lambda: adjust_slice_axis(slice_state, cfg, axis=2, delta=-1),
        "slice_z_pos": lambda: adjust_slice_axis(slice_state, cfg, axis=2, delta=1),
    }
    if ndim >= 4:
        slice_handlers.update({
            "slice_w_neg": lambda: adjust_slice_axis(slice_state, cfg, axis=3, delta=-1),
            "slice_w_pos": lambda: adjust_slice_axis(slice_state, cfg, axis=3, delta=1),
        })
    return dispatch_bound_action(key, slice_bindings, slice_handlers) is not None


def handle_game_keydown(event: pygame.event.Event,
                        state: GameStateND,
                        slice_state: SliceState) -> str:
    cfg = state.config
    key = event.key

    system_action = system_key_action(key)
    if system_action == "quit":
        return "quit"
    if system_action == "menu":
        return "menu"
    if system_action == "restart":
        return "restart"
    if system_action == "toggle_grid":
        return "toggle_grid"

    if _dispatch_slice_key(key, cfg, slice_state):
        return "continue"

    if state.game_over:
        return "continue"

    dispatch_nd_gameplay_key(key, state)
    return "continue"
