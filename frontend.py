# tetris_nd/frontend_pygame.py

import sys
from dataclasses import dataclass
from typing import Tuple, Optional

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


def color_for_cell(cell_id: int) -> Tuple[int, int, int]:
    if cell_id <= 0:
        return (0, 0, 0)
    return COLOR_MAP.get(cell_id, (200, 200, 200))


def gravity_interval_ms_from_config(cfg: GameConfig) -> int:
    """
    Map speed_level to a gravity interval in milliseconds.
    speed_level = 1  -> slow (1000 ms)
    speed_level = 10 -> fast (~100 ms)
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
    lines = [
        "4D Tetris – 2D mode",
        "",
        f"Score: {state.score}",
        f"Lines: {state.lines_cleared}",
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


# ---------- Main loop ----------

def create_initial_state() -> GameState:
    cfg = GameConfig(width=10, height=20)
    board = BoardND((cfg.width, cfg.height))
    return GameState(config=cfg, board=board)


def run():
    pygame.init()
    pygame.display.set_caption("4D Tetris (2D prototype)")

    cfg = GameConfig(width=10, height=20)
    board_px_w = cfg.width * CELL_SIZE
    board_px_h = cfg.height * CELL_SIZE

    window_w = board_px_w + SIDE_PANEL + 3 * MARGIN
    window_h = board_px_h + 2 * MARGIN

    screen = pygame.display.set_mode((window_w, window_h))
    clock = pygame.time.Clock()

    try:
        font = pygame.font.SysFont("consolas", 18)
    except Exception:
        font = pygame.font.Font(None, 18)

    board_offset = (MARGIN, MARGIN)
    panel_offset = (MARGIN + board_px_w + MARGIN, MARGIN)

    state = create_initial_state()

    # Gravity: one step every X milliseconds
    gravity_interval_ms = 500
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
                    # Restart game
                    state = create_initial_state()
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
            # Use the engine's step with Action.NONE = just gravity
            state.step(Action.NONE)

        # ----- Drawing -----
        screen.fill(BG_COLOR)
        draw_board(screen, state, board_offset)
        draw_side_panel(screen, state, panel_offset, font)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
