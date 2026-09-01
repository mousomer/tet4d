from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_REL = "config/project/policy_pack.json"
REQUIRED_ROLES = {
    "governance",
    "current_state",
    "active_task",
    "planning",
    "history",
    "architecture",
    "product_contract",
    "template",
    "generated_reference",
}
EXPECTED_OWNER_DOMAINS = {
    "engineering",
    "verification",
    "security_and_sanitation",
    "config_and_generated_data",
    "native_and_platform",
    "change_governance",
}
ACTIVE_GROUPS = ("human", "machine", "operational", "active_task")
STATIC_HUMAN_PATHS = {
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    ".github/pull_request_template.md",
    "godot/AGENTS.md",
    "native/AGENTS.md",
}
FIXED_LIMITS = {
    "AGENTS.md": 150,
    "godot/AGENTS.md": 70,
    "native/AGENTS.md": 70,
    "CURRENT_STATE.md": 150,
    "docs/BACKLOG.md": 250,
    POLICY_REL: 1000,
}
PROVENANCE_FAMILIES = {
    "contracts",
    "workspace_bundle",
    "authority_transfer",
    "config_authority",
    "godot_semantic_boundary",
    "live_board_visual_roles",
    "native_cpp_tooling",
    "menu_graph",
    "risk_gates",
    "policy_runtime_rules",
    "wheel_reuse_rules",
    "utility_reuse",
    "loc_guidance",
    "dedup_dead_code_rules",
    "drift_protection",
    "governance_surface",
    "routing_verification_floor",
    "generated_reference_integrity",
    "secret_and_path_sanitation",
}


@dataclass(frozen=True)
class SurfaceIssue:
    kind: str
    message: str


@dataclass(frozen=True)
class SurfaceMeasurement:
    human: int
    machine: int
    operational: int
    active_task: int
    total: int
    hard_limit: int
    file_loc: dict[str, int]


