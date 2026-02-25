# tetris_nd/pieces_nd.py
from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from .pieces2d import get_standard_tetrominoes
from .core.model import Coord


RelCoordND = Coord

PIECE_SET_3D_STANDARD = "native_3d"
PIECE_SET_3D_EMBED_2D = "embedded_2d"
PIECE_SET_3D_RANDOM = "random_cells_3d"
PIECE_SET_3D_DEBUG = "debug_rectangles_3d"
PIECE_SET_3D_OPTIONS = (
    PIECE_SET_3D_STANDARD,
    PIECE_SET_3D_EMBED_2D,
    PIECE_SET_3D_RANDOM,
    PIECE_SET_3D_DEBUG,
)

PIECE_SET_4D_STANDARD = "standard_4d_5"
PIECE_SET_4D_SIX = "standard_4d_6"
PIECE_SET_4D_EMBED_3D = "embedded_3d"
PIECE_SET_4D_EMBED_2D = "embedded_2d"
PIECE_SET_4D_RANDOM = "random_cells_4d"
PIECE_SET_4D_DEBUG = "debug_rectangles_4d"
PIECE_SET_4D_OPTIONS = (
    PIECE_SET_4D_STANDARD,
    PIECE_SET_4D_SIX,
    PIECE_SET_4D_EMBED_3D,
    PIECE_SET_4D_EMBED_2D,
    PIECE_SET_4D_RANDOM,
    PIECE_SET_4D_DEBUG,
)

DEFAULT_RANDOM_CELL_COUNT_3D = 5
DEFAULT_RANDOM_CELL_COUNT_4D = 5
DEFAULT_RANDOM_BAG_SIZE_ND = 7
_PIECE_SET_OPTIONS_BY_DIM = {
    3: PIECE_SET_3D_OPTIONS,
    4: PIECE_SET_4D_OPTIONS,
}


def _validate_ndim(ndim: int) -> None:
    if ndim < 2:
        raise ValueError("ndim must be >= 2")


def piece_set_options_for_dimension(ndim: int) -> Tuple[str, ...]:
    _validate_ndim(ndim)
    dim_key = 4 if ndim >= 4 else ndim
    if dim_key in _PIECE_SET_OPTIONS_BY_DIM:
        return _PIECE_SET_OPTIONS_BY_DIM[dim_key]
    # Kept for generic callers; ND gameplay currently starts at 3D.
    return (PIECE_SET_3D_EMBED_2D,)


def piece_set_label(piece_set_id: str) -> str:
    labels = {
        PIECE_SET_3D_STANDARD: "True 3D",
        PIECE_SET_3D_EMBED_2D: "Embedded 2D",
        PIECE_SET_3D_RANDOM: "Random Cells 3D",
        PIECE_SET_3D_DEBUG: "Debug Rectangles 3D",
        PIECE_SET_4D_STANDARD: "True 4D (5-cell)",
        PIECE_SET_4D_SIX: "True 4D (6-cell)",
        PIECE_SET_4D_EMBED_3D: "Embedded 3D",
        PIECE_SET_4D_EMBED_2D: "Embedded 2D",
        PIECE_SET_4D_RANDOM: "Random Cells 4D",
        PIECE_SET_4D_DEBUG: "Debug Rectangles 4D",
    }
    return labels.get(piece_set_id, piece_set_id)


def normalize_piece_set_4d(piece_set_4d: str | None) -> str:
    if piece_set_4d is None:
        return PIECE_SET_4D_STANDARD
    if piece_set_4d in PIECE_SET_4D_OPTIONS:
        return piece_set_4d
    raise ValueError(f"unsupported 4D piece set: {piece_set_4d}")


def normalize_piece_set_for_dimension(ndim: int, piece_set_id: str | None) -> str:
    options = piece_set_options_for_dimension(ndim)
    if piece_set_id is None:
        if ndim == 3:
            return PIECE_SET_3D_STANDARD
        if ndim >= 4:
            return PIECE_SET_4D_STANDARD
        return options[0]
    if piece_set_id in options:
        return piece_set_id
    raise ValueError(f"unsupported piece set for {ndim}D: {piece_set_id}")


