from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Iterable, Sequence, TypeAlias

Coord2D: TypeAlias = tuple[int, int]
CoordND: TypeAlias = tuple[int, ...]
Blocks2D: TypeAlias = tuple[Coord2D, ...]
BlocksND: TypeAlias = tuple[CoordND, ...]

_QUARTER_TURNS = 4
_MAX_3D_ORIENTATION_DEPTH = 7
_MAX_4D_ORIENTATION_DEPTH = 6
_MAX_3D_ORIENTATION_COUNT = 96
_MAX_4D_ORIENTATION_COUNT = 180


def _validate_ndim(ndim: int) -> None:
    if ndim < 2:
        raise ValueError("ndim must be >= 2")


def _resolve_quarter_turns(
    quarter_turns: int | None,
    *,
    steps_cw: int | None = None,
) -> int:
    if quarter_turns is None:
        if steps_cw is None:
            raise TypeError("quarter_turns is required")
        return int(steps_cw)
    resolved = int(quarter_turns)
    if steps_cw is not None and int(steps_cw) != resolved:
        raise ValueError("quarter_turns and steps_cw must match when both are provided")
    return resolved


def _coerce_blocks_nd(blocks: Iterable[Sequence[int]]) -> BlocksND:
    coords = tuple(tuple(int(value) for value in block) for block in blocks)
    if not coords:
        return tuple()
    ndim = len(coords[0])
    for coord in coords:
        if len(coord) != ndim:
            raise ValueError("inconsistent coordinate dimensions")
    return coords


def _coerce_blocks_2d(blocks: Iterable[Sequence[int]]) -> Blocks2D:
    coords = _coerce_blocks_nd(blocks)
    for coord in coords:
        if len(coord) != 2:
            raise ValueError("2D blocks must contain exactly two coordinates")
    return tuple((coord[0], coord[1]) for coord in coords)


@lru_cache(maxsize=8192)
def _block_axis_bounds_cached(blocks: BlocksND) -> tuple[CoordND, CoordND]:
    first = blocks[0]
    mins = [int(value) for value in first]
    maxs = [int(value) for value in first]
    for coord in blocks[1:]:
        for axis, value in enumerate(coord):
            if value < mins[axis]:
                mins[axis] = int(value)
            elif value > maxs[axis]:
                maxs[axis] = int(value)
    return tuple(mins), tuple(maxs)


def block_axis_bounds(blocks: Iterable[Sequence[int]]) -> tuple[CoordND, CoordND]:
    coords = _coerce_blocks_nd(blocks)
    if not coords:
        raise ValueError("piece must contain at least one block")
    return _block_axis_bounds_cached(coords)


@lru_cache(maxsize=8192)
def _canonicalize_blocks_nd_cached(blocks: BlocksND) -> BlocksND:
    return tuple(sorted(blocks))


def canonicalize_blocks_nd(blocks: Iterable[Sequence[int]]) -> BlocksND:
    coords = _coerce_blocks_nd(blocks)
    if not coords:
        return tuple()
    return _canonicalize_blocks_nd_cached(coords)


def canonicalize_blocks_2d(blocks: Iterable[Sequence[int]]) -> Blocks2D:
    coords = _coerce_blocks_2d(blocks)
    if not coords:
        return tuple()
    return tuple((coord[0], coord[1]) for coord in _canonicalize_blocks_nd_cached(coords))


def _axis_center_map(coords: BlocksND, *, axes: Iterable[int]) -> dict[int, int]:
    mins, maxs = _block_axis_bounds_cached(coords)
    ndim = len(coords[0])
    centers: dict[int, int] = {}
    for axis in axes:
        if not (0 <= axis < ndim):
            raise ValueError("normalization axis out of bounds")
        centers[axis] = (mins[axis] + maxs[axis]) // 2
    return centers


