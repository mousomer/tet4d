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
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

WORK_TYPES = ("Planning", "Coding", "Manifest")
ARTIFACT_ROLES = (
    "governance_treatment",
    "executable_machinery",
    "product_authority",
    "planning_document",
    "generated",
    "bookkeeping",
)
ROLE_PROVENANCE = ("explicit_declared", "bootstrap_projected", "unclassified")
COMPATIBILITY_RESULTS = (
    "compatible",
    "contradiction",
    "unclassified",
    "indeterminate",
)

_COMPATIBILITY = {
    "Planning": {
        "governance_treatment": "contradiction",
        "executable_machinery": "contradiction",
        "product_authority": "compatible",
        "planning_document": "compatible",
        "generated": "contradiction",
        "bookkeeping": "compatible",
    },
    "Coding": {
        "governance_treatment": "contradiction",
        "executable_machinery": "compatible",
        "product_authority": "compatible",
        "planning_document": "compatible",
        "generated": "compatible",
        "bookkeeping": "compatible",
    },
    "Manifest": {
        "governance_treatment": "compatible",
        "executable_machinery": "contradiction",
        "product_authority": "contradiction",
        "planning_document": "compatible",
        "generated": "compatible",
        "bookkeeping": "compatible",
    },
}

# These exact paths are bootstrap roots accepted by the work-type ADR. They are
# not patterns and they do not turn the observer output into role authority.
_INSTRUCTION_ROOTS = {
    "AGENTS.md",
    "CLAUDE.md",
    "godot/AGENTS.md",
    "native/AGENTS.md",
}
_COMPATIBILITY_TREATMENT = "config/project/policy_pack.json"
_PROJECT_MANIFEST = "config/governance/project.json"
_BOOTSTRAP_PRODUCT_AUTHORITIES = {
    "docs/architecture/work_type_classification.md",
}
_BOOTSTRAP_GENERATED = {
    "config/governance/workspace.lock.json",
    "docs/CONFIGURATION_REFERENCE.md",
}


class ObservationError(ValueError):
    """Raised when an observation request or its local evidence is invalid."""


@dataclass(frozen=True)
class RoleResolution:
    role: str
    provenance: str
    source: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "role_provenance": self.provenance,
            "role_source": self.source,
        }


@dataclass(frozen=True)
class RoleIndex:
    explicit: dict[str, RoleResolution]
    bootstrap: dict[str, RoleResolution]
    bootstrap_directories: tuple[tuple[str, RoleResolution], ...]

    def resolve(self, path: str) -> RoleResolution:
        normalized = _normalize_repo_path(path)
        if normalized in self.explicit:
            return self.explicit[normalized]
        if normalized in self.bootstrap:
            return self.bootstrap[normalized]
        for directory, resolution in self.bootstrap_directories:
            if normalized.startswith(f"{directory}/"):
                return resolution
        return RoleResolution("unclassified", "unclassified", None)


def _normalize_repo_path(path: str) -> str:
    normalized = Path(path).as_posix().removeprefix("./")
    if not normalized or normalized == "." or normalized.startswith("../"):
        raise ObservationError(f"path is not repository-relative: {path!r}")
    return normalized.rstrip("/")


def _json_pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


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
        normalized = _normalize_repo_path(relative)
        state = _file_state(root / relative)
        if state is not None:
            snapshot[normalized] = state
    return dict(sorted(snapshot.items()))


def classify_changes(
    before: dict[str, dict[str, object]],
    after: dict[str, dict[str, object]],
) -> list[dict[str, str]]:
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

    for path in sorted(deleted - renamed_from):
        changes.append({"path": path, "change_kind": "deleted"})
    for path in sorted(created - renamed_to):
        changes.append({"path": path, "change_kind": "created"})
    for path in sorted(before_paths & after_paths):
        if before[path] != after[path]:
            changes.append({"path": path, "change_kind": "modified"})
    return sorted(changes, key=lambda item: (item["path"], item["change_kind"]))


