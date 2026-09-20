from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.governance.observe_work_segment import (
    ARTIFACT_ROLES,
    WORK_TYPES,
    ObservationError,
    build_role_index,
    classify_changes,
    compatibility,
    finish_segment,
    main,
    start_segment,
    validate_work_type,
)


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
            "governance_pack": {
                "lock": "config/governance/workspace.lock.json",
            }
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
            ],
            "routes": {
                "example": {"dispatch_paths": ["routed/only.txt"]},
            },
            "generated_surfaces": [
                {"target": "generated/reference.json#/value"},
            ],
        },
    )
    _write_json(
        root / "tools/workspace_governance/MANIFEST.json",
        {
            "artifact_roles": [
                {"path": "MANIFEST.json", "role": "executable_machinery"},
                {"path": "worker.py", "role": "executable_machinery"},
            ]
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


def test_work_type_vocabulary_is_exact_and_unknown_is_rejected() -> None:
    assert WORK_TYPES == ("Planning", "Coding", "Manifest")
    for work_type in WORK_TYPES:
        assert validate_work_type(work_type) == work_type
    for unknown in ("Meta", "Mixed", "Verification", "Unknown"):
        with pytest.raises(ObservationError, match="work_type"):
            validate_work_type(unknown)


def test_role_vocabulary_is_exact() -> None:
    assert ARTIFACT_ROLES == (
        "governance_treatment",
        "executable_machinery",
        "product_authority",
        "planning_document",
        "generated",
        "bookkeeping",
    )


def test_role_resolution_preserves_explicit_bootstrap_and_unknown_provenance(
    observer_repo: Path,
) -> None:
    roles = build_role_index(observer_repo)

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
    assert roles.resolve("docs/rds/feature.md").role == "product_authority"
    assert roles.resolve("docs/BACKLOG.md").role == "bookkeeping"
    assert roles.resolve("generated/reference.json").role == "generated"

    unknown = roles.resolve("src/unknown.py")
    assert unknown.to_dict() == {
        "role": "unclassified",
        "role_provenance": "unclassified",
        "role_source": None,
    }


def test_dispatch_paths_do_not_determine_or_change_artifact_role(
    observer_repo: Path,
) -> None:
    before = build_role_index(observer_repo)
    assert before.resolve("routed/only.txt").role == "unclassified"
    assert before.resolve("godot/AGENTS.md").role == "governance_treatment"

    project_path = observer_repo / "config/governance/project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["routes"]["example"]["dispatch_paths"] = ["src/unknown.py"]
    _write_json(project_path, project)

    after = build_role_index(observer_repo)
    assert after.resolve("routed/only.txt").role == "unclassified"
    assert after.resolve("src/unknown.py").role == "unclassified"
    assert after.resolve("godot/AGENTS.md").role == "governance_treatment"


@pytest.mark.parametrize(
    ("work_type", "compatible_role", "contradictory_role"),
    [
        ("Planning", "product_authority", "executable_machinery"),
        ("Coding", "executable_machinery", "governance_treatment"),
        ("Manifest", "governance_treatment", "product_authority"),
    ],
)
def test_compatibility_has_positive_and_negative_examples_for_every_work_type(
    work_type: str,
    compatible_role: str,
    contradictory_role: str,
) -> None:
    assert compatibility(work_type, compatible_role) == "compatible"
    assert compatibility(work_type, contradictory_role) == "contradiction"
    assert compatibility(work_type, "unclassified") == "unclassified"


def test_change_classification_reports_created_modified_deleted_and_renamed() -> None:
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
    assert coding["observer_mode"] == "log_only"
    assert coding["authoritative"] is False
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
