"""Validate the machine-readable handoff state in the repository handoff document.

The handoff document carries a delimited JSON state block and a delimited
volatile notes region. This validator enforces that ``active`` handoff state
never lands on the default branch or on a non-draft pull request that targets
it, and that ``none`` state carries no stale branch, pull-request, or prose.

Context resolution order (first usable source wins):

1. explicit command-line arguments;
2. GitHub Actions event variables and the event payload file;
3. the local Git checkout.

The validator never contacts the network and never prints absolute paths.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PACK_REL = "config/project/policy_pack.json"
DEFAULT_BRANCH_FALLBACK = "master"
SCHEMA_VERSION = 1
STATUS_NONE = "none"
STATUS_ACTIVE = "active"
NO_ACTIVE_HANDOFF_SENTENCE = "No active handoff."

STATE_BLOCK = re.compile(
    r"<!-- BEGIN HANDOFF:state -->\s*```json\s*(?P<json>\{.*?\})\s*```\s*"
    r"<!-- END HANDOFF:state -->",
    re.DOTALL,
)
NOTES_BLOCK = re.compile(
    r"<!-- BEGIN HANDOFF:notes -->(?P<notes>.*?)<!-- END HANDOFF:notes -->",
    re.DOTALL,
)


@dataclass(frozen=True)
class HandoffState:
    status: str
    branch: str | None
    pull_request: int | None


@dataclass(frozen=True)
class Context:
    """Where the validation is running, resolved without network access."""

    source: str  # "explicit" | "github" | "git" | "unknown"
    branch: str | None
    default_branch: str
    event: str | None  # "pull_request" | "push" | None
    is_draft: bool | None
    pull_request: int | None
    base_branch: str | None
    issues: tuple[str, ...] = ()


def parse_document(text: str) -> tuple[HandoffState | None, str | None, list[str]]:
    """Return (state, notes, issues) parsed from the handoff document text."""
    issues: list[str] = []
    state_matches = STATE_BLOCK.findall(text)
    if len(state_matches) != 1:
        issues.append(
            f"handoff document must contain exactly one HANDOFF:state block "
            f"(found {len(state_matches)})"
        )
        return None, None, issues
    try:
        payload = json.loads(state_matches[0])
    except json.JSONDecodeError as exc:
        issues.append(f"HANDOFF:state block is not valid JSON: {exc.msg}")
        return None, None, issues
    state = _parse_state(payload, issues)

    notes_matches = NOTES_BLOCK.findall(text)
    if len(notes_matches) != 1:
        issues.append(
            f"handoff document must contain exactly one HANDOFF:notes region "
            f"(found {len(notes_matches)})"
        )
        return state, None, issues
    return state, notes_matches[0], issues


def _parse_state(payload: Any, issues: list[str]) -> HandoffState | None:
    if not isinstance(payload, dict):
        issues.append("HANDOFF:state must be a JSON object")
        return None
    allowed = {"schema_version", "status", "branch", "pull_request"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        issues.append(f"HANDOFF:state has unknown keys: {', '.join(unknown)}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        issues.append(f"HANDOFF:state.schema_version must be {SCHEMA_VERSION}")
    status = payload.get("status")
    if status not in {STATUS_NONE, STATUS_ACTIVE}:
        issues.append(
            f"HANDOFF:state.status must be '{STATUS_NONE}' or '{STATUS_ACTIVE}'"
        )
        return None
    branch = payload.get("branch")
    if branch is not None and (not isinstance(branch, str) or not branch.strip()):
        issues.append("HANDOFF:state.branch must be null or a non-empty string")
        branch = None
    pull_request = payload.get("pull_request")
    if pull_request is not None and (
        isinstance(pull_request, bool)
        or not isinstance(pull_request, int)
        or pull_request <= 0
    ):
        issues.append("HANDOFF:state.pull_request must be null or a positive integer")
        pull_request = None
    return HandoffState(status=status, branch=branch, pull_request=pull_request)


def validate_state(
    state: HandoffState, notes: str | None, context: Context
) -> list[str]:
    """Apply the lifecycle rules for ``state`` under ``context``."""
    if state.status == STATUS_NONE:
        return _validate_none(state, notes)
    return _validate_active(state, context)


def _validate_none(state: HandoffState, notes: str | None) -> list[str]:
    issues: list[str] = []
    if state.branch is not None:
        issues.append("status 'none' must not name a branch")
    if state.pull_request is not None:
        issues.append("status 'none' must not name a pull request")
    if notes is not None:
        stripped = notes.strip()
        if stripped and stripped != NO_ACTIVE_HANDOFF_SENTENCE:
            issues.append(
                "status 'none' requires the HANDOFF:notes region to be empty "
                f"or exactly '{NO_ACTIVE_HANDOFF_SENTENCE}'"
            )
    return issues


def _active_context_block(state: HandoffState, context: Context) -> str | None:
    """Return the reason ``active`` state is forbidden in this context, if any."""
    default = context.default_branch
    if state.branch is None:
        return "status 'active' requires a branch"
    if state.branch == default:
        return f"status 'active' must not name the default branch '{default}'"
    if context.event == "push" and context.branch == default:
        return "default-branch push must carry handoff status 'none'"
    if (
        context.event == "pull_request"
        and context.is_draft is False
        and context.base_branch == default
    ):
        return (
            "non-draft pull request targeting the default branch must carry "
            "handoff status 'none'"
        )
    if context.branch is None:
        return (
            "status 'active' requires a resolvable branch: checkout is detached "
            "and no explicit or CI branch context is available"
        )
    if context.branch == default:
        return "default-branch checkout must carry handoff status 'none'"
    return None


def _validate_active(state: HandoffState, context: Context) -> list[str]:
    blocker = _active_context_block(state, context)
    if blocker is not None:
        return [blocker]
    issues: list[str] = []
    if context.branch != state.branch:
        issues.append(
            f"handoff branch '{state.branch}' does not match the current branch "
            f"'{context.branch}'"
        )
    if (
        state.pull_request is not None
        and context.pull_request is not None
        and state.pull_request != context.pull_request
    ):
        issues.append(
            f"handoff pull request {state.pull_request} does not match the "
            f"current pull request {context.pull_request}"
        )
    return issues


def _load_event_payload(
    env: dict[str, str],
) -> tuple[dict[str, Any] | None, str | None]:
    path_text = env.get("GITHUB_EVENT_PATH")
    if not path_text:
        return None, "requires GITHUB_EVENT_PATH"
    try:
        payload = json.loads(Path(path_text).read_text(encoding="utf-8"))
    except OSError:
        return None, "could not read its event payload"
    except json.JSONDecodeError:
        return None, "event payload is not valid JSON"
    if not isinstance(payload, dict):
        return None, "event payload root must be a JSON object"
    return payload, None


def _pull_request_context(
    env: dict[str, str], payload: dict[str, Any], default_branch: str
) -> Context:
    pr = payload.get("pull_request")
    issues: list[str] = []
    if not isinstance(pr, dict):
        issues.append("requires pull_request to be a JSON object")
        pr = {}
    base = pr.get("base")
    base_ref = base.get("ref") if isinstance(base, dict) else None
    draft = pr.get("draft")
    number = pr.get("number")
    branch = env.get("GITHUB_HEAD_REF")
    if not isinstance(draft, bool):
        issues.append("requires pull_request.draft to be a JSON boolean")
    if not isinstance(base_ref, str) or not base_ref.strip():
        issues.append("requires pull_request.base.ref to be a non-empty string")
    if not isinstance(branch, str) or not branch.strip():
        issues.append("requires GITHUB_HEAD_REF")
    if number is not None and (
        isinstance(number, bool) or not isinstance(number, int) or number <= 0
    ):
        issues.append("pull_request.number must be a positive integer when present")
    return Context(
        source="github",
        branch=branch.strip() if isinstance(branch, str) and branch.strip() else None,
        default_branch=default_branch,
        event="pull_request",
        is_draft=draft if isinstance(draft, bool) else None,
        pull_request=number
        if isinstance(number, int) and not isinstance(number, bool)
        else None,
        base_branch=base_ref.strip()
        if isinstance(base_ref, str) and base_ref.strip()
        else None,
        issues=tuple(f"GitHub pull-request context {issue}" for issue in issues),
    )


def _github_context(env: dict[str, str], default_branch: str) -> Context | None:
    """Classify the GitHub event exhaustively.

    Only ``push`` and the pull-request events carry lifecycle meaning. Every
    other event (``workflow_dispatch``, ``schedule``, ``workflow_call``, ...)
    resolves to ``event=None`` so that no push or pull-request rule is applied
    to an event that never occurred.
    """
    event = env.get("GITHUB_EVENT_NAME")
    if not event:
        return None
    payload, payload_issue = _load_event_payload(env)
    if event in {"pull_request", "pull_request_target"} and payload_issue is not None:
        return Context(
            source="github",
            branch=None,
            default_branch=default_branch,
            event="pull_request",
            is_draft=None,
            pull_request=None,
            base_branch=None,
            issues=(f"GitHub pull-request context {payload_issue}",),
        )
    payload = payload or {}
    repo = payload.get("repository")
    if isinstance(repo, dict) and isinstance(repo.get("default_branch"), str):
        default_branch = repo["default_branch"]
    if event in {"pull_request", "pull_request_target"}:
        return _pull_request_context(env, payload, default_branch)
    return Context(
        source="github",
        branch=env.get("GITHUB_REF_NAME") or None,
        default_branch=default_branch,
        event="push" if event == "push" else None,
        is_draft=None,
        pull_request=None,
        base_branch=None,
    )


def _git_branch(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "symbolic-ref", "--short", "-q", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    name = result.stdout.strip()
    return name or None


def resolve_context(
    *,
    root: Path,
    env: dict[str, str],
    explicit_branch: str | None = None,
    explicit_default_branch: str | None = None,
    explicit_event: str | None = None,
    explicit_draft: bool | None = None,
    explicit_pull_request: int | None = None,
    explicit_base_branch: str | None = None,
) -> Context:
    """Resolve context from explicit arguments, then GitHub event, then git.

    Every explicit argument participates in the precedence test: supplying any
    one of them selects explicit mode, and each unset field falls back to the
    GitHub event context when present and to the local checkout otherwise.
    """
    explicit_fields = (
        explicit_branch,
        explicit_default_branch,
        explicit_event,
        explicit_draft,
        explicit_pull_request,
        explicit_base_branch,
    )
    default_branch = explicit_default_branch or DEFAULT_BRANCH_FALLBACK
    base = _github_context(env, default_branch)
    if base is None:
        base = Context(
            source="git",
            branch=_git_branch(root),
            default_branch=default_branch,
            event=None,
            is_draft=None,
            pull_request=None,
            base_branch=None,
        )
    if all(field is None for field in explicit_fields):
        return base

    def pick(explicit: Any, fallback: Any) -> Any:
        return explicit if explicit is not None else fallback

    return Context(
        source="explicit",
        branch=pick(explicit_branch, base.branch),
        default_branch=explicit_default_branch or base.default_branch,
        event=pick(explicit_event, base.event),
        is_draft=pick(explicit_draft, base.is_draft),
        pull_request=pick(explicit_pull_request, base.pull_request),
        base_branch=pick(explicit_base_branch, base.base_branch),
    )


def handoff_document_rel(root: Path) -> str | None:
    """Read the handoff document path from the policy pack's authority model."""
    try:
        payload = json.loads((root / POLICY_PACK_REL).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    authority = payload.get("authority_model") if isinstance(payload, dict) else None
    rel = authority.get("handoff_doc") if isinstance(authority, dict) else None
    resolved, _issue = _repository_relative_handoff_path(root, rel)
    return resolved


def _repository_relative_handoff_path(
    root: Path, candidate: object
) -> tuple[str | None, str | None]:
    """Return a safe relative document name without exposing rejected input."""
    if not isinstance(candidate, str) or not candidate.strip():
        return None, "must name a repository-relative handoff document"
    rel = candidate.strip()
    windows = PureWindowsPath(rel)
    if (
        Path(rel).is_absolute()
        or windows.is_absolute()
        or windows.drive
        or chr(92) in rel
        or ".." in rel.split("/")
    ):
        return None, "must name a repository-relative handoff document"
    resolved_root = root.resolve()
    resolved_candidate = (resolved_root / rel).resolve()
    if not resolved_candidate.is_relative_to(resolved_root):
        return None, "must name a repository-relative handoff document"
    return resolved_candidate.relative_to(resolved_root).as_posix(), None


def _configured_handoff_document_rel(root: Path) -> tuple[str | None, str | None]:
    try:
        payload = json.loads((root / POLICY_PACK_REL).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return (
            None,
            f"{POLICY_PACK_REL} authority_model.handoff_doc must name a repository-relative handoff document",
        )
    authority = payload.get("authority_model") if isinstance(payload, dict) else None
    rel = authority.get("handoff_doc") if isinstance(authority, dict) else None
    resolved, issue = _repository_relative_handoff_path(root, rel)
    if issue is not None:
        return None, f"{POLICY_PACK_REL} authority_model.handoff_doc {issue}"
    return resolved, None


def validate(
    root: Path, context: Context, *, handoff_rel: str | None = None
) -> list[str]:
    issues = list(context.issues)
    if handoff_rel is None:
        rel, path_issue = _configured_handoff_document_rel(root)
    else:
        rel, path_issue = _repository_relative_handoff_path(root, handoff_rel)
    if path_issue is not None:
        return [*issues, path_issue]
    assert rel is not None
    try:
        text = (root / rel).read_text(encoding="utf-8")
    except OSError:
        return [*issues, f"handoff document {rel} is missing or unreadable"]
    state, notes, document_issues = parse_document(text)
    if state is None:
        return [*issues, *(f"{rel}: {issue}" for issue in document_issues)]
    document_issues.extend(validate_state(state, notes, context))
    return [*issues, *(f"{rel}: {issue}" for issue in document_issues)]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--handoff-doc", default=None)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--default-branch", default=None)
    parser.add_argument("--event", choices=["pull_request", "push"], default=None)
    draft = parser.add_mutually_exclusive_group()
    draft.add_argument("--draft", dest="draft", action="store_true", default=None)
    draft.add_argument("--not-draft", dest="draft", action="store_false")
    parser.add_argument("--pull-request", type=int, default=None)
    parser.add_argument("--base-branch", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.root.resolve()
    context = resolve_context(
        root=root,
        env=dict(os.environ),
        explicit_branch=args.branch,
        explicit_default_branch=args.default_branch,
        explicit_event=args.event,
        explicit_draft=args.draft,
        explicit_pull_request=args.pull_request,
        explicit_base_branch=args.base_branch,
    )
    issues = validate(root, context, handoff_rel=args.handoff_doc)
    if issues:
        print("Handoff lifecycle validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    branch = context.branch or "(detached)"
    print(
        f"Handoff lifecycle validation passed "
        f"(context={context.source}, branch={branch})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
