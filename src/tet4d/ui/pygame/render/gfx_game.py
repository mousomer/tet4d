import math
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

import pygame

from tet4d.engine.gameplay.api import (
    gravity_interval_ms_gameplay,
    map_overlay_cells_gameplay,
)
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.rotation_anim import RigidPieceOverlay2D
from tet4d.engine.runtime.menu_config import ui_copy_section
from tet4d.engine.runtime.menu_field_spec import FieldSpec
from tet4d.engine.runtime.project_config import project_constant_int
from tet4d.engine.ui_logic.view_modes import GridMode, ShadowMode
from tet4d.ui.pygame.endgame_animation import (
    EndgameAnimationState,
    rotate_point,
    transform_grid_break_mark,
    transform_shell_artifact,
    transform_shell_geometry,
)
from tet4d.ui.pygame.render.font_profiles import (
    GfxFonts,
    init_fonts as init_fonts_for_profile,
)
from tet4d.ui.pygame.render.active_piece_projection_guides import (
    GuideCell2D,
    build_boundary_projection_segments_2d,
    draw_boundary_projection_segments_2d,
    projection_guide_enabled,
)
from tet4d.ui.pygame.render.gfx_panel_2d import draw_side_panel_2d
from tet4d.ui.pygame.render.panel_utils import draw_game_over_banner
from tet4d.ui.pygame.ui_utils import (
    compute_slider_row_layout,
    draw_corner_chip,
    draw_tron_menu_background,
    draw_tron_panel,
    draw_value_slider,
    draw_wrapped_label_value_lines,
    format_menu_title,
    fit_text,
    menu_slider_row_min_total_width,
    standard_menu_panel_rect,
    wrapped_label_value_layout,
)

_SETUP_MENU_COPY = ui_copy_section("setup_menu")


# ---------- Visual config & colors ----------

CELL_SIZE = project_constant_int(
    ("rendering", "2d", "cell_size"), 30, min_value=12, max_value=120
)
MARGIN = project_constant_int(
    ("rendering", "2d", "margin"), 20, min_value=0, max_value=240
)
SIDE_PANEL = project_constant_int(
    ("rendering", "2d", "side_panel"), 360, min_value=120, max_value=720
)

BG_COLOR = (10, 10, 30)
GRID_COLOR = (40, 40, 80)
TEXT_COLOR = (230, 230, 230)
HIGHLIGHT_COLOR = (255, 215, 0)

# Tetromino-ish colors for IDs 1..7
COLOR_MAP = {
    1: (0, 255, 255),  # I - cyan
    2: (255, 255, 0),  # O - yellow
    3: (160, 0, 240),  # T - purple
    4: (0, 255, 0),  # S - green
    5: (255, 0, 0),  # Z - red
    6: (0, 0, 255),  # J - blue
    7: (255, 165, 0),  # L - orange
}


def color_for_cell(cell_id: int) -> Tuple[int, int, int]:
    if cell_id <= 0:
        return (0, 0, 0)
    return COLOR_MAP.get(cell_id, (200, 200, 200))


@dataclass(frozen=True)
class ClearEffect2D:
    levels: Tuple[int, ...]
    progress: float  # 0.0 .. 1.0


ActiveOverlay2D = tuple[tuple[tuple[float, float], ...], int] | RigidPieceOverlay2D


def init_fonts() -> GfxFonts:
    """Initialize fonts using the 2D profile."""
    return init_fonts_for_profile("2d")


# ---------- Misc helpers ----------


def draw_gradient_background(
    surface: pygame.Surface,
    top_color: Tuple[int, int, int],
    bottom_color: Tuple[int, int, int],
) -> None:
    """Simple vertical gradient fill."""
    draw_tron_menu_background(surface, top_color=top_color, bottom_color=bottom_color)


