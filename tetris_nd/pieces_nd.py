# tetris_nd/pieces_nd.py
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from .pieces2d import get_standard_tetrominoes
from .types import Coord


RelCoordND = Coord


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


@dataclass(frozen=True)
class PieceShapeND:
    name: str
    blocks: Tuple[RelCoordND, ...]
    color_id: int


def get_standard_pieces_nd(ndim: int) -> List[PieceShapeND]:
    """
    Reuse the classic tetromino set as scaffolding, then lift it into ND.
    In 3D/4D these pieces can still rotate in higher-dimensional planes.
    """
    _validate_ndim(ndim)
    shapes_2d = get_standard_tetrominoes()
    return [
        PieceShapeND(
            name=shape.name,
            blocks=lift_2d_blocks_to_nd(shape.blocks, ndim),
            color_id=shape.color_id,
        )
        for shape in shapes_2d
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
