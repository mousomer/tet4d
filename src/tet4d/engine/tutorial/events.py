from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tet4d.engine.runtime.settings_schema import sanitize_text

EVENT_STEP_STARTED = "step_started"
EVENT_HINT_SHOWN = "hint_shown"
EVENT_CONDITION_MET = "condition_met"
EVENT_STEP_COMPLETED = "step_completed"
EVENT_LESSON_COMPLETED = "lesson_completed"
EVENT_LESSON_SKIPPED = "lesson_skipped"

_MAX_EVENT_NAME_LENGTH = 96


@dataclass(frozen=True)
class TutorialEvent:
    sequence: int
    name: str
    payload: dict[str, Any]


def sanitize_event_name(name: object) -> str:
    if not isinstance(name, str):
        return ""
    cleaned = sanitize_text(name, max_length=_MAX_EVENT_NAME_LENGTH).strip().lower()
    return cleaned


def build_event(
    *,
    sequence: int,
    name: object,
    payload: dict[str, Any] | None = None,
) -> TutorialEvent:
    clean_name = sanitize_event_name(name)
    if not clean_name:
        raise ValueError("event name must be a non-empty printable string")
    return TutorialEvent(
        sequence=max(0, int(sequence)),
        name=clean_name,
        payload=dict(payload or {}),
    )
