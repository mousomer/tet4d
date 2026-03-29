from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class TopologyLabTopBarLayout:
    rect: pygame.Rect
    title_rect: pygame.Rect
    ribbon_rect: pygame.Rect
    dimension_chip_rect: pygame.Rect
    validity_chip_rect: pygame.Rect


@dataclass(frozen=True)
class TopologyLabFooterLayout:
    rect: pygame.Rect
    hint_lane_rect: pygame.Rect
    action_rect: pygame.Rect
    hint_chip_max_width: int


@dataclass(frozen=True)
class TopologyLabShellLayout:
    panel_rect: pygame.Rect
    content_rect: pygame.Rect
    controls_rect: pygame.Rect | None
    menu_w: int
    top_bar: TopologyLabTopBarLayout | None
    footer: TopologyLabFooterLayout | None
    separator_x: int | None


@dataclass(frozen=True)
class TopologyLabRowTextBudgets:
    label_width: int
    value_width: int


def topology_lab_row_text_budgets(
    *, menu_w: int, row_rect_width: int
) -> TopologyLabRowTextBudgets:
    usable_width = max(120, int(row_rect_width))
    reserved_width = 48
    min_value_width = 56
    max_label_width = max(120, usable_width - 110)
    preferred_label_width = min(int(menu_w * 0.56), int(usable_width * 0.62))
    label_width = max(132, min(max_label_width, preferred_label_width))
    if label_width + min_value_width + reserved_width > usable_width:
        label_width = max(80, usable_width - min_value_width - reserved_width)
    value_width = max(min_value_width, usable_width - label_width - reserved_width)
    return TopologyLabRowTextBudgets(
        label_width=max(80, label_width),
        value_width=max(48, value_width),
    )


def build_topology_lab_shell_layout(
    *,
    width: int,
    height: int,
    general_editor: bool,
    scene_pane_active: bool,
    row_count: int,
    dimension_text_width: int,
    validity_text_width: int,
    action_count: int,
) -> TopologyLabShellLayout:
    if general_editor:
        panel_w = min(1320, max(420, width - 24))
        panel_h = min(height - 24, max(660, height - 24))
    else:
        panel_w = min(820, max(420, width - 40))
        panel_h = min(height - 178, 92 + row_count * 36)
    panel_x = (width - panel_w) // 2
    panel_y = max(12, (height - panel_h) // 2)
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

    if not general_editor:
        return TopologyLabShellLayout(
            panel_rect=panel_rect,
            content_rect=panel_rect.copy(),
            controls_rect=None,
            menu_w=panel_w,
            top_bar=None,
            footer=None,
            separator_x=None,
        )

    top_bar_h = 46
    bottom_bar_h = 44
    content_y = panel_y + top_bar_h + 8
    content_h = panel_h - top_bar_h - bottom_bar_h - 16
    content_rect = pygame.Rect(panel_x + 10, content_y, panel_w - 20, content_h)
    compact_width = content_rect.width < 820
    menu_w_cap = 320 if compact_width else (334 if scene_pane_active else 344)
    menu_w_floor = 248 if compact_width else (272 if scene_pane_active else 296)
    menu_w = min(
        menu_w_cap,
        max(menu_w_floor, int(content_rect.width * (0.30 if scene_pane_active else 0.33))),
    )
    controls_rect = pygame.Rect(panel_x + 10, content_y, menu_w - 12, content_h)
    top_bar_rect = pygame.Rect(panel_x + 10, panel_y + 10, panel_w - 20, top_bar_h)

    chip_h = 28
    chip_gap = 8
    chip_top = top_bar_rect.y + 8
    right_pad = 14
    validity_w = max(60, validity_text_width + 22)
    dimension_w = max(44, dimension_text_width + 22)
    validity_chip_rect = pygame.Rect(
        top_bar_rect.right - right_pad - validity_w,
        chip_top,
        validity_w,
        chip_h,
    )
    dimension_chip_rect = pygame.Rect(
        validity_chip_rect.x - chip_gap - dimension_w,
        chip_top,
        dimension_w,
        chip_h,
    )

    title_x = top_bar_rect.x + 14
    title_y = top_bar_rect.y + 12
    available_center_width = max(220, dimension_chip_rect.x - title_x - 24)
    title_w = min(220, max(150, int(available_center_width * 0.30)))
    ribbon_x = title_x + title_w + 12
    ribbon_right = max(ribbon_x + 180, dimension_chip_rect.x - 12)
    ribbon_rect = pygame.Rect(
        ribbon_x,
        top_bar_rect.y + 8,
        max(180, min(310, ribbon_right - ribbon_x)),
        30,
    )
    title_rect = pygame.Rect(
        title_x,
        title_y,
        max(120, ribbon_rect.x - title_x - 12),
        22,
    )

    bottom_rect = pygame.Rect(
        panel_x + 10,
        panel_y + panel_h - 54,
        panel_w - 20,
        40,
    )
    min_hint_lane_w = 180
    action_area_w = min(
        max(96, bottom_rect.width - min_hint_lane_w - 20),
        max(96, action_count * 96 + max(0, action_count - 1) * 8),
    )
    action_rect = pygame.Rect(
        bottom_rect.right - action_area_w - 10,
        bottom_rect.y + 6,
        action_area_w,
        28,
    )
    hint_lane_rect = pygame.Rect(
        bottom_rect.x + 10,
        bottom_rect.y + 8,
        max(40, action_rect.x - bottom_rect.x - 20),
        24,
    )
    footer = TopologyLabFooterLayout(
        rect=bottom_rect,
        hint_lane_rect=hint_lane_rect,
        action_rect=action_rect,
        hint_chip_max_width=190,
    )

    return TopologyLabShellLayout(
        panel_rect=panel_rect,
        content_rect=content_rect,
        controls_rect=controls_rect,
        menu_w=menu_w,
        top_bar=TopologyLabTopBarLayout(
            rect=top_bar_rect,
            title_rect=title_rect,
            ribbon_rect=ribbon_rect,
            dimension_chip_rect=dimension_chip_rect,
            validity_chip_rect=validity_chip_rect,
        ),
        footer=footer,
        separator_x=panel_x + menu_w + 8,
    )