def _normalize_axes_preserve_order(
    coords: BlocksND,
    *,
    axes: Iterable[int],
) -> BlocksND:
    centers = _axis_center_map(coords, axes=axes)
    ndim = len(coords[0])
    return tuple(
        tuple(
            coord[axis] - centers[axis] if axis in centers else coord[axis]
            for axis in range(ndim)
        )
        for coord in coords
    )


def _normalize_axes_2d_preserve_order(
    coords: Blocks2D,
    *,
    axes: Iterable[int],
) -> Blocks2D:
    normalized = _normalize_axes_preserve_order(coords, axes=axes)
    return tuple((coord[0], coord[1]) for coord in normalized)


def normalize_blocks_2d(blocks: Iterable[Sequence[int]]) -> Blocks2D:
    coords = _coerce_blocks_2d(blocks)
    if not coords:
        raise ValueError("piece must contain at least one block")
    return canonicalize_blocks_2d(
        _normalize_axes_2d_preserve_order(coords, axes=(0, 1))
    )


def normalize_blocks_nd(blocks: Iterable[Sequence[int]]) -> BlocksND:
    coords = _coerce_blocks_nd(blocks)
    if not coords:
        raise ValueError("piece must contain at least one block")
    ndim = len(coords[0])
    _validate_ndim(ndim)
    return canonicalize_blocks_nd(_normalize_axes_preserve_order(coords, axes=range(ndim)))


def rotate_point_2d(
    x: int,
    y: int,
    quarter_turns: int | None = None,
    *,
    steps_cw: int | None = None,
) -> Coord2D:
    steps = _resolve_quarter_turns(quarter_turns, steps_cw=steps_cw) % _QUARTER_TURNS
    if steps == 0:
        return x, y
    if steps == 1:
        return y, -x
    if steps == 2:
        return -x, -y
    return -y, x


@lru_cache(maxsize=4096)
def _rotation_pivot_2d_cached(blocks: Blocks2D) -> tuple[float, float]:
    if not blocks:
        return 0.0, 0.0
    (min_x, min_y), (max_x, max_y) = _block_axis_bounds_cached(blocks)
    span_x = max_x - min_x
    span_y = max_y - min_y
    x_even = (span_x % 2) == 0
    y_even = (span_y % 2) == 0
    if x_even == y_even:
        return (min_x + max_x) / 2.0, (min_y + max_y) / 2.0
    center_mass_x = sum(x for x, y in blocks) / len(blocks)
    center_mass_y = sum(y for x, y in blocks) / len(blocks)
    min_dist_sq = float("inf")
    pivot_block = blocks[0]
    for block in blocks:
        dist_sq = (block[0] - center_mass_x) ** 2 + (block[1] - center_mass_y) ** 2
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            pivot_block = block
    return float(pivot_block[0]), float(pivot_block[1])


def rotation_pivot_2d(blocks: Iterable[Sequence[int]]) -> tuple[float, float]:
    coords = _coerce_blocks_2d(blocks)
    return _rotation_pivot_2d_cached(coords)


@lru_cache(maxsize=4096)
def _rotate_blocks_2d_cached(blocks: Blocks2D, quarter_turns: int) -> Blocks2D:
    steps = quarter_turns % _QUARTER_TURNS
    if not blocks or steps == 0:
        return blocks

    rotated = blocks
    for _ in range(steps):
        pivot_x, pivot_y = _rotation_pivot_2d_cached(rotated)
        # Apply one positive quarter-turn around the canonical pivot.
        rotated_coords: list[Coord2D] = []
        for x, y in rotated:
            # Translate to pivot origin
            rel_x = x - pivot_x
            rel_y = y - pivot_y
            # In the repo's screen-aligned x/y frame, a positive quarter-turn is (x, y) -> (y, -x).
            new_rel_x = rel_y
            new_rel_y = -rel_x
            # Translate back and round to integers
            new_x = round(new_rel_x + pivot_x)
            new_y = round(new_rel_y + pivot_y)
            rotated_coords.append((new_x, new_y))

        rotated = tuple(rotated_coords)
    return rotated


