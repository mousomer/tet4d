from __future__ import annotations

from typing import Any

from ..runtime.runtime_config import (
    assist_bot_factor,
    assist_combined_bounds,
    assist_grid_factor,
    assist_kick_factor,
    assist_speed_formula,
    kick_default_level,
)
from ..runtime.score_analyzer import hud_analysis_lines
from .leveling import compute_speed_level
from .pieces2d import PIECE_SET_2D_OPTIONS, piece_set_2d_label
from .pieces_nd import piece_set_label, piece_set_options_for_dimension
from .speed_curve import gravity_interval_ms
from .topology import TOPOLOGY_MODE_OPTIONS, map_overlay_cells, topology_mode_from_index, topology_mode_label
from .topology_designer import (
    designer_profile_label_for_index,
    designer_profiles_for_dimension,
    export_resolved_topology_profile,
    resolve_topology_designer_selection,
)


def gravity_interval_ms_gameplay(speed_level: int, *, dimension: int) -> int:
    return gravity_interval_ms(speed_level, dimension=dimension)


def map_overlay_cells_gameplay(*args: Any, **kwargs: Any) -> Any:
    return map_overlay_cells(*args, **kwargs)


def topology_mode_from_index_runtime(index: int) -> str:
    return str(topology_mode_from_index(index))


def topology_mode_label_runtime(mode: str | None) -> str:
    return str(topology_mode_label(mode))


def topology_mode_options_runtime() -> tuple[str, ...]:
    return tuple(str(option) for option in TOPOLOGY_MODE_OPTIONS)


def topology_designer_profiles_runtime(dimension: int):
    return designer_profiles_for_dimension(dimension)


def topology_designer_profile_label_runtime(dimension: int, index: int) -> str:
    return str(designer_profile_label_for_index(dimension, index))


def topology_designer_resolve_runtime(
    *,
    dimension: int,
    gravity_axis: int,
    topology_mode: str,
    topology_advanced: bool,
    profile_index: int,
):
    return resolve_topology_designer_selection(
        dimension=dimension,
        gravity_axis=gravity_axis,
        topology_mode=topology_mode,
        topology_advanced=topology_advanced,
        profile_index=profile_index,
    )


def topology_designer_export_runtime(
    *,
    dimension: int,
    gravity_axis: int,
    topology_mode: str,
    topology_advanced: bool,
    profile_index: int,
):
    return export_resolved_topology_profile(
        dimension=dimension,
        gravity_axis=gravity_axis,
        topology_mode=topology_mode,
        topology_advanced=topology_advanced,
        profile_index=profile_index,
    )


def piece_set_2d_options_gameplay() -> tuple[str, ...]:
    return tuple(PIECE_SET_2D_OPTIONS)


def piece_set_2d_label_gameplay(piece_set_id: str) -> str:
    return piece_set_2d_label(piece_set_id)


def piece_set_label_gameplay(piece_set_id: str) -> str:
    return piece_set_label(piece_set_id)


def piece_set_options_for_dimension_gameplay(dimension: int):
    return tuple(piece_set_options_for_dimension(dimension))


def compute_speed_level_runtime(*args: Any, **kwargs: Any) -> int:
    return int(compute_speed_level(*args, **kwargs))


def hud_analysis_lines_runtime(event: dict[str, object] | None) -> tuple[str, ...]:
    return hud_analysis_lines(event)


def runtime_assist_combined_score_multiplier(*args: Any, **kwargs: Any) -> Any:
    bot_mode = kwargs.get("bot_mode") if kwargs else args[0]
    grid_mode = kwargs.get("grid_mode") if kwargs else args[1]
    speed_level = kwargs.get("speed_level") if kwargs else args[2]
    kick_level = kwargs.get("kick_level") if kwargs else (args[3] if len(args) > 3 else None)
    bot_name = getattr(bot_mode, "value", bot_mode)
    grid_name = getattr(grid_mode, "value", grid_mode)
    kick_name = kick_default_level() if kick_level is None else getattr(kick_level, "value", kick_level)
    base, per_level, min_level, max_level = assist_speed_formula()
    level = max(min_level, min(max_level, int(speed_level)))
    speed_factor = min(1.0, base + (per_level * level))
    combined = (
        assist_bot_factor(str(bot_name))
        * assist_grid_factor(str(grid_name))
        * assist_kick_factor(str(kick_name))
        * speed_factor
    )
    min_factor, max_factor = assist_combined_bounds()
    return max(min_factor, min(max_factor, combined))


def runtime_collect_cleared_ghost_cells(*args: Any, **kwargs: Any) -> Any:
    state = kwargs.get("state", args[0] if len(args) > 0 else None)
    expected_coord_len = kwargs.get("expected_coord_len", args[1] if len(args) > 1 else 0)
    color_for_cell = kwargs.get("color_for_cell", args[2] if len(args) > 2 else None)
    if state is None or getattr(state, "board", None) is None or color_for_cell is None:
        return ()
    ghost_cells: list[tuple[tuple[int, ...], tuple[int, int, int]]] = []
    for coord, cell_id in state.board.last_cleared_cells:
        if len(coord) != int(expected_coord_len):
            continue
        ghost_cells.append((tuple(coord), color_for_cell(cell_id)))
    return tuple(ghost_cells)


__all__ = [name for name in globals() if name.endswith("_runtime") or name.endswith("_gameplay")]
