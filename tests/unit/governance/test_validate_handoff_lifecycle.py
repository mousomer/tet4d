from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

import tools.governance.validate_handoff_lifecycle as lifecycle

ROOT = Path(__file__).resolve().parents[3]
CI_WORKFLOW_PATH = ROOT / ".github/workflows/ci.yml"


def _doc(
    *,
    status: str = "none",
    branch: str | None = None,
    pull_request: int | None = None,
    notes: str = "",
    schema_version: int = 1,
    raw_state: str | None = None,
) -> str:
    state = raw_state or json.dumps(
        {
            "schema_version": schema_version,
            "status": status,
            "branch": branch,
            "pull_request": pull_request,
        },
        indent=2,
    )
    return (
        "# Handoff\n\n## Active Focus\n\n"
        "<!-- BEGIN HANDOFF:state -->\n```json\n"
        f"{state}\n```\n<!-- END HANDOFF:state -->\n\n"
        f"<!-- BEGIN HANDOFF:notes -->\n{notes}\n<!-- END HANDOFF:notes -->\n"
    )


def _repo(tmp_path: Path, doc: str, *, handoff_rel: str = "HANDOFF.md") -> Path:
    root = tmp_path / "repo"
    (root / "config" / "project").mkdir(parents=True)
    (root / "config" / "project" / "policy_pack.json").write_text(
        json.dumps({"authority_model": {"handoff_doc": handoff_rel}}),
        encoding="utf-8",
    )
    (root / handoff_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / handoff_rel).write_text(doc, encoding="utf-8")
    return root


def _ctx(
    *,
    branch: str | None = "feature/x",
    event: str | None = None,
    is_draft: bool | None = None,
    pull_request: int | None = None,
    base_branch: str | None = None,
    default_branch: str = "master",
) -> lifecycle.Context:
    return lifecycle.Context(
        source="explicit",
        branch=branch,
        default_branch=default_branch,
        event=event,
        is_draft=is_draft,
        pull_request=pull_request,
        base_branch=base_branch,
    )


def _run(root: Path, ctx: lifecycle.Context) -> list[str]:
    return lifecycle.validate(root, ctx)


# --- parsing -----------------------------------------------------------------


def test_valid_none_state_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc())
    assert _run(root, _ctx(branch="master")) == []


def test_none_with_canonical_sentence_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(notes="No active handoff."))
    assert _run(root, _ctx(branch="master")) == []


def test_missing_state_block_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, "# Handoff\n\nno block\n")
    issues = _run(root, _ctx())
    assert any("exactly one HANDOFF:state block" in i for i in issues)


def test_malformed_json_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(raw_state='{"status": "none",}'))
    issues = _run(root, _ctx())
    assert any("not valid JSON" in i for i in issues)


def test_missing_notes_region_fails(tmp_path: Path) -> None:
    doc = _doc().split("<!-- BEGIN HANDOFF:notes -->")[0]
    root = _repo(tmp_path, doc)
    issues = _run(root, _ctx())
    assert any("exactly one HANDOFF:notes region" in i for i in issues)


@pytest.mark.parametrize(
    ("raw", "fragment"),
    [
        (
            '{"schema_version": 2, "status": "none", "branch": null, "pull_request": null}',
            "schema_version",
        ),
        (
            '{"schema_version": 1, "status": "done", "branch": null, "pull_request": null}',
            "status must be",
        ),
        (
            '{"schema_version": 1, "status": "none", "branch": "", "pull_request": null}',
            "branch must be null",
        ),
        (
            '{"schema_version": 1, "status": "none", "branch": null, "pull_request": 0}',
            "pull_request must be null",
        ),
        (
            '{"schema_version": 1, "status": "none", "branch": null, "pull_request": null, "extra": 1}',
            "unknown keys",
        ),
    ],
)
def test_schema_violations_fail(tmp_path: Path, raw: str, fragment: str) -> None:
    root = _repo(tmp_path, _doc(raw_state=raw))
    issues = _run(root, _ctx())
    assert any(fragment in i for i in issues), issues


# --- none state -----------------------------------------------------------------


def test_none_with_stale_branch_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(branch="codex/old"))
    assert any("must not name a branch" in i for i in _run(root, _ctx()))


def test_none_with_stale_pull_request_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(pull_request=92))
    assert any("must not name a pull request" in i for i in _run(root, _ctx()))


def test_none_with_volatile_prose_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(notes="Working state: PR 3 on codex/old"))
    assert any("HANDOFF:notes region to be empty" in i for i in _run(root, _ctx()))


# --- active state ---------------------------------------------------------------


def test_active_on_matching_local_branch_passes(tmp_path: Path) -> None:
    root = _repo(
        tmp_path, _doc(status="active", branch="feature/x", notes="Resume here.")
    )
    assert _run(root, _ctx(branch="feature/x")) == []