def rotate_point_nd(
    point: Sequence[int],
    axis_a: int,
    axis_b: int,
    steps_cw: int,
) -> RelCoordND:
    """
    Rotate an integer lattice point by 90-degree steps in the (axis_a, axis_b) plane.
    Positive steps are clockwise using the same convention as 2D rotation.
    """
    ndim = len(point)
    _validate_ndim(ndim)
    if axis_a == axis_b:
        raise ValueError("rotation axes must be different")
    if not (0 <= axis_a < ndim and 0 <= axis_b < ndim):
        raise ValueError("rotation axis out of bounds")

    steps = steps_cw % 4
    coords = list(point)
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

    # steps == 3
    coords[axis_a] = -b_val
    coords[axis_b] = a_val
    return tuple(coords)


def lift_2d_blocks_to_nd(
    blocks_2d: Sequence[Tuple[int, int]],
    ndim: int,
) -> Tuple[RelCoordND, ...]:
    """
    Embed 2D blocks into N dimensions by appending zeros on extra axes.
    """
    _validate_ndim(ndim)
    extra_zeros = (0,) * (ndim - 2)
    return tuple((x, y) + extra_zeros for (x, y) in blocks_2d)


def _embed_blocks_to_nd(
    blocks: Sequence[Sequence[int]],
    ndim: int,
) -> Tuple[RelCoordND, ...]:
    """
    Embed lower-dimensional blocks into ndim by appending trailing zeros.
    """
    _validate_ndim(ndim)
    if not blocks:
        raise ValueError("blocks must be non-empty")
    src_dim = len(blocks[0])
    if src_dim > ndim:
        raise ValueError("source block dimension cannot exceed target ndim")
    for block in blocks:
        if len(block) != src_dim:
            raise ValueError("all blocks must have equal dimension")
    tail = (0,) * (ndim - src_dim)
    return tuple(tuple(block) + tail for block in blocks)


