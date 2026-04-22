from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import pygame

from tet4d.engine.ui_logic.view_modes import GridMode
from tet4d.ui.pygame.render.board_boundary import (
    BoardBoundaryPlane,
    board_boundary_coordinate,
    board_boundary_planes,
)
from tet4d.ui.pygame.projection3d import (
    DepthDenominatorFn,
    Point2,
    Point3,
    ProjectRawFn,
    ProjectedFacePrimitive,
    TransformRawFn,
)


Coord2F: TypeAlias = tuple[float, float]
Coord3F: TypeAlias = tuple[float, float, float]
GuideCell2D: TypeAlias = tuple[Coord2F, float]
GuideCell3D: TypeAlias = tuple[Coord3F, float]


BoundaryTarget = BoardBoundaryPlane


@dataclass(frozen=True)
class BoundaryProjectionSegment2D:
    start: Coord2F
    end: Coord2F
    axis: int
    side: str
    color: tuple[int, int, int]


def projection_guide_enabled(grid_mode: GridMode) -> bool:
    return grid_mode in (GridMode.BOTTOM_BOUNDARY, GridMode.ALL_BOUNDARIES)


def boundary_targets_for_mode(
    *,
    dims: tuple[int, ...],
    gravity_axis: int,
    grid_mode: GridMode,
) -> tuple[BoundaryTarget, ...]:
    if not projection_guide_enabled(grid_mode):
        return ()
    if grid_mode == GridMode.BOTTOM_BOUNDARY:
        axis = max(0, min(len(dims) - 1, int(gravity_axis)))
        return (
            BoundaryTarget(
                axis=axis,
                side="+",
                coordinate=board_boundary_coordinate(dims=dims, axis=axis, side="+"),
            ),
        )
    return tuple(board_boundary_planes(dims))


def _clamp_scale(scale: float) -> float:
    return max(0.0, min(1.0, float(scale)))


