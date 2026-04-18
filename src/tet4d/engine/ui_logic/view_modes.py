from __future__ import annotations

from enum import Enum

from ..runtime.runtime_config import grid_mode_cycle_names, grid_mode_fallback_name


class GridMode(str, Enum):
    OFF = "off"
    SHADOW = "off"  # Legacy alias
    BOTTOM_BOUNDARY = "bottom_boundary"
    EDGE = "edge"
    FULL = "full"
    HELPER = "helper"
    ALL_BOUNDARIES = "all_boundaries"


def _grid_mode_from_name(mode_name: str) -> GridMode:
    normalized = mode_name.strip().lower()
    if normalized == GridMode.BOTTOM_BOUNDARY.value:
        return GridMode.BOTTOM_BOUNDARY
    if normalized == GridMode.EDGE.value:
        return GridMode.EDGE
    if normalized == GridMode.FULL.value:
        return GridMode.FULL
    if normalized == GridMode.HELPER.value:
        return GridMode.HELPER
    if normalized == GridMode.ALL_BOUNDARIES.value:
        return GridMode.ALL_BOUNDARIES
    return GridMode.OFF


_GRID_MODE_CYCLE: tuple[GridMode, ...] = tuple(
    _grid_mode_from_name(mode_name) for mode_name in grid_mode_cycle_names()
)
_GRID_MODE_FALLBACK = _grid_mode_from_name(grid_mode_fallback_name())


def cycle_grid_mode(mode: GridMode) -> GridMode:
    try:
        idx = _GRID_MODE_CYCLE.index(mode)
    except ValueError:
        return _GRID_MODE_FALLBACK
    return _GRID_MODE_CYCLE[(idx + 1) % len(_GRID_MODE_CYCLE)]


def grid_mode_label(mode: GridMode) -> str:
    if mode in (GridMode.OFF, GridMode.SHADOW):
        return "OFF"
    if mode == GridMode.BOTTOM_BOUNDARY:
        return "BOTTOM BOUNDARY"
    if mode == GridMode.ALL_BOUNDARIES:
        return "ALL BOUNDARIES"
    return mode.value.upper()