def _normalize_blocks_nd(blocks: Iterable[RelCoordND]) -> Tuple[RelCoordND, ...]:
    coords = list(blocks)
    if not coords:
        raise ValueError("piece must contain at least one block")
    ndim = len(coords[0])
    if ndim < 2:
        raise ValueError("piece dimension must be >= 2")
    for coord in coords:
        if len(coord) != ndim:
            raise ValueError("inconsistent coordinate dimensions")
    mins = [min(coord[axis] for coord in coords) for axis in range(ndim)]
    maxs = [max(coord[axis] for coord in coords) for axis in range(ndim)]
    centers = [(mins[axis] + maxs[axis]) // 2 for axis in range(ndim)]
    normalized = sorted(
        tuple(coord[axis] - centers[axis] for axis in range(ndim)) for coord in coords
    )
    return tuple(normalized)


def _axis_neighbors_nd(coord: RelCoordND) -> tuple[RelCoordND, ...]:
    neighbors: list[RelCoordND] = []
    for axis in range(len(coord)):
        for delta in (-1, 1):
            updated = list(coord)
            updated[axis] += delta
            neighbors.append(tuple(updated))
    return tuple(neighbors)


def _random_connected_blocks_nd(
    ndim: int,
    cell_count: int,
    rng: random.Random,
) -> Tuple[RelCoordND, ...]:
    _validate_ndim(ndim)
    if cell_count < 1:
        raise ValueError("cell_count must be >= 1")

    cells: set[RelCoordND] = {tuple(0 for _ in range(ndim))}
    attempts = 0
    max_attempts = max(50, cell_count * 120)
    while len(cells) < cell_count and attempts < max_attempts:
        base = rng.choice(tuple(cells))
        candidate = rng.choice(_axis_neighbors_nd(base))
        attempts += 1
        if candidate in cells:
            continue
        cells.add(candidate)

    # Guaranteed completion fallback.
    if len(cells) < cell_count:
        next_coord = [0] * ndim
        while len(cells) < cell_count:
            next_coord[0] += 1
            cells.add(tuple(next_coord))
    return _normalize_blocks_nd(cells)


def _random_piece_bag_nd(
    ndim: int,
    rng: random.Random,
    *,
    cell_count: int,
    bag_size: int = DEFAULT_RANDOM_BAG_SIZE_ND,
    name_prefix: str,
) -> List["PieceShapeND"]:
    bag_size = max(1, bag_size)
    cell_count = max(1, cell_count)
    seen: set[Tuple[RelCoordND, ...]] = set()
    shapes: List[PieceShapeND] = []
    attempts = 0
    max_attempts = bag_size * 160
    while len(shapes) < bag_size and attempts < max_attempts:
        blocks = _random_connected_blocks_nd(ndim, cell_count, rng)
        attempts += 1
        if blocks in seen:
            continue
        seen.add(blocks)
        idx = len(shapes) + 1
        shapes.append(
            PieceShapeND(
                name=f"{name_prefix}_{idx}",
                blocks=blocks,
                color_id=(idx - 1) % 7 + 1,
            )
        )
    while len(shapes) < bag_size:
        idx = len(shapes) + 1
        shapes.append(
            PieceShapeND(
                name=f"{name_prefix}_{idx}",
                blocks=_random_connected_blocks_nd(ndim, cell_count, rng),
                color_id=(idx - 1) % 7 + 1,
            )
        )
    return shapes


def _rect_blocks_nd(size_by_axis: Sequence[int]) -> Tuple[RelCoordND, ...]:
    coords: list[RelCoordND] = [tuple()]
    for axis_size in size_by_axis:
        if axis_size < 1:
            raise ValueError("axis sizes must be >= 1")
        expanded: list[RelCoordND] = []
        for base in coords:
            for value in range(axis_size):
                expanded.append((*base, value))
        coords = expanded
    return _normalize_blocks_nd(coords)


def _scaled_span(
    axis_size: int, ratio: float, min_size: int, max_cap: int | None = None
) -> int:
    clamped_axis = max(1, int(axis_size))
    scaled = max(min_size, int(round(clamped_axis * ratio)))
    scaled = min(scaled, clamped_axis)
    if max_cap is not None:
        scaled = min(scaled, max_cap)
    return max(1, scaled)


def _debug_board_dims(ndim: int, board_dims: Sequence[int] | None) -> tuple[int, ...]:
    if board_dims is None:
        defaults = (10, 20, 6, 4)
        if ndim <= len(defaults):
            return defaults[:ndim]
        return defaults + tuple(4 for _ in range(ndim - len(defaults)))
    dims = tuple(max(1, int(value)) for value in board_dims)
    if len(dims) >= ndim:
        return dims[:ndim]
    return dims + tuple(4 for _ in range(ndim - len(dims)))


def _extend_sizes(head: Sequence[int], ndim: int) -> tuple[int, ...]:
    return tuple(head) + tuple(1 for _ in range(max(0, ndim - len(head))))


def get_debug_rectangles_nd(
    ndim: int, board_dims: Sequence[int] | None = None
) -> List["PieceShapeND"]:
    _validate_ndim(ndim)
    dims = _debug_board_dims(ndim, board_dims)
    x_size = dims[0]
    y_size = dims[1]
    z_size = dims[2] if ndim >= 3 else 1
    w_size = dims[3] if ndim >= 4 else 1

    long_x = _scaled_span(x_size, 0.65, min_size=4, max_cap=10)
    thin_y = _scaled_span(y_size, 0.08, min_size=2, max_cap=2)
    thin_z = _scaled_span(z_size, 0.2, min_size=2, max_cap=2)
    thin_w = _scaled_span(w_size, 0.25, min_size=2, max_cap=2)

    flat_x = _scaled_span(x_size, 0.6, min_size=3, max_cap=9)
    flat_z = _scaled_span(z_size, 0.65, min_size=3, max_cap=5)

    thick_x = _scaled_span(x_size, 0.5, min_size=3, max_cap=7)
    thick_y = _scaled_span(y_size, 0.12, min_size=2, max_cap=3)
    thick_z = _scaled_span(z_size, 0.5, min_size=2, max_cap=4)

    layer_x = _scaled_span(x_size, 0.65, min_size=4, max_cap=10)
    layer_z = _scaled_span(z_size, 0.65, min_size=3, max_cap=5)
    layer_w = _scaled_span(w_size, 0.5, min_size=2, max_cap=3)

    specs: list[tuple[str, tuple[int, ...], int]] = [
        ("DBG_LONG_1D", _extend_sizes((long_x, 1), ndim), 1),
        ("DBG_LONG_2D", _extend_sizes((long_x, thin_y), ndim), 2),
    ]

    if ndim >= 3:
        specs.append(("DBG_LONG_3D", _extend_sizes((long_x, thin_y, thin_z), ndim), 3))
        specs.append(("DBG_SURFACE_FLAT", _extend_sizes((flat_x, 1, flat_z), ndim), 4))
        specs.append(
            ("DBG_SURFACE_THICK", _extend_sizes((thick_x, thick_y, thick_z), ndim), 5)
        )

    if ndim >= 4:
        specs.append(
            ("DBG_LONG_4D", _extend_sizes((long_x, thin_y, thin_z, thin_w), ndim), 6)
        )
        specs.append(
            ("DBG_LAYER_4D", _extend_sizes((layer_x, 1, layer_z, layer_w), ndim), 7)
        )

    return [
        PieceShapeND(name=name, blocks=_rect_blocks_nd(size_by_axis), color_id=color_id)
        for name, size_by_axis, color_id in specs
    ]


# True 3D polycube set (4 cells per piece).
_PIECES_3D: Tuple[Tuple[str, Tuple[Tuple[int, int, int], ...], int], ...] = (
    ("I3", ((-1, 0, 0), (0, 0, 0), (1, 0, 0), (2, 0, 0)), 1),
    ("O3", ((0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)), 2),
    ("L3", ((-1, 0, 0), (0, 0, 0), (1, 0, 0), (1, 1, 0)), 3),
    ("T3", ((-1, 0, 0), (0, 0, 0), (1, 0, 0), (0, 1, 0)), 4),
    ("S3", ((0, 0, 0), (1, 0, 0), (-1, 1, 0), (0, 1, 0)), 5),
    ("J3D", ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), 6),
    ("SCREW3", ((0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 1, 1)), 7),
)


