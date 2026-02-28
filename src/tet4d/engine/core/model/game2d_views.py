from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GameConfig2DCoreView:
    width: int
    height: int
    gravity_axis: int
    speed_level: int
    topology_mode: str
    wrap_gravity_axis: bool
    piece_set: str
    random_cell_count: int
    challenge_layers: int
    lock_piece_points: int
    exploration_mode: bool


@dataclass(frozen=True)
class GameState2DCoreView:
    config: GameConfig2DCoreView
    score: int
    lines_cleared: int
    game_over: bool
    board_cells: tuple[tuple[tuple[int, int], int], ...]
    current_piece_cells: tuple[tuple[int, int], ...]
    has_current_piece: bool


__all__ = ["GameConfig2DCoreView", "GameState2DCoreView"]
