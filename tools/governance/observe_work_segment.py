from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.workspace_governance.resolver.core import GovernanceResolver
from tools.workspace_governance.resolver.roles import (
    COMPATIBILITY_RESULTS,
    ROLE_PROVENANCE,
    WORK_TYPES,
    WORKSPACE_MANIFEST,
    WRITE_COMPATIBILITY,
    RoleDeclarationError,
    RoleIndex,
    compatibility,
    normalize_repo_path,
    validate_compatibility_table,
)
from tools.workspace_governance.validators.core import load_manifest_json, pack_hash

SCHEMA_VERSION = 2


class ObservationError(ValueError):
    """Raised when an observation request or its local evidence is invalid."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ObservationError(f"missing required JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ObservationError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ObservationError(f"expected an object in {path}")
    return value


def _git(root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ObservationError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout


def _head(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD").decode("ascii").strip()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _parse_time(value: str, *, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ObservationError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ObservationError(f"{field} must include a timezone")
    return parsed


def validate_work_type(work_type: str) -> str:
    if work_type not in WORK_TYPES:
        raise ObservationError(
            f"work_type must be exactly one of: {', '.join(WORK_TYPES)}"
        )
    return work_type


def _file_state(path: Path) -> dict[str, object] | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None
    mode = stat.S_IMODE(metadata.st_mode)
    if stat.S_ISLNK(metadata.st_mode):
        payload = os.fsencode(os.readlink(path))
        kind = "symlink"
    elif stat.S_ISREG(metadata.st_mode):
        payload = path.read_bytes()
        kind = "file"
    elif stat.S_ISDIR(metadata.st_mode):
        # A tracked directory can only be a gitlink. The index entry is the
        # evidence; ordinary directories are represented by their files.
        payload = b"gitlink"
        kind = "gitlink"
    else:
        return None
    digest = hashlib.sha256(kind.encode("ascii") + b"\0" + payload).hexdigest()
    return {"sha256": digest, "kind": kind, "mode": mode, "size": len(payload)}


def repository_snapshot(root: Path) -> dict[str, dict[str, object]]:
    root = root.resolve()
    raw_paths = _git(
        root,
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
    )
    snapshot: dict[str, dict[str, object]] = {}
    for raw_path in raw_paths.split(b"\0"):
        if not raw_path:
            continue
        relative = os.fsdecode(raw_path)
        normalized = normalize_repo_path(relative)
        state = _file_state(root / relative)
        if state is not None:
            snapshot[normalized] = state
    return dict(sorted(snapshot.items()))


def classify_changes(
    before: dict[str, dict[str, object]],
    after: dict[str, dict[str, object]],
) -> list[dict[str, str]]:
    """List every written path; a rename writes both of its paths.

    A rename is reported from both ends so the path it vacates is judged by
    its own role: moving an instruction file away removes it from the
    governance surface even though its content survives elsewhere.
    """
    before_paths = set(before)
    after_paths = set(after)
    deleted = before_paths - after_paths
    created = after_paths - before_paths
    changes: list[dict[str, str]] = []

    deleted_by_state: dict[str, list[str]] = {}
    created_by_state: dict[str, list[str]] = {}
    for path in deleted:
        deleted_by_state.setdefault(
            json.dumps(before[path], sort_keys=True), []
        ).append(path)
    for path in created:
        created_by_state.setdefault(json.dumps(after[path], sort_keys=True), []).append(
            path
        )

    renamed_from: set[str] = set()
    renamed_to: set[str] = set()
    for signature in sorted(set(deleted_by_state) & set(created_by_state)):
        old_paths = deleted_by_state[signature]
        new_paths = created_by_state[signature]
        if len(old_paths) == 1 and len(new_paths) == 1:
            old_path, new_path = old_paths[0], new_paths[0]
            renamed_from.add(old_path)
            renamed_to.add(new_path)
            changes.append(
                {
                    "path": new_path,
                    "change_kind": "renamed",
                    "previous_path": old_path,
                }
            )
            changes.append(
                {"path": old_path, "change_kind": "renamed_away", "next_path": new_path}
            )

    for path in sorted(deleted - renamed_from):
        changes.append({"path": path, "change_kind": "deleted"})
    for path in sorted(created - renamed_to):
        changes.append({"path": path, "change_kind": "created"})
    for path in sorted(before_paths & after_paths):
        if before[path] != after[path]:
            changes.append({"path": path, "change_kind": "modified"})
    return sorted(changes, key=lambda item: (item["path"], item["change_kind"]))


def _pack_identity(root: Path) -> dict[str, str]:
    workspace = _load_json(root / WORKSPACE_MANIFEST)
    lock = _load_json(root / workspace["governance_pack"]["lock"])
    pack_root = root / lock["pack_path"]
    manifest = load_manifest_json(pack_root / "MANIFEST.json")
    return {
        "version": str(manifest["version"]),
        "revision": str(manifest["revision"]),
        "content_sha256": pack_hash(pack_root)[0],
    }


def capture_treatment(root: Path) -> dict[str, object]:
    """Capture the roles and table this checkout's treatment judges writes by."""
    try:
        return {
            "pack": _pack_identity(root),
            "role_index": GovernanceResolver.for_root(root).role_index().to_dict(),
            "write_compatibility": WRITE_COMPATIBILITY,
        }
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise ObservationError(f"treatment cannot be resolved: {exc}") from exc


