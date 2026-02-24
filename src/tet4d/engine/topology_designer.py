from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .project_config import project_root_path, topology_profile_export_file_default_path
from .topology import (
    EDGE_BOUNDED,
    AxisEdgeRule,
    EdgeRules,
    default_edge_rules_for_mode,
    normalize_edge_behavior,
    normalize_topology_mode,
)


_DESIGNER_PRESETS_FILE = (
    project_root_path() / "config" / "topology" / "designer_presets.json"
)
_PROFILE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_AXIS_NAMES = ("x", "y", "z", "w")
_AXIS_TO_INDEX = {axis_name: idx for idx, axis_name in enumerate(_AXIS_NAMES)}


@dataclass(frozen=True)
class TopologyDesignerProfile:
    profile_id: str
    label: str
    description: str
    mode_override: str | None
    axis_edges: dict[int, AxisEdgeRule]


def _read_json_payload(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _axis_index_from_key(raw_key: object) -> int | None:
    if not isinstance(raw_key, str):
        return None
    key = raw_key.strip().lower()
    if key in _AXIS_TO_INDEX:
        return _AXIS_TO_INDEX[key]
    if key.isdigit():
        index = int(key)
        if 0 <= index < len(_AXIS_NAMES):
            return index
    return None


def _normalize_profile_meta(
    raw_profile: object,
) -> tuple[str, str, str, str | None, dict[object, object]] | None:
    if not isinstance(raw_profile, dict):
        return None
    profile_id = raw_profile.get("id")
    label = raw_profile.get("label")
    description = raw_profile.get("description")
    mode_raw = raw_profile.get("mode")
    axis_edges_raw = raw_profile.get("axis_edges", {})
    if not isinstance(profile_id, str) or _PROFILE_ID_RE.match(profile_id) is None:
        return None
    if not isinstance(label, str) or not label.strip():
        return None
    if not isinstance(description, str) or not description.strip():
        return None
    if mode_raw is None:
        mode_override = None
    else:
        if not isinstance(mode_raw, str):
            return None
        mode_override = normalize_topology_mode(mode_raw)
    if not isinstance(axis_edges_raw, dict):
        return None
    return profile_id, label.strip(), description.strip(), mode_override, axis_edges_raw


def _normalize_axis_edges(axis_edges_raw: dict[object, object]) -> dict[int, AxisEdgeRule] | None:
    axis_edges: dict[int, AxisEdgeRule] = {}
    for axis_key, edge_rule_raw in axis_edges_raw.items():
        axis_index = _axis_index_from_key(axis_key)
        if axis_index is None:
            return None
        if not isinstance(edge_rule_raw, dict):
            return None
        neg = normalize_edge_behavior(edge_rule_raw.get("neg"))
        pos = normalize_edge_behavior(edge_rule_raw.get("pos"))
        axis_edges[axis_index] = (neg, pos)
    return axis_edges


def _normalize_profile(raw_profile: object) -> TopologyDesignerProfile | None:
    normalized_meta = _normalize_profile_meta(raw_profile)
    if normalized_meta is None:
        return None
    profile_id, label, description, mode_override, axis_edges_raw = normalized_meta
    axis_edges = _normalize_axis_edges(axis_edges_raw)
    if axis_edges is None:
        return None

    return TopologyDesignerProfile(
        profile_id=profile_id,
        label=label,
        description=description,
        mode_override=mode_override,
        axis_edges=axis_edges,
    )


def _default_profiles() -> tuple[TopologyDesignerProfile, ...]:
    return (
        TopologyDesignerProfile(
            profile_id="inherit_mode",
            label="Inherit mode",
            description="Use selected topology mode without extra designer overrides.",
            mode_override=None,
            axis_edges={},
        ),
    )


@lru_cache(maxsize=1)
def _profiles_all() -> tuple[TopologyDesignerProfile, ...]:
    payload = _read_json_payload(_DESIGNER_PRESETS_FILE)
    profiles_raw = payload.get("profiles")
    if not isinstance(profiles_raw, list):
        return _default_profiles()

    profiles: list[TopologyDesignerProfile] = []
    seen_ids: set[str] = set()
    for raw_profile in profiles_raw:
        profile = _normalize_profile(raw_profile)
        if profile is None:
            continue
        if profile.profile_id in seen_ids:
            continue
        seen_ids.add(profile.profile_id)
        profiles.append(profile)
    if not profiles:
        return _default_profiles()
    return tuple(profiles)


def designer_profiles_for_dimension(dimension: int) -> tuple[TopologyDesignerProfile, ...]:
    if dimension not in (2, 3, 4):
        raise ValueError("dimension must be one of: 2, 3, 4")
    profiles = _profiles_all()
    filtered = tuple(
        profile
        for profile in profiles
        if not profile.axis_edges or any(axis < dimension for axis in profile.axis_edges)
    )
    if filtered:
        return filtered
    return _default_profiles()


def designer_profile_label_for_index(dimension: int, index: int) -> str:
    profiles = designer_profiles_for_dimension(dimension)
    safe_index = max(0, min(len(profiles) - 1, int(index)))
    profile = profiles[safe_index]
    return profile.label


def designer_profile_index_by_id(dimension: int, profile_id: str) -> int:
    profiles = designer_profiles_for_dimension(dimension)
    target = profile_id.strip().lower()
    for idx, profile in enumerate(profiles):
        if profile.profile_id.strip().lower() == target:
            return idx
    return 0


def resolve_topology_designer_selection(
    *,
    dimension: int,
    gravity_axis: int,
    topology_mode: str,
    topology_advanced: bool,
    profile_index: int,
    wrap_gravity_axis: bool = False,
) -> tuple[str, EdgeRules | None, TopologyDesignerProfile | None]:
    base_mode = normalize_topology_mode(topology_mode)
    if not topology_advanced:
        return base_mode, None, None

    profiles = designer_profiles_for_dimension(dimension)
    safe_index = max(0, min(len(profiles) - 1, int(profile_index)))
    profile = profiles[safe_index]

    resolved_mode = normalize_topology_mode(profile.mode_override or base_mode)
    rules = list(
        default_edge_rules_for_mode(
            dimension,
            gravity_axis,
            mode=resolved_mode,
            wrap_gravity_axis=wrap_gravity_axis,
        )
    )
    for axis, (neg, pos) in profile.axis_edges.items():
        if axis >= dimension:
            continue
        if axis == gravity_axis and not wrap_gravity_axis:
            rules[axis] = (EDGE_BOUNDED, EDGE_BOUNDED)
            continue
        rules[axis] = (neg, pos)
    return resolved_mode, tuple(rules), profile


def export_resolved_topology_profile(
    *,
    dimension: int,
    gravity_axis: int,
    topology_mode: str,
    topology_advanced: bool,
    profile_index: int,
    wrap_gravity_axis: bool = False,
) -> tuple[bool, str, Path | None]:
    resolved_mode, edge_rules, profile = resolve_topology_designer_selection(
        dimension=dimension,
        gravity_axis=gravity_axis,
        topology_mode=topology_mode,
        topology_advanced=topology_advanced,
        profile_index=profile_index,
        wrap_gravity_axis=wrap_gravity_axis,
    )
    destination = topology_profile_export_file_default_path()
    payload: dict[str, object] = {
        "version": 1,
        "dimension": int(dimension),
        "gravity_axis": int(gravity_axis),
        "mode_input": normalize_topology_mode(topology_mode),
        "mode_resolved": resolved_mode,
        "advanced_enabled": bool(topology_advanced),
    }
    if profile is not None:
        payload["profile"] = {
            "id": profile.profile_id,
            "label": profile.label,
            "description": profile.description,
        }
    if edge_rules is not None:
        payload["edge_rules"] = [
            {
                "axis": _AXIS_NAMES[axis] if axis < len(_AXIS_NAMES) else str(axis),
                "neg": neg,
                "pos": pos,
            }
            for axis, (neg, pos) in enumerate(edge_rules)
        ]

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        return False, f"Failed exporting topology profile: {exc}", None
    return True, f"Exported topology profile to {destination}", destination
