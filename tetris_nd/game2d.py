# tetris_nd/game2d.py
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional
import random

from .board import BoardND
from .pieces2d import (
    ActivePiece2D,
    PieceShape2D,
    PIECE_SET_2D_CLASSIC,
    get_piece_bag_2d,
    normalize_piece_set_2d,
)


def _score_for_clear(cleared_lines: int) -> int:
    if cleared_lines <= 0:
        return 0
    table = {
        1: 40,
        2: 100,
        3: 300,
        4: 1200,
    }
    if cleared_lines in table:
        return table[cleared_lines]
    return table[4] + (cleared_lines - 4) * 400


class Action(Enum):
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    SOFT_DROP = auto()
    HARD_DROP = auto()
    ROTATE_CW = auto()
    ROTATE_CCW = auto()
    NONE = auto()          # no user input, just gravity tick


@dataclass
class GameConfig:
    width: int = 10
    height: int = 20
    gravity_axis: int = 1   # for 2D, dims=(width, height), so y-axis
    speed_level: int = 1    # 1..10, used by frontend to pick gravity speed
    piece_set: str = PIECE_SET_2D_CLASSIC
    random_cell_count: int = 4

    def __post_init__(self):
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be > 0")
        # 2D mode is defined as gravity along y (axis 1), clearing full x-rows.
        if self.gravity_axis != 1:
            raise ValueError("2D mode requires gravity_axis=1 (y-axis)")
        if not (1 <= self.speed_level <= 10):
            raise ValueError("speed_level must be in [1, 10]")
        self.piece_set = normalize_piece_set_2d(self.piece_set)
        if not (3 <= self.random_cell_count <= 8):
            raise ValueError("random_cell_count must be in [3, 8]")


@dataclass
class GameState:
    config: GameConfig
    board: BoardND
    current_piece: Optional[ActivePiece2D] = None
    next_bag: List[PieceShape2D] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)
    score: int = 0
    lines_cleared: int = 0
    game_over: bool = False

    def __post_init__(self):
        if self.board is None:
            self.board = BoardND((self.config.width, self.config.height))
        if not self.next_bag:
            self._refill_bag()
        if self.current_piece is None:
            self.spawn_new_piece()

    # --- Piece bag handling ---

    def _refill_bag(self):
        """Refill the 7-bag for random piece selection."""
        generated = get_piece_bag_2d(
            self.config.piece_set,
            rng=self.rng,
            random_cell_count=self.config.random_cell_count,
            board_dims=(self.config.width, self.config.height),
        )
        self.next_bag = [shape for shape in generated if self._shape_fits_spawn(shape)]
        if not self.next_bag:
            # Fallback to a stable baseline bag if selected set cannot spawn on this board.
            self.next_bag = [
                shape
                for shape in get_piece_bag_2d(
                    PIECE_SET_2D_CLASSIC,
                    rng=self.rng,
                    board_dims=(self.config.width, self.config.height),
                )
                if self._shape_fits_spawn(shape)
            ]
        self.rng.shuffle(self.next_bag)

    def draw_next_piece_shape(self) -> PieceShape2D:
        if not self.next_bag:
            self._refill_bag()
        return self.next_bag.pop()

    # --- Piece spawning & validation ---

    def spawn_new_piece(self):
        """
        Spawn a new piece at the top center.
        We allow negative y so pieces can start above the visible board.
        """
        shape = self.draw_next_piece_shape()
        min_x = min(block[0] for block in shape.blocks)
        max_x = max(block[0] for block in shape.blocks)
        span_x = max_x - min_x + 1
        spawn_x = ((self.config.width - span_x) // 2) - min_x
        spawn_y = -2  # above the visible area
        self.current_piece = ActivePiece2D(shape, (spawn_x, spawn_y), rotation=0)
        if not self._can_exist(self.current_piece):
            self.game_over = True

    def _shape_fits_spawn(self, shape: PieceShape2D) -> bool:
        if not shape.blocks:
            return False
        min_x = min(block[0] for block in shape.blocks)
        max_x = max(block[0] for block in shape.blocks)
        span_x = max_x - min_x + 1
        min_y = min(block[1] for block in shape.blocks)
        max_y = max(block[1] for block in shape.blocks)
        span_y = max_y - min_y + 1
        return span_x <= self.config.width and span_y <= self.config.height

    def _can_exist(self, piece: ActivePiece2D) -> bool:
        """
        Check if a piece configuration is valid (inside horizontal bounds,
        not below the bottom, no collision with locked cells).
        y < 0 is allowed (piece entering from above).
        """
        width, height = self.config.width, self.config.height
        for (x, y) in piece.cells():
            # Left/right bounds
            if x < 0 or x >= width:
                return False
            # Bottom bound
            if y >= height:
                return False
            # Above top is allowed
            if y < 0:
                continue
            # Collision with locked cells
            if (x, y) in self.board.cells:
                return False
        return True

    def lock_current_piece(self) -> int:
        """
        Lock current piece into the board and clear any full lines.
        Returns number of cleared lines.
        """
        if self.current_piece is None:
            return 0

        piece = self.current_piece
        width, height = self.config.width, self.config.height

        # If any block is above the top row, the game is over.
        for (x, y) in piece.cells():
            if y < 0:
                self.game_over = True

        # Lock only visible cells (inside the board)
        for (x, y) in piece.cells():
            if 0 <= x < width and 0 <= y < height:
                self.board.cells[(x, y)] = piece.shape.color_id

        cleared = self.board.clear_planes(self.config.gravity_axis)
        self.lines_cleared += cleared
        self.score += _score_for_clear(cleared)

        return cleared

    # --- Movement / rotation helpers ---

    def try_move(self, dx: int, dy: int):
        if self.current_piece is None:
            return
        moved = self.current_piece.moved(dx, dy)
        if self._can_exist(moved):
            self.current_piece = moved

    def try_rotate(self, delta_steps: int):
        if self.current_piece is None:
            return
        rotated = self.current_piece.rotated(delta_steps)
        if self._can_exist(rotated):
            self.current_piece = rotated

    def hard_drop(self):
        if self.current_piece is None:
            return
        # Move down until just before collision
        while True:
            moved = self.current_piece.moved(0, 1)
            if self._can_exist(moved):
                self.current_piece = moved
            else:
                break
        # Lock piece and spawn new one
        self.lock_current_piece()
        if not self.game_over:
            self.spawn_new_piece()

    def _apply_action(self, action: Action) -> bool:
        if action == Action.HARD_DROP:
            self.hard_drop()
            return True

        action_handlers = {
            Action.MOVE_LEFT: lambda: self.try_move(-1, 0),
            Action.MOVE_RIGHT: lambda: self.try_move(1, 0),
            Action.SOFT_DROP: lambda: self.try_move(0, 1),
            Action.ROTATE_CW: lambda: self.try_rotate(+1),
            Action.ROTATE_CCW: lambda: self.try_rotate(-1),
        }
        handler = action_handlers.get(action)
        if handler is not None:
            handler()
        return False

    # --- Main step function ---

    def step(self, action: Action = Action.NONE):
        """
        Advance the game by one tick with the given player action.
        Action is applied first, then we apply gravity (one row down).
        """
        if self.game_over:
            return

        # Hard drop locks immediately and already handles spawning.
        if self._apply_action(action):
            return

        # Gravity tick
        if self.current_piece is None:
            return

        moved_down = self.current_piece.moved(0, 1)
        if self._can_exist(moved_down):
            self.current_piece = moved_down
        else:
            # Lock and spawn new piece
            self.lock_current_piece()
            if not self.game_over:
                self.spawn_new_piece()
