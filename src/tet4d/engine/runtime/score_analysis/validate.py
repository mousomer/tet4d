from __future__ import annotations

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
