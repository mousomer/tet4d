# tetris_nd/gfx_pygame.py

from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

import pygame

from .font_profiles import GfxFonts, init_fonts as init_fonts_for_profile
from .game2d import GameState, GameConfig
from .gfx_panel_2d import draw_side_panel_2d
from .project_config import project_constant_int
from .speed_curve import gravity_interval_ms
from .topology import map_overlay_cells
from .ui_utils import draw_vertical_gradient, fit_text
from .view_modes import GridMode


# ---------- Visual config & colors ----------

CELL_SIZE = project_constant_int(("rendering", "2d", "cell_size"), 30, min_value=12, max_value=120)
MARGIN = project_constant_int(("rendering", "2d", "margin"), 20, min_value=0, max_value=240)
SIDE_PANEL = project_constant_int(("rendering", "2d", "side_panel"), 200, min_value=120, max_value=720)

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


@dataclass(frozen=True)
class ClearEffect2D:
    levels: Tuple[int, ...]
    progress: float  # 0.0 .. 1.0


ActiveOverlay2D = tuple[tuple[tuple[float, float], ...], int]


def init_fonts() -> GfxFonts:
    """Initialize fonts using the 2D profile."""
    return init_fonts_for_profile("2d")


# ---------- Misc helpers ----------

def draw_gradient_background(surface: pygame.Surface,
                             top_color: Tuple[int, int, int],
                             bottom_color: Tuple[int, int, int]) -> None:
    """Simple vertical gradient fill."""
    draw_vertical_gradient(surface, top_color, bottom_color)


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

