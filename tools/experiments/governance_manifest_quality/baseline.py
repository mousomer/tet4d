from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.governance.policy_pack_io import load_policy_pack
from tools.governance.validate_governance_surface import validate_surface
from tools.workspace_governance.validators.core import (
    load_manifest_json,
    pack_hash,
)

ROOT = Path(__file__).resolve().parents[3]
BASELINE_PATH = Path(__file__).with_name("frozen_baseline.json")
POLICY_PATH = Path("config/project/policy_pack.json")
PROJECT_MANIFEST_PATH = Path("config/governance/project.json")
WORKSPACE_LOCK_PATH = Path("config/governance/workspace.lock.json")
PROJECT_SCHEMA_PATH = Path("tools/workspace_governance/schemas/project.schema.json")
RESOLVER_PATH = Path("tools/workspace_governance/resolver/core.py")
WORKSPACE_PACK_PATH = Path("tools/workspace_governance")
FROZEN_TREATMENT_PATHS = (
    ".governance/workspace.json",
    "config/governance/project.json",
    "config/governance/workspace.lock.json",
    "config/project/policy_pack.json",
    "tools/workspace_governance",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    ".github/pull_request_template.md",
    "docs/governance",
    "godot/AGENTS.md",
    "native/AGENTS.md",
)


class BaselineMismatchError(RuntimeError):
    """Raised when the checkout is not the declared frozen treatment."""

    def __init__(self, fingerprint: dict[str, Any], mismatches: list[str]) -> None:
        super().__init__("frozen baseline mismatch: " + "; ".join(mismatches))
        self.fingerprint = fingerprint
        self.mismatches = mismatches


@dataclass(frozen=True)
class FrozenBaseline:
    baseline_repository_commit: str
    workspace_governance_pack_name: str
    workspace_governance_pack_path: str
    workspace_governance_lock_algorithm: str
    workspace_governance_revision: str
    workspace_governance_content_sha256: str
    machine_policy_path: str
    machine_policy_raw_sha256: str
    machine_policy_serialized_bytes: int
    machine_policy_advisory_bytes: int
    machine_policy_hard_ceiling_bytes: int
    human_governance_diagnostic_loc: int
    backlog_ceiling_loc: int


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def load_frozen_baseline(path: Path = BASELINE_PATH) -> FrozenBaseline:
    payload = _read_json(path)
    repository = payload["repository"]
    workspace = payload["workspace_governance"]
    machine_policy = payload["machine_policy"]
    thresholds = payload["thresholds"]
    return FrozenBaseline(
        baseline_repository_commit=str(repository["baseline_commit"]),
        workspace_governance_pack_name=str(workspace["pack_name"]),
        workspace_governance_pack_path=str(workspace["pack_path"]),
        workspace_governance_lock_algorithm=str(workspace["lock_algorithm"]),
        workspace_governance_revision=str(workspace["revision"]),
        workspace_governance_content_sha256=str(workspace["content_sha256"]),
        machine_policy_path=str(machine_policy["path"]),
        machine_policy_raw_sha256=str(machine_policy["raw_sha256"]),
        machine_policy_serialized_bytes=int(machine_policy["serialized_bytes"]),
        machine_policy_advisory_bytes=int(thresholds["machine_policy_advisory_bytes"]),
        machine_policy_hard_ceiling_bytes=int(
            thresholds["machine_policy_hard_ceiling_bytes"]
        ),
        human_governance_diagnostic_loc=int(
            thresholds["human_governance_diagnostic_loc"]
        ),
        backlog_ceiling_loc=int(thresholds["backlog_ceiling_loc"]),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _git_commit_exists(root: Path, commit: str) -> bool:
    return (
        subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=root,
            check=False,
            capture_output=True,
        ).returncode
        == 0
    )


def _git_is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=root,
            check=False,
            capture_output=True,
        ).returncode
        == 0
    )