def _declared_pack_roles(root: Path) -> dict[str, RoleResolution]:
    workspace = _load_json(root / ".governance/workspace.json")
    governance_pack = workspace.get("governance_pack")
    if not isinstance(governance_pack, dict):
        raise ObservationError("workspace manifest lacks governance_pack")
    lock_path = governance_pack.get("lock")
    if not isinstance(lock_path, str):
        raise ObservationError("workspace governance_pack.lock must be a path")
    lock = _load_json(root / lock_path)
    pack_path = lock.get("pack_path")
    if not isinstance(pack_path, str):
        raise ObservationError("workspace lock pack_path must be a path")
    manifest_path = root / pack_path / "MANIFEST.json"
    manifest = _load_json(manifest_path)
    declarations = manifest.get("artifact_roles")
    if not isinstance(declarations, list):
        raise ObservationError("pack manifest artifact_roles must be a list")
    roles: dict[str, RoleResolution] = {}
    for index, declaration in enumerate(declarations):
        if not isinstance(declaration, dict):
            raise ObservationError(f"artifact_roles[{index}] must be an object")
        relative, role = declaration.get("path"), declaration.get("role")
        if not isinstance(relative, str) or role not in ARTIFACT_ROLES:
            raise ObservationError(f"artifact_roles[{index}] is invalid")
        path = _normalize_repo_path(f"{pack_path}/{relative}")
        roles[path] = RoleResolution(
            str(role),
            "explicit_declared",
            f"{Path(pack_path).as_posix()}/MANIFEST.json#/artifact_roles/{index}",
        )
    return roles


def _project_declared_roles(project: dict[str, Any]) -> dict[str, RoleResolution]:
    explicit: dict[str, RoleResolution] = {}
    project_roles = project.get("artifact_roles", {})
    if not isinstance(project_roles, dict):
        raise ObservationError("project artifact_roles must be an object")
    for raw_path, role in project_roles.items():
        if not isinstance(raw_path, str) or role not in ARTIFACT_ROLES:
            raise ObservationError(
                "project artifact_roles contains an invalid declaration"
            )
        path = _normalize_repo_path(raw_path)
        explicit[path] = RoleResolution(
            str(role),
            "explicit_declared",
            f"{_PROJECT_MANIFEST}#/artifact_roles/{_json_pointer_token(raw_path)}",
        )
    return explicit


def _add_bootstrap_role(
    bootstrap: dict[str, RoleResolution], path: str, role: str, source: str
) -> None:
    normalized = _normalize_repo_path(path.split("#", 1)[0])
    bootstrap.setdefault(
        normalized,
        RoleResolution(role, "bootstrap_projected", source),
    )


def _base_bootstrap_roles() -> dict[str, RoleResolution]:
    bootstrap: dict[str, RoleResolution] = {}
    _add_bootstrap_role(
        bootstrap,
        _PROJECT_MANIFEST,
        "governance_treatment",
        "accepted bootstrap root",
    )
    _add_bootstrap_role(
        bootstrap,
        _COMPATIBILITY_TREATMENT,
        "governance_treatment",
        "accepted compatibility authority",
    )
    for path in sorted(_INSTRUCTION_ROOTS):
        _add_bootstrap_role(
            bootstrap,
            path,
            "governance_treatment",
            "accepted instruction bootstrap root",
        )
    for path in sorted(_BOOTSTRAP_PRODUCT_AUTHORITIES):
        _add_bootstrap_role(
            bootstrap,
            path,
            "product_authority",
            "accepted architecture authority",
        )
    for path in sorted(_BOOTSTRAP_GENERATED):
        _add_bootstrap_role(bootstrap, path, "generated", "accepted generated surface")
    return bootstrap


def _apply_authority_bootstrap_role(
    authority: dict[str, Any],
    *,
    index: int,
    bootstrap: dict[str, RoleResolution],
) -> tuple[str, RoleResolution] | None:
    source = authority.get("source")
    authority_id = authority.get("authority_id")
    if not isinstance(source, str) or not isinstance(authority_id, str):
        return None
    provenance = f"{_PROJECT_MANIFEST}#/authorities/{index} ({authority_id})"
    if authority.get("canonical_governance") is True:
        if authority.get("source_type") == "file":
            _add_bootstrap_role(bootstrap, source, "governance_treatment", provenance)
        return None
    if authority_id == "open-work-backlog":
        _add_bootstrap_role(bootstrap, source, "bookkeeping", provenance)
        return None
    if authority.get("authority_type") != "human":
        return None
    resolution = RoleResolution("product_authority", "bootstrap_projected", provenance)
    if authority.get("source_type") == "directory":
        return (_normalize_repo_path(source), resolution)
    if authority.get("source_type") == "file":
        _add_bootstrap_role(bootstrap, source, "product_authority", provenance)
    return None


