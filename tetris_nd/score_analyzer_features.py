from __future__ import annotations

import math
from itertools import product
from statistics import pstdev
from typing import Any


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _plane_size(dims: tuple[int, ...], gravity_axis: int) -> int:
    size = 1
    for axis, axis_size in enumerate(dims):
        if axis == gravity_axis:
            continue
        size *= max(1, axis_size)
    return max(1, size)


def _lateral_axes(dims: tuple[int, ...], gravity_axis: int) -> tuple[int, ...]:
    return tuple(axis for axis in range(len(dims)) if axis != gravity_axis)


def _iter_columns(dims: tuple[int, ...], gravity_axis: int):
    axes = _lateral_axes(dims, gravity_axis)
    ranges = [range(max(1, dims[axis])) for axis in axes]
    if not ranges:
        yield tuple()
        return
    for values in product(*ranges):
        yield tuple(values)


def _coord_from_column(
    column: tuple[int, ...],
    *,
    lateral_axes: tuple[int, ...],
    gravity_axis: int,
    gravity_value: int,
    ndim: int,
) -> tuple[int, ...]:
    coord = [0] * ndim
    coord[gravity_axis] = gravity_value
    for idx, axis in enumerate(lateral_axes):
        coord[axis] = column[idx]
    return tuple(coord)


