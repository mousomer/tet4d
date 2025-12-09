# tetris_nd/pieces2d.py
from dataclasses import dataclass
from typing import List, Tuple

# Simple 2D relative coordinate
RelCoord2D = Tuple[int, int]


@dataclass(frozen=True)
class PieceShape2D:
    name: str
    blocks: List[RelCoord2D]  # relative to pivot at (0,0)
    color_id: int             # just an int; front-end will map to colors


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


def rotate_point_2d(x: int, y: int, steps_cw: int) -> RelCoord2D:
    """
    Rotate (x, y) around origin by 90° * steps_cw clockwise.
    steps_cw can be any integer; we mod 4.
    """
    steps = steps_cw % 4
    if steps == 0:
        return x, y
    elif steps == 1:      # 90° CW: (x, y) -> (y, -x)
        return y, -x
    elif steps == 2:      # 180°
        return -x, -y
    else:                 # 270° CW == 90° CCW
        return -y, x


@dataclass
class ActivePiece2D:
    """
    A falling tetromino in 2D. Position is the pivot's location on the board.
    """
    shape: PieceShape2D
    pos: Tuple[int, int]      # (x, y) of pivot on board
    rotation: int = 0         # 0,1,2,3 -> 0°,90°,180°,270° CW

    def cells(self) -> List[Tuple[int, int]]:
        """
        List of absolute board cells currently occupied by this piece.
        """
        px, py = self.pos
        result: List[Tuple[int, int]] = []
        for (bx, by) in self.shape.blocks:
            rx, ry = rotate_point_2d(bx, by, self.rotation)
            result.append((px + rx, py + ry))
        return result

    def moved(self, dx: int, dy: int) -> "ActivePiece2D":
        return ActivePiece2D(self.shape, (self.pos[0] + dx, self.pos[1] + dy), self.rotation)

    def rotated(self, delta_steps: int) -> "ActivePiece2D":
        return ActivePiece2D(self.shape, self.pos, (self.rotation + delta_steps) % 4)
