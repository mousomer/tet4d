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

import contextlib
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import sys
import tempfile
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
CONTEXT_FIELDS = ("session_id", "task_id", "agent", "model")
KEY_FILENAME = "telemetry-key-v1"
KEY_BYTES = 32
GOV_ARGV_NORMALIZATION = "gov-argv-1"
WORKSPACE_PATH_NORMALIZATION = "workspace-path-1"
GOVERNANCE_DIAGNOSTIC_FACT_NORMALIZATION = "governance-diagnostic-fact-1"

_GOV_COMMANDS = frozenset({"check", "resolve", "explain", "doctor", "sync", "env"})
_GOV_BOOLEAN_OPTIONS = frozenset(
    {"--json", "--print-interpreter", "--allow-missing-interpreter"}
)
_GOV_PRIVATE_VALUE_OPTIONS = frozenset({"--root", "--task", "--route"})
_GOV_EXECUTION_MODES = frozenset({"LOCAL_FIX", "FEATURE", "STRUCTURAL_CHANGE"})


class TelemetryError(ValueError):
    """An event cannot be recorded as a valid telemetry fact."""


@dataclass(frozen=True)
class TelemetryKey:
    """A local secret and its non-secret rotation-detection identifier."""

    secret: bytes
    key_id: str


@dataclass(frozen=True)
class TelemetrySettings:
    enabled: bool
    workspace_id: str | None
    directory: Path | None

    @property
    def key_directory(self) -> Path | None:
        """Where the telemetry key lives: beside the events, never among them.

        Copying or pruning the event files must not carry the key along;
        with the key, every keyed identity in a copy could be tested against
        guesses.
        """
        return self.directory.parent if self.directory is not None else None

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


