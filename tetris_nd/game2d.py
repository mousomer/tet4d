# tetris_nd/game2d.py
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional
import random

from .board import BoardND
from .pieces2d import PieceShape2D, ActivePiece2D, get_standard_tetrominoes


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
    speed_level: int = 5    # 1..10, used by frontend to pick gravity speed


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
        self.next_bag = get_standard_tetrominoes()
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
        spawn_x = self.config.width // 2
        spawn_y = -2  # above the visible area
        self.current_piece = ActivePiece2D(shape, (spawn_x, spawn_y), rotation=0)
        if not self._can_exist(self.current_piece):
            self.game_over = True

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

        # Simple scoring (tweak as you wish)
        if cleared == 1:
            self.score += 40
        elif cleared == 2:
            self.score += 100
        elif cleared == 3:
            self.score += 300
        elif cleared == 4:
            self.score += 1200

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

    # --- Main step function ---

    def step(self, action: Action = Action.NONE):
        """
        Advance the game by one tick with the given player action.
        Action is applied first, then we apply gravity (one row down).
        """
        if self.game_over:
            return

        # Handle user action
        if action == Action.MOVE_LEFT:
            self.try_move(-1, 0)
        elif action == Action.MOVE_RIGHT:
            self.try_move(1, 0)
        elif action == Action.SOFT_DROP:
            self.try_move(0, 1)
        elif action == Action.ROTATE_CW:
            self.try_rotate(+1)
        elif action == Action.ROTATE_CCW:
            self.try_rotate(-1)
        elif action == Action.HARD_DROP:
            self.hard_drop()
            return  # hard drop already locked & possibly spawned a new piece

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
