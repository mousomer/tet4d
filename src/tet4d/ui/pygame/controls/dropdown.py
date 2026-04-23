from __future__ import annotations

from typing import Callable

import pygame


def open_dropdown(state, *, row_key: str) -> None:
    state.open_dropdown_row_key = str(row_key)
    state.dropdown_scroll_offset = 0
    state.dropdown_hover_index = None


def close_dropdown(state) -> None:
    state.open_dropdown_row_key = None
    state.dropdown_hover_index = None


def dropdown_menu_rect(
    row_rect: pygame.Rect,
    *,
    option_count: int,
    viewport: pygame.Rect,
    font: pygame.font.Font,
    menu_width: int,
    option_vertical_padding: int,
) -> pygame.Rect:
    option_height = font.get_height() + int(option_vertical_padding)
    max_visible_options = max(1, (viewport.height - 16) // option_height)
    visible_count = min(int(option_count), max_visible_options)
    height = max(option_height + 8, visible_count * option_height + 8)
    width = min(
        max(int(menu_width), row_rect.width // 2),
        max(int(menu_width), viewport.width - 12),
    )
    rect = pygame.Rect(
        row_rect.right - width - 8,
        row_rect.bottom + 2,
        width,
        height,
    )
    if rect.right > viewport.right - 4:
        rect.x = viewport.right - rect.width - 4
    if rect.bottom > viewport.bottom - 4:
        rect.y = max(viewport.y + 4, row_rect.y - rect.height - 2)
    return rect


def dropdown_visible_slice(
    state,
    *,
    option_count: int,
    menu_rect: pygame.Rect,
    font: pygame.font.Font,
    option_vertical_padding: int,
) -> tuple[int, int]:
    option_height = font.get_height() + int(option_vertical_padding)
    visible_count = max(1, (menu_rect.height - 8) // option_height)
    max_offset = max(0, int(option_count) - visible_count)
    offset = max(0, min(max_offset, int(state.dropdown_scroll_offset)))
    return offset, min(int(option_count), offset + visible_count)


def dropdown_option_rects(
    state,
    *,
    menu_rect: pygame.Rect,
    option_count: int,
    font: pygame.font.Font,
    option_vertical_padding: int,
) -> tuple[tuple[int, pygame.Rect], ...]:
    start, end = dropdown_visible_slice(
        state,
        option_count=option_count,
        menu_rect=menu_rect,
        font=font,
        option_vertical_padding=option_vertical_padding,
    )
    option_height = font.get_height() + int(option_vertical_padding)
    rects: list[tuple[int, pygame.Rect]] = []
    for visible_index, option_index in enumerate(range(start, end)):
        rects.append(
            (
                option_index,
                pygame.Rect(
                    menu_rect.x + 4,
                    menu_rect.y + 4 + visible_index * option_height,
                    menu_rect.width - 8,
                    option_height,
                ),
            )
        )
    return tuple(rects)


def dropdown_option_index_at_position(
    state,
    *,
    row_layouts,
    row_rects,
    layout_viewport: pygame.Rect,
    font: pygame.font.Font,
    position: tuple[int, int],
    options_for_row: Callable[[str], tuple[tuple[str, str], ...]],
    menu_width: int,
    option_vertical_padding: int,
) -> int | None:
    if state.open_dropdown_row_key is None:
        return None
    open_index = next(
        (idx for idx, row_layout in enumerate(row_layouts) if row_layout.row_key == state.open_dropdown_row_key),
        None,
    )
    if open_index is None:
        return None
    options = options_for_row(state.open_dropdown_row_key)
    if not options:
        return None
    menu_rect = dropdown_menu_rect(
        row_rects[open_index],
        option_count=len(options),
        viewport=layout_viewport,
        font=font,
        menu_width=menu_width,
        option_vertical_padding=option_vertical_padding,
    )
    for option_index, option_rect in dropdown_option_rects(
        state,
        menu_rect=menu_rect,
        option_count=len(options),
        font=font,
        option_vertical_padding=option_vertical_padding,
    ):
        if option_rect.collidepoint(position):
            return option_index
    return None


def update_dropdown_hover_index(
    state,
    *,
    row_layouts,
    row_rects,
    layout_viewport: pygame.Rect,
    font: pygame.font.Font,
    position: tuple[int, int],
    options_for_row: Callable[[str], tuple[tuple[str, str], ...]],
    menu_width: int,
    option_vertical_padding: int,
) -> None:
    state.dropdown_hover_index = dropdown_option_index_at_position(
        state,
        row_layouts=row_layouts,
        row_rects=row_rects,
        layout_viewport=layout_viewport,
        font=font,
        position=position,
        options_for_row=options_for_row,
        menu_width=menu_width,
        option_vertical_padding=option_vertical_padding,
    )


def update_dropdown_scroll(
    state,
    event,
    *,
    row_layouts,
    row_rects,
    layout_viewport: pygame.Rect,
    font: pygame.font.Font,
    options_for_row: Callable[[str], tuple[tuple[str, str], ...]],
    menu_width: int,
    option_vertical_padding: int,
) -> bool:
    if event.type != pygame.MOUSEWHEEL or state.open_dropdown_row_key is None:
        return False
    open_index = next(
        (idx for idx, row_layout in enumerate(row_layouts) if row_layout.row_key == state.open_dropdown_row_key),
        None,
    )
    if open_index is None:
        return False
    options = options_for_row(state.open_dropdown_row_key)
    if not options:
        return False
    menu_rect = dropdown_menu_rect(
        row_rects[open_index],
        option_count=len(options),
        viewport=layout_viewport,
        font=font,
        menu_width=menu_width,
        option_vertical_padding=option_vertical_padding,
    )
    dropdown_visible_slice(
        state,
        option_count=len(options),
        menu_rect=menu_rect,
        font=font,
        option_vertical_padding=option_vertical_padding,
    )
    state.dropdown_scroll_offset = max(0, int(state.dropdown_scroll_offset) - int(event.y))
    return True


def select_dropdown_option_from_click(
    state,
    *,
    position: tuple[int, int],
    row_layouts,
    row_rects,
    layout_viewport: pygame.Rect,
    font: pygame.font.Font,
    options_for_row: Callable[[str], tuple[tuple[str, str], ...]],
    apply_value: Callable[[str, str], bool],
    menu_width: int,
    option_vertical_padding: int,
) -> tuple[str | None, bool]:
    if state.open_dropdown_row_key is None:
        return None, False
    open_index = next(
        (idx for idx, row_layout in enumerate(row_layouts) if row_layout.row_key == state.open_dropdown_row_key),
        None,
    )
    if open_index is None:
        close_dropdown(state)
        return None, False
    row_key = str(state.open_dropdown_row_key)
    options = options_for_row(row_key)
    if not options:
        close_dropdown(state)
        return row_key, False
    menu_rect = dropdown_menu_rect(
        row_rects[open_index],
        option_count=len(options),
        viewport=layout_viewport,
        font=font,
        menu_width=menu_width,
        option_vertical_padding=option_vertical_padding,
    )
    if not menu_rect.collidepoint(position):
        close_dropdown(state)
        return None, False
    for option_index, option_rect in dropdown_option_rects(
        state,
        menu_rect=menu_rect,
        option_count=len(options),
        font=font,
        option_vertical_padding=option_vertical_padding,
    ):
        if option_rect.collidepoint(position):
            changed = apply_value(row_key, options[int(option_index)][0])
            close_dropdown(state)
            return row_key, changed
    close_dropdown(state)
    return row_key, False
