from __future__ import annotations

from collections.abc import Callable
from typing import Any


def lock_and_respawn(state: Any) -> int:
    cleared = int(state.lock_current_piece())
    if not state.game_over:
        state.spawn_new_piece()
    return cleared


def advance_or_lock_and_respawn(
    state: Any,
    *,
    try_advance: Callable[[], bool],
) -> Any:
    if not try_advance():
        lock_and_respawn(state)
    return state


def run_hard_drop(
    state: Any,
    *,
    try_advance: Callable[[], bool],
) -> None:
    if state.current_piece is None:
        return
    if state.config.exploration_mode:
        state.spawn_new_piece()
        return
    while try_advance():
        pass
    lock_and_respawn(state)


__all__ = ["advance_or_lock_and_respawn", "lock_and_respawn", "run_hard_drop"]
