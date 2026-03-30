from __future__ import annotations

import pygame

from tet4d.ui.pygame.topology_lab.common import TopologyLabHitTarget
from tet4d.ui.pygame.ui_utils import (
    button_border,
    button_text,
    draw_centered_wrapped_text,
    draw_fitted_text_line,
    draw_panel_frame,
    panel_bg,
    panel_border,
    wrap_text_lines,
)

_BLOCKED_BUTTON_COLOR = (74, 84, 118)


def build_preview_lines(preview: dict[str, object], *, dimension: int) -> list[str]:
    graph = preview["movement_graph"]
    lines = [
        f"Cells: {graph['cell_count']}  Edges: {graph['directed_edge_count']}",
        (
            "Traversals: "
            + f"{graph['boundary_traversal_count']}  Components: {graph['component_count']}"
        ),
    ]
    warnings = preview.get("warnings", ())
    if warnings:
        lines.append("Warnings")
        lines.extend(f"- {warning}" for warning in warnings[:3])
    basis_arrows = preview.get("basis_arrows", ())
    if basis_arrows:
        lines.append("Arrow basis")
        for arrow in basis_arrows[:2]:
            lines.append(str(arrow["crossing"]))
            for pair in arrow.get("basis_pairs", ())[: max(1, dimension - 1)]:
                lines.append(f"  {pair['from']} -> {pair['to']}")
    samples = preview.get("sample_boundary_traversals", ())
    if samples:
        lines.append("Samples")
        for sample in samples[:3]:
            lines.append(
                f"- {sample['source_boundary']} -> {sample['target_boundary']} via {sample['step']}"
            )
    return lines


def draw_preview_panel(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    title: str,
    lines: list[str],
) -> None:
    draw_panel_frame(
        surface,
        rect=area,
        fill_color=panel_bg(),
        border_color=panel_border(),
    )
    title_surf = draw_fitted_text_line(
        surface,
        font=fonts.hint_font,
        text=title,
        color=(220, 228, 250),
        max_width=area.width - 20,
        x=area.x + 10,
        y=area.y + 10,
    )
    y = area.y + 18 + title_surf.get_height()
    for index, line in enumerate(lines):
        color = (220, 228, 250) if index == 0 else (188, 198, 228)
        wrapped_lines = wrap_text_lines(fonts.hint_font, line, area.width - 20)
        for wrapped in wrapped_lines:
            surf = fonts.hint_font.render(wrapped, True, color)
            if y + surf.get_height() > area.bottom - 8:
                return
            surface.blit(surf, (area.x + 10, y))
            y += surf.get_height() + 4


def draw_probe_controls(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    step_options: list[dict[str, object]],
    title: str,
    active_color: tuple[int, int, int],
) -> list[TopologyLabHitTarget]:
    hits: list[TopologyLabHitTarget] = []
    if not step_options:
        return hits
    title_surf = draw_fitted_text_line(
        surface,
        font=fonts.hint_font,
        text=title,
        color=active_color,
        max_width=area.width - 4,
        x=area.x + 2,
        y=area.y,
    )
    buttons_area = area.copy()
    buttons_area.y += title_surf.get_height() + 6
    buttons_area.height = max(24, area.height - title_surf.get_height() - 6)
    columns = min(4, max(1, len(step_options)))
    rows = max(1, (len(step_options) + columns - 1) // columns)
    gap = 6
    button_w = max(54, (buttons_area.width - (columns - 1) * gap) // columns)
    button_h = max(16, (buttons_area.height - (rows - 1) * gap) // rows)
    for index, option in enumerate(step_options):
        row = index // columns
        col = index % columns
        rect = pygame.Rect(
            buttons_area.x + col * (button_w + gap),
            buttons_area.y + row * (button_h + gap),
            button_w,
            button_h,
        )
        blocked = bool(option.get("blocked", False))
        color = _BLOCKED_BUTTON_COLOR if blocked else active_color
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, button_border(), rect, 1, border_radius=8)
        draw_centered_wrapped_text(
            surface,
            rect=rect,
            font=fonts.hint_font,
            text=str(option.get("step", "?")),
            color=button_text(),
            max_lines=1,
            text_width_padding=6,
        )
        hits.append(
            TopologyLabHitTarget("probe_step", str(option.get("step", "")), rect.copy())
        )
    return hits


__all__ = ["build_preview_lines", "draw_preview_panel", "draw_probe_controls"]
