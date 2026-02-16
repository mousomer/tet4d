# tetris_nd/game_nd.py
from dataclasses import dataclass, field
import random
from typing import List, Optional, Sequence

from .board import BoardND
from .pieces_nd import (
    ActivePieceND,
    PIECE_SET_3D_STANDARD,
    PIECE_SET_4D_STANDARD,
    PieceShapeND,
    get_piece_shapes_nd,
    normalize_piece_set_for_dimension,
    normalize_piece_set_4d,  # backward-compatible parameter support
)
from .types import Coord


def _score_for_clear(cleared_planes: int) -> int:
    if cleared_planes <= 0:
        return 0
    table = {
        1: 40,
        2: 100,
        3: 300,
        4: 1200,
    }
    if cleared_planes in table:
        return table[cleared_planes]
    return table[4] + (cleared_planes - 4) * 400


@dataclass
class GameConfigND:
    dims: Coord = (10, 20, 6)
    gravity_axis: int = 1
    speed_level: int = 1  # 1..10, used by frontend timing
    piece_set_id: str | None = None
    piece_set_4d: str = PIECE_SET_4D_STANDARD
    random_cell_count: int = 5

    def __post_init__(self) -> None:
        if len(self.dims) < 2:
            raise ValueError("dims must have at least 2 axes")
        if any(d <= 0 for d in self.dims):
            raise ValueError("all dimensions must be > 0")
        if not (0 <= self.gravity_axis < len(self.dims)):
            raise ValueError("invalid gravity_axis")
        if not (1 <= self.speed_level <= 10):
            raise ValueError("speed_level must be in [1, 10]")
        if not (3 <= self.random_cell_count <= 8):
            raise ValueError("random_cell_count must be in [3, 8]")

        ndim = len(self.dims)
        selected_piece_set = self.piece_set_id
        if selected_piece_set is None and ndim >= 4:
            selected_piece_set = normalize_piece_set_4d(self.piece_set_4d)
        if selected_piece_set is None and ndim == 3:
            selected_piece_set = PIECE_SET_3D_STANDARD
        self.piece_set_id = normalize_piece_set_for_dimension(ndim, selected_piece_set)
        # Keep legacy field populated for existing callers/UI labels.
        self.piece_set_4d = self.piece_set_id

    @property
    def ndim(self) -> int:
        return len(self.dims)