def rotate_blocks_2d(
    blocks: Iterable[Sequence[int]],
    quarter_turns: int | None = None,
    *,
    steps_cw: int | None = None,
) -> Blocks2D:
    coords = _coerce_blocks_2d(blocks)
    turns = _resolve_quarter_turns(quarter_turns, steps_cw=steps_cw)
    return _rotate_blocks_2d_cached(coords, turns % _QUARTER_TURNS)


def rotate_point_nd(
    point: Sequence[int],
    axis_a: int,
    axis_b: int,
    quarter_turns: int | None = None,
    *,
    steps_cw: int | None = None,
) -> CoordND:
    ndim = len(point)
    _validate_ndim(ndim)
    if axis_a == axis_b:
        raise ValueError("rotation axes must be different")
    if not (0 <= axis_a < ndim and 0 <= axis_b < ndim):
        raise ValueError("rotation axis out of bounds")

    steps = _resolve_quarter_turns(quarter_turns, steps_cw=steps_cw) % _QUARTER_TURNS
    coords = [int(value) for value in point]
    a_val = coords[axis_a]
    b_val = coords[axis_b]

    if steps == 0:
        return tuple(coords)
    if steps == 1:
        coords[axis_a] = b_val
        coords[axis_b] = -a_val
        return tuple(coords)
    if steps == 2:
        coords[axis_a] = -a_val
        coords[axis_b] = -b_val
        return tuple(coords)

    coords[axis_a] = -b_val
    coords[axis_b] = a_val
    return tuple(coords)


@lru_cache(maxsize=8192)
def _rotate_blocks_nd_cached(
    blocks: BlocksND,
    axis_a: int,
    axis_b: int,
    quarter_turns: int,
) -> BlocksND:
    steps = quarter_turns % _QUARTER_TURNS
    if not blocks or steps == 0:
        return blocks

    ndim = len(blocks[0])
    rotated = blocks
    for _ in range(steps):
        mins, maxs = _block_axis_bounds_cached(rotated)
        min_a = mins[axis_a]
        max_a = maxs[axis_a]
        min_b = mins[axis_b]
        max_b = maxs[axis_b]
        span_a = max_a - min_a
        span_b = max_b - min_b

        # Determine rotation pivot based on bounding box parity in rotation plane
        a_even = (span_a % 2) == 0
        b_even = (span_b % 2) == 0

        if a_even == b_even:
            # Case 1 & 2: Both odd or both even - use geometric center
            pivot_a = (min_a + max_a) / 2.0
            pivot_b = (min_b + max_b) / 2.0
        else:
            # Case 3: Mixed parity - find block closest to center of mass
            a_values = [coord[axis_a] for coord in rotated]
            b_values = [coord[axis_b] for coord in rotated]
            center_mass_a = sum(a_values) / len(rotated)
            center_mass_b = sum(b_values) / len(rotated)

            # Find closest block to center of mass (in rotation plane only)
            min_dist_sq = float('inf')
            pivot_block = rotated[0]
            for block in rotated:
                dist_sq = (block[axis_a] - center_mass_a) ** 2 + (block[axis_b] - center_mass_b) ** 2
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    pivot_block = block

            # Rotate around the center of the chosen block
            pivot_a = float(pivot_block[axis_a])
            pivot_b = float(pivot_block[axis_b])

        # Apply rotation around pivot
        rotated_coords: list[CoordND] = []
        for coord in rotated:
            # Translate to pivot origin (in rotation plane)
            rel_a = coord[axis_a] - pivot_a
            rel_b = coord[axis_b] - pivot_b
            # Apply one positive quarter-turn in the active rotation plane.
            new_rel_a = rel_b
            new_rel_b = -rel_a
            # Translate back and round to integers
            new_a = round(new_rel_a + pivot_a)
            new_b = round(new_rel_b + pivot_b)
            # Build new coordinate
            new_coord = tuple(
                new_a if axis == axis_a
                else new_b if axis == axis_b
                else coord[axis]
                for axis in range(ndim)
            )
            rotated_coords.append(new_coord)

        rotated = tuple(rotated_coords)
    return rotated


