from __future__ import annotations

from dataclasses import dataclass

from tet4d.engine.runtime.project_config import project_constant_float
from tet4d.ui.pygame.projection3d import (
    Point2,
    ProjectedFacePrimitive,
    ProjectedLineFragment,
    ProjectedLinePrimitive,
)

_DEPTH_EPSILON = project_constant_float(
    ("rendering", "projected_occlusion", "depth_epsilon"),
    0.02,
    min_value=0.0,
    max_value=1.0,
)
_POINT_EPSILON_PX = project_constant_float(
    ("rendering", "projected_occlusion", "point_epsilon_px"),
    0.75,
    min_value=0.0,
    max_value=8.0,
)
_SPLIT_EPSILON_PX = project_constant_float(
    ("rendering", "projected_occlusion", "split_epsilon_px"),
    0.5,
    min_value=0.0,
    max_value=8.0,
)


@dataclass(frozen=True)
class SegmentOcclusionPolicy:
    depth_epsilon: float
    point_epsilon_px: float
    split_epsilon_px: float


@dataclass(frozen=True)
class OccludedSegmentBuckets:
    segments_under_piece: tuple[ProjectedLineFragment, ...]
    segments_over_piece: tuple[ProjectedLineFragment, ...]


_DEFAULT_POLICY = SegmentOcclusionPolicy(
    depth_epsilon=float(_DEPTH_EPSILON),
    point_epsilon_px=float(_POINT_EPSILON_PX),
    split_epsilon_px=float(_SPLIT_EPSILON_PX),
)


def default_segment_occlusion_policy() -> SegmentOcclusionPolicy:
    return _DEFAULT_POLICY


def resolve_board_line_occlusion(
    board_segments: tuple[ProjectedLinePrimitive, ...],
    piece_faces: tuple[ProjectedFacePrimitive, ...],
    *,
    policy: SegmentOcclusionPolicy | None = None,
) -> OccludedSegmentBuckets:
    active_policy = policy if policy is not None else _DEFAULT_POLICY
    if not board_segments:
        return OccludedSegmentBuckets((), ())
    if not piece_faces:
        return OccludedSegmentBuckets(
            tuple(
                ProjectedLineFragment(
                    start=segment.start,
                    end=segment.end,
                    source_type=segment.source_type,
                )
                for segment in board_segments
            ),
            (),
        )

    under: list[ProjectedLineFragment] = []
    over: list[ProjectedLineFragment] = []
    for segment in board_segments:
        for fragment, draw_over_piece in _classify_segment_fragments(
            segment,
            piece_faces,
            policy=active_policy,
        ):
            if draw_over_piece:
                over.append(fragment)
            else:
                under.append(fragment)
    return OccludedSegmentBuckets(tuple(under), tuple(over))


def _classify_segment_fragments(
    segment: ProjectedLinePrimitive,
    faces: tuple[ProjectedFacePrimitive, ...],
    *,
    policy: SegmentOcclusionPolicy,
) -> tuple[tuple[ProjectedLineFragment, bool], ...]:
    candidate_faces = tuple(
        face
        for face in faces
        if _bbox_overlaps(_segment_bbox(segment), _polygon_bbox(face.polygon))
    )
    if not candidate_faces:
        return (
            (
                ProjectedLineFragment(
                    start=segment.start,
                    end=segment.end,
                    source_type=segment.source_type,
                ),
                False,
            ),
        )

    split_params = [0.0, 1.0]
    for face in candidate_faces:
        split_params.extend(_polygon_edge_intersection_params(segment, face, policy))
    split_params = _sorted_unique_params(
        split_params,
        tolerance=policy.split_epsilon_px / max(_segment_length(segment), 1.0),
    )

    classified: list[tuple[ProjectedLineFragment, bool]] = []
    for start_t, end_t in zip(split_params, split_params[1:]):
        start = _interpolate_point(segment.start, segment.end, start_t)
        end = _interpolate_point(segment.start, segment.end, end_t)
        if _point_distance(start, end) <= policy.split_epsilon_px:
            continue
        mid_t = (start_t + end_t) * 0.5
        sample_point = _interpolate_point(segment.start, segment.end, mid_t)
        covering_faces = tuple(
            face
            for face in candidate_faces
            if _face_depth_at_point(face, sample_point, policy.point_epsilon_px)
            is not None
        )
        draw_over_piece = False
        if covering_faces:
            nearest_face_depth = min(
                depth
                for depth in (
                    _face_depth_at_point(face, sample_point, policy.point_epsilon_px)
                    for face in covering_faces
                )
                if depth is not None
            )
            segment_depth = _segment_depth_at_param(segment, mid_t)
            draw_over_piece = segment_depth + policy.depth_epsilon < nearest_face_depth
        classified.append(
            (
                ProjectedLineFragment(
                    start=start,
                    end=end,
                    source_type=segment.source_type,
                ),
                draw_over_piece,
            )
        )
    return tuple(classified)


