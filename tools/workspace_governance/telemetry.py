"""Portable agent telemetry: record generic activity, never interpret it.

The pack records low-level facts about what happened; projects and experiments
interpret them elsewhere. Each event is one observation: its type and payload
say what happened, its source and attribution say how it was observed, and an
optional enrichment block adds what only that observer could see. Events follow
a versioned, project-independent schema, live outside the repository keyed by
workspace identity, and are written only on a machine whose local overlay
enables telemetry.

Recording must never change the outcome of the command it observes: every
failure here degrades to a single warning on stderr.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.workspace_governance.resolver.core import SAFE_WORKSPACE_ID
from tools.workspace_governance.validators.core import (
    _schema_issues,
    load_manifest_json,
)

SCHEMA_VERSION = 1
SCHEMA_FILE = Path(__file__).parent / "schemas/telemetry-event.v1.schema.json"
PRODUCER = "workspace-governance"
CONTEXT_VARIABLE = "GOVERNANCE_TELEMETRY_CONTEXT"
STORE_DIR = "workspace-governance"
CONTEXT_FIELDS = ("session_id", "task_id", "tool_call_id", "agent", "model")


class TelemetryError(ValueError):
    """An event cannot be recorded as a valid telemetry fact."""


@dataclass(frozen=True)
class TelemetrySettings:
    enabled: bool
    workspace_id: str | None
    directory: Path | None

    def to_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "workspace_id": self.workspace_id,
            "directory": str(self.directory) if self.directory else None,
        }


def producer_version() -> str:
    """The version of the pack that is recording, read from its own files."""
    return (Path(__file__).parent / "VERSION").read_text(encoding="utf-8").strip()


def store_directory(
    workspace_id: str, environ: dict[str, str] | None = None
) -> Path | None:
    """The workspace's event store, outside every checkout of it."""
    if not SAFE_WORKSPACE_ID.match(workspace_id):
        return None
    env = os.environ if environ is None else environ
    base = env.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
    return Path(base).expanduser() / STORE_DIR / workspace_id / "telemetry"


def resolve_settings(
    local: dict[str, Any] | None,
    workspace_id: str | None,
    environ: dict[str, str] | None = None,
) -> TelemetrySettings:
    """Telemetry is on only where the machine's overlay turns it on."""
    declared = (local or {}).get("telemetry")
    enabled = isinstance(declared, dict) and declared.get("enabled") is True
    directory = (
        store_directory(workspace_id, environ) if workspace_id is not None else None
    )
    return TelemetrySettings(enabled and directory is not None, workspace_id, directory)


def _hashed(value: str) -> dict[str, object]:
    return {
        "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
        "length": len(value),
    }


def recorded_arguments(
    argv: list[str], sensitive_options: frozenset[str]
) -> list[dict[str, object]]:
    """One token per argument; the values of sensitive options only as hashes.

    Free text and machine paths are recorded as a hash and a length, never as
    content. Which options carry them is the observer's knowledge of the
    program, so the caller names them.
    """
    tokens: list[dict[str, object]] = []
    hash_next = False
    for token in argv:
        option, separator, value = token.partition("=")
        if hash_next:
            tokens.append(_hashed(token))
            hash_next = False
        elif option in sensitive_options and separator:
            tokens.append({"prefix": option + separator, **_hashed(value)})
        else:
            tokens.append({"value": token})
            hash_next = token in sensitive_options
    return tokens


def run_context(environ: dict[str, str] | None = None) -> dict[str, object]:
    """Per-run context supplied at invocation; carried, never interpreted."""
    env = os.environ if environ is None else environ
    raw = env.get(CONTEXT_VARIABLE)
    if raw is None:
        return {"status": "absent", "labels": {}}
    invalid: dict[str, object] = {"status": "invalid", "labels": {}}
    try:
        supplied = json.loads(raw)
    except ValueError:
        return invalid
    if not isinstance(supplied, dict) or set(supplied) - {*CONTEXT_FIELDS, "labels"}:
        return invalid
    labels = supplied.get("labels", {})
    if not isinstance(labels, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in labels.items()
    ):
        return invalid
    context: dict[str, object] = {"status": "supplied", "labels": dict(labels)}
    for field in CONTEXT_FIELDS:
        value = supplied.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or not value:
            return invalid
        context[field] = value
    return context


