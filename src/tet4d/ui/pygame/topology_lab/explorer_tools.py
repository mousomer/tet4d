from __future__ import annotations

import pygame

from tet4d.ui.pygame.ui_utils import (
    button_active,
    button_bg,
    button_border,
    button_text,
    draw_centered_wrapped_text,
)

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
        color = button_active() if workspace == active_workspace else button_bg()
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, button_border(), rect, 1, border_radius=8)
        draw_centered_wrapped_text(
            surface,
            rect=rect,
            font=fonts.hint_font,
            text=WORKSPACE_LABELS[workspace],
            color=button_text(),
        )
        hits.append(TopologyLabHitTarget("workspace_mode", workspace, rect.copy()))
    return hits


__all__ = ["cycle_tool", "draw_tool_ribbon"]