# Dedicated 4D set (5 cells per piece) where each shape spans x, y, z, and w.
_PIECES_4D: Tuple[Tuple[str, Tuple[Tuple[int, int, int, int], ...], int], ...] = (
    (
        "CROSS4",
        ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)),
        1,
    ),
    (
        "SKEW4_A",
        ((0, 0, 0, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, 1, 1, 0), (0, 1, 1, 1)),
        2,
    ),
    (
        "SKEW4_B",
        ((0, 0, 0, 0), (1, 0, 0, 0), (1, -1, 0, 0), (1, -1, 1, 0), (1, -1, 1, 1)),
        3,
    ),
    (
        "TEE4",
        ((-1, 0, 0, 0), (0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 1, 0), (0, 1, 1, 1)),
        4,
    ),
    (
        "CORK4",
        ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (1, 1, 1, 0), (1, 1, 1, 1)),
        5,
    ),
    (
        "STAIR4",
        ((0, 0, 0, 0), (0, 1, 0, 0), (1, 1, 0, 0), (1, 1, 1, 0), (1, 1, 1, 1)),
        6,
    ),
    (
        "FORK4",
        ((0, 0, 0, 0), (-1, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 1), (0, 0, 1, 1)),
        7,
    ),
)


# Optional dedicated 4D set (6 cells per piece).
_PIECES_4D_SIX: Tuple[Tuple[str, Tuple[Tuple[int, int, int, int], ...], int], ...] = (
    (
        "CROSS6",
        (
            (0, 0, 0, 0),
            (-1, 0, 0, 0),
            (1, 0, 0, 0),
            (0, 1, 0, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 1),
        ),
        1,
    ),
    (
        "RIBBON6_A",
        (
            (0, 0, 0, 0),
            (1, 0, 0, 0),
            (1, 1, 0, 0),
            (1, 1, 1, 0),
            (1, 1, 1, 1),
            (0, 1, 1, 1),
        ),
        2,
    ),
    (
        "RIBBON6_B",
        (
            (0, 0, 0, 0),
            (-1, 0, 0, 0),
            (-1, 1, 0, 0),
            (-1, 1, 1, 0),
            (-1, 1, 1, 1),
            (0, 1, 1, 1),
        ),
        3,
    ),
    (
        "STAIR6",
        (
            (0, 0, 0, 0),
            (0, 1, 0, 0),
            (1, 1, 0, 0),
            (1, 1, 1, 0),
            (1, 1, 1, 1),
            (2, 1, 1, 1),
        ),
        4,
    ),
    (
        "FORK6",
        (
            (0, 0, 0, 0),
            (-1, 0, 0, 0),
            (1, 0, 0, 0),
            (0, 1, 0, 0),
            (0, 0, 1, 1),
            (0, 1, 1, 1),
        ),
        5,
    ),
    (
        "TWIST6",
        (
            (0, 0, 0, 0),
            (0, 1, 0, 0),
            (1, 1, 0, 0),
            (1, 1, 1, 0),
            (2, 1, 1, 0),
            (2, 1, 1, 1),
        ),
        6,
    ),
    (
        "PLANE6",
        (
            (0, 0, 0, 0),
            (1, 0, 0, 0),
            (0, 1, 0, 0),
            (1, 1, 0, 0),
            (1, 1, 1, 0),
            (1, 1, 1, 1),
        ),
        7,
    ),
)


