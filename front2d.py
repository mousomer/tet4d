# tetris_nd/frontend_pygame.py

import sys
import random
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum, auto

import pygame

from tetris_nd.board import BoardND
from tetris_nd.game2d import GameConfig, GameState, Action
from tetris_nd.gfx_game import (
    GfxFonts,
    init_fonts,
    draw_menu,
    draw_game_frame,
    gravity_interval_ms_from_config,
)
from tetris_nd.keybindings import DISABLED_KEYS_2D, KEYS_2D, SYSTEM_KEYS, key_matches

DEFAULT_GAME_SEED = 1337


# ---------- Menu state & actions (logic, not drawing) ----------

@dataclass
class GameSettings:
    width: int = 10
    height: int = 20
    speed_level: int = 1  # 1..10, mapped to gravity interval


class MenuAction(Enum):
    QUIT = auto()
    START_GAME = auto()
    SELECT_UP = auto()
    SELECT_DOWN = auto()
    VALUE_LEFT = auto()
    VALUE_RIGHT = auto()
    NO_OP = auto()


@dataclass
class MenuState:
    settings: GameSettings = field(default_factory=GameSettings)
    selected_index: int = 0  # 0=width, 1=height, 2=speed
    running: bool = True
    start_game: bool = False


# ---------- Menu logic helpers ----------

def gather_menu_actions() -> List[MenuAction]:
    actions: List[MenuAction] = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            actions.append(MenuAction.QUIT)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                actions.append(MenuAction.QUIT)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                actions.append(MenuAction.START_GAME)
            elif event.key == pygame.K_UP:
                actions.append(MenuAction.SELECT_UP)
            elif event.key == pygame.K_DOWN:
                actions.append(MenuAction.SELECT_DOWN)
            elif event.key == pygame.K_LEFT:
                actions.append(MenuAction.VALUE_LEFT)
            elif event.key == pygame.K_RIGHT:
                actions.append(MenuAction.VALUE_RIGHT)
    if not actions:
        actions.append(MenuAction.NO_OP)
    return actions


def apply_menu_actions(state: MenuState, actions: List[MenuAction]) -> None:
    for action in actions:
        if action == MenuAction.NO_OP:
            continue

        if action == MenuAction.QUIT:
            state.running = False

        elif action == MenuAction.START_GAME:
            state.start_game = True

        elif action == MenuAction.SELECT_UP:
            state.selected_index = (state.selected_index - 1) % 3

        elif action == MenuAction.SELECT_DOWN:
            state.selected_index = (state.selected_index + 1) % 3

        elif action == MenuAction.VALUE_LEFT:
            if state.selected_index == 0:
                state.settings.width = max(6, state.settings.width - 1)
            elif state.selected_index == 1:
                state.settings.height = max(12, state.settings.height - 1)
            elif state.selected_index == 2:
                state.settings.speed_level = max(1, state.settings.speed_level - 1)

        elif action == MenuAction.VALUE_RIGHT:
            if state.selected_index == 0:
                state.settings.width = min(16, state.settings.width + 1)
            elif state.selected_index == 1:
                state.settings.height = min(30, state.settings.height + 1)
            elif state.selected_index == 2:
                state.settings.speed_level = min(10, state.settings.speed_level + 1)


# ---------- Menu loop ----------

def run_menu(screen: pygame.Surface, fonts: GfxFonts) -> Optional[GameSettings]:
    """
    Intro screen where width, height, and speed_level can be set.
    Returns GameSettings if user starts the game, or None if user quits.
    """
    clock = pygame.time.Clock()
    state = MenuState()

    while state.running and not state.start_game:
        _dt = clock.tick(60)
        actions = gather_menu_actions()
        apply_menu_actions(state, actions)
        draw_menu(screen, fonts, state.settings, state.selected_index)
        pygame.display.flip()

    if state.start_game and state.running:
        return state.settings
    return None


# ---------- Game helpers ----------

def create_initial_state(cfg: GameConfig) -> GameState:
    board = BoardND((cfg.width, cfg.height))
    return GameState(config=cfg, board=board, rng=random.Random(DEFAULT_GAME_SEED))


