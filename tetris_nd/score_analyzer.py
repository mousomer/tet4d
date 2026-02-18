from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from itertools import product
from pathlib import Path
from statistics import pstdev
from typing import Any


_ROOT_DIR = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _ROOT_DIR / "config" / "gameplay" / "score_analyzer.json"
_DEFAULT_EVENTS_PATH = "state/analytics/score_events.jsonl"
_DEFAULT_SUMMARY_PATH = "state/analytics/score_summary.json"
_LOGGING_ENABLED_OVERRIDE: bool | None = None
_SUMMARY_CACHE: dict[str, dict[str, object]] = {}


def new_analysis_session_id() -> str:
    return uuid.uuid4().hex[:16]


def _default_config() -> dict[str, Any]:
    return {
        "version": 1,
        "enabled": True,
        "board": {
            "near_complete_threshold": 0.8,
            "top_zone_layers": 3,
        },
        "logging": {
            "enabled": False,
            "events_file": "state/analytics/score_events.jsonl",
            "summary_file": "state/analytics/score_summary.json",
        },
        "scores": {
            "board_health": {
                "bias": 0.62,
                "weights": {},
            },
            "placement_quality": {
                "bias": 0.56,
                "weights": {},
            },
        },
    }


@lru_cache(maxsize=1)
def _score_analyzer_config() -> dict[str, Any]:
    config = _default_config()
    try:
        raw = _CONFIG_PATH.read_text(encoding="utf-8")
        loaded = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return config
    if not isinstance(loaded, dict):
        return config
    merged = dict(config)
    for key, value in loaded.items():
        merged[key] = value
    return merged


def reload_score_analyzer_config() -> None:
    _score_analyzer_config.cache_clear()


def reset_score_analyzer_runtime_state() -> None:
    global _LOGGING_ENABLED_OVERRIDE
    _LOGGING_ENABLED_OVERRIDE = None
    _SUMMARY_CACHE.clear()
    reload_score_analyzer_config()


def _resolve_output_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (_ROOT_DIR / path).resolve()


def _logging_config() -> dict[str, object]:
    cfg = _score_analyzer_config()
    logging_obj = cfg.get("logging", {})
    if not isinstance(logging_obj, dict):
        return {
            "enabled": False,
            "events_file": _DEFAULT_EVENTS_PATH,
            "summary_file": _DEFAULT_SUMMARY_PATH,
        }
    return {
        "enabled": bool(logging_obj.get("enabled", False)),
        "events_file": str(logging_obj.get("events_file", _DEFAULT_EVENTS_PATH)),
        "summary_file": str(logging_obj.get("summary_file", _DEFAULT_SUMMARY_PATH)),
    }


def set_score_analyzer_logging_enabled(enabled: bool | None) -> None:
    global _LOGGING_ENABLED_OVERRIDE
    if enabled is None:
        _LOGGING_ENABLED_OVERRIDE = None
        return
    _LOGGING_ENABLED_OVERRIDE = bool(enabled)


def score_analyzer_logging_enabled() -> bool:
    logging_cfg = _logging_config()
    configured = bool(logging_cfg.get("enabled", False))
    if _LOGGING_ENABLED_OVERRIDE is None:
        return configured
    return bool(_LOGGING_ENABLED_OVERRIDE)


def score_analyzer_settings_snapshot() -> dict[str, object]:
    logging_cfg = _logging_config()
    return {
        "enabled": bool(_score_analyzer_config().get("enabled", True)),
        "logging_enabled": score_analyzer_logging_enabled(),
        "configured_logging_enabled": bool(logging_cfg.get("enabled", False)),
        "events_file": str(logging_cfg.get("events_file", _DEFAULT_EVENTS_PATH)),
        "summary_file": str(logging_cfg.get("summary_file", _DEFAULT_SUMMARY_PATH)),
    }


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


