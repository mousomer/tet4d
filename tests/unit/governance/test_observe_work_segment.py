from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.governance.observe_work_segment import (
    ObservationError,
    classify_changes,
    finish_segment,
    main,
    start_segment,
    validate_work_type,
)
from tools.workspace_governance.resolver.core import GovernanceResolver
from tools.workspace_governance.resolver.roles import WORK_TYPES


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def observer_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Observer Test")
    _git(root, "config", "user.email", "observer@example.invalid")

    _write_json(
        root / ".governance/workspace.json",
        {
            "projects": [
                {
                    "id": "demo",
                    "repository": ".",
                    "manifest": "config/governance/project.json",
                }
            ],
            "defaults": {"project": "demo"},
            "governance_pack": {"lock": "config/governance/workspace.lock.json"},
        },
    )
    _write_json(
        root / "config/governance/workspace.lock.json",
        {"pack_path": "tools/workspace_governance"},
    )
    _write_json(
        root / "config/governance/project.json",
        {
            "artifact_roles": {"notes/plan.md": "planning_document"},
            "role_bootstrap": {
                "instruction_roots": ["AGENTS.md", "godot/AGENTS.md"],
                "bookkeeping": ["docs/BACKLOG.md"],
            },
            "authorities": [
                {
                    "authority_id": "engineering",
                    "authority_type": "human",
                    "canonical_governance": True,
                    "source": "docs/governance/ENGINEERING.md",
                    "source_type": "file",
                },
                {
                    "authority_id": "product-requirements",
                    "authority_type": "human",
                    "canonical_governance": False,
                    "source": "docs/rds/",
                    "source_type": "directory",
                },
                {
                    "authority_id": "open-work-backlog",
                    "authority_type": "human",
                    "canonical_governance": False,
                    "source": "docs/BACKLOG.md",
                    "source_type": "file",
                },
                {
                    "authority_id": "legacy-policy-pack",
                    "authority_type": "compatibility",
                    "canonical_governance": False,
                    "source": "config/project/policy_pack.json",
                    "source_type": "file",
                },
            ],
            "routes": {
                "example": {"dispatch_paths": ["routed/only.txt"]},
            },
            "generated_surfaces": [
                {"target": "config/project/policy_pack.json#/routes"},
                {"target": "generated/reference.json"},
            ],
        },
    )
    _write_json(
        root / "tools/workspace_governance/MANIFEST.json",
        {
            "version": "0.0.0",
            "revision": "observer-fixture",
            "lock_algorithm": "sha256-path-and-content-v1",
            "pack_hash_excludes": [],
            "artifact_roles": [
                {"path": "MANIFEST.json", "role": "executable_machinery"},
                {"path": "worker.py", "role": "executable_machinery"},
            ],
            "bootstrap_roots": ["MANIFEST.json"],
        },
    )
    files = {
        "AGENTS.md": "instructions\n",
        "config/project/policy_pack.json": "{}\n",
        "docs/BACKLOG.md": "backlog\n",
        "docs/governance/ENGINEERING.md": "governance\n",
        "docs/rds/feature.md": "requirements\n",
        "generated/reference.json": "{}\n",
        "godot/AGENTS.md": "godot instructions\n",
        "notes/plan.md": "plan\n",
        "routed/only.txt": "route context\n",
        "src/unknown.py": "print('unknown')\n",
        "tools/workspace_governance/worker.py": "VALUE = 1\n",
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "fixture")
    return root


def _roles(root: Path):
    return GovernanceResolver.for_root(root).role_index()


def _observe(root: Path, state: Path, work_type: str, edit) -> dict:
    start_segment(
        root,
        state_path=state,
        segment_id="g1-test",
        work_type=work_type,
        started_at="2026-09-20T10:00:00Z",
    )
    edit(root)
    return finish_segment(state, ended_at="2026-09-20T10:00:05Z")


def _by_path(observation: dict) -> dict[str, dict]:
    return {item["path"]: item for item in observation["artifacts"]}


def test_work_type_vocabulary_is_exact_and_unknown_is_rejected() -> None:
    for work_type in WORK_TYPES:
        assert validate_work_type(work_type) == work_type
    for unknown in ("Meta", "Mixed", "Verification", "Unknown"):
        with pytest.raises(ObservationError, match="work_type"):
            validate_work_type(unknown)


