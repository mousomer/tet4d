from .board import BoardND
from .game2d_types import Action
from .game2d_views import GameConfig2DCoreView, GameState2DCoreView
from .game_nd_views import GameConfigNDCoreView, GameStateNDCoreView

Coord = tuple[int, ...]

__all__ = [
    "Action",
    "BoardND",
    "Coord",
    "GameConfig2DCoreView",
    "GameConfigNDCoreView",
    "GameState2DCoreView",
    "GameStateNDCoreView",
]
