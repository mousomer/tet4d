from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid

from .project_config import (
    leaderboard_file_default_path,
    project_constant_int,
)
from .settings_schema import atomic_write_json, read_json_object_or_empty, sanitize_text

_SCHEMA_VERSION = 1
_DEFAULT_MAX_ENTRIES = 200


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _max_entries_limit() -> int:
    return project_constant_int(
        ("analytics", "leaderboard_max_entries"),
        _DEFAULT_MAX_ENTRIES,
        min_value=1,
        max_value=10_000,
    )


def _leaderboard_path(path: Path | None) -> Path:
    if path is not None:
        return path
    return leaderboard_file_default_path()


def _default_payload() -> dict[str, Any]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "updated_at_utc": _now_utc_iso(),
        "entries": [],
    }


def _safe_int(
    value: object,
    *,
    default: int,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        number = int(default)
    else:
        number = int(value)
    if min_value is not None and number < min_value:
        number = min_value
    if max_value is not None and number > max_value:
        number = max_value
    return number


def _safe_float(
    value: object,
    *,
    default: float,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        number = float(default)
    else:
        number = float(value)
    if min_value is not None and number < min_value:
        number = min_value
    if max_value is not None and number > max_value:
        number = max_value
    return number


def _safe_text(value: object, *, max_length: int = 48, fallback: str = "") -> str:
    text = sanitize_text(value, max_length=max_length).strip()
    if text:
        return text
    return fallback


def _normalized_outcome(value: object) -> str:
    outcome = _safe_text(value, max_length=24, fallback="session_end").lower()
    if outcome in {"menu", "quit", "restart", "game_over", "session_end"}:
        return outcome
    return "session_end"


def _normalize_entry(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        raw = {}
    run_id = _safe_text(
        raw.get("run_id"),
        max_length=24,
        fallback=uuid.uuid4().hex[:12],
    )
    timestamp = _safe_text(
        raw.get("timestamp_utc"),
        max_length=48,
        fallback=_now_utc_iso(),
    )
    return {
        "run_id": run_id,
        "timestamp_utc": timestamp,
        "player_name": _safe_text(
            raw.get("player_name"),
            max_length=32,
            fallback="Player",
        ),
        "dimension": _safe_int(raw.get("dimension"), default=2, min_value=2, max_value=4),
        "score": _safe_int(raw.get("score"), default=0, min_value=0),
        "lines_cleared": _safe_int(raw.get("lines_cleared"), default=0, min_value=0),
        "start_speed_level": _safe_int(
            raw.get("start_speed_level"),
            default=1,
            min_value=1,
            max_value=10,
        ),
        "end_speed_level": _safe_int(
            raw.get("end_speed_level"),
            default=1,
            min_value=1,
            max_value=10,
        ),
        "duration_seconds": round(
            _safe_float(raw.get("duration_seconds"), default=0.0, min_value=0.0), 3
        ),
        "outcome": _normalized_outcome(raw.get("outcome")),
        "bot_mode": _safe_text(raw.get("bot_mode"), max_length=24, fallback="off"),
        "grid_mode": _safe_text(raw.get("grid_mode"), max_length=24, fallback="full"),
        "random_mode": _safe_text(
            raw.get("random_mode"),
            max_length=24,
            fallback="fixed_seed",
        ),
        "topology_mode": _safe_text(
            raw.get("topology_mode"),
            max_length=32,
            fallback="bounded",
        ),
        "exploration_mode": bool(raw.get("exploration_mode", False)),
    }


def _entry_sort_key(entry: dict[str, object]) -> tuple[object, ...]:
    return (
        -int(entry["score"]),
        -int(entry["lines_cleared"]),
        -int(entry["end_speed_level"]),
        float(entry["duration_seconds"]),
        str(entry["timestamp_utc"]),
        str(entry["run_id"]),
    )


def _sort_and_trim(
    entries: list[dict[str, object]],
    *,
    max_entries: int,
) -> list[dict[str, object]]:
    ordered = sorted(entries, key=_entry_sort_key)
    return ordered[:max_entries]


def _load_payload(path: Path) -> dict[str, Any]:
    raw = read_json_object_or_empty(path)
    entries_raw = raw.get("entries")
    if not isinstance(entries_raw, list):
        entries_raw = []
    entries = [_normalize_entry(item) for item in entries_raw]
    max_entries = _max_entries_limit()
    return {
        "schema_version": _safe_int(
            raw.get("schema_version"),
            default=_SCHEMA_VERSION,
            min_value=1,
        ),
        "updated_at_utc": _safe_text(
            raw.get("updated_at_utc"),
            max_length=48,
            fallback=_now_utc_iso(),
        ),
        "entries": _sort_and_trim(entries, max_entries=max_entries),
    }


def leaderboard_payload(*, path: Path | None = None) -> dict[str, Any]:
    target = _leaderboard_path(path)
    if not target.exists():
        return _default_payload()
    return _load_payload(target)


def leaderboard_top_entries(
    *,
    limit: int = 20,
    path: Path | None = None,
) -> tuple[dict[str, object], ...]:
    payload = leaderboard_payload(path=path)
    safe_limit = _safe_int(limit, default=20, min_value=1, max_value=200)
    entries = payload.get("entries")
    if not isinstance(entries, list):
        return ()
    return tuple(entries[:safe_limit])


def leaderboard_entry_rank(
    *,
    dimension: int,
    score: int,
    lines_cleared: int,
    start_speed_level: int,
    end_speed_level: int,
    duration_seconds: float,
    outcome: str,
    bot_mode: str,
    grid_mode: str,
    random_mode: str,
    topology_mode: str,
    exploration_mode: bool,
    path: Path | None = None,
) -> int:
    target = _leaderboard_path(path)
    payload = _load_payload(target) if target.exists() else _default_payload()
    entries_raw = payload.get("entries")
    if not isinstance(entries_raw, list):
        entries_raw = []
    entries = [_normalize_entry(item) for item in entries_raw]
    candidate = _normalize_entry(
        {
            "run_id": "__candidate__",
            "timestamp_utc": _now_utc_iso(),
            "player_name": "Player",
            "dimension": dimension,
            "score": score,
            "lines_cleared": lines_cleared,
            "start_speed_level": start_speed_level,
            "end_speed_level": end_speed_level,
            "duration_seconds": duration_seconds,
            "outcome": outcome,
            "bot_mode": bot_mode,
            "grid_mode": grid_mode,
            "random_mode": random_mode,
            "topology_mode": topology_mode,
            "exploration_mode": exploration_mode,
        }
    )
    ordered = sorted([*entries, candidate], key=_entry_sort_key)
    for idx, entry in enumerate(ordered):
        if str(entry.get("run_id")) == "__candidate__":
            return idx + 1
    return len(ordered)


def leaderboard_entry_would_enter(
    *,
    dimension: int,
    score: int,
    lines_cleared: int,
    start_speed_level: int,
    end_speed_level: int,
    duration_seconds: float,
    outcome: str,
    bot_mode: str,
    grid_mode: str,
    random_mode: str,
    topology_mode: str,
    exploration_mode: bool,
    path: Path | None = None,
) -> tuple[bool, int]:
    rank = leaderboard_entry_rank(
        dimension=dimension,
        score=score,
        lines_cleared=lines_cleared,
        start_speed_level=start_speed_level,
        end_speed_level=end_speed_level,
        duration_seconds=duration_seconds,
        outcome=outcome,
        bot_mode=bot_mode,
        grid_mode=grid_mode,
        random_mode=random_mode,
        topology_mode=topology_mode,
        exploration_mode=exploration_mode,
        path=path,
    )
    return rank <= _max_entries_limit(), rank


def record_leaderboard_entry(
    *,
    dimension: int,
    score: int,
    lines_cleared: int,
    start_speed_level: int,
    end_speed_level: int,
    duration_seconds: float,
    outcome: str,
    bot_mode: str,
    grid_mode: str,
    random_mode: str,
    topology_mode: str,
    exploration_mode: bool,
    player_name: str = "Player",
    path: Path | None = None,
) -> dict[str, object]:
    target = _leaderboard_path(path)
    payload = _load_payload(target) if target.exists() else _default_payload()
    entries_raw = payload.get("entries")
    if not isinstance(entries_raw, list):
        entries_raw = []

    entry = _normalize_entry(
        {
            "run_id": uuid.uuid4().hex[:12],
            "timestamp_utc": _now_utc_iso(),
            "player_name": player_name,
            "dimension": dimension,
            "score": score,
            "lines_cleared": lines_cleared,
            "start_speed_level": start_speed_level,
            "end_speed_level": end_speed_level,
            "duration_seconds": duration_seconds,
            "outcome": outcome,
            "bot_mode": bot_mode,
            "grid_mode": grid_mode,
            "random_mode": random_mode,
            "topology_mode": topology_mode,
            "exploration_mode": exploration_mode,
        }
    )

    entries = [_normalize_entry(item) for item in entries_raw]
    entries.append(entry)
    payload["entries"] = _sort_and_trim(entries, max_entries=_max_entries_limit())
    payload["schema_version"] = _SCHEMA_VERSION
    payload["updated_at_utc"] = _now_utc_iso()
    atomic_write_json(target, payload)
    return entry


__all__ = [
    "leaderboard_entry_rank",
    "leaderboard_entry_would_enter",
    "leaderboard_payload",
    "leaderboard_top_entries",
    "record_leaderboard_entry",
]
