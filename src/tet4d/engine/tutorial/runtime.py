from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any

from tet4d.engine.runtime.project_config import project_constant_int
from tet4d.engine.runtime.settings_schema import sanitize_text

from .content import tutorial_lesson_map
from .manager import TutorialManager
from .persistence import (
    load_tutorial_progress,
    mark_tutorial_lesson_completed,
    mark_tutorial_lesson_started,
)

_ALWAYS_ALLOWED_ACTIONS = {"quit", "soft_drop"}
_MAX_MODE_LENGTH = 8
_MOVE_PREFIX = "move_"
_ROTATE_PREFIX = "rotate_"
_OVERLAY_ACTIONS = {"overlay_alpha_dec", "overlay_alpha_inc"}
_OVERLAY_STEP_IDS = frozenset(_OVERLAY_ACTIONS)
_GOAL_STEP_IDS = frozenset(
    {"target_drop", "line_fill", "layer_fill", "hyper_layer_fill", "full_clear_bonus"}
)
_CAMERA_ROTATION_STEP_IDS = frozenset(
    {
        "yaw_fine_neg",
        "yaw_neg",
        "yaw_pos",
        "yaw_fine_pos",
        "pitch_neg",
        "pitch_pos",
        "view_xw_neg",
        "view_xw_pos",
        "view_zw_neg",
        "view_zw_pos",
    }
)
_CAMERA_CONTROL_STEP_IDS = frozenset(
    {"toggle_grid", "zoom_in", "zoom_out", "cycle_projection", "camera_reset"}
)
_TUTORIAL_STAGE_DELAY_MS = project_constant_int(
    ("tutorial", "step_transition_delay_ms"),
    1000,
    min_value=0,
    max_value=5000,
)
_OVERLAY_TARGET_MIN_PERCENT = project_constant_int(
    ("tutorial", "overlay_target_percent", "min"),
    20,
    min_value=0,
    max_value=100,
)
_OVERLAY_TARGET_MAX_PERCENT = project_constant_int(
    ("tutorial", "overlay_target_percent", "max"),
    80,
    min_value=0,
    max_value=100,
)
_OVERLAY_TARGET_TOLERANCE_PERCENT = project_constant_int(
    ("tutorial", "overlay_target_tolerance_percent"),
    2,
    min_value=0,
    max_value=20,
)


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
    required_event_count = max(1, int(step.complete_when.event_count_required))
    if required_event_count > 1:
        payload["required_event_count"] = required_event_count
    return payload


def _is_move_or_rotate_step(step_id: str | None) -> bool:
    if not step_id:
        return False
    return step_id.startswith(_MOVE_PREFIX) or step_id.startswith(_ROTATE_PREFIX)