def test_role_resolution_preserves_explicit_bootstrap_and_unknown_provenance(
    observer_repo: Path,
) -> None:
    roles = _roles(observer_repo)

    explicit = roles.resolve("tools/workspace_governance/worker.py")
    assert (explicit.role, explicit.provenance) == (
        "executable_machinery",
        "explicit_declared",
    )
    project_explicit = roles.resolve("notes/plan.md")
    assert (project_explicit.role, project_explicit.provenance) == (
        "planning_document",
        "explicit_declared",
    )
    governance = roles.resolve("docs/governance/ENGINEERING.md")
    assert (governance.role, governance.provenance) == (
        "governance_treatment",
        "bootstrap_projected",
    )
    instruction = roles.resolve("godot/AGENTS.md")
    assert instruction.role == "governance_treatment"
    assert instruction.source == (
        "config/governance/project.json#/role_bootstrap/instruction_roots/1"
    )
    assert roles.resolve("docs/rds/feature.md").role == "product_authority"
    # The declared bookkeeping record outranks its human-authority projection.
    assert roles.resolve("docs/BACKLOG.md").role == "bookkeeping"
    # A compatibility authority is treatment; a pointer target inside it does
    # not turn the whole file into a generated artifact.
    assert roles.resolve("config/project/policy_pack.json").role == (
        "governance_treatment"
    )
    assert roles.resolve("generated/reference.json").role == "generated"
    assert roles.resolve("config/governance/workspace.lock.json").role == "generated"

    unknown = roles.resolve("src/unknown.py")
    assert unknown.to_dict() == {
        "role": "unclassified",
        "role_provenance": "unclassified",
        "role_source": None,
    }


def test_dispatch_paths_do_not_determine_or_change_artifact_role(
    observer_repo: Path,
) -> None:
    before = _roles(observer_repo)
    assert before.resolve("routed/only.txt").role == "unclassified"
    assert before.resolve("godot/AGENTS.md").role == "governance_treatment"

    project_path = observer_repo / "config/governance/project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["routes"]["example"]["dispatch_paths"] = ["src/unknown.py"]
    _write_json(project_path, project)

    after = _roles(observer_repo)
    assert after.resolve("routed/only.txt").role == "unclassified"
    assert after.resolve("src/unknown.py").role == "unclassified"
    assert after.resolve("godot/AGENTS.md").role == "governance_treatment"


def test_change_classification_reports_both_ends_of_a_rename() -> None:
    unchanged = {"sha256": "same", "kind": "file", "mode": 420, "size": 4}
    before = {
        "delete.txt": {"sha256": "delete", "kind": "file", "mode": 420, "size": 1},
        "modify.txt": {"sha256": "old", "kind": "file", "mode": 420, "size": 1},
        "old-name.txt": unchanged,
    }
    after = {
        "create.txt": {"sha256": "create", "kind": "file", "mode": 420, "size": 1},
        "modify.txt": {"sha256": "new", "kind": "file", "mode": 420, "size": 1},
        "new-name.txt": unchanged,
    }

    assert classify_changes(before, after) == [
        {"path": "create.txt", "change_kind": "created"},
        {"path": "delete.txt", "change_kind": "deleted"},
        {"path": "modify.txt", "change_kind": "modified"},
        {
            "path": "new-name.txt",
            "change_kind": "renamed",
            "previous_path": "old-name.txt",
        },
        {
            "path": "old-name.txt",
            "change_kind": "renamed_away",
            "next_path": "new-name.txt",
        },
    ]


def test_coding_contradiction_is_recorded_without_blocking_and_manifest_is_allowed(
    observer_repo: Path, tmp_path: Path
) -> None:
    state = tmp_path / "segment-state.json"
    start_segment(
        observer_repo,
        state_path=state,
        segment_id="g1-test",
        work_type="Coding",
        started_at="2026-09-20T10:00:00Z",
    )
    governance = observer_repo / "docs/governance/ENGINEERING.md"
    governance.write_text("changed governance\n", encoding="utf-8")

    coding = finish_segment(
        state,
        ended_at="2026-09-20T10:00:05Z",
        tool_call_count=3,
        failures=1,
        retries=1,
        outcome="completed",
    )
    assert coding["schema_version"] == 2
    assert coding["observer_mode"] == "log_only"
    assert coding["authoritative"] is False
    assert coding["treatment"]["judged_by"] == "base"
    assert coding["treatment"]["candidate"]["state"] == "resolved"
    assert coding["artifacts"] == [
        {
            "path": "docs/governance/ENGINEERING.md",
            "change_kind": "modified",
            "role": "governance_treatment",
            "role_provenance": "bootstrap_projected",
            "role_source": (
                "config/governance/project.json#/authorities/0 (engineering)"
            ),
            "compatibility": "contradiction",
            "condition": None,
            "bootstrap_root": False,
            "candidate_role": "governance_treatment",
            "candidate_role_provenance": "bootstrap_projected",
            "candidate_role_source": (
                "config/governance/project.json#/authorities/0 (engineering)"
            ),
            "role_changed": False,
        }
    ]
    assert coding["telemetry"] == {
        "segment_count": 1,
        "files_written": 1,
        "elapsed_seconds": 5.0,
        "tool_call_count": 3,
        "failures": 1,
        "retries": 1,
        "final_outcome": "completed",
    }

    saved = json.loads(state.read_text(encoding="utf-8"))
    saved["segment"]["work_type"] = "Manifest"
    _write_json(state, saved)
    manifest = finish_segment(state, ended_at="2026-09-20T10:00:05Z")
    assert manifest["artifacts"][0]["compatibility"] == "compatible"