def _board_health_features(
    cells_map: dict[tuple[int, ...], int],
    *,
    dims: tuple[int, ...],
    gravity_axis: int,
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

    config = _score_analyzer_config()
    near_threshold = float(config.get("board", {}).get("near_complete_threshold", 0.8))
    near_complete_planes_norm, clearable_planes_norm = _completion_ratios(
        plane_counts,
        gravity_size=gravity_size,
        plane_size=plane_size,
        near_threshold=near_threshold,
    )

    top_layers = int(config.get("board", {}).get("top_zone_layers", 3))
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


def _placement_features(
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


def _weighted_score(features: dict[str, float], score_obj: dict[str, Any]) -> float:
    weights = score_obj.get("weights", {})
    if not isinstance(weights, dict):
        weights = {}
    bias = float(score_obj.get("bias", 0.5))
    value = bias
    for key, feature_value in features.items():
        weight = float(weights.get(key, 0.0))
        value += weight * float(feature_value)
    return round(_clamp01(value), 6)


def analyze_lock_event(
    *,
    board_pre: dict[tuple[int, ...], int],
    board_post: dict[tuple[int, ...], int],
    dims: tuple[int, ...],
    gravity_axis: int,
    locked_cells: tuple[tuple[int, ...], ...],
    cleared: int,
    piece_id: str,
    actor_mode: str,
    bot_mode: str,
    grid_mode: str,
    speed_level: int,
    raw_points: int,
    final_points: int,
    session_id: str,
    seq: int,
) -> dict[str, object]:
    cfg = _score_analyzer_config()
    board_pre_features = _board_health_features(board_pre, dims=dims, gravity_axis=gravity_axis)
    board_post_features = _board_health_features(board_post, dims=dims, gravity_axis=gravity_axis)
    placement = _placement_features(
        board_pre=board_pre,
        board_post=board_post,
        board_pre_features=board_pre_features,
        board_post_features=board_post_features,
        dims=dims,
        gravity_axis=gravity_axis,
        locked_cells=locked_cells,
        cleared=cleared,
    )
    delta = {
        key: round(float(board_post_features[key]) - float(board_pre_features[key]), 6)
        for key in board_post_features
    }

    scores_obj = cfg.get("scores", {})
    board_health_score = _weighted_score(
        board_post_features,
        dict(scores_obj.get("board_health", {})) if isinstance(scores_obj, dict) else {},
    )
    placement_quality_score = _weighted_score(
        placement,
        dict(scores_obj.get("placement_quality", {})) if isinstance(scores_obj, dict) else {},
    )

    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": int(cfg.get("version", 1)),
        "session_id": session_id,
        "seq": int(seq),
        "timestamp_utc": timestamp,
        "dimension": len(dims),
        "board_dims": [int(v) for v in dims],
        "piece_id": piece_id,
        "actor_mode": actor_mode,
        "bot_mode": bot_mode,
        "grid_mode": grid_mode,
        "speed_level": int(speed_level),
        "cleared": int(cleared),
        "raw_points": int(raw_points),
        "final_points": int(final_points),
        "board_pre": board_pre_features,
        "placement": placement,
        "board_post": board_post_features,
        "delta": delta,
        "board_health_score": board_health_score,
        "placement_quality_score": placement_quality_score,
    }


_EVENT_REQUIRED_FIELDS = (
    "schema_version",
    "session_id",
    "seq",
    "timestamp_utc",
    "dimension",
    "board_dims",
    "piece_id",
    "actor_mode",
    "bot_mode",
    "grid_mode",
    "speed_level",
    "cleared",
    "raw_points",
    "final_points",
    "board_pre",
    "placement",
    "board_post",
    "delta",
    "board_health_score",
    "placement_quality_score",
)
_SUMMARY_REQUIRED_FIELDS = (
    "schema_version",
    "updated_at_utc",
    "totals",
    "score_means",
    "dimensions",
    "actor_modes",
    "bot_modes",
    "grid_modes",
    "sessions",
)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_event_required_fields(event: dict[str, object]) -> tuple[bool, str]:
    for key in _EVENT_REQUIRED_FIELDS:
        if key not in event:
            return False, f"missing event field: {key}"
    return True, ""


def _validate_event_identity(event: dict[str, object]) -> tuple[bool, str]:
    if not isinstance(event.get("session_id"), str) or not str(event["session_id"]).strip():
        return False, "event.session_id must be a non-empty string"
    if not isinstance(event.get("piece_id"), str) or not str(event["piece_id"]).strip():
        return False, "event.piece_id must be a non-empty string"
    return True, ""


def _validate_event_scalars(event: dict[str, object]) -> tuple[bool, str]:
    for scalar_key in ("seq", "dimension", "speed_level", "cleared", "raw_points", "final_points"):
        value = event.get(scalar_key)
        if isinstance(value, bool) or not isinstance(value, int):
            return False, f"event.{scalar_key} must be an integer"
    return True, ""


def _validate_event_structures(event: dict[str, object]) -> tuple[bool, str]:
    if not isinstance(event.get("board_dims"), list) or not event["board_dims"]:
        return False, "event.board_dims must be a non-empty list"
    for dict_key in ("board_pre", "placement", "board_post", "delta"):
        if not isinstance(event.get(dict_key), dict):
            return False, f"event.{dict_key} must be an object"
    return True, ""


def _validate_event_scores(event: dict[str, object]) -> tuple[bool, str]:
    for score_key in ("board_health_score", "placement_quality_score"):
        value = event.get(score_key)
        if not _is_number(value):
            return False, f"event.{score_key} must be numeric"
        if not 0.0 <= float(value) <= 1.0:
            return False, f"event.{score_key} must be in [0, 1]"
    return True, ""


def validate_score_analysis_event(event: dict[str, object]) -> tuple[bool, str]:
    if not isinstance(event, dict):
        return False, "event must be an object"
    checks = (
        _validate_event_required_fields,
        _validate_event_identity,
        _validate_event_scalars,
        _validate_event_structures,
        _validate_event_scores,
    )
    for check in checks:
        ok, msg = check(event)
        if not ok:
            return ok, msg
    return True, ""


def _new_summary() -> dict[str, object]:
    return {
        "schema_version": int(_score_analyzer_config().get("version", 1)),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "events": 0,
            "cleared_total": 0,
            "raw_points_total": 0,
            "final_points_total": 0,
        },
        "score_means": {
            "board_health": 0.0,
            "placement_quality": 0.0,
        },
        "dimensions": {},
        "actor_modes": {},
        "bot_modes": {},
        "grid_modes": {},
        "sessions": {},
    }