def _face_depth_at_point(
    face: ProjectedFacePrimitive,
    point: Point2,
    point_epsilon_px: float,
) -> float | None:
    polygon = face.polygon
    if len(polygon) < 3:
        return None
    triangles = ((0, 1, 2),)
    if len(polygon) >= 4:
        triangles = ((0, 1, 2), (0, 2, 3))
    for tri in triangles:
        bary = _triangle_barycentric(
            point,
            polygon[tri[0]],
            polygon[tri[1]],
            polygon[tri[2]],
            point_epsilon_px,
        )
        if bary is None:
            continue
        weights = (
            bary[0] / face.vertex_denominators[tri[0]],
            bary[1] / face.vertex_denominators[tri[1]],
            bary[2] / face.vertex_denominators[tri[2]],
        )
        weight_total = weights[0] + weights[1] + weights[2]
        if abs(weight_total) <= 1e-9:
            continue
        return (
            weights[0] * face.vertex_depths[tri[0]]
            + weights[1] * face.vertex_depths[tri[1]]
            + weights[2] * face.vertex_depths[tri[2]]
        ) / weight_total
    return None


def _segment_depth_at_param(segment: ProjectedLinePrimitive, screen_t: float) -> float:
    weight_start = (1.0 - screen_t) / segment.start_denominator
    weight_end = screen_t / segment.end_denominator
    weight_total = weight_start + weight_end
    if abs(weight_total) <= 1e-9:
        return segment.start_depth
    return (
        weight_start * segment.start_depth + weight_end * segment.end_depth
    ) / weight_total


def _triangle_barycentric(
    point: Point2,
    a: Point2,
    b: Point2,
    c: Point2,
    epsilon_px: float,
) -> tuple[float, float, float] | None:
    det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(det) <= 1e-9:
        return None
    w0 = ((b[1] - c[1]) * (point[0] - c[0]) + (c[0] - b[0]) * (point[1] - c[1])) / det
    w1 = ((c[1] - a[1]) * (point[0] - c[0]) + (a[0] - c[0]) * (point[1] - c[1])) / det
    w2 = 1.0 - w0 - w1
    tolerance = _normalized_triangle_tolerance(a, b, c, epsilon_px)
    if w0 < -tolerance or w1 < -tolerance or w2 < -tolerance:
        return None
    return w0, w1, w2


def _normalized_triangle_tolerance(
    a: Point2,
    b: Point2,
    c: Point2,
    epsilon_px: float,
) -> float:
    scale = max(
        _point_distance(a, b),
        _point_distance(b, c),
        _point_distance(c, a),
        1.0,
    )
    return epsilon_px / scale


def _polygon_edge_intersection_params(
    segment: ProjectedLinePrimitive,
    face: ProjectedFacePrimitive,
    policy: SegmentOcclusionPolicy,
) -> tuple[float, ...]:
    polygon = face.polygon
    params: list[float] = []
    for index in range(len(polygon)):
        edge_start = polygon[index]
        edge_end = polygon[(index + 1) % len(polygon)]
        params.extend(
            _segment_intersection_params(
                segment.start,
                segment.end,
                edge_start,
                edge_end,
                policy.point_epsilon_px,
            )
        )
    return tuple(params)


