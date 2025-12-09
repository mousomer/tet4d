# tetris_nd/frontend_pygame.py

import sys
from dataclasses import dataclass
from typing import Tuple, Optional, List
from enum import Enum, auto

import pygame

from tetris_nd.board import BoardND
from tetris_nd.game2d import GameConfig, GameState, Action


# ---------- Visual config ----------

CELL_SIZE = 30          # pixels per cell
MARGIN = 20             # outer margin
SIDE_PANEL = 200        # width for score / text

BG_COLOR = (10, 10, 30)
GRID_COLOR = (40, 40, 80)
TEXT_COLOR = (230, 230, 230)
HIGHLIGHT_COLOR = (255, 215, 0)

# Tetromino-ish colors for IDs 1..7
COLOR_MAP = {
    1: (0, 255, 255),    # I - cyan
    2: (255, 255, 0),    # O - yellow
    3: (160, 0, 240),    # T - purple
    4: (0, 255, 0),      # S - green
    5: (255, 0, 0),      # Z - red
    6: (0, 0, 255),      # J - blue
    7: (255, 165, 0),    # L - orange
}

@dataclass
class MenuFonts:
    title_font: pygame.font.Font
    menu_font: pygame.font.Font
    hint_font: pygame.font.Font


def init_menu_fonts() -> MenuFonts:
    try:
        title_font = pygame.font.SysFont("consolas", 36, bold=True)
        menu_font = pygame.font.SysFont("consolas", 24)
        hint_font = pygame.font.SysFont("consolas", 18)
    except Exception:
        title_font = pygame.font.Font(None, 36)
        menu_font = pygame.font.Font(None, 24)
        hint_font = pygame.font.Font(None, 18)
    return MenuFonts(title_font, menu_font, hint_font)


def draw_gradient_background(surface: pygame.Surface,
                             top_color: Tuple[int, int, int],
                             bottom_color: Tuple[int, int, int]) -> None:
    """Simple vertical gradient fill."""
    width, height = surface.get_size()
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))


def color_for_cell(cell_id: int) -> Tuple[int, int, int]:
    if cell_id <= 0:
        return (0, 0, 0)
    return COLOR_MAP.get(cell_id, (200, 200, 200))


# ---------- Settings dataclass ----------

@dataclass
class GameSettings:
    width: int = 10
    height: int = 20
    speed_level: int = 5  # 1..10, mapped to gravity interval


def gravity_interval_ms_from_config(cfg: GameConfig) -> int:
    """
    Map speed_level to a gravity interval in milliseconds.
    speed_level = 1  -> slow  (1000 ms)
    speed_level = 10 -> fast  (~100 ms)
    """
    base_ms = 1000
    level = max(1, min(10, cfg.speed_level))
    interval = base_ms // level
    return max(80, interval)


# ---------- Drawing functions ----------

def draw_board(surface: pygame.Surface, state: GameState,
               board_offset: Tuple[int, int]) -> None:
    """Draw grid + locked cells + active piece."""
    ox, oy = board_offset
    w, h = state.config.width, state.config.height

    # Board background
    board_rect = pygame.Rect(ox, oy, w * CELL_SIZE, h * CELL_SIZE)
    pygame.draw.rect(surface, (20, 20, 50), board_rect)

    # Grid
    for x in range(w + 1):
        x_px = ox + x * CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (x_px, oy), (x_px, oy + h * CELL_SIZE))
    for y in range(h + 1):
        y_px = oy + y * CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (ox, y_px), (ox + w * CELL_SIZE, y_px))

    # Locked cells
    for (x, y), cell_id in state.board.cells.items():
        if 0 <= x < w and 0 <= y < h:
            draw_cell(surface, x, y, cell_id, board_offset)

    # Active piece
    if state.current_piece is not None:
        shape_color = state.current_piece.shape.color_id
        for (x, y) in state.current_piece.cells():
            if 0 <= x < w and 0 <= y < h:
                draw_cell(surface, x, y, shape_color, board_offset, outline=True)


def draw_cell(surface: pygame.Surface, x: int, y: int, cell_id: int,
              board_offset: Tuple[int, int], outline: bool = False) -> None:
    ox, oy = board_offset
    rect = pygame.Rect(
        ox + x * CELL_SIZE + 1,
        oy + y * CELL_SIZE + 1,
        CELL_SIZE - 2,
        CELL_SIZE - 2,
    )
    color = color_for_cell(cell_id)
    pygame.draw.rect(surface, color, rect)
    if outline:
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)