@dataclass(frozen=True)
class PieceShapeND:
    name: str
    blocks: Tuple[RelCoordND, ...]
    color_id: int


PieceSetFactoryND = Callable[
    [int, random.Random | None, int | None, Sequence[int] | None],
    List[PieceShapeND],
]


def _shape_records_to_nd(
    records: Sequence[Tuple[str, Sequence[Sequence[int]], int]],
    ndim: int,
) -> List[PieceShapeND]:
    return [
        PieceShapeND(
            name=name, blocks=_embed_blocks_to_nd(blocks, ndim), color_id=color_id
        )
        for name, blocks, color_id in records
    ]


def _embedded_2d_shapes_nd(ndim: int) -> List[PieceShapeND]:
    return [
        PieceShapeND(
            name=f"{shape.name}_E2",
            blocks=lift_2d_blocks_to_nd(shape.blocks, ndim),
            color_id=shape.color_id,
        )
        for shape in get_standard_tetrominoes()
    ]


def _standard_3d_piece_set(
    ndim: int,
    _rng: random.Random | None,
    _random_cell_count: int | None,
    _board_dims: Sequence[int] | None,
) -> List[PieceShapeND]:
    return _shape_records_to_nd(_PIECES_3D, ndim)


def _embedded_2d_piece_set(
    ndim: int,
    _rng: random.Random | None,
    _random_cell_count: int | None,
    _board_dims: Sequence[int] | None,
) -> List[PieceShapeND]:
    return _embedded_2d_shapes_nd(ndim)


def _debug_piece_set(
    ndim: int,
    _rng: random.Random | None,
    _random_cell_count: int | None,
    board_dims: Sequence[int] | None,
) -> List[PieceShapeND]:
    return get_debug_rectangles_nd(ndim, board_dims=board_dims)


def _random_piece_set(
    ndim: int,
    rng: random.Random | None,
    random_cell_count: int | None,
    _board_dims: Sequence[int] | None,
    *,
    default_random_cell_count: int,
    name_prefix: str,
) -> List[PieceShapeND]:
    active_rng = rng if rng is not None else random.Random()
    count = (
        default_random_cell_count if random_cell_count is None else random_cell_count
    )
    return _random_piece_bag_nd(
        ndim,
        active_rng,
        cell_count=max(1, count),
        name_prefix=name_prefix,
    )


def _random_3d_piece_set(
    ndim: int,
    rng: random.Random | None,
    random_cell_count: int | None,
    board_dims: Sequence[int] | None,
) -> List[PieceShapeND]:
    return _random_piece_set(
        ndim,
        rng,
        random_cell_count,
        board_dims,
        default_random_cell_count=DEFAULT_RANDOM_CELL_COUNT_3D,
        name_prefix="R3",
    )


def _standard_4d_piece_set(
    ndim: int,
    _rng: random.Random | None,
    _random_cell_count: int | None,
    _board_dims: Sequence[int] | None,
) -> List[PieceShapeND]:
    return _shape_records_to_nd(_PIECES_4D, ndim)


def _six_cell_4d_piece_set(
    ndim: int,
    _rng: random.Random | None,
    _random_cell_count: int | None,
    _board_dims: Sequence[int] | None,
) -> List[PieceShapeND]:
    return _shape_records_to_nd(_PIECES_4D_SIX, ndim)


def _embedded_3d_piece_set(
    ndim: int,
    _rng: random.Random | None,
    _random_cell_count: int | None,
    _board_dims: Sequence[int] | None,
) -> List[PieceShapeND]:
    return _shape_records_to_nd(_PIECES_3D, ndim)


def _random_4d_piece_set(
    ndim: int,
    rng: random.Random | None,
    random_cell_count: int | None,
    board_dims: Sequence[int] | None,
) -> List[PieceShapeND]:
    return _random_piece_set(
        ndim,
        rng,
        random_cell_count,
        board_dims,
        default_random_cell_count=DEFAULT_RANDOM_CELL_COUNT_4D,
        name_prefix="R4",
    )


_PIECE_SET_FACTORIES_3D: dict[str, PieceSetFactoryND] = {
    PIECE_SET_3D_STANDARD: _standard_3d_piece_set,
    PIECE_SET_3D_EMBED_2D: _embedded_2d_piece_set,
    PIECE_SET_3D_RANDOM: _random_3d_piece_set,
    PIECE_SET_3D_DEBUG: _debug_piece_set,
}

