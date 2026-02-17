from __future__ import annotations

from enum import Enum


class GridMode(str, Enum):
    OFF = "off"
    SHADOW = "off"  # Legacy alias
    EDGE = "edge"
    FULL = "full"
    HELPER = "helper"


_GRID_MODE_CYCLE: tuple[GridMode, ...] = (
    GridMode.OFF,
    GridMode.EDGE,
    GridMode.FULL,
    GridMode.HELPER,
)


def cycle_grid_mode(mode: GridMode) -> GridMode:
    try:
        idx = _GRID_MODE_CYCLE.index(mode)
    except ValueError:
        return GridMode.FULL
    return _GRID_MODE_CYCLE[(idx + 1) % len(_GRID_MODE_CYCLE)]


def grid_mode_label(mode: GridMode) -> str:
    if mode in (GridMode.OFF, GridMode.SHADOW):
        return "OFF"
    return mode.value.upper()