def draw_side_panel(surface: pygame.Surface, state: GameState,
                    panel_offset: Tuple[int, int], font: pygame.font.Font) -> None:
    px, py = panel_offset
    gravity_ms = gravity_interval_ms_from_config(state.config)
    rows_per_sec = 1000.0 / gravity_ms if gravity_ms > 0 else 0.0

    lines = [
        "4D Tetris – 2D mode",
        "",
        f"Score: {state.score}",
        f"Lines: {state.lines_cleared}",
        f"Speed level: {state.config.speed_level}",
        f"Fall: {rows_per_sec:.2f} rows/s",
        "",
        "Controls:",
        " ← / → : move",
        " ↑ / X : rot CW",
        " Z     : rot CCW",
        " ↓     : soft drop",
        " SPACE : hard drop",
        "",
        "Esc: quit",
        "R: restart",
    ]

    y = py
    for line in lines:
        surf = font.render(line, True, TEXT_COLOR)
        surface.blit(surf, (px, y))
        y += surf.get_height() + 4

    if state.game_over:
        y += 10
        surf = font.render("GAME OVER", True, (255, 80, 80))
        surface.blit(surf, (px, y))
        y += surf.get_height() + 4
        surf2 = font.render("Press R to restart", True, (255, 200, 200))
        surface.blit(surf2, (px, y))



@dataclass
class GameSettings:
    width: int = 10
    height: int = 20
    speed_level: int = 5  # 1..10, mapped to gravity interval


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
    settings: GameSettings = GameSettings()
    selected_index: int = 0  # 0=width, 1=height, 2=speed
    running: bool = True
    start_game: bool = False




# ---------- Menu (intro screen) ----------


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



def draw_menu(screen: pygame.Surface, state: MenuState, fonts: MenuFonts) -> None:
    draw_gradient_background(screen, (15, 15, 60), (2, 2, 20))
    width, height = screen.get_size()

    # Title + subtitle centered at top
    title_text = "4D Tetris – Setup"
    subtitle_text = "Use ↑/↓ to select, ←/→ to change, Enter to start, Esc to quit."

    title_surf = fonts.title_font.render(title_text, True, TEXT_COLOR)
    subtitle_surf = fonts.hint_font.render(subtitle_text, True, (200, 200, 220))

    title_x = (width - title_surf.get_width()) // 2
    screen.blit(title_surf, (title_x, 60))

    subtitle_x = (width - subtitle_surf.get_width()) // 2
    screen.blit(subtitle_surf, (subtitle_x, 60 + title_surf.get_height() + 10))

    # Settings panel (glass card)
    panel_w = int(width * 0.6)
    panel_h = 220
    panel_x = (width - panel_w) // 2
    panel_y = 160

    # Semi-transparent dark panel
    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (0, 0, 0, 140),
                     panel_surf.get_rect(), border_radius=16)
    screen.blit(panel_surf, (panel_x, panel_y))

    # Settings list inside panel
    labels = [
        f"Board width:   {state.settings.width}",
        f"Board height:  {state.settings.height}",
        f"Speed level:   {state.settings.speed_level}   (1 = slow, 10 = fast)",
    ]

    option_y = panel_y + 30
    option_x = panel_x + 40

    for i, text in enumerate(labels):
        is_selected = (i == state.selected_index)
        txt_color = TEXT_COLOR if not is_selected else HIGHLIGHT_COLOR

        text_surf = fonts.menu_font.render(text, True, txt_color)
        text_rect = text_surf.get_rect(topleft=(option_x, option_y))

        if is_selected:
            # Soft highlight bar behind selected option
            highlight_rect = text_rect.inflate(20, 10)
            highlight_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                highlight_surf,
                (255, 255, 255, 40),
                highlight_surf.get_rect(),
                border_radius=10,
            )
            screen.blit(highlight_surf, highlight_rect.topleft)

        screen.blit(text_surf, text_rect.topleft)
        option_y += text_surf.get_height() + 18

    # Bottom hint
    hint_lines = [
        "↑ / ↓  select option   |   ← / →  change value",
        "Enter  start game      |   Esc     quit",
    ]
    hint_y = panel_y + panel_h + 30
    for line in hint_lines:
        hint_surf = fonts.hint_font.render(line, True, (210, 210, 230))
        hint_x = (width - hint_surf.get_width()) // 2
        screen.blit(hint_surf, (hint_x, hint_y))
        hint_y += hint_surf.get_height() + 4



def run_menu(screen: pygame.Surface, base_font: pygame.font.Font) -> Optional[GameSettings]:
    """
    Intro screen where width, height, and speed_level can be set.
    Returns GameSettings if user starts the game, or None if user quits.
    """
    clock = pygame.time.Clock()
    fonts = init_menu_fonts()
    state = MenuState()

    while state.running and not state.start_game:
        _dt = clock.tick(60)
        actions = gather_menu_actions()
        apply_menu_actions(state, actions)
        draw_menu(screen, state, fonts)
        pygame.display.flip()

    if state.start_game and state.running:
        return state.settings
    return None


