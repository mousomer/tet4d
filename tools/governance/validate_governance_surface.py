from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.governance.policy_pack_io import PolicyPackError, load_policy_pack

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
REQUIRED_FILE_CLASSES = {
    "stable_authoritative",
    "generated_derived",
    "edge_state",
    "archival_history",
}
EDGE_STATE_PATHS = {"CURRENT_STATE.md", "docs/BACKLOG.md"}
EDGE_STATE_ROLES = {
    "conditional_open_work_authority",
    "restart_handoff_context",
}
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
    "docs/BACKLOG.md": 300,
}
POLICY_PACK_ADVISORY_BYTE_LIMIT = 80 * 1024
POLICY_PACK_BYTE_LIMIT = 96 * 1024
CANONICAL_SERIALIZATION = {
    "tool": "tools/governance/policy_pack_io.py",
    "format_version": 1,
    "check_argument": "--check",
    "newline_terminated": True,
}
SHELL_GOVERNANCE_STEP = re.compile(
    r'^\s*run_governance_step\s+"([a-z][a-z0-9_]*)"(?=\s|$)', re.MULTILINE
)


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
    policy_bytes: int
    policy_advisory_byte_limit: int
    policy_byte_limit: int
    policy_exceeds_advisory: bool
    policy_nodes: int
    policy_leaves: int
    policy_max_depth: int
    largest_policy_section_bytes: int
    file_loc: dict[str, int]


def _load_policy(root: Path) -> dict[str, Any]:
    return load_policy_pack(root / POLICY_REL)


def discover_enforcement_families(root: Path = ROOT) -> set[str]:
    """Derive provenance families from the actual Python and shell call graph."""
    from tools.governance import validate_governance

    families = {check.name for check in validate_governance._checks()}
    verify_path = root / "scripts/verify.sh"
    try:
        verify_text = verify_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PolicyPackError(f"cannot inspect governance call graph: {exc}") from exc
    shell_families = set(SHELL_GOVERNANCE_STEP.findall(verify_text))
    if not shell_families:
        raise PolicyPackError(
            "scripts/verify.sh registers no run_governance_step invocations"
        )
    return families | shell_families


def _str_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return None
    return value


def physical_loc_of(text: str) -> int:
    """Count physical lines. Shared so every producer measures LOC identically."""
    return len(text.splitlines())


def _physical_loc(path: Path) -> int:
    return physical_loc_of(path.read_text(encoding="utf-8"))


def policy_structure_metrics(value: object, depth: int = 0) -> tuple[int, int, int]:
    """Return node count, leaf count and maximum nesting for a JSON value.

    Shared so every producer measures structure identically. A scalar is one
    node and one leaf; changing that silently shifts every recorded node count.
    """
    if isinstance(value, (dict, list)):
        items = value.values() if isinstance(value, dict) else value
        measured = [policy_structure_metrics(item, depth + 1) for item in items]
        return (
            1 + sum(item[0] for item in measured),
            sum(item[1] for item in measured),
            max([depth, *(item[2] for item in measured)]),
        )
    return 1, 1, depth


def _is_history_path(path: str) -> bool:
    return path == "docs/history" or path.startswith("docs/history/")


def _is_under(path: str, roots: list[str]) -> bool:
    return any(
        path == root.rstrip("/") or path.startswith(root.rstrip("/") + "/")
        for root in roots
    )


def _role_for_path(path: str, roles: dict[str, list[str]]) -> str | None:
    matches = [
        (len(root.rstrip("/")), role)
        for role, roots in roles.items()
        for root in roots
        if path == root.rstrip("/") or path.startswith(root.rstrip("/") + "/")
    ]
    return max(matches)[1] if matches else None


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


