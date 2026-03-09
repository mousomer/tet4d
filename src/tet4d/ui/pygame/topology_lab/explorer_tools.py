from __future__ import annotations

import pygame

from tet4d.ui.pygame.ui_utils import fit_text

from .common import TopologyLabHitTarget
from .scene_state import TOOL_LABELS, TOPOLOGY_LAB_TOOLS, TopologyLabState, set_active_tool


def cycle_tool(state: TopologyLabState, step: int) -> None:
    current = TOPOLOGY_LAB_TOOLS.index(state.active_tool)
    set_active_tool(state, TOPOLOGY_LAB_TOOLS[(current + step) % len(TOPOLOGY_LAB_TOOLS)])


def draw_tool_ribbon(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    active_tool: str,
) -> list[TopologyLabHitTarget]:
    hits: list[TopologyLabHitTarget] = []
    count = len(TOPOLOGY_LAB_TOOLS)
    gap = 8
    button_w = max(72, (area.width - (count - 1) * gap) // count)
    for index, tool in enumerate(TOPOLOGY_LAB_TOOLS):
        rect = pygame.Rect(area.x + index * (button_w + gap), area.y, button_w, area.height)
        color = (86, 98, 146) if tool == active_tool else (38, 44, 70)
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, (16, 18, 26), rect, 1, border_radius=8)
        surf = fonts.hint_font.render(
            fit_text(fonts.hint_font, TOOL_LABELS[tool], rect.width - 10),
            True,
            (232, 236, 248),
        )
        surface.blit(surf, (rect.centerx - surf.get_width() // 2, rect.centery - surf.get_height() // 2))
        hits.append(TopologyLabHitTarget("tool_mode", tool, rect.copy()))
    return hits


__all__ = ["cycle_tool", "draw_tool_ribbon"]
