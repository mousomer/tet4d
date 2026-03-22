from __future__ import annotations

import pygame

from tet4d.engine.topology_explorer import BoundaryRef
from tet4d.ui.pygame.topology_lab.arrow_overlay import draw_glue_arrows
from tet4d.ui.pygame.topology_lab.common import (
    TopologyLabHitTarget,
    axis_color,
    boundary_fill_color,
)


def _board_rect(area: pygame.Rect, dims: tuple[int, ...]) -> tuple[pygame.Rect, int]:
    cols, rows = dims[0], dims[1]
    cell = max(16, min((area.width - 90) // max(1, cols), (area.height - 90) // max(1, rows)))
    board = pygame.Rect(0, 0, cell * cols, cell * rows)
    board.center = (area.centerx, area.centery + 12)
    return board, cell


def _edge_rects(board: pygame.Rect, edge: int) -> dict[str, pygame.Rect]:
    return {
        "x-": pygame.Rect(board.left - edge - 8, board.top, edge, board.height),
        "x+": pygame.Rect(board.right + 8, board.top, edge, board.height),
        "y-": pygame.Rect(board.left, board.bottom + 8, board.width, edge),
        "y+": pygame.Rect(board.left, board.top - edge - 8, board.width, edge),
    }


def _cell_rect(board: pygame.Rect, cell_size: int, coord: tuple[int, int]) -> pygame.Rect:
    return pygame.Rect(
        board.x + coord[0] * cell_size,
        board.y + coord[1] * cell_size,
        cell_size,
        cell_size,
    )


def _draw_grid(
    surface: pygame.Surface, board: pygame.Rect, cell_size: int, preview_dims: tuple[int, ...]
) -> None:
    pygame.draw.rect(surface, (18, 22, 38), board)
    pygame.draw.rect(surface, (92, 102, 138), board, 2)
    for x in range(preview_dims[0] + 1):
        xpos = board.x + x * cell_size
        pygame.draw.line(surface, (42, 50, 74), (xpos, board.y), (xpos, board.bottom), 1)
    for y in range(preview_dims[1] + 1):
        ypos = board.y + y * cell_size
        pygame.draw.line(surface, (42, 50, 74), (board.x, ypos), (board.right, ypos), 1)


def _draw_sandbox_cells(
    surface: pygame.Surface,
    *,
    board: pygame.Rect,
    cell_size: int,
    preview_dims: tuple[int, ...],
    sandbox_cells: tuple[tuple[int, ...], ...] | None,
    sandbox_valid: bool | None,
) -> None:
    if not sandbox_cells:
        return
    fill = (236, 198, 92) if sandbox_valid or sandbox_valid is None else (220, 92, 92)
    for coord in sandbox_cells:
        if len(coord) != 2:
            continue
        x, y = coord
        if not (0 <= x < preview_dims[0] and 0 <= y < preview_dims[1]):
            continue
        rect = _cell_rect(board, cell_size, (x, y)).inflate(-4, -4)
        pygame.draw.rect(surface, fill, rect, border_radius=4)


def _probe_centers(
    board: pygame.Rect,
    cell_size: int,
    preview_dims: tuple[int, ...],
    probe_path: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None,
) -> list[tuple[int, int]]:
    centers: list[tuple[int, int]] = []
    for coord in (probe_path or ())[-10:]:
        if len(coord) < 2:
            continue
        x = int(coord[0])
        y = int(coord[1])
        if not (0 <= x < preview_dims[0] and 0 <= y < preview_dims[1]):
            continue
        centers.append(_cell_rect(board, cell_size, (x, y)).center)
    return centers


def draw_probe_path_glyphs(
    surface: pygame.Surface,
    *,
    centers: list[tuple[int, int]],
    cell_size: int,
) -> None:
    if len(centers) >= 2:
        pygame.draw.lines(surface, (88, 170, 214), False, centers, 2)
    for center in centers[:-1]:
        pygame.draw.circle(surface, (120, 146, 176), center, max(3, cell_size // 7))


def _draw_probe_path(
    surface: pygame.Surface,
    *,
    board: pygame.Rect,
    cell_size: int,
    preview_dims: tuple[int, ...],
    probe_path: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None,
) -> None:
    draw_probe_path_glyphs(
        surface,
        centers=_probe_centers(board, cell_size, preview_dims, probe_path),
        cell_size=cell_size,
    )


def draw_probe_neighbor_glyphs(
    surface: pygame.Surface,
    *,
    centers: list[tuple[int, int]],
    cell_size: int,
) -> None:
    for center in centers:
        pygame.draw.circle(surface, (120, 146, 176), center, max(3, cell_size // 7))
        pygame.draw.circle(surface, (200, 214, 238), center, max(1, cell_size // 10))


def _draw_neighbor_markers(
    surface: pygame.Surface,
    *,
    board: pygame.Rect,
    cell_size: int,
    preview_dims: tuple[int, ...],
    neighbor_markers: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None,
) -> None:
    draw_probe_neighbor_glyphs(
        surface,
        centers=_probe_centers(board, cell_size, preview_dims, neighbor_markers),
        cell_size=cell_size,
    )


def draw_probe_center_glyph(
    surface: pygame.Surface,
    *,
    center: tuple[int, int],
    cell_size: int,
) -> None:
    pygame.draw.circle(surface, (112, 240, 255), center, max(5, cell_size // 4))
    pygame.draw.circle(surface, (12, 18, 26), center, max(2, cell_size // 7))


def _draw_probe(
    surface: pygame.Surface,
    *,
    board: pygame.Rect,
    cell_size: int,
    preview_dims: tuple[int, ...],
    probe_coord: tuple[int, ...] | None,
) -> None:
    if probe_coord is None or len(probe_coord) < 2:
        return
    x = int(probe_coord[0])
    y = int(probe_coord[1])
    if not (0 <= x < preview_dims[0] and 0 <= y < preview_dims[1]):
        return
    probe = _cell_rect(board, cell_size, (x, y))
    draw_probe_center_glyph(surface, center=probe.center, cell_size=cell_size)


def _draw_boundary_edges(
    surface: pygame.Surface,
    fonts,
    *,
    boundaries: tuple[BoundaryRef, ...],
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
    active_glue_ids: dict[str, str],
    edge_rects: dict[str, pygame.Rect],
    hovered_boundary_index: int | None,
    selected_boundary_index: int | None,
) -> list[TopologyLabHitTarget]:
    hits: list[TopologyLabHitTarget] = []
    for index, boundary in enumerate(boundaries):
        rect = edge_rects[boundary.label]
        fill = boundary_fill_color(boundary)
        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, (18, 20, 26), rect, 2, border_radius=8)
        if boundary == source_boundary:
            pygame.draw.rect(surface, (255, 226, 120), rect.inflate(6, 6), 2, border_radius=10)
        if boundary == target_boundary:
            pygame.draw.rect(surface, (112, 240, 255), rect.inflate(12, 12), 2, border_radius=12)
        if hovered_boundary_index == index:
            pygame.draw.rect(surface, (244, 244, 244), rect.inflate(2, 2), 1, border_radius=9)
        if selected_boundary_index == index:
            pygame.draw.rect(surface, (184, 204, 255), rect.inflate(10, 10), 2, border_radius=12)
        glue_id = active_glue_ids.get(boundary.label, "free")
        label = fonts.menu_font.render(boundary.label, True, (12, 18, 28))
        status = fonts.hint_font.render(glue_id, True, (24, 28, 40))
        axis_badge = fonts.hint_font.render(boundary.label[0].upper(), True, axis_color(boundary.axis))
        surface.blit(label, (rect.centerx - label.get_width() // 2, rect.y + 4))
        surface.blit(status, (rect.centerx - status.get_width() // 2, rect.bottom - status.get_height() - 4))
        surface.blit(axis_badge, (rect.right - axis_badge.get_width() - 6, rect.y + 4))
        hits.append(TopologyLabHitTarget("boundary_pick", index, rect.copy()))
    return hits


def _summary_parts(
    probe_coord: tuple[int, ...] | None,
    probe_path: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None,
    sandbox_cells: tuple[tuple[int, ...], ...] | None,
    sandbox_valid: bool | None,
    sandbox_message: str,
) -> list[str]:
    parts: list[str] = []
    if probe_coord is not None:
        parts.append(f"probe {list(probe_coord[:2])}")
    if probe_path:
        parts.append(f"trace {max(0, len(probe_path) - 1)}")
    if sandbox_cells:
        status = "valid" if sandbox_valid or sandbox_valid is None else "invalid"
        parts.append(f"sandbox {len(sandbox_cells)} cells ({status})")
    if sandbox_message:
        parts.append(sandbox_message)
    return parts


def _draw_summary(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    board: pygame.Rect,
    probe_coord: tuple[int, ...] | None,
    probe_path: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None,
    sandbox_cells: tuple[tuple[int, ...], ...] | None,
    sandbox_valid: bool | None,
    sandbox_message: str,
) -> None:
    summary_parts = _summary_parts(
        probe_coord,
        probe_path,
        sandbox_cells,
        sandbox_valid,
        sandbox_message,
    )
    if not summary_parts:
        return
    summary_y = min(area.bottom - 22, board.bottom + 18)
    summary = fonts.hint_font.render(" | ".join(summary_parts), True, (188, 198, 228))
    surface.blit(summary, (area.x + 6, summary_y))


def draw_scene(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    boundaries: tuple[BoundaryRef, ...],
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
    active_glue_ids: dict[str, str],
    basis_arrows: list[dict[str, object]] | tuple[dict[str, object], ...],
    preview_dims: tuple[int, ...],
    selected_glue_id: str | None = None,
    highlighted_glue_id: str | None = None,
    hovered_boundary_index: int | None = None,
    selected_boundary_index: int | None = None,
    probe_coord: tuple[int, ...] | None = None,
    probe_path: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None = None,
    neighbor_markers: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None = None,
    sandbox_cells: tuple[tuple[int, ...], ...] | None = None,
    sandbox_valid: bool | None = None,
    sandbox_message: str = "",
) -> list[TopologyLabHitTarget]:
    hits: list[TopologyLabHitTarget] = []
    title = fonts.hint_font.render("Explorer board", True, (220, 228, 250))
    surface.blit(title, (area.x, area.y - title.get_height() - 4))
    board, cell_size = _board_rect(area, preview_dims)
    _draw_grid(surface, board, cell_size, preview_dims)
    _draw_sandbox_cells(
        surface,
        board=board,
        cell_size=cell_size,
        preview_dims=preview_dims,
        sandbox_cells=sandbox_cells,
        sandbox_valid=sandbox_valid,
    )
    _draw_probe_path(
        surface,
        board=board,
        cell_size=cell_size,
        preview_dims=preview_dims,
        probe_path=probe_path,
    )
    _draw_neighbor_markers(
        surface,
        board=board,
        cell_size=cell_size,
        preview_dims=preview_dims,
        neighbor_markers=neighbor_markers,
    )
    _draw_probe(
        surface,
        board=board,
        cell_size=cell_size,
        preview_dims=preview_dims,
        probe_coord=probe_coord,
    )

    edge_rects = _edge_rects(board, max(18, min(28, cell_size)))
    hits.extend(
        _draw_boundary_edges(
            surface,
            fonts,
            boundaries=boundaries,
            source_boundary=source_boundary,
            target_boundary=target_boundary,
            active_glue_ids=active_glue_ids,
            edge_rects=edge_rects,
            hovered_boundary_index=hovered_boundary_index,
            selected_boundary_index=selected_boundary_index,
        )
    )
    hits.extend(
        draw_glue_arrows(
            surface,
            fonts,
            cards_by_label=edge_rects,
            basis_arrows=basis_arrows,
            clip_rect=area,
            selected_glue_id=selected_glue_id,
            highlighted_glue_id=highlighted_glue_id,
        )
    )
    _draw_summary(
        surface,
        fonts,
        area=area,
        board=board,
        probe_coord=probe_coord,
        probe_path=probe_path,
        sandbox_cells=sandbox_cells,
        sandbox_valid=sandbox_valid,
        sandbox_message=sandbox_message,
    )
    return hits


__all__ = ["draw_scene"]
