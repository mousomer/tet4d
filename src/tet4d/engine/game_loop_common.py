from __future__ import annotations

from importlib import import_module

_ui_game_loop_common = import_module("tet4d.ui.pygame.game_loop_common")

GameLoopDecision = _ui_game_loop_common.GameLoopDecision
GameKeyResult = _ui_game_loop_common.GameKeyResult
process_game_events = _ui_game_loop_common.process_game_events