def _atomic_json_write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        Path(temporary).replace(path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def start_segment(
    root: Path,
    *,
    state_path: Path,
    segment_id: str,
    work_type: str,
    started_at: str | None = None,
    task_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, object]:
    if not segment_id.strip():
        raise ObservationError("segment_id must be non-empty")
    validate_work_type(work_type)
    root = root.resolve()
    observed_at = started_at or _utc_now()
    _parse_time(observed_at, field="started_at")
    segment = {
        "segment_id": segment_id,
        "work_type": work_type,
        "task_id": task_id,
        "session_id": session_id,
    }
    boundary = {"head": _head(root), "observed_at": observed_at}
    base = capture_treatment(root)
    state: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "segment": segment,
        "start_boundary": boundary,
        "start_snapshot": repository_snapshot(root),
        "base_treatment": base,
    }
    _atomic_json_write(state_path, state)
    return {
        "schema_version": SCHEMA_VERSION,
        "observer_mode": "log_only",
        "authoritative": False,
        "segment": segment,
        "start_boundary": boundary,
        "base_pack": base["pack"],
        "state_path": str(state_path),
    }


def _base_treatment(state: dict[str, Any]) -> tuple[RoleIndex, dict, dict]:
    base = state.get("base_treatment")
    if not isinstance(base, dict):
        raise ObservationError("observer state lacks its base treatment")
    try:
        return (
            RoleIndex.from_dict(base.get("role_index")),
            validate_compatibility_table(base.get("write_compatibility")),
            dict(base.get("pack") or {}),
        )
    except RoleDeclarationError as exc:
        raise ObservationError(f"observer base treatment is invalid: {exc}") from exc


def _candidate_treatment(root: Path) -> tuple[RoleIndex | None, dict[str, object]]:
    """The treatment on disk at the end, or why it could not be resolved.

    A segment may leave the governance documents broken. Its writes are still
    judged by the base treatment, so an unresolvable candidate is recorded
    rather than failing the observation.
    """
    try:
        candidate = capture_treatment(root)
    except ObservationError as exc:
        return None, {"state": "unavailable", "pack": None, "reason": str(exc)}
    index = RoleIndex.from_dict(candidate["role_index"])
    return index, {"state": "resolved", "pack": candidate["pack"], "reason": None}


def _judge(
    change: dict[str, str],
    work_type: str,
    base: RoleIndex,
    table: dict[str, dict[str, str]],
    candidate: RoleIndex | None,
) -> dict[str, object]:
    path = change["path"]
    resolution = base.resolve(path)
    result, condition = compatibility(work_type, resolution.role, table)
    artifact: dict[str, object] = {
        **change,
        **resolution.to_dict(),
        "compatibility": result,
        "condition": condition,
        "bootstrap_root": base.is_root(path)
        or (candidate is not None and candidate.is_root(path)),
        "candidate_role": None,
        "candidate_role_provenance": None,
        "candidate_role_source": None,
        "role_changed": None,
    }
    if candidate is not None:
        moved = candidate.resolve(path)
        artifact.update(
            candidate_role=moved.role,
            candidate_role_provenance=moved.provenance,
            candidate_role_source=moved.source,
            role_changed=moved.role != resolution.role,
        )
    return artifact