def _segment_intersection_params(
    seg_start: Point2,
    seg_end: Point2,
    edge_start: Point2,
    edge_end: Point2,
    epsilon_px: float,
) -> tuple[float, ...]:
    seg_vec = (seg_end[0] - seg_start[0], seg_end[1] - seg_start[1])
    edge_vec = (edge_end[0] - edge_start[0], edge_end[1] - edge_start[1])
    cross = _cross(seg_vec, edge_vec)
    offset = (edge_start[0] - seg_start[0], edge_start[1] - seg_start[1])
    if abs(cross) <= 1e-9:
        if abs(_cross(offset, seg_vec)) > epsilon_px:
            return ()
        seg_len_sq = max(seg_vec[0] * seg_vec[0] + seg_vec[1] * seg_vec[1], 1e-9)
        return tuple(
            max(0.0, min(1.0, value))
            for value in (
                (
                    (edge_start[0] - seg_start[0]) * seg_vec[0]
                    + (edge_start[1] - seg_start[1]) * seg_vec[1]
                )
                / seg_len_sq,
                (
                    (edge_end[0] - seg_start[0]) * seg_vec[0]
                    + (edge_end[1] - seg_start[1]) * seg_vec[1]
                )
                / seg_len_sq,
            )
            if -0.01 <= value <= 1.01
        )
    seg_t = _cross(offset, edge_vec) / cross
    edge_t = _cross(offset, seg_vec) / cross
    if -0.01 <= seg_t <= 1.01 and -0.01 <= edge_t <= 1.01:
        return (max(0.0, min(1.0, seg_t)),)
    return ()


def _segment_bbox(segment: ProjectedLinePrimitive) -> tuple[float, float, float, float]:
    return (
        min(segment.start[0], segment.end[0]),
        min(segment.start[1], segment.end[1]),
        max(segment.start[0], segment.end[0]),
        max(segment.start[1], segment.end[1]),
    )


def _polygon_bbox(polygon: tuple[Point2, ...]) -> tuple[float, float, float, float]:
    xs = tuple(point[0] for point in polygon)
    ys = tuple(point[1] for point in polygon)
    return min(xs), min(ys), max(xs), max(ys)


def _bbox_overlaps(
    lhs: tuple[float, float, float, float],
    rhs: tuple[float, float, float, float],
) -> bool:
    return not (
        lhs[2] < rhs[0] or rhs[2] < lhs[0] or lhs[3] < rhs[1] or rhs[3] < lhs[1]
    )


def _sorted_unique_params(values: list[float], tolerance: float) -> list[float]:
    ordered = sorted(max(0.0, min(1.0, value)) for value in values)
    unique: list[float] = []
    for value in ordered:
        if not unique or abs(value - unique[-1]) > tolerance:
            unique.append(value)
    if not unique:
        return [0.0, 1.0]
    if unique[0] > 0.0:
        unique.insert(0, 0.0)
    if unique[-1] < 1.0:
        unique.append(1.0)
    return unique


def _segment_length(segment: ProjectedLinePrimitive) -> float:
    return _point_distance(segment.start, segment.end)


def _point_distance(start: Point2, end: Point2) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    return (dx * dx + dy * dy) ** 0.5


def _interpolate_point(start: Point2, end: Point2, amount: float) -> Point2:
    return (
        start[0] + (end[0] - start[0]) * amount,
        start[1] + (end[1] - start[1]) * amount,
    )


def _cross(lhs: Point2, rhs: Point2) -> float:
    return lhs[0] * rhs[1] - lhs[1] * rhs[0]


__all__ = [
    "OccludedSegmentBuckets",
    "SegmentOcclusionPolicy",
    "default_segment_occlusion_policy",
    "resolve_board_line_occlusion",
]