def test_active_on_mismatched_local_branch_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x"))
    assert any(
        "does not match the current branch" in i
        for i in _run(root, _ctx(branch="feature/y"))
    )


def test_active_on_detached_checkout_fails_explicitly(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x"))
    issues = _run(root, _ctx(branch=None))
    assert any("detached" in i for i in issues)


def test_none_on_detached_checkout_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc())
    assert _run(root, _ctx(branch=None)) == []


def test_active_naming_default_branch_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="master"))
    assert any(
        "must not name the default branch" in i
        for i in _run(root, _ctx(branch="master"))
    )


def test_active_on_default_branch_checkout_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x"))
    assert any(
        "default-branch checkout" in i for i in _run(root, _ctx(branch="master"))
    )


def test_active_without_branch_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(status="active"))
    assert any("requires a branch" in i for i in _run(root, _ctx()))


def test_draft_pr_with_matching_active_state_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x", pull_request=98))
    ctx = _ctx(
        branch="feature/x",
        event="pull_request",
        is_draft=True,
        pull_request=98,
        base_branch="master",
    )
    assert _run(root, ctx) == []


def test_draft_pr_with_mismatched_pull_request_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x", pull_request=98))
    ctx = _ctx(
        branch="feature/x",
        event="pull_request",
        is_draft=True,
        pull_request=99,
        base_branch="master",
    )
    assert any("does not match the current pull request" in i for i in _run(root, ctx))


def test_draft_pr_with_mismatched_branch_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x"))
    ctx = _ctx(
        branch="feature/y", event="pull_request", is_draft=True, base_branch="master"
    )
    assert any("does not match the current branch" in i for i in _run(root, ctx))


def test_non_draft_pr_targeting_default_with_active_state_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x"))
    ctx = _ctx(
        branch="feature/x", event="pull_request", is_draft=False, base_branch="master"
    )
    assert any(
        "non-draft pull request targeting the default branch" in i
        for i in _run(root, ctx)
    )


def test_non_draft_pr_targeting_feature_branch_with_active_state_passes(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x"))
    ctx = _ctx(
        branch="feature/x",
        event="pull_request",
        is_draft=False,
        base_branch="feature/base",
    )
    assert _run(root, ctx) == []


def test_default_branch_push_with_active_state_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x"))
    ctx = _ctx(branch="master", event="push")
    assert any("default-branch push" in i for i in _run(root, ctx))


def test_default_branch_push_with_none_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc())
    assert _run(root, _ctx(branch="master", event="push")) == []


# --- document resolution --------------------------------------------------------


def test_handoff_document_is_read_from_policy_pack(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(), handoff_rel="docs/RESUME.md")
    assert _run(root, _ctx()) == []
    assert lifecycle.handoff_document_rel(root) == "docs/RESUME.md"


def test_missing_handoff_document_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc())
    (root / "HANDOFF.md").unlink()
    assert any("missing or unreadable" in i for i in _run(root, _ctx()))


@pytest.mark.parametrize("rel", ["/abs/HANDOFF.md", "../HANDOFF.md", ""])
def test_unsafe_handoff_document_path_is_rejected(tmp_path: Path, rel: str) -> None:
    root = _repo(tmp_path, _doc())
    (root / "config" / "project" / "policy_pack.json").write_text(
        json.dumps({"authority_model": {"handoff_doc": rel}}), encoding="utf-8"
    )
    assert any("authority_model.handoff_doc" in i for i in _run(root, _ctx()))


# --- context resolution ---------------------------------------------------------


def _event_file(tmp_path: Path, payload: dict) -> str:
    path = tmp_path / "event.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_github_pull_request_context_is_read_from_event_payload(tmp_path: Path) -> None:
    env = {
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_HEAD_REF": "feature/x",
        "GITHUB_EVENT_PATH": _event_file(
            tmp_path,
            {
                "pull_request": {
                    "number": 98,
                    "draft": True,
                    "base": {"ref": "master"},
                },
                "repository": {"default_branch": "main"},
            },
        ),
    }
    ctx = lifecycle.resolve_context(
        root=tmp_path,
        env=env,
        explicit_branch=None,
        explicit_default_branch=None,
        explicit_event=None,
        explicit_draft=None,
        explicit_pull_request=None,
        explicit_base_branch=None,
    )
    assert ctx.source == "github"
    assert ctx.event == "pull_request"
    assert ctx.branch == "feature/x"
    assert ctx.is_draft is True
    assert ctx.pull_request == 98
    assert ctx.base_branch == "master"
    assert ctx.default_branch == "main"


