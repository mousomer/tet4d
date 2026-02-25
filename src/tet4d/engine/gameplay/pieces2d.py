# tetris_nd/pieces2d.py
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Tuple

# Simple 2D relative coordinate
RelCoord2D = Tuple[int, int]

PIECE_SET_2D_CLASSIC = "classic"
PIECE_SET_2D_RANDOM = "random_cells_2d"
PIECE_SET_2D_DEBUG = "debug_rectangles_2d"
PIECE_SET_2D_OPTIONS = (
    PIECE_SET_2D_CLASSIC,
    PIECE_SET_2D_RANDOM,
    PIECE_SET_2D_DEBUG,
)
DEFAULT_RANDOM_CELL_COUNT_2D = 4
DEFAULT_RANDOM_BAG_SIZE_2D = 7


@dataclass(frozen=True)
class PieceShape2D:
    name: str
    blocks: List[RelCoord2D]  # relative to pivot at (0,0)
    color_id: int  # just an int; front-end will map to colors


def get_standard_tetrominoes() -> List[PieceShape2D]:
    """
    Classic 7 tetrominoes. Coordinates are relative to pivot at (0,0).
    We'll allow some negative relative coords; the game logic allows
    pieces to exist partly above the top of the board.
    """
    return [
        PieceShape2D("I", [(-1, 0), (0, 0), (1, 0), (2, 0)], 1),
        PieceShape2D("O", [(0, 0), (1, 0), (0, 1), (1, 1)], 2),
        PieceShape2D("T", [(-1, 0), (0, 0), (1, 0), (0, 1)], 3),
        PieceShape2D("S", [(0, 0), (1, 0), (-1, 1), (0, 1)], 4),
        PieceShape2D("Z", [(-1, 0), (0, 0), (0, 1), (1, 1)], 5),
        PieceShape2D("J", [(-1, 0), (-1, 1), (0, 0), (1, 0)], 6),
        PieceShape2D("L", [(-1, 0), (0, 0), (1, 0), (1, 1)], 7),
    ]


def normalize_piece_set_2d(piece_set: str | None) -> str:
    if piece_set is None:
        return PIECE_SET_2D_CLASSIC
    if piece_set in PIECE_SET_2D_OPTIONS:
        return piece_set
    raise ValueError(f"unsupported 2D piece set: {piece_set}")


def piece_set_2d_label(piece_set: str) -> str:
    if piece_set == PIECE_SET_2D_RANDOM:
        return "Random Cells"
    if piece_set == PIECE_SET_2D_DEBUG:
        return "Debug Rectangles"
    return "Classic Tetrominoes"


def _normalize_offsets(blocks: Iterable[RelCoord2D]) -> Tuple[RelCoord2D, ...]:
    points = list(blocks)
    if not points:
        raise ValueError("piece must contain at least one block")
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2
    normalized = sorted((x - center_x, y - center_y) for x, y in points)
    return tuple(normalized)


def _neighbors_2d(
    cell: RelCoord2D,
) -> tuple[RelCoord2D, RelCoord2D, RelCoord2D, RelCoord2D]:
    x, y = cell
    return (
        (x - 1, y),
        (x + 1, y),
        (x, y - 1),
        (x, y + 1),
    )


def _random_connected_blocks_2d(
    cell_count: int, rng: random.Random
) -> Tuple[RelCoord2D, ...]:
    if cell_count < 1:
        raise ValueError("cell_count must be >= 1")
    cells = {(0, 0)}
    attempts = 0
    max_attempts = cell_count * 80
    while len(cells) < cell_count and attempts < max_attempts:
        base = rng.choice(tuple(cells))
        candidate = rng.choice(_neighbors_2d(base))
        attempts += 1
        if candidate in cells:
            continue
        cells.add(candidate)
    if len(cells) < cell_count:
        # Guaranteed progress fallback.
        x = 1
        while len(cells) < cell_count:
            cells.add((x, 0))
            x += 1
    return _normalize_offsets(cells)


def get_random_pieces_2d(
    rng: random.Random,
    cell_count: int = DEFAULT_RANDOM_CELL_COUNT_2D,
    bag_size: int = DEFAULT_RANDOM_BAG_SIZE_2D,
) -> List[PieceShape2D]:
    bag_size = max(1, bag_size)
    cell_count = max(1, cell_count)

    seen: set[Tuple[RelCoord2D, ...]] = set()
    pieces: List[PieceShape2D] = []
    attempts = 0
    max_attempts = bag_size * 120
    while len(pieces) < bag_size and attempts < max_attempts:
        blocks = _random_connected_blocks_2d(cell_count, rng)
        attempts += 1
        if blocks in seen:
            continue
        seen.add(blocks)
        shape_name = f"R2_{len(pieces) + 1}"
        color_id = (len(pieces) % 7) + 1
        pieces.append(PieceShape2D(shape_name, list(blocks), color_id))

    while len(pieces) < bag_size:
        blocks = _random_connected_blocks_2d(cell_count, rng)
        shape_name = f"R2_{len(pieces) + 1}"
        color_id = (len(pieces) % 7) + 1
        pieces.append(PieceShape2D(shape_name, list(blocks), color_id))
    return pieces


