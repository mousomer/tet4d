from __future__ import annotations

from typing import Any

from tet4d.engine.runtime.project_config import tutorial_progress_file_default_path
from tet4d.engine.runtime.settings_schema import (
    atomic_write_json,
    read_json_object_or_empty,
    sanitize_text,
)

_SCHEMA_VERSION = 1
_MAX_LESSON_ID_LENGTH = 96


def _sanitize_lesson_id(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return sanitize_text(value, max_length=_MAX_LESSON_ID_LENGTH).strip().lower()


def _normalize_completed(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in raw:
        lesson_id = _sanitize_lesson_id(value)
        if not lesson_id or lesson_id in seen:
            continue
        seen.add(lesson_id)
        out.append(lesson_id)
    return out


def _default_payload() -> dict[str, Any]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "last_started_lesson": "",
        "last_completed_lesson": "",
        "completed_lessons": [],
    }


def _normalize_payload(raw: dict[str, Any]) -> dict[str, Any]:
    payload = _default_payload()
    payload["schema_version"] = int(_SCHEMA_VERSION)
    payload["last_started_lesson"] = _sanitize_lesson_id(raw.get("last_started_lesson"))
    payload["last_completed_lesson"] = _sanitize_lesson_id(
        raw.get("last_completed_lesson")
    )
    payload["completed_lessons"] = _normalize_completed(raw.get("completed_lessons"))
    return payload


def load_tutorial_progress() -> dict[str, Any]:
    raw = read_json_object_or_empty(tutorial_progress_file_default_path())
    return _normalize_payload(raw)


def save_tutorial_progress(payload: dict[str, Any]) -> None:
    normalized = _normalize_payload(payload)
    atomic_write_json(tutorial_progress_file_default_path(), normalized)


def mark_tutorial_lesson_started(lesson_id: str) -> dict[str, Any]:
    payload = load_tutorial_progress()
    payload["last_started_lesson"] = _sanitize_lesson_id(lesson_id)
    save_tutorial_progress(payload)
    return payload


def mark_tutorial_lesson_completed(lesson_id: str) -> dict[str, Any]:
    clean_id = _sanitize_lesson_id(lesson_id)
    payload = load_tutorial_progress()
    payload["last_completed_lesson"] = clean_id
    completed = list(payload.get("completed_lessons", []))
    if clean_id and clean_id not in completed:
        completed.append(clean_id)
    payload["completed_lessons"] = completed
    save_tutorial_progress(payload)
    return payload