def _draw_menu_header(
    screen: pygame.Surface,
    fonts: GfxFonts,
    bindings_file_hint: str | None,
    extra_hint_lines: Tuple[str, ...],
    bindings_status: str,
    bindings_status_error: bool,
) -> int:
    width, height = screen.get_size()
    title_surf = fonts.title_font.render("2D Tetris - Setup", True, TEXT_COLOR)
    subtitle_text = fit_text(
        fonts.hint_font,
        "Use Up/Down to select, Left/Right to change, Enter to start, Esc to quit.",
        width - 28,
    )
    subtitle_surf = fonts.hint_font.render(subtitle_text, True, (200, 200, 220))

    title_y = 46
    screen.blit(title_surf, ((width - title_surf.get_width()) // 2, title_y))
    subtitle_y = title_y + title_surf.get_height() + 8
    screen.blit(subtitle_surf, ((width - subtitle_surf.get_width()) // 2, subtitle_y))

    hint_lines = (
        (f"L = load keys, S = save keys ({bindings_file_hint})", *extra_hint_lines)
        if bindings_file_hint
        else extra_hint_lines
    )
    hint_y = subtitle_y + subtitle_surf.get_height() + 10
    line_h = fonts.hint_font.get_height() + 2
    max_hint_bottom = min(height // 2, hint_y + line_h * max(2, len(hint_lines) + 1))
    for line in hint_lines:
        if hint_y + line_h > max_hint_bottom:
            break
        hint_text = fit_text(fonts.hint_font, line, width - 28)
        hint_surf = fonts.hint_font.render(hint_text, True, (200, 200, 220))
        screen.blit(hint_surf, ((width - hint_surf.get_width()) // 2, hint_y))
        hint_y += hint_surf.get_height() + 2

    if bindings_status and hint_y + line_h <= max_hint_bottom:
        status_color = (255, 150, 150) if bindings_status_error else (170, 240, 170)
        status_text = fit_text(fonts.hint_font, bindings_status, width - 28)
        status_surf = fonts.hint_font.render(status_text, True, status_color)
        screen.blit(status_surf, ((width - status_surf.get_width()) // 2, hint_y + 2))
        hint_y += status_surf.get_height() + 4
    return hint_y


def _draw_menu_settings_panel(
    screen: pygame.Surface,
    fonts: GfxFonts,
    settings,
    selected_index: int,
    panel_top: int,
    menu_fields: Optional[Sequence[tuple[str, str, int, int]]] = None,
    value_formatter: Optional[Callable[[str, object], str]] = None,
) -> Tuple[int, int, int, int]:
    width, height = screen.get_size()
    panel_w = min(max(340, int(width * 0.6)), width - 24)
    if menu_fields:
        labels = []
        for label, attr_name, _min_val, _max_val in menu_fields:
            value = getattr(settings, attr_name)
            value_text = value_formatter(attr_name, value) if value_formatter else str(value)
            labels.append(f"{label}:  {value_text}")
    else:
        labels = [
            f"Board width:   {settings.width}",
            f"Board height:  {settings.height}",
            f"Speed level:   {settings.speed_level}   (1 = slow, 10 = fast)",
        ]

    panel_h_default = max(220, 86 + len(labels) * 44)
    panel_max_h = max(140, height - panel_top - 126)
    panel_h = min(panel_h_default, panel_max_h)
    panel_x = (width - panel_w) // 2
    panel_y = max(134, panel_top)
    panel_y = min(panel_y, max(60, height - panel_h - 126))

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (0, 0, 0, 140), panel_surf.get_rect(), border_radius=16)
    screen.blit(panel_surf, (panel_x, panel_y))

    option_y = panel_y + 24
    option_x = panel_x + 28
    option_w = panel_w - 56
    option_bottom = panel_y + panel_h - 16
    row_h_default = fonts.menu_font.get_height() + 18
    row_h = min(
        row_h_default,
        max(fonts.menu_font.get_height() + 8, (option_bottom - option_y) // max(1, len(labels))),
    )

    for i, text in enumerate(labels):
        if option_y + fonts.menu_font.get_height() > option_bottom:
            break
        is_selected = i == selected_index
        txt_color = TEXT_COLOR if not is_selected else HIGHLIGHT_COLOR
        text_fit = fit_text(fonts.menu_font, text, option_w - 8)
        text_surf = fonts.menu_font.render(text_fit, True, txt_color)
        text_rect = text_surf.get_rect(topleft=(option_x, option_y))

        if is_selected:
            highlight_rect = pygame.Rect(option_x - 8, option_y - 4, option_w + 16, text_rect.height + 10)
            highlight_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(highlight_surf, (255, 255, 255, 40), highlight_surf.get_rect(), border_radius=10)
            screen.blit(highlight_surf, highlight_rect.topleft)

        screen.blit(text_surf, text_rect.topleft)
        option_y += row_h

    return panel_x, panel_y, panel_w, panel_h


def _draw_menu_dpad_and_commands(
    screen: pygame.Surface,
    fonts: GfxFonts,
    panel_y: int,
    panel_h: int,
) -> None:
    width, height = screen.get_size()
    dpad_center_y = panel_y + panel_h + 56
    dpad_center_x = width // 2
    dpad_offset = 50
    button_size = (36, 36)

    full_block_bottom = dpad_center_y + dpad_offset + 50 + 32 + fonts.hint_font.get_height() + 8
    if full_block_bottom > height - 6:
        compact_text = fit_text(
            fonts.hint_font,
            "Arrows navigate   Enter start   Esc quit",
            width - 24,
        )
        compact_surf = fonts.hint_font.render(compact_text, True, (200, 200, 220))
        y = max(panel_y + panel_h + 8, height - compact_surf.get_height() - 8)
        screen.blit(compact_surf, ((width - compact_surf.get_width()) // 2, y))
        return

    up_color = (80, 140, 255)
    down_color = (80, 200, 140)
    side_color = (255, 190, 80)
    border = (240, 240, 255)
    draw_button_with_arrow(screen, (dpad_center_x, dpad_center_y - dpad_offset), button_size, "up", "Up", fonts.hint_font, up_color, border)
    draw_button_with_arrow(screen, (dpad_center_x, dpad_center_y + dpad_offset), button_size, "down", "Down", fonts.hint_font, down_color, border)
    draw_button_with_arrow(screen, (dpad_center_x - dpad_offset, dpad_center_y), button_size, "left", "Left", fonts.hint_font, side_color, border)
    draw_button_with_arrow(screen, (dpad_center_x + dpad_offset, dpad_center_y), button_size, "right", "Right", fonts.hint_font, side_color, border)

    cmd_y = dpad_center_y + dpad_offset + 50
    cmd_spacing = 140
    cmd_size = (100, 32)
    cmd_color = (100, 100, 160)
    cmd_border = (230, 230, 255)
    draw_button_with_arrow(screen, (dpad_center_x - cmd_spacing // 2, cmd_y), cmd_size, None, "Enter = Start", fonts.hint_font, cmd_color, cmd_border)
    draw_button_with_arrow(screen, (dpad_center_x + cmd_spacing // 2, cmd_y), cmd_size, None, "Esc = Quit", fonts.hint_font, cmd_color, cmd_border)


def draw_menu(
    screen: pygame.Surface,
    fonts: GfxFonts,
    settings,
    selected_index: int,
    bindings_file_hint: str | None = "keybindings/2d.json",
    extra_hint_lines: Tuple[str, ...] = (),
    bindings_status: str = "",
    bindings_status_error: bool = False,
    menu_fields: Optional[Sequence[tuple[str, str, int, int]]] = None,
    value_formatter: Optional[Callable[[str, object], str]] = None,
) -> None:
    draw_gradient_background(screen, (15, 15, 60), (2, 2, 20))
    header_bottom = _draw_menu_header(screen, fonts, bindings_file_hint, extra_hint_lines, bindings_status, bindings_status_error)
    _panel_x, panel_y, _panel_w, panel_h = _draw_menu_settings_panel(
        screen,
        fonts,
        settings,
        selected_index,
        panel_top=header_bottom + 12,
        menu_fields=menu_fields,
        value_formatter=value_formatter,
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


def _draw_board_edges_only(surface: pygame.Surface, board_rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, (86, 104, 146), board_rect, 2)


def _helper_grid_marks_2d(state: GameState, width: int, height: int) -> tuple[set[int], set[int]]:
    x_marks: set[int] = set()
    y_marks: set[int] = set()
    for x, y in state.current_piece_cells_mapped(include_above=False):
        if 0 <= x < width and 0 <= y < height:
            x_marks.add(x)
            x_marks.add(x + 1)
            y_marks.add(y)
            y_marks.add(y + 1)
    return x_marks, y_marks


def _draw_helper_grid(surface: pygame.Surface,
                      board_rect: pygame.Rect,
                      width_cells: int,
                      height_cells: int,
                      x_marks: set[int],
                      y_marks: set[int]) -> None:
    for x in sorted(x_marks):
        if not (0 <= x <= width_cells):
            continue
        x_px = board_rect.x + x * CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (x_px, board_rect.y), (x_px, board_rect.bottom))
    for y in sorted(y_marks):
        if not (0 <= y <= height_cells):
            continue
        y_px = board_rect.y + y * CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (board_rect.x, y_px), (board_rect.right, y_px))


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


def _draw_full_grid(surface: pygame.Surface, ox: int, oy: int, width_cells: int, height_cells: int) -> None:
    for x in range(width_cells + 1):
        x_px = ox + x * CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (x_px, oy), (x_px, oy + height_cells * CELL_SIZE))
    for y in range(height_cells + 1):
        y_px = oy + y * CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (ox, y_px), (ox + width_cells * CELL_SIZE, y_px))


def _draw_grid_variant(surface: pygame.Surface,
                       board_rect: pygame.Rect,
                       state: GameState,
                       ox: int,
                       oy: int,
                       width_cells: int,
                       height_cells: int,
                       grid_mode: GridMode) -> None:
    if grid_mode in (GridMode.OFF, GridMode.SHADOW, GridMode.HELPER):
        _draw_board_shadow(surface, board_rect)
    elif grid_mode == GridMode.EDGE:
        _draw_board_edges_only(surface, board_rect)

    if grid_mode == GridMode.FULL:
        _draw_full_grid(surface, ox, oy, width_cells, height_cells)
    elif grid_mode == GridMode.HELPER:
        x_marks, y_marks = _helper_grid_marks_2d(state, width_cells, height_cells)
        _draw_helper_grid(surface, board_rect, width_cells, height_cells, x_marks, y_marks)


def _draw_locked_cells(surface: pygame.Surface,
                       state: GameState,
                       board_offset: tuple[int, int],
                       width_cells: int,
                       height_cells: int,
                       *,
                       outline: bool) -> None:
    for (x, y), cell_id in state.board.cells.items():
        if 0 <= x < width_cells and 0 <= y < height_cells:
            _draw_cell(surface, x, y, cell_id, board_offset, outline=outline)


def _draw_cell_float(surface: pygame.Surface,
                     x: float,
                     y: float,
                     cell_id: int,
                     board_offset: tuple[int, int],
                     *,
                     outline: bool) -> None:
    ox, oy = board_offset
    rect = pygame.Rect(
        round(ox + x * CELL_SIZE + 1),
        round(oy + y * CELL_SIZE + 1),
        CELL_SIZE - 2,
        CELL_SIZE - 2,
    )
    color = color_for_cell(cell_id)
    pygame.draw.rect(surface, color, rect)
    if outline:
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)


def _draw_active_piece_cells(surface: pygame.Surface,
                             state: GameState,
                             board_offset: tuple[int, int],
                             width_cells: int,
                             height_cells: int,
                             *,
                             overlay: ActiveOverlay2D | None) -> None:
    if overlay is not None:
        raw_cells, color_id = overlay
        mapped_overlay = map_overlay_cells(
            state.topology_policy,
            raw_cells,
            allow_above_gravity=False,
        )
        for x, y in mapped_overlay:
            if 0.0 <= x < width_cells and 0.0 <= y < height_cells:
                _draw_cell_float(
                    surface,
                    x,
                    y,
                    color_id,
                    board_offset,
                    outline=True,
                )
        return

    if state.current_piece is None:
        return
    shape_color = state.current_piece.shape.color_id
    for x, y in state.current_piece_cells_mapped(include_above=False):
        if 0 <= x < width_cells and 0 <= y < height_cells:
            _draw_cell(surface, x, y, shape_color, board_offset, outline=True)


def draw_board(surface: pygame.Surface, state: GameState,
               board_offset: Tuple[int, int],
               grid_mode: GridMode = GridMode.FULL,
               clear_effect: Optional[ClearEffect2D] = None,
               active_piece_overlay: ActiveOverlay2D | None = None) -> None:
    """Draw grid + locked cells + active piece."""
    ox, oy = board_offset
    w, h = state.config.width, state.config.height

    # Board background
    board_rect = pygame.Rect(ox, oy, w * CELL_SIZE, h * CELL_SIZE)
    pygame.draw.rect(surface, (20, 20, 50), board_rect)
    _draw_grid_variant(surface, board_rect, state, ox, oy, w, h, grid_mode)
    _draw_locked_cells(
        surface,
        state,
        board_offset,
        w,
        h,
        outline=(grid_mode == GridMode.EDGE),
    )
    _draw_active_piece_cells(
        surface,
        state,
        board_offset,
        w,
        h,
        overlay=active_piece_overlay,
    )

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


def draw_side_panel(surface: pygame.Surface,
                    state: GameState,
                    panel_offset: Tuple[int, int],
                    fonts: GfxFonts,
                    grid_mode: GridMode = GridMode.FULL,
                    bot_lines: Sequence[str] = ()) -> None:
    draw_side_panel_2d(
        surface,
        state,
        panel_offset,
        fonts,
        grid_mode=grid_mode,
        bot_lines=bot_lines,
        side_panel_width=SIDE_PANEL,
        text_color=TEXT_COLOR,
        gravity_interval_from_config=gravity_interval_ms_from_config,
    )


def gravity_interval_ms_from_config(cfg: GameConfig) -> int:
    return gravity_interval_ms(cfg.speed_level, dimension=2)


def draw_game_frame(screen: pygame.Surface,
                    cfg: GameConfig,
                    state: GameState,
                    fonts: GfxFonts,
                    grid_mode: GridMode = GridMode.FULL,
                    bot_lines: Sequence[str] = (),
                    clear_effect: Optional[ClearEffect2D] = None,
                    active_piece_overlay: ActiveOverlay2D | None = None) -> None:
    """Single call to draw the whole game frame."""
    screen.fill(BG_COLOR)
    board_offset, panel_offset = compute_game_layout(screen, cfg)
    draw_board(
        screen,
        state,
        board_offset,
        grid_mode=grid_mode,
        clear_effect=clear_effect,
        active_piece_overlay=active_piece_overlay,
    )
    draw_side_panel(screen, state, panel_offset, fonts, grid_mode=grid_mode, bot_lines=bot_lines)