def _load_summary(path: Path) -> dict[str, object]:
    try:
        raw = path.read_text(encoding="utf-8")
        loaded = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return _new_summary()
    if not isinstance(loaded, dict):
        return _new_summary()
    ok, _msg = validate_score_analysis_summary(loaded)
    if not ok:
        return _new_summary()
    return loaded


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp_path.replace(path)


def _increment_counter(target: dict[str, object], key: str, amount: int = 1) -> None:
    current = target.get(key, 0)
    count = int(current) if isinstance(current, int) and not isinstance(current, bool) else 0
    target[key] = count + amount


def _update_summary(summary: dict[str, object], event: dict[str, object]) -> dict[str, object]:
    totals = summary.get("totals")
    if not isinstance(totals, dict):
        totals = {}
        summary["totals"] = totals
    score_means = summary.get("score_means")
    if not isinstance(score_means, dict):
        score_means = {}
        summary["score_means"] = score_means

    for key in ("dimensions", "actor_modes", "bot_modes", "grid_modes", "sessions"):
        if not isinstance(summary.get(key), dict):
            summary[key] = {}

    events = int(totals.get("events", 0)) + 1
    totals["events"] = events
    totals["cleared_total"] = int(totals.get("cleared_total", 0)) + int(event["cleared"])
    totals["raw_points_total"] = int(totals.get("raw_points_total", 0)) + int(event["raw_points"])
    totals["final_points_total"] = int(totals.get("final_points_total", 0)) + int(event["final_points"])

    prev_health = float(score_means.get("board_health", 0.0))
    prev_quality = float(score_means.get("placement_quality", 0.0))
    health = float(event["board_health_score"])
    quality = float(event["placement_quality_score"])
    score_means["board_health"] = round(prev_health + ((health - prev_health) / events), 6)
    score_means["placement_quality"] = round(prev_quality + ((quality - prev_quality) / events), 6)

    dimensions = summary["dimensions"]
    _increment_counter(dimensions, str(event["dimension"]))
    actor_modes = summary["actor_modes"]
    _increment_counter(actor_modes, str(event["actor_mode"]))
    bot_modes = summary["bot_modes"]
    _increment_counter(bot_modes, str(event["bot_mode"]))
    grid_modes = summary["grid_modes"]
    _increment_counter(grid_modes, str(event["grid_mode"]))

    sessions = summary["sessions"]
    session_id = str(event["session_id"])
    session_obj = sessions.get(session_id)
    if not isinstance(session_obj, dict):
        session_obj = {"events": 0, "last_seq": 0, "last_timestamp_utc": ""}
        sessions[session_id] = session_obj
    session_obj["events"] = int(session_obj.get("events", 0)) + 1
    session_obj["last_seq"] = int(event["seq"])
    session_obj["last_timestamp_utc"] = str(event["timestamp_utc"])

    summary["schema_version"] = int(event.get("schema_version", summary.get("schema_version", 1)))
    summary["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    return summary


def _validate_summary_required_fields(summary: dict[str, object]) -> tuple[bool, str]:
    for key in _SUMMARY_REQUIRED_FIELDS:
        if key not in summary:
            return False, f"missing summary field: {key}"
    return True, ""


def _validate_summary_totals(summary: dict[str, object]) -> tuple[bool, str]:
    totals = summary.get("totals")
    if not isinstance(totals, dict):
        return False, "summary.totals must be an object"
    for field in ("events", "cleared_total", "raw_points_total", "final_points_total"):
        value = totals.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            return False, f"summary.totals.{field} must be an integer"
    return True, ""


def _validate_summary_score_means(summary: dict[str, object]) -> tuple[bool, str]:
    score_means = summary.get("score_means")
    if not isinstance(score_means, dict):
        return False, "summary.score_means must be an object"
    for field in ("board_health", "placement_quality"):
        value = score_means.get(field)
        if not _is_number(value):
            return False, f"summary.score_means.{field} must be numeric"
    return True, ""


def _validate_summary_group_maps(summary: dict[str, object]) -> tuple[bool, str]:
    for key in ("dimensions", "actor_modes", "bot_modes", "grid_modes", "sessions"):
        if not isinstance(summary.get(key), dict):
            return False, f"summary.{key} must be an object"
    return True, ""


def validate_score_analysis_summary(summary: dict[str, object]) -> tuple[bool, str]:
    if not isinstance(summary, dict):
        return False, "summary must be an object"
    checks = (
        _validate_summary_required_fields,
        _validate_summary_totals,
        _validate_summary_score_means,
        _validate_summary_group_maps,
    )
    for check in checks:
        ok, msg = check(summary)
        if not ok:
            return ok, msg
    return True, ""


def score_analysis_summary_snapshot() -> dict[str, object]:
    logging_cfg = _logging_config()
    raw_summary = str(logging_cfg.get("summary_file", _DEFAULT_SUMMARY_PATH))
    summary_path = _resolve_output_path(raw_summary)
    cache_key = str(summary_path)
    summary = _SUMMARY_CACHE.get(cache_key)
    if summary is not None:
        return dict(summary)
    loaded = _load_summary(summary_path)
    _SUMMARY_CACHE[cache_key] = loaded
    return dict(loaded)


def record_score_analysis_event(event: dict[str, object]) -> None:
    valid, _msg = validate_score_analysis_event(event)
    if not valid:
        return
    if not score_analyzer_logging_enabled():
        return

    logging_cfg = _logging_config()
    raw_events = str(logging_cfg.get("events_file", _DEFAULT_EVENTS_PATH))
    raw_summary = str(logging_cfg.get("summary_file", _DEFAULT_SUMMARY_PATH))
    events_path = _resolve_output_path(raw_events)
    summary_path = _resolve_output_path(raw_summary)
    summary_cache_key = str(summary_path)

    try:
        events_path.parent.mkdir(parents=True, exist_ok=True)
        with events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
    except OSError:
        return

    try:
        summary = _SUMMARY_CACHE.get(summary_cache_key)
        if summary is None:
            summary = _load_summary(summary_path)
        updated = _update_summary(summary, event)
        _atomic_write_json(summary_path, updated)
        _SUMMARY_CACHE[summary_cache_key] = updated
    except OSError:
        return


def hud_analysis_lines(event: dict[str, object] | None) -> tuple[str, ...]:
    if not isinstance(event, dict):
        return ()
    raw_quality = event.get("placement_quality_score")
    raw_health = event.get("board_health_score")
    raw_delta = event.get("delta")
    if not isinstance(raw_quality, (int, float)) or not isinstance(raw_health, (int, float)):
        return ()

    quality = float(raw_quality)
    health = float(raw_health)
    trend = "flat"
    if isinstance(raw_delta, dict):
        holes_delta = float(raw_delta.get("holes_count_norm", 0.0))
        near_delta = float(raw_delta.get("near_complete_planes_norm", 0.0))
        top_delta = float(raw_delta.get("top_zone_risk_norm", 0.0))
        trend_score = (-holes_delta * 1.2) + (near_delta * 1.0) + (-top_delta * 0.8)
        if trend_score > 0.015:
            trend = "up"
        elif trend_score < -0.015:
            trend = "down"

    return (
        f"Quality: {quality:.2f}",
        f"Board health: {health:.2f}",
        f"Trend: {trend}",
    )