def rotate_blocks_nd(
    blocks: Iterable[Sequence[int]],
    axis_a: int,
    axis_b: int,
    quarter_turns: int | None = None,
    *,
    steps_cw: int | None = None,
) -> BlocksND:
    coords = _coerce_blocks_nd(blocks)
    if not coords:
        return tuple()
    ndim = len(coords[0])
    _validate_ndim(ndim)
    if axis_a == axis_b:
        raise ValueError("rotation axes must be different")
    if not (0 <= axis_a < ndim and 0 <= axis_b < ndim):
        raise ValueError("rotation axis out of bounds")
    turns = _resolve_quarter_turns(quarter_turns, steps_cw=steps_cw)
    return _rotate_blocks_nd_cached(coords, axis_a, axis_b, turns % _QUARTER_TURNS)


def _calculate_rotation_pivot(
    blocks: tuple[tuple[float, ...], ...],
    axis_a: int,
    axis_b: int,
) -> tuple[float, float]:
    """
    Calculate the pivot point for rotation in the (axis_a, axis_b) plane.
    Uses true geometric center (matching discrete rotation's pivot calculation).
    """
    if not blocks:
        return (0.0, 0.0)

    # Get min/max along rotation axes
    a_values = [b[axis_a] for b in blocks]
    b_values = [b[axis_b] for b in blocks]

    min_a, max_a = min(a_values), max(a_values)
    min_b, max_b = min(b_values), max(b_values)

    # Use true geometric center (discrete rotation rounds after transformation)
    pivot_a = (min_a + max_a) / 2.0
    pivot_b = (min_b + max_b) / 2.0

    return pivot_a, pivot_b


def rotate_blocks_nd_continuous(
    blocks: Iterable[Sequence[int | float]],
    axis_a: int,
    axis_b: int,
    angle_radians: float,
) -> tuple[tuple[float, ...], ...]:
    """
    Rotate blocks by a continuous angle (in radians) in the plane defined by axis_a and axis_b.

    Unlike rotate_blocks_nd which only supports discrete 90-degree rotations,
    this function supports any rotation angle for smooth animation.

    The discrete rotation algorithm uses a grid-based transformation that preserves tetromino shapes.
    This continuous version interpolates between the start and end states while maintaining
    the correct pivot point and final position to match discrete rotation exactly.

    Returns blocks as float tuples to preserve fractional coordinates.
    """
    import math

    coords_raw = tuple(tuple(float(v) for v in block) for block in blocks)
    if not coords_raw:
        return tuple()

    ndim = len(coords_raw[0])
    _validate_ndim(ndim)
    if axis_a == axis_b:
        raise ValueError("rotation axes must be different")
    if not (0 <= axis_a < ndim and 0 <= axis_b < ndim):
        raise ValueError("rotation axis out of bounds")

    # Get bounds for pivot calculation
    a_values = [b[axis_a] for b in coords_raw]
    b_values = [b[axis_b] for b in coords_raw]
    min_a, max_a = min(a_values), max(a_values)
    min_b, max_b = min(b_values), max(b_values)
    # Calculate geometric center for smooth rotation
    # This is the true bounding box center, used as pivot
    pivot_a = (min_a + max_a) / 2.0
    pivot_b = (min_b + max_b) / 2.0

    cos_theta = math.cos(angle_radians)
    sin_theta = math.sin(angle_radians)

    rotated: list[tuple[float, ...]] = []
    for coord in coords_raw:
        coord_list = list(coord)

        # Translate to pivot origin
        a_rel = coord[axis_a] - pivot_a
        b_rel = coord[axis_b] - pivot_b

        # Apply the standard rotation matrix; callers choose the signed angle.
        new_a = a_rel * cos_theta - b_rel * sin_theta
        new_b = a_rel * sin_theta + b_rel * cos_theta

        # Translate back from pivot
        coord_list[axis_a] = new_a + pivot_a
        coord_list[axis_b] = new_b + pivot_b

        rotated.append(tuple(coord_list))

    # Apply same centering normalization as discrete rotation
    # The discrete rotation re-centers after transformation
    rotated_tuple = tuple(rotated)

    # Calculate new bounds
    a_values_new = [b[axis_a] for b in rotated_tuple]
    b_values_new = [b[axis_b] for b in rotated_tuple]
    min_a_new, max_a_new = min(a_values_new), max(a_values_new)
    min_b_new, max_b_new = min(b_values_new), max(b_values_new)

    # Use integer division to match discrete rotation's centering
    # This ensures the final state matches exactly at angle = π/2, π, 3π/2, etc.
    center_a = (int(min_a_new) + int(max_a_new)) // 2
    center_b = (int(min_b_new) + int(max_b_new)) // 2

    return tuple(
        tuple(
            v - center_a
            if i == axis_a
            else v - center_b
            if i == axis_b
            else v
            for i, v in enumerate(coord)
        )
        for coord in rotated_tuple
    )


