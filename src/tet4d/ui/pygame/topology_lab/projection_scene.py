from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import ceil
from typing import Iterable, Sequence

import pygame

from tet4d.engine.topology_explorer import (
    BLOCKED_MOVE,
    CELLWISE_DEFORMATION,
    RIGID_TRANSFORM,
    BoundaryRef,
    CellStepResult,
    ExplorerTopologyProfile,
    PieceStepResult,
    build_explorer_transport_resolver,
    movement_steps_for_dimension,
)
from tet4d.ui.pygame.ui_utils import fit_text

from .common import (
    TopologyLabHitTarget,
    axis_color,
    boundary_fill_color,
)

_BACKGROUND = (18, 22, 38)
_BORDER = (76, 84, 112)
_GRID = (42, 50, 74)
_TEXT = (220, 228, 250)
_MUTED = (168, 178, 208)
_SELECTED = (112, 240, 255)
_SANDBOX = (236, 198, 92)
_INVALID = (220, 92, 92)
_DEFORMATION = (214, 122, 228)
_PANEL_GAP = 10
_RIBBON_GAP = 6
_HEADER_HEIGHT = 22
_RIBBON_PADDING = 6
_CELL_PICK_KIND = "projection_cell"
_PANEL_KIND = "projection_panel"
_SANDBOX_TOOL = "piece_sandbox"


@dataclass(frozen=True)
class _ProjectionPanel:
    axes: tuple[int, int]
    rect: pygame.Rect

    @property
    def label(self) -> str:
        return projection_label(self.axes)


def projection_pairs_for_dimension(
    dimension: int,
) -> tuple[tuple[int, int], ...]:
    dim = int(dimension)
    if dim == 3:
        return ((0, 1), (0, 2), (1, 2))
    if dim == 4:
        return ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    return tuple(tuple(pair) for pair in combinations(range(dim), 2))


def projection_label(axes: Sequence[int]) -> str:
    return "".join("xyzw"[int(axis)] for axis in axes)


def projection_hidden_axes(
    dimension: int,
    axes: Sequence[int],
) -> tuple[int, ...]:
    visible = {int(axis) for axis in axes}
    return tuple(axis for axis in range(int(dimension)) if axis not in visible)


def projection_hidden_label(
    dimension: int,
    axes: Sequence[int],
    selected_coord: Sequence[int],
    *,
    slab_radius: int = 0,
) -> str:
    hidden_axes = projection_hidden_axes(dimension, axes)
    if not hidden_axes:
        return "visible: all dims"
    pieces = [f"{'xyzw'[axis]}={int(selected_coord[axis])}" for axis in hidden_axes]
    if int(slab_radius) > 0:
        return f"hidden {'  '.join(pieces)}  slab +/-{int(slab_radius)}"
    return f"hidden {'  '.join(pieces)}  slice"


def _panel_grid_rect(
    panel_rect: pygame.Rect,
    dims: tuple[int, ...],
    axes: tuple[int, int],
) -> tuple[pygame.Rect, int]:
    cols = max(1, int(dims[axes[0]]))
    rows = max(1, int(dims[axes[1]]))
    content = panel_rect.inflate(-12, -12)
    content.y += _HEADER_HEIGHT
    content.height = max(44, content.height - (_HEADER_HEIGHT + 8))
    cell = max(
        10,
        min(
            (content.width - 4) // cols,
            (content.height - 4) // rows,
        ),
    )
    board = pygame.Rect(0, 0, cell * cols, cell * rows)
    board.center = (content.centerx, content.centery + 2)
    return board, cell


def _draw_panel_frame(
    surface: pygame.Surface,
    fonts,
    *,
    panel: _ProjectionPanel,
    selected_coord: tuple[int, ...],
    slab_radius: int,
) -> None:
    pygame.draw.rect(surface, _BACKGROUND, panel.rect, border_radius=10)
    pygame.draw.rect(surface, _BORDER, panel.rect, 1, border_radius=10)
    title = fonts.hint_font.render(panel.label, True, _TEXT)
    hidden = fonts.hint_font.render(
        fit_text(
            fonts.hint_font,
            projection_hidden_label(
                len(selected_coord),
                panel.axes,
                selected_coord,
                slab_radius=slab_radius,
            ),
            panel.rect.width - 16,
        ),
        True,
        _MUTED,
    )
    surface.blit(title, (panel.rect.x + 8, panel.rect.y + 6))
    surface.blit(hidden, (panel.rect.x + 8, panel.rect.y + 8 + title.get_height()))


