from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from timeit import default_timer
from typing import Iterator


@dataclass(frozen=True)
class ExplorerInteractionAuditEvent:
    action: str
    phase: str
    kind: str
    elapsed_ms: float
    metadata: dict[str, object]


@dataclass(frozen=True)
class ExplorerInteractionAuditSpan:
    action: str
    phase: str
    duration_ms: float
    metadata: dict[str, object]


@dataclass
class ExplorerInteractionAudit:
    started_at: float = field(default_factory=default_timer)
    action_stack: list[str] = field(default_factory=list)
    events: list[ExplorerInteractionAuditEvent] = field(default_factory=list)
    spans: list[ExplorerInteractionAuditSpan] = field(default_factory=list)


_ACTIVE_AUDIT: ContextVar[ExplorerInteractionAudit | None] = ContextVar(
    "topology_lab_active_audit",
    default=None,
)


def current_audit_action(state: object) -> str | None:
    audit = getattr(state, "interaction_audit", None)
    if not isinstance(audit, ExplorerInteractionAudit) or not audit.action_stack:
        return None
    return audit.action_stack[-1]


def _audit_for_state(state: object) -> ExplorerInteractionAudit | None:
    audit = getattr(state, "interaction_audit", None)
    if isinstance(audit, ExplorerInteractionAudit):
        return audit
    return None


def _elapsed_ms(audit: ExplorerInteractionAudit) -> float:
    return (default_timer() - audit.started_at) * 1000.0


def _metadata_payload(metadata: dict[str, object]) -> dict[str, object]:
    return {str(key): value for key, value in metadata.items() if value is not None}


def _pop_action(audit: ExplorerInteractionAudit, action: str) -> None:
    if not audit.action_stack:
        return
    if audit.action_stack[-1] == action:
        audit.action_stack.pop()
        return
    for index in range(len(audit.action_stack) - 1, -1, -1):
        if audit.action_stack[index] == action:
            del audit.action_stack[index]
            return


@contextmanager
def record_interaction_handler(
    state: object,
    action: str,
    **metadata: object,
) -> Iterator[None]:
    audit = _audit_for_state(state)
    if audit is None:
        yield
        return
    payload = _metadata_payload(metadata)
    audit.events.append(
        ExplorerInteractionAuditEvent(
            action=str(action),
            phase="handler",
            kind="start",
            elapsed_ms=_elapsed_ms(audit),
            metadata=payload,
        )
    )
    audit.action_stack.append(str(action))
    token = _ACTIVE_AUDIT.set(audit)
    started_at = default_timer()
    try:
        yield
    finally:
        _ACTIVE_AUDIT.reset(token)
        _pop_action(audit, str(action))
        audit.events.append(
            ExplorerInteractionAuditEvent(
                action=str(action),
                phase="handler",
                kind="end",
                elapsed_ms=_elapsed_ms(audit),
                metadata=payload,
            )
        )
        audit.spans.append(
            ExplorerInteractionAuditSpan(
                action=str(action),
                phase="handler",
                duration_ms=(default_timer() - started_at) * 1000.0,
                metadata=payload,
            )
        )


@contextmanager
def record_interaction_phase(
    state: object,
    phase: str,
    *,
    action: str | None = None,
    **metadata: object,
) -> Iterator[None]:
    audit = _audit_for_state(state)
    if audit is None:
        yield
        return
    resolved_action = (
        str(action)
        if action is not None
        else current_audit_action(state) or "scene_refresh"
    )
    payload = _metadata_payload(metadata)
    audit.events.append(
        ExplorerInteractionAuditEvent(
            action=resolved_action,
            phase=str(phase),
            kind="start",
            elapsed_ms=_elapsed_ms(audit),
            metadata=payload,
        )
    )
    token = _ACTIVE_AUDIT.set(audit)
    started_at = default_timer()
    try:
        yield
    finally:
        _ACTIVE_AUDIT.reset(token)
        audit.events.append(
            ExplorerInteractionAuditEvent(
                action=resolved_action,
                phase=str(phase),
                kind="end",
                elapsed_ms=_elapsed_ms(audit),
                metadata=payload,
            )
        )
        audit.spans.append(
            ExplorerInteractionAuditSpan(
                action=resolved_action,
                phase=str(phase),
                duration_ms=(default_timer() - started_at) * 1000.0,
                metadata=payload,
            )
        )


@contextmanager
def record_active_interaction_phase(
    phase: str,
    **metadata: object,
) -> Iterator[None]:
    audit = _ACTIVE_AUDIT.get()
    if audit is None:
        yield
        return
    resolved_action = audit.action_stack[-1] if audit.action_stack else "scene_refresh"
    payload = _metadata_payload(metadata)
    audit.events.append(
        ExplorerInteractionAuditEvent(
            action=resolved_action,
            phase=str(phase),
            kind="start",
            elapsed_ms=_elapsed_ms(audit),
            metadata=payload,
        )
    )
    started_at = default_timer()
    try:
        yield
    finally:
        audit.events.append(
            ExplorerInteractionAuditEvent(
                action=resolved_action,
                phase=str(phase),
                kind="end",
                elapsed_ms=_elapsed_ms(audit),
                metadata=payload,
            )
        )
        audit.spans.append(
            ExplorerInteractionAuditSpan(
                action=resolved_action,
                phase=str(phase),
                duration_ms=(default_timer() - started_at) * 1000.0,
                metadata=payload,
            )
        )


def latest_span_for_phase(
    state: object,
    *,
    action: str,
    phase: str,
) -> ExplorerInteractionAuditSpan | None:
    audit = _audit_for_state(state)
    if audit is None:
        return None
    for span in reversed(audit.spans):
        if span.action == action and span.phase == phase:
            return span
    return None


__all__ = [
    "ExplorerInteractionAudit",
    "ExplorerInteractionAuditEvent",
    "ExplorerInteractionAuditSpan",
    "current_audit_action",
    "record_active_interaction_phase",
    "latest_span_for_phase",
    "record_interaction_handler",
    "record_interaction_phase",
]
