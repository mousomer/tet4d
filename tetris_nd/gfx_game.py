# tetris_nd/gfx_pygame.py

from dataclasses import dataclass
from typing import Tuple, Optional

import pygame

from .game2d import GameState, GameConfig
from .keybindings import CONTROL_LINES_2D


# ---------- Visual config & colors ----------

CELL_SIZE = 30          # pixels per board cell
MARGIN = 20             # outer margin for board
SIDE_PANEL = 200        # width for score / text / d-pad

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


# ---------- Fonts container ----------

@dataclass
class GfxFonts:
    title_font: pygame.font.Font
    menu_font: pygame.font.Font
    hint_font: pygame.font.Font
    panel_font: pygame.font.Font


@dataclass(frozen=True)
class ClearEffect2D:
    levels: Tuple[int, ...]
    progress: float  # 0.0 .. 1.0


def init_fonts() -> GfxFonts:
    """Initialize a set of fonts, with fallbacks."""
    try:
        title_font = pygame.font.SysFont("consolas", 36, bold=True)
        menu_font = pygame.font.SysFont("consolas", 24)
        hint_font = pygame.font.SysFont("consolas", 18)
        panel_font = pygame.font.SysFont("consolas", 18)
    except (pygame.error, OSError):
        title_font = pygame.font.Font(None, 36)
        menu_font = pygame.font.Font(None, 24)
        hint_font = pygame.font.Font(None, 18)
        panel_font = pygame.font.Font(None, 18)
    return GfxFonts(title_font, menu_font, hint_font, panel_font)


# ---------- Misc helpers ----------

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


def draw_button_with_arrow(
    surface: pygame.Surface,
    center: Tuple[int, int],
    size: Tuple[int, int],
    direction: Optional[str],   # 'up', 'down', 'left', 'right', or None
    label: str,
    font: pygame.font.Font,
    bg_color: Tuple[int, int, int],
    border_color: Tuple[int, int, int],
) -> None:
    """
    Draw a rounded rectangular button with an optional arrow icon and a text label.
    Arrow is drawn as a white triangle; label is below the button.
    """
    w, h = size
    rect = pygame.Rect(0, 0, w, h)
    rect.center = center

    # Button background
    button_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(
        button_surf, (*bg_color, 200), button_surf.get_rect(), border_radius=10
    )
    pygame.draw.rect(
        button_surf, border_color, button_surf.get_rect(), width=2, border_radius=10
    )
    surface.blit(button_surf, rect.topleft)

    # Arrow icon
    if direction is not None:
        pad = min(w, h) // 4
        cx, cy = rect.center
        if direction == "up":
            points = [
                (cx, rect.top + pad),
                (rect.left + pad, rect.bottom - pad),
                (rect.right - pad, rect.bottom - pad),
            ]
        elif direction == "down":
            points = [
                (cx, rect.bottom - pad),
                (rect.left + pad, rect.top + pad),
                (rect.right - pad, rect.top + pad),
            ]
        elif direction == "left":
            points = [
                (rect.left + pad, cy),
                (rect.right - pad, rect.top + pad),
                (rect.right - pad, rect.bottom - pad),
            ]
        elif direction == "right":
            points = [
                (rect.right - pad, cy),
                (rect.left + pad, rect.top + pad),
                (rect.left + pad, rect.bottom - pad),
            ]
        else:
            points = []
        if points:
            pygame.draw.polygon(surface, (255, 255, 255), points)

    # Label under the button
    if label:
        text_surf = font.render(label, True, (230, 230, 230))
        text_rect = text_surf.get_rect()
        text_rect.centerx = rect.centerx
        text_rect.top = rect.bottom + 4
        surface.blit(text_surf, text_rect)


# ---------- Menu drawing ----------

