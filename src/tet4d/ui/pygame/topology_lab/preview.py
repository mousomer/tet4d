from __future__ import annotations

import pygame

from tet4d.ui.pygame.topology_lab.common import TopologyLabHitTarget
from tet4d.ui.pygame.ui_utils import fit_text


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
    pygame.draw.rect(surface, (18, 22, 38), area, border_radius=10)
    pygame.draw.rect(surface, (76, 84, 112), area, 1, border_radius=10)
    title_surf = fonts.hint_font.render(title, True, (220, 228, 250))
    surface.blit(title_surf, (area.x + 10, area.y + 10))
    y = area.y + 18 + title_surf.get_height()
    for index, line in enumerate(lines):
        color = (220, 228, 250) if index == 0 else (188, 198, 228)
        text = fit_text(fonts.hint_font, line, area.width - 20)
        surf = fonts.hint_font.render(text, True, color)
        if y + surf.get_height() > area.bottom - 8:
            break
        surface.blit(surf, (area.x + 10, y))
        y += surf.get_height() + 4


def draw_probe_controls(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    step_options: list[dict[str, object]],
) -> list[TopologyLabHitTarget]:
    hits: list[TopologyLabHitTarget] = []
    if not step_options:
        return hits
    columns = min(4, max(1, len(step_options)))
    rows = max(1, (len(step_options) + columns - 1) // columns)
    gap = 8
    button_w = max(54, (area.width - (columns - 1) * gap) // columns)
    button_h = max(24, (area.height - (rows - 1) * gap) // rows)
    for index, option in enumerate(step_options):
        row = index // columns
        col = index % columns
        rect = pygame.Rect(
            area.x + col * (button_w + gap),
            area.y + row * (button_h + gap),
            button_w,
            button_h,
        )
        blocked = bool(option.get("blocked", False))
        color = (74, 84, 118) if blocked else (56, 92, 130)
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, (16, 18, 26), rect, 1, border_radius=8)
        text_surf = fonts.hint_font.render(
            str(option.get("step", "?")), True, (232, 236, 248)
        )
        surface.blit(
            text_surf,
            (
                rect.centerx - text_surf.get_width() // 2,
                rect.centery - text_surf.get_height() // 2,
            ),
        )
        hits.append(
            TopologyLabHitTarget("probe_step", str(option.get("step", "")), rect.copy())
        )
    return hits


__all__ = ["build_preview_lines", "draw_preview_panel", "draw_probe_controls"]