def draw_button_with_arrow(
    surface: pygame.Surface,
    center: Tuple[int, int],
    size: Tuple[int, int],
    direction: Optional[str],  # 'up', 'down', 'left', 'right', or None
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
    title_surf = fonts.title_font.render(
        format_menu_title(_SETUP_MENU_COPY["title_2d"]), True, TEXT_COLOR
    )

    title_y = 46
    screen.blit(title_surf, ((width - title_surf.get_width()) // 2, title_y))
    draw_corner_chip(screen, font=fonts.hint_font, text="Back", x=18, y=18)

    hint_lines = (
        (
            _SETUP_MENU_COPY["bindings_hint_template"].format(
                bindings_file_hint=bindings_file_hint
            ),
            *extra_hint_lines,
        )
        if bindings_file_hint
        else extra_hint_lines
    )
    hint_y = title_y + title_surf.get_height() + 18
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


def _menu_row_height(
    font: pygame.font.Font,
    *,
    field: FieldSpec,
    value_text: str,
    total_width: int,
) -> int:
    if field.uses_slider():
        return compute_slider_row_layout(
            font,
            label=field.label,
            value=value_text,
            total_width=total_width,
        ).row_height
    return wrapped_label_value_layout(
        font,
        label=field.label,
        value=value_text,
        total_width=total_width,
    )[2]


def _draw_menu_setting_row(
    screen: pygame.Surface,
    *,
    font: pygame.font.Font,
    option_x: int,
    option_w: int,
    option_y: int,
    field: FieldSpec,
    value_text: str,
    raw_value: object,
    is_selected: bool,
    flash_frames: int,
    min_row_height: int,
) -> int:
    txt_color = TEXT_COLOR if not is_selected else HIGHLIGHT_COLOR
    slider_layout = (
        compute_slider_row_layout(
            font,
            label=field.label,
            value=value_text,
            total_width=option_w,
        )
        if field.uses_slider()
        else None
    )
    if slider_layout is None:
        label_lines, value_lines, row_height = wrapped_label_value_layout(
            font,
            label=field.label,
            value=value_text,
            total_width=option_w,
        )
    else:
        label_lines = slider_layout.label_lines
        value_lines = slider_layout.value_lines
        row_height = slider_layout.row_height
    row_height = max(int(min_row_height), row_height)
    if slider_layout is None:
        text_top_y = option_y
        value_right = option_x + option_w
    else:
        text_top_y = option_y + slider_layout.text_top_padding
        value_right = (
            option_x
            + slider_layout.label_width
            + slider_layout.text_gap
            + slider_layout.value_width
        )

    if is_selected:
        highlight_rect = pygame.Rect(
            option_x - 8, option_y - 4, option_w + 16, row_height
        )
        highlight_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            highlight_surf,
            (255, 255, 255, 40),
            highlight_surf.get_rect(),
            border_radius=10,
        )
        screen.blit(highlight_surf, highlight_rect.topleft)
        if flash_frames > 0:
            flash_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                flash_surf,
                (112, 236, 255, min(120, 42 + (flash_frames * 6))),
                flash_surf.get_rect(),
                border_radius=10,
            )
            screen.blit(flash_surf, highlight_rect.topleft)

    draw_wrapped_label_value_lines(
        screen,
        font=font,
        label_lines=label_lines,
        value_lines=value_lines,
        label_x=option_x,
        value_right=value_right,
        top_y=text_top_y,
        label_color=txt_color,
    )
    if slider_layout is not None and isinstance(raw_value, int):
        draw_value_slider(
            screen,
            rect=pygame.Rect(
                option_x + option_w - slider_layout.slider_width,
                option_y
                + row_height
                - slider_layout.row_bottom_padding
                - slider_layout.slider_height,
                slider_layout.slider_width,
                slider_layout.slider_height,
            ),
            fraction=max(
                0.0,
                min(
                    1.0,
                    (float(raw_value) - float(field.min_value or 0))
                    / max(
                        1.0,
                        float(field.max_value or 0) - float(field.min_value or 0),
                    ),
                ),
            ),
            flash_strength=max(0.0, min(1.0, flash_frames / 12.0))
            if is_selected
            else 0.0,
        )
    return row_height


def _draw_menu_settings_panel(
    screen: pygame.Surface,
    fonts: GfxFonts,
    settings,
    selected_index: int,
    panel_top: int,
    flash_frames: int = 0,
    menu_fields: Optional[Sequence[FieldSpec]] = None,
    value_formatter: Optional[Callable[[FieldSpec, object], str]] = None,
) -> Tuple[int, int, int, int]:
    width, height = screen.get_size()
    panel_w = min(max(340, int(width * 0.6)), width - 24)
    if menu_fields:
        panel_w = min(
            width - 24,
            max(panel_w, min(menu_slider_row_min_total_width() + 84, width - 24)),
        )
    if menu_fields:
        labels = [
            f"{field.label}:  "
            + (
                value_formatter(field, getattr(settings, field.attr_name))
                if value_formatter
                else str(getattr(settings, field.attr_name))
            )
            for field in menu_fields
        ]
        row_heights = [
            _menu_row_height(
                fonts.menu_font,
                field=field,
                value_text=(
                    value_formatter(field, getattr(settings, field.attr_name))
                    if value_formatter
                    else str(getattr(settings, field.attr_name))
                ),
                total_width=panel_w - 56,
            )
            for field in menu_fields
        ]
    else:
        labels = [
            f"Board width:   {settings.width}",
            f"Board height:  {settings.height}",
            f"Speed level:   {settings.speed_level}   (1 = slow, 10 = fast)",
        ]
        row_heights = [fonts.menu_font.get_height() + 18 for _ in labels]

    row_h_default = fonts.menu_font.get_height() + 18
    panel_max_h = max(140, height - panel_top - 126)
    row_h = min(
        max(row_heights) if row_heights else row_h_default,
        max(
            fonts.menu_font.get_height() + 8,
            (panel_max_h - 40) // max(1, len(labels)),
        ),
    )
    panel_h = min(
        panel_max_h,
        40 + sum(max(row_height, row_h) for row_height in row_heights),
    )
    panel_rect = standard_menu_panel_rect(
        screen,
        panel_w=panel_w,
        panel_h=panel_h,
        panel_top=max(134, panel_top),
        bottom_reserved=118,
    )
    panel_x = panel_rect.x
    panel_y = panel_rect.y

    draw_tron_panel(screen, rect=panel_rect)

    option_y = panel_y + 24
    option_x = panel_x + 28
    option_w = panel_w - 56
    option_bottom = panel_y + panel_h - 16

    for i, text in enumerate(labels):
        if option_y + fonts.menu_font.get_height() > option_bottom:
            break
        label_text, _separator, value_text = text.partition(":")
        value_text = value_text.strip()
        if menu_fields:
            field = menu_fields[i]
            raw_value = getattr(settings, field.attr_name)
        else:
            field = FieldSpec(
                label=label_text.rstrip(":"),
                attr_name="",
                semantic_type="int",
                control_family="stepper",
            )
            raw_value = value_text
        option_y += _draw_menu_setting_row(
            screen,
            font=fonts.menu_font,
            option_x=option_x,
            option_w=option_w,
            option_y=option_y,
            field=field,
            value_text=value_text,
            raw_value=raw_value,
            is_selected=(i == selected_index),
            flash_frames=flash_frames,
            min_row_height=row_h,
        )

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

    full_block_bottom = (
        dpad_center_y + dpad_offset + 50 + 32 + fonts.hint_font.get_height() + 8
    )
    if full_block_bottom > height - 6:
        compact_text = fit_text(
            fonts.hint_font,
            _SETUP_MENU_COPY["compact_controls_hint"],
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


def draw_menu(
    screen: pygame.Surface,
    fonts: GfxFonts,
    settings,
    selected_index: int,
    bindings_file_hint: str | None = "keybindings/2d.json",
    extra_hint_lines: Tuple[str, ...] = (),
    bindings_status: str = "",
    bindings_status_error: bool = False,
    flash_frames: int = 0,
    menu_fields: Optional[Sequence[FieldSpec]] = None,
    value_formatter: Optional[Callable[[FieldSpec, object], str]] = None,
) -> None:
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
        flash_frames=flash_frames,
        menu_fields=menu_fields,
        value_formatter=value_formatter,
    )
    _draw_menu_dpad_and_commands(screen, fonts, panel_y, panel_h)


# ---------- Game drawing ----------


def compute_game_layout(
    screen: pygame.Surface, cfg: GameConfig
) -> Tuple[Tuple[int, int], Tuple[int, int]]:
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
        pygame.draw.line(
            shadow, (130, 150, 190, alpha), (0, y), (board_rect.width, y), 1
        )

    surface.blit(shadow, board_rect.topleft)
    pygame.draw.rect(surface, (86, 104, 146), board_rect, 2)


def _draw_board_edges_only(surface: pygame.Surface, board_rect: pygame.Rect) -> None:
    for index in range(board_rect.width // CELL_SIZE):
        left = board_rect.x + index * CELL_SIZE
        right = left + CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (left, board_rect.y), (right, board_rect.y))
        pygame.draw.line(surface, GRID_COLOR, (left, board_rect.bottom), (right, board_rect.bottom))
    for index in range(board_rect.height // CELL_SIZE):
        top = board_rect.y + index * CELL_SIZE
        bottom = top + CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (board_rect.x, top), (board_rect.x, bottom))
        pygame.draw.line(surface, GRID_COLOR, (board_rect.right, top), (board_rect.right, bottom))
    pygame.draw.rect(surface, (86, 104, 146), board_rect, 2)


def _helper_grid_marks_2d(
    state: GameState, width: int, height: int
) -> tuple[set[int], set[int]]:
    x_marks: set[int] = set()
    y_marks: set[int] = set()
    for x, y in state.current_piece_cells_mapped(include_above=False):
        if 0 <= x < width and 0 <= y < height:
            x_marks.add(x)
            x_marks.add(x + 1)
            y_marks.add(y)
            y_marks.add(y + 1)
    return x_marks, y_marks


def _draw_helper_grid(
    surface: pygame.Surface,
    board_rect: pygame.Rect,
    width_cells: int,
    height_cells: int,
    x_marks: set[int],
    y_marks: set[int],
) -> None:
    for x in sorted(x_marks):
        if not (0 <= x <= width_cells):
            continue
        x_px = board_rect.x + x * CELL_SIZE
        pygame.draw.line(
            surface, GRID_COLOR, (x_px, board_rect.y), (x_px, board_rect.bottom)
        )
    for y in sorted(y_marks):
        if not (0 <= y <= height_cells):
            continue
        y_px = board_rect.y + y * CELL_SIZE
        pygame.draw.line(
            surface, GRID_COLOR, (board_rect.x, y_px), (board_rect.right, y_px)
        )


def _draw_clear_effect(
    surface: pygame.Surface,
    board_rect: pygame.Rect,
    width_cells: int,
    clear_effect: Optional[ClearEffect2D],
) -> None:
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
        pygame.draw.rect(
            overlay, (120, 220, 255, min(255, base_alpha + 45)), sweep_rect
        )
        pygame.draw.rect(
            overlay, (255, 255, 255, min(255, base_alpha + 55)), overlay.get_rect(), 2
        )

        surface.blit(overlay, row_rect.topleft)


def _draw_full_grid(
    surface: pygame.Surface, ox: int, oy: int, width_cells: int, height_cells: int
) -> None:
    for x in range(width_cells + 1):
        x_px = ox + x * CELL_SIZE
        pygame.draw.line(
            surface, GRID_COLOR, (x_px, oy), (x_px, oy + height_cells * CELL_SIZE)
        )
    for y in range(height_cells + 1):
        y_px = oy + y * CELL_SIZE
        pygame.draw.line(
            surface, GRID_COLOR, (ox, y_px), (ox + width_cells * CELL_SIZE, y_px)
        )


def _draw_grid_variant(
    surface: pygame.Surface,
    board_rect: pygame.Rect,
    state: GameState,
    ox: int,
    oy: int,
    width_cells: int,
    height_cells: int,
    grid_mode: GridMode,
) -> None:
    if grid_mode in (
        GridMode.OFF,
        GridMode.SHADOW,
        GridMode.HELPER,
        GridMode.BOTTOM_BOUNDARY,
        GridMode.ALL_BOUNDARIES,
    ):
        _draw_board_shadow(surface, board_rect)
    elif grid_mode == GridMode.EDGE:
        _draw_board_edges_only(surface, board_rect)

    if grid_mode == GridMode.FULL:
        _draw_full_grid(surface, ox, oy, width_cells, height_cells)
    elif grid_mode == GridMode.HELPER:
        x_marks, y_marks = _helper_grid_marks_2d(state, width_cells, height_cells)
        _draw_helper_grid(
            surface, board_rect, width_cells, height_cells, x_marks, y_marks
        )


def _draw_locked_cells(
    surface: pygame.Surface,
    state: GameState,
    board_offset: tuple[int, int],
    width_cells: int,
    height_cells: int,
    *,
    overlay_transparency: float,
    outline: bool,
) -> None:
    locked_opacity = 1.0 - max(0.0, min(1.0, float(overlay_transparency)))
    locked_alpha = max(0, min(255, int(round(255.0 * locked_opacity))))
    if locked_alpha >= 255:
        for (x, y), cell_id in state.board.cells.items():
            if 0 <= x < width_cells and 0 <= y < height_cells:
                _draw_cell(surface, x, y, cell_id, board_offset, outline=outline)
        return
    if locked_alpha <= 0:
        return
    ox, oy = board_offset
    overlay = pygame.Surface(
        (width_cells * CELL_SIZE, height_cells * CELL_SIZE),
        pygame.SRCALPHA,
    )
    for (x, y), cell_id in state.board.cells.items():
        if 0 <= x < width_cells and 0 <= y < height_cells:
            local_rect = pygame.Rect(
                x * CELL_SIZE + 1,
                y * CELL_SIZE + 1,
                CELL_SIZE - 2,
                CELL_SIZE - 2,
            )
            color = color_for_cell(cell_id)
            pygame.draw.rect(overlay, (*color, locked_alpha), local_rect)
            if outline:
                pygame.draw.rect(overlay, (255, 255, 255, locked_alpha), local_rect, 2)
    surface.blit(overlay, (ox, oy))


def _clamp_channel(value: float) -> int:
    return max(0, min(255, int(round(value))))


def _shade_color(
    color: tuple[int, int, int],
    *,
    delta: float = 0.0,
    scale: float = 1.0,
) -> tuple[int, int, int]:
    return tuple(_clamp_channel((channel * scale) + delta) for channel in color)


def _rotated_cell_quad_points(
    *,
    center_cell: tuple[float, float],
    angle_deg: float,
) -> tuple[tuple[float, float], ...]:
    half_extent = float(CELL_SIZE - 2) / (2.0 * float(CELL_SIZE))
    angle_rad = math.radians(float(angle_deg))
    cos_t = math.cos(angle_rad)
    sin_t = math.sin(angle_rad)
    cx, cy = center_cell
    points: list[tuple[float, float]] = []
    for local_x, local_y in (
        (-half_extent, -half_extent),
        (half_extent, -half_extent),
        (half_extent, half_extent),
        (-half_extent, half_extent),
    ):
        points.append(
            (
                cx + (local_x * cos_t) - (local_y * sin_t),
                cy + (local_x * sin_t) + (local_y * cos_t),
            )
        )
    return tuple(points)


def _polygon_area(points: Sequence[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    for idx, (x0, y0) in enumerate(points):
        x1, y1 = points[(idx + 1) % len(points)]
        area += (x0 * y1) - (x1 * y0)
    return area / 2.0


def _line_rect_intersection(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
    *,
    axis: int,
    boundary: float,
) -> tuple[float, float]:
    delta = point_b[axis] - point_a[axis]
    if abs(delta) <= 1e-9:
        result = list(point_a)
        result[axis] = boundary
        return (float(result[0]), float(result[1]))
    t = (boundary - point_a[axis]) / delta
    return (
        float(point_a[0] + ((point_b[0] - point_a[0]) * t)),
        float(point_a[1] + ((point_b[1] - point_a[1]) * t)),
    )


def _clip_polygon_against_edge(
    points: Sequence[tuple[float, float]],
    *,
    is_inside,
    intersection,
) -> tuple[tuple[float, float], ...]:
    if not points:
        return tuple()
    output: list[tuple[float, float]] = []
    prev = tuple(points[-1])
    prev_inside = bool(is_inside(prev))
    for current in points:
        current_pt = tuple(current)
        current_inside = bool(is_inside(current_pt))
        if current_inside:
            if not prev_inside:
                output.append(tuple(intersection(prev, current_pt)))
            output.append(current_pt)
        elif prev_inside:
            output.append(tuple(intersection(prev, current_pt)))
        prev = current_pt
        prev_inside = current_inside
    return tuple(output)


def _clip_polygon_to_rect(
    points: Sequence[tuple[float, float]],
    *,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
) -> tuple[tuple[float, float], ...]:
    clipped = tuple(tuple(point) for point in points)
    clipped = _clip_polygon_against_edge(
        clipped,
        is_inside=lambda point: point[0] >= xmin - 1e-9,
        intersection=lambda a, b: _line_rect_intersection(a, b, axis=0, boundary=xmin),
    )
    clipped = _clip_polygon_against_edge(
        clipped,
        is_inside=lambda point: point[0] <= xmax + 1e-9,
        intersection=lambda a, b: _line_rect_intersection(a, b, axis=0, boundary=xmax),
    )
    clipped = _clip_polygon_against_edge(
        clipped,
        is_inside=lambda point: point[1] >= ymin - 1e-9,
        intersection=lambda a, b: _line_rect_intersection(a, b, axis=1, boundary=ymin),
    )
    clipped = _clip_polygon_against_edge(
        clipped,
        is_inside=lambda point: point[1] <= ymax + 1e-9,
        intersection=lambda a, b: _line_rect_intersection(a, b, axis=1, boundary=ymax),
    )
    if len(clipped) < 3 or abs(_polygon_area(clipped)) <= 1e-9:
        return tuple()
    return clipped


def _overlay_axis_offsets_2d(
    state: GameState,
    *,
    axis: int,
) -> tuple[float, ...]:
    policy = state.topology_policy
    edge_rules = policy.edge_rules or tuple()
    if axis >= len(policy.dims) or axis >= len(edge_rules):
        return (0.0,)
    neg_behavior, pos_behavior = edge_rules[axis]
    if neg_behavior == "bounded" and pos_behavior == "bounded":
        return (0.0,)
    size = float(policy.dims[axis])
    return (-size, 0.0, size)


def _map_fragment_polygon_2d(
    state: GameState,
    points: Sequence[tuple[float, float]],
) -> tuple[tuple[float, float], ...]:
    if (
        state.config.exploration_mode
        and state.config.explorer_topology_profile is not None
    ):
        return tuple((float(x), float(y)) for x, y in points)
    return tuple(
        tuple(float(value) for value in coord)
        for coord in map_overlay_cells_gameplay(
            state.topology_policy,
            points,
            allow_above_gravity=False,
        )
    )


def _localize_fragment_axis_2d(
    *,
    original_value: float,
    mapped_value: float,
    offset: float,
    size: float,
    wraps: bool,
) -> float:
    if not wraps:
        return float(mapped_value - offset)
    candidates = [float(mapped_value + (size * step)) for step in (-2, -1, 0, 1, 2)]
    best = min(candidates, key=lambda candidate: abs(candidate - original_value))
    return float(best - offset)


def _localize_mapped_fragment_2d(
    state: GameState,
    *,
    original_points: Sequence[tuple[float, float]],
    mapped_points: Sequence[tuple[float, float]],
    offset_x: float,
    offset_y: float,
) -> tuple[tuple[float, float], ...]:
    edge_rules = state.topology_policy.edge_rules or tuple()
    wraps_x = len(edge_rules) > 0 and (
        edge_rules[0][0] != "bounded" or edge_rules[0][1] != "bounded"
    )
    wraps_y = len(edge_rules) > 1 and (
        edge_rules[1][0] != "bounded" or edge_rules[1][1] != "bounded"
    )
    size_x = float(state.topology_policy.dims[0])
    size_y = float(state.topology_policy.dims[1])
    localized: list[tuple[float, float]] = []
    for (orig_x, orig_y), (mapped_x, mapped_y) in zip(original_points, mapped_points):
        localized.append(
            (
                _localize_fragment_axis_2d(
                    original_value=float(orig_x),
                    mapped_value=float(mapped_x),
                    offset=float(offset_x),
                    size=size_x,
                    wraps=wraps_x,
                ),
                _localize_fragment_axis_2d(
                    original_value=float(orig_y),
                    mapped_value=float(mapped_y),
                    offset=float(offset_y),
                    size=size_y,
                    wraps=wraps_y,
                ),
            )
        )
    return tuple(localized)


def _to_screen_points_2d(
    board_offset: tuple[int, int],
    points: Sequence[tuple[float, float]],
) -> tuple[tuple[float, float], ...]:
    ox, oy = board_offset
    return tuple(
        (
            float(ox) + (float(x) * CELL_SIZE),
            float(oy) + (float(y) * CELL_SIZE),
        )
        for x, y in points
    )


def _draw_styled_piece_quad(
    surface: pygame.Surface,
    points: tuple[tuple[float, float], ...],
    color: tuple[int, int, int],
) -> None:
    if len(points) < 3:
        return
    shadow_points = tuple((x + 2.0, y + 2.0) for x, y in points)
    pygame.draw.polygon(surface, (0, 0, 0, 70), shadow_points)
    pygame.draw.polygon(surface, color, points)
    if len(points) != 4:
        pygame.draw.polygon(surface, (255, 255, 255, 210), points, 1)
        return
    highlight = _shade_color(color, delta=30.0)
    bevel = _shade_color(color, scale=0.65)
    pygame.draw.line(surface, highlight, points[0], points[1], 2)
    pygame.draw.line(surface, highlight, points[0], points[3], 2)
    pygame.draw.line(surface, bevel, points[3], points[2], 2)
    pygame.draw.line(surface, bevel, points[1], points[2], 2)
    pygame.draw.polygon(surface, (255, 255, 255, 210), points, 1)


def _draw_overlay_cell_boxes_2d(
    surface: pygame.Surface,
    state: GameState,
    cells: Sequence[tuple[float, float]],
    color_id: int,
    board_offset: tuple[int, int],
    *,
    width_cells: int,
    height_cells: int,
    angle_deg: float,
) -> None:
    if not cells:
        return
    color = color_for_cell(int(color_id))
    x_offsets = _overlay_axis_offsets_2d(state, axis=0)
    y_offsets = _overlay_axis_offsets_2d(state, axis=1)
    for x, y in cells:
        raw_quad = _rotated_cell_quad_points(
            center_cell=(float(x) + 0.5, float(y) + 0.5),
            angle_deg=float(angle_deg),
        )
        for offset_x in x_offsets:
            for offset_y in y_offsets:
                clipped = _clip_polygon_to_rect(
                    raw_quad,
                    xmin=float(offset_x),
                    xmax=float(offset_x + width_cells),
                    ymin=float(offset_y),
                    ymax=float(offset_y + height_cells),
                )
                if not clipped:
                    continue
                mapped = _map_fragment_polygon_2d(state, clipped)
                if len(mapped) < 3 or abs(_polygon_area(mapped)) <= 1e-9:
                    continue
                localized = _localize_mapped_fragment_2d(
                    state,
                    original_points=clipped,
                    mapped_points=mapped,
                    offset_x=float(offset_x),
                    offset_y=float(offset_y),
                )
                if abs(_polygon_area(localized)) <= 1e-9:
                    continue
                _draw_styled_piece_quad(
                    surface,
                    _to_screen_points_2d(board_offset, localized),
                    color,
                )


def _draw_active_piece_cells(
    surface: pygame.Surface,
    state: GameState,
    board_offset: tuple[int, int],
    width_cells: int,
    height_cells: int,
    *,
    overlay: ActiveOverlay2D | None,
) -> None:
    if isinstance(overlay, RigidPieceOverlay2D):
        _draw_rigid_piece_overlay(
            surface,
            state,
            overlay,
            board_offset,
            width_cells=width_cells,
            height_cells=height_cells,
        )
        return
    if overlay is not None:
        raw_cells, color_id = overlay
        _draw_overlay_cell_boxes_2d(
            surface,
            state,
            raw_cells,
            color_id,
            board_offset,
            width_cells=width_cells,
            height_cells=height_cells,
            angle_deg=0.0,
        )
        return

    if state.current_piece is None:
        return
    shape_color = state.current_piece.shape.color_id
    for x, y in state.current_piece_cells_mapped(include_above=False):
        if 0 <= x < width_cells and 0 <= y < height_cells:
            _draw_cell(surface, x, y, shape_color, board_offset, outline=True)


def _projection_guide_cells_2d(
    state: GameState,
    *,
    overlay: ActiveOverlay2D | None,
    width_cells: int,
    height_cells: int,
) -> tuple[tuple[GuideCell2D, ...], int | None]:
    if isinstance(overlay, RigidPieceOverlay2D):
        raw_cells = tuple(
            (float(coord[0]), float(coord[1])) for coord in overlay.cells
        )
        color_id = int(overlay.color_id)
    elif overlay is not None:
        raw_cells = tuple(
            (float(coord[0]), float(coord[1])) for coord in overlay[0]
        )
        color_id = int(overlay[1])
    elif state.current_piece is not None:
        raw_cells = tuple(
            (float(coord[0]), float(coord[1]))
            for coord in state.current_piece_cells_mapped(include_above=False)
        )
        color_id = int(state.current_piece.shape.color_id)
    else:
        return tuple(), None

    if (
        state.config.exploration_mode
        and state.config.explorer_topology_profile is not None
    ):
        mapped_cells = raw_cells
    else:
        mapped_cells = tuple(
            (
                float(mapped[0]),
                float(mapped[1]),
            )
            for mapped in map_overlay_cells_gameplay(
                state.topology_policy,
                raw_cells,
                allow_above_gravity=False,
            )
        )

    cells: list[GuideCell2D] = []
    for x, y in mapped_cells:
        if 0.0 <= float(x) < width_cells and 0.0 <= float(y) < height_cells:
            cells.append(((float(x), float(y)), 1.0))
    return tuple(cells), color_id


def _draw_projection_guide_2d(
    surface: pygame.Surface,
    state: GameState,
    board_offset: tuple[int, int],
    *,
    width_cells: int,
    height_cells: int,
    grid_mode: GridMode,
    overlay: ActiveOverlay2D | None,
) -> None:
    if not projection_guide_enabled(grid_mode):
        return
    cells, color_id = _projection_guide_cells_2d(
        state,
        overlay=overlay,
        width_cells=width_cells,
        height_cells=height_cells,
    )
    if not cells or color_id is None:
        return
    segments = build_boundary_projection_segments_2d(
        cells=cells,
        dims=(width_cells, height_cells),
        gravity_axis=int(state.config.gravity_axis),
        grid_mode=grid_mode,
        color=color_for_cell(int(color_id)),
    )
    draw_boundary_projection_segments_2d(
        surface,
        segments=segments,
        board_offset=board_offset,
        cell_size=CELL_SIZE,
    )


def _draw_rigid_piece_overlay(
    surface: pygame.Surface,
    state: GameState,
    overlay: RigidPieceOverlay2D,
    board_offset: tuple[int, int],
    *,
    width_cells: int,
    height_cells: int,
) -> None:
    _draw_overlay_cell_boxes_2d(
        surface,
        state,
        overlay.cells,
        overlay.color_id,
        board_offset,
        width_cells=width_cells,
        height_cells=height_cells,
        angle_deg=float(overlay.angle_deg),
    )


def _endgame_screen_points_2d(
    board_offset: tuple[int, int],
    points: Sequence[tuple[float, float, float]],
) -> tuple[tuple[float, float], ...]:
    return _to_screen_points_2d(
        board_offset,
        tuple((float(point[0]) + 0.5, float(point[1]) + 0.5) for point in points),
    )


def _endgame_cell_quad_points_2d(
    *,
    center: tuple[float, float, float],
    rotation_deg: tuple[float, float, float],
) -> tuple[tuple[float, float, float], ...]:
    local_corners = (
        (-0.5, -0.5, 0.0),
        (0.5, -0.5, 0.0),
        (0.5, 0.5, 0.0),
        (-0.5, 0.5, 0.0),
    )
    return tuple(
        (
            center[0] + rotated[0],
            center[1] + rotated[1],
            0.0,
        )
        for rotated in (rotate_point(point, rotation_deg) for point in local_corners)
    )


def _draw_endgame_grid_break_marks_2d(
    overlay: pygame.Surface,
    *,
    board_offset: tuple[int, int],
    endgame_animation: EndgameAnimationState,
) -> None:
    for mark in endgame_animation.grid_break_marks:
        tail, head, alpha = transform_grid_break_mark(
            mark,
            elapsed_ms=float(endgame_animation.elapsed_ms),
        )
        if alpha <= 0.0:
            continue
        line_points = _endgame_screen_points_2d(
            board_offset,
            ((tail[0], tail[1], 0.0), (head[0], head[1], 0.0)),
        )
        color = color_for_cell(int(mark.color_id))
        pygame.draw.line(
            overlay,
            (0, 0, 0, max(0, min(190, int(round(190 * alpha))))),
            line_points[0],
            line_points[1],
            4,
        )
        pygame.draw.line(
            overlay,
            (*color, max(0, min(255, int(round(235 * alpha))))),
            line_points[0],
            line_points[1],
            1,
        )


def _draw_endgame_board_2d(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    board_offset: tuple[int, int],
    endgame_animation: EndgameAnimationState,
) -> None:
    pygame.draw.rect(surface, (20, 20, 50), board_rect)
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    drag = float(endgame_animation.tuning.burst_drag_per_second)

    for shell_fragment in endgame_animation.shell_fragments:
        transformed, alpha = transform_shell_geometry(
            shell_fragment,
            elapsed_ms=float(endgame_animation.elapsed_ms),
            drag_per_second=drag,
        )
        if alpha <= 0.0:
            continue
        screen_points = _endgame_screen_points_2d(
            board_offset,
            (
                (transformed[0][0], transformed[0][1], 0.0),
                (transformed[1][0], transformed[1][1], 0.0),
            ),
        )
        pygame.draw.line(
            overlay,
            (*GRID_COLOR, max(0, min(255, int(round(220 * alpha))))),
            screen_points[0],
            screen_points[1],
            2,
        )

    _draw_endgame_grid_break_marks_2d(
        overlay,
        board_offset=board_offset,
        endgame_animation=endgame_animation,
    )

    for artifact in endgame_animation.escaping_artifacts:
        tail, head, alpha = transform_shell_artifact(
            artifact,
            elapsed_ms=float(endgame_animation.elapsed_ms),
        )
        if alpha <= 0.0:
            continue
        line_points = _endgame_screen_points_2d(
            board_offset,
            (
                (tail[0], tail[1], 0.0),
                (head[0], head[1], 0.0),
            ),
        )
        color = color_for_cell(int(artifact.color_id))
        width = 1 if artifact.kind == "spark" else 2
        pygame.draw.line(
            overlay,
            (*color, max(0, min(255, int(round(210 * alpha))))),
            line_points[0],
            line_points[1],
            width,
        )

    assert endgame_animation.explosion_controller is not None
    relic_render_states = endgame_animation.explosion_controller.render_particles(
        render_context=endgame_animation.snapshot.render_context
    )
    shadow_mode = ShadowMode(str(endgame_animation.snapshot.shadow_mode))
    if shadow_mode != ShadowMode.OFF:
        shadow_segments = tuple(
            segment
            for relic_state in relic_render_states
            for segment in build_boundary_projection_segments_2d(
                cells=(
                    (
                        tuple(
                            float(value)
                            for value in relic_state.render_position[:2]
                        ),
                        0.82,
                    ),
                ),
                dims=(
                    int(endgame_animation.snapshot.board_dims[0]),
                    int(endgame_animation.snapshot.board_dims[1]),
                ),
                gravity_axis=1,
                grid_mode=GridMode(shadow_mode.value),
                color=color_for_cell(int(relic_state.color_id)),
            )
        )
        draw_boundary_projection_segments_2d(
            overlay,
            segments=shadow_segments,
            board_offset=board_offset,
            cell_size=CELL_SIZE,
        )
    for relic_state in relic_render_states:
        color = color_for_cell(int(relic_state.color_id))
        if endgame_animation.snapshot.trace_enabled:
            for segment in tuple(getattr(relic_state, "trail_segments", ())):
                line_points = _endgame_screen_points_2d(
                    board_offset,
                    (
                        (
                            segment.tail_render_position[0],
                            segment.tail_render_position[1],
                            0.0,
                        ),
                        (
                            segment.head_render_position[0],
                            segment.head_render_position[1],
                            0.0,
                        ),
                    ),
                )
                pygame.draw.line(
                    overlay,
                    (
                        color[0],
                        color[1],
                        color[2],
                        max(0, min(255, int(round(172 * float(segment.alpha))))),
                    ),
                    line_points[0],
                    line_points[1],
                    max(
                        1,
                        int(round(CELL_SIZE * 0.08 * max(0.35, float(segment.width)))),
                    ),
                )
        position = relic_state.render_position
        rotation_deg = relic_state.rotation_deg
        alpha = relic_state.alpha
        if alpha <= 0.0:
            continue
        quad_points = _endgame_screen_points_2d(
            board_offset,
            _endgame_cell_quad_points_2d(center=position, rotation_deg=rotation_deg),
        )
        fill_alpha = max(0, min(255, int(round(255 * alpha))))
        outline_alpha = max(0, min(255, int(round(220 * alpha))))
        shadow_points = tuple((x + 2.0, y + 2.0) for x, y in quad_points)
        pygame.draw.polygon(overlay, (0, 0, 0, min(140, fill_alpha)), shadow_points)
        pygame.draw.polygon(overlay, (*color, fill_alpha), quad_points)
        pygame.draw.polygon(overlay, (255, 255, 255, outline_alpha), quad_points, 2)

    surface.blit(overlay, (0, 0))


def draw_board(
    surface: pygame.Surface,
    state: GameState,
    board_offset: Tuple[int, int],
    grid_mode: GridMode = GridMode.FULL,
    overlay_transparency: float = 0.25,
    clear_effect: Optional[ClearEffect2D] = None,
    active_piece_overlay: ActiveOverlay2D | None = None,
    endgame_animation: EndgameAnimationState | None = None,
) -> None:
    """Draw grid + locked cells + active piece."""
    ox, oy = board_offset
    w, h = state.config.width, state.config.height

    # Board background
    board_rect = pygame.Rect(ox, oy, w * CELL_SIZE, h * CELL_SIZE)
    if endgame_animation is not None and endgame_animation.frozen_render_active:
        _draw_endgame_board_2d(
            surface,
            board_rect=board_rect,
            board_offset=board_offset,
            endgame_animation=endgame_animation,
        )
        return
    pygame.draw.rect(surface, (20, 20, 50), board_rect)
    _draw_grid_variant(surface, board_rect, state, ox, oy, w, h, grid_mode)
    _draw_locked_cells(
        surface,
        state,
        board_offset,
        w,
        h,
        overlay_transparency=overlay_transparency,
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
    _draw_projection_guide_2d(
        surface,
        state,
        board_offset,
        width_cells=w,
        height_cells=h,
        grid_mode=grid_mode,
        overlay=active_piece_overlay,
    )

    _draw_clear_effect(surface, board_rect, w, clear_effect)


def _draw_cell(
    surface: pygame.Surface,
    x: int,
    y: int,
    cell_id: int,
    board_offset: Tuple[int, int],
    outline: bool = False,
) -> None:
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


def draw_side_panel(
    surface: pygame.Surface,
    state: GameState,
    panel_offset: Tuple[int, int],
    fonts: GfxFonts,
    grid_mode: GridMode = GridMode.FULL,
    bot_lines: Sequence[str] = (),
    overlay_transparency: float = 0.25,
) -> None:
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
        overlay_transparency=overlay_transparency,
    )


def gravity_interval_ms_from_config(cfg: GameConfig) -> int:
    return gravity_interval_ms_gameplay(cfg.speed_level, dimension=2)


def draw_game_frame(
    screen: pygame.Surface,
    cfg: GameConfig,
    state: GameState,
    fonts: GfxFonts,
    grid_mode: GridMode = GridMode.FULL,
    bot_lines: Sequence[str] = (),
    overlay_transparency: float = 0.25,
    clear_effect: Optional[ClearEffect2D] = None,
    active_piece_overlay: ActiveOverlay2D | None = None,
    endgame_animation: EndgameAnimationState | None = None,
) -> None:
    """Single call to draw the whole game frame."""
    screen.fill(BG_COLOR)
    board_offset, panel_offset = compute_game_layout(screen, cfg)
    board_rect = pygame.Rect(
        board_offset[0],
        board_offset[1],
        cfg.width * CELL_SIZE,
        cfg.height * CELL_SIZE,
    )
    draw_board(
        screen,
        state,
        board_offset,
        grid_mode=grid_mode,
        overlay_transparency=overlay_transparency,
        clear_effect=clear_effect,
        active_piece_overlay=active_piece_overlay,
        endgame_animation=endgame_animation,
    )
    if state.game_over:
        draw_game_over_banner(
            screen,
            rect=board_rect,
            fonts=fonts,
        )
    draw_side_panel(
        screen,
        state,
        panel_offset,
        fonts,
        grid_mode=grid_mode,
        bot_lines=bot_lines,
        overlay_transparency=overlay_transparency,
    )