def test_a_segment_cannot_relabel_its_own_writes(
    observer_repo: Path, tmp_path: Path
) -> None:
    def relabel_and_edit(root: Path) -> None:
        project_path = root / "config/governance/project.json"
        project = json.loads(project_path.read_text(encoding="utf-8"))
        project["artifact_roles"].update(
            {
                "AGENTS.md": "bookkeeping",
                "docs/governance/ENGINEERING.md": "executable_machinery",
            }
        )
        _write_json(project_path, project)
        for path in ("AGENTS.md", "docs/governance/ENGINEERING.md"):
            (root / path).write_text("weakened\n", encoding="utf-8")

    observation = _observe(
        observer_repo, tmp_path / "state.json", "Coding", relabel_and_edit
    )
    artifacts = _by_path(observation)
    assert {path: item["compatibility"] for path, item in artifacts.items()} == {
        "AGENTS.md": "contradiction",
        "config/governance/project.json": "contradiction",
        "docs/governance/ENGINEERING.md": "contradiction",
    }
    # The relabel is visible as data. A root keeps its fixed role even in the
    # candidate, while a non-root declaration does change the candidate role.
    assert artifacts["AGENTS.md"]["candidate_role"] == "governance_treatment"
    assert artifacts["docs/governance/ENGINEERING.md"]["role_changed"] is True
    assert observation["summary"]["role_changes"] == 1
    assert observation["summary"]["bootstrap_root_writes"] == 2


def test_moving_an_instruction_file_away_is_judged_at_its_old_path(
    observer_repo: Path, tmp_path: Path
) -> None:
    def move_away(root: Path) -> None:
        (root / "godot/AGENTS.md").rename(root / "src/notes.md")

    artifacts = _by_path(
        _observe(observer_repo, tmp_path / "state.json", "Coding", move_away)
    )
    assert artifacts["godot/AGENTS.md"]["change_kind"] == "renamed_away"
    assert artifacts["godot/AGENTS.md"]["compatibility"] == "contradiction"
    assert artifacts["godot/AGENTS.md"]["bootstrap_root"] is True
    assert artifacts["src/notes.md"]["compatibility"] == "unclassified"


def test_conditional_cells_are_reported_with_their_condition(
    observer_repo: Path, tmp_path: Path
) -> None:
    def edit(root: Path) -> None:
        (root / "docs/rds/feature.md").write_text("changed\n", encoding="utf-8")
        (root / "notes/plan.md").write_text("changed\n", encoding="utf-8")

    observation = _observe(observer_repo, tmp_path / "state.json", "Manifest", edit)
    artifacts = _by_path(observation)
    assert artifacts["docs/rds/feature.md"]["compatibility"] == "conditional"
    assert artifacts["docs/rds/feature.md"]["condition"] == (
        "contradiction_unless_justified"
    )
    assert artifacts["notes/plan.md"]["condition"] == (
        "allowed_if_documenting_manifest_decision"
    )
    assert observation["summary"]["compatibility"]["conditional"] == 2
    assert observation["summary"]["conditions"] == {
        "allowed_if_documenting_manifest_decision": 1,
        "contradiction_unless_justified": 1,
    }


def test_a_broken_candidate_treatment_is_recorded_and_writes_still_judged(
    observer_repo: Path, tmp_path: Path
) -> None:
    def break_manifest(root: Path) -> None:
        (root / "config/governance/project.json").write_text("{", encoding="utf-8")

    observation = _observe(
        observer_repo, tmp_path / "state.json", "Coding", break_manifest
    )
    candidate = observation["treatment"]["candidate"]
    assert candidate["state"] == "unavailable"
    assert candidate["reason"]
    (artifact,) = observation["artifacts"]
    assert artifact["compatibility"] == "contradiction"
    assert artifact["role_changed"] is None


def test_version_one_state_is_refused(observer_repo: Path, tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    start_segment(observer_repo, state_path=state, segment_id="s", work_type="Coding")
    saved = json.loads(state.read_text(encoding="utf-8"))
    saved["schema_version"] = 1
    _write_json(state, saved)
    with pytest.raises(ObservationError, match="unsupported observer state schema"):
        finish_segment(state)


def test_cli_returns_success_when_observation_contains_contradiction(
    observer_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    state = tmp_path / "cli-state.json"
    assert (
        main(
            [
                "start",
                "--root",
                str(observer_repo),
                "--state",
                str(state),
                "--segment-id",
                "cli-test",
                "--work-type",
                "Coding",
                "--started-at",
                "2026-09-20T10:00:00Z",
            ]
        )
        == 0
    )
    capsys.readouterr()
    (observer_repo / "docs/governance/ENGINEERING.md").write_text(
        "changed governance\n", encoding="utf-8"
    )

    assert (
        main(
            [
                "finish",
                "--state",
                str(state),
                "--ended-at",
                "2026-09-20T10:00:01Z",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["compatibility"]["contradiction"] == 1