def _draw_grid(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: int,
    dims: tuple[int, ...],
    axes: tuple[int, int],
) -> None:
    pygame.draw.rect(surface, (14, 18, 28), board_rect)
    pygame.draw.rect(surface, (92, 102, 138), board_rect, 2)
    for column in range(int(dims[axes[0]]) + 1):
        xpos = board_rect.x + column * cell_size
        pygame.draw.line(
            surface, _GRID, (xpos, board_rect.y), (xpos, board_rect.bottom), 1
        )
    for row in range(int(dims[axes[1]]) + 1):
        ypos = board_rect.y + row * cell_size
        pygame.draw.line(
            surface, _GRID, (board_rect.x, ypos), (board_rect.right, ypos), 1
        )


def _coord_matches_slice(
    coord: Sequence[int],
    *,
    dimension: int,
    axes: tuple[int, int],
    selected_coord: Sequence[int],
    slab_radius: int,
) -> bool:
    for axis in projection_hidden_axes(dimension, axes):
        if abs(int(coord[axis]) - int(selected_coord[axis])) > int(slab_radius):
            return False
    return True


def _full_coord_for_panel_cell(
    *,
    axes: tuple[int, int],
    pair_coord: tuple[int, int],
    selected_coord: Sequence[int],
) -> tuple[int, ...]:
    full = list(int(value) for value in selected_coord)
    full[axes[0]] = int(pair_coord[0])
    full[axes[1]] = int(pair_coord[1])
    return tuple(full)


def _cell_rect(
    board_rect: pygame.Rect,
    cell_size: int,
    pair_coord: tuple[int, int],
) -> pygame.Rect:
    return pygame.Rect(
        board_rect.x + int(pair_coord[0]) * cell_size,
        board_rect.y + int(pair_coord[1]) * cell_size,
        cell_size,
        cell_size,
    )


def _draw_cell_hits(
    *,
    board_rect: pygame.Rect,
    cell_size: int,
    dims: tuple[int, ...],
    axes: tuple[int, int],
    selected_coord: tuple[int, ...],
) -> list[TopologyLabHitTarget]:
    hits: list[TopologyLabHitTarget] = []
    for x_value in range(int(dims[axes[0]])):
        for y_value in range(int(dims[axes[1]])):
            full_coord = _full_coord_for_panel_cell(
                axes=axes,
                pair_coord=(x_value, y_value),
                selected_coord=selected_coord,
            )
            hits.append(
                TopologyLabHitTarget(
                    _CELL_PICK_KIND,
                    full_coord,
                    _cell_rect(board_rect, cell_size, (x_value, y_value)),
                )
            )
    return hits


def _pair_coord(coord: Sequence[int], axes: tuple[int, int]) -> tuple[int, int]:
    return int(coord[axes[0]]), int(coord[axes[1]])