def _validate_file_classifications(  # noqa: C901 - validates one policy declaration
    surface: dict[str, Any], active: dict[str, list[str]], issues: list[SurfaceIssue]
) -> None:
    """Keep edge roles authoritative without turning their size into a score."""
    classes = surface.get("file_classifications")
    if not isinstance(classes, dict) or set(classes) != REQUIRED_FILE_CLASSES:
        issues.append(
            SurfaceIssue("schema", "file_classifications must define all file classes")
        )
        return
    declared: dict[str, set[str]] = {}
    for file_class, paths in classes.items():
        if not isinstance(paths, list) or any(
            not isinstance(path, str) or not path for path in paths
        ):
            issues.append(
                SurfaceIssue("schema", f"file class {file_class} must be list[str]")
            )
            continue
        declared[file_class] = set(paths)
    if declared.get("edge_state") != EDGE_STATE_PATHS:
        issues.append(
            SurfaceIssue(
                "classification", "edge_state must be current-state and backlog"
            )
        )
    if not EDGE_STATE_PATHS.issubset(set(active.get("operational", []))):
        issues.append(
            SurfaceIssue("classification", "edge-state files must remain operational")
        )
    profiles = surface.get("edge_state_profiles")
    if not isinstance(profiles, dict) or set(profiles) != EDGE_STATE_PATHS:
        issues.append(
            SurfaceIssue(
                "schema", "edge_state_profiles must cover current-state and backlog"
            )
        )
        return
    for path, profile in profiles.items():
        if (
            not isinstance(profile, dict)
            or set(profile) != {"operational_role", "limit_rationale"}
            or profile.get("operational_role") not in EDGE_STATE_ROLES
            or not isinstance(profile.get("limit_rationale"), list)
            or not all(
                isinstance(item, str) and item for item in profile["limit_rationale"]
            )
        ):
            issues.append(SurfaceIssue("schema", f"invalid edge-state profile: {path}"))
    if (
        profiles.get("CURRENT_STATE.md", {}).get("operational_role")
        != "restart_handoff_context"
    ):
        issues.append(
            SurfaceIssue(
                "classification", "current-state must be restart/handoff context"
            )
        )
    if (
        profiles.get("docs/BACKLOG.md", {}).get("operational_role")
        != "conditional_open_work_authority"
    ):
        issues.append(
            SurfaceIssue(
                "classification", "backlog must be conditional open-work authority"
            )
        )


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
    # Physical lines bound the material people must review as prose. The compact,
    # canonically serialized machine policy has its own byte ceiling below.
    total = sum(totals[group] for group in ACTIVE_GROUPS if group != "machine")
    if hard_limit and total > hard_limit:
        issues.append(
            SurfaceIssue(
                "size",
                f"reviewable governance total {total} LOC exceeds hard limit {hard_limit}",
            )
        )
    byte_limits = surface.get("machine_policy_byte_limits")
    expected_byte_limits = {
        "advisory": POLICY_PACK_ADVISORY_BYTE_LIMIT,
        "hard_ceiling": POLICY_PACK_BYTE_LIMIT,
        "status": "temporary_provisional_operational_ceiling",
    }
    if byte_limits != expected_byte_limits:
        issues.append(
            SurfaceIssue(
                "size",
                f"machine_policy_byte_limits must equal {expected_byte_limits}",
            )
        )
    if surface.get("canonical_serialization") != CANONICAL_SERIALIZATION:
        issues.append(
            SurfaceIssue(
                "format",
                "canonical_serialization must identify the canonical policy-pack tool",
            )
        )
    policy_path = root / POLICY_REL
    policy_bytes = len(policy_path.read_bytes()) if policy_path.is_file() else 0
    policy_exceeds_advisory = policy_bytes > POLICY_PACK_ADVISORY_BYTE_LIMIT
    policy = _load_policy(root)
    policy_nodes, policy_leaves, policy_max_depth = policy_structure_metrics(policy)
    largest_policy_section_bytes = max(
        (
            len(json.dumps(value, ensure_ascii=False).encode("utf-8"))
            for value in policy.values()
        ),
        default=0,
    )
    if policy_bytes > POLICY_PACK_BYTE_LIMIT:
        issues.append(
            SurfaceIssue(
                "size",
                f"{POLICY_REL}: {policy_bytes} bytes exceeds hard limit "
                f"{POLICY_PACK_BYTE_LIMIT}",
            )
        )
    return SurfaceMeasurement(
        human=totals["human"],
        machine=totals["machine"],
        operational=totals["operational"],
        active_task=totals["active_task"],
        total=total,
        hard_limit=hard_limit,
        policy_bytes=policy_bytes,
        policy_advisory_byte_limit=POLICY_PACK_ADVISORY_BYTE_LIMIT,
        policy_byte_limit=POLICY_PACK_BYTE_LIMIT,
        policy_exceeds_advisory=policy_exceeds_advisory,
        policy_nodes=policy_nodes,
        policy_leaves=policy_leaves,
        policy_max_depth=policy_max_depth,
        largest_policy_section_bytes=largest_policy_section_bytes,
        file_loc=file_loc,
    )


