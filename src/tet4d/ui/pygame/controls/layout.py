from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame

from tet4d.ui.pygame.ui_utils import (
    SliderRowLayout,
    compute_slider_row_layout,
    wrapped_label_value_layout,
)


@dataclass(frozen=True)
class ControlRowLayout:
    row_key: str
    label_lines: tuple[str, ...]
    value_lines: tuple[str, ...]
    row_height: int
    control_kind: str
    value_right_padding: int = 12
    slider_fraction: float | None = None
    slider_layout: SliderRowLayout | None = None


def build_control_row_layouts(
    row_keys: tuple[str, ...],
    *,
    font: pygame.font.Font,
    panel_width: int,
    dropdown_affordance_width: int,
    label_for_row: Callable[[str], str],
    value_for_row: Callable[[str], str],
    control_kind_for_row: Callable[[str], str],
    slider_fraction_for_row: Callable[[str], float | None],
) -> tuple[ControlRowLayout, ...]:
    layouts: list[ControlRowLayout] = []
    for row_key in row_keys:
        label = label_for_row(row_key)
        value = value_for_row(row_key)
        control_kind = control_kind_for_row(row_key)
        slider_fraction = slider_fraction_for_row(row_key)
        slider_layout = None
        value_right_padding = (
            12 + int(dropdown_affordance_width) if control_kind == "dropdown" else 12
        )
        if control_kind == "numeric" and slider_fraction is not None:
            slider_layout = compute_slider_row_layout(
                font,
                label=label,
                value=value,
                total_width=max(120, panel_width - 36),
            )
            label_lines = slider_layout.label_lines
            value_lines = slider_layout.value_lines
            row_height = slider_layout.row_height
        else:
            label_lines, value_lines, row_height = wrapped_label_value_layout(
                font,
                label=label,
                value=value,
                total_width=max(120, panel_width - 36),
                value_width_fraction=0.42,
                min_label_width=92,
                horizontal_padding=18 + value_right_padding,
                column_gap=12,
            )
        layouts.append(
            ControlRowLayout(
                row_key=row_key,
                label_lines=label_lines,
                value_lines=value_lines,
                row_height=row_height,
                control_kind=control_kind,
                value_right_padding=value_right_padding,
                slider_fraction=slider_fraction,
                slider_layout=slider_layout,
            )
        )
    return tuple(layouts)


def row_rects(
    *,
    viewport: pygame.Rect,
    row_layouts: tuple[ControlRowLayout, ...],
    scroll_offset: int,
) -> tuple[pygame.Rect, ...]:
    row_gap = 6
    row_y = viewport.y - int(scroll_offset)
    rects: list[pygame.Rect] = []
    for row_layout in row_layouts:
        rects.append(
            pygame.Rect(
                viewport.x + 2,
                row_y,
                viewport.width - 4,
                row_layout.row_height,
            )
        )
        row_y += row_layout.row_height + row_gap
    return tuple(rects)


def slider_rect_for_row(
    row_rect: pygame.Rect,
    row_layout: ControlRowLayout,
) -> pygame.Rect | None:
    if row_layout.slider_layout is None:
        return None
    return pygame.Rect(
        row_rect.right - 12 - row_layout.slider_layout.slider_width,
        row_rect.y
        + row_layout.row_height
        - row_layout.slider_layout.row_bottom_padding
        - row_layout.slider_layout.slider_height,
        row_layout.slider_layout.slider_width,
        row_layout.slider_layout.slider_height,
    )


def row_index_at_position(
    row_rects: tuple[pygame.Rect, ...],
    *,
    position: tuple[int, int],
) -> int | None:
    for index, row_rect in enumerate(row_rects):
        if row_rect.collidepoint(position):
            return index
    return None