def _load_policy(root: Path) -> dict[str, Any]:
    payload = json.loads((root / POLICY_REL).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{POLICY_REL} must be an object")
    return payload


def _str_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return None
    return value


def _physical_loc(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _is_history_path(path: str) -> bool:
    return path == "docs/history" or path.startswith("docs/history/")


def _is_under(path: str, roots: list[str]) -> bool:
    return any(
        path == root.rstrip("/") or path.startswith(root.rstrip("/") + "/")
        for root in roots
    )


def _validate_roles(
    root: Path, surface: dict[str, Any], issues: list[SurfaceIssue]
) -> dict[str, list[str]]:
    raw = surface.get("document_roles")
    if not isinstance(raw, dict):
        issues.append(
            SurfaceIssue(
                "schema", "governance_surface.document_roles must be an object"
            )
        )
        return {}
    if set(raw) != REQUIRED_ROLES:
        issues.append(
            SurfaceIssue(
                "roles",
                "document roles must be exactly: " + ", ".join(sorted(REQUIRED_ROLES)),
            )
        )
    roles: dict[str, list[str]] = {}
    seen: dict[str, str] = {}
    for role, value in raw.items():
        paths = _str_list(value)
        if paths is None:
            issues.append(
                SurfaceIssue("schema", f"document role {role} must be list[str]")
            )
            continue
        roles[role] = paths
        for rel in paths:
            prior = seen.get(rel)
            if prior is not None:
                issues.append(
                    SurfaceIssue("roles", f"{rel} has duplicate roles: {prior}, {role}")
                )
            seen[rel] = role
            if not (root / rel).exists():
                issues.append(
                    SurfaceIssue(
                        "missing", f"registered {role} path does not exist: {rel}"
                    )
                )
    return roles


def _validate_owners(
    root: Path, policy: dict[str, Any], issues: list[SurfaceIssue]
) -> dict[str, str]:
    authority = policy.get("authority_model")
    owners = (
        authority.get("canonical_human_owners") if isinstance(authority, dict) else None
    )
    if not isinstance(owners, dict):
        issues.append(
            SurfaceIssue(
                "owners", "authority_model.canonical_human_owners must be an object"
            )
        )
        return {}
    if set(owners) != EXPECTED_OWNER_DOMAINS:
        issues.append(
            SurfaceIssue(
                "owners",
                "canonical governance domains must be exactly the six registered domains",
            )
        )
    typed = {str(key): value for key, value in owners.items() if isinstance(value, str)}
    if len(typed) != len(owners):
        issues.append(
            SurfaceIssue("owners", "every canonical owner must be a path string")
        )
    paths = list(typed.values())
    if len(paths) != len(set(paths)):
        issues.append(SurfaceIssue("owners", "canonical owner paths must be unique"))
    for rel in paths:
        if not (root / rel).is_file():
            issues.append(
                SurfaceIssue("missing", f"canonical owner does not exist: {rel}")
            )
    return typed


def _active_paths(
    surface: dict[str, Any], issues: list[SurfaceIssue]
) -> dict[str, list[str]]:
    raw = surface.get("active_governance")
    if not isinstance(raw, dict):
        issues.append(
            SurfaceIssue(
                "schema", "governance_surface.active_governance must be an object"
            )
        )
        return {}
    if set(raw) != set(ACTIVE_GROUPS):
        issues.append(
            SurfaceIssue(
                "schema",
                "active_governance must define human, machine, operational, and active_task",
            )
        )
    result: dict[str, list[str]] = {}
    seen: set[str] = set()
    for group in ACTIVE_GROUPS:
        paths = _str_list(raw.get(group))
        if paths is None:
            issues.append(
                SurfaceIssue("schema", f"active_governance.{group} must be list[str]")
            )
            continue
        result[group] = paths
        for rel in paths:
            if rel in seen:
                issues.append(
                    SurfaceIssue(
                        "surface", f"active path appears more than once: {rel}"
                    )
                )
            seen.add(rel)
    return result


def _validate_routes(  # noqa: C901 - one bounded structural route audit
    root: Path, policy: dict[str, Any], issues: list[SurfaceIssue]
) -> None:
    authority = policy.get("authority_model")
    routing = policy.get("codex_routing")
    routes = routing.get("routes") if isinstance(routing, dict) else None
    if not isinstance(authority, dict) or not isinstance(routes, dict):
        issues.append(
            SurfaceIssue(
                "routes", "authority_model and codex_routing.routes must be objects"
            )
        )
        return
    for route_id, route in routes.items():
        if not isinstance(route, dict):
            issues.append(SurfaceIssue("routes", f"route {route_id} must be an object"))
            continue
        keys = _str_list(route.get("authority_keys", []))
        dispatch = _str_list(route.get("dispatch_paths", []))
        if keys is None or dispatch is None:
            issues.append(
                SurfaceIssue("routes", f"route {route_id} paths must be list[str]")
            )
            continue
        if not keys and not dispatch:
            issues.append(
                SurfaceIssue("routes", f"route {route_id} resolves no context")
            )
        for key in keys:
            rel = authority.get(key)
            if not isinstance(rel, str) or not (root / rel).exists():
                issues.append(
                    SurfaceIssue(
                        "routes", f"route {route_id} has unresolved authority: {key}"
                    )
                )
                continue
            if _is_history_path(rel):
                issues.append(
                    SurfaceIssue("routes", f"route {route_id} enters history: {rel}")
                )
        for rel in dispatch:
            if not (root / rel).exists():
                issues.append(
                    SurfaceIssue(
                        "routes", f"route {route_id} has missing dispatch path: {rel}"
                    )
                )
            if _is_history_path(rel):
                issues.append(
                    SurfaceIssue("routes", f"route {route_id} enters history: {rel}")
                )


def _validate_lifecycle(
    root: Path,
    surface: dict[str, Any],
    active: dict[str, list[str]],
    issues: list[SurfaceIssue],
) -> None:
    lifecycle = surface.get("lifecycle")
    if not isinstance(lifecycle, dict):
        issues.append(
            SurfaceIssue("schema", "governance_surface.lifecycle must be an object")
        )
        return
    headings = _str_list(lifecycle.get("forbidden_active_heading_regex"))
    volatile = lifecycle.get("volatile_test_count_regex")
    if headings is None or not isinstance(volatile, str):
        issues.append(SurfaceIssue("schema", "lifecycle regex fields are invalid"))
        return
    scanned = (
        active.get("human", [])
        + active.get("operational", [])
        + active.get("active_task", [])
    )
    for rel in scanned:
        path = root / rel
        if not path.is_file() or path.suffix.lower() != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in headings:
            if re.search(pattern, text, flags=re.MULTILINE | re.IGNORECASE):
                issues.append(
                    SurfaceIssue(
                        "lifecycle",
                        f"active file contains append-only history heading: {rel}",
                    )
                )
                break
        if re.search(volatile, text, flags=re.MULTILINE | re.IGNORECASE):
            issues.append(
                SurfaceIssue(
                    "lifecycle", f"active file contains volatile test inventory: {rel}"
                )
            )


def validate_provenance(
    mapping: object, expected_families: set[str], owner_paths: set[str]
) -> list[SurfaceIssue]:
    if not isinstance(mapping, dict):
        return [SurfaceIssue("provenance", "validator_provenance must be an object")]
    issues: list[SurfaceIssue] = []
    keys = set(mapping)
    for family in sorted(expected_families - keys):
        issues.append(
            SurfaceIssue("provenance", f"missing validator provenance: {family}")
        )
    for family in sorted(keys - expected_families):
        issues.append(
            SurfaceIssue("provenance", f"unowned validator rule family: {family}")
        )
    for family, owner in mapping.items():
        if owner not in owner_paths:
            issues.append(
                SurfaceIssue(
                    "provenance",
                    f"validator family {family} has non-canonical owner: {owner}",
                )
            )
    return issues


def _measure(  # noqa: C901 - measurement and all coupled hard ceilings stay atomic
    root: Path,
    surface: dict[str, Any],
    active: dict[str, list[str]],
    owner_paths: set[str],
    issues: list[SurfaceIssue],
) -> SurfaceMeasurement:
    file_loc: dict[str, int] = {}
    totals = {group: 0 for group in ACTIVE_GROUPS}
    for group, paths in active.items():
        for rel in paths:
            path = root / rel
            if not path.is_file():
                issues.append(
                    SurfaceIssue(
                        "missing", f"active governance file does not exist: {rel}"
                    )
                )
                continue
            loc = _physical_loc(path)
            file_loc[rel] = loc
            totals[group] += loc
    limits = surface.get("per_file_limits")
    if not isinstance(limits, dict):
        issues.append(
            SurfaceIssue(
                "schema", "governance_surface.per_file_limits must be an object"
            )
        )
        limits = {}
    required_limits = {**FIXED_LIMITS, **{rel: 300 for rel in owner_paths}}
    for rel, expected in required_limits.items():
        if limits.get(rel) != expected:
            issues.append(
                SurfaceIssue("size", f"{rel} hard limit must equal {expected}")
            )
    for rel, limit in limits.items():
        if not isinstance(rel, str) or not isinstance(limit, int) or limit <= 0:
            issues.append(
                SurfaceIssue(
                    "schema", "per-file limits must map paths to positive integers"
                )
            )
            continue
        loc = file_loc.get(rel)
        if loc is None and (root / rel).is_file():
            loc = _physical_loc(root / rel)
            file_loc[rel] = loc
        if loc is not None and loc > limit:
            issues.append(
                SurfaceIssue("size", f"{rel}: {loc} LOC exceeds hard limit {limit}")
            )
    task_limit = surface.get("active_task_limit")
    if task_limit != 250:
        issues.append(SurfaceIssue("size", "active_task_limit must equal 250"))
    else:
        for rel in active.get("active_task", []):
            if file_loc.get(rel, 0) > task_limit:
                issues.append(
                    SurfaceIssue(
                        "size",
                        f"{rel}: {file_loc[rel]} LOC exceeds active-task limit {task_limit}",
                    )
                )
    hard_limit = surface.get("aggregate_hard_limit")
    if hard_limit != 2500:
        issues.append(SurfaceIssue("size", "aggregate_hard_limit must equal 2500"))
        hard_limit = 0
    total = sum(totals.values())
    if hard_limit and total > hard_limit:
        issues.append(
            SurfaceIssue(
                "size",
                f"active governance total {total} LOC exceeds hard limit {hard_limit}",
            )
        )
    return SurfaceMeasurement(
        human=totals["human"],
        machine=totals["machine"],
        operational=totals["operational"],
        active_task=totals["active_task"],
        total=total,
        hard_limit=hard_limit,
        file_loc=file_loc,
    )


def validate_surface(  # noqa: C901 - composes the complete surface invariant
    root: Path = ROOT, *, expected_provenance: set[str] | None = None
) -> tuple[list[SurfaceIssue], SurfaceMeasurement | None]:
    issues: list[SurfaceIssue] = []
    try:
        policy = _load_policy(root)
    except (OSError, TypeError, json.JSONDecodeError) as exc:
        return [SurfaceIssue("policy", str(exc))], None
    surface = policy.get("governance_surface")
    if not isinstance(surface, dict):
        return [SurfaceIssue("schema", "governance_surface must be an object")], None
    roles = _validate_roles(root, surface, issues)
    owners = _validate_owners(root, policy, issues)
    active = _active_paths(surface, issues)
    owner_paths = set(owners.values())
    if not owner_paths.issubset(set(active.get("human", []))):
        issues.append(
            SurfaceIssue(
                "owners", "every canonical owner must be active human governance"
            )
        )
    expected_human = STATIC_HUMAN_PATHS | owner_paths
    if set(active.get("human", [])) != expected_human:
        issues.append(
            SurfaceIssue(
                "surface",
                "active human governance must be exactly the dispatch/review surfaces and six canonical owners",
            )
        )
    if active.get("machine", []) != [POLICY_REL]:
        issues.append(
            SurfaceIssue(
                "surface", f"active machine governance must be exactly {POLICY_REL}"
            )
        )
    if set(active.get("operational", [])) != {"CURRENT_STATE.md", "docs/BACKLOG.md"}:
        issues.append(
            SurfaceIssue(
                "surface",
                "operational context must be CURRENT_STATE.md and docs/BACKLOG.md",
            )
        )
    excluded_roots = (
        roles.get("history", []) + roles.get("planning", []) + roles.get("template", [])
    )
    excluded_roots += (
        roles.get("architecture", [])
        + roles.get("product_contract", [])
        + roles.get("generated_reference", [])
    )
    for paths in active.values():
        for rel in paths:
            if _is_under(rel, excluded_roots):
                issues.append(
                    SurfaceIssue(
                        "roles", f"excluded role entered active governance: {rel}"
                    )
                )
    deprecated = policy.get("deprecated_authorities")
    blocked = (
        deprecated.get("blocked_paths", []) if isinstance(deprecated, dict) else []
    )
    active_flat = {rel for paths in active.values() for rel in paths}
    for rel in sorted(
        active_flat.intersection(blocked if isinstance(blocked, list) else [])
    ):
        issues.append(SurfaceIssue("retired", f"retired authority is active: {rel}"))
    _validate_routes(root, policy, issues)
    _validate_lifecycle(root, surface, active, issues)
    if expected_provenance is not None:
        issues.extend(
            validate_provenance(
                surface.get("validator_provenance"), expected_provenance, owner_paths
            )
        )
    measurement = _measure(root, surface, active, owner_paths, issues)
    return issues, measurement


def _base_total(root: Path, measurement: SurfaceMeasurement, ref: str) -> int | None:
    total = 0
    for rel in measurement.file_loc:
        result = subprocess.run(
            ["git", "show", f"{ref}:{rel}"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode != 0:
            return None
        total += len(result.stdout.splitlines())
    return total


def _print_report(measurement: SurfaceMeasurement, *, base_ref: str | None) -> None:
    print("Governance surface")
    print(f"Human governance:           {measurement.human:5d} LOC")
    print(f"Machine policy:             {measurement.machine:5d} LOC")
    print(f"Operational routed context: {measurement.operational:5d} LOC")
    print(f"Active task records:        {measurement.active_task:5d} LOC")
    print(f"Active governance total:    {measurement.total:5d} LOC")
    print(f"Hard limit:                 {measurement.hard_limit:5d} LOC")
    if base_ref:
        base = _base_total(ROOT, measurement, base_ref)
        delta = "unavailable" if base is None else f"{measurement.total - base:+d} LOC"
    else:
        delta = "not requested"
    print(f"Delta vs base:              {delta}")
    print("Per-file LOC:")
    for rel, loc in sorted(measurement.file_loc.items()):
        print(f"- {rel}: {loc}")
    print("Aggregate compliance is binding; per-file compliance alone is insufficient.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the active governance surface"
    )
    parser.add_argument("--base-ref", default=os.environ.get("GOVERNANCE_BASE_REF"))
    args = parser.parse_args(argv)
    issues, measurement = validate_surface(
        ROOT, expected_provenance=PROVENANCE_FAMILIES
    )
    if measurement is not None:
        _print_report(measurement, base_ref=args.base_ref)
    if issues:
        print("Governance surface validation failed:")
        for issue in issues:
            print(f"- [{issue.kind}] {issue.message}")
        return 1
    print("Governance surface validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