def _frozen_paths_match(root: Path, baseline_commit: str) -> bool:
    if not _git_commit_exists(root, baseline_commit):
        return False
    return (
        subprocess.run(
            [
                "git",
                "diff",
                "--quiet",
                baseline_commit,
                "--",
                *FROZEN_TREATMENT_PATHS,
            ],
            cwd=root,
            check=False,
            capture_output=True,
        ).returncode
        == 0
    )


def _schema_identity(root: Path, project: dict[str, Any]) -> dict[str, Any]:
    scenarios = project.get("execution", {}).get("representative_scenarios")
    scenario_bytes = json.dumps(
        scenarios, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "project_manifest_schema_version": project.get("schema_version"),
        "project_schema_sha256": _sha256(root / PROJECT_SCHEMA_PATH),
        "resolver_sha256": _sha256(root / RESOLVER_PATH),
        "scenario_definitions_sha256": hashlib.sha256(scenario_bytes).hexdigest(),
    }


def measure_fingerprint(
    root: Path = ROOT, *, baseline_commit: str | None = None
) -> dict[str, Any]:
    if baseline_commit is None:
        baseline_commit = load_frozen_baseline().baseline_repository_commit
    policy_path = root / POLICY_PATH
    policy = load_policy_pack(policy_path)
    project = _read_json(root / PROJECT_MANIFEST_PATH)
    workspace_lock = _read_json(root / WORKSPACE_LOCK_PATH)
    workspace_manifest = load_manifest_json(
        root / WORKSPACE_PACK_PATH / "MANIFEST.json"
    )
    workspace_content_sha256, workspace_files = pack_hash(root / WORKSPACE_PACK_PATH)
    checkout_commit = _git_head(root)
    issues, surface = validate_surface(root)
    if surface is None:
        messages = "; ".join(issue.message for issue in issues)
        raise RuntimeError(f"governance surface cannot be measured: {messages}")

    active = policy["governance_surface"]["active_governance"]
    active_files = {
        group: sorted(str(path) for path in paths)
        for group, paths in sorted(active.items())
    }
    largest_name = max(
        policy,
        key=lambda key: len(
            json.dumps(policy[key], ensure_ascii=False).encode("utf-8")
        ),
    )
    return {
        "schema_version": 1,
        "fingerprint_kind": "non_authoritative_experiment_record",
        "repository": {
            "baseline_commit": baseline_commit,
            "checkout_commit": checkout_commit,
            "baseline_commit_exists": _git_commit_exists(root, baseline_commit),
            "baseline_is_ancestor_of_checkout": _git_is_ancestor(
                root, baseline_commit, checkout_commit
            ),
            "frozen_treatment_paths_match_baseline": _frozen_paths_match(
                root, baseline_commit
            ),
        },
        "workspace_governance": {
            "revision": workspace_manifest.get("revision"),
            "content_sha256": workspace_content_sha256,
            "locked_revision": workspace_lock.get("revision"),
            "locked_content_sha256": workspace_lock.get("content_sha256"),
            "lock_algorithm": workspace_lock.get("lock_algorithm"),
            "pack_name": workspace_lock.get("pack_name"),
            "pack_path": workspace_lock.get("pack_path"),
            "locked_files_match_computed": workspace_lock.get("files")
            == workspace_files,
        },
        "machine_policy": {
            "path": POLICY_PATH.as_posix(),
            "raw_sha256": _sha256(policy_path),
            "serialized_bytes": len(policy_path.read_bytes()),
            "node_count": surface.policy_nodes,
            "leaf_count": surface.policy_leaves,
            "maximum_nesting_depth": surface.policy_max_depth,
            "largest_top_level_section": {
                "name": largest_name,
                "bytes": surface.largest_policy_section_bytes,
            },
        },
        "human_governance_loc": surface.human,
        "active_governance_files": active_files,
        "schema_identity": _schema_identity(root, project),
        "thresholds": {
            "machine_policy_advisory_bytes": surface.policy_advisory_byte_limit,
            "machine_policy_hard_ceiling_bytes": surface.policy_byte_limit,
            "human_governance_diagnostic_loc": 900,
            "backlog_ceiling_loc": policy["governance_surface"]["per_file_limits"][
                "docs/BACKLOG.md"
            ],
        },
        "governance_surface_issues": [
            {"kind": issue.kind, "message": issue.message} for issue in issues
        ],
    }


