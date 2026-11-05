"""Shared completion contract and explicit, bounded execution-trace review.

This does not intercept agent tools or enable transcript collection. Callers
provide normalized observations; absent completion remains unknown.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

POLICY_ID = "synchronous-completion-v1"
POLICY_PATH = "policies/execution.json"
REQUIRED = {
    "local_completion": "await_exit",
    "remote_completion": "blocking_watch_or_notification",
    "yield_handling": "resume_same_invocation",
    "agent_status_polling": "forbidden",
    "parallel_completion": "await_all_preserve_failures",
    "unknown_outcome": "never_success",
    "recovery": "reconnect_same_identity_no_automatic_redispatch",
}


def load_policy(pack: Path, manifest: dict) -> dict:
    binding = manifest.get("execution_policy")
    if binding != {"id": POLICY_ID, "path": POLICY_PATH}:
        raise ValueError("missing or incompatible shared execution policy binding")
    path = pack / POLICY_PATH
    if path.is_symlink() or not path.resolve().is_relative_to(pack.resolve()):
        raise ValueError("execution policy must be owned by the selected pack")
    raw = path.read_bytes()
    policy = json.loads(raw)
    if policy != {"schema_version": 1, "id": POLICY_ID, "requirements": REQUIRED}:
        raise ValueError("shared execution policy is incomplete or weakened")
    return {**policy, "sha256": hashlib.sha256(raw).hexdigest()}


def _start(event: dict, active: dict, outcomes: dict) -> str | None:
    identity = event["id"]
    if identity in active or identity in outcomes:
        return "duplicate_execution"
    if event.get("mode") not in {"local", "remote"}:
        return "unsupported_completion_mechanism"
    sha = event.get("sha")
    if event["mode"] == "remote" and (
        not isinstance(sha, str)
        or len(sha) != 40
        or any(c not in "0123456789abcdef" for c in sha)
    ):
        return "missing_remote_sha"
    active[identity] = {**event, "watching": False}
    return None


def _finish(event: dict, active: dict, outcomes: dict) -> str | None:
    identity = event["id"]
    operation = active[identity]
    if operation["mode"] == "remote" and not operation["watching"]:
        return "missing_completion_mechanism"
    if event.get("sha", operation.get("sha")) != operation.get("sha"):
        return "remote_identity_changed"
    code = event.get("exit_code")
    if type(code) is not int:
        return "missing_exit_status"
    outcomes[identity] = "success" if code == 0 else "failure"
    del active[identity]
    return None


def _continue(event: dict, active: dict, outcomes: dict) -> str | None:
    identity, kind = event["id"], event.get("event")
    operation = active[identity]
    if event.get("sha", operation.get("sha")) != operation.get("sha"):
        return "remote_identity_changed"
    if kind in {"status_query", "log_tail", "redispatch"}:
        return "agent_polling_or_redispatch"
    if kind == "watch":
        if operation["watching"]:
            return "duplicate_watcher"
        operation["watching"] = True
    elif kind in {"yield", "wait", "disconnect", "reconnect", "notification"}:
        if kind == "notification":
            operation["watching"] = True
    elif kind == "finish":
        return _finish(event, active, outcomes)
    elif kind in {"timeout", "cancel", "unsupported"}:
        outcomes[identity] = kind
        del active[identity]
    else:
        return "unsupported_event"
    return None


def review_execution(events: list[dict]) -> dict:
    """Review at most 10,000 explicit observations; absent completion is unknown.

    This opt-in checker does not collect or intercept tool calls. A remote run's
    commit SHA belongs to its identity, including during watcher recovery.
    """
    active: dict[str, dict] = {}
    outcomes: dict[str, str] = {}
    violations: list[str] = []
    if not isinstance(events, list) or len(events) > 10000:
        return {
            "status": "violation",
            "violations": ["invalid_trace"],
            "pending": [],
            "outcomes": {},
        }
    for event in events:
        if not isinstance(event, dict):
            violations.append("invalid_event")
            continue
        identity = event.get("id")
        if not isinstance(identity, str) or not identity:
            violations.append("missing_identity")
            continue
        if event.get("event") == "start":
            violation = _start(event, active, outcomes)
        elif identity not in active:
            violation = "unknown_execution"
        else:
            violation = _continue(event, active, outcomes)
        if violation:
            violations.append(violation)
    status = "success" if all(v == "success" for v in outcomes.values()) else "failure"
    if active or not outcomes:
        status = "unknown"
    if violations:
        status = "violation"
    return {
        "status": status,
        "violations": violations,
        "pending": sorted(active),
        "outcomes": outcomes,
    }