def _rect_blocks_2d(width: int, height: int) -> list[RelCoord2D]:
    cells = [(x, y) for y in range(height) for x in range(width)]
    normalized = _normalize_offsets(cells)
    return list(normalized)


def _scaled_span(
    axis_size: int, ratio: float, min_size: int, max_cap: int | None = None
) -> int:
    clamped_axis = max(1, int(axis_size))
    scaled = max(min_size, int(round(clamped_axis * ratio)))
    scaled = min(scaled, clamped_axis)
    if max_cap is not None:
        scaled = min(scaled, max_cap)
    return max(1, scaled)


def get_debug_rectangles_2d(
    board_dims: tuple[int, int] | None = None,
) -> List[PieceShape2D]:
    width, height = board_dims if board_dims is not None else (10, 20)
    width = max(1, int(width))
    height = max(1, int(height))

    long_1d = width
    half_w = max(2, width // 2)
    long_2d_w = half_w
    long_2d_h = _scaled_span(height, 0.08, min_size=2, max_cap=2)
    flat_w = width
    flat_h = _scaled_span(height, 0.12, min_size=2, max_cap=3)
    thick_w = half_w
    thick_h = _scaled_span(height, 0.2, min_size=3, max_cap=5)

    return [
        PieceShape2D("DBG_LONG_1D", _rect_blocks_2d(long_1d, 1), 1),
        PieceShape2D("DBG_LONG_2D", _rect_blocks_2d(long_2d_w, long_2d_h), 2),
        PieceShape2D("DBG_SURFACE_FLAT", _rect_blocks_2d(flat_w, flat_h), 3),
        PieceShape2D("DBG_SURFACE_THICK", _rect_blocks_2d(thick_w, thick_h), 4),
    ]


def get_piece_bag_2d(
    piece_set: str | None = None,
    *,
    rng: random.Random | None = None,
    random_cell_count: int = DEFAULT_RANDOM_CELL_COUNT_2D,
    bag_size: int = DEFAULT_RANDOM_BAG_SIZE_2D,
    board_dims: tuple[int, int] | None = None,
) -> List[PieceShape2D]:
    selected = normalize_piece_set_2d(piece_set)
    if selected == PIECE_SET_2D_CLASSIC:
        return get_standard_tetrominoes()
    if selected == PIECE_SET_2D_DEBUG:
        return get_debug_rectangles_2d(board_dims=board_dims)
    active_rng = rng if rng is not None else random.Random()
    return get_random_pieces_2d(
        active_rng,
        cell_count=random_cell_count,
        bag_size=bag_size,
    )


def rotate_point_2d(x: int, y: int, steps_cw: int) -> RelCoord2D:
    """
    Rotate (x, y) around origin by 90° * steps_cw clockwise.
    steps_cw can be any integer; we mod 4.
    """
    steps = steps_cw % 4
    if steps == 0:
        return x, y
    elif steps == 1:  # 90° CW: (x, y) -> (y, -x)
        return y, -x
    elif steps == 2:  # 180°
        return -x, -y
    else:  # 270° CW == 90° CCW
        return -y, x


@dataclass
class ActivePiece2D:
    """
    A falling tetromino in 2D. Position is the pivot's location on the board.
    """

    shape: PieceShape2D
    pos: Tuple[int, int]  # (x, y) of pivot on board
    rotation: int = 0  # 0,1,2,3 -> 0°,90°,180°,270° CW

    def cells(self) -> List[Tuple[int, int]]:
        """
        List of absolute board cells currently occupied by this piece.
        """
        px, py = self.pos
        result: List[Tuple[int, int]] = []
        for bx, by in self.shape.blocks:
            rx, ry = rotate_point_2d(bx, by, self.rotation)
            result.append((px + rx, py + ry))
        return result

    def moved(self, dx: int, dy: int) -> "ActivePiece2D":
        return ActivePiece2D(
            self.shape, (self.pos[0] + dx, self.pos[1] + dy), self.rotation
        )

    def rotated(self, delta_steps: int) -> "ActivePiece2D":
        return ActivePiece2D(self.shape, self.pos, (self.rotation + delta_steps) % 4)
