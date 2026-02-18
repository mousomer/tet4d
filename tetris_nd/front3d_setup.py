from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

import pygame
from .board import BoardND
from .challenge_mode import apply_challenge_prefill_nd
from .game_nd import GameConfigND, GameStateND
from .keybindings import active_key_profile, load_active_profile_bindings
from .menu_config import default_settings_payload, setup_fields_for_dimension
from .menu_controls import FieldSpec, MenuAction, apply_menu_actions, gather_menu_actions
from .menu_keybinding_shortcuts import menu_binding_status_color
from .menu_settings_state import load_menu_settings, save_menu_settings
from .pieces_nd import piece_set_label, piece_set_options_for_dimension
from .exploration_mode import minimal_exploration_dims_nd
from .playbot import run_dry_run_nd
from .playbot.types import bot_planner_algorithm_from_index, bot_planner_profile_from_index
from .projection3d import draw_gradient_background
from .speed_curve import gravity_interval_ms


BG_TOP = (18, 24, 50)
BG_BOTTOM = (6, 8, 20)
TEXT_COLOR = (230, 230, 230)
HIGHLIGHT_COLOR = (255, 215, 0)
DEFAULT_GAME_SEED = 1337
_DEFAULT_MODE_3D = default_settings_payload()["settings"]["3d"]


@dataclass
class GameSettings3D:
    width: int = _DEFAULT_MODE_3D["width"]
    height: int = _DEFAULT_MODE_3D["height"]
    depth: int = _DEFAULT_MODE_3D["depth"]
    speed_level: int = _DEFAULT_MODE_3D["speed_level"]
    piece_set_index: int = _DEFAULT_MODE_3D["piece_set_index"]
    bot_mode_index: int = _DEFAULT_MODE_3D["bot_mode_index"]
    bot_algorithm_index: int = _DEFAULT_MODE_3D["bot_algorithm_index"]
    bot_profile_index: int = _DEFAULT_MODE_3D["bot_profile_index"]
    bot_speed_level: int = _DEFAULT_MODE_3D["bot_speed_level"]
    bot_budget_ms: int = _DEFAULT_MODE_3D["bot_budget_ms"]
    challenge_layers: int = _DEFAULT_MODE_3D["challenge_layers"]
    exploration_mode: int = _DEFAULT_MODE_3D["exploration_mode"]


_PIECE_SET_3D_CHOICES = tuple(piece_set_options_for_dimension(3))
_PIECE_SET_3D_LABELS = tuple(piece_set_label(piece_set_id) for piece_set_id in _PIECE_SET_3D_CHOICES)


@dataclass
class MenuState:
    settings: GameSettings3D = field(default_factory=GameSettings3D)
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


_MENU_FIELDS: list[FieldSpec] = [
    *setup_fields_for_dimension(3, piece_set_max=len(_PIECE_SET_3D_CHOICES) - 1),
]

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


def _menu_value_text(attr_name: str, value: object) -> str:
    if attr_name == "piece_set_index":
        safe_index = max(0, min(len(_PIECE_SET_3D_LABELS) - 1, int(value)))
        return _PIECE_SET_3D_LABELS[safe_index]
    if attr_name == "exploration_mode":
        return "ON" if int(value) else "OFF"
    return str(value)


