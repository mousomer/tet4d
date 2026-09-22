"""Policy-declared governance file classes used by quality instrumentation.

The classes describe the job a file performs. They deliberately do not encode
a score: edge-state material is assessed from observed access evidence, not
from its physical size.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

FILE_CLASSES = frozenset(
    {
        "stable_authoritative",
        "generated_derived",
        "edge_state",
        "archival_history",
    }
)
DEFAULT_FILE_CLASS = "unclassified"
EDGE_STATE_ROLES = {
    "conditional_open_work_authority",
    "restart_handoff_context",
}


def declared_file_classes(policy: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    """Return validated class declarations without deriving authority from paths.

    A policy predating the declarations, such as the frozen PR118 treatment,
    declares no class at all.  Measurement stays possible under the rules that
    produced the historical result: every path is then ``unclassified``.
    """
    surface = policy.get("governance_surface")
    raw = surface.get("file_classifications") if isinstance(surface, dict) else None
    if raw is None:
        return {}
    if not isinstance(raw, dict) or set(raw) != set(FILE_CLASSES):
        raise ValueError("governance_surface.file_classifications is invalid")
    result: dict[str, tuple[str, ...]] = {}
    for file_class, paths in raw.items():
        if not isinstance(paths, list) or any(
            not isinstance(path, str) or not path for path in paths
        ):
            raise ValueError(f"invalid {file_class} file-class paths")
        result[file_class] = tuple(paths)
    return result


def file_class_for_path(path: str, declarations: dict[str, tuple[str, ...]]) -> str:
    """Resolve an exact file or a declared directory root to its class."""
    normalized = PurePosixPath(path).as_posix()
    matches = {
        file_class
        for file_class, roots in declarations.items()
        for root in roots
        if normalized == root.rstrip("/")
        or normalized.startswith(root.rstrip("/") + "/")
    }
    if len(matches) > 1:
        raise ValueError(
            f"ambiguous governance file class for {normalized}: {sorted(matches)}"
        )
    return next(iter(matches), DEFAULT_FILE_CLASS)


def declared_edge_state_profiles(
    policy: dict[str, Any],
) -> dict[str, dict[str, object]]:
    """Read the edge-specific operational roles from machine governance.

    As with the classes, a policy that predates the profiles declares none.
    """
    surface = policy.get("governance_surface")
    raw = surface.get("edge_state_profiles") if isinstance(surface, dict) else None
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise TypeError("governance_surface.edge_state_profiles is invalid")
    expected = {"CURRENT_STATE.md", "docs/BACKLOG.md"}
    if set(raw) != expected:
        raise ValueError("edge-state profiles must cover current-state and backlog")
    result: dict[str, dict[str, object]] = {}
    for path, profile in raw.items():
        if (
            not isinstance(profile, dict)
            or set(profile) != {"operational_role", "limit_rationale"}
            or profile.get("operational_role") not in EDGE_STATE_ROLES
            or not isinstance(profile.get("limit_rationale"), list)
            or not all(
                isinstance(item, str) and item for item in profile["limit_rationale"]
            )
        ):
            raise ValueError(f"invalid edge-state profile for {path}")
        result[path] = dict(profile)
    return result