def run_menu_old(screen: pygame.Surface, font: pygame.font.Font) -> Optional[GameSettings]:
    """
    Simple intro screen where width, height, and speed_level can be set.
    Returns GameSettings if user starts the game, or None if user quits.
    """
    clock = pygame.time.Clock()
    settings = GameSettings()
    selected_idx = 0  # 0=width, 1=height, 2=speed

    running = True
    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None

                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    # Start game with current settings
                    return settings

                # Move selection
                if event.key == pygame.K_UP:
                    selected_idx = (selected_idx - 1) % 3
                elif event.key == pygame.K_DOWN:
                    selected_idx = (selected_idx + 1) % 3

                # Adjust values
                if event.key == pygame.K_LEFT:
                    if selected_idx == 0:
                        settings.width = max(6, settings.width - 1)
                    elif selected_idx == 1:
                        settings.height = max(12, settings.height - 1)
                    elif selected_idx == 2:
                        settings.speed_level = max(1, settings.speed_level - 1)
                elif event.key == pygame.K_RIGHT:
                    if selected_idx == 0:
                        settings.width = min(16, settings.width + 1)
                    elif selected_idx == 1:
                        settings.height = min(30, settings.height + 1)
                    elif selected_idx == 2:
                        settings.speed_level = min(10, settings.speed_level + 1)

        # Draw menu
        screen.fill(BG_COLOR)

        # Title
        title = "4D Tetris – Settings"
        subtitle = "Use ↑/↓ to select, ←/→ to change, Enter to start, Esc to quit."
        title_surf = font.render(title, True, TEXT_COLOR)
        subtitle_surf = font.render(subtitle, True, TEXT_COLOR)

        screen.blit(title_surf, (40, 40))
        screen.blit(subtitle_surf, (40, 40 + title_surf.get_height() + 10))

        # Settings list
        labels = [
            f"Board width:  {settings.width}",
            f"Board height: {settings.height}",
            f"Speed level:  {settings.speed_level}  (1=slow, 10=fast)",
        ]

        y = 120
        for i, text in enumerate(labels):
            color = HIGHLIGHT_COLOR if i == selected_idx else TEXT_COLOR
            surf = font.render(text, True, color)
            screen.blit(surf, (60, y))
            y += surf.get_height() + 8

        pygame.display.flip()

    return None


# ---------- Main game loop ----------

def create_initial_state(cfg: GameConfig) -> GameState:
    board = BoardND((cfg.width, cfg.height))
    return GameState(config=cfg, board=board)


def run():
    pygame.init()
    pygame.display.set_caption("4D Tetris")

    # First, create a window just for the menu
    menu_screen = pygame.display.set_mode((800, 600))

    try:
        font = pygame.font.SysFont("consolas", 18)
    except Exception:
        font = pygame.font.Font(None, 18)

    settings = run_menu(menu_screen, font)
    if settings is None:
        pygame.quit()
        sys.exit()

    # Now compute final game window size from chosen settings
    cfg = GameConfig(
        width=settings.width,
        height=settings.height,
        gravity_axis=1,
        speed_level=settings.speed_level,
    )

    board_px_w = cfg.width * CELL_SIZE
    board_px_h = cfg.height * CELL_SIZE

    window_w = board_px_w + SIDE_PANEL + 3 * MARGIN
    window_h = board_px_h + 2 * MARGIN

    screen = pygame.display.set_mode((window_w, window_h))
    pygame.display.set_caption("4D Tetris (2D prototype)")

    clock = pygame.time.Clock()

    # Reuse font from earlier
    board_offset = (MARGIN, MARGIN)
    panel_offset = (MARGIN + board_px_w + MARGIN, MARGIN)

    state = create_initial_state(cfg)
    gravity_interval_ms = gravity_interval_ms_from_config(cfg)
    gravity_accumulator = 0

    running = True
    while running:
        dt = clock.tick(60)  # limit to 60 FPS, dt in milliseconds
        gravity_accumulator += dt

        # ----- Events -----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_r:
                    # Restart game with same config
                    state = create_initial_state(cfg)
                    gravity_accumulator = 0
                    continue

                if state.game_over:
                    # Don’t react to other keys when game over
                    continue

                # Movement / rotation / drops
                if event.key == pygame.K_LEFT:
                    state.try_move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    state.try_move(1, 0)
                elif event.key == pygame.K_UP or event.key == pygame.K_x:
                    state.try_rotate(+1)
                elif event.key == pygame.K_z:
                    state.try_rotate(-1)
                elif event.key == pygame.K_SPACE:
                    state.hard_drop()
                elif event.key == pygame.K_DOWN:
                    # Soft drop: move one step down immediately
                    state.try_move(0, 1)

        # ----- Gravity tick -----
        if not state.game_over and gravity_accumulator >= gravity_interval_ms:
            gravity_accumulator = 0
            state.step(Action.NONE)  # just gravity

        # ----- Drawing -----
        screen.fill(BG_COLOR)
        draw_board(screen, state, board_offset)
        draw_side_panel(screen, state, panel_offset, font)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