def _suppress_board_piece_setup(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload:
        return {}
    kept: dict[str, Any] = {}
    camera_preset = payload.get("camera_preset")
    if camera_preset is not None:
        kept["camera_preset"] = camera_preset
    return kept


def _is_overlay_target_step(step_id: str | None) -> bool:
    if not step_id:
        return False
    return step_id in _OVERLAY_STEP_IDS


def _overlay_percent(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        return None
    return max(0, min(100, int(round(float(value) * 100.0))))


def _overlay_range() -> tuple[int, int]:
    low = max(0, min(100, int(_OVERLAY_TARGET_MIN_PERCENT)))
    high = max(0, min(100, int(_OVERLAY_TARGET_MAX_PERCENT)))
    if high < low:
        low, high = high, low
    return low, high


def _segment_title_for_step(*, step_id: str | None, mode: str) -> str:
    if not step_id:
        return "Overview"
    if step_id in _GOAL_STEP_IDS:
        return "Goals"
    if step_id in _CAMERA_CONTROL_STEP_IDS or step_id in _OVERLAY_STEP_IDS:
        return "Camera Controls"
    if step_id in _CAMERA_ROTATION_STEP_IDS:
        return "Camera Rotations"
    if step_id.startswith(_ROTATE_PREFIX):
        return "Piece Rotations"
    if step_id.startswith(_MOVE_PREFIX) or step_id in {"soft_drop", "hard_drop"}:
        return "Translations"
    if mode in {"3d", "4d"}:
        return "Camera Controls"
    return "Overview"


def _now_ms() -> int:
    return int(time.monotonic() * 1000.0)


@dataclass
class TutorialRuntimeSession:
    lesson_id: str
    mode: str
    manager: TutorialManager
    step_start_lines_cleared: int = 0
    _last_step_id: str | None = None
    _status_message: str = ""
    _pending_setup_step_id: str | None = None
    _last_lines_cleared: int = 0
    _transition_from_step_id: str | None = None
    _pending_step_advance_at_ms: int | None = None
    _overlay_target_percent: int | None = None
    _overlay_target_nonce: int = 0
    _overlay_action_seen: bool = False
    _overlay_current_percent: int | None = None

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
        if self._pending_step_advance_at_ms is not None:
            return False
        if _is_overlay_target_step(self._last_step_id) and action in _OVERLAY_ACTIONS:
            return True
        return self.manager.is_action_allowed(action)

    def observe_action(self, action_id: object) -> None:
        if not self.manager.is_running():
            return
        action = sanitize_text(action_id, max_length=96).strip().lower()
        if not action:
            return
        if _is_overlay_target_step(self._last_step_id) and action in _OVERLAY_ACTIONS:
            self._overlay_action_seen = True
        self.manager.record_event(action)

    def sync_and_advance(
        self,
        *,
        lines_cleared: int,
        overlay_transparency: float | None = None,
        grid_visible: bool | None = None,
        board_cell_count: int | None = None,
    ) -> bool:
        if not self.manager.is_running():
            return False
        current_lines = _normalized_lines_cleared(lines_cleared)
        self._last_lines_cleared = current_lines
        target_met = self._sync_predicates(
            current_lines=current_lines,
            overlay_transparency=overlay_transparency,
            grid_visible=grid_visible,
            board_cell_count=board_cell_count,
        )
        progressed = self._maybe_advance_step(target_met=target_met)

        snapshot = self.manager.snapshot()
        if snapshot.lesson_id is None and snapshot.status == "completed":
            mark_tutorial_lesson_completed(self.lesson_id)
            self._status_message = "Tutorial complete"
            self._last_step_id = None
            self._pending_setup_step_id = None
            self._pending_step_advance_at_ms = None
            return progressed
        if snapshot.step_id != self._last_step_id:
            self._enter_step_runtime_state(
                step_id=snapshot.step_id,
                current_lines=current_lines,
            )
        return progressed

    def _sync_predicates(
        self,
        *,
        current_lines: int,
        overlay_transparency: float | None,
        grid_visible: bool | None,
        board_cell_count: int | None,
    ) -> bool:
        cleared_step = current_lines > int(self.step_start_lines_cleared)
        self.manager.set_predicate("line_cleared", cleared_step)
        self.manager.set_predicate("layer_cleared", cleared_step)
        self.manager.set_predicate("hyper_layer_cleared", cleared_step)
        overlay_pct = _overlay_percent(overlay_transparency)
        self._overlay_current_percent = overlay_pct
        range_low, range_high = _overlay_range()
        in_range = False
        if overlay_pct is not None:
            in_range = range_low <= int(overlay_pct) <= range_high
        target_met = self._overlay_target_reached(overlay_pct)
        self.manager.set_predicate("overlay_alpha_in_range", in_range)
        self.manager.set_predicate(
            "overlay_alpha_target_reached",
            bool(target_met and self._overlay_action_seen),
        )
        if grid_visible is not None:
            self.manager.set_predicate("grid_enabled", bool(grid_visible))
        if board_cell_count is not None:
            self.manager.set_predicate("board_cleared", int(board_cell_count) <= 0)
        return bool(target_met)

    def _maybe_advance_step(self, *, target_met: bool) -> bool:
        completion_ready = self.manager.completion_ready()
        if completion_ready and _is_overlay_target_step(self._last_step_id):
            completion_ready = bool(target_met and self._overlay_action_seen)
        if not completion_ready:
            self._pending_step_advance_at_ms = None
            return False
        if self._pending_step_advance_at_ms is None:
            self._pending_step_advance_at_ms = _now_ms() + int(_TUTORIAL_STAGE_DELAY_MS)
            self._status_message = "Stage complete. Next stage in 1s..."
        if _now_ms() < int(self._pending_step_advance_at_ms):
            return False
        progressed = self.manager.advance_if_complete()
        self._pending_step_advance_at_ms = None
        return bool(progressed)

    def restart(self) -> bool:
        restarted = self.manager.restart()
        if restarted:
            self.step_start_lines_cleared = 0
            self._last_step_id = self.manager.snapshot().step_id
            self._pending_setup_step_id = self._last_step_id
            self._transition_from_step_id = None
            self._pending_step_advance_at_ms = None
            self._overlay_action_seen = False
            self._refresh_overlay_target()
            self._status_message = "Tutorial restarted"
        return restarted

    def redo_stage(self) -> bool:
        redone = self.manager.redo_current_step()
        if redone:
            snapshot = self.manager.snapshot()
            self.step_start_lines_cleared = int(self._last_lines_cleared)
            self._last_step_id = snapshot.step_id
            self._pending_setup_step_id = snapshot.step_id
            self._transition_from_step_id = None
            self._pending_step_advance_at_ms = None
            self._overlay_action_seen = False
            self._refresh_overlay_target()
            self._status_message = "Stage restarted"
        return redone

    def previous_stage(self) -> bool:
        moved = self.manager.previous_step()
        if moved:
            snapshot = self.manager.snapshot()
            self.step_start_lines_cleared = int(self._last_lines_cleared)
            self._last_step_id = snapshot.step_id
            self._pending_setup_step_id = snapshot.step_id
            self._transition_from_step_id = None
            self._pending_step_advance_at_ms = None
            self._overlay_action_seen = False
            self._refresh_overlay_target()
            self._status_message = "Moved to previous stage"
        return moved

    def next_stage(self) -> bool:
        moved = self.manager.next_step()
        if moved:
            snapshot = self.manager.snapshot()
            self.step_start_lines_cleared = int(self._last_lines_cleared)
            self._last_step_id = snapshot.step_id
            self._pending_setup_step_id = snapshot.step_id
            self._transition_from_step_id = None
            self._pending_step_advance_at_ms = None
            self._overlay_action_seen = False
            self._refresh_overlay_target()
            self._status_message = "Moved to next stage"
        return moved

    def skip(self) -> bool:
        skipped = self.manager.skip()
        if skipped:
            self._status_message = "Tutorial skipped"
            self._pending_setup_step_id = None
            self._transition_from_step_id = None
            self._pending_step_advance_at_ms = None
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
        setup_payload = _step_setup_payload(step)
        if _is_move_or_rotate_step(self._transition_from_step_id) and _is_move_or_rotate_step(
            snapshot.step_id
        ):
            setup_payload = _suppress_board_piece_setup(setup_payload)
        self._pending_setup_step_id = None
        self._transition_from_step_id = None
        return {
            "lesson_id": lesson.lesson_id,
            "step_id": step.step_id,
            "setup": setup_payload,
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
            "next_step_text": "",
            "key_prompts": [],
            "highlights": [],
            "progress_text": "",
            "segment_title": "",
            "system_controls_text": "",
        }
        if snapshot.lesson_id is None:
            return payload
        lesson = self.manager.current_lesson()
        step = self.manager.current_step()
        payload["lesson_title"] = lesson.title
        payload["step_text"] = step.ui.text
        payload["segment_title"] = _segment_title_for_step(
            step_id=step.step_id,
            mode=self.mode,
        )
        hint_text = step.ui.hint or ""
        if _is_overlay_target_step(step.step_id):
            target = self._overlay_target_percent
            current = self._overlay_current_percent
            if target is not None and current is not None:
                hint_text = (
                    f"{hint_text} Target: {target}% (current: {current}%).".strip()
                )
            elif target is not None:
                hint_text = f"{hint_text} Target: {target}%.".strip()
        payload["step_hint"] = hint_text
        next_index = int(snapshot.step_index) + 1
        if next_index < len(lesson.steps):
            payload["next_step_text"] = lesson.steps[next_index].ui.text
        payload["key_prompts"] = list(step.ui.key_prompts)
        payload["highlights"] = list(step.ui.highlights)
        payload["progress_text"] = (
            f"Step {snapshot.step_index + 1}/{len(lesson.steps)}"
        )
        payload["system_controls_text"] = "System controls: Help, Menu, Restart, Quit."
        return payload

    def required_action(self) -> str | None:
        if not self.manager.is_running():
            return None
        step = self.manager.current_step()
        if not step.ui.key_prompts:
            return None
        action = str(step.ui.key_prompts[0]).strip().lower()
        return action or None

    def allowed_actions(self) -> tuple[str, ...]:
        if not self.manager.is_running():
            return ()
        step = self.manager.current_step()
        actions = list(step.gating.allow)
        if _is_overlay_target_step(step.step_id):
            for action in sorted(_OVERLAY_ACTIONS):
                if action not in actions:
                    actions.append(action)
        return tuple(actions)

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

    def _enter_step_runtime_state(
        self,
        *,
        step_id: str | None,
        current_lines: int,
    ) -> None:
        self._transition_from_step_id = self._last_step_id
        self.step_start_lines_cleared = current_lines
        self._last_step_id = step_id
        self._pending_setup_step_id = step_id
        self._pending_step_advance_at_ms = None
        self._overlay_action_seen = False
        self._refresh_overlay_target()

    def _refresh_overlay_target(self) -> None:
        step_id = self._last_step_id
        self._overlay_target_percent = None
        if not _is_overlay_target_step(step_id):
            return
        low, high = _overlay_range()
        seed = f"{self.lesson_id}:{step_id}:{self._overlay_target_nonce}"
        target_rng = random.Random(seed)
        self._overlay_target_percent = int(target_rng.randint(low, high))
        self._overlay_target_nonce += 1

    def _overlay_target_reached(self, overlay_percent: int | None) -> bool:
        if overlay_percent is None or self._overlay_target_percent is None:
            return False
        tolerance = max(0, int(_OVERLAY_TARGET_TOLERANCE_PERCENT))
        return abs(int(overlay_percent) - int(self._overlay_target_percent)) <= tolerance


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
    session = TutorialRuntimeSession(
        lesson_id=clean_id,
        mode=clean_mode,
        manager=manager,
        step_start_lines_cleared=0,
        _last_step_id=manager.snapshot().step_id,
        _status_message="Tutorial started",
        _pending_setup_step_id=manager.snapshot().step_id,
        _last_lines_cleared=0,
    )
    session._refresh_overlay_target()
    return session


def tutorial_progress_snapshot() -> dict[str, Any]:
    return load_tutorial_progress()