def _publish_key(key_path: Path) -> None:
    """Create the key whole or not at all.

    The secret is written and synced to a private staging file, then
    hard-linked into place. Linking fails if another process published first,
    and this one then uses that key. A reader therefore never sees a partial
    key, and an interrupted creation never leaves one behind.
    """
    descriptor, staged = tempfile.mkstemp(
        prefix=f".{KEY_FILENAME}.", dir=key_path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(secrets.token_bytes(KEY_BYTES))
            handle.flush()
            os.fsync(handle.fileno())
        with contextlib.suppress(FileExistsError):
            os.link(staged, key_path)
    finally:
        os.unlink(staged)


def telemetry_key(directory: Path) -> TelemetryKey:
    """Load or securely create the private telemetry key kept in `directory`.

    For a workspace store that is `TelemetrySettings.key_directory`, beside the
    append-only observations and never in a checkout. The identifier lets a
    reader detect rotation or deletion without exposing the secret or treating
    records made under a new key as comparable.
    """
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    key_path = directory / KEY_FILENAME
    if not key_path.exists():
        _publish_key(key_path)
    # Ensure an old key cannot become group- or world-readable.
    os.chmod(key_path, 0o600)
    secret = key_path.read_bytes()
    if len(secret) != KEY_BYTES:
        raise TelemetryError("telemetry key has an invalid length")
    key_id = hmac.new(
        secret,
        b"workspace-governance telemetry key identifier v1",
        hashlib.sha256,
    ).hexdigest()
    return TelemetryKey(secret=secret, key_id=key_id)


def private_identity(
    value: str,
    key: TelemetryKey,
    *,
    normalization: str,
    include_length: bool = False,
) -> dict[str, object]:
    """A key-scoped correlatable identity for a privacy-sensitive value."""
    identity: dict[str, object] = {
        "hmac_sha256": hmac.new(
            key.secret, value.encode("utf-8"), hashlib.sha256
        ).hexdigest(),
        "key_id": key.key_id,
        "normalization": normalization,
    }
    if include_length:
        identity["length"] = len(value)
    return identity


def _gov_value_token(option: str, value: str, key: TelemetryKey) -> dict[str, object]:
    if option == "--mode" and value in _GOV_EXECUTION_MODES:
        return {"value": value}
    return private_identity(
        value, key, normalization=GOV_ARGV_NORMALIZATION, include_length=True
    )


def _gov_option_token(
    token: str, key: TelemetryKey
) -> tuple[dict[str, object], str | None] | None:
    """Return a classified `gov` option and its pending value option, if any."""
    if token in _GOV_BOOLEAN_OPTIONS:
        return {"value": token}, None
    option, separator, value = token.partition("=")
    if option in _GOV_PRIVATE_VALUE_OPTIONS:
        if separator:
            return {
                "prefix": option + separator,
                **_gov_value_token(option, value, key),
            }, None
        return {"value": token}, option
    if option == "--mode":
        if separator:
            value_token = _gov_value_token(option, value, key)
            if value_token == {"value": value}:
                return {"value": token}, None
            return {"prefix": option + separator, **value_token}, None
        return {"value": token}, option
    return None


def recorded_gov_arguments(
    argv: list[str], key: TelemetryKey
) -> list[dict[str, object]]:
    """Classify the owned `gov` grammar without retaining free-form values.

    This deliberately is not a shell parser. Only fixed command names, option
    names, execution-mode values, and boolean switches are literals. Every
    positional value, free-form option value, and machine path is an HMAC
    identity using the explicitly versioned `gov-argv-1` normalization.
    """
    tokens: list[dict[str, object]] = []
    command: str | None = None
    value_for: str | None = None

    def private(value: str) -> dict[str, object]:
        return _gov_value_token("", value, key)

    for token in argv:
        if value_for is not None:
            tokens.append(_gov_value_token(value_for, token, key))
            value_for = None
            continue
        option_token = _gov_option_token(token, key)
        if option_token is not None:
            classified, value_for = option_token
            tokens.append(classified)
        elif command is None and token in _GOV_COMMANDS:
            command = token
            tokens.append({"value": token})
        else:
            tokens.append(private(token))
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


def checkout_identity(root: Path, key: TelemetryKey) -> dict[str, object]:
    """Which checkout acted, without recording where it lives on this machine."""
    identity: dict[str, object] = {
        "path": private_identity(
            str(root.resolve()), key, normalization=WORKSPACE_PATH_NORMALIZATION
        )
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
    key: TelemetryKey,
    resolution: dict[str, Any] | None = None,
) -> dict[str, object]:
    """What only a first-hand `gov` observer knows about its own execution."""
    enrichment: dict[str, object] = {
        "subcommand": subcommand,
        "diagnostics": [
            {
                "code": str(item.get("code")),
                "fact": private_identity(
                    str(item.get("fact")),
                    key,
                    normalization=GOVERNANCE_DIAGNOSTIC_FACT_NORMALIZATION,
                    include_length=True,
                ),
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
    key: TelemetryKey,
    exit_status: int | None = None,
    duration_ms: int | None = None,
    observed_at: str | None = None,
    recorded_at: str | None = None,
    governance: dict[str, object] | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, object]:
    """A first-hand observation of a command this process executed.

    A completion's `observed_at` is when the command finished; it started
    `duration_ms` earlier. Both default to now, which is when `gov` records it.

    Process IDs are only local, ephemeral supplementary evidence. They can
    support a later correlation conclusion, but are not a cross-source
    invocation identity and never replace source_ref, evidence_ref, or this
    observation's own identity.
    """
    program_identity = Path(program).name
    if not program_identity:
        raise TelemetryError("program must have a basename or logical name")
    payload: dict[str, object] = {
        "program": program_identity,
        "arguments": arguments,
        "phase": "completion",
        "invocation": {
            "process_id": os.getpid(),
            "parent_process_id": os.getppid(),
        },
    }
    if exit_status is not None:
        payload["exit_status"] = exit_status
    if duration_ms is not None:
        payload["duration_ms"] = max(0, duration_ms)
    if governance is not None:
        payload["governance"] = governance
    observed = observed_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    event: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "observation_id": uuid.uuid4().hex,
        "event_type": "command_execution",
        "observed_at": observed,
        "recorded_at": recorded_at
        or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "workspace_id": workspace_id,
        "checkout": checkout_identity(root, key),
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
    """Each token is a safe literal or a keyed private identity."""
    payload = event.get("payload")
    tokens = payload.get("arguments") if isinstance(payload, dict) else None
    issues = []
    for index, token in enumerate(tokens if isinstance(tokens, list) else []):
        keys = set(token) if isinstance(token, dict) else set()
        private = {"hmac_sha256", "key_id", "normalization"}
        if keys not in (
            {"value"},
            private,
            private | {"length"},
            private | {"prefix"},
            private | {"prefix", "length"},
        ):
            issues.append(
                f"payload.arguments[{index}]: not a literal or keyed private identity"
            )
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
    day = str(event["recorded_at"])[:10]
    path = directory / f"events-{day}.jsonl"
    line = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(descriptor, line)
    finally:
        os.close(descriptor)
    return path


def iter_events(directory: Path) -> Iterator[dict[str, Any]]:
    """Every stored event, oldest file first, in the order it was written.

    A record in a schema version this reader does not support is refused, not
    read as if it were v1. Unknown event types within v1 are yielded; callers
    skip the types they do not interpret.
    """
    if not directory.is_dir():
        return
    for path in sorted(directory.glob("events-*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                event = json.loads(line)
                version = (
                    event.get("schema_version") if isinstance(event, dict) else None
                )
                if version != SCHEMA_VERSION:
                    raise TelemetryError(
                        f"{path.name}:{number}: unsupported telemetry "
                        f"schema_version {version!r}"
                    )
                yield event


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
    "GOVERNANCE_DIAGNOSTIC_FACT_NORMALIZATION",
    "SCHEMA_VERSION",
    "TelemetryError",
    "TelemetryKey",
    "TelemetrySettings",
    "append_event",
    "build_command_execution",
    "checkout_identity",
    "event_issues",
    "governance_enrichment",
    "iter_events",
    "private_identity",
    "producer_version",
    "record",
    "recorded_gov_arguments",
    "resolution_summary",
    "resolve_settings",
    "run_context",
    "store_directory",
    "telemetry_key",
]