def validate_fingerprint(
    fingerprint: dict[str, Any], baseline: FrozenBaseline
) -> list[str]:
    repository = fingerprint["repository"]
    workspace = fingerprint["workspace_governance"]
    machine_policy = fingerprint["machine_policy"]
    thresholds = fingerprint["thresholds"]
    comparisons = (
        (
            "baseline repository commit",
            repository["baseline_commit"],
            baseline.baseline_repository_commit,
        ),
        (
            "baseline repository commit exists",
            repository["baseline_commit_exists"],
            True,
        ),
        (
            "baseline is ancestor of checkout",
            repository["baseline_is_ancestor_of_checkout"],
            True,
        ),
        (
            "frozen treatment paths match baseline",
            repository["frozen_treatment_paths_match_baseline"],
            True,
        ),
        (
            "workspace-governance pack name",
            workspace["pack_name"],
            baseline.workspace_governance_pack_name,
        ),
        (
            "workspace-governance pack path",
            workspace["pack_path"],
            baseline.workspace_governance_pack_path,
        ),
        (
            "workspace-governance lock algorithm",
            workspace["lock_algorithm"],
            baseline.workspace_governance_lock_algorithm,
        ),
        (
            "workspace-governance revision",
            workspace["revision"],
            baseline.workspace_governance_revision,
        ),
        (
            "workspace-governance content SHA-256",
            workspace["content_sha256"],
            baseline.workspace_governance_content_sha256,
        ),
        (
            "workspace-governance locked revision",
            workspace["locked_revision"],
            baseline.workspace_governance_revision,
        ),
        (
            "workspace-governance locked content SHA-256",
            workspace["locked_content_sha256"],
            baseline.workspace_governance_content_sha256,
        ),
        (
            "workspace-governance locked files",
            workspace["locked_files_match_computed"],
            True,
        ),
        (
            "machine-policy path",
            machine_policy["path"],
            baseline.machine_policy_path,
        ),
        (
            "machine-policy raw SHA-256",
            machine_policy["raw_sha256"],
            baseline.machine_policy_raw_sha256,
        ),
        (
            "machine-policy serialized bytes",
            machine_policy["serialized_bytes"],
            baseline.machine_policy_serialized_bytes,
        ),
        (
            "machine-policy advisory bytes",
            thresholds["machine_policy_advisory_bytes"],
            baseline.machine_policy_advisory_bytes,
        ),
        (
            "machine-policy hard ceiling bytes",
            thresholds["machine_policy_hard_ceiling_bytes"],
            baseline.machine_policy_hard_ceiling_bytes,
        ),
        (
            "human-governance diagnostic LOC",
            thresholds["human_governance_diagnostic_loc"],
            baseline.human_governance_diagnostic_loc,
        ),
        (
            "BACKLOG ceiling LOC",
            thresholds["backlog_ceiling_loc"],
            baseline.backlog_ceiling_loc,
        ),
    )
    return [
        f"{name}: measured {actual!r}, declared {expected!r}"
        for name, actual, expected in comparisons
        if actual != expected
    ]


def require_frozen_baseline(
    root: Path = ROOT, baseline_path: Path = BASELINE_PATH
) -> dict[str, Any]:
    baseline = load_frozen_baseline(baseline_path)
    fingerprint = measure_fingerprint(
        root, baseline_commit=baseline.baseline_repository_commit
    )
    mismatches = validate_fingerprint(fingerprint, baseline)
    if mismatches:
        raise BaselineMismatchError(fingerprint, mismatches)
    return fingerprint
