from __future__ import annotations

import math
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass

import pygame

from tet4d.ui.pygame.render.board_boundary import board_boundary_coordinate

from tet4d.engine.runtime.project_config import project_constant_int

from .ui_utils import draw_vertical_gradient

Point2 = tuple[float, float]
Point3 = tuple[float, float, float]
Cell3 = tuple[int, int, int]
Face = tuple[float, list[Point2], tuple[int, int, int], bool]
ProjectRawFn = Callable[[Point3], Point2 | None]
TransformRawFn = Callable[[Point3], Point3]
Segment2 = tuple[Point2, Point2]
DepthDenominatorFn = Callable[[float], float]


@dataclass(frozen=True)
class ProjectedLinePrimitive:
    start: Point2
    end: Point2
    start_depth: float
    end_depth: float
    start_denominator: float
    end_denominator: float
    source_type: str


@dataclass(frozen=True)
class ProjectedLineFragment:
    start: Point2
    end: Point2
    source_type: str


@dataclass(frozen=True)
class ProjectedFacePrimitive:
    avg_depth: float
    polygon: tuple[Point2, ...]
    color: tuple[int, int, int]
    active: bool
    vertex_depths: tuple[float, ...]
    vertex_denominators: tuple[float, ...]


_CUBE_VERTS: list[Point3] = [
    (-0.5, -0.5, -0.5),
    (0.5, -0.5, -0.5),
    (0.5, 0.5, -0.5),
    (-0.5, 0.5, -0.5),
    (-0.5, -0.5, 0.5),
    (0.5, -0.5, 0.5),
    (0.5, 0.5, 0.5),
    (-0.5, 0.5, 0.5),
]

_CUBE_FACES: list[tuple[list[int], float]] = [
    ([0, 1, 2, 3], 0.58),
    ([4, 5, 6, 7], 0.95),
    ([0, 3, 7, 4], 0.72),
    ([1, 2, 6, 5], 0.84),
    ([0, 1, 5, 4], 0.63),
    ([3, 2, 6, 7], 1.10),
]

_BOX_EDGES: list[tuple[int, int]] = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 0),
    (4, 5),
    (5, 6),
    (6, 7),
    (7, 4),
    (0, 4),
    (1, 5),
    (2, 6),
    (3, 7),
]

_BOX_FACES: list[list[int]] = [
    [0, 1, 2, 3],
    [4, 5, 6, 7],
    [0, 1, 5, 4],
    [3, 2, 6, 7],
    [0, 3, 7, 4],
    [1, 2, 6, 5],
]

_PROJECTION_LATTICE_CACHE_MAX = project_constant_int(
    ("cache_limits", "projection_lattice_max"),
    96,
    min_value=8,
    max_value=4096,
)
_PROJECTION_LATTICE_CACHE: OrderedDict[
    object,
    tuple[tuple[ProjectedLinePrimitive, ...], tuple[ProjectedLinePrimitive, ...]],
] = OrderedDict()


def shade_color(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return (
        max(0, min(255, int(color[0] * factor))),
        max(0, min(255, int(color[1] * factor))),
        max(0, min(255, int(color[2] * factor))),
    )


def color_for_cell(
    cell_id: int,
    color_map: dict[int, tuple[int, int, int]],
    default: tuple[int, int, int] = (200, 200, 200),
) -> tuple[int, int, int]:
    if cell_id <= 0:
        return default
    return color_map.get(cell_id, default)


def draw_gradient_background(
    surface: pygame.Surface,
    top_color: tuple[int, int, int],
    bottom_color: tuple[int, int, int],
) -> None:
    draw_vertical_gradient(surface, top_color, bottom_color)


def raw_to_world(raw: Point3, dims: Cell3) -> Point3:
    width, height, depth = dims
    x = raw[0] - (width - 1) / 2.0
    y = -(raw[1] - (height - 1) / 2.0)
    z = raw[2] - (depth - 1) / 2.0
    return x, y, z


def transform_point(world: Point3, yaw_deg: float, pitch_deg: float) -> Point3:
    x, y, z = world
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)

    x1 = math.cos(yaw) * x + math.sin(yaw) * z
    z1 = -math.sin(yaw) * x + math.cos(yaw) * z
    y1 = y

    y2 = math.cos(pitch) * y1 - math.sin(pitch) * z1
    z2 = math.sin(pitch) * y1 + math.cos(pitch) * z1
    return x1, y2, z2


