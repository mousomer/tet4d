from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tet4d.engine.runtime.settings_schema import sanitize_text

from .content import tutorial_lesson_map
from .manager import TutorialManager
from .persistence import (
    load_tutorial_progress,
    mark_tutorial_lesson_completed,
    mark_tutorial_lesson_started,
)

_ALWAYS_ALLOWED_ACTIONS = {"quit"}
_MAX_MODE_LENGTH = 8


def _normalize_mode(value: object) -> str:
    if not isinstance(value, str):
        return "2d"
    mode = sanitize_text(value, max_length=_MAX_MODE_LENGTH).strip().lower()
    if mode not in {"2d", "3d", "4d"}:
        return "2d"
    return mode


def _normalized_lines_cleared(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return max(0, int(value))


def _step_setup_payload(step: Any) -> dict[str, Any]:
    setup_items = (
        ("camera_preset", step.setup.camera_preset),
        ("spawn_piece", step.setup.spawn_piece),
        ("starter_piece_id", step.setup.starter_piece_id),
        ("board_preset", step.setup.board_preset),
        ("rng_seed", step.setup.rng_seed),
        ("spawn_min_visible_layer", step.setup.spawn_min_visible_layer),
        ("bottom_layers_min", step.setup.bottom_layers_min),
        ("bottom_layers_max", step.setup.bottom_layers_max),
    )
    payload: dict[str, Any] = {}
    for key, value in setup_items:
        if value is not None:
            payload[key] = value
    return payload


@dataclass
class TutorialRuntimeSession:
    lesson_id: str
    mode: str
    manager: TutorialManager
    step_start_lines_cleared: int = 0
    _last_step_id: str | None = None
    _status_message: str = ""
    _pending_setup_step_id: str | None = None

    def is_running(self) -> bool:
        return bool(self.manager.is_running())

    def action_allowed(self, action_id: object) -> bool:
        action = sanitize_text(action_id, max_length=96).strip().lower()
        if not action:
            return False
        if action in _ALWAYS_ALLOWED_ACTIONS:
            return True
        if not self.manager.is_running():
            return True
        return self.manager.is_action_allowed(action)

    def observe_action(self, action_id: object) -> None:
        if not self.manager.is_running():
            return
        action = sanitize_text(action_id, max_length=96).strip().lower()
        if not action:
            return
        self.manager.record_event(action)

    def sync_and_advance(self, *, lines_cleared: int) -> bool:
        if not self.manager.is_running():
            return False
        current_lines = _normalized_lines_cleared(lines_cleared)
        cleared_step = current_lines > int(self.step_start_lines_cleared)
        self.manager.set_predicate("line_cleared", cleared_step)
        self.manager.set_predicate("layer_cleared", cleared_step)
        self.manager.set_predicate("hyper_layer_cleared", cleared_step)
        progressed = self.manager.advance_if_complete()
        snapshot = self.manager.snapshot()
        if snapshot.lesson_id is None and snapshot.status == "completed":
            mark_tutorial_lesson_completed(self.lesson_id)
            self._status_message = "Tutorial complete"
            self._last_step_id = None
            self._pending_setup_step_id = None
            return progressed
        if snapshot.step_id != self._last_step_id:
            self.step_start_lines_cleared = current_lines
            self._last_step_id = snapshot.step_id
            self._pending_setup_step_id = snapshot.step_id
        return progressed

    def restart(self) -> bool:
        restarted = self.manager.restart()
        if restarted:
            self.step_start_lines_cleared = 0
            self._last_step_id = self.manager.snapshot().step_id
            self._pending_setup_step_id = self._last_step_id
            self._status_message = "Tutorial restarted"
        return restarted

    def skip(self) -> bool:
        skipped = self.manager.skip()
        if skipped:
            self._status_message = "Tutorial skipped"
            self._pending_setup_step_id = None
        return skipped

    def consume_pending_setup(self) -> dict[str, Any] | None:
        if not self.manager.is_running():
            return None
        snapshot = self.manager.snapshot()
        if snapshot.step_id is None:
            return None
        if snapshot.step_id != self._pending_setup_step_id:
            return None
        lesson = self.manager.current_lesson()
        step = self.manager.current_step()
        self._pending_setup_step_id = None
        return {
            "lesson_id": lesson.lesson_id,
            "step_id": step.step_id,
            "setup": _step_setup_payload(step),
        }

    def overlay_payload(self) -> dict[str, Any]:
        snapshot = self.manager.snapshot()
        payload: dict[str, Any] = {
            "running": bool(self.manager.is_running()),
            "status": snapshot.status,
            "lesson_id": snapshot.lesson_id,
            "step_id": snapshot.step_id,
            "step_index": int(snapshot.step_index),
            "status_message": self._status_message,
            "lesson_title": "",
            "step_text": "",
            "step_hint": "",
            "key_prompts": [],
            "highlights": [],
            "progress_text": "",
        }
        if snapshot.lesson_id is None:
            return payload
        lesson = self.manager.current_lesson()
        step = self.manager.current_step()
        payload["lesson_title"] = lesson.title
        payload["step_text"] = step.ui.text
        payload["step_hint"] = step.ui.hint or ""
        payload["key_prompts"] = list(step.ui.key_prompts)
        payload["highlights"] = list(step.ui.highlights)
        payload["progress_text"] = (
            f"Step {snapshot.step_index + 1}/{len(lesson.steps)}"
        )
        return payload

    def event_log_tail_payload(self, *, limit: int = 200) -> list[dict[str, Any]]:
        events = self.manager.event_log_tail(limit=limit)
        payload: list[dict[str, Any]] = []
        for event in events:
            payload.append(
                {
                    "sequence": int(event.sequence),
                    "name": str(event.name),
                    "payload": dict(event.payload),
                }
            )
        return payload


def create_tutorial_runtime_session(*, lesson_id: str, mode: str) -> TutorialRuntimeSession:
    lessons = tutorial_lesson_map()
    clean_id = sanitize_text(lesson_id, max_length=96).strip().lower()
    lesson = lessons.get(clean_id)
    if lesson is None:
        raise KeyError(f"Unknown tutorial lesson id: {lesson_id}")
    clean_mode = _normalize_mode(mode)
    if lesson.mode != clean_mode:
        raise ValueError(
            f"lesson '{clean_id}' targets mode '{lesson.mode}', not '{clean_mode}'"
        )
    manager = TutorialManager(lessons)
    manager.start(clean_id)
    mark_tutorial_lesson_started(clean_id)
    return TutorialRuntimeSession(
        lesson_id=clean_id,
        mode=clean_mode,
        manager=manager,
        step_start_lines_cleared=0,
        _last_step_id=manager.snapshot().step_id,
        _status_message="Tutorial started",
        _pending_setup_step_id=manager.snapshot().step_id,
    )


def tutorial_progress_snapshot() -> dict[str, Any]:
    return load_tutorial_progress()
