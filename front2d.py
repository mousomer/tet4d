# tetris_nd/frontend_pygame.py

import sys
import random
from dataclasses import dataclass, field
from typing import Optional

import pygame

from tetris_nd.board import BoardND
from tetris_nd.game2d import GameConfig, GameState, Action
from tetris_nd.game_loop_common import process_game_events
from tetris_nd.gfx_game import (
    ClearEffect2D,
    GfxFonts,
    init_fonts,
    draw_menu,
    draw_game_frame,
    gravity_interval_ms_from_config,
)
from tetris_nd.keybindings import (
    DISABLED_KEYS_2D,
    KEYS_2D,
    SYSTEM_KEYS,
    initialize_keybinding_files,
)
from tetris_nd.key_dispatch import (
    dispatch_bound_action,
    match_bound_action,
)
from tetris_nd.menu_controls import (
    FieldSpec,
    apply_menu_actions,
    gather_menu_actions,
)

DEFAULT_GAME_SEED = 1337


# ---------- Menu state & actions (logic, not drawing) ----------

@dataclass
class GameSettings:
    width: int = 10
    height: int = 20
    speed_level: int = 1  # 1..10, mapped to gravity interval


@dataclass
class MenuState:
    settings: GameSettings = field(default_factory=GameSettings)
    selected_index: int = 0  # 0=width, 1=height, 2=speed
    running: bool = True
    start_game: bool = False
    bindings_status: str = ""
    bindings_status_error: bool = False


_MENU_FIELDS: list[FieldSpec] = [
    ("Board width", "width", 6, 16),
    ("Board height", "height", 12, 30),
    ("Speed level", "speed_level", 1, 10),
]


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
        apply_menu_actions(state, actions, _MENU_FIELDS, 2)
        draw_menu(
            screen,
            fonts,
            state.settings,
            state.selected_index,
            bindings_file_hint="keybindings/2d.json",
            bindings_status=state.bindings_status,
            bindings_status_error=state.bindings_status_error,
        )
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
        "restart"     -> restart game with current config
        "toggle_grid" -> toggle board grid visibility
        "continue"    -> keep running
    """
    key = event.key

    system_action = match_bound_action(
        key,
        SYSTEM_KEYS,
        ("quit", "menu", "restart", "toggle_grid"),
    )
    if system_action == "quit":
        return "quit"
    if system_action == "menu":
        return "menu"
    if system_action == "restart":
        return "restart"
    if system_action == "toggle_grid":
        return "toggle_grid"

    if state.game_over:
        # Don't react to movement keys when game over
        return "continue"

    # Explicitly disable ND-only controls in 2D mode.
    if key in DISABLED_KEYS_2D:
        return "continue"

    # Movement / rotation / drops
    dispatch_bound_action(
        key,
        KEYS_2D,
        {
            "move_x_neg": lambda: state.try_move(-1, 0),
            "move_x_pos": lambda: state.try_move(1, 0),
            "rotate_xy_pos": lambda: state.try_rotate(+1),
            "rotate_xy_neg": lambda: state.try_rotate(-1),
            "hard_drop": state.hard_drop,
            "soft_drop": lambda: state.try_move(0, 1),
        },
    )

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
    clear_anim_levels: tuple[int, ...] = ()
    clear_anim_elapsed_ms = 0.0
    clear_anim_duration_ms = 320.0
    last_lines_cleared = state.lines_cleared

    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60)
        gravity_accumulator += dt

        # ----- Events -----
        def on_restart() -> None:
            nonlocal state, gravity_accumulator, clear_anim_levels, clear_anim_elapsed_ms, last_lines_cleared
            state = create_initial_state(cfg)
            gravity_accumulator = 0
            clear_anim_levels = ()
            clear_anim_elapsed_ms = 0.0
            last_lines_cleared = state.lines_cleared

        def on_toggle_grid() -> None:
            nonlocal show_grid
            show_grid = not show_grid

        decision = process_game_events(
            keydown_handler=lambda event: handle_game_keydown(event, state, cfg),
            on_restart=on_restart,
            on_toggle_grid=on_toggle_grid,
        )
        if decision == "quit":
            return False
        if decision == "menu":
            return True

        # ----- Gravity tick -----
        if not state.game_over and gravity_accumulator >= gravity_interval_ms:
            gravity_accumulator = 0
            state.step(Action.NONE)  # just gravity

        if state.lines_cleared != last_lines_cleared:
            clear_anim_levels = tuple(state.board.last_cleared_levels)
            clear_anim_elapsed_ms = 0.0
            last_lines_cleared = state.lines_cleared
        if clear_anim_levels:
            clear_anim_elapsed_ms += dt
            if clear_anim_elapsed_ms >= clear_anim_duration_ms:
                clear_anim_levels = ()
                clear_anim_elapsed_ms = 0.0

        clear_effect = None
        if clear_anim_levels:
            clear_effect = ClearEffect2D(
                levels=clear_anim_levels,
                progress=min(1.0, clear_anim_elapsed_ms / clear_anim_duration_ms),
            )

        # ----- Drawing -----
        draw_game_frame(
            screen,
            cfg,
            state,
            fonts,
            show_grid=show_grid,
            clear_effect=clear_effect,
        )
        pygame.display.flip()

    # Normally not reached
    return False


# ---------- Main run ----------

def run():
    pygame.init()
    initialize_keybinding_files()
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