def _neighbor_coords(coord: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    neighbors: list[tuple[int, ...]] = []
    for axis in range(len(coord)):
        for delta in (-1, 1):
            updated = list(coord)
            updated[axis] += delta
            neighbors.append(tuple(updated))
    return tuple(neighbors)


def _connected_components(cells: set[tuple[int, ...]]) -> int:
    if not cells:
        return 0
    remaining = set(cells)
    components = 0
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            curr = stack.pop()
            for nxt in _neighbor_coords(curr):
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
    return components


def _top_columns_and_plane_counts(
    cells: set[tuple[int, ...]],
    *,
    lateral_axes: tuple[int, ...],
    gravity_axis: int,
    gravity_size: int,
) -> tuple[dict[tuple[int, ...], int], list[int]]:
    top_per_column: dict[tuple[int, ...], int] = {}
    plane_counts = [0] * gravity_size
    for coord in cells:
        g_val = coord[gravity_axis]
        if 0 <= g_val < gravity_size:
            plane_counts[g_val] += 1
        column = tuple(coord[axis] for axis in lateral_axes)
        prev = top_per_column.get(column)
        if prev is None or g_val < prev:
            top_per_column[column] = g_val
    return top_per_column, plane_counts


def _height_hole_features(
    cells: set[tuple[int, ...]],
    *,
    dims: tuple[int, ...],
    gravity_axis: int,
    gravity_size: int,
    lateral_axes: tuple[int, ...],
    top_per_column: dict[tuple[int, ...], int],
) -> tuple[dict[tuple[int, ...], int], int, float]:
    heights: dict[tuple[int, ...], int] = {}
    holes_count = 0
    holes_depth_weighted = 0.0
    for column in _iter_columns(dims, gravity_axis):
        top = top_per_column.get(column)
        if top is None:
            heights[column] = 0
            continue
        height = gravity_size - top
        heights[column] = height
        seen_block = False
        for g_val in range(top, gravity_size):
            coord = _coord_from_column(
                column,
                lateral_axes=lateral_axes,
                gravity_axis=gravity_axis,
                gravity_value=g_val,
                ndim=len(dims),
            )
            if coord in cells:
                seen_block = True
                continue
            if seen_block:
                holes_count += 1
                holes_depth_weighted += float(g_val - top + 1)
    return heights, holes_count, holes_depth_weighted


def _surface_roughness_norm(
    heights: dict[tuple[int, ...], int],
    *,
    dims: tuple[int, ...],
    lateral_axes: tuple[int, ...],
    gravity_size: int,
) -> float:
    roughness = 0.0
    roughness_edges = 0
    for column, value in heights.items():
        column_list = list(column)
        for axis_idx, axis in enumerate(lateral_axes):
            if column[axis_idx] + 1 >= dims[axis]:
                continue
            column_list[axis_idx] += 1
            neighbor = tuple(column_list)
            column_list[axis_idx] -= 1
            roughness += abs(value - heights.get(neighbor, 0))
            roughness_edges += 1
    if roughness_edges == 0:
        return 0.0
    return _clamp01(roughness / (roughness_edges * gravity_size))


def _completion_ratios(
    plane_counts: list[int],
    *,
    gravity_size: int,
    plane_size: int,
    near_threshold: float,
) -> tuple[float, float]:
    near_complete_planes = 0
    clearable_planes = 0
    for count in plane_counts:
        ratio = count / plane_size
        if ratio >= 1.0:
            clearable_planes += 1
        elif ratio >= near_threshold:
            near_complete_planes += 1
    near_complete_planes_norm = near_complete_planes / gravity_size
    clearable_planes_norm = clearable_planes / gravity_size
    return _clamp01(near_complete_planes_norm), _clamp01(clearable_planes_norm)


def _top_zone_risk_norm(
    cells: set[tuple[int, ...]],
    *,
    gravity_axis: int,
    gravity_size: int,
    plane_size: int,
    top_layers: int,
) -> float:
    safe_top_layers = max(1, min(gravity_size, top_layers))
    top_count = sum(1 for coord in cells if coord[gravity_axis] < safe_top_layers)
    return _clamp01(top_count / max(1, safe_top_layers * plane_size))


def _slice_balance_norm(cells: set[tuple[int, ...]], dims: tuple[int, ...]) -> float:
    if len(dims) < 4 or dims[3] <= 1:
        return 1.0
    per_w = [0] * dims[3]
    for coord in cells:
        per_w[coord[3]] += 1
    mean_w = sum(per_w) / len(per_w)
    if mean_w <= 0:
        return 1.0
    coeff_var = pstdev(per_w) / mean_w
    return _clamp01(1.0 - coeff_var)


def board_health_features(
    cells_map: dict[tuple[int, ...], int],
    *,
    dims: tuple[int, ...],
    gravity_axis: int,
    near_threshold: float = 0.8,
    top_layers: int = 3,
) -> dict[str, float]:
    total_cells = max(1, math.prod(max(1, axis) for axis in dims))
    gravity_size = max(1, dims[gravity_axis])
    plane_size = _plane_size(dims, gravity_axis)
    lateral_axes = _lateral_axes(dims, gravity_axis)

    cells = set(cells_map.keys())
    occupied_count = len(cells)
    occupied_ratio = occupied_count / total_cells

    top_per_column, plane_counts = _top_columns_and_plane_counts(
        cells,
        lateral_axes=lateral_axes,
        gravity_axis=gravity_axis,
        gravity_size=gravity_size,
    )
    heights, holes_count, holes_depth_weighted = _height_hole_features(
        cells,
        dims=dims,
        gravity_axis=gravity_axis,
        gravity_size=gravity_size,
        lateral_axes=lateral_axes,
        top_per_column=top_per_column,
    )

    max_height_norm = max(heights.values(), default=0) / gravity_size
    mean_height_norm = (sum(heights.values()) / max(1, len(heights))) / gravity_size

    surface_roughness_norm = _surface_roughness_norm(
        heights,
        dims=dims,
        lateral_axes=lateral_axes,
        gravity_size=gravity_size,
    )

    holes_count_norm = holes_count / total_cells
    holes_depth_norm = _clamp01(holes_depth_weighted / (total_cells * gravity_size))
    cavity_volume_norm = holes_count_norm

    near_complete_planes_norm, clearable_planes_norm = _completion_ratios(
        plane_counts,
        gravity_size=gravity_size,
        plane_size=plane_size,
        near_threshold=near_threshold,
    )

    top_zone_risk_norm = _top_zone_risk_norm(
        cells,
        gravity_axis=gravity_axis,
        gravity_size=gravity_size,
        plane_size=plane_size,
        top_layers=top_layers,
    )

    components = _connected_components(cells)
    fragmentation_norm = components / max(1, occupied_count)
    slice_balance_norm = _slice_balance_norm(cells, dims)

    return {
        "occupied_ratio": _clamp01(occupied_ratio),
        "max_height_norm": _clamp01(max_height_norm),
        "mean_height_norm": _clamp01(mean_height_norm),
        "surface_roughness_norm": surface_roughness_norm,
        "holes_count_norm": _clamp01(holes_count_norm),
        "holes_depth_norm": holes_depth_norm,
        "cavity_volume_norm": _clamp01(cavity_volume_norm),
        "near_complete_planes_norm": _clamp01(near_complete_planes_norm),
        "clearable_planes_norm": _clamp01(clearable_planes_norm),
        "top_zone_risk_norm": _clamp01(top_zone_risk_norm),
        "fragmentation_norm": _clamp01(fragmentation_norm),
        "slice_balance_norm": _clamp01(slice_balance_norm),
    }


def placement_features(
    *,
    board_pre: dict[tuple[int, ...], int],
    board_post: dict[tuple[int, ...], int],
    board_pre_features: dict[str, float],
    board_post_features: dict[str, float],
    dims: tuple[int, ...],
    gravity_axis: int,
    locked_cells: tuple[tuple[int, ...], ...],
    cleared: int,
) -> dict[str, float]:
    gravity_size = max(1, dims[gravity_axis])
    post_cells = set(board_post.keys())
    locked = [coord for coord in locked_cells if 0 <= coord[gravity_axis] < gravity_size]

    if not locked:
        return {
            "drop_distance_norm": 0.0,
            "landing_coords_norm": 0.0,
            "support_contacts_norm": 0.0,
            "side_contacts_norm": 0.0,
            "overhang_cells_norm": 0.0,
            "immediate_clears_norm": 0.0,
            "clear_contribution_norm": 0.0,
            "near_complete_progress_norm": 0.0,
            "holes_created_norm": 0.0,
            "holes_filled_norm": 0.0,
            "cavity_delta_norm": 0.0,
            "roughness_delta_norm": 0.0,
            "top_risk_delta_norm": 0.0,
        }

    locked_count = len(locked)
    drop_distance_norm = sum(coord[gravity_axis] for coord in locked) / (locked_count * max(1, gravity_size - 1))

    lateral_axes = _lateral_axes(dims, gravity_axis)
    if lateral_axes:
        landing_values: list[float] = []
        for axis in lateral_axes:
            denom = max(1, dims[axis] - 1)
            landing_values.append(sum(coord[axis] for coord in locked) / (locked_count * denom))
        landing_coords_norm = _clamp01(sum(landing_values) / len(landing_values))
    else:
        landing_coords_norm = 0.0

    support_contacts = 0
    overhang_cells = 0
    side_contacts = 0
    max_side_contacts = max(1, locked_count * len(lateral_axes) * 2)
    for coord in locked:
        below = list(coord)
        below[gravity_axis] += 1
        below_coord = tuple(below)
        if coord[gravity_axis] == gravity_size - 1 or below_coord in post_cells:
            support_contacts += 1
        else:
            overhang_cells += 1

        for axis in lateral_axes:
            for delta in (-1, 1):
                side = list(coord)
                side[axis] += delta
                side_coord = tuple(side)
                if side_coord in post_cells:
                    side_contacts += 1

    support_contacts_norm = support_contacts / locked_count
    side_contacts_norm = _clamp01(side_contacts / max_side_contacts)
    overhang_cells_norm = overhang_cells / locked_count

    immediate_clears_norm = _clamp01(cleared / max(1, min(4, gravity_size)))
    clear_contribution_norm = 1.0 if cleared > 0 else 0.0

    pre_holes = board_pre_features["holes_count_norm"]
    post_holes = board_post_features["holes_count_norm"]
    pre_cavity = board_pre_features["cavity_volume_norm"]
    post_cavity = board_post_features["cavity_volume_norm"]
    pre_rough = board_pre_features["surface_roughness_norm"]
    post_rough = board_post_features["surface_roughness_norm"]
    pre_top = board_pre_features["top_zone_risk_norm"]
    post_top = board_post_features["top_zone_risk_norm"]
    pre_near = board_pre_features["near_complete_planes_norm"]
    post_near = board_post_features["near_complete_planes_norm"]

    near_complete_progress_norm = _clamp01(max(0.0, post_near - pre_near))
    holes_created_norm = _clamp01(max(0.0, post_holes - pre_holes))
    holes_filled_norm = _clamp01(max(0.0, pre_holes - post_holes))
    cavity_delta_norm = _clamp01(max(0.0, post_cavity - pre_cavity))
    roughness_delta_norm = _clamp01(max(0.0, pre_rough - post_rough))
    top_risk_delta_norm = _clamp01(max(0.0, pre_top - post_top))

    return {
        "drop_distance_norm": _clamp01(drop_distance_norm),
        "landing_coords_norm": landing_coords_norm,
        "support_contacts_norm": _clamp01(support_contacts_norm),
        "side_contacts_norm": side_contacts_norm,
        "overhang_cells_norm": _clamp01(overhang_cells_norm),
        "immediate_clears_norm": immediate_clears_norm,
        "clear_contribution_norm": clear_contribution_norm,
        "near_complete_progress_norm": near_complete_progress_norm,
        "holes_created_norm": holes_created_norm,
        "holes_filled_norm": holes_filled_norm,
        "cavity_delta_norm": cavity_delta_norm,
        "roughness_delta_norm": roughness_delta_norm,
        "top_risk_delta_norm": top_risk_delta_norm,
    }


def weighted_score(features: dict[str, float], score_obj: dict[str, Any]) -> float:
    weights = score_obj.get("weights", {})
    if not isinstance(weights, dict):
        weights = {}
    bias = float(score_obj.get("bias", 0.5))
    value = bias
    for key, feature_value in features.items():
        weight = float(weights.get(key, 0.0))
        value += weight * float(feature_value)
    return round(_clamp01(value), 6)
