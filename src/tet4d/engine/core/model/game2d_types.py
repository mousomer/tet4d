from __future__ import annotations

from enum import Enum, auto
from typing import Protocol


class Action(Enum):
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    SOFT_DROP = auto()
    HARD_DROP = auto()
    ROTATE_CW = auto()
    ROTATE_CCW = auto()
    NONE = auto()  # no user input, just gravity tick


class GameConfig2DLike(Protocol):
    exploration_mode: bool


class ActivePiece2DLike(Protocol):
    def moved(self, dx: int, dy: int) -> "ActivePiece2DLike": ...


class GameState2DLike(Protocol):
    game_over: bool
    config: GameConfig2DLike
    current_piece: ActivePiece2DLike | None

    def hard_drop(self) -> None: ...
    def try_move(self, dx: int, dy: int) -> None: ...
    def try_rotate(self, delta_steps: int) -> None: ...
    def _can_exist(self, piece: ActivePiece2DLike) -> bool: ...
    def lock_current_piece(self) -> int: ...
    def spawn_new_piece(self) -> None: ...


__all__ = ["Action", "GameConfig2DLike", "GameState2DLike", "ActivePiece2DLike"]
