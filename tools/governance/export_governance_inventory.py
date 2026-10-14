"""Rebuild a non-authoritative migration ledger from its immutable Git baseline.

The curated obligation rows and coverage limits remain review inputs. This
exporter certifies source/runner correspondence, not semantic completeness.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = ROOT / "docs/plans/all_repository_governance_ledger.json"
PROJECT = "config/governance/project.json"
POLICY = "config/project/policy_pack.json"
PYTHON_RUNNER = "tools/governance/validate_governance.py"
SHELL_RUNNER = "scripts/verify.sh"
COLUMNS = [
    "id",
    "normalized_statement",
    "source_anchor",
    "disposition",
    "mechanism_refs",
]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative(path: str) -> str:
    parsed = PurePosixPath(path)
    if not path or parsed.is_absolute() or ".." in parsed.parts or "\\" in path:
        raise ValueError(f"source must be a repository-relative POSIX path: {path!r}")
    return path


def _git_bytes(commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{_relative(path)}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(f"baseline does not contain source {path!r}")
    return result.stdout


def _source_span(blob: bytes, first: int, last: int) -> dict[str, Any]:
    lines = blob.splitlines(keepends=True)
    if not (1 <= first <= last <= len(lines)):
        raise ValueError(f"invalid source span {first}-{last} ({len(lines)} lines)")
    return {"lines": [first, last], "sha256": _sha(b"".join(lines[first - 1 : last]))}


def _runner_families(commit: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    blob = _git_bytes(commit, PYTHON_RUNNER)
    tree = ast.parse(blob.decode("utf-8"))
    registry = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_checks"
    )
    for node in ast.walk(registry):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "GovernanceCheck"
        ):
            continue
        family = ast.literal_eval(node.args[0])
        if family in result:
            raise ValueError(f"duplicate runner family: {family}")
        result[family] = {
            "runner": PYTHON_RUNNER,
            **_source_span(blob, node.lineno, node.end_lineno or node.lineno),
            "invocation": ast.get_source_segment(blob.decode("utf-8"), node),
        }
    blob = _git_bytes(commit, SHELL_RUNNER)
    for number, line in enumerate(blob.decode("utf-8").splitlines(), 1):
        match = re.match(r'^run_governance_step\s+"([^"]+)"\s+(.+)$', line)
        if match:
            family = match.group(1)
            if family in result:
                raise ValueError(f"duplicate runner family: {family}")
            result[family] = {
                "runner": SHELL_RUNNER,
                **_source_span(blob, number, number),
                "invocation": match.group(2),
            }
    return result


def _family_registry(
    ledger: dict[str, Any], commit: str, policy: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    owners = policy["governance_surface"]["validator_provenance"]
    families = _runner_families(commit)
    if set(families) != set(owners):
        raise ValueError("runner graph and provenance registry family sets differ")
    if set(ledger["family_coverage"]) != set(families):
        raise ValueError(
            "curated coverage notes do not match the baseline runner graph"
        )
    canonical = set(policy["authority_model"]["canonical_human_owners"].values())
    if set(owners.values()) - canonical:
        raise ValueError("family registry contains a non-canonical human owner")
    for family, declaration in families.items():
        declaration["owner_source"] = owners[family]
        declaration["registry_pointer"] = (
            f"{POLICY}#/governance_surface/validator_provenance/{family}"
        )
    return families


def _validate_row(
    row: list[Any], ids: set[str], ledger: dict[str, Any], available: set[str]
) -> None:
    if len(row) != 5:
        raise ValueError("obligation rows must match the five declared columns")
    identity, statement, _anchor, disposition, mechanisms = row
    if identity in ids or identity == "session-global-doctrine":
        raise ValueError(f"duplicate or non-portable obligation ID: {identity}")
    if not isinstance(statement, str) or not statement:
        raise ValueError(f"empty obligation statement: {identity}")
    if disposition not in ledger["dispositions"]:
        raise ValueError(f"unknown disposition for {identity}: {disposition}")
    if set(mechanisms) - available:
        raise ValueError(f"unknown mechanism reference for {identity}")


def _obligation_counts(
    ledger: dict[str, Any], families: dict[str, Any]
) -> dict[str, Any]:
    ids: set[str] = set()
    dispositions: dict[str, int] = {}
    available = set(ledger["mechanisms"]) | set(families)
    for row in ledger["obligations"]:
        _validate_row(row, ids, ledger, available)
        ids.add(row[0])
        dispositions[row[3]] = dispositions.get(row[3], 0) + 1
    return {
        "provisional_repository_entries": len(ids),
        "non_authoritative_analysis_entries": sum(
            row[2].startswith("experiment-governance:") for row in ledger["obligations"]
        ),
        "dispositions": dict(sorted(dispositions.items())),
    }


def _anchor_hashes(
    ledger: dict[str, Any], source_blobs: dict[str, bytes]
) -> dict[str, Any]:
    anchors = [row[2] for row in ledger["obligations"]]
    for decision in ledger["baseline_decisions"]:
        anchors.extend(decision["sources"])
    result: dict[str, Any] = {}
    for anchor in anchors:
        match = re.fullmatch(r"([a-z-]+):(\d+)-(\d+)", anchor)
        if not match or match.group(1) not in source_blobs:
            raise ValueError(f"invalid source anchor: {anchor}")
        key, first, last = match.group(1), int(match.group(2)), int(match.group(3))
        result[anchor] = _source_span(source_blobs[key], first, last)
    return dict(sorted(result.items()))


def _artifact_hashes(
    ledger: dict[str, Any], commit: str, source_blobs: dict[str, bytes]
) -> dict[str, str]:
    artifacts = {
        value["path"]: _sha(source_blobs[key])
        for key, value in ledger["source_catalog"].items()
    }
    for path in (PROJECT, POLICY, PYTHON_RUNNER, SHELL_RUNNER):
        artifacts[path] = _sha(_git_bytes(commit, path))
    for mechanism in ledger["mechanisms"].values():
        for path in mechanism["paths"]:
            _relative(path)
            if "/skills/" not in path:
                artifacts[path] = _sha(_git_bytes(commit, path))
    return dict(sorted(artifacts.items()))


def rebuild(ledger: dict[str, Any], source_commit: str | None = None) -> dict[str, Any]:
    if ledger.get("schema_version") != 1:
        raise ValueError("unsupported ledger schema_version")
    if ledger.get("obligation_columns") != COLUMNS:
        raise ValueError("unsupported obligation columns")
    commit = source_commit or ledger["provenance"]["baseline_commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("baseline_commit must be a full immutable Git commit ID")
    project = json.loads(_git_bytes(commit, PROJECT))
    policy = json.loads(_git_bytes(commit, POLICY))
    families = _family_registry(ledger, commit, policy)
    source_blobs = {
        key: _git_bytes(commit, value["path"])
        for key, value in ledger["source_catalog"].items()
    }
    counts = _obligation_counts(ledger, families)
    counts.update(
        authorities=len(project["authorities"]),
        routes=len(project["routes"]),
        enforcement_families=len(families),
    )
    ledger["provenance"]["baseline_commit"] = commit
    ledger["generated"] = {
        "exporter_sha256": _sha(Path(__file__).read_bytes()),
        "source_sha256": _artifact_hashes(ledger, commit, source_blobs),
        "anchor_sha256": _anchor_hashes(ledger, source_blobs),
        "counts": counts,
        "canonical_human_owners": policy["authority_model"]["canonical_human_owners"],
        "authorities": project["authorities"],
        "authority_registry_source": f"{PROJECT}#/authorities",
        "routes": project["routes"],
        "route_registry_source": f"{PROJECT}#/routes",
        "enforcement_families": dict(sorted(families.items())),
    }
    return ledger


def _inline_entries(value: Any, indent: int) -> str:
    pad = " " * indent

    def dump(item: Any) -> str:
        return json.dumps(item, ensure_ascii=False)

    if isinstance(value, dict):
        lines = [f"{pad}  {dump(key)}: {dump(item)}" for key, item in value.items()]
        braces = ("{", "}")
    else:
        lines = [f"{pad}  {dump(item)}" for item in value]
        braces = ("[", "]")
    return braces[0] + "\n" + ",\n".join(lines) + "\n" + pad + braces[1]


def render(ledger: dict[str, Any]) -> str:
    """Keep source/disposition rows compact without minifying the whole ledger."""
    rendered = json.dumps(ledger, ensure_ascii=False, indent=2) + "\n"
    blocks = [
        (ledger[key], 2)
        for key in ("source_catalog", "obligations", "mechanisms", "baseline_decisions")
    ]
    blocks.extend(
        (ledger["generated"][key], 4)
        for key in ("anchor_sha256", "authorities", "routes", "enforcement_families")
    )
    for block, indent in blocks:
        pretty = json.dumps(block, ensure_ascii=False, indent=2)
        pretty = pretty.replace("\n", "\n" + " " * indent)
        rendered = rendered.replace(pretty, _inline_entries(block, indent), 1)
    return rendered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument(
        "--source-commit", help="Explicitly select a new immutable committed baseline"
    )
    args = parser.parse_args(argv)
    try:
        original = args.ledger.read_text(encoding="utf-8")
        output = render(rebuild(json.loads(original), args.source_commit))
        if args.check:
            if original != output:
                print(
                    "governance inventory: stale metadata or non-canonical bytes",
                    file=sys.stderr,
                )
                return 1
        else:
            args.ledger.write_text(output, encoding="utf-8")
    except (KeyError, StopIteration, TypeError, ValueError, OSError) as error:
        print(f"governance inventory: {error}", file=sys.stderr)
        return 1
    print(
        "governance inventory: OK (pinned sources; semantic coverage remains review input)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