def _authority_bootstrap_roles(
    project: dict[str, Any], bootstrap: dict[str, RoleResolution]
) -> list[tuple[str, RoleResolution]]:
    authorities = project.get("authorities")
    if not isinstance(authorities, list):
        raise ObservationError("project authorities must be a list")
    directories: list[tuple[str, RoleResolution]] = []
    for index, authority in enumerate(authorities):
        if not isinstance(authority, dict):
            raise ObservationError(f"authorities[{index}] must be an object")
        directory = _apply_authority_bootstrap_role(
            authority, index=index, bootstrap=bootstrap
        )
        if directory is not None:
            directories.append(directory)
    return directories


def _add_generated_bootstrap_roles(
    project: dict[str, Any], bootstrap: dict[str, RoleResolution]
) -> None:
    generated_surfaces = project.get("generated_surfaces", [])
    if not isinstance(generated_surfaces, list):
        raise ObservationError("project generated_surfaces must be a list")
    for index, surface in enumerate(generated_surfaces):
        if not isinstance(surface, dict) or not isinstance(surface.get("target"), str):
            raise ObservationError(f"generated_surfaces[{index}] is invalid")
        _add_bootstrap_role(
            bootstrap,
            str(surface["target"]),
            "generated",
            f"{_PROJECT_MANIFEST}#/generated_surfaces/{index}",
        )


def build_role_index(root: Path) -> RoleIndex:
    root = root.resolve()
    project = _load_json(root / _PROJECT_MANIFEST)
    explicit = _declared_pack_roles(root)
    explicit.update(_project_declared_roles(project))

    bootstrap = _base_bootstrap_roles()
    directories = _authority_bootstrap_roles(project, bootstrap)
    _add_generated_bootstrap_roles(project, bootstrap)

    return RoleIndex(
        explicit=dict(sorted(explicit.items())),
        bootstrap=dict(sorted(bootstrap.items())),
        bootstrap_directories=tuple(
            sorted(directories, key=lambda item: (-len(item[0]), item[0]))
        ),
    )


def compatibility(work_type: str, role: str) -> str:
    validate_work_type(work_type)
    if role == "unclassified":
        return "unclassified"
    if role not in ARTIFACT_ROLES:
        return "indeterminate"
    return _COMPATIBILITY[work_type][role]


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
    state: dict[str, object] = {
        "schema_version": 1,
        "root": str(root),
        "segment": segment,
        "start_boundary": boundary,
        "start_snapshot": repository_snapshot(root),
    }
    _atomic_json_write(state_path, state)
    return {
        "schema_version": 1,
        "observer_mode": "log_only",
        "authoritative": False,
        "segment": segment,
        "start_boundary": boundary,
        "state_path": str(state_path),
    }


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
    if state.get("schema_version") != 1:
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
    root = Path(root_value).resolve()
    observed_at = ended_at or _utc_now()
    end_time = _parse_time(observed_at, field="ended_at")
    start_time = _parse_time(str(start_boundary.get("observed_at")), field="started_at")
    elapsed = (end_time - start_time).total_seconds()
    if elapsed < 0:
        raise ObservationError("ended_at must not precede started_at")

    end_boundary = {"head": _head(root), "observed_at": observed_at}
    end_snapshot = repository_snapshot(root)
    changes = classify_changes(start_snapshot, end_snapshot)
    role_index = build_role_index(root)
    artifacts: list[dict[str, object]] = []
    for change in changes:
        resolution = role_index.resolve(change["path"])
        artifact: dict[str, object] = {
            **change,
            **resolution.to_dict(),
            "compatibility": compatibility(work_type, resolution.role),
        }
        artifacts.append(artifact)

    compatibility_counts = Counter(
        str(artifact["compatibility"]) for artifact in artifacts
    )
    provenance_counts = Counter(
        str(artifact["role_provenance"]) for artifact in artifacts
    )
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
        "schema_version": 1,
        "observer_mode": "log_only",
        "authoritative": False,
        "segment": segment,
        "start_boundary": start_boundary,
        "end_boundary": end_boundary,
        "artifacts": artifacts,
        "summary": {
            "compatibility": {
                result: compatibility_counts[result] for result in COMPATIBILITY_RESULTS
            },
            "role_provenance": {
                provenance: provenance_counts[provenance]
                for provenance in ROLE_PROVENANCE
            },
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
    except (ObservationError, OSError) as exc:
        print(f"observe-work-segment: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
