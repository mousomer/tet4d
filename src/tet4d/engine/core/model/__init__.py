from .game2d_types import Action
from .game2d_views import GameConfig2DCoreView, GameState2DCoreView
from .game_nd_views import GameConfigNDCoreView, GameStateNDCoreView
from .board import BoardND
from typing import Tuple

Coord = Tuple[int, ...]

__all__ = [
    "Action",
    "BoardND",
    "Coord",
    "GameConfig2DCoreView",
    "GameState2DCoreView",
    "GameConfigNDCoreView",
    "GameStateNDCoreView",
]