def _draw_menu_header(screen: pygame.Surface,
                      fonts: GfxFonts,
                      bindings_file_hint: str,
                      extra_hint_lines: Tuple[str, ...],
                      bindings_status: str,
                      bindings_status_error: bool) -> int:
    width, _ = screen.get_size()
    title_text = "2D Tetris – Setup"
    subtitle_text = "Use Up/Down to select, Left/Right to change, Enter to start, Esc to quit."
    bindings_hint_text = f"L = load keys, S = save keys ({bindings_file_hint})"

    title_surf = fonts.title_font.render(title_text, True, TEXT_COLOR)
    subtitle_surf = fonts.hint_font.render(subtitle_text, True, (200, 200, 220))

    title_x = (width - title_surf.get_width()) // 2
    screen.blit(title_surf, (title_x, 60))

    subtitle_x = (width - subtitle_surf.get_width()) // 2
    screen.blit(subtitle_surf, (subtitle_x, 60 + title_surf.get_height() + 10))

    hint_y = 60 + title_surf.get_height() + 34
    for line in (bindings_hint_text, *extra_hint_lines):
        hint_surf = fonts.hint_font.render(line, True, (200, 200, 220))
        hint_x = (width - hint_surf.get_width()) // 2
        screen.blit(hint_surf, (hint_x, hint_y))
        hint_y += hint_surf.get_height() + 2

    if bindings_status:
        status_color = (255, 150, 150) if bindings_status_error else (170, 240, 170)
        status_surf = fonts.hint_font.render(bindings_status, True, status_color)
        status_x = (width - status_surf.get_width()) // 2
        screen.blit(status_surf, (status_x, hint_y + 2))
        hint_y += status_surf.get_height() + 4
    return hint_y


def _draw_menu_settings_panel(screen: pygame.Surface,
                              fonts: GfxFonts,
                              settings,
                              selected_index: int,
                              panel_top: int) -> Tuple[int, int, int, int]:
    """
    Draw the glass panel with width/height/speed settings.
    Returns (panel_x, panel_y, panel_w, panel_h).
    """
    width, height = screen.get_size()
    panel_w = int(width * 0.6)
    panel_h = 220
    panel_x = (width - panel_w) // 2
    panel_y = max(160, panel_top)
    max_panel_y = max(160, height - 430)
    panel_y = min(panel_y, max_panel_y)

    # Semi-transparent dark panel
    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (0, 0, 0, 140),
                     panel_surf.get_rect(), border_radius=16)
    screen.blit(panel_surf, (panel_x, panel_y))

    # Settings list inside panel
    labels = [
        f"Board width:   {settings.width}",
        f"Board height:  {settings.height}",
        f"Speed level:   {settings.speed_level}   (1 = slow, 10 = fast)",
    ]

    option_y = panel_y + 30
    option_x = panel_x + 40

    for i, text in enumerate(labels):
        is_selected = (i == selected_index)
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

    return panel_x, panel_y, panel_w, panel_h


