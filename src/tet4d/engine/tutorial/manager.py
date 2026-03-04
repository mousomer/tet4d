from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from tet4d.engine.runtime.settings_schema import sanitize_text

from .conditions import evaluate_completion
from .events import (
    EVENT_CONDITION_MET,
    EVENT_LESSON_COMPLETED,
    EVENT_LESSON_SKIPPED,
    EVENT_STEP_COMPLETED,
    EVENT_STEP_STARTED,
    TutorialEvent,
    build_event,
)
from .gating import TutorialInputGate, gate_for_step
from .schema import (
    TutorialLesson,
    TutorialPayload,
    TutorialStep,
    build_tutorial_lesson_map,
)

_MAX_LESSON_ID_LENGTH = 96
_MAX_PREDICATE_NAME_LENGTH = 96
_EVENT_LOG_LIMIT = 200


def _normalize_lesson_id(raw: object) -> str:
    if not isinstance(raw, str):
        return ""
    return sanitize_text(raw, max_length=_MAX_LESSON_ID_LENGTH).strip().lower()


def _normalize_predicate_name(raw: object) -> str:
    if not isinstance(raw, str):
        return ""
    return sanitize_text(raw, max_length=_MAX_PREDICATE_NAME_LENGTH).strip().lower()


@dataclass(frozen=True)
class TutorialSnapshot:
    status: str
    lesson_id: str | None
    step_id: str | None
    step_index: int


class TutorialManager:
    def __init__(self, lessons: Mapping[str, TutorialLesson]) -> None:
        ordered_lessons = dict(lessons)
        if not ordered_lessons:
            raise ValueError("TutorialManager requires at least one lesson")
        self._lessons = ordered_lessons
        self._active_lesson_id: str | None = None
        self._step_index = 0
        self._events_seen: dict[str, int] = {}
        self._predicate_values: dict[str, bool] = {}
        self._event_log: list[TutorialEvent] = []
        self._sequence = 0
        self._status = "idle"

    @classmethod
    def from_payload(cls, payload: TutorialPayload) -> TutorialManager:
        return cls(build_tutorial_lesson_map(payload))

    def lesson_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._lessons.keys()))

    def start(self, lesson_id: str) -> None:
        target = _normalize_lesson_id(lesson_id)
        if target not in self._lessons:
            raise KeyError(f"Unknown tutorial lesson: {lesson_id}")
        self._active_lesson_id = target
        self._step_index = 0
        self._status = "running"
        self._enter_current_step()

    def restart(self) -> bool:
        if self._active_lesson_id is None:
            return False
        self.start(self._active_lesson_id)
        return True

    def redo_current_step(self) -> bool:
        if not self.is_running():
            return False
        self._enter_current_step()
        return True

    def previous_step(self) -> bool:
        if not self.is_running() or self._step_index <= 0:
            return False
        self._step_index -= 1
        self._enter_current_step()
        return True

    def next_step(self) -> bool:
        if not self.is_running():
            return False
        lesson = self.current_lesson()
        if self._step_index + 1 >= len(lesson.steps):
            return False
        self._step_index += 1
        self._enter_current_step()
        return True

    def skip(self) -> bool:
        if self._active_lesson_id is None:
            return False
        self._emit(EVENT_LESSON_SKIPPED, {"lesson_id": self._active_lesson_id})
        self._active_lesson_id = None
        self._step_index = 0
        self._status = "skipped"
        self._events_seen.clear()
        self._predicate_values.clear()
        return True

    def is_running(self) -> bool:
        return self._active_lesson_id is not None and self._status == "running"

    def current_lesson(self) -> TutorialLesson:
        if self._active_lesson_id is None:
            raise RuntimeError("No active tutorial lesson")
        return self._lessons[self._active_lesson_id]

    def current_step(self) -> TutorialStep:
        lesson = self.current_lesson()
        return lesson.steps[self._step_index]

    def current_gate(self) -> TutorialInputGate:
        return gate_for_step(self.current_step())

    def is_action_allowed(self, action_id: object) -> bool:
        return self.current_gate().is_action_allowed(action_id)

    def record_event(self, name: object, payload: dict[str, Any] | None = None) -> None:
        event = build_event(
            sequence=self._next_sequence(),
            name=name,
            payload=payload,
        )
        self._event_log.append(event)
        self._event_log = self._event_log[-_EVENT_LOG_LIMIT:]
        self._events_seen[event.name] = self._events_seen.get(event.name, 0) + 1

    def set_predicate(self, name: object, value: bool) -> None:
        key = _normalize_predicate_name(name)
        if not key:
            return
        self._predicate_values[key] = bool(value)

    def clear_predicates(self) -> None:
        self._predicate_values.clear()

    def completion_ready(self) -> bool:
        if not self.is_running():
            return False
        step = self.current_step()
        return bool(
            evaluate_completion(
                step.complete_when,
                events_seen=self._events_seen,
                predicate_values=self._predicate_values,
            )
        )

    def advance_if_complete(self) -> bool:
        if not self.is_running():
            return False
        if not self.completion_ready():
            return False
        lesson = self.current_lesson()
        step = self.current_step()
        self._emit(
            EVENT_CONDITION_MET,
            {
                "lesson_id": lesson.lesson_id,
                "step_id": step.step_id,
                "step_index": self._step_index,
            },
        )
        self._emit(
            EVENT_STEP_COMPLETED,
            {
                "lesson_id": lesson.lesson_id,
                "step_id": step.step_id,
                "step_index": self._step_index,
            },
        )
        if self._step_index + 1 >= len(lesson.steps):
            self._emit(EVENT_LESSON_COMPLETED, {"lesson_id": lesson.lesson_id})
            self._active_lesson_id = None
            self._step_index = 0
            self._status = "completed"
            self._events_seen.clear()
            self._predicate_values.clear()
            return True
        self._step_index += 1
        self._enter_current_step()
        return True

    def snapshot(self) -> TutorialSnapshot:
        if self._active_lesson_id is None:
            return TutorialSnapshot(
                status=self._status,
                lesson_id=None,
                step_id=None,
                step_index=0,
            )
        step = self.current_step()
        return TutorialSnapshot(
            status=self._status,
            lesson_id=self._active_lesson_id,
            step_id=step.step_id,
            step_index=self._step_index,
        )

    def event_log_tail(self, *, limit: int = _EVENT_LOG_LIMIT) -> tuple[TutorialEvent, ...]:
        bounded_limit = max(1, int(limit))
        return tuple(self._event_log[-bounded_limit:])

    def _emit(self, name: str, payload: dict[str, Any] | None = None) -> None:
        self.record_event(name, payload=payload)

    def _next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    def _enter_current_step(self) -> None:
        lesson = self.current_lesson()
        step = self.current_step()
        self._events_seen.clear()
        self._predicate_values.clear()
        self._emit(
            EVENT_STEP_STARTED,
            {
                "lesson_id": lesson.lesson_id,
                "step_id": step.step_id,
                "step_index": self._step_index,
            },
        )
