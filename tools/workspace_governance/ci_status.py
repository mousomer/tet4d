"""One-shot pull-request CI status: exactly one GitHub request, never a wait.

``gov ci-status <pr>`` makes a single ``gh api graphql`` request and interprets
it. It never watches, refreshes, retries or sleeps. Results:

======== ==== ===========================================================
state    exit meaning
======== ==== ===========================================================
PASS     0    every check required by the gate completed successfully
FAIL     10   a required check failed, was cancelled or timed out
PENDING  11   a required check has not finished (report PENDING_EXTERNAL)
UNKNOWN  12   the check set is missing, incomplete, empty, stale or unbound
              (no visible required checks and no --require; pass
              --use-observed-set to gate on whatever checks exist)
ERROR    13   the request itself failed; no CI conclusion was observed
======== ==== ===========================================================

Exit 2 is a usage error. CI failure (10) is never conflated with command
failure (13). Only PASS is verification.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

EXIT = {"PASS": 0, "FAIL": 10, "PENDING": 11, "UNKNOWN": 12, "ERROR": 13}
TIMEOUT_SECONDS = 60
QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    nameWithOwner
    pullRequest(number: $number) {
      number state headRefName headRefOid
      commits(last: 1) { nodes { commit { oid statusCheckRollup {
        contexts(first: 100) {
          pageInfo { hasNextPage }
          nodes {
            __typename
            ... on CheckRun {
              name status conclusion isRequired(pullRequestNumber: $number)
            }
            ... on StatusContext {
              context state isRequired(pullRequestNumber: $number)
            }
          }
        }
      } } } }
    }
  }
}
"""
PASS_CONCLUSIONS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
PENDING_STATES = {
    "QUEUED",
    "IN_PROGRESS",
    "WAITING",
    "PENDING",
    "REQUESTED",
    "EXPECTED",
}
REMOTE_URL = re.compile(
    r"^(?:https://(?:[^@/]+@)?github\.com/|git@[^:]+:|ssh://git@[^/]+/)"
    r"(?P<owner>[A-Za-z0-9_.-]+)/(?P<name>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
Runner = Callable[[list[str], Path], tuple[int, str, str]]


def run(argv: list[str], cwd: Path) -> tuple[int, str, str]:
    result = subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def _repository(root: Path, declared: str | None, runner: Runner) -> str:
    if declared:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", declared):
            raise ValueError("--repo must be OWNER/NAME")
        return declared
    code, out, _ = runner(["git", "config", "--get", "remote.origin.url"], root)
    match = REMOTE_URL.match(out.strip()) if code == 0 else None
    if match is None:
        raise ValueError("cannot derive OWNER/NAME from remote.origin.url; pass --repo")
    return f"{match['owner']}/{match['name']}"


def _local_head(root: Path, runner: Runner) -> tuple[str | None, str | None]:
    code, branch, _ = runner(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"], root
    )
    sha_code, sha, _ = runner(["git", "rev-parse", "HEAD"], root)
    return (
        branch.strip() if code == 0 else None,
        sha.strip() if sha_code == 0 else None,
    )


def _bucket(node: dict) -> str:
    if node.get("__typename") == "StatusContext":
        state = node.get("state")
        if state == "SUCCESS":
            return "pass"
        return "pending" if state in PENDING_STATES else "fail"
    if node.get("status") != "COMPLETED":
        return "pending"
    return "pass" if node.get("conclusion") in PASS_CONCLUSIONS else "fail"


def _checks(commit: dict) -> tuple[list[dict], bool]:
    rollup = commit.get("statusCheckRollup") or {}
    contexts = rollup.get("contexts") or {}
    nodes = contexts.get("nodes") or []
    complete = not (contexts.get("pageInfo") or {}).get("hasNextPage", False)
    checks = [
        {
            "name": node.get("name") or node.get("context") or "",
            "required": bool(node.get("isRequired")),
            "bucket": _bucket(node),
        }
        for node in nodes
        if isinstance(node, dict) and node.get("__typename")
    ]
    return checks, complete


def interpret(
    data: dict,
    *,
    require: list[str],
    allow_zero: bool,
    expected_sha: str | None,
    use_observed_set: bool = False,
) -> dict:
    """Pure interpretation of one GraphQL response."""
    pull = (data.get("data") or {}).get("repository", {}) or {}
    pull = pull.get("pullRequest")
    if not isinstance(pull, dict):
        return _result("UNKNOWN", ["pull request not found"])
    nodes = (pull.get("commits") or {}).get("nodes") or []
    commit = (nodes[-1] or {}).get("commit") if nodes else None
    if not isinstance(commit, dict) or commit.get("oid") != pull.get("headRefOid"):
        return _result("UNKNOWN", ["head commit status unavailable"], pull)
    reasons: list[str] = []
    if expected_sha and expected_sha != pull["headRefOid"]:
        return _result("UNKNOWN", ["PR head differs from the expected SHA"], pull)
    checks, complete = _checks(commit)
    if not complete:
        reasons.append("check set truncated; result incomplete")
    gated = [c for c in checks if c["required"] or c["name"] in require]
    unbound = not any(c["required"] for c in checks) and not require
    unbound = unbound and not allow_zero
    if unbound:
        # Observed failures and pending runs still surface; PASS needs a gate.
        gated = checks
        reasons.append(
            "gate explicitly uses the observed check set"
            if use_observed_set
            else "no required checks visible and none declared (--require); "
            "required runs may not exist yet, so PASS is withheld"
        )
    missing = sorted(set(require) - {c["name"] for c in checks})
    reasons += [f"required check missing: {name}" for name in missing]
    if not gated and not allow_zero:
        reasons.append("no checks observed; zero checks is not success")
    incomplete = bool(missing) or not complete or (unbound and not use_observed_set)
    state = _aggregate(gated, incomplete or (not gated and not allow_zero))
    return _result(state, reasons, pull, checks)


def _aggregate(gated: list[dict], unknown: bool) -> str:
    buckets = {c["bucket"] for c in gated}
    if "fail" in buckets:
        return "FAIL"
    if "pending" in buckets:
        return "PENDING"
    return "UNKNOWN" if unknown else "PASS"


def _result(state: str, reasons: list[str], pull=None, checks=None) -> dict:
    pull = pull or {}
    return {
        "state": state,
        "code": "PENDING_EXTERNAL" if state == "PENDING" else None,
        "verification": state == "PASS",
        "exit_code": EXIT[state],
        "pr": pull.get("number"),
        "pr_state": pull.get("state"),
        "head_ref": pull.get("headRefName"),
        "head_sha": pull.get("headRefOid"),
        "checks": checks or [],
        "reasons": reasons,
        "next": (
            "Stop here. Do not query again until a host notification, a relevant "
            "event or a new user instruction."
            if state in {"PENDING", "UNKNOWN"}
            else None
        ),
    }


def ci_status(
    root: Path,
    pr: int,
    *,
    repo: str | None = None,
    require: list[str] | None = None,
    allow_zero: bool = False,
    expected_sha: str | None = None,
    use_observed_set: bool = False,
    runner: Runner = run,
) -> dict:
    """Make exactly one GitHub request and interpret it."""
    try:
        repository = _repository(root, repo, runner)
        branch, local_sha = _local_head(root, runner)
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        return _result("ERROR", [str(exc)])
    owner, name = repository.split("/", 1)
    argv = ["gh", "api", "graphql", "-f", f"query={QUERY}"]
    argv += ["-F", f"owner={owner}", "-F", f"name={name}", "-F", f"number={pr}"]
    try:
        code, out, err = runner(argv, root)
        data = json.loads(out) if code == 0 else None
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        return {
            **_result("ERROR", [f"request failed: {exc}"]),
            "repository": repository,
        }
    if not isinstance(data, dict) or data.get("errors"):
        reason = (err.strip() or json.dumps((data or {}).get("errors")))[:500]
        return {
            **_result("ERROR", [f"request failed: {reason}"]),
            "repository": repository,
        }
    head = ((data.get("data") or {}).get("repository") or {}).get("pullRequest") or {}
    if expected_sha is None and branch and branch == head.get("headRefName"):
        expected_sha = local_sha
    result = interpret(
        data,
        require=require or [],
        allow_zero=allow_zero,
        expected_sha=expected_sha,
        use_observed_set=use_observed_set,
    )
    return {
        **result,
        "repository": repository,
        "expected_sha": expected_sha,
        "head_sha_verified": bool(expected_sha) and expected_sha == result["head_sha"],
    }