def test_github_push_context_uses_ref_name(tmp_path: Path) -> None:
    env = {"GITHUB_EVENT_NAME": "push", "GITHUB_REF_NAME": "master"}
    ctx = lifecycle.resolve_context(
        root=tmp_path,
        env=env,
        explicit_branch=None,
        explicit_default_branch=None,
        explicit_event=None,
        explicit_draft=None,
        explicit_pull_request=None,
        explicit_base_branch=None,
    )
    assert ctx.event == "push"
    assert ctx.branch == "master"


def test_explicit_arguments_override_github_context(tmp_path: Path) -> None:
    env = {"GITHUB_EVENT_NAME": "push", "GITHUB_REF_NAME": "master"}
    ctx = lifecycle.resolve_context(
        root=tmp_path,
        env=env,
        explicit_branch="feature/x",
        explicit_default_branch=None,
        explicit_event=None,
        explicit_draft=None,
        explicit_pull_request=None,
        explicit_base_branch=None,
    )
    assert ctx.source == "explicit"
    assert ctx.branch == "feature/x"
    assert ctx.event == "push"


def test_local_git_context_reports_detached_head_as_none(tmp_path: Path) -> None:
    root = tmp_path / "git"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "trunk"], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "init",
        ],
        cwd=root,
        check=True,
    )
    ctx = lifecycle.resolve_context(
        root=root,
        env={},
        explicit_branch=None,
        explicit_default_branch=None,
        explicit_event=None,
        explicit_draft=None,
        explicit_pull_request=None,
        explicit_base_branch=None,
    )
    assert ctx.source == "git"
    assert ctx.branch == "trunk"
    subprocess.run(["git", "checkout", "-q", "--detach"], cwd=root, check=True)
    detached = lifecycle.resolve_context(
        root=root,
        env={},
        explicit_branch=None,
        explicit_default_branch=None,
        explicit_event=None,
        explicit_draft=None,
        explicit_pull_request=None,
        explicit_base_branch=None,
    )
    assert detached.branch is None


# --- CLI and output --------------------------------------------------------------