def finish_segment(
    state_path: Path,
    *,
    ended_at: str | None = None,
    tool_call_count: int = 0,
    failures: int = 0,
    retries: int = 0,
    outcome: str | None = None,
) -> dict[str, object]:
    state = _load_json(state_path)
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ObservationError("unsupported observer state schema")
    root_value = state.get("root")
    segment = state.get("segment")
    start_boundary = state.get("start_boundary")
    start_snapshot = state.get("start_snapshot")
    if not isinstance(root_value, str) or not isinstance(segment, dict):
        raise ObservationError("observer state is incomplete")
    if not isinstance(start_boundary, dict) or not isinstance(start_snapshot, dict):
        raise ObservationError("observer state lacks its start evidence")
    for field, value in {
        "tool_call_count": tool_call_count,
        "failures": failures,
        "retries": retries,
    }.items():
        if value < 0:
            raise ObservationError(f"{field} must be non-negative")

    work_type = validate_work_type(str(segment.get("work_type")))
    base_index, table, base_pack = _base_treatment(state)
    root = Path(root_value).resolve()
    observed_at = ended_at or _utc_now()
    end_time = _parse_time(observed_at, field="ended_at")
    start_time = _parse_time(str(start_boundary.get("observed_at")), field="started_at")
    elapsed = (end_time - start_time).total_seconds()
    if elapsed < 0:
        raise ObservationError("ended_at must not precede started_at")

    end_boundary = {"head": _head(root), "observed_at": observed_at}
    changes = classify_changes(start_snapshot, repository_snapshot(root))
    candidate_index, candidate = _candidate_treatment(root)
    artifacts = [
        _judge(change, work_type, base_index, table, candidate_index)
        for change in changes
    ]

    compatibility_counts = Counter(str(item["compatibility"]) for item in artifacts)
    provenance_counts = Counter(str(item["role_provenance"]) for item in artifacts)
    telemetry: dict[str, object] = {
        "segment_count": 1,
        "files_written": len(artifacts),
        "elapsed_seconds": round(elapsed, 6),
        "tool_call_count": tool_call_count,
        "failures": failures,
        "retries": retries,
    }
    if outcome is not None:
        telemetry["final_outcome"] = outcome
    return {
        "schema_version": SCHEMA_VERSION,
        "observer_mode": "log_only",
        "authoritative": False,
        "segment": segment,
        "start_boundary": start_boundary,
        "end_boundary": end_boundary,
        # Writes are judged by the treatment in force when the segment began,
        # so a segment cannot relabel its own writes.
        "treatment": {
            "judged_by": "base",
            "base_pack": base_pack,
            "candidate": candidate,
        },
        "artifacts": artifacts,
        "summary": {
            "compatibility": {
                result: compatibility_counts[result] for result in COMPATIBILITY_RESULTS
            },
            "conditions": dict(
                sorted(
                    Counter(
                        str(item["condition"])
                        for item in artifacts
                        if item["condition"] is not None
                    ).items()
                )
            ),
            "role_provenance": {
                provenance: provenance_counts[provenance]
                for provenance in ROLE_PROVENANCE
            },
            "role_changes": sum(item["role_changed"] is True for item in artifacts),
            "bootstrap_root_writes": sum(
                bool(item["bootstrap_root"]) for item in artifacts
            ),
        },
        "telemetry": telemetry,
    }


def _emit(payload: dict[str, object], output: str) -> None:
    if output == "-":
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return
    _atomic_json_write(Path(output), payload)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record non-authoritative, log-only work-segment evidence."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="declare and snapshot a segment")
    start.add_argument("--root", type=Path, default=PROJECT_ROOT)
    start.add_argument("--state", type=Path, required=True)
    start.add_argument("--segment-id", required=True)
    start.add_argument("--work-type", choices=WORK_TYPES, required=True)
    start.add_argument("--started-at")
    start.add_argument("--task-id")
    start.add_argument("--session-id")
    start.add_argument("--output", default="-")

    finish = subparsers.add_parser("finish", help="close and report a segment")
    finish.add_argument("--state", type=Path, required=True)
    finish.add_argument("--ended-at")
    finish.add_argument("--tool-call-count", type=int, default=0)
    finish.add_argument("--failures", type=int, default=0)
    finish.add_argument("--retries", type=int, default=0)
    finish.add_argument("--outcome")
    finish.add_argument("--output", default="-")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "start":
            payload = start_segment(
                args.root,
                state_path=args.state,
                segment_id=args.segment_id,
                work_type=args.work_type,
                started_at=args.started_at,
                task_id=args.task_id,
                session_id=args.session_id,
            )
        else:
            payload = finish_segment(
                args.state,
                ended_at=args.ended_at,
                tool_call_count=args.tool_call_count,
                failures=args.failures,
                retries=args.retries,
                outcome=args.outcome,
            )
        _emit(payload, args.output)
    except (ObservationError, RoleDeclarationError, OSError) as exc:
        print(f"observe-work-segment: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
