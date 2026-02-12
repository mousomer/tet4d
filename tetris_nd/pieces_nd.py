# tetris_nd/pieces_nd.py
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from .pieces2d import get_standard_tetrominoes
from .types import Coord


RelCoordND = Coord

PIECE_SET_4D_STANDARD = "standard_4d_5"
PIECE_SET_4D_SIX = "standard_4d_6"
PIECE_SET_4D_OPTIONS = (PIECE_SET_4D_STANDARD, PIECE_SET_4D_SIX)


def _validate_ndim(ndim: int) -> None:
    if ndim < 2:
        raise ValueError("ndim must be >= 2")


def rotate_point_nd(point: Sequence[int],
                    axis_a: int,
                    axis_b: int,
                    steps_cw: int) -> RelCoordND:
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


def lift_2d_blocks_to_nd(blocks_2d: Sequence[Tuple[int, int]],
                         ndim: int) -> Tuple[RelCoordND, ...]:
    """
    Embed 2D blocks into N dimensions by appending zeros on extra axes.
    """
    _validate_ndim(ndim)
    extra_zeros = (0,) * (ndim - 2)
    return tuple((x, y) + extra_zeros for (x, y) in blocks_2d)


def _embed_blocks_to_nd(blocks: Sequence[Sequence[int]],
                        ndim: int) -> Tuple[RelCoordND, ...]:
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
    ("CROSS4", ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)), 1),
    ("SKEW4_A", ((0, 0, 0, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, 1, 1, 0), (0, 1, 1, 1)), 2),
    ("SKEW4_B", ((0, 0, 0, 0), (1, 0, 0, 0), (1, -1, 0, 0), (1, -1, 1, 0), (1, -1, 1, 1)), 3),
    ("TEE4", ((-1, 0, 0, 0), (0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 1, 0), (0, 1, 1, 1)), 4),
    ("CORK4", ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (1, 1, 1, 0), (1, 1, 1, 1)), 5),
    ("STAIR4", ((0, 0, 0, 0), (0, 1, 0, 0), (1, 1, 0, 0), (1, 1, 1, 0), (1, 1, 1, 1)), 6),
    ("FORK4", ((0, 0, 0, 0), (-1, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 1), (0, 0, 1, 1)), 7),
)

# Optional dedicated 4D set (6 cells per piece).
_PIECES_4D_SIX: Tuple[Tuple[str, Tuple[Tuple[int, int, int, int], ...], int], ...] = (
    ("CROSS6", ((0, 0, 0, 0), (-1, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)), 1),
    ("RIBBON6_A", ((0, 0, 0, 0), (1, 0, 0, 0), (1, 1, 0, 0), (1, 1, 1, 0), (1, 1, 1, 1), (0, 1, 1, 1)), 2),
    ("RIBBON6_B", ((0, 0, 0, 0), (-1, 0, 0, 0), (-1, 1, 0, 0), (-1, 1, 1, 0), (-1, 1, 1, 1), (0, 1, 1, 1)), 3),
    ("STAIR6", ((0, 0, 0, 0), (0, 1, 0, 0), (1, 1, 0, 0), (1, 1, 1, 0), (1, 1, 1, 1), (2, 1, 1, 1)), 4),
    ("FORK6", ((0, 0, 0, 0), (-1, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 1), (0, 1, 1, 1)), 5),
    ("TWIST6", ((0, 0, 0, 0), (0, 1, 0, 0), (1, 1, 0, 0), (1, 1, 1, 0), (2, 1, 1, 0), (2, 1, 1, 1)), 6),
    ("PLANE6", ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (1, 1, 0, 0), (1, 1, 1, 0), (1, 1, 1, 1)), 7),
)


def normalize_piece_set_4d(piece_set_4d: str | None) -> str:
    if piece_set_4d is None:
        return PIECE_SET_4D_STANDARD
    if piece_set_4d in PIECE_SET_4D_OPTIONS:
        return piece_set_4d
    raise ValueError(f"unsupported 4D piece set: {piece_set_4d}")


@dataclass(frozen=True)
class PieceShapeND:
    name: str
    blocks: Tuple[RelCoordND, ...]
    color_id: int


def get_standard_pieces_nd(ndim: int, piece_set_4d: str | None = None) -> List[PieceShapeND]:
    """
    Return dimension-native piece sets:
    - 2D: classic tetrominoes
    - 3D: true 3D polycubes
    - 4D: true 4D polycubes (5-cell default, optional 6-cell set)
    - >4D: embed the selected 4D set and keep extra axes at 0
    """
    _validate_ndim(ndim)
    normalized_set_4d = normalize_piece_set_4d(piece_set_4d)
    if ndim == 2:
        shapes_2d = get_standard_tetrominoes()
        return [
            PieceShapeND(
                name=shape.name,
                blocks=lift_2d_blocks_to_nd(shape.blocks, ndim),
                color_id=shape.color_id,
            )
            for shape in shapes_2d
        ]

    if ndim == 3:
        return [
            PieceShapeND(name=name, blocks=_embed_blocks_to_nd(blocks, ndim), color_id=color_id)
            for name, blocks, color_id in _PIECES_3D
        ]

    # ndim >= 4
    source_set = _PIECES_4D if normalized_set_4d == PIECE_SET_4D_STANDARD else _PIECES_4D_SIX
    return [
        PieceShapeND(name=name, blocks=_embed_blocks_to_nd(blocks, ndim), color_id=color_id)
        for name, blocks, color_id in source_set
    ]


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