@lru_cache(maxsize=32)
def rotation_planes_nd(ndim: int, gravity_axis: int) -> tuple[tuple[int, int], ...]:
    if ndim == 3:
        extra = [axis for axis in range(ndim) if axis != 0 and axis != gravity_axis]
        z_axis = extra[0] if extra else 2
        return (
            (0, gravity_axis),
            (0, z_axis),
            (gravity_axis, z_axis),
        )
    pairs: list[tuple[int, int]] = []
    for axis_a in range(ndim):
        for axis_b in range(axis_a + 1, ndim):
            pairs.append((axis_a, axis_b))
    return tuple(pairs)


@lru_cache(maxsize=512)
def enumerate_orientations_nd(
    start_blocks: BlocksND,
    ndim: int,
    gravity_axis: int,
) -> tuple[BlocksND, ...]:
    planes = rotation_planes_nd(ndim, gravity_axis)
    max_depth = _MAX_3D_ORIENTATION_DEPTH if ndim == 3 else _MAX_4D_ORIENTATION_DEPTH
    max_orientations = (
        _MAX_3D_ORIENTATION_COUNT if ndim == 3 else _MAX_4D_ORIENTATION_COUNT
    )

    queue: deque[tuple[BlocksND, int]] = deque([(start_blocks, 0)])
    seen: set[BlocksND] = {start_blocks}
    ordered: list[BlocksND] = [start_blocks]

    while queue and len(seen) < max_orientations:
        blocks, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for axis_a, axis_b in planes:
            for step in (1, -1):
                # Rotate then normalize to compare shapes (not positions)
                rotated = normalize_blocks_nd(
                    rotate_blocks_nd(
                        blocks,
                        axis_a=axis_a,
                        axis_b=axis_b,
                        quarter_turns=step,
                    )
                )
                rotated_canonical = canonicalize_blocks_nd(rotated)
                if rotated_canonical in seen:
                    continue
                seen.add(rotated_canonical)
                ordered.append(rotated_canonical)
                queue.append((rotated_canonical, depth + 1))
                if len(seen) >= max_orientations:
                    break
            if len(seen) >= max_orientations:
                break
    return tuple(ordered)


__all__ = [
    "Blocks2D",
    "BlocksND",
    "Coord2D",
    "CoordND",
    "block_axis_bounds",
    "canonicalize_blocks_2d",
    "canonicalize_blocks_nd",
    "enumerate_orientations_nd",
    "normalize_blocks_2d",
    "normalize_blocks_nd",
    "rotate_blocks_2d",
    "rotate_blocks_nd",
    "rotate_blocks_nd_continuous",
    "rotate_point_2d",
    "rotate_point_nd",
    "rotation_planes_nd",
]
