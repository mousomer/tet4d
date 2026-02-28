from __future__ import annotations

from dataclasses import dataclass

Coord = tuple[int, ...]


@dataclass(frozen=True)
class GameConfigNDCoreView:
    dims: Coord
    gravity_axis: int
    speed_level: int
    topology_mode: str
    wrap_gravity_axis: bool
    piece_set_id: str | None
    random_cell_count: int
    challenge_layers: int
    lock_piece_points: int
    exploration_mode: bool


@dataclass(frozen=True)
class GameStateNDCoreView:
    config: GameConfigNDCoreView
    score: int
    lines_cleared: int
    game_over: bool
    board_cells: tuple[tuple[Coord, int], ...]
    current_piece_cells: tuple[Coord, ...]
    has_current_piece: bool


__all__ = ["GameConfigNDCoreView", "GameStateNDCoreView"]