def handle_game_keydown(event: pygame.event.Event,
                        state: GameState,
                        cfg: GameConfig) -> Optional[str]:
    """
    Handle a single KEYDOWN event during the game.
    Returns:
        "quit"        -> user wants to quit the program
        "menu"        -> user wants to go back to the menu
        "toggle_grid" -> toggle board grid visibility
        "continue"    -> keep running
    """
    key = event.key

    if key_matches(SYSTEM_KEYS, "quit", key):
        return "quit"

    if key_matches(SYSTEM_KEYS, "menu", key):
        return "menu"

    if key_matches(SYSTEM_KEYS, "restart", key):
        # Restart game with same config
        new_state = create_initial_state(cfg)
        state.board = new_state.board
        state.current_piece = new_state.current_piece
        state.next_bag = new_state.next_bag
        state.rng = new_state.rng
        state.score = 0
        state.lines_cleared = 0
        state.game_over = False
        return "continue"

    if key == pygame.K_g:
        return "toggle_grid"

    if state.game_over:
        # Don't react to movement keys when game over
        return "continue"

    # Explicitly disable ND-only controls in 2D mode.
    if key in DISABLED_KEYS_2D:
        return "continue"

    # Movement / rotation / drops
    if key_matches(KEYS_2D, "move_x_neg", key):
        state.try_move(-1, 0)
    elif key_matches(KEYS_2D, "move_x_pos", key):
        state.try_move(1, 0)
    elif key_matches(KEYS_2D, "rotate_xy_pos", key):
        state.try_rotate(+1)
    elif key_matches(KEYS_2D, "rotate_xy_neg", key):
        state.try_rotate(-1)
    elif key_matches(KEYS_2D, "hard_drop", key):
        state.hard_drop()
    elif key_matches(KEYS_2D, "soft_drop", key):
        state.try_move(0, 1)

    return "continue"


def run_game_loop(screen: pygame.Surface,
                  cfg: GameConfig,
                  fonts: GfxFonts) -> bool:
    """
    Run a single game session.
    Returns:
        True  -> user wants to go back to menu
        False -> user wants to quit the program
    """
    state = create_initial_state(cfg)
    gravity_interval_ms = gravity_interval_ms_from_config(cfg)
    gravity_accumulator = 0
    show_grid = True

    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60)
        gravity_accumulator += dt

        # ----- Events -----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                result = handle_game_keydown(event, state, cfg)
                if result == "quit":
                    return False
                if result == "menu":
                    return True
                if result == "toggle_grid":
                    show_grid = not show_grid

        # ----- Gravity tick -----
        if not state.game_over and gravity_accumulator >= gravity_interval_ms:
            gravity_accumulator = 0
            state.step(Action.NONE)  # just gravity

        # ----- Drawing -----
        draw_game_frame(screen, cfg, state, fonts, show_grid=show_grid)
        pygame.display.flip()

    # Normally not reached
    return False


# ---------- Main run ----------

def run():
    pygame.init()
    fonts = init_fonts()

    running = True
    while running:
        # --- MENU ---
        pygame.display.set_caption("2D Tetris – Setup")
        menu_screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        settings = run_menu(menu_screen, fonts)
        if settings is None:
            break  # user quit from menu

        # --- GAME ---
        cfg = GameConfig(
            width=settings.width,
            height=settings.height,
            gravity_axis=1,
            speed_level=settings.speed_level,
        )

        # Initial suggested window size; user can resize afterwards
        board_px_w = cfg.width * 30  # CELL_SIZE from gfx
        board_px_h = cfg.height * 30
        window_w = board_px_w + 200 + 3 * 20  # SIDE_PANEL + margins
        window_h = board_px_h + 2 * 20

        pygame.display.set_caption("2D Tetris")
        game_screen = pygame.display.set_mode((window_w, window_h), pygame.RESIZABLE)

        back_to_menu = run_game_loop(game_screen, cfg, fonts)
        if not back_to_menu:
            running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