_PIECE_SET_FACTORIES_4D: dict[str, PieceSetFactoryND] = {
    PIECE_SET_4D_STANDARD: _standard_4d_piece_set,
    PIECE_SET_4D_SIX: _six_cell_4d_piece_set,
    PIECE_SET_4D_EMBED_3D: _embedded_3d_piece_set,
    PIECE_SET_4D_EMBED_2D: _embedded_2d_piece_set,
    PIECE_SET_4D_RANDOM: _random_4d_piece_set,
    PIECE_SET_4D_DEBUG: _debug_piece_set,
}

_PIECE_SET_FACTORIES_BY_DIM = {
    3: _PIECE_SET_FACTORIES_3D,
    4: _PIECE_SET_FACTORIES_4D,
}


def _piece_set_factories_for_dimension(ndim: int) -> dict[str, PieceSetFactoryND]:
    dim_key = 4 if ndim >= 4 else ndim
    factories = _PIECE_SET_FACTORIES_BY_DIM.get(dim_key)
    if factories is None:
        raise ValueError(f"unsupported piece-set dimension: {ndim}")
    return factories


def get_piece_shapes_nd(
    ndim: int,
    *,
    piece_set_id: str | None = None,
    piece_set_4d: str | None = None,
    random_cell_count: int | None = None,
    rng: random.Random | None = None,
    board_dims: Sequence[int] | None = None,
) -> List[PieceShapeND]:
    _validate_ndim(ndim)

    if ndim == 2:
        return _embedded_2d_shapes_nd(ndim)

    selected = piece_set_id
    if selected is None and ndim >= 4 and piece_set_4d is not None:
        selected = normalize_piece_set_4d(piece_set_4d)
    selected = normalize_piece_set_for_dimension(ndim, selected)
    factories = _piece_set_factories_for_dimension(ndim)
    factory = factories.get(selected)
    if factory is None:
        raise ValueError(f"unsupported piece set for {ndim}D: {selected}")
    return factory(ndim, rng, random_cell_count, board_dims)


def get_standard_pieces_nd(
    ndim: int, piece_set_4d: str | None = None
) -> List[PieceShapeND]:
    """
    Backward-compatible API:
    - 2D: classic tetrominoes
    - 3D: true 3D polycubes
    - 4D+: 4D set selected via piece_set_4d
    """
    if ndim == 2:
        return _embedded_2d_shapes_nd(2)
    if ndim == 3:
        return get_piece_shapes_nd(3, piece_set_id=PIECE_SET_3D_STANDARD)
    return get_piece_shapes_nd(
        ndim,
        piece_set_id=normalize_piece_set_4d(piece_set_4d),
    )


@dataclass(frozen=True)
class ActivePieceND:
    """
    A falling ND piece.
    Position is the pivot coordinate in board space.
    rel_blocks contains oriented offsets from that pivot.
    """

    shape: PieceShapeND
    pos: Coord
    rel_blocks: Tuple[RelCoordND, ...]

    def __post_init__(self) -> None:
        ndim = len(self.pos)
        _validate_ndim(ndim)
        if not self.rel_blocks:
            raise ValueError("piece must have at least one block")
        for block in self.rel_blocks:
            if len(block) != ndim:
                raise ValueError("block dimension does not match piece position")

    @classmethod
    def from_shape(cls, shape: PieceShapeND, pos: Coord) -> "ActivePieceND":
        if not shape.blocks:
            raise ValueError("shape has no blocks")
        if len(shape.blocks[0]) != len(pos):
            raise ValueError("shape dimension does not match position dimension")
        return cls(shape=shape, pos=pos, rel_blocks=shape.blocks)

    def cells(self) -> List[Coord]:
        result: List[Coord] = []
        for block in self.rel_blocks:
            result.append(tuple(p + b for p, b in zip(self.pos, block)))
        return result

    def moved(self, delta: Sequence[int]) -> "ActivePieceND":
        if len(delta) != len(self.pos):
            raise ValueError("delta dimension mismatch")
        new_pos = tuple(p + d for p, d in zip(self.pos, delta))
        return ActivePieceND(shape=self.shape, pos=new_pos, rel_blocks=self.rel_blocks)

    def rotated(self, axis_a: int, axis_b: int, delta_steps: int) -> "ActivePieceND":
        new_blocks = tuple(
            rotate_point_nd(block, axis_a=axis_a, axis_b=axis_b, steps_cw=delta_steps)
            for block in self.rel_blocks
        )
        return ActivePieceND(shape=self.shape, pos=self.pos, rel_blocks=new_blocks)