def validate_surface(  # noqa: C901 - composes the complete surface invariant
    root: Path = ROOT, *, expected_provenance: set[str] | None = None
) -> tuple[list[SurfaceIssue], SurfaceMeasurement | None]:
    issues: list[SurfaceIssue] = []
    try:
        policy = _load_policy(root)
    except (OSError, PolicyPackError) as exc:
        return [SurfaceIssue("policy", str(exc))], None
    surface = policy.get("governance_surface")
    if not isinstance(surface, dict):
        return [SurfaceIssue("schema", "governance_surface must be an object")], None
    roles = _validate_roles(root, surface, issues)
    owners = _validate_owners(root, policy, issues)
    active = _active_paths(surface, issues)
    _validate_file_classifications(surface, active, issues)
    owner_paths = set(owners.values())
    authority = policy.get("authority_model")
    topology_authority = (
        authority.get("topology_current_authority")
        if isinstance(authority, dict)
        else None
    )
    if (
        not isinstance(topology_authority, str)
        or _role_for_path(topology_authority, roles) != "architecture"
    ):
        issues.append(
            SurfaceIssue(
                "roles",
                "topology_current_authority must resolve to the architecture role",
            )
        )
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
    if expected_provenance is None:
        try:
            expected_provenance = discover_enforcement_families(root)
        except PolicyPackError as exc:
            issues.append(SurfaceIssue("provenance", str(exc)))
            expected_provenance = set()
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
        if rel == POLICY_REL:
            continue
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
    print(f"Reviewable governance total:{measurement.total:5d} LOC")
    print(f"Hard limit:                 {measurement.hard_limit:5d} LOC")
    print(
        f"Machine policy bytes:       {measurement.policy_bytes:5d} / "
        f"{measurement.policy_advisory_byte_limit} advisory / "
        f"{measurement.policy_byte_limit} hard"
    )
    if measurement.policy_exceeds_advisory:
        advisory_kib = measurement.policy_advisory_byte_limit / 1024
        print(
            "ADVISORY: machine policy exceeds provisional "
            f"{measurement.policy_advisory_byte_limit}-byte "
            f"({advisory_kib:g} KiB) review threshold"
        )
    print(
        "Machine policy structure:   "
        f"{measurement.policy_nodes} nodes, {measurement.policy_leaves} leaves, "
        f"depth {measurement.policy_max_depth}, "
        f"largest section {measurement.largest_policy_section_bytes} bytes"
    )
    if base_ref:
        base = _base_total(ROOT, measurement, base_ref)
        delta = "unavailable" if base is None else f"{measurement.total - base:+d} LOC"
    else:
        delta = "not requested"
    print(f"Delta vs base:              {delta}")
    print("Per-file LOC:")
    for rel, loc in sorted(measurement.file_loc.items()):
        print(f"- {rel}: {loc}")
    print(
        "Safety limits are binding; structural measurements inform experimental governability calibration."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the active governance surface"
    )
    parser.add_argument("--base-ref", default=os.environ.get("GOVERNANCE_BASE_REF"))
    args = parser.parse_args(argv)
    issues, measurement = validate_surface(ROOT)
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
