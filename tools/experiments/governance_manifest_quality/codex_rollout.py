from __future__ import annotations

import hashlib
import json
import re
import shlex
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache
from pathlib import Path, PurePosixPath
from typing import Any

from .measurement import TrajectoryValidationError, normalize_trajectory

_JS_CMD = re.compile(r"\bcmd\s*:\s*(\"(?:\\.|[^\"\\])*\")")
_PATCH_PATH = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.MULTILINE)
_SED_RANGE = re.compile(r"^(\d+)(?:,(\d+))?p$")
_EXIT_CODE = re.compile(r"(?:Process exited with code|exit_code[\"']?\s*:)\s*(\d+)")
_SHELL_SPLIT = re.compile(r"\s*(?:&&|;)\s*")
_SEARCH_TOOLS = {"rg", "grep"}
_OTHER_MATERIALIZING_TOOLS = {"find", "ls"}


@dataclass(frozen=True)
class RejectedTrajectory:
    source_id: str
    status: str
    reason: str


class RolloutFormatError(ValueError):
    """A rollout is malformed or unsupported."""


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@cache
def _git_revision_exists(root: Path, revision: str) -> bool:
    if not re.fullmatch(r"[0-9a-fA-F]{7,64}", revision):
        return False
    return (
        subprocess.run(
            ["git", "cat-file", "-e", f"{revision}^{{commit}}"],
            cwd=root,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _flatten_output(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts) if parts else None
    return None


def _commands(name: object, arguments: object) -> list[str]:
    if not isinstance(name, str):
        return []
    if name in {"exec_command", "shell_command"} and isinstance(arguments, str):
        try:
            decoded = json.loads(arguments)
        except json.JSONDecodeError:
            return []
        command = decoded.get("cmd") if isinstance(decoded, dict) else None
        return [command] if isinstance(command, str) else []
    if name == "exec" and isinstance(arguments, str):
        commands = []
        for match in _JS_CMD.finditer(arguments):
            try:
                command = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            if isinstance(command, str):
                commands.append(command)
        return commands
    return []


def _repo_path(raw: str, repository_root: Path) -> str | None:
    candidate = raw.strip().strip("'\"")
    if not candidate or candidate == "-":
        return None
    path = Path(candidate)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(repository_root.resolve())
        except ValueError:
            return None
    posix = PurePosixPath(path.as_posix())
    if ".." in posix.parts or posix.as_posix() in {".", ""}:
        return None
    return posix.as_posix()


def classify_repository_path(
    path: str, active_files: set[str]
) -> tuple[str, str | None]:
    if path in active_files:
        return "governance", "active_governance"
    governance_roots = (
        ".governance/",
        "config/governance/",
        "config/project/policy_pack.json",
        "docs/governance/",
        "tools/governance/",
        "tools/workspace_governance/",
    )
    if any(
        path == root.rstrip("/") or path.startswith(root) for root in governance_roots
    ):
        return "governance", "governance_mechanism"
    return "non_governance", None


@cache
def _git_file_bytes(root: Path, revision: str | None, path: str) -> bytes | None:
    if revision is None or not re.fullmatch(r"[0-9a-fA-F]{7,64}", revision):
        return None
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


@cache
def _git_path_exists(root: Path, revision: str | None, path: str) -> bool:
    if revision is None or not re.fullmatch(r"[0-9a-fA-F]{7,64}", revision):
        return False
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{revision}:{path}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _repository_path_exists(root: Path, revision: str | None, path: str) -> bool:
    return (root / path).exists() or _git_path_exists(root, revision, path)


def _line_range(content: bytes, start_line: int, end_line: int) -> tuple[int, int]:
    lines = content.splitlines(keepends=True)
    start_index = min(max(start_line - 1, 0), len(lines))
    end_index = min(max(end_line, 0), len(lines))
    start = sum(len(line) for line in lines[:start_index])
    end = sum(len(line) for line in lines[:end_index])
    return start, end


def _read_spec(  # noqa: C901 - recognizes the bounded supported shell-read grammar
    command: str, repository_root: Path
) -> tuple[str, str, int | None, int | None] | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    if not tokens:
        return None
    executable = Path(tokens[0]).name
    if executable == "cat" and len(tokens) == 2:
        path = _repo_path(tokens[1], repository_root)
        return (path, "whole_file", None, None) if path else None
    if executable == "sed" and len(tokens) >= 4 and tokens[1] == "-n":
        match = _SED_RANGE.fullmatch(tokens[2])
        path = _repo_path(tokens[-1], repository_root)
        if match and path:
            start = int(match.group(1))
            end = int(match.group(2) or match.group(1))
            return path, "bounded", start, end
    if executable == "head" and len(tokens) >= 3:
        path = _repo_path(tokens[-1], repository_root)
        count = None
        for index, token in enumerate(tokens[:-1]):
            if token in {"-n", "--lines"} and index + 1 < len(tokens):
                try:
                    count = int(tokens[index + 1])
                except ValueError:
                    pass
        if path and count is not None and count >= 0:
            return path, "bounded", 1, count
    return None


def _retrieval_events(
    commands: list[str],
    repository_root: Path,
    revision: str | None,
    active_files: set[str],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    shell_commands = [
        part for command in commands for part in _SHELL_SPLIT.split(command) if part
    ]
    for command in shell_commands:
        spec = _read_spec(command, repository_root)
        if spec is None:
            continue
        path, access_mode, start_line, end_line = spec
        content = _git_file_bytes(repository_root, revision, path)
        byte_range = None
        materialized = None
        content_identity = None
        if content is not None:
            content_identity = f"git:{revision}:{hashlib.sha256(content).hexdigest()}"
            if access_mode == "whole_file":
                byte_range = {"start": 0, "end": len(content)}
            elif start_line is not None and end_line is not None:
                start, end = _line_range(content, start_line, end_line)
                byte_range = {"start": start, "end": end}
            if byte_range is not None:
                materialized = byte_range["end"] - byte_range["start"]
        source_class, governance_kind = classify_repository_path(path, active_files)
        events.append(
            {
                "event_type": "retrieval",
                "path": path,
                "source_class": source_class,
                "governance_kind": governance_kind,
                "access_mode": access_mode,
                "materialized_bytes": materialized,
                "byte_range": byte_range,
                "content_identity": content_identity,
                "route": None,
                "authority": None,
                "evidence": "shell_read_command",
            }
        )
    return events


def _search_retrieval_events(
    commands: list[str],
    repository_root: Path,
    revision: str | None,
    active_files: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    limitations: list[dict[str, Any]] = []
    shell_commands = [
        part for command in commands for part in _SHELL_SPLIT.split(command) if part
    ]
    for command in shell_commands:
        try:
            tokens = shlex.split(command)
        except ValueError:
            continue
        if not tokens:
            continue
        executable = Path(tokens[0]).name
        if executable in _SEARCH_TOOLS:
            for token in tokens[1:]:
                if token.startswith("-"):
                    continue
                path = _repo_path(token, repository_root)
                if path is None or not _repository_path_exists(
                    repository_root, revision, path
                ):
                    continue
                source_class, governance_kind = classify_repository_path(
                    path, active_files
                )
                events.append(
                    {
                        "event_type": "retrieval",
                        "path": path,
                        "source_class": source_class,
                        "governance_kind": governance_kind,
                        "access_mode": "bounded",
                        "materialized_bytes": None,
                        "byte_range": None,
                        "content_identity": None,
                        "route": None,
                        "authority": None,
                        "evidence": "search_scope_without_byte_ranges",
                    }
                )
            limitations.append(
                {"kind": "search_materialization_unresolved", "event_sequence": None}
            )
        elif executable in _OTHER_MATERIALIZING_TOOLS or (
            executable == "git" and len(tokens) > 1 and tokens[1] in {"diff", "show"}
        ):
            limitations.append(
                {"kind": "command_materialization_unresolved", "event_sequence": None}
            )
    return events, limitations


def _mutation_events(
    tool_input: str,
    repository_root: Path,
    active_files: set[str],
) -> list[dict[str, Any]]:
    events = []
    patch_text = tool_input.replace("\\r\\n", "\n").replace("\\n", "\n")
    matches = list(_PATCH_PATH.finditer(patch_text))
    for index, match in enumerate(matches):
        path = _repo_path(match.group(1), repository_root)
        if path is None:
            continue
        source_class, governance_kind = classify_repository_path(path, active_files)
        marker = match.group(0)
        operation = "edit"
        if marker.startswith("*** Add"):
            operation = "create"
        elif marker.startswith("*** Delete"):
            operation = "delete"
        section_end = (
            matches[index + 1].start() if index + 1 < len(matches) else len(patch_text)
        )
        section_lines = patch_text[match.end() : section_end].splitlines()
        added_lines = [
            line
            for line in section_lines
            if line.startswith("+") and not line.startswith("+++")
        ]
        deleted_lines = [
            line
            for line in section_lines
            if line.startswith("-") and not line.startswith("---")
        ]
        bytes_changed = sum(
            len(line[1:].encode("utf-8")) + 1 for line in added_lines + deleted_lines
        )
        events.append(
            {
                "event_type": "mutation",
                "path": path,
                "source_class": source_class,
                "governance_kind": governance_kind,
                "operation": operation,
                "bytes_changed": bytes_changed,
                "lines_added": len(added_lines),
                "lines_deleted": len(deleted_lines),
                "generated_file": None,
                "intentional": True,
                "evidence": "apply_patch_target",
            }
        )
    return events


def _execution_event(
    name: str | None,
    commands: list[str],
    output: str | None,
) -> dict[str, Any]:
    joined = "\n".join(commands)
    lowered = joined.lower()
    exit_match = _EXIT_CODE.search(output or "")
    exit_code = int(exit_match.group(1)) if exit_match else None
    is_search = any(token in lowered for token in ("rg ", "grep ", "find "))
    is_test = any(
        token in lowered
        for token in ("pytest", "verify.sh", "verify_focus.sh", "ctest")
    )
    command_kind = None
    if is_test:
        command_kind = "test"
    elif is_search:
        command_kind = "search"
    elif commands:
        command_kind = "shell"
    return {
        "event_type": "execution",
        "tool": name,
        "command_kind": command_kind,
        "is_search": is_search if commands else None,
        "is_test": is_test if commands else None,
        "exit_code": exit_code,
        "duration_ms": None,
        "repeated_failure": None,
        "command_identity": _text_sha256(joined) if joined else None,
    }


def _active_files(policy: dict[str, Any]) -> set[str]:
    groups = policy["governance_surface"]["active_governance"]
    return {str(path) for paths in groups.values() for path in paths}


def _matching_repository(cwd: object, repository_root: Path) -> bool:
    return isinstance(cwd, str) and Path(cwd).resolve() == repository_root.resolve()


def _task_identity(payload: dict[str, Any]) -> str | None:
    if payload.get("role") != "user":
        return None
    content = payload.get("content")
    if not isinstance(content, list):
        return None
    text = "".join(
        item.get("text", "")
        for item in content
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    )
    return _text_sha256(text) if text else None


def _repository_context(
    rows: list[dict[str, Any]], repository_root: Path
) -> tuple[bool, bool, str | None, object]:
    """Resolve repository provenance before reconstructing expensive tool events."""
    matching = False
    saw_repository_provenance = False
    revision = None
    started_at = None
    for row in rows:
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        row_type = row.get("type")
        if row_type == "session_meta":
            cwd = payload.get("cwd")
            saw_repository_provenance = saw_repository_provenance or isinstance(
                cwd, str
            )
            matching = matching or _matching_repository(cwd, repository_root)
            started_at = started_at or payload.get("timestamp")
            git = payload.get("git")
            if isinstance(git, dict) and isinstance(git.get("commit_hash"), str):
                revision = git["commit_hash"]
                saw_repository_provenance = True
                matching = matching or _git_revision_exists(repository_root, revision)
        elif row_type == "turn_context":
            cwd = payload.get("cwd")
            saw_repository_provenance = saw_repository_provenance or isinstance(
                cwd, str
            )
            matching = matching or _matching_repository(cwd, repository_root)
    return matching, saw_repository_provenance, revision, started_at


def adapt_rollout(  # noqa: C901 - one pass preserves ordering across rollout variants
    path: Path,
    repository_root: Path,
    policy: dict[str, Any],
) -> dict[str, Any] | RejectedTrajectory:
    source_id = _file_sha256(path)
    active_files = _active_files(policy)
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    return RejectedTrajectory(
                        source_id,
                        "rejected_during_ingestion",
                        f"malformed_json_line:{line_number}:{exc.msg}",
                    )
                if not isinstance(row, dict):
                    return RejectedTrajectory(
                        source_id, "rejected_during_ingestion", "non_object_jsonl_row"
                    )
                rows.append(row)
    except OSError as exc:
        return RejectedTrajectory(
            source_id,
            "rejected_during_ingestion",
            f"source_read_error:{type(exc).__name__}",
        )
    if not rows:
        return RejectedTrajectory(
            source_id, "rejected_during_ingestion", "empty_trajectory"
        )

    matching, saw_repository_provenance, revision, started_at = _repository_context(
        rows, repository_root
    )
    if not matching:
        status = (
            "excluded" if saw_repository_provenance else "missing_required_provenance"
        )
        reason = (
            "different_repository"
            if saw_repository_provenance
            else "repository_identity_unavailable"
        )
        return RejectedTrajectory(source_id, status, reason)

    saw_supported_envelope = False
    model = None
    task_identity = None
    token_information = None
    elapsed_ms = 0
    elapsed_recorded = False
    source_format = "codex_rollout_legacy"
    pending: dict[str, tuple[str | None, str, list[str]]] = {}
    events: list[dict[str, Any]] = []
    limitations: list[dict[str, Any]] = []
    failed_identities: set[str] = set()

    for row in rows:
        row_type = row.get("type")
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        if row_type == "session_meta":
            continue
        elif row_type == "turn_context":
            if isinstance(payload.get("model"), str):
                model = payload["model"]
        elif row_type == "event_msg" and payload.get("type") == "token_count":
            info = payload.get("info")
            if isinstance(info, dict) and isinstance(
                info.get("total_token_usage"), dict
            ):
                token_information = {
                    "total_token_usage": info["total_token_usage"],
                    "model_context_window": info.get("model_context_window"),
                }
        elif row_type == "event_msg" and payload.get("type") == "task_complete":
            duration = payload.get("duration_ms")
            if (
                isinstance(duration, int)
                and not isinstance(duration, bool)
                and duration >= 0
            ):
                elapsed_ms += duration
                elapsed_recorded = True
        if row_type != "response_item":
            continue
        message_identity = _task_identity(payload)
        task_identity = task_identity or message_identity
        item_type = payload.get("type")
        if item_type in {
            "message",
            "reasoning",
            "compaction",
            "function_call",
            "function_call_output",
            "custom_tool_call",
            "custom_tool_call_output",
        }:
            saw_supported_envelope = True
        if item_type in {"function_call", "custom_tool_call"}:
            if item_type == "custom_tool_call":
                source_format = "codex_rollout_custom_tool"
            call_id = payload.get("call_id")
            name = payload.get("name")
            raw_input = payload.get("arguments", payload.get("input"))
            if not isinstance(call_id, str) or not isinstance(raw_input, str):
                continue
            commands = _commands(name, raw_input)
            pending[call_id] = (
                name if isinstance(name, str) else None,
                raw_input,
                commands,
            )
        elif item_type in {"function_call_output", "custom_tool_call_output"}:
            call_id = payload.get("call_id")
            if not isinstance(call_id, str) or call_id not in pending:
                continue
            name, raw_input, commands = pending.pop(call_id)
            output = _flatten_output(payload.get("output"))
            execution = _execution_event(name, commands, output)
            identity = execution["command_identity"]
            if (
                execution["exit_code"] not in {None, 0}
                and identity in failed_identities
            ):
                execution["repeated_failure"] = True
            elif execution["exit_code"] not in {None, 0} and identity is not None:
                execution["repeated_failure"] = False
                failed_identities.add(identity)
            events.append(execution)
            events.extend(
                _retrieval_events(commands, repository_root, revision, active_files)
            )
            search_events, search_limitations = _search_retrieval_events(
                commands, repository_root, revision, active_files
            )
            events.extend(search_events)
            limitations.extend(search_limitations)
            events.extend(_mutation_events(raw_input, repository_root, active_files))

    if not saw_supported_envelope:
        return RejectedTrajectory(
            source_id, "unsupported_format", "no_supported_response_envelope"
        )
    if pending:
        return RejectedTrajectory(
            source_id, "excluded_after_normalization", "incomplete_tool_calls"
        )
    payload = {
        "schema_version": 1,
        "source": {
            "source_id": source_id,
            "source_format": source_format,
            "repository_revision": revision,
            "task_identity": task_identity,
            "model": model,
            "token_information": token_information,
            "started_at": started_at,
            "elapsed_ms": elapsed_ms if elapsed_recorded else None,
        },
        "events": events,
        "outcome_evidence": None,
        "evidence_limitations": limitations,
    }
    try:
        return normalize_trajectory(payload)
    except (TrajectoryValidationError, KeyError, TypeError) as exc:
        return RejectedTrajectory(
            source_id,
            "excluded_after_normalization",
            f"normalization_error:{type(exc).__name__}",
        )


def discover_rollouts(source_roots: Iterable[Path]) -> list[Path]:
    paths = {
        path.resolve()
        for root in source_roots
        if root.exists()
        for path in (root.rglob("*.jsonl") if root.is_dir() else [root])
        if path.is_file()
    }
    return sorted(paths)