def normalize_angle_deg(angle_deg: float) -> float:
    return angle_deg % 360.0


def shortest_angle_delta_deg(start_deg: float, target_deg: float) -> float:
    return ((target_deg - start_deg + 540.0) % 360.0) - 180.0


def smoothstep01(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def interpolate_angle_deg(start_deg: float, target_deg: float, t: float) -> float:
    eased = smoothstep01(t)
    delta = shortest_angle_delta_deg(start_deg, target_deg)
    return normalize_angle_deg(start_deg + delta * eased)


def orthographic_point(trans: Point3, center_px: Point2, zoom: float) -> Point2:
    tx, ty, _tz = trans
    cx, cy = center_px
    return cx + zoom * tx, cy - zoom * ty


def perspective_point(
    trans: Point3,
    center_px: Point2,
    zoom: float,
    cam_dist: float,
    near_clip: float = 0.08,
) -> Point2 | None:
    tx, ty, tz = trans
    zc = tz + cam_dist
    if zc <= near_clip:
        return None
    cx, cy = center_px
    return cx + zoom * (tx / zc), cy - zoom * (ty / zc)


def projective_point(
    trans: Point3,
    center_px: Point2,
    zoom: float,
    strength: float,
    bias: float,
    min_denom: float = 0.15,
) -> Point2:
    tx, ty, tz = trans
    denom = 1.0 + strength * (tz + bias)
    if denom <= min_denom:
        denom = min_denom
    cx, cy = center_px
    return cx + zoom * (tx / denom), cy - zoom * (ty / denom)


def box_raw_corners(dims: Cell3) -> list[Point3]:
    min_x = board_boundary_coordinate(dims=dims, axis=0, side="-")
    max_x = board_boundary_coordinate(dims=dims, axis=0, side="+")
    min_y = board_boundary_coordinate(dims=dims, axis=1, side="-")
    max_y = board_boundary_coordinate(dims=dims, axis=1, side="+")
    min_z = board_boundary_coordinate(dims=dims, axis=2, side="-")
    max_z = board_boundary_coordinate(dims=dims, axis=2, side="+")
    return [
        (min_x, min_y, min_z),
        (max_x, min_y, min_z),
        (max_x, max_y, min_z),
        (min_x, max_y, min_z),
        (min_x, min_y, max_z),
        (max_x, min_y, max_z),
        (max_x, max_y, max_z),
        (min_x, max_y, max_z),
    ]


def fit_orthographic_zoom(
    dims: Cell3,
    yaw_deg: float,
    pitch_deg: float,
    rect: pygame.Rect,
    pad_x: float,
    pad_y: float,
    min_zoom: float,
    max_zoom: float,
) -> float:
    transformed = [
        transform_point(raw_to_world(raw, dims), yaw_deg, pitch_deg)
        for raw in box_raw_corners(dims)
    ]
    min_x = min(point[0] for point in transformed)
    max_x = max(point[0] for point in transformed)
    min_y = min(point[1] for point in transformed)
    max_y = max(point[1] for point in transformed)
    span_x = max(0.01, max_x - min_x)
    span_y = max(0.01, max_y - min_y)
    fit_x = (rect.width - pad_x) / span_x
    fit_y = (rect.height - pad_y) / span_y
    return max(min_zoom, min(max_zoom, min(fit_x, fit_y)))


def projection_cache_key(
    *,
    prefix: str,
    dims: Cell3,
    center_px: Point2,
    yaw_deg: float,
    pitch_deg: float,
    zoom: float,
    extras: tuple[object, ...] = (),
) -> tuple[object, ...]:
    return (
        prefix,
        dims,
        round(yaw_deg, 3),
        round(pitch_deg, 3),
        round(zoom, 3),
        int(center_px[0]),
        int(center_px[1]),
        *extras,
    )


def projection_helper_cache_key(
    *,
    prefix: str,
    dims: Cell3,
    center_px: Point2,
    yaw_deg: float,
    pitch_deg: float,
    zoom: float,
    marks: tuple[set[int], set[int], set[int]],
    extras: tuple[object, ...] = (),
) -> tuple[object, ...]:
    return projection_cache_key(
        prefix=prefix,
        dims=dims,
        center_px=center_px,
        yaw_deg=yaw_deg,
        pitch_deg=pitch_deg,
        zoom=zoom,
        extras=(
            *extras,
            tuple(sorted(marks[0])),
            tuple(sorted(marks[1])),
            tuple(sorted(marks[2])),
        ),
    )


def _axis_segments_y(
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
    x_marks: set[int] | None,
    z_marks: set[int] | None,
) -> list[ProjectedLinePrimitive]:
    segments: list[ProjectedLinePrimitive] = []
    for x in range(dims[0] + 1):
        if x_marks is not None and x not in x_marks:
            continue
        for z in range(dims[2] + 1):
            if z_marks is not None and z not in z_marks:
                continue
            segment = _project_line_primitive(
                (x - 0.5, -0.5, z - 0.5),
                (x - 0.5, dims[1] - 0.5, z - 0.5),
                project_raw=project_raw,
                transform_raw=transform_raw,
                depth_denominator=depth_denominator,
                source_type="gridline",
            )
            if segment is not None:
                segments.append(segment)
    return segments


def _axis_segments_x(
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
    y_marks: set[int] | None,
    z_marks: set[int] | None,
) -> list[ProjectedLinePrimitive]:
    segments: list[ProjectedLinePrimitive] = []
    for y in range(dims[1] + 1):
        if y_marks is not None and y not in y_marks:
            continue
        for z in range(dims[2] + 1):
            if z_marks is not None and z not in z_marks:
                continue
            segment = _project_line_primitive(
                (-0.5, y - 0.5, z - 0.5),
                (dims[0] - 0.5, y - 0.5, z - 0.5),
                project_raw=project_raw,
                transform_raw=transform_raw,
                depth_denominator=depth_denominator,
                source_type="gridline",
            )
            if segment is not None:
                segments.append(segment)
    return segments


def _axis_segments_z(
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
    x_marks: set[int] | None,
    y_marks: set[int] | None,
) -> list[ProjectedLinePrimitive]:
    segments: list[ProjectedLinePrimitive] = []
    for x in range(dims[0] + 1):
        if x_marks is not None and x not in x_marks:
            continue
        for y in range(dims[1] + 1):
            if y_marks is not None and y not in y_marks:
                continue
            segment = _project_line_primitive(
                (x - 0.5, y - 0.5, -0.5),
                (x - 0.5, y - 0.5, dims[2] - 0.5),
                project_raw=project_raw,
                transform_raw=transform_raw,
                depth_denominator=depth_denominator,
                source_type="gridline",
            )
            if segment is not None:
                segments.append(segment)
    return segments


def _frame_segments(
    dims: Cell3,
    project_raw: ProjectRawFn,
) -> list[Segment2]:
    frame_segments: list[Segment2] = []
    projected: list[Point2 | None] = [project_raw(raw) for raw in box_raw_corners(dims)]
    for a, b in _BOX_EDGES:
        pa = projected[a]
        pb = projected[b]
        if pa is not None and pb is not None:
            frame_segments.append((pa, pb))
    return frame_segments


def _frame_line_primitives(
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
) -> list[ProjectedLinePrimitive]:
    frame_segments: list[ProjectedLinePrimitive] = []
    raw_corners = box_raw_corners(dims)
    for a, b in _BOX_EDGES:
        segment = _project_line_primitive(
            raw_corners[a],
            raw_corners[b],
            project_raw=project_raw,
            transform_raw=transform_raw,
            depth_denominator=depth_denominator,
            source_type="box_edge",
        )
        if segment is not None:
            frame_segments.append(segment)
    return frame_segments


def _lattice_segments(
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
    x_marks: set[int] | None = None,
    y_marks: set[int] | None = None,
    z_marks: set[int] | None = None,
) -> tuple[tuple[ProjectedLinePrimitive, ...], tuple[ProjectedLinePrimitive, ...]]:
    inner_segments: list[ProjectedLinePrimitive] = []
    inner_segments.extend(
        _axis_segments_y(
            dims, project_raw, transform_raw, depth_denominator, x_marks, z_marks
        )
    )
    inner_segments.extend(
        _axis_segments_x(
            dims, project_raw, transform_raw, depth_denominator, y_marks, z_marks
        )
    )
    inner_segments.extend(
        _axis_segments_z(
            dims, project_raw, transform_raw, depth_denominator, x_marks, y_marks
        )
    )
    return tuple(inner_segments), tuple(
        _frame_line_primitives(dims, project_raw, transform_raw, depth_denominator)
    )


def _projection_lattice_segments_cached(
    *,
    cache_key: object | None,
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
    x_marks: set[int] | None = None,
    y_marks: set[int] | None = None,
    z_marks: set[int] | None = None,
) -> tuple[tuple[ProjectedLinePrimitive, ...], tuple[ProjectedLinePrimitive, ...]]:
    if cache_key is None:
        return _lattice_segments(
            dims,
            project_raw,
            transform_raw,
            depth_denominator,
            x_marks,
            y_marks,
            z_marks,
        )

    cached = _PROJECTION_LATTICE_CACHE.get(cache_key)
    if cached is not None:
        _PROJECTION_LATTICE_CACHE.move_to_end(cache_key)
        return cached

    segments = _lattice_segments(
        dims,
        project_raw,
        transform_raw,
        depth_denominator,
        x_marks,
        y_marks,
        z_marks,
    )
    _PROJECTION_LATTICE_CACHE[cache_key] = segments
    _PROJECTION_LATTICE_CACHE.move_to_end(cache_key)
    while len(_PROJECTION_LATTICE_CACHE) > _PROJECTION_LATTICE_CACHE_MAX:
        _PROJECTION_LATTICE_CACHE.popitem(last=False)
    return segments


def draw_projected_lattice(
    surface: pygame.Surface,
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
    inner_color: tuple[int, int, int],
    frame_color: tuple[int, int, int],
    frame_width: int = 2,
    cache_key: object | None = None,
) -> None:
    inner_segments, frame_segments = _projection_lattice_segments_cached(
        cache_key=cache_key,
        dims=dims,
        project_raw=project_raw,
        transform_raw=transform_raw,
        depth_denominator=depth_denominator,
    )
    draw_projected_line_fragments(
        surface,
        tuple(
            ProjectedLineFragment(
                start=segment.start,
                end=segment.end,
                source_type=segment.source_type,
            )
            for segment in (*inner_segments, *frame_segments)
        ),
        inner_color=inner_color,
        frame_color=frame_color,
        frame_width=frame_width,
    )


def draw_projected_helper_lattice(
    surface: pygame.Surface,
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
    x_marks: set[int],
    y_marks: set[int],
    z_marks: set[int],
    inner_color: tuple[int, int, int],
    frame_color: tuple[int, int, int],
    frame_width: int = 2,
    cache_key: object | None = None,
) -> None:
    inner_segments, frame_segments = _projection_lattice_segments_cached(
        cache_key=cache_key,
        dims=dims,
        project_raw=project_raw,
        transform_raw=transform_raw,
        depth_denominator=depth_denominator,
        x_marks=_clip_marks(x_marks, dims[0]),
        y_marks=_clip_marks(y_marks, dims[1]),
        z_marks=_clip_marks(z_marks, dims[2]),
    )
    draw_projected_line_fragments(
        surface,
        tuple(
            ProjectedLineFragment(
                start=segment.start,
                end=segment.end,
                source_type=segment.source_type,
            )
            for segment in (*inner_segments, *frame_segments)
        ),
        inner_color=inner_color,
        frame_color=frame_color,
        frame_width=frame_width,
    )


def _clip_marks(marks: set[int], max_value: int) -> set[int]:
    return {value for value in marks if 0 <= value <= max_value}


def draw_projected_box_edges(
    surface: pygame.Surface,
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
    edge_color: tuple[int, int, int] = (96, 118, 164),
    edge_width: int = 2,
) -> None:
    draw_projected_line_fragments(
        surface,
        tuple(
            ProjectedLineFragment(
                start=segment.start,
                end=segment.end,
                source_type=segment.source_type,
            )
            for segment in _frame_line_primitives(
                dims, project_raw, transform_raw, depth_denominator
            )
        ),
        inner_color=edge_color,
        frame_color=edge_color,
        frame_width=edge_width,
    )


def draw_projected_box_shadow(
    surface: pygame.Surface,
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    fill_color: tuple[int, int, int] = (34, 44, 72),
    edge_color: tuple[int, int, int] = (86, 104, 146),
    fill_alpha: int = 72,
    edge_alpha: int = 138,
    edge_width: int = 2,
) -> None:
    raw_corners = box_raw_corners(dims)
    projected: list[Point2] = []
    transformed: list[Point3] = []

    for raw in raw_corners:
        projected_point = project_raw(raw)
        if projected_point is None:
            return
        projected.append(projected_point)
        transformed.append(transform_raw(raw))

    face_depths: list[tuple[float, list[int]]] = []
    for face in _BOX_FACES:
        depth = sum(transformed[i][2] for i in face) / float(len(face))
        face_depths.append((depth, face))
    face_depths.sort(key=lambda item: item[0], reverse=True)

    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for _depth, face in face_depths[:2]:
        polygon = [projected[i] for i in face]
        pygame.draw.polygon(overlay, (*fill_color, fill_alpha), polygon)

    for a, b in _BOX_EDGES:
        pygame.draw.line(
            overlay,
            (*edge_color, edge_alpha),
            projected[a],
            projected[b],
            edge_width,
        )
    surface.blit(overlay, (0, 0))


def build_cube_faces(
    cell: Cell3,
    color: tuple[int, int, int],
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    active: bool,
    active_boost: float = 1.08,
    scale: float = 1.0,
) -> list[Face]:
    return [
        (
            primitive.avg_depth,
            list(primitive.polygon),
            primitive.color,
            primitive.active,
        )
        for primitive in build_cube_face_primitives(
            cell=cell,
            color=color,
            project_raw=project_raw,
            transform_raw=transform_raw,
            active=active,
            active_boost=active_boost,
            scale=scale,
            depth_denominator=lambda depth: 1.0,
        )
    ]


def build_cube_face_primitives(
    cell: Cell3,
    color: tuple[int, int, int],
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    active: bool,
    *,
    depth_denominator: DepthDenominatorFn,
    active_boost: float = 1.08,
    scale: float = 1.0,
) -> list[ProjectedFacePrimitive]:
    transformed: list[Point3] = []
    projected: list[Point2] = []
    denominators: list[float] = []

    for ox, oy, oz in _CUBE_VERTS:
        scaled_ox = ox * scale
        scaled_oy = oy * scale
        scaled_oz = oz * scale
        raw = (cell[0] + scaled_ox, cell[1] + scaled_oy, cell[2] + scaled_oz)
        transformed_point = transform_raw(raw)
        transformed.append(transformed_point)
        projected_point = project_raw(raw)
        if projected_point is None:
            return []
        projected.append(projected_point)
        denominators.append(depth_denominator(transformed_point[2]))

    faces: list[ProjectedFacePrimitive] = []
    for face_indices, shade_factor in _CUBE_FACES:
        polygon = tuple(projected[i] for i in face_indices)
        avg_depth = sum(transformed[i][2] for i in face_indices) / 4.0
        factor = shade_factor * (active_boost if active else 1.0)
        faces.append(
            ProjectedFacePrimitive(
                avg_depth=avg_depth,
                polygon=polygon,
                color=shade_color(color, factor),
                active=active,
                vertex_depths=tuple(transformed[i][2] for i in face_indices),
                vertex_denominators=tuple(denominators[i] for i in face_indices),
            )
        )
    return faces


def _rotate_point_local(point: Point3, rotation_deg: Point3) -> Point3:
    x, y, z = point
    rx, ry, rz = (
        math.radians(rotation_deg[0]),
        math.radians(rotation_deg[1]),
        math.radians(rotation_deg[2]),
    )

    cos_x, sin_x = math.cos(rx), math.sin(rx)
    y, z = ((y * cos_x) - (z * sin_x), (y * sin_x) + (z * cos_x))

    cos_y, sin_y = math.cos(ry), math.sin(ry)
    x, z = ((x * cos_y) + (z * sin_y), (-x * sin_y) + (z * cos_y))

    cos_z, sin_z = math.cos(rz), math.sin(rz)
    x, y = ((x * cos_z) - (y * sin_z), (x * sin_z) + (y * cos_z))
    return (x, y, z)


def build_oriented_cube_face_primitives(
    center: Point3,
    color: tuple[int, int, int],
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    active: bool,
    *,
    depth_denominator: DepthDenominatorFn,
    rotation_deg: Point3 = (0.0, 0.0, 0.0),
    active_boost: float = 1.08,
    scale: float = 1.0,
) -> list[ProjectedFacePrimitive]:
    transformed: list[Point3] = []
    projected: list[Point2] = []
    denominators: list[float] = []

    for ox, oy, oz in _CUBE_VERTS:
        rotated = _rotate_point_local(
            (ox * scale, oy * scale, oz * scale),
            rotation_deg,
        )
        raw = (
            center[0] + rotated[0],
            center[1] + rotated[1],
            center[2] + rotated[2],
        )
        transformed_point = transform_raw(raw)
        transformed.append(transformed_point)
        projected_point = project_raw(raw)
        if projected_point is None:
            return []
        projected.append(projected_point)
        denominators.append(depth_denominator(transformed_point[2]))

    faces: list[ProjectedFacePrimitive] = []
    for face_indices, shade_factor in _CUBE_FACES:
        polygon = tuple(projected[i] for i in face_indices)
        avg_depth = sum(transformed[i][2] for i in face_indices) / 4.0
        factor = shade_factor * (active_boost if active else 1.0)
        faces.append(
            ProjectedFacePrimitive(
                avg_depth=avg_depth,
                polygon=polygon,
                color=shade_color(color, factor),
                active=active,
                vertex_depths=tuple(transformed[i][2] for i in face_indices),
                vertex_denominators=tuple(denominators[i] for i in face_indices),
            )
        )
    return faces


def build_oriented_cube_faces(
    center: Point3,
    color: tuple[int, int, int],
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    active: bool,
    *,
    rotation_deg: Point3 = (0.0, 0.0, 0.0),
    active_boost: float = 1.08,
    scale: float = 1.0,
) -> list[Face]:
    return [
        (
            primitive.avg_depth,
            list(primitive.polygon),
            primitive.color,
            primitive.active,
        )
        for primitive in build_oriented_cube_face_primitives(
            center=center,
            color=color,
            project_raw=project_raw,
            transform_raw=transform_raw,
            active=active,
            depth_denominator=lambda depth: 1.0,
            rotation_deg=rotation_deg,
            active_boost=active_boost,
            scale=scale,
        )
    ]


def project_lattice_primitives(
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
    *,
    cache_key: object | None = None,
) -> tuple[tuple[ProjectedLinePrimitive, ...], tuple[ProjectedLinePrimitive, ...]]:
    return _projection_lattice_segments_cached(
        cache_key=cache_key,
        dims=dims,
        project_raw=project_raw,
        transform_raw=transform_raw,
        depth_denominator=depth_denominator,
    )


def project_helper_lattice_primitives(
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
    *,
    x_marks: set[int],
    y_marks: set[int],
    z_marks: set[int],
    cache_key: object | None = None,
) -> tuple[tuple[ProjectedLinePrimitive, ...], tuple[ProjectedLinePrimitive, ...]]:
    return _projection_lattice_segments_cached(
        cache_key=cache_key,
        dims=dims,
        project_raw=project_raw,
        transform_raw=transform_raw,
        depth_denominator=depth_denominator,
        x_marks=_clip_marks(x_marks, dims[0]),
        y_marks=_clip_marks(y_marks, dims[1]),
        z_marks=_clip_marks(z_marks, dims[2]),
    )


def project_box_edge_primitives(
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
) -> tuple[ProjectedLinePrimitive, ...]:
    return tuple(
        _frame_line_primitives(dims, project_raw, transform_raw, depth_denominator)
    )


def project_boundary_lattice_primitives(
    dims: Cell3,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
) -> tuple[ProjectedLinePrimitive, ...]:
    boundary_segments: list[ProjectedLinePrimitive] = []
    seen: set[tuple[tuple[float, float, float], tuple[float, float, float], str]] = set()

    def append_segment(
        raw_start: Point3,
        raw_end: Point3,
        *,
        source_type: str,
    ) -> None:
        ordered = tuple(sorted((raw_start, raw_end)))
        key = (ordered[0], ordered[1], source_type)
        if key in seen:
            return
        seen.add(key)
        segment = _project_line_primitive(
            raw_start,
            raw_end,
            project_raw=project_raw,
            transform_raw=transform_raw,
            depth_denominator=depth_denominator,
            source_type=source_type,
        )
        if segment is not None:
            boundary_segments.append(segment)

    _append_boundary_axis_segments(dims, append_segment)
    return tuple(boundary_segments)


def _append_boundary_axis_segments(
    dims: Cell3,
    append_segment,
) -> None:
    max_x, max_y, max_z = dims
    _append_boundary_segments_for_axis(
        range_a=range(max_x + 1),
        range_b=range(max_z + 1),
        max_a=max_x,
        max_b=max_z,
        endpoint_builder=lambda a, b: (
            (
                board_boundary_coordinate(dims=dims, axis=0, side="-" if a == 0 else "+")
                if a in {0, max_x}
                else a - 0.5,
                board_boundary_coordinate(dims=dims, axis=1, side="-"),
                board_boundary_coordinate(dims=dims, axis=2, side="-" if b == 0 else "+")
                if b in {0, max_z}
                else b - 0.5,
            ),
            (
                board_boundary_coordinate(dims=dims, axis=0, side="-" if a == 0 else "+")
                if a in {0, max_x}
                else a - 0.5,
                board_boundary_coordinate(dims=dims, axis=1, side="+"),
                board_boundary_coordinate(dims=dims, axis=2, side="-" if b == 0 else "+")
                if b in {0, max_z}
                else b - 0.5,
            ),
        ),
        append_segment=append_segment,
    )
    _append_boundary_segments_for_axis(
        range_a=range(max_y + 1),
        range_b=range(max_z + 1),
        max_a=max_y,
        max_b=max_z,
        endpoint_builder=lambda a, b: (
            (
                board_boundary_coordinate(dims=dims, axis=0, side="-"),
                board_boundary_coordinate(dims=dims, axis=1, side="-" if a == 0 else "+")
                if a in {0, max_y}
                else a - 0.5,
                board_boundary_coordinate(dims=dims, axis=2, side="-" if b == 0 else "+")
                if b in {0, max_z}
                else b - 0.5,
            ),
            (
                board_boundary_coordinate(dims=dims, axis=0, side="+"),
                board_boundary_coordinate(dims=dims, axis=1, side="-" if a == 0 else "+")
                if a in {0, max_y}
                else a - 0.5,
                board_boundary_coordinate(dims=dims, axis=2, side="-" if b == 0 else "+")
                if b in {0, max_z}
                else b - 0.5,
            ),
        ),
        append_segment=append_segment,
    )
    _append_boundary_segments_for_axis(
        range_a=range(max_x + 1),
        range_b=range(max_y + 1),
        max_a=max_x,
        max_b=max_y,
        endpoint_builder=lambda a, b: (
            (
                board_boundary_coordinate(dims=dims, axis=0, side="-" if a == 0 else "+")
                if a in {0, max_x}
                else a - 0.5,
                board_boundary_coordinate(dims=dims, axis=1, side="-" if b == 0 else "+")
                if b in {0, max_y}
                else b - 0.5,
                board_boundary_coordinate(dims=dims, axis=2, side="-"),
            ),
            (
                board_boundary_coordinate(dims=dims, axis=0, side="-" if a == 0 else "+")
                if a in {0, max_x}
                else a - 0.5,
                board_boundary_coordinate(dims=dims, axis=1, side="-" if b == 0 else "+")
                if b in {0, max_y}
                else b - 0.5,
                board_boundary_coordinate(dims=dims, axis=2, side="+"),
            ),
        ),
        append_segment=append_segment,
    )


def _append_boundary_segments_for_axis(
    *,
    range_a: range,
    range_b: range,
    max_a: int,
    max_b: int,
    endpoint_builder,
    append_segment,
) -> None:
    for a in range_a:
        for b in range_b:
            if a not in {0, max_a} and b not in {0, max_b}:
                continue
            append_segment(
                *endpoint_builder(a, b),
                source_type=_boundary_segment_source_type(a, b, max_a=max_a, max_b=max_b),
            )


def _boundary_segment_source_type(a: int, b: int, *, max_a: int, max_b: int) -> str:
    if a in {0, max_a} and b in {0, max_b}:
        return "box_edge"
    return "gridline"


def draw_projected_line_fragments(
    surface: pygame.Surface,
    fragments: tuple[ProjectedLineFragment, ...],
    *,
    inner_color: tuple[int, int, int],
    frame_color: tuple[int, int, int],
    frame_width: int = 2,
) -> None:
    for fragment in fragments:
        color = inner_color if fragment.source_type == "gridline" else frame_color
        width = 1 if fragment.source_type == "gridline" else frame_width
        pygame.draw.line(surface, color, fragment.start, fragment.end, width)


def _project_line_primitive(
    raw_start: Point3,
    raw_end: Point3,
    *,
    project_raw: ProjectRawFn,
    transform_raw: TransformRawFn,
    depth_denominator: DepthDenominatorFn,
    source_type: str,
) -> ProjectedLinePrimitive | None:
    start = project_raw(raw_start)
    end = project_raw(raw_end)
    if start is None or end is None:
        return None
    start_transformed = transform_raw(raw_start)
    end_transformed = transform_raw(raw_end)
    return ProjectedLinePrimitive(
        start=start,
        end=end,
        start_depth=start_transformed[2],
        end_depth=end_transformed[2],
        start_denominator=depth_denominator(start_transformed[2]),
        end_denominator=depth_denominator(end_transformed[2]),
        source_type=source_type,
    )
