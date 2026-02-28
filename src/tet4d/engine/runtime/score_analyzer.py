from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from .project_config import (
    PROJECT_ROOT,
    sanitize_state_relative_path,
    score_events_file_default_relative,
    score_summary_file_default_relative,
    state_dir_relative,
)
from .score_analyzer_features import (
    board_health_features,
    placement_features,
    weighted_score,
)

_ROOT_DIR = PROJECT_ROOT
_CONFIG_PATH = _ROOT_DIR / "config" / "gameplay" / "score_analyzer.json"
_DEFAULT_EVENTS_PATH = score_events_file_default_relative()
_DEFAULT_SUMMARY_PATH = score_summary_file_default_relative()
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


def _load_json_object_or_default(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
        loaded = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return default
    if not isinstance(loaded, dict):
        return default
    return loaded


def _atomic_write_summary_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)


def _append_json_line(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


@lru_cache(maxsize=1)
def _score_analyzer_config() -> dict[str, Any]:
    config = _default_config()
    loaded = _load_json_object_or_default(_CONFIG_PATH, config)
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


def _state_root() -> Path:
    return (_ROOT_DIR / state_dir_relative()).resolve()


def _sanitize_state_relative_path(raw_path: object, default_relative: str) -> str:
    return sanitize_state_relative_path(raw_path, default_relative=default_relative)


def _resolve_output_path(raw_path: object, default_relative: str) -> Path:
    relative = _sanitize_state_relative_path(raw_path, default_relative)
    resolved = (_ROOT_DIR / relative).resolve()
    state_root = _state_root()
    if resolved != state_root and state_root not in resolved.parents:
        return (_ROOT_DIR / default_relative).resolve()
    return resolved


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
        "events_file": _sanitize_state_relative_path(
            logging_obj.get("events_file"),
            _DEFAULT_EVENTS_PATH,
        ),
        "summary_file": _sanitize_state_relative_path(
            logging_obj.get("summary_file"),
            _DEFAULT_SUMMARY_PATH,
        ),
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
    board_obj = cfg.get("board", {})
    near_threshold = (
        float(board_obj.get("near_complete_threshold", 0.8))
        if isinstance(board_obj, dict)
        else 0.8
    )
    top_layers = (
        int(board_obj.get("top_zone_layers", 3)) if isinstance(board_obj, dict) else 3
    )

    board_pre_features = board_health_features(
        board_pre,
        dims=dims,
        gravity_axis=gravity_axis,
        near_threshold=near_threshold,
        top_layers=top_layers,
    )
    board_post_features = board_health_features(
        board_post,
        dims=dims,
        gravity_axis=gravity_axis,
        near_threshold=near_threshold,
        top_layers=top_layers,
    )
    placement = placement_features(
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
    board_health_score = weighted_score(
        board_post_features,
        dict(scores_obj.get("board_health", {}))
        if isinstance(scores_obj, dict)
        else {},
    )
    placement_quality_score = weighted_score(
        placement,
        dict(scores_obj.get("placement_quality", {}))
        if isinstance(scores_obj, dict)
        else {},
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


def _require_fields(
    payload: dict[str, object], fields: tuple[str, ...], *, label: str
) -> tuple[bool, str]:
    for key in fields:
        if key not in payload:
            return False, f"missing {label} field: {key}"
    return True, ""


def _require_non_empty_string_fields(
    payload: dict[str, object],
    fields: tuple[str, ...],
    *,
    label: str,
) -> tuple[bool, str]:
    for field in fields:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            return False, f"{label}.{field} must be a non-empty string"
    return True, ""


def _require_integer_fields(
    payload: dict[str, object],
    fields: tuple[str, ...],
    *,
    label: str,
) -> tuple[bool, str]:
    for field in fields:
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            return False, f"{label}.{field} must be an integer"
    return True, ""


def _require_object_fields(
    payload: dict[str, object],
    fields: tuple[str, ...],
    *,
    label: str,
) -> tuple[bool, str]:
    for field in fields:
        value = payload.get(field)
        if not isinstance(value, dict):
            return False, f"{label}.{field} must be an object"
    return True, ""


def _require_numeric_fields(
    payload: dict[str, object],
    fields: tuple[str, ...],
    *,
    label: str,
    min_value: float | None = None,
    max_value: float | None = None,
) -> tuple[bool, str]:
    for field in fields:
        value = payload.get(field)
        if not _is_number(value):
            return False, f"{label}.{field} must be numeric"
        number = float(value)
        if min_value is not None and number < min_value:
            return False, f"{label}.{field} must be >= {min_value}"
        if max_value is not None and number > max_value:
            return False, f"{label}.{field} must be <= {max_value}"
    return True, ""


def validate_score_analysis_event(event: dict[str, object]) -> tuple[bool, str]:
    if not isinstance(event, dict):
        return False, "event must be an object"
    ok, msg = _require_fields(event, _EVENT_REQUIRED_FIELDS, label="event")
    if not ok:
        return ok, msg
    ok, msg = _require_non_empty_string_fields(
        event, ("session_id", "piece_id"), label="event"
    )
    if not ok:
        return ok, msg
    ok, msg = _require_integer_fields(
        event,
        ("seq", "dimension", "speed_level", "cleared", "raw_points", "final_points"),
        label="event",
    )
    if not ok:
        return ok, msg
    board_dims = event.get("board_dims")
    if not isinstance(board_dims, list) or not board_dims:
        return False, "event.board_dims must be a non-empty list"
    ok, msg = _require_object_fields(
        event, ("board_pre", "placement", "board_post", "delta"), label="event"
    )
    if not ok:
        return ok, msg
    ok, msg = _require_numeric_fields(
        event,
        ("board_health_score", "placement_quality_score"),
        label="event",
        min_value=0.0,
        max_value=1.0,
    )
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
    loaded = _load_json_object_or_default(path, _new_summary())
    ok, _msg = validate_score_analysis_summary(loaded)
    if not ok:
        return _new_summary()
    return loaded


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    _atomic_write_summary_json(path, payload)


def _increment_counter(target: dict[str, object], key: str, amount: int = 1) -> None:
    current = target.get(key, 0)
    count = (
        int(current)
        if isinstance(current, int) and not isinstance(current, bool)
        else 0
    )
    target[key] = count + amount


def _update_summary(
    summary: dict[str, object], event: dict[str, object]
) -> dict[str, object]:
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
    totals["cleared_total"] = int(totals.get("cleared_total", 0)) + int(
        event["cleared"]
    )
    totals["raw_points_total"] = int(totals.get("raw_points_total", 0)) + int(
        event["raw_points"]
    )
    totals["final_points_total"] = int(totals.get("final_points_total", 0)) + int(
        event["final_points"]
    )

    prev_health = float(score_means.get("board_health", 0.0))
    prev_quality = float(score_means.get("placement_quality", 0.0))
    health = float(event["board_health_score"])
    quality = float(event["placement_quality_score"])
    score_means["board_health"] = round(
        prev_health + ((health - prev_health) / events), 6
    )
    score_means["placement_quality"] = round(
        prev_quality + ((quality - prev_quality) / events), 6
    )

    for summary_key, event_key in (
        ("dimensions", "dimension"),
        ("actor_modes", "actor_mode"),
        ("bot_modes", "bot_mode"),
        ("grid_modes", "grid_mode"),
    ):
        bucket = summary[summary_key]
        _increment_counter(bucket, str(event[event_key]))

    sessions = summary["sessions"]
    session_id = str(event["session_id"])
    session_obj = sessions.get(session_id)
    if not isinstance(session_obj, dict):
        session_obj = {"events": 0, "last_seq": 0, "last_timestamp_utc": ""}
        sessions[session_id] = session_obj
    session_obj["events"] = int(session_obj.get("events", 0)) + 1
    session_obj["last_seq"] = int(event["seq"])
    session_obj["last_timestamp_utc"] = str(event["timestamp_utc"])

    summary["schema_version"] = int(
        event.get("schema_version", summary.get("schema_version", 1))
    )
    summary["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    return summary


def validate_score_analysis_summary(summary: dict[str, object]) -> tuple[bool, str]:
    if not isinstance(summary, dict):
        return False, "summary must be an object"
    ok, msg = _require_fields(summary, _SUMMARY_REQUIRED_FIELDS, label="summary")
    if not ok:
        return ok, msg
    totals = summary.get("totals")
    if not isinstance(totals, dict):
        return False, "summary.totals must be an object"
    ok, msg = _require_integer_fields(
        totals,
        ("events", "cleared_total", "raw_points_total", "final_points_total"),
        label="summary.totals",
    )
    if not ok:
        return ok, msg
    score_means = summary.get("score_means")
    if not isinstance(score_means, dict):
        return False, "summary.score_means must be an object"
    ok, msg = _require_numeric_fields(
        score_means,
        ("board_health", "placement_quality"),
        label="summary.score_means",
    )
    if not ok:
        return ok, msg
    ok, msg = _require_object_fields(
        summary,
        ("dimensions", "actor_modes", "bot_modes", "grid_modes", "sessions"),
        label="summary",
    )
    if not ok:
        return ok, msg
    return True, ""


def score_analysis_summary_snapshot() -> dict[str, object]:
    logging_cfg = _logging_config()
    raw_summary = str(logging_cfg.get("summary_file", _DEFAULT_SUMMARY_PATH))
    summary_path = _resolve_output_path(raw_summary, _DEFAULT_SUMMARY_PATH)
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
    events_path = _resolve_output_path(raw_events, _DEFAULT_EVENTS_PATH)
    summary_path = _resolve_output_path(raw_summary, _DEFAULT_SUMMARY_PATH)
    summary_cache_key = str(summary_path)

    try:
        _append_json_line(events_path, event)
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
    if not isinstance(raw_quality, (int, float)) or not isinstance(
        raw_health, (int, float)
    ):
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