def draw_menu(screen: pygame.Surface, fonts, state: MenuState) -> None:
    draw_gradient_background(screen, BG_TOP, BG_BOTTOM)
    width, _ = screen.get_size()

    title = fonts.title_font.render("3D Tetris – Setup", True, TEXT_COLOR)
    subtitle = fonts.hint_font.render(
        "Use Up/Down to select, Left/Right to change, Enter to start.",
        True,
        (210, 210, 230),
    )
    screen.blit(title, ((width - title.get_width()) // 2, 60))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, 108))

    panel_w = int(width * 0.62)
    panel_h = max(280, 96 + len(_MENU_FIELDS) * 44)
    panel_x = (width - panel_w) // 2
    panel_y = 160

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 145), panel.get_rect(), border_radius=16)
    screen.blit(panel, (panel_x, panel_y))

    y = panel_y + 28
    for idx, (label, attr_name, _, _) in enumerate(_MENU_FIELDS):
        value = getattr(state.settings, attr_name)
        value_text = _menu_value_text(attr_name, value)
        text = f"{label}: {value_text}"
        selected = idx == state.selected_index
        text_color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        surf = fonts.menu_font.render(text, True, text_color)
        rect = surf.get_rect(topleft=(panel_x + 36, y))
        if selected:
            hi_rect = rect.inflate(20, 10)
            hi = pygame.Surface(hi_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 40), hi.get_rect(), border_radius=10)
            screen.blit(hi, hi_rect.topleft)
        screen.blit(surf, rect.topleft)
        y += 50

    hints = [
        "Esc = quit",
        "F7 dry-run verify (bot, no graphics)",
        "Use Main Menu -> Bot Options / Keybindings for shared controls.",
        "Projection modes are available during gameplay (P).",
    ]
    hy = panel_y + panel_h + 20
    for line in hints:
        surf = fonts.hint_font.render(line, True, (210, 210, 230))
        screen.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 4

    if state.bindings_status:
        status_color = menu_binding_status_color(state.bindings_status_error)
        status = fonts.hint_font.render(state.bindings_status, True, status_color)
        screen.blit(status, ((width - status.get_width()) // 2, hy))


def run_menu(screen: pygame.Surface, fonts) -> Optional[GameSettings3D]:
    clock = pygame.time.Clock()
    load_active_profile_bindings()
    state = MenuState()
    ok, msg = load_menu_settings(state, 3, include_profile=True)
    if not ok:
        state.bindings_status = msg
        state.bindings_status_error = True

    while state.running and not state.start_game:
        _dt = clock.tick(60)
        actions = gather_menu_actions(state, 3)
        apply_menu_actions(
            state,
            actions,
            _MENU_FIELDS,
            3,
            blocked_actions=_SETUP_BLOCKED_ACTIONS,
        )
        if state.run_dry_run:
            if bool(state.settings.exploration_mode):
                state.bindings_status = "Dry-run is disabled in exploration mode"
                state.bindings_status_error = False
            else:
                report = run_dry_run_nd(
                    build_config(state.settings),
                    planner_profile=bot_planner_profile_from_index(state.settings.bot_profile_index),
                    planning_budget_ms=state.settings.bot_budget_ms,
                    planner_algorithm=bot_planner_algorithm_from_index(state.settings.bot_algorithm_index),
                )
                state.bindings_status = report.reason
                state.bindings_status_error = not report.passed
        draw_menu(screen, fonts, state)
        pygame.display.flip()

    if state.running and state.start_game:
        ok, msg = save_menu_settings(state, 3)
        if not ok:
            state.bindings_status = msg
            state.bindings_status_error = True
        return state.settings
    save_menu_settings(state, 3)
    return None


def gravity_interval_ms_from_config(cfg: GameConfigND) -> int:
    return gravity_interval_ms(cfg.speed_level, dimension=3)


def build_config(settings: GameSettings3D) -> GameConfigND:
    piece_set_id = _PIECE_SET_3D_CHOICES[
        max(0, min(len(_PIECE_SET_3D_CHOICES) - 1, settings.piece_set_index))
    ]
    exploration_enabled = bool(settings.exploration_mode)
    dims = (settings.width, settings.height, settings.depth)
    if exploration_enabled:
        dims = minimal_exploration_dims_nd(3, piece_set_id)
    return GameConfigND(
        dims=dims,
        gravity_axis=1,
        speed_level=settings.speed_level,
        piece_set_id=piece_set_id,
        challenge_layers=0 if exploration_enabled else settings.challenge_layers,
        exploration_mode=exploration_enabled,
    )


def create_initial_state(cfg: GameConfigND) -> GameStateND:
    board = BoardND(cfg.dims)
    state = GameStateND(config=cfg, board=board, rng=random.Random(DEFAULT_GAME_SEED))
    if not cfg.exploration_mode:
        apply_challenge_prefill_nd(state, layers=cfg.challenge_layers)
    return state