@dataclass
class GameStateND:
    config: GameConfigND
    board: BoardND
    current_piece: Optional[ActivePieceND] = None
    next_bag: List[PieceShapeND] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)
    score: int = 0
    lines_cleared: int = 0
    game_over: bool = False

    def __post_init__(self) -> None:
        if self.board is None:
            self.board = BoardND(self.config.dims)
        if self.board.dims != self.config.dims:
            raise ValueError("board dims must match config dims")
        if not self.next_bag:
            self._refill_bag()
        if self.current_piece is None:
            self.spawn_new_piece()

    # --- Bag and spawning ---

    def _refill_bag(self) -> None:
        attempts = 0
        while True:
            generated = get_piece_shapes_nd(
                self.config.ndim,
                piece_set_id=self.config.piece_set_id,
                random_cell_count=self.config.random_cell_count,
                rng=self.rng,
                board_dims=self.config.dims,
            )
            self.next_bag = [shape for shape in generated if self._shape_fits_board(shape)]
            if self.next_bag:
                break
            attempts += 1
            if attempts >= 4:
                # Stable fallback for tiny boards.
                fallback_id = PIECE_SET_3D_STANDARD if self.config.ndim == 3 else PIECE_SET_4D_STANDARD
                fallback = get_piece_shapes_nd(
                    self.config.ndim,
                    piece_set_id=fallback_id,
                    rng=self.rng,
                    board_dims=self.config.dims,
                )
                self.next_bag = [shape for shape in fallback if self._shape_fits_board(shape)]
                if self.next_bag:
                    break
                raise RuntimeError("no spawnable pieces for current board dimensions")
        self.rng.shuffle(self.next_bag)

    def draw_next_piece_shape(self) -> PieceShapeND:
        if not self.next_bag:
            self._refill_bag()
        return self.next_bag.pop()

    def _spawn_pos_for_shape(self, shape: PieceShapeND) -> Coord:
        g = self.config.gravity_axis
        coords = [0] * self.config.ndim
        for axis in range(self.config.ndim):
            axis_values = [block[axis] for block in shape.blocks]
            min_axis = min(axis_values)
            max_axis = max(axis_values)
            if axis == g:
                coords[axis] = -2 - min_axis
            else:
                span = max_axis - min_axis + 1
                start = (self.config.dims[axis] - span) // 2
                coords[axis] = start - min_axis
        return tuple(coords)

    def spawn_new_piece(self) -> None:
        shape = self.draw_next_piece_shape()
        self.current_piece = ActivePieceND.from_shape(shape, self._spawn_pos_for_shape(shape))
        if not self._can_exist(self.current_piece):
            self.game_over = True

    def _shape_fits_board(self, shape: PieceShapeND) -> bool:
        for axis in range(self.config.ndim):
            axis_values = [block[axis] for block in shape.blocks]
            span = max(axis_values) - min(axis_values) + 1
            if span > self.config.dims[axis]:
                return False
        return True

    # --- Validation and locking ---

    def _can_exist(self, piece: ActivePieceND) -> bool:
        g = self.config.gravity_axis
        dims = self.config.dims

        for coord in piece.cells():
            # Non-gravity axes must remain fully inside bounds.
            for axis, value in enumerate(coord):
                if axis == g:
                    if value >= dims[axis]:
                        return False
                else:
                    if value < 0 or value >= dims[axis]:
                        return False

            # Above the top along gravity axis is allowed.
            if coord[g] < 0:
                continue

            if coord in self.board.cells:
                return False
        return True

    def lock_current_piece(self) -> int:
        if self.current_piece is None:
            return 0

        g = self.config.gravity_axis
        piece = self.current_piece

        # If any block is still above the board along gravity axis, game over.
        for coord in piece.cells():
            if coord[g] < 0:
                self.game_over = True

        for coord in piece.cells():
            if self.board.inside_bounds(coord):
                self.board.cells[coord] = piece.shape.color_id

        cleared = self.board.clear_planes(g)
        self.lines_cleared += cleared
        self.score += _score_for_clear(cleared)
        return cleared

    # --- Movement and rotation ---

    def try_move(self, delta: Sequence[int]) -> bool:
        if self.current_piece is None:
            return False
        candidate = self.current_piece.moved(delta)
        if self._can_exist(candidate):
            self.current_piece = candidate
            return True
        return False

    def try_move_axis(self, axis: int, delta: int) -> bool:
        if not (0 <= axis < self.config.ndim):
            raise ValueError("axis out of bounds")
        vector = [0] * self.config.ndim
        vector[axis] = delta
        return self.try_move(vector)

    def try_rotate(self, axis_a: int, axis_b: int, delta_steps: int = 1) -> bool:
        if self.current_piece is None:
            return False
        rotated = self.current_piece.rotated(axis_a, axis_b, delta_steps)
        if self._can_exist(rotated):
            self.current_piece = rotated
            return True
        return False

    def hard_drop(self) -> None:
        if self.current_piece is None:
            return

        g = self.config.gravity_axis
        while self.try_move_axis(g, 1):
            pass

        self.lock_current_piece()
        if not self.game_over:
            self.spawn_new_piece()

    # --- Time step ---

    def step_gravity(self) -> None:
        if self.game_over or self.current_piece is None:
            return

        g = self.config.gravity_axis
        if not self.try_move_axis(g, 1):
            self.lock_current_piece()
            if not self.game_over:
                self.spawn_new_piece()

    def step(self) -> None:
        self.step_gravity()