def _draw_selected_cell(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: int,
    axes: tuple[int, int],
    selected_coord: tuple[int, ...],
) -> None:
    rect = _cell_rect(board_rect, cell_size, _pair_coord(selected_coord, axes)).inflate(
        -4, -4
    )
    pygame.draw.rect(surface, _SELECTED, rect, 2, border_radius=5)
    pygame.draw.circle(surface, _SELECTED, rect.center, max(3, cell_size // 6))


def _draw_probe_path(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: int,
    axes: tuple[int, int],
    dimension: int,
    selected_coord: tuple[int, ...],
    probe_path: Iterable[Sequence[int]] | None,
    slab_radius: int,
) -> None:
    points: list[tuple[int, int]] = []
    for coord in probe_path or ():
        if not _coord_matches_slice(
            coord,
            dimension=dimension,
            axes=axes,
            selected_coord=selected_coord,
            slab_radius=slab_radius,
        ):
            continue
        rect = _cell_rect(board_rect, cell_size, _pair_coord(coord, axes))
        points.append(rect.center)
    if len(points) >= 2:
        pygame.draw.lines(surface, (88, 170, 214), False, points[-8:], 2)
    for point in points[-8:-1]:
        pygame.draw.circle(surface, (120, 146, 176), point, max(3, cell_size // 7))


def _draw_sandbox_cells(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: int,
    axes: tuple[int, int],
    dimension: int,
    selected_coord: tuple[int, ...],
    sandbox_cells: tuple[tuple[int, ...], ...] | None,
    sandbox_valid: bool | None,
    slab_radius: int,
) -> None:
    if not sandbox_cells:
        return
    fill = _SANDBOX if sandbox_valid or sandbox_valid is None else _INVALID
    for coord in sandbox_cells:
        if not _coord_matches_slice(
            coord,
            dimension=dimension,
            axes=axes,
            selected_coord=selected_coord,
            slab_radius=slab_radius,
        ):
            continue
        rect = _cell_rect(board_rect, cell_size, _pair_coord(coord, axes)).inflate(
            -4, -4
        )
        pygame.draw.rect(surface, fill, rect, border_radius=4)
        pygame.draw.rect(surface, (18, 20, 26), rect, 1, border_radius=4)


def _step_preview_color(
    step_axis: int,
    traversal_glue_id: str | None,
) -> tuple[int, int, int]:
    base = axis_color(step_axis)
    if traversal_glue_id is None:
        return base
    return tuple(min(255, channel + 34) for channel in base)


def _draw_cell_step_previews(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: int,
    axes: tuple[int, int],
    selected_coord: tuple[int, ...],
    cell_steps: tuple[CellStepResult, ...],
    focused_glue_id: str | None,
    dimension: int,
    slab_radius: int,
) -> list[str]:
    legend: list[str] = []
    source_rect = _cell_rect(board_rect, cell_size, _pair_coord(selected_coord, axes))
    for step_result in cell_steps:
        step_label = step_result.step.label
        if step_result.target is None:
            legend.append(f"{step_label} blocked")
            continue
        traversal = step_result.traversal
        legend.append(
            f"{step_label} -> {list(step_result.target)}"
            + (f" via {traversal.glue_id}" if traversal is not None else "")
        )
        if not _coord_matches_slice(
            step_result.target,
            dimension=dimension,
            axes=axes,
            selected_coord=selected_coord,
            slab_radius=slab_radius,
        ):
            continue
        target_rect = _cell_rect(
            board_rect, cell_size, _pair_coord(step_result.target, axes)
        ).inflate(-6, -6)
        color = _step_preview_color(
            step_result.step.axis,
            None if traversal is None else traversal.glue_id,
        )
        width = 3 if traversal is not None else 2
        pygame.draw.line(surface, color, source_rect.center, target_rect.center, width)
        pygame.draw.rect(surface, color, target_rect, width, border_radius=4)
        if traversal is not None:
            seam_color = _SELECTED
            if traversal.glue_id == focused_glue_id:
                seam_color = (255, 226, 120)
            pygame.draw.circle(
                surface,
                seam_color,
                target_rect.center,
                max(4, cell_size // 7),
            )
    return legend


def _piece_result_style(
    result: PieceStepResult,
) -> tuple[tuple[int, int, int], str]:
    if result.kind == BLOCKED_MOVE:
        return _INVALID, "blocked"
    if result.kind == CELLWISE_DEFORMATION:
        if result.rigidly_coherent:
            return _SELECTED, "rigid/chart-split"
        return _DEFORMATION, "cellwise"
    if result.kind == RIGID_TRANSFORM:
        return _SELECTED, "rigid"
    return (126, 214, 146), "free"


def _draw_piece_step_previews(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: int,
    axes: tuple[int, int],
    selected_coord: tuple[int, ...],
    piece_steps: tuple[tuple[str, PieceStepResult], ...],
    dimension: int,
    slab_radius: int,
) -> list[str]:
    legend: list[str] = []
    for step_label, result in piece_steps:
        color, status = _piece_result_style(result)
        legend.append(f"{step_label} {status}")
        if result.moved_cells is None:
            continue
        visible_cells = [
            coord
            for coord in result.moved_cells
            if _coord_matches_slice(
                coord,
                dimension=dimension,
                axes=axes,
                selected_coord=selected_coord,
                slab_radius=slab_radius,
            )
        ]
        for coord in visible_cells:
            rect = _cell_rect(board_rect, cell_size, _pair_coord(coord, axes)).inflate(
                -7,
                -7,
            )
            pygame.draw.rect(surface, color, rect, 2, border_radius=4)
    return legend


def _boundary_edge_rect(
    board_rect: pygame.Rect,
    boundary: BoundaryRef,
    *,
    axes: tuple[int, int],
) -> pygame.Rect | None:
    edge = 6
    if boundary.axis == axes[0]:
        if boundary.side == "-":
            return pygame.Rect(
                board_rect.left - edge - 2, board_rect.top, edge, board_rect.height
            )
        return pygame.Rect(
            board_rect.right + 2, board_rect.top, edge, board_rect.height
        )
    if boundary.axis == axes[1]:
        if boundary.side == "-":
            return pygame.Rect(
                board_rect.x, board_rect.y - edge - 2, board_rect.width, edge
            )
        return pygame.Rect(board_rect.x, board_rect.bottom + 2, board_rect.width, edge)
    return None


def _draw_focus_boundaries(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    axes: tuple[int, int],
    focus_boundaries: tuple[BoundaryRef, ...],
) -> None:
    for boundary in focus_boundaries:
        edge_rect = _boundary_edge_rect(board_rect, boundary, axes=axes)
        if edge_rect is None:
            continue
        pygame.draw.rect(
            surface,
            boundary_fill_color(boundary),
            edge_rect,
            border_radius=4,
        )


def _layout_projection_panels(
    area: pygame.Rect,
    *,
    dimension: int,
    header_height: int,
) -> tuple[list[_ProjectionPanel], pygame.Rect | None]:
    content = pygame.Rect(
        area.x,
        area.y + header_height,
        area.width,
        max(80, area.height - header_height),
    )
    panels: list[_ProjectionPanel] = []
    info_rect: pygame.Rect | None = None
    pairs = projection_pairs_for_dimension(dimension)
    if dimension == 3:
        columns = 2
        rows = 2
        cell_width = (content.width - _PANEL_GAP) // columns
        cell_height = (content.height - _PANEL_GAP) // rows
        cells: list[pygame.Rect] = []
        for row in range(rows):
            for column in range(columns):
                cells.append(
                    pygame.Rect(
                        content.x + column * (cell_width + _PANEL_GAP),
                        content.y + row * (cell_height + _PANEL_GAP),
                        cell_width,
                        cell_height,
                    )
                )
        for index, pair in enumerate(pairs):
            panels.append(_ProjectionPanel(pair, cells[index]))
        info_rect = cells[-1]
        return panels, info_rect

    columns = 3
    rows = max(1, ceil(len(pairs) / columns))
    cell_width = (content.width - _PANEL_GAP * (columns - 1)) // columns
    cell_height = (content.height - _PANEL_GAP * (rows - 1)) // rows
    for index, pair in enumerate(pairs):
        row = index // columns
        column = index % columns
        panels.append(
            _ProjectionPanel(
                pair,
                pygame.Rect(
                    content.x + column * (cell_width + _PANEL_GAP),
                    content.y + row * (cell_height + _PANEL_GAP),
                    cell_width,
                    cell_height,
                ),
            )
        )
    return panels, None


def _draw_wrapped_pills(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    items: Sequence[
        tuple[str, tuple[int, int, int], tuple[int, int, int], str, object]
    ],
) -> list[TopologyLabHitTarget]:
    hits: list[TopologyLabHitTarget] = []
    x_pos = area.x
    y_pos = area.y
    row_height = fonts.hint_font.get_height() + 8
    for label, fill, outline, kind, value in items:
        width = max(42, fonts.hint_font.size(label)[0] + 14)
        if x_pos + width > area.right:
            x_pos = area.x
            y_pos += row_height + _RIBBON_GAP
        rect = pygame.Rect(x_pos, y_pos, width, row_height)
        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, outline, rect, 1, border_radius=8)
        text = fonts.hint_font.render(label, True, (12, 18, 28))
        surface.blit(
            text,
            (
                rect.x + (rect.width - text.get_width()) // 2,
                rect.y + (rect.height - text.get_height()) // 2,
            ),
        )
        hits.append(TopologyLabHitTarget(kind, value, rect.copy()))
        x_pos = rect.right + _RIBBON_GAP
    return hits


def _focus_boundaries_for_glue(
    profile: ExplorerTopologyProfile | None,
    *,
    glue_id: str | None,
) -> tuple[BoundaryRef, ...]:
    if profile is None or not glue_id:
        return ()
    for glue in profile.gluings:
        if glue.glue_id == glue_id:
            return (glue.source, glue.target)
    return ()


def _resolve_cell_previews(
    *,
    profile: ExplorerTopologyProfile | None,
    dims: tuple[int, ...],
    coord: tuple[int, ...],
) -> tuple[CellStepResult, ...]:
    if profile is None:
        return ()
    try:
        resolver = build_explorer_transport_resolver(profile, dims)
    except ValueError:
        return ()
    return tuple(
        resolver.resolve_cell_step(coord, step)
        for step in movement_steps_for_dimension(profile.dimension)
    )


def _resolve_piece_previews(
    *,
    profile: ExplorerTopologyProfile | None,
    dims: tuple[int, ...],
    sandbox_cells: tuple[tuple[int, ...], ...] | None,
) -> tuple[tuple[str, PieceStepResult], ...]:
    if profile is None or not sandbox_cells:
        return ()
    try:
        resolver = build_explorer_transport_resolver(profile, dims)
    except ValueError:
        return ()
    previews: list[tuple[str, PieceStepResult]] = []
    for step in movement_steps_for_dimension(profile.dimension):
        previews.append((step.label, resolver.resolve_piece_step(sandbox_cells, step)))
    return tuple(previews)


def _draw_projection_legend(
    surface: pygame.Surface,
    fonts,
    *,
    panel_rect: pygame.Rect,
    lines: Sequence[str],
    color: tuple[int, int, int] = _MUTED,
) -> None:
    if not lines:
        return
    y_pos = panel_rect.bottom - 8
    for line in reversed(tuple(lines)[:3]):
        text = fonts.hint_font.render(
            fit_text(fonts.hint_font, line, panel_rect.width - 16),
            True,
            color,
        )
        y_pos -= text.get_height()
        surface.blit(text, (panel_rect.x + 8, y_pos))
        y_pos -= 2


def _draw_info_panel(
    surface: pygame.Surface,
    fonts,
    *,
    rect: pygame.Rect,
    selected_coord: tuple[int, ...],
    focused_glue_id: str | None,
    active_tool: str | None,
    sandbox_valid: bool | None,
    sandbox_message: str,
    cell_legend: Sequence[str],
    piece_legend: Sequence[str],
) -> None:
    pygame.draw.rect(surface, _BACKGROUND, rect, border_radius=10)
    pygame.draw.rect(surface, _BORDER, rect, 1, border_radius=10)
    lines = [
        "Projection sync",
        f"Selected cell: {list(selected_coord)}",
        f"Tool: {str(active_tool or '').replace('_', ' ') or 'inspect'}",
    ]
    if focused_glue_id:
        lines.append(f"Seam focus: {focused_glue_id}")
    if sandbox_valid is not None:
        lines.append("Sandbox: " + ("valid" if sandbox_valid else "rejected"))
    if sandbox_message:
        lines.append(sandbox_message)
    if piece_legend:
        lines.append("Moves: " + "  ".join(piece_legend[:3]))
    elif cell_legend:
        lines.append("Neighbors: " + "  ".join(cell_legend[:3]))
    y_pos = rect.y + 10
    for index, line in enumerate(lines):
        text = fonts.hint_font.render(
            fit_text(fonts.hint_font, line, rect.width - 16),
            True,
            _TEXT if index == 0 else _MUTED,
        )
        surface.blit(text, (rect.x + 8, y_pos))
        y_pos += text.get_height() + 4


def _selected_projection_coord(
    dimension: int,
    probe_coord: tuple[int, ...] | None,
) -> tuple[int, ...]:
    if probe_coord is not None and len(probe_coord) == dimension:
        return tuple(int(value) for value in probe_coord)
    return tuple(0 for _ in range(dimension))


def _draw_projection_heading(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    dimension: int,
    selected_coord: tuple[int, ...],
) -> None:
    title = fonts.hint_font.render(
        f"{dimension}D synchronized projections",
        True,
        _TEXT,
    )
    subtitle = fonts.hint_font.render(
        fit_text(
            fonts.hint_font,
            (
                f"Selected {list(selected_coord)}  hidden slices stay explicit "
                "in every panel"
            ),
            area.width - 12,
        ),
        True,
        _MUTED,
    )
    surface.blit(title, (area.x, area.y - title.get_height() - 4))
    surface.blit(
        subtitle,
        (area.x + title.get_width() + 10, area.y - subtitle.get_height() - 4),
    )


def _boundary_pill_items(
    *,
    boundaries: tuple[BoundaryRef, ...],
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
    active_glue_ids: dict[str, str],
    hovered_boundary_index: int | None,
    selected_boundary_index: int | None,
) -> list[tuple[str, tuple[int, int, int], tuple[int, int, int], str, object]]:
    items: list[
        tuple[str, tuple[int, int, int], tuple[int, int, int], str, object]
    ] = []
    for index, boundary in enumerate(boundaries):
        outline = axis_color(boundary.axis)
        fill = boundary_fill_color(boundary)
        if boundary == source_boundary:
            outline = (255, 226, 120)
        elif boundary == target_boundary:
            outline = _SELECTED
        elif selected_boundary_index == index:
            outline = (184, 204, 255)
        elif hovered_boundary_index == index:
            outline = (248, 248, 248)
        status = active_glue_ids.get(boundary.label, "free")
        items.append(
            (
                f"{boundary.label}:{status}",
                fill,
                outline,
                "boundary_pick",
                index,
            )
        )
    return items


def _seam_pill_items(
    *,
    active_glue_ids: dict[str, str],
    selected_glue_id: str | None,
    highlighted_glue_id: str | None,
) -> list[tuple[str, tuple[int, int, int], tuple[int, int, int], str, object]]:
    items: list[
        tuple[str, tuple[int, int, int], tuple[int, int, int], str, object]
    ] = []
    seen_glues: set[str] = set()
    for glue_id in active_glue_ids.values():
        if glue_id == "free" or glue_id in seen_glues:
            continue
        seen_glues.add(glue_id)
        outline = (192, 206, 255)
        if glue_id == selected_glue_id:
            outline = (255, 226, 120)
        elif glue_id == highlighted_glue_id:
            outline = _SELECTED
        items.append((glue_id, (30, 36, 56), outline, "glue_pick", glue_id))
    return items


def _draw_projection_ribbon(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    boundaries: tuple[BoundaryRef, ...],
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
    active_glue_ids: dict[str, str],
    hovered_boundary_index: int | None,
    selected_boundary_index: int | None,
    selected_glue_id: str | None,
    highlighted_glue_id: str | None,
) -> list[TopologyLabHitTarget]:
    pygame.draw.rect(surface, (16, 20, 34), area, border_radius=10)
    pygame.draw.rect(surface, _BORDER, area, 1, border_radius=10)
    boundary_area = pygame.Rect(
        area.x + _RIBBON_PADDING,
        area.y + _RIBBON_PADDING,
        area.width - (_RIBBON_PADDING * 2),
        (area.height - (_RIBBON_PADDING * 2) - _RIBBON_GAP) // 2,
    )
    seam_area = pygame.Rect(
        area.x + _RIBBON_PADDING,
        boundary_area.bottom + _RIBBON_GAP,
        area.width - (_RIBBON_PADDING * 2),
        area.bottom - boundary_area.bottom - (_RIBBON_GAP + _RIBBON_PADDING),
    )
    hits = _draw_wrapped_pills(
        surface,
        fonts,
        area=boundary_area,
        items=_boundary_pill_items(
            boundaries=boundaries,
            source_boundary=source_boundary,
            target_boundary=target_boundary,
            active_glue_ids=active_glue_ids,
            hovered_boundary_index=hovered_boundary_index,
            selected_boundary_index=selected_boundary_index,
        ),
    )
    hits.extend(
        _draw_wrapped_pills(
            surface,
            fonts,
            area=seam_area,
            items=_seam_pill_items(
                active_glue_ids=active_glue_ids,
                selected_glue_id=selected_glue_id,
                highlighted_glue_id=highlighted_glue_id,
            ),
        )
    )
    return hits


def _draw_projection_panel(
    surface: pygame.Surface,
    fonts,
    *,
    panel: _ProjectionPanel,
    dims: tuple[int, ...],
    dimension: int,
    selected_coord: tuple[int, ...],
    probe_path: Iterable[Sequence[int]] | None,
    sandbox_cells: tuple[tuple[int, ...], ...] | None,
    sandbox_valid: bool | None,
    slab_radius: int,
    focus_boundaries: tuple[BoundaryRef, ...],
    cell_steps: tuple[CellStepResult, ...],
    piece_steps: tuple[tuple[str, PieceStepResult], ...],
    active_tool: str | None,
    focused_glue_id: str | None,
) -> tuple[list[TopologyLabHitTarget], list[str]]:
    hits = [TopologyLabHitTarget(_PANEL_KIND, panel.label, panel.rect.copy())]
    _draw_panel_frame(
        surface,
        fonts,
        panel=panel,
        selected_coord=selected_coord,
        slab_radius=slab_radius,
    )
    board_rect, cell_size = _panel_grid_rect(panel.rect, dims, panel.axes)
    _draw_grid(
        surface,
        board_rect=board_rect,
        cell_size=cell_size,
        dims=dims,
        axes=panel.axes,
    )
    _draw_focus_boundaries(
        surface,
        board_rect=board_rect,
        axes=panel.axes,
        focus_boundaries=focus_boundaries,
    )
    hits.extend(
        _draw_cell_hits(
            board_rect=board_rect,
            cell_size=cell_size,
            dims=dims,
            axes=panel.axes,
            selected_coord=selected_coord,
        )
    )
    _draw_probe_path(
        surface,
        board_rect=board_rect,
        cell_size=cell_size,
        axes=panel.axes,
        dimension=dimension,
        selected_coord=selected_coord,
        probe_path=probe_path,
        slab_radius=slab_radius,
    )
    _draw_sandbox_cells(
        surface,
        board_rect=board_rect,
        cell_size=cell_size,
        axes=panel.axes,
        dimension=dimension,
        selected_coord=selected_coord,
        sandbox_cells=sandbox_cells,
        sandbox_valid=sandbox_valid,
        slab_radius=slab_radius,
    )
    _draw_selected_cell(
        surface,
        board_rect=board_rect,
        cell_size=cell_size,
        axes=panel.axes,
        selected_coord=selected_coord,
    )
    if active_tool == _SANDBOX_TOOL and piece_steps:
        legend = _draw_piece_step_previews(
            surface,
            board_rect=board_rect,
            cell_size=cell_size,
            axes=panel.axes,
            selected_coord=selected_coord,
            piece_steps=piece_steps,
            dimension=dimension,
            slab_radius=slab_radius,
        )
    else:
        legend = _draw_cell_step_previews(
            surface,
            board_rect=board_rect,
            cell_size=cell_size,
            axes=panel.axes,
            selected_coord=selected_coord,
            cell_steps=cell_steps,
            focused_glue_id=focused_glue_id,
            dimension=dimension,
            slab_radius=slab_radius,
        )
    _draw_projection_legend(
        surface,
        fonts,
        panel_rect=panel.rect,
        lines=legend,
        color=_MUTED,
    )
    return hits, legend


def _draw_projection_panels(
    surface: pygame.Surface,
    fonts,
    *,
    panels: list[_ProjectionPanel],
    info_rect: pygame.Rect | None,
    dims: tuple[int, ...],
    dimension: int,
    selected_coord: tuple[int, ...],
    probe_path: Iterable[Sequence[int]] | None,
    sandbox_cells: tuple[tuple[int, ...], ...] | None,
    sandbox_valid: bool | None,
    sandbox_message: str,
    slab_radius: int,
    focus_boundaries: tuple[BoundaryRef, ...],
    cell_steps: tuple[CellStepResult, ...],
    piece_steps: tuple[tuple[str, PieceStepResult], ...],
    active_tool: str | None,
    focused_glue_id: str | None,
) -> list[TopologyLabHitTarget]:
    hits: list[TopologyLabHitTarget] = []
    cell_legend_for_info: list[str] = []
    piece_legend_for_info: list[str] = []
    for panel in panels:
        panel_hits, legend = _draw_projection_panel(
            surface,
            fonts,
            panel=panel,
            dims=dims,
            dimension=dimension,
            selected_coord=selected_coord,
            probe_path=probe_path,
            sandbox_cells=sandbox_cells,
            sandbox_valid=sandbox_valid,
            slab_radius=slab_radius,
            focus_boundaries=focus_boundaries,
            cell_steps=cell_steps,
            piece_steps=piece_steps,
            active_tool=active_tool,
            focused_glue_id=focused_glue_id,
        )
        hits.extend(panel_hits)
        if active_tool == _SANDBOX_TOOL and legend and not piece_legend_for_info:
            piece_legend_for_info = legend
        if active_tool != _SANDBOX_TOOL and legend and not cell_legend_for_info:
            cell_legend_for_info = legend
    if info_rect is not None:
        _draw_info_panel(
            surface,
            fonts,
            rect=info_rect,
            selected_coord=selected_coord,
            focused_glue_id=focused_glue_id,
            active_tool=active_tool,
            sandbox_valid=sandbox_valid,
            sandbox_message=sandbox_message,
            cell_legend=cell_legend_for_info,
            piece_legend=piece_legend_for_info,
        )
    return hits


def draw_projection_scene(
    surface: pygame.Surface,
    fonts,
    *,
    dimension: int,
    area: pygame.Rect,
    boundaries: tuple[BoundaryRef, ...],
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
    active_glue_ids: dict[str, str],
    preview_dims: tuple[int, ...],
    profile: ExplorerTopologyProfile | None = None,
    active_tool: str | None = None,
    selected_glue_id: str | None = None,
    highlighted_glue_id: str | None = None,
    hovered_boundary_index: int | None = None,
    selected_boundary_index: int | None = None,
    probe_coord: tuple[int, ...] | None = None,
    probe_path: Iterable[Sequence[int]] | None = None,
    sandbox_cells: tuple[tuple[int, ...], ...] | None = None,
    sandbox_valid: bool | None = None,
    sandbox_message: str = "",
    slab_radius: int = 0,
) -> list[TopologyLabHitTarget]:
    dims = tuple(int(value) for value in preview_dims)
    selected_coord = _selected_projection_coord(dimension, probe_coord)
    _draw_projection_heading(
        surface,
        fonts,
        area=area,
        dimension=dimension,
        selected_coord=selected_coord,
    )
    header_height = 70 if dimension == 4 else 64
    ribbon_rect = pygame.Rect(area.x, area.y, area.width, header_height)
    hits = _draw_projection_ribbon(
        surface,
        fonts,
        area=ribbon_rect,
        boundaries=boundaries,
        source_boundary=source_boundary,
        target_boundary=target_boundary,
        active_glue_ids=active_glue_ids,
        hovered_boundary_index=hovered_boundary_index,
        selected_boundary_index=selected_boundary_index,
        selected_glue_id=selected_glue_id,
        highlighted_glue_id=highlighted_glue_id,
    )
    cell_steps = _resolve_cell_previews(
        profile=profile,
        dims=dims,
        coord=selected_coord,
    )
    piece_steps = _resolve_piece_previews(
        profile=profile,
        dims=dims,
        sandbox_cells=sandbox_cells,
    )
    focused_glue_id = highlighted_glue_id or selected_glue_id
    panels, info_rect = _layout_projection_panels(
        area,
        dimension=dimension,
        header_height=header_height + _PANEL_GAP,
    )
    hits.extend(
        _draw_projection_panels(
            surface,
            fonts,
            panels=panels,
            info_rect=info_rect,
            dims=dims,
            dimension=dimension,
            selected_coord=selected_coord,
            probe_path=probe_path,
            sandbox_cells=sandbox_cells,
            sandbox_valid=sandbox_valid,
            sandbox_message=sandbox_message,
            slab_radius=slab_radius,
            focus_boundaries=_focus_boundaries_for_glue(
                profile,
                glue_id=focused_glue_id,
            ),
            cell_steps=cell_steps,
            piece_steps=piece_steps,
            active_tool=active_tool,
            focused_glue_id=focused_glue_id,
        )
    )
    return hits


__all__ = [
    "draw_projection_scene",
    "projection_hidden_label",
    "projection_pairs_for_dimension",
]
