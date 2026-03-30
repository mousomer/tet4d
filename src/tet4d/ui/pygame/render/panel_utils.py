from __future__ import annotations

from collections.abc import Sequence

import pygame

from .control_helper import (
    ControlGroup,
    control_groups_for_dimension,
    draw_grouped_control_helper,
)
from .text_render_cache import render_text_cached


def _draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    alpha: int,
    radius: int,
    color: tuple[int, int, int],
) -> None:
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*color, alpha), panel.get_rect(), border_radius=radius)
    surface.blit(panel, rect.topleft)


def _merge_summary_into_main_group(
    *,
    header_lines: Sequence[str],
    control_groups: Sequence[ControlGroup],
) -> list[ControlGroup]:
    summary_rows = tuple(f"\t{line.strip()}\t" for line in header_lines if line.strip())
    groups = list(control_groups)
    if not summary_rows:
        return groups
    for idx, (name, rows) in enumerate(groups):
        if name == "Main":
            groups[idx] = (name, summary_rows + rows)
            return groups
    return [("Main", summary_rows), *groups]


def _join_sections(*sections: Sequence[str]) -> tuple[str, ...]:
    lines: list[str] = []
    for section in sections:
        section_lines = [str(line).strip() for line in section if str(line).strip()]
        if not section_lines:
            continue
        if lines:
            lines.append("")
        lines.extend(section_lines)
    return tuple(lines)


def _draw_meter(
    surface: pygame.Surface,
    *,
    panel_rect: pygame.Rect,
    fonts,
    start_y: int,
    label: str | None,
    value: float | None,
    hint: str | None,
) -> int:
    if not label or value is None:
        return start_y
    y = start_y + 2
    clamped = max(0.0, min(1.0, float(value)))
    label_surf = render_text_cached(
        font=fonts.hint_font,
        text=f"{label}: {int(round(clamped * 100.0))}%",
        color=(196, 208, 236),
    )
    surface.blit(label_surf, (panel_rect.x + 12, y))
    y += label_surf.get_height() + 4
    bar_rect = pygame.Rect(panel_rect.x + 12, y, panel_rect.width - 24, 10)
    pygame.draw.rect(surface, (30, 38, 62), bar_rect, border_radius=5)
    fill_rect = pygame.Rect(
        bar_rect.x,
        bar_rect.y,
        max(2, int(bar_rect.width * clamped)),
        bar_rect.height,
    )
    pygame.draw.rect(surface, (88, 168, 236), fill_rect, border_radius=5)
    pygame.draw.rect(surface, (130, 148, 186), bar_rect, 1, border_radius=5)
    y += bar_rect.height + 4
    if hint:
        hint_surf = render_text_cached(
            font=fonts.hint_font,
            text=str(hint),
            color=(168, 180, 212),
        )
        surface.blit(hint_surf, (panel_rect.x + 12, y))
        y += hint_surf.get_height() + 4
    return y


def _compute_controls_rect(
    *,
    panel_rect: pygame.Rect,
    controls_top: int,
    reserve_bottom: int,
) -> pygame.Rect:
    controls_bottom_limit = panel_rect.bottom - reserve_bottom - 8
    available_h = max(0, controls_bottom_limit - controls_top)
    controls_h = max(0, int(available_h))
    return pygame.Rect(
        panel_rect.x + 6,
        controls_top,
        panel_rect.width - 12,
        controls_h,
    )


def _stats_group_rows(lines: Sequence[str]) -> tuple[str, ...]:
    rows: list[str] = []
    if not lines:
        return ("\tno runtime stats\t",)
    for line in lines:
        text = str(line)
        if not text.strip():
            rows.append("\t\t")
            continue
        rows.append(f"\t{text}\t")
    return tuple(rows)


def _append_stats_group(
    *,
    control_groups: Sequence[ControlGroup],
    stats_lines: Sequence[str],
) -> list[ControlGroup]:
    groups = list(control_groups)
    groups.append(("Stats", _stats_group_rows(stats_lines)))
    return groups


def draw_unified_game_side_panel(
    surface: pygame.Surface,
    *,
    panel_rect: pygame.Rect,
    fonts,
    title: str,
    score: int,
    lines_cleared: int,
    speed_level: int,
    dimension: int,
    include_exploration: bool,
    data_lines: Sequence[str] = (),
    bot_lines: Sequence[str] = (),
    analysis_lines: Sequence[str] = (),
    game_over: bool = False,
    meter_label: str | None = None,
    meter_value: float | None = None,
    meter_hint: str | None = None,
) -> None:
    _draw_panel(surface, panel_rect, alpha=140, radius=12, color=(0, 0, 0))
    header_lines = (
        str(title),
        f"Score: {int(score)}",
        f"Lines: {int(lines_cleared)}",
        f"Speed level: {int(speed_level)}",
    )
    low_priority_lines = _join_sections(data_lines, bot_lines, analysis_lines)
    groups = _merge_summary_into_main_group(
        header_lines=header_lines,
        control_groups=control_groups_for_dimension(
            max(2, min(4, int(dimension))),
            include_exploration=bool(include_exploration),
            unified_structure=True,
        ),
    )
    groups = _append_stats_group(
        control_groups=groups,
        stats_lines=low_priority_lines,
    )
    y = _draw_meter(
        surface,
        panel_rect=panel_rect,
        fonts=fonts,
        start_y=panel_rect.y + 10,
        label=meter_label,
        value=meter_value,
        hint=meter_hint,
    )
    controls_top = y + 4
    reserve_bottom = 26 if game_over else 0
    controls_rect = _compute_controls_rect(
        panel_rect=panel_rect,
        controls_top=controls_top,
        reserve_bottom=reserve_bottom,
    )
    draw_grouped_control_helper(
        surface,
        groups=groups,
        rect=controls_rect,
        panel_font=fonts.panel_font,
        hint_font=fonts.hint_font,
    )
    if game_over:
        over = render_text_cached(
            font=fonts.panel_font,
            text="GAME OVER",
            color=(255, 80, 80),
        )
        surface.blit(over, (panel_rect.x + 12, panel_rect.bottom - 26))