def test_cli_output_never_contains_absolute_root(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x"))
    result = lifecycle.main(["--root", str(root), "--branch", "feature/y"])
    out = capsys.readouterr().out
    assert result == 1
    assert str(root) not in out
    assert "does not match the current branch" in out


def test_cli_passes_on_valid_none(tmp_path: Path, capsys) -> None:
    root = _repo(tmp_path, _doc())
    assert lifecycle.main(["--root", str(root), "--branch", "master"]) == 0
    assert "passed" in capsys.readouterr().out


# --- repository wiring -----------------------------------------------------------


def test_live_repository_handoff_document_passes_on_default_branch() -> None:
    ctx = _ctx(branch="master", event="push")
    assert lifecycle.validate(ROOT, ctx) == []


def test_unified_governance_registers_handoff_lifecycle() -> None:
    from tools.governance import validate_governance

    assert "handoff_lifecycle" in {c.name for c in validate_governance._checks()}


def _pull_request_trigger_types(text: str) -> set[str]:
    """Collect the `types:` entries under the top-level `pull_request:` trigger."""
    lines = text.splitlines()
    try:
        start = lines.index("  pull_request:")
    except ValueError:
        return set()
    if start + 1 >= len(lines) or lines[start + 1].strip() != "types:":
        return set()
    types: set[str] = set()
    for line in lines[start + 2 :]:
        if not line.startswith("      - "):
            break
        types.add(line.strip()[2:])
    return types


def test_ci_pull_request_trigger_covers_draft_transitions() -> None:
    text = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    types = _pull_request_trigger_types(text)
    assert types, "pull_request trigger must list explicit types"
    assert {
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
        "converted_to_draft",
    } <= types


def test_ci_always_on_plan_step_runs_handoff_validator() -> None:
    text = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    step = text.split("- name: Run always-on repository contracts", 1)[1].split(
        "- name:", 1
    )[0]
    assert "tools/governance/validate_handoff_lifecycle.py" in step


def test_ci_required_gate_remains_unconditional() -> None:
    text = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    gate = text.split("  required-gate:", 1)[1].split("\n    steps:", 1)[0]
    assert re.search(r"^    if: always\(\)\s*$", gate, re.MULTILINE) is not None


# --- event classification -------------------------------------------------------


@pytest.mark.parametrize(
    "event_name",
    ["workflow_dispatch", "schedule", "workflow_call", "release", "merge_group"],
)
def test_non_push_non_pull_request_events_carry_no_lifecycle_event(
    tmp_path: Path, event_name: str
) -> None:
    env = {"GITHUB_EVENT_NAME": event_name, "GITHUB_REF_NAME": "master"}

    ctx = lifecycle.resolve_context(root=tmp_path, env=env)

    assert ctx.source == "github"
    assert ctx.event is None
    assert ctx.branch == "master"


def test_push_event_is_classified_as_push(tmp_path: Path) -> None:
    env = {"GITHUB_EVENT_NAME": "push", "GITHUB_REF_NAME": "master"}

    assert lifecycle.resolve_context(root=tmp_path, env=env).event == "push"


def test_pull_request_target_is_classified_as_pull_request(tmp_path: Path) -> None:
    env = {
        "GITHUB_EVENT_NAME": "pull_request_target",
        "GITHUB_HEAD_REF": "feature/x",
        "GITHUB_EVENT_PATH": _event_file(
            tmp_path,
            {"pull_request": {"number": 7, "draft": False, "base": {"ref": "master"}}},
        ),
    }

    ctx = lifecycle.resolve_context(root=tmp_path, env=env)

    assert ctx.event == "pull_request"
    assert ctx.is_draft is False


def test_workflow_dispatch_does_not_apply_the_push_rule(tmp_path: Path) -> None:
    """An `active` handoff must not be judged by push rules on a non-push event."""
    root = _repo(tmp_path, _doc(status="active", branch="feature/x"))
    env = {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF_NAME": "feature/x"}

    ctx = lifecycle.resolve_context(root=root, env=env)

    assert lifecycle.validate(root, ctx) == []


def test_workflow_dispatch_on_default_branch_still_rejects_active(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x"))
    env = {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF_NAME": "master"}

    ctx = lifecycle.resolve_context(root=root, env=env)

    assert any("default-branch checkout" in i for i in lifecycle.validate(root, ctx))


# --- explicit precedence --------------------------------------------------------


@pytest.mark.parametrize(
    ("kwargs", "field", "expected"),
    [
        ({"explicit_branch": "feature/x"}, "branch", "feature/x"),
        ({"explicit_default_branch": "trunk"}, "default_branch", "trunk"),
        ({"explicit_event": "pull_request"}, "event", "pull_request"),
        ({"explicit_draft": False}, "is_draft", False),
        ({"explicit_pull_request": 98}, "pull_request", 98),
        ({"explicit_base_branch": "release"}, "base_branch", "release"),
    ],
)
def test_every_explicit_argument_selects_explicit_context(
    tmp_path: Path, kwargs: dict, field: str, expected: object
) -> None:
    env = {"GITHUB_EVENT_NAME": "push", "GITHUB_REF_NAME": "master"}

    ctx = lifecycle.resolve_context(root=tmp_path, env=env, **kwargs)

    assert ctx.source == "explicit"
    assert getattr(ctx, field) == expected


def test_explicit_pull_request_alone_is_honoured_against_github_context(
    tmp_path: Path,
) -> None:
    env = {
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_HEAD_REF": "feature/x",
        "GITHUB_EVENT_PATH": _event_file(
            tmp_path,
            {"pull_request": {"number": 12, "draft": True, "base": {"ref": "master"}}},
        ),
    }

    ctx = lifecycle.resolve_context(root=tmp_path, env=env, explicit_pull_request=98)

    assert ctx.pull_request == 98
    assert ctx.branch == "feature/x"
    assert ctx.is_draft is True


def test_explicit_default_branch_overrides_event_payload(tmp_path: Path) -> None:
    env = {
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REF_NAME": "trunk",
        "GITHUB_EVENT_PATH": _event_file(
            tmp_path, {"repository": {"default_branch": "main"}}
        ),
    }

    ctx = lifecycle.resolve_context(
        root=tmp_path, env=env, explicit_default_branch="trunk"
    )

    assert ctx.default_branch == "trunk"


def test_explicit_draft_alone_changes_the_verdict(tmp_path: Path) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x"))
    env = {
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_HEAD_REF": "feature/x",
        "GITHUB_EVENT_PATH": _event_file(
            tmp_path,
            {"pull_request": {"number": 3, "draft": True, "base": {"ref": "master"}}},
        ),
    }

    draft_ctx = lifecycle.resolve_context(root=root, env=env)
    ready_ctx = lifecycle.resolve_context(root=root, env=env, explicit_draft=False)

    assert lifecycle.validate(root, draft_ctx) == []
    assert any(
        "non-draft pull request" in i for i in lifecycle.validate(root, ready_ctx)
    )


def test_cli_accepts_pull_request_without_branch_or_event(
    tmp_path: Path, capsys
) -> None:
    root = _repo(tmp_path, _doc(status="active", branch="feature/x", pull_request=98))

    result = lifecycle.main(
        ["--root", str(root), "--branch", "feature/x", "--pull-request", "99"]
    )

    assert result == 1
    assert "does not match the current pull request" in capsys.readouterr().out
