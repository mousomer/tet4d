from __future__ import annotations

import pygame

from tet4d.ui.pygame.ui_utils import wrap_text_lines

from .common import TopologyLabHitTarget
from .scene_state import (
    TOPOLOGY_LAB_WORKSPACES,
    TopologyLabState,
    WORKSPACE_LABELS,
    active_workspace_name,
    set_active_workspace,
)


def cycle_tool(state: TopologyLabState, step: int) -> None:
    current = TOPOLOGY_LAB_WORKSPACES.index(active_workspace_name(state))
    set_active_workspace(
        state,
        TOPOLOGY_LAB_WORKSPACES[(current + step) % len(TOPOLOGY_LAB_WORKSPACES)],
    )


def draw_tool_ribbon(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    active_workspace: str,
) -> list[TopologyLabHitTarget]:
    hits: list[TopologyLabHitTarget] = []
    count = len(TOPOLOGY_LAB_WORKSPACES)
    gap = 8
    button_w = max(72, (area.width - (count - 1) * gap) // count)
    for index, workspace in enumerate(TOPOLOGY_LAB_WORKSPACES):
        rect = pygame.Rect(area.x + index * (button_w + gap), area.y, button_w, area.height)
        color = (86, 98, 146) if workspace == active_workspace else (38, 44, 70)
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, (16, 18, 26), rect, 1, border_radius=8)
        lines = wrap_text_lines(
            fonts.hint_font,
            WORKSPACE_LABELS[workspace],
            rect.width - 10,
        )[:2]
        line_gap = 2
        total_h = len(lines) * fonts.hint_font.get_height() + max(0, len(lines) - 1) * line_gap
        y = rect.centery - total_h // 2
        for line in lines:
            surf = fonts.hint_font.render(
                line,
                True,
                (232, 236, 248),
            )
            surface.blit(surf, (rect.centerx - surf.get_width() // 2, y))
            y += fonts.hint_font.get_height() + line_gap
        hits.append(TopologyLabHitTarget("workspace_mode", workspace, rect.copy()))
    return hits


__all__ = ["cycle_tool", "draw_tool_ribbon"]