def _git(root: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and value else None


def checkout_identity(root: Path) -> dict[str, object]:
    """Which checkout acted, without recording where it lives on this machine."""
    identity: dict[str, object] = {
        "path_sha256": hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()
    }
    revision = _git(root, "rev-parse", "HEAD")
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if revision:
        identity["revision"] = revision
    if branch and branch != "HEAD":
        identity["branch"] = branch
    return identity


def governance_enrichment(
    subcommand: str,
    diagnostics: list[dict[str, Any]],
    resolution: dict[str, Any] | None = None,
) -> dict[str, object]:
    """What only a first-hand `gov` observer knows about its own execution."""
    enrichment: dict[str, object] = {
        "subcommand": subcommand,
        "diagnostics": [
            {
                "code": str(item.get("code")),
                "fact": str(item.get("fact")),
                "owner": str(item.get("owner")),
            }
            for item in diagnostics
        ],
    }
    if resolution is not None:
        enrichment["resolution"] = resolution_summary(resolution)
    return enrichment


def build_command_execution(
    *,
    root: Path,
    workspace_id: str,
    project_id: str | None,
    producer_version: str,
    program: str,
    arguments: list[dict[str, object]],
    exit_status: int,
    duration_ms: int,
    governance: dict[str, object] | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, object]:
    """A first-hand observation of a command this process executed.

    The process identities are correlation evidence: another observer of the
    same execution, such as an agent transcript, can be matched to them
    explicitly rather than by program, arguments and time.
    """
    payload: dict[str, object] = {
        "program": program,
        "arguments": arguments,
        "exit_status": exit_status,
        "duration_ms": max(0, duration_ms),
        "invocation": {
            "process_id": os.getpid(),
            "parent_process_id": os.getppid(),
        },
    }
    if governance is not None:
        payload["governance"] = governance
    event: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "event_id": uuid.uuid4().hex,
        "event_type": "command_execution",
        "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "workspace_id": workspace_id,
        "checkout": checkout_identity(root),
        "context": run_context(environ),
        "source": {
            "kind": "self_instrumented",
            "producer": PRODUCER,
            "producer_version": producer_version,
        },
        "attribution": {"basis": "first_hand"},
        "payload": payload,
    }
    if project_id:
        event["project_id"] = project_id
    return event


def resolution_summary(resolved: dict[str, Any]) -> dict[str, object]:
    """Which governance context a resolution handed out, by identity."""
    entries = resolved.get("entries", {})
    summary: dict[str, object] = {"entries": sorted(entries)}

    def value(key: str) -> Any:
        entry = entries.get(key)
        return entry.get("value") if isinstance(entry, dict) else None

    if isinstance(value("execution.mode"), str):
        summary["mode"] = value("execution.mode")
    if isinstance(value("matched_scenario"), str):
        summary["matched_scenario"] = value("matched_scenario")
    if isinstance(value("routes"), dict):
        summary["routes"] = sorted(value("routes"))
    if isinstance(value("authorities"), list):
        summary["authorities"] = [
            {"authority_id": item["authority_id"], "source": item["source"]}
            for item in value("authorities")
            if isinstance(item, dict)
        ]
    return summary


def _schema() -> dict[str, Any]:
    return load_manifest_json(SCHEMA_FILE)


def _argument_issues(event: dict[str, Any]) -> list[str]:
    """Each token is a literal, or a hash with an optional literal prefix."""
    payload = event.get("payload")
    tokens = payload.get("arguments") if isinstance(payload, dict) else None
    issues = []
    for index, token in enumerate(tokens if isinstance(tokens, list) else []):
        keys = set(token) if isinstance(token, dict) else set()
        if keys not in (
            {"value"},
            {"sha256", "length"},
            {"prefix", "sha256", "length"},
        ):
            issues.append(f"payload.arguments[{index}]: not a literal or a hash")
    return issues


def event_issues(event: dict[str, Any]) -> list[str]:
    schema_issues = [
        f"{issue.fact}: {issue.reason}"
        for issue in _schema_issues(event, _schema(), path="", source=SCHEMA_FILE.name)
    ]
    return schema_issues + _argument_issues(event)


def append_event(directory: Path, event: dict[str, Any]) -> Path:
    """Validate and append one event to the day's append-only file."""
    problems = event_issues(event)
    if problems:
        raise TelemetryError("; ".join(problems))
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    day = str(event["observed_at"])[:10]
    path = directory / f"events-{day}.jsonl"
    line = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(descriptor, line)
    finally:
        os.close(descriptor)
    return path


def iter_events(directory: Path) -> Iterator[dict[str, Any]]:
    """Every stored event, oldest file first, in the order it was written."""
    if not directory.is_dir():
        return
    for path in sorted(directory.glob("events-*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def record(settings: TelemetrySettings, event_factory) -> Path | None:
    """Record one event if enabled; report, never raise, when that fails."""
    if not settings.enabled or settings.directory is None:
        return None
    try:
        return append_event(settings.directory, event_factory())
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"gov: telemetry not recorded: {exc}", file=sys.stderr)
        return None


__all__ = [
    "CONTEXT_VARIABLE",
    "SCHEMA_VERSION",
    "TelemetryError",
    "TelemetrySettings",
    "append_event",
    "build_command_execution",
    "checkout_identity",
    "event_issues",
    "governance_enrichment",
    "iter_events",
    "producer_version",
    "record",
    "recorded_arguments",
    "resolution_summary",
    "resolve_settings",
    "run_context",
    "store_directory",
]
