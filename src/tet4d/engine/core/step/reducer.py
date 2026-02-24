from __future__ import annotations

from typing import Any


def step_2d(state: Any, action: Any) -> Any:
    state.step(action)
    return state


def step_nd(state: Any) -> Any:
    state.step()
    return state


__all__ = ["step_2d", "step_nd"]