def _draw_menu_dpad_and_commands(screen: pygame.Surface,
                                 fonts: GfxFonts,
                                 panel_y: int,
                                 panel_h: int) -> None:
    """Draw small D-pad and Enter/Esc buttons under the settings panel."""
    width, _ = screen.get_size()

    # D-pad
    dpad_center_y = panel_y + panel_h + 60
    dpad_center_x = width // 2
    dpad_offset = 50
    button_size = (36, 36)

    up_color = (80, 140, 255)
    down_color = (80, 200, 140)
    side_color = (255, 190, 80)
    border = (240, 240, 255)

    draw_button_with_arrow(
        screen,
        (dpad_center_x, dpad_center_y - dpad_offset),
        button_size,
        "up",
        "Up",
        fonts.hint_font,
        up_color,
        border,
    )
    draw_button_with_arrow(
        screen,
        (dpad_center_x, dpad_center_y + dpad_offset),
        button_size,
        "down",
        "Down",
        fonts.hint_font,
        down_color,
        border,
    )
    draw_button_with_arrow(
        screen,
        (dpad_center_x - dpad_offset, dpad_center_y),
        button_size,
        "left",
        "Left",
        fonts.hint_font,
        side_color,
        border,
    )
    draw_button_with_arrow(
        screen,
        (dpad_center_x + dpad_offset, dpad_center_y),
        button_size,
        "right",
        "Right",
        fonts.hint_font,
        side_color,
        border,
    )

    # Enter / Esc buttons
    cmd_y = dpad_center_y + dpad_offset + 50
    cmd_spacing = 140
    cmd_size = (100, 32)
    cmd_color = (100, 100, 160)
    cmd_border = (230, 230, 255)

    draw_button_with_arrow(
        screen,
        (dpad_center_x - cmd_spacing // 2, cmd_y),
        cmd_size,
        None,
        "Enter = Start",
        fonts.hint_font,
        cmd_color,
        cmd_border,
    )
    draw_button_with_arrow(
        screen,
        (dpad_center_x + cmd_spacing // 2, cmd_y),
        cmd_size,
        None,
        "Esc = Quit",
        fonts.hint_font,
        cmd_color,
        cmd_border,
    )


def draw_menu(screen: pygame.Surface,
              fonts: GfxFonts,
              settings,
              selected_index: int,
              bindings_file_hint: str = "keybindings/2d.json",
              extra_hint_lines: Tuple[str, ...] = (),
              bindings_status: str = "",
              bindings_status_error: bool = False) -> None:
    """Top-level menu draw call."""
    draw_gradient_background(screen, (15, 15, 60), (2, 2, 20))
    header_bottom = _draw_menu_header(
        screen,
        fonts,
        bindings_file_hint,
        extra_hint_lines,
        bindings_status,
        bindings_status_error,
    )
    _panel_x, panel_y, _panel_w, panel_h = _draw_menu_settings_panel(
        screen,
        fonts,
        settings,
        selected_index,
        panel_top=header_bottom + 12,
    )
    _draw_menu_dpad_and_commands(screen, fonts, panel_y, panel_h)


# ---------- Game drawing ----------

def compute_game_layout(screen: pygame.Surface,
                        cfg: GameConfig) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Compute offsets for board and side panel based on current window size.
    Returns (board_offset, panel_offset).
    """
    window_w, window_h = screen.get_size()
    board_px_w = cfg.width * CELL_SIZE
    board_px_h = cfg.height * CELL_SIZE

    board_x = max(MARGIN, (window_w - SIDE_PANEL - board_px_w) // 2)
    board_y = max(MARGIN, (window_h - board_px_h) // 2)
    board_offset = (board_x, board_y)
    panel_offset = (board_x + board_px_w + MARGIN, board_y)
    return board_offset, panel_offset


def _draw_board_shadow(surface: pygame.Surface, board_rect: pygame.Rect) -> None:
    """
    Draw a subtle board silhouette when grid lines are hidden.
    """
    shadow = pygame.Surface(board_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow, (16, 24, 52, 170), shadow.get_rect())

    step = max(6, CELL_SIZE)
    for y in range(0, board_rect.height, step):
        alpha = 20 if (y // step) % 2 == 0 else 10
        pygame.draw.line(shadow, (130, 150, 190, alpha), (0, y), (board_rect.width, y), 1)

    for x in range(0, board_rect.width, step * 2):
        pygame.draw.line(
            shadow,
            (170, 190, 220, 16),
            (x, 0),
            (min(board_rect.width, x + board_rect.height), board_rect.height),
            1,
        )

    surface.blit(shadow, board_rect.topleft)
    pygame.draw.rect(surface, (86, 104, 146), board_rect, 2)


def _draw_clear_effect(surface: pygame.Surface,
                       board_rect: pygame.Rect,
                       width_cells: int,
                       clear_effect: Optional[ClearEffect2D]) -> None:
    if clear_effect is None or not clear_effect.levels:
        return

    progress = max(0.0, min(1.0, clear_effect.progress))
    fade = 1.0 - progress
    base_alpha = int(170 * fade)
    if base_alpha <= 0:
        return

    row_width = width_cells * CELL_SIZE
    for level in clear_effect.levels:
        row_top = board_rect.y + level * CELL_SIZE
        row_rect = pygame.Rect(board_rect.x, row_top, row_width, CELL_SIZE)

        overlay = pygame.Surface(row_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(overlay, (255, 245, 210, base_alpha), overlay.get_rect())

        sweep_center = int(progress * row_rect.width)
        sweep_rect = pygame.Rect(max(0, sweep_center - 24), 0, 48, row_rect.height)
        pygame.draw.rect(overlay, (120, 220, 255, min(255, base_alpha + 45)), sweep_rect)
        pygame.draw.rect(overlay, (255, 255, 255, min(255, base_alpha + 55)), overlay.get_rect(), 2)

        surface.blit(overlay, row_rect.topleft)


def draw_board(surface: pygame.Surface, state: GameState,
               board_offset: Tuple[int, int],
               show_grid: bool = True,
               clear_effect: Optional[ClearEffect2D] = None) -> None:
    """Draw grid + locked cells + active piece."""
    ox, oy = board_offset
    w, h = state.config.width, state.config.height

    # Board background
    board_rect = pygame.Rect(ox, oy, w * CELL_SIZE, h * CELL_SIZE)
    pygame.draw.rect(surface, (20, 20, 50), board_rect)
    if not show_grid:
        _draw_board_shadow(surface, board_rect)

    # Grid
    if show_grid:
        for x in range(w + 1):
            x_px = ox + x * CELL_SIZE
            pygame.draw.line(surface, GRID_COLOR, (x_px, oy), (x_px, oy + h * CELL_SIZE))
        for y in range(h + 1):
            y_px = oy + y * CELL_SIZE
            pygame.draw.line(surface, GRID_COLOR, (ox, y_px), (ox + w * CELL_SIZE, y_px))

    # Locked cells
    for (x, y), cell_id in state.board.cells.items():
        if 0 <= x < w and 0 <= y < h:
            _draw_cell(surface, x, y, cell_id, board_offset)

    # Active piece
    if state.current_piece is not None:
        shape_color = state.current_piece.shape.color_id
        for (x, y) in state.current_piece.cells():
            if 0 <= x < w and 0 <= y < h:
                _draw_cell(surface, x, y, shape_color, board_offset, outline=True)

    _draw_clear_effect(surface, board_rect, w, clear_effect)


def _draw_cell(surface: pygame.Surface, x: int, y: int, cell_id: int,
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


def _draw_side_panel_text(surface: pygame.Surface,
                          state: GameState,
                          panel_offset: Tuple[int, int],
                          fonts: GfxFonts,
                          show_grid: bool) -> int:
    """Draw the textual part of the side panel. Returns the current y after text."""
    px, py = panel_offset
    gravity_ms = gravity_interval_ms_from_config(state.config)
    rows_per_sec = 1000.0 / gravity_ms if gravity_ms > 0 else 0.0

    lines = [
        "2D Tetris",
        "",
        f"Score: {state.score}",
        f"Lines: {state.lines_cleared}",
        f"Speed level: {state.config.speed_level}",
        f"Fall: {rows_per_sec:.2f} rows/s",
        f"Grid: {'ON' if show_grid else 'OFF'}",
        "",
        *CONTROL_LINES_2D,
    ]

    y = py
    for line in lines:
        surf = fonts.panel_font.render(line, True, TEXT_COLOR)
        surface.blit(surf, (px, y))
        y += surf.get_height() + 4
    return y


def _draw_side_panel_dpad(surface: pygame.Surface,
                          start_y: int,
                          panel_offset: Tuple[int, int],
                          fonts: GfxFonts) -> int:
    """Draw a mini D-pad inside the side panel. Returns new y."""
    px, _ = panel_offset
    dpad_center_x = px + SIDE_PANEL // 2
    dpad_center_y = start_y + 35
    g_button_size = (24, 24)
    g_offset = 26

    pad_bg = (60, 90, 150)
    pad_border = (230, 230, 255)

    draw_button_with_arrow(
        surface,
        (dpad_center_x, dpad_center_y - g_offset),
        g_button_size,
        "up",
        "",
        fonts.hint_font,
        pad_bg,
        pad_border,
    )
    draw_button_with_arrow(
        surface,
        (dpad_center_x, dpad_center_y + g_offset),
        g_button_size,
        "down",
        "",
        fonts.hint_font,
        pad_bg,
        pad_border,
    )
    draw_button_with_arrow(
        surface,
        (dpad_center_x - g_offset, dpad_center_y),
        g_button_size,
        "left",
        "",
        fonts.hint_font,
        pad_bg,
        pad_border,
    )
    draw_button_with_arrow(
        surface,
        (dpad_center_x + g_offset, dpad_center_y),
        g_button_size,
        "right",
        "",
        fonts.hint_font,
        pad_bg,
        pad_border,
    )

    return dpad_center_y + g_offset + 20


def draw_side_panel(surface: pygame.Surface,
                    state: GameState,
                    panel_offset: Tuple[int, int],
                    fonts: GfxFonts,
                    show_grid: bool = True) -> None:
    """Top-level side panel draw."""
    y_after_text = _draw_side_panel_text(surface, state, panel_offset, fonts, show_grid)
    y_after_dpad = _draw_side_panel_dpad(surface, y_after_text, panel_offset, fonts)

    # Game over message below D-pad (if needed)
    if state.game_over:
        px, _ = panel_offset
        y = y_after_dpad + 10
        surf = fonts.panel_font.render("GAME OVER", True, (255, 80, 80))
        surface.blit(surf, (px, y))
        y += surf.get_height() + 4
        surf2 = fonts.panel_font.render("Press R to restart", True, (255, 200, 200))
        surface.blit(surf2, (px, y))


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


def draw_game_frame(screen: pygame.Surface,
                    cfg: GameConfig,
                    state: GameState,
                    fonts: GfxFonts,
                    show_grid: bool = True,
                    clear_effect: Optional[ClearEffect2D] = None) -> None:
    """Single call to draw the whole game frame."""
    screen.fill(BG_COLOR)
    board_offset, panel_offset = compute_game_layout(screen, cfg)
    draw_board(
        screen,
        state,
        board_offset,
        show_grid=show_grid,
        clear_effect=clear_effect,
    )
    draw_side_panel(screen, state, panel_offset, fonts, show_grid=show_grid)
