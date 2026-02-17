from __future__ import annotations

import math
from collections.abc import Callable

import pygame

Point2 = tuple[float, float]
Point3 = tuple[float, float, float]
Cell3 = tuple[int, int, int]
Face = tuple[float, list[Point2], tuple[int, int, int], bool]
ProjectRawFn = Callable[[Point3], Point2 | None]
TransformRawFn = Callable[[Point3], Point3]

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
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
]

_BOX_FACES: list[list[int]] = [
    [0, 1, 2, 3],
    [4, 5, 6, 7],
    [0, 1, 5, 4],
    [3, 2, 6, 7],
    [0, 3, 7, 4],
    [1, 2, 6, 5],
]


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
    width, height = surface.get_size()
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))


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
    return [
        (-0.5, -0.5, -0.5),
        (dims[0] - 0.5, -0.5, -0.5),
        (dims[0] - 0.5, dims[1] - 0.5, -0.5),
        (-0.5, dims[1] - 0.5, -0.5),
        (-0.5, -0.5, dims[2] - 0.5),
        (dims[0] - 0.5, -0.5, dims[2] - 0.5),
        (dims[0] - 0.5, dims[1] - 0.5, dims[2] - 0.5),
        (-0.5, dims[1] - 0.5, dims[2] - 0.5),
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


def _draw_lattice_axis_lines(
    surface: pygame.Surface,
    dims: Cell3,
    project_raw: ProjectRawFn,
    color: tuple[int, int, int],
    x_marks: set[int] | None = None,
    y_marks: set[int] | None = None,
    z_marks: set[int] | None = None,
) -> None:
    # Lines parallel to Y axis at (x, z) boundaries.
    for x in range(dims[0] + 1):
        if x_marks is not None and x not in x_marks:
            continue
        for z in range(dims[2] + 1):
            if z_marks is not None and z not in z_marks:
                continue
            p0 = project_raw((x - 0.5, -0.5, z - 0.5))
            p1 = project_raw((x - 0.5, dims[1] - 0.5, z - 0.5))
            if p0 is not None and p1 is not None:
                pygame.draw.line(surface, color, p0, p1, 1)

    # Lines parallel to X axis at (y, z) boundaries.
    for y in range(dims[1] + 1):
        if y_marks is not None and y not in y_marks:
            continue
        for z in range(dims[2] + 1):
            if z_marks is not None and z not in z_marks:
                continue
            p0 = project_raw((-0.5, y - 0.5, z - 0.5))
            p1 = project_raw((dims[0] - 0.5, y - 0.5, z - 0.5))
            if p0 is not None and p1 is not None:
                pygame.draw.line(surface, color, p0, p1, 1)

    # Lines parallel to Z axis at (x, y) boundaries.
    for x in range(dims[0] + 1):
        if x_marks is not None and x not in x_marks:
            continue
        for y in range(dims[1] + 1):
            if y_marks is not None and y not in y_marks:
                continue
            p0 = project_raw((x - 0.5, y - 0.5, -0.5))
            p1 = project_raw((x - 0.5, y - 0.5, dims[2] - 0.5))
            if p0 is not None and p1 is not None:
                pygame.draw.line(surface, color, p0, p1, 1)


def _draw_lattice_frame(
    surface: pygame.Surface,
    dims: Cell3,
    project_raw: ProjectRawFn,
    color: tuple[int, int, int],
    width: int,
) -> None:
    projected: list[Point2 | None] = [project_raw(raw) for raw in box_raw_corners(dims)]
    for a, b in _BOX_EDGES:
        pa = projected[a]
        pb = projected[b]
        if pa is not None and pb is not None:
            pygame.draw.line(surface, color, pa, pb, width)


def draw_projected_lattice(
    surface: pygame.Surface,
    dims: Cell3,
    project_raw: ProjectRawFn,
    inner_color: tuple[int, int, int],
    frame_color: tuple[int, int, int],
    frame_width: int = 2,
) -> None:
    _draw_lattice_axis_lines(surface, dims, project_raw, inner_color)
    _draw_lattice_frame(surface, dims, project_raw, frame_color, frame_width)


def draw_projected_helper_lattice(
    surface: pygame.Surface,
    dims: Cell3,
    project_raw: ProjectRawFn,
    x_marks: set[int],
    y_marks: set[int],
    z_marks: set[int],
    inner_color: tuple[int, int, int],
    frame_color: tuple[int, int, int],
    frame_width: int = 2,
) -> None:
    def _clip_marks(marks: set[int], max_value: int) -> set[int]:
        return {value for value in marks if 0 <= value <= max_value}

    _draw_lattice_axis_lines(
        surface,
        dims,
        project_raw,
        inner_color,
        x_marks=_clip_marks(x_marks, dims[0]),
        y_marks=_clip_marks(y_marks, dims[1]),
        z_marks=_clip_marks(z_marks, dims[2]),
    )
    _draw_lattice_frame(surface, dims, project_raw, frame_color, frame_width)


def draw_projected_box_edges(
    surface: pygame.Surface,
    dims: Cell3,
    project_raw: ProjectRawFn,
    edge_color: tuple[int, int, int] = (96, 118, 164),
    edge_width: int = 2,
) -> None:
    _draw_lattice_frame(surface, dims, project_raw, edge_color, edge_width)


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
) -> list[Face]:
    transformed: list[Point3] = []
    projected: list[Point2] = []

    for ox, oy, oz in _CUBE_VERTS:
        raw = (cell[0] + ox, cell[1] + oy, cell[2] + oz)
        transformed.append(transform_raw(raw))
        projected_point = project_raw(raw)
        if projected_point is None:
            return []
        projected.append(projected_point)

    faces: list[Face] = []
    for face_indices, shade_factor in _CUBE_FACES:
        polygon = [projected[i] for i in face_indices]
        avg_depth = sum(transformed[i][2] for i in face_indices) / 4.0
        factor = shade_factor * (active_boost if active else 1.0)
        faces.append((avg_depth, polygon, shade_color(color, factor), active))
    return faces
