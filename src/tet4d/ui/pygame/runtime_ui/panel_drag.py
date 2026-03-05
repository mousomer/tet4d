from __future__ import annotations

import pygame


def helper_panel_rect_for_surface(
    *,
    surface_size: tuple[int, int],
    offset: tuple[int, int],
    side_panel: int,
    margin: int,
) -> pygame.Rect:
    width, height = surface_size
    rect = pygame.Rect(
        width - side_panel - margin,
        margin,
        side_panel,
        height - (2 * margin),
    )
    rect.move_ip(int(offset[0]), int(offset[1]))
    rect.x = max(0, min(width - rect.width, rect.x))
    rect.y = max(0, min(height - rect.height, rect.y))
    return rect


class PanelDragMixin:
    panel_drag_target: str | None
    panel_drag_origin_mouse: tuple[int, int] | None
    panel_drag_origin_offset: tuple[int, int] | None
    helper_panel_offset: tuple[int, int]
    tutorial_panel_offset: tuple[int, int]

    def _panel_rects(self) -> tuple[pygame.Rect | None, pygame.Rect | None]:
        raise NotImplementedError

    def _reset_panel_drag_state(self) -> None:
        self.panel_drag_target = None
        self.panel_drag_origin_mouse = None
        self.panel_drag_origin_offset = None

    def _panel_contains_point(self, pos: tuple[int, int]) -> bool:
        helper_rect, tutorial_rect = self._panel_rects()
        return bool(
            (helper_rect is not None and helper_rect.collidepoint(pos))
            or (tutorial_rect is not None and tutorial_rect.collidepoint(pos))
        )

    def _start_panel_drag(self, pos: tuple[int, int]) -> bool:
        helper_rect, tutorial_rect = self._panel_rects()
        if tutorial_rect is not None and tutorial_rect.collidepoint(pos):
            self.panel_drag_target = "tutorial"
            self.panel_drag_origin_mouse = pos
            self.panel_drag_origin_offset = tuple(self.tutorial_panel_offset)
            return True
        if helper_rect is not None and helper_rect.collidepoint(pos):
            self.panel_drag_target = "helper"
            self.panel_drag_origin_mouse = pos
            self.panel_drag_origin_offset = tuple(self.helper_panel_offset)
            return True
        self._reset_panel_drag_state()
        return False

    def _update_panel_drag(self, pos: tuple[int, int]) -> bool:
        if not self.panel_drag_target:
            return False
        if self.panel_drag_origin_mouse is None or self.panel_drag_origin_offset is None:
            self._reset_panel_drag_state()
            return False
        dx = int(pos[0]) - int(self.panel_drag_origin_mouse[0])
        dy = int(pos[1]) - int(self.panel_drag_origin_mouse[1])
        next_offset = (
            int(self.panel_drag_origin_offset[0]) + dx,
            int(self.panel_drag_origin_offset[1]) + dy,
        )
        if self.panel_drag_target == "tutorial":
            self.tutorial_panel_offset = next_offset
        elif self.panel_drag_target == "helper":
            self.helper_panel_offset = next_offset
        return True

    def _stop_panel_drag(self) -> bool:
        if not self.panel_drag_target:
            return False
        self._reset_panel_drag_state()
        return True

    def _handle_panel_drag_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEWHEEL:
            return self._panel_contains_point(tuple(pygame.mouse.get_pos()))
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._start_panel_drag(tuple(event.pos))
        if event.type == pygame.MOUSEMOTION:
            return self._update_panel_drag(tuple(event.pos))
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            return self._stop_panel_drag()
        return False