def _guide_color(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(min(255, int((channel * 0.55) + 110.0)) for channel in color)


def build_boundary_projection_segments_2d(
    *,
    cells: tuple[GuideCell2D, ...],
    dims: tuple[int, int],
    gravity_axis: int,
    grid_mode: GridMode,
    color: tuple[int, int, int],
) -> tuple[BoundaryProjectionSegment2D, ...]:
    targets = boundary_targets_for_mode(
        dims=dims,
        gravity_axis=gravity_axis,
        grid_mode=grid_mode,
    )
    if not targets:
        return ()
    guide_color = _guide_color(color)
    segments: list[BoundaryProjectionSegment2D] = []
    for (cell_x, cell_y), scale in cells:
        half = 0.5 * _clamp_scale(scale)
        if half <= 0.0:
            continue
        center_x = float(cell_x) + 0.5
        center_y = float(cell_y) + 0.5
        for target in targets:
            if target.axis == 0:
                segments.append(
                    BoundaryProjectionSegment2D(
                        start=(target.coordinate, center_y - half),
                        end=(target.coordinate, center_y + half),
                        axis=target.axis,
                        side=target.side,
                        color=guide_color,
                    )
                )
            else:
                segments.append(
                    BoundaryProjectionSegment2D(
                        start=(center_x - half, target.coordinate),
                        end=(center_x + half, target.coordinate),
                        axis=target.axis,
                        side=target.side,
                        color=guide_color,
                    )
                )
    return tuple(segments)


def draw_boundary_projection_segments_2d(
    surface: pygame.Surface,
    *,
    segments: tuple[BoundaryProjectionSegment2D, ...],
    board_offset: tuple[int, int],
    cell_size: int,
    outer_width: int = 6,
    inner_width: int = 3,
) -> None:
    if not segments:
        return
    ox, oy = board_offset
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for segment in segments:
        start = (
            float(ox) + (float(segment.start[0]) * float(cell_size)),
            float(oy) + (float(segment.start[1]) * float(cell_size)),
        )
        end = (
            float(ox) + (float(segment.end[0]) * float(cell_size)),
            float(oy) + (float(segment.end[1]) * float(cell_size)),
        )
        pygame.draw.line(overlay, (255, 255, 255, 72), start, end, outer_width)
        pygame.draw.line(
            overlay,
            (*segment.color, 186),
            start,
            end,
            inner_width,
        )
    surface.blit(overlay, (0, 0))


def _boundary_quad_vertices(
    *,
    cell: Coord3F,
    scale: float,
    target: BoundaryTarget,
) -> tuple[Point3, Point3, Point3, Point3]:
    half = 0.5 * _clamp_scale(scale)
    center = (float(cell[0]) + 0.5, float(cell[1]) + 0.5, float(cell[2]) + 0.5)
    tangent_axes = tuple(axis for axis in range(3) if axis != target.axis)
    vertices: list[Point3] = []
    for offset_a, offset_b in ((-half, -half), (half, -half), (half, half), (-half, half)):
        raw = [center[0], center[1], center[2]]
        raw[target.axis] = float(target.coordinate)
        raw[tangent_axes[0]] += float(offset_a)
        raw[tangent_axes[1]] += float(offset_b)
        vertices.append((float(raw[0]), float(raw[1]), float(raw[2])))
    return vertices[0], vertices[1], vertices[2], vertices[3]


def build_boundary_projection_face_primitives(
    *,
    cells: tuple[GuideCell3D, ...],
    dims: tuple[int, int, int],
    gravity_axis: int,
    grid_mode: GridMode,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
    color: tuple[int, int, int],
) -> tuple[ProjectedFacePrimitive, ...]:
    targets = boundary_targets_for_mode(
        dims=dims,
        gravity_axis=gravity_axis,
        grid_mode=grid_mode,
    )
    if not targets:
        return ()
    guide_color = _guide_color(color)
    primitives: list[ProjectedFacePrimitive] = []
    for cell, scale in cells:
        if _clamp_scale(scale) <= 0.0:
            continue
        for target in targets:
            raw_vertices = _boundary_quad_vertices(cell=cell, scale=scale, target=target)
            projected: list[Point2] = []
            depths: list[float] = []
            denominators: list[float] = []
            for raw in raw_vertices:
                projected_point = project_raw(raw)
                if projected_point is None:
                    projected = []
                    break
                transformed = transform_raw(raw)
                projected.append(projected_point)
                depths.append(float(transformed[2]))
                denominators.append(float(depth_denominator(float(transformed[2]))))
            if len(projected) != 4:
                continue
            primitives.append(
                ProjectedFacePrimitive(
                    avg_depth=sum(depths) / 4.0,
                    polygon=tuple(projected),
                    color=guide_color,
                    active=False,
                    vertex_depths=tuple(depths),
                    vertex_denominators=tuple(denominators),
                )
            )
    return tuple(primitives)


def draw_boundary_projection_faces(
    surface: pygame.Surface,
    *,
    faces: tuple[ProjectedFacePrimitive, ...],
    fill_alpha: int = 38,
    outline_alpha: int = 122,
) -> None:
    if not faces:
        return
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for primitive in sorted(faces, key=lambda item: item.avg_depth, reverse=True):
        if len(primitive.polygon) < 3:
            continue
        pygame.draw.polygon(overlay, (*primitive.color, fill_alpha), primitive.polygon)
        outline = tuple(min(255, channel + 35) for channel in primitive.color)
        pygame.draw.polygon(overlay, (*outline, outline_alpha), primitive.polygon, 2)
    surface.blit(overlay, (0, 0))


__all__ = [
    "BoundaryProjectionSegment2D",
    "BoundaryTarget",
    "GuideCell2D",
    "GuideCell3D",
    "boundary_targets_for_mode",
    "build_boundary_projection_face_primitives",
    "build_boundary_projection_segments_2d",
    "draw_boundary_projection_faces",
    "draw_boundary_projection_segments_2d",
    "projection_guide_enabled",
]
