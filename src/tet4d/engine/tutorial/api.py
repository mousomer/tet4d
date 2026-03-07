from __future__ import annotations

from typing import Any

from .content import (
    tutorial_board_dims_for_mode,
    tutorial_lesson_ids,
    tutorial_payload_dict,
    tutorial_plan_payload_dict,
)
from .runtime import create_tutorial_runtime_session, tutorial_progress_snapshot
from .setup_apply import (
    apply_tutorial_step_setup_2d,
    apply_tutorial_step_setup_nd,
    ensure_tutorial_piece_visibility_2d,
    ensure_tutorial_piece_visibility_nd,
)


def tutorial_lessons_payload_runtime() -> dict[str, Any]:
    return tutorial_payload_dict()


def tutorial_plan_payload_runtime() -> dict[str, Any]:
    return tutorial_plan_payload_dict()


def tutorial_lesson_ids_runtime() -> tuple[str, ...]:
    return tutorial_lesson_ids()


def tutorial_board_dims_runtime(mode: str) -> tuple[int, ...]:
    return tutorial_board_dims_for_mode(mode)


def tutorial_progress_snapshot_runtime() -> dict[str, Any]:
    return tutorial_progress_snapshot()


def tutorial_runtime_create_session_runtime(*, lesson_id: str, mode: str) -> Any:
    return create_tutorial_runtime_session(lesson_id=lesson_id, mode=mode)


def tutorial_runtime_action_allowed_runtime(session: Any, action_id: str) -> bool:
    return bool(session.action_allowed(action_id))


def tutorial_runtime_is_running_runtime(session: Any) -> bool:
    return bool(session.is_running())


def tutorial_runtime_observe_action_runtime(session: Any, action_id: str) -> None:
    session.observe_action(action_id)


def tutorial_runtime_sync_and_advance_runtime(
    session: Any,
    *,
    lines_cleared: int,
    overlay_transparency: float | None = None,
    grid_visible: bool = True,
    grid_mode: str | None = None,
    board_cell_count: int = 0,
) -> None:
    session.sync_and_advance(
        lines_cleared=lines_cleared,
        overlay_transparency=overlay_transparency,
        grid_visible=grid_visible,
        grid_mode=grid_mode,
        board_cell_count=board_cell_count,
    )


def tutorial_runtime_overlay_payload_runtime(session: Any) -> dict[str, Any]:
    return dict(session.overlay_payload())


def tutorial_runtime_required_action_runtime(session: Any) -> str | None:
    return session.required_action()


def tutorial_runtime_allowed_actions_runtime(session: Any) -> tuple[str, ...]:
    return tuple(session.allowed_actions())


def tutorial_runtime_event_log_tail_runtime(
    session: Any,
    *,
    limit: int = 200,
) -> tuple[dict[str, Any], ...]:
    return tuple(session.event_log_tail_payload(limit=limit))


def tutorial_runtime_consume_pending_setup_runtime(
    session: Any,
) -> dict[str, Any] | None:
    payload = session.consume_pending_setup()
    if payload is None:
        return None
    return dict(payload)


def tutorial_runtime_restart_runtime(session: Any) -> bool:
    return bool(session.restart())


def tutorial_runtime_redo_stage_runtime(session: Any) -> bool:
    return bool(session.redo_stage())


def tutorial_runtime_previous_stage_runtime(session: Any) -> bool:
    return bool(session.previous_stage())


def tutorial_runtime_next_stage_runtime(session: Any) -> bool:
    return bool(session.next_stage())


def tutorial_runtime_skip_runtime(session: Any) -> bool:
    return bool(session.skip())


def tutorial_runtime_transition_pending_runtime(session: Any) -> bool:
    return bool(session.transition_pending())


def tutorial_runtime_completion_ready_runtime(session: Any) -> bool:
    return bool(session.completion_ready())


def tutorial_apply_step_setup_2d_runtime(
    state: Any,
    cfg: Any,
    payload: dict[str, Any],
) -> None:
    setup = payload.get("setup")
    if not isinstance(setup, dict):
        setup = {}
    apply_tutorial_step_setup_2d(
        state,
        cfg,
        setup,
        lesson_id=str(payload.get("lesson_id", "")),
        step_id=str(payload.get("step_id", "")),
    )


def tutorial_apply_step_setup_nd_runtime(
    state: Any,
    cfg: Any,
    payload: dict[str, Any],
) -> None:
    setup = payload.get("setup")
    if not isinstance(setup, dict):
        setup = {}
    apply_tutorial_step_setup_nd(
        state,
        cfg,
        setup,
        lesson_id=str(payload.get("lesson_id", "")),
        step_id=str(payload.get("step_id", "")),
    )


def tutorial_ensure_piece_visibility_2d_runtime(
    state: Any,
    cfg: Any,
    *,
    min_visible_layer: int = 2,
) -> bool:
    try:
        ensure_tutorial_piece_visibility_2d(
            state,
            cfg,
            min_visible_layer=int(min_visible_layer),
        )
        return True
    except RuntimeError:
        return False


def tutorial_ensure_piece_visibility_nd_runtime(
    state: Any,
    cfg: Any,
    *,
    min_visible_layer: int = 2,
) -> bool:
    try:
        ensure_tutorial_piece_visibility_nd(
            state,
            cfg,
            min_visible_layer=int(min_visible_layer),
        )
        return True
    except RuntimeError:
        return False


__all__ = [name for name in globals() if name.endswith("_runtime")]
