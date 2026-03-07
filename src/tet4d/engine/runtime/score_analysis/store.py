from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def default_config(config_path: Path) -> dict[str, Any]:
    try:
        raw = config_path.read_text(encoding="utf-8")
        loaded = json.loads(raw)
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        pass
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
            "board_health": {"bias": 0.62, "weights": {}},
            "placement_quality": {"bias": 0.56, "weights": {}},
        },
    }


def load_json_object_or_default(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
        loaded = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return default
    if not isinstance(loaded, dict):
        return default
    return loaded


def atomic_write_summary_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)


def append_json_line(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def load_summary(
    path: Path,
    *,
    new_summary_fn,
    validate_summary_fn,
) -> dict[str, object]:
    loaded = load_json_object_or_default(path, new_summary_fn())
    ok, _msg = validate_summary_fn(loaded)
    if not ok:
        return new_summary_fn()
    return loaded
