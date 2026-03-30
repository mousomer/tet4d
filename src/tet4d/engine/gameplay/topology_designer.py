from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..runtime.project_config import (
    project_root_path,
    topology_profile_export_file_default_path,
)
from ..runtime.settings_schema import read_json_object_or_empty, write_json_object
from .topology import (
    EDGE_BOUNDED,
    AxisEdgeRule,
    EdgeRules,
    default_edge_rules_for_mode,
    normalize_edge_behavior,
    normalize_topology_mode,
)


GAMEPLAY_MODE_NORMAL = "normal"
GAMEPLAY_MODE_EXPLORER = "explorer"
TOPOLOGY_GAMEPLAY_MODE_OPTIONS = (
    GAMEPLAY_MODE_NORMAL,
    GAMEPLAY_MODE_EXPLORER,
)
_GAMEPLAY_MODE_SET = frozenset(TOPOLOGY_GAMEPLAY_MODE_OPTIONS)
_GAMEPLAY_MODE_LABELS = {
    GAMEPLAY_MODE_NORMAL: "Normal Game",
    GAMEPLAY_MODE_EXPLORER: "Explorer Mode",
}

_DESIGNER_PRESETS_FILE = (
    project_root_path() / "config" / "topology" / "designer_presets.json"
)
_PROFILE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_AXIS_NAMES = ("x", "y", "z", "w")
_AXIS_TO_INDEX = {axis_name: idx for idx, axis_name in enumerate(_AXIS_NAMES)}
_DIMENSION_KEYS = {2: "2d", 3: "3d", 4: "4d"}


@dataclass(frozen=True)
class TopologyDesignerProfile:
    profile_id: str
    label: str
    description: str
    mode_override: str | None
    axis_edges: dict[int, AxisEdgeRule]


@dataclass(frozen=True)
class TopologyProfileState:
    gameplay_mode: str
    dimension: int
    topology_mode: str
    edge_rules: EdgeRules
    preset_id: str | None = None


def normalize_topology_gameplay_mode(mode: str | None) -> str:
    if mode is None:
        return GAMEPLAY_MODE_NORMAL
    normalized = str(mode).strip().lower()
    if normalized not in _GAMEPLAY_MODE_SET:
        raise ValueError(f"unknown topology gameplay mode: {mode!r}")
    return normalized


def topology_gameplay_mode_label(mode: str | None) -> str:
    normalized = normalize_topology_gameplay_mode(mode)
    return _GAMEPLAY_MODE_LABELS[normalized]


def _read_json_payload(path: Path) -> dict[str, Any]:
    return read_json_object_or_empty(path)


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


def _normalize_axis_edges(
    axis_edges_raw: dict[object, object],
) -> dict[int, AxisEdgeRule] | None:
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


def _normalize_edge_rules(
    rules_raw: object,
    *,
    dimension: int,
) -> EdgeRules:
    if not isinstance(rules_raw, (list, tuple)):
        raise ValueError("edge_rules must be a list of axis rules")
    if len(rules_raw) != int(dimension):
        raise ValueError("edge_rules axis count must match dimension")
    normalized: list[AxisEdgeRule] = []
    for axis_rule in rules_raw:
        if not isinstance(axis_rule, (list, tuple)) or len(axis_rule) != 2:
            raise ValueError("each edge rule must contain [neg, pos]")
        neg = normalize_edge_behavior(axis_rule[0])
        pos = normalize_edge_behavior(axis_rule[1])
        normalized.append((neg, pos))
    return tuple(normalized)


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
            label="Use selected mode",
            description="Use the selected topology mode without per-edge overrides.",
            mode_override=None,
            axis_edges={},
        ),
    )


def _axis_edges_valid_for_dimension(
    axis_edges: dict[int, AxisEdgeRule],
    *,
    dimension: int,
) -> bool:
    return all(0 <= axis < int(dimension) for axis in axis_edges)


def _validate_gameplay_mode_rules(
    *,
    gameplay_mode: str,
    dimension: int,
    gravity_axis: int,
    rules: EdgeRules,
) -> EdgeRules:
    if len(rules) != int(dimension):
        raise ValueError("edge_rules axis count must match dimension")
    normalized_mode = normalize_topology_gameplay_mode(gameplay_mode)
    if normalized_mode == GAMEPLAY_MODE_NORMAL:
        gravity_rule = rules[int(gravity_axis)]
        if gravity_rule != (EDGE_BOUNDED, EDGE_BOUNDED):
            raise ValueError(
                "normal gameplay topology cannot wrap or invert the gravity axis"
            )
    return tuple((str(neg), str(pos)) for neg, pos in rules)


def validate_topology_profile_state(
    *,
    gameplay_mode: str,
    dimension: int,
    gravity_axis: int,
    topology_mode: str,
    edge_rules: EdgeRules,
    preset_id: str | None = None,
) -> TopologyProfileState:
    if dimension not in _DIMENSION_KEYS:
        raise ValueError("dimension must be one of: 2, 3, 4")
    normalized_mode = normalize_topology_mode(topology_mode)
    validated_rules = _validate_gameplay_mode_rules(
        gameplay_mode=gameplay_mode,
        dimension=dimension,
        gravity_axis=gravity_axis,
        rules=edge_rules,
    )
    normalized_preset_id = None
    if isinstance(preset_id, str) and preset_id.strip():
        candidate = preset_id.strip()
        if _PROFILE_ID_RE.match(candidate) is not None:
            normalized_preset_id = candidate
    return TopologyProfileState(
        gameplay_mode=normalize_topology_gameplay_mode(gameplay_mode),
        dimension=int(dimension),
        topology_mode=normalized_mode,
        edge_rules=validated_rules,
        preset_id=normalized_preset_id,
    )


def _normalized_profiles_for_dimension(
    profiles_raw: object,
    *,
    dimension: int,
) -> tuple[TopologyDesignerProfile, ...]:
    profiles: list[TopologyDesignerProfile] = []
    seen_ids: set[str] = set()
    if isinstance(profiles_raw, list):
        for raw_profile in profiles_raw:
            profile = _normalize_profile(raw_profile)
            if profile is None or profile.profile_id in seen_ids:
                continue
            if not _axis_edges_valid_for_dimension(
                profile.axis_edges,
                dimension=dimension,
            ):
                continue
            seen_ids.add(profile.profile_id)
            profiles.append(profile)
    if not profiles:
        profiles = list(_default_profiles())
    return tuple(profiles)


def _profiles_from_legacy_payload(
    profiles_raw: object,
) -> dict[str, dict[int, tuple[TopologyDesignerProfile, ...]]]:
    if not isinstance(profiles_raw, list):
        return {}
    profile_tuple = _normalized_profiles_for_dimension(profiles_raw, dimension=4)
    return {
        mode: {dimension: profile_tuple for dimension in _DIMENSION_KEYS}
        for mode in TOPOLOGY_GAMEPLAY_MODE_OPTIONS
    }


def _profiles_from_mode_payload(
    payload: dict[str, Any],
) -> dict[str, dict[int, tuple[TopologyDesignerProfile, ...]]]:
    profiles_root = payload.get("profiles")
    if isinstance(profiles_root, list):
        return _profiles_from_legacy_payload(profiles_root)
    if not isinstance(profiles_root, dict):
        return {}

    normalized: dict[str, dict[int, tuple[TopologyDesignerProfile, ...]]] = {}
    for gameplay_mode in TOPOLOGY_GAMEPLAY_MODE_OPTIONS:
        raw_mode_profiles = profiles_root.get(gameplay_mode)
        if not isinstance(raw_mode_profiles, dict):
            continue
        mode_profiles: dict[int, tuple[TopologyDesignerProfile, ...]] = {}
        for dimension, dim_key in _DIMENSION_KEYS.items():
            mode_profiles[dimension] = _normalized_profiles_for_dimension(
                raw_mode_profiles.get(dim_key),
                dimension=dimension,
            )
        if mode_profiles:
            normalized[gameplay_mode] = mode_profiles
    return normalized


@lru_cache(maxsize=1)
def _profiles_by_mode_and_dimension() -> dict[str, dict[int, tuple[TopologyDesignerProfile, ...]]]:
    payload = _read_json_payload(_DESIGNER_PRESETS_FILE)
    profiles = _profiles_from_mode_payload(payload)
    if profiles:
        return profiles
    return _profiles_from_legacy_payload(payload.get("profiles"))


def designer_profiles_for_dimension(
    dimension: int,
    gameplay_mode: str | None = None,
) -> tuple[TopologyDesignerProfile, ...]:
    if dimension not in _DIMENSION_KEYS:
        raise ValueError("dimension must be one of: 2, 3, 4")
    normalized_mode = normalize_topology_gameplay_mode(gameplay_mode)
    profiles = _profiles_by_mode_and_dimension().get(normalized_mode, {})
    filtered = profiles.get(int(dimension), ())
    if filtered:
        return filtered
    return _default_profiles()


def designer_profile_label_for_index(
    dimension: int,
    index: int,
    gameplay_mode: str | None = None,
) -> str:
    profiles = designer_profiles_for_dimension(dimension, gameplay_mode)
    safe_index = max(0, min(len(profiles) - 1, int(index)))
    profile = profiles[safe_index]
    return profile.label


def profile_state_from_preset(
    *,
    dimension: int,
    gravity_axis: int,
    gameplay_mode: str,
    preset_index: int,
    topology_mode: str | None = None,
) -> TopologyProfileState:
    normalized_gameplay_mode = normalize_topology_gameplay_mode(gameplay_mode)
    profiles = designer_profiles_for_dimension(dimension, normalized_gameplay_mode)
    safe_index = max(0, min(len(profiles) - 1, int(preset_index)))
    profile = profiles[safe_index]
    resolved_mode = normalize_topology_mode(profile.mode_override or topology_mode)
    rules = list(
        default_edge_rules_for_mode(
            dimension,
            gravity_axis,
            mode=resolved_mode,
            wrap_gravity_axis=(normalized_gameplay_mode == GAMEPLAY_MODE_EXPLORER),
        )
    )
    for axis, rule in profile.axis_edges.items():
        if axis < int(dimension):
            rules[axis] = rule
    return validate_topology_profile_state(
        gameplay_mode=normalized_gameplay_mode,
        dimension=dimension,
        gravity_axis=gravity_axis,
        topology_mode=resolved_mode,
        edge_rules=tuple(rules),
        preset_id=profile.profile_id,
    )


def default_topology_profile_state(
    *,
    dimension: int,
    gravity_axis: int,
    gameplay_mode: str,
) -> TopologyProfileState:
    return profile_state_from_preset(
        dimension=dimension,
        gravity_axis=gravity_axis,
        gameplay_mode=gameplay_mode,
        preset_index=0,
        topology_mode="bounded",
    )


def topology_profile_state_from_payload(
    *,
    dimension: int,
    gravity_axis: int,
    gameplay_mode: str,
    payload: object,
) -> TopologyProfileState:
    default_state = default_topology_profile_state(
        dimension=dimension,
        gravity_axis=gravity_axis,
        gameplay_mode=gameplay_mode,
    )
    if not isinstance(payload, dict):
        return default_state
    raw_topology_mode = payload.get("topology_mode", default_state.topology_mode)
    try:
        normalized_mode = normalize_topology_mode(raw_topology_mode)
    except ValueError:
        normalized_mode = default_state.topology_mode
    raw_edge_rules = payload.get("edge_rules")
    if raw_edge_rules is None:
        edge_rules = default_state.edge_rules
    else:
        try:
            edge_rules = _normalize_edge_rules(raw_edge_rules, dimension=dimension)
        except ValueError:
            edge_rules = default_state.edge_rules
    raw_preset_id = payload.get("preset_id")
    preset_id = raw_preset_id if isinstance(raw_preset_id, str) else default_state.preset_id
    try:
        return validate_topology_profile_state(
            gameplay_mode=gameplay_mode,
            dimension=dimension,
            gravity_axis=gravity_axis,
            topology_mode=normalized_mode,
            edge_rules=edge_rules,
            preset_id=preset_id,
        )
    except ValueError:
        return default_state


def topology_profile_state_payload(profile: TopologyProfileState) -> dict[str, object]:
    return {
        "topology_mode": profile.topology_mode,
        "preset_id": profile.preset_id,
        "edge_rules": [[neg, pos] for neg, pos in profile.edge_rules],
    }


def export_topology_profile_state(
    *,
    profile: TopologyProfileState,
    gravity_axis: int,
) -> tuple[bool, str, Path | None]:
    destination = topology_profile_export_file_default_path()
    payload: dict[str, object] = {
        "version": 2,
        "dimension": int(profile.dimension),
        "gameplay_mode": profile.gameplay_mode,
        "gravity_axis": int(gravity_axis),
        "mode_input": profile.topology_mode,
        "mode_resolved": profile.topology_mode,
        "advanced_enabled": True,
        "edge_rules": [
            {
                "axis": _AXIS_NAMES[axis] if axis < len(_AXIS_NAMES) else str(axis),
                "neg": neg,
                "pos": pos,
            }
            for axis, (neg, pos) in enumerate(profile.edge_rules)
        ],
    }
    if profile.preset_id:
        payload["profile"] = {"id": profile.preset_id}
    try:
        write_json_object(destination, payload)
    except OSError as exc:
        return False, f"Failed exporting topology profile: {exc}", None
    return True, f"Exported topology profile to {destination}", destination


def resolve_topology_designer_selection(
    *,
    dimension: int,
    gravity_axis: int,
    topology_mode: str,
    topology_advanced: bool,
    profile_index: int,
    gameplay_mode: str | None = None,
    wrap_gravity_axis: bool | None = None,
) -> tuple[str, EdgeRules | None, TopologyDesignerProfile | None]:
    base_mode = normalize_topology_mode(topology_mode)
    normalized_gameplay_mode = normalize_topology_gameplay_mode(gameplay_mode)
    wrap_gravity = (
        normalized_gameplay_mode == GAMEPLAY_MODE_EXPLORER
        if wrap_gravity_axis is None
        else bool(wrap_gravity_axis)
    )
    if not topology_advanced:
        if normalized_gameplay_mode == GAMEPLAY_MODE_NORMAL:
            return base_mode, None, None
        rules = _validate_gameplay_mode_rules(
            gameplay_mode=normalized_gameplay_mode,
            dimension=dimension,
            gravity_axis=gravity_axis,
            rules=default_edge_rules_for_mode(
                dimension,
                gravity_axis,
                mode=base_mode,
                wrap_gravity_axis=wrap_gravity,
            ),
        )
        return base_mode, rules, None

    profiles = designer_profiles_for_dimension(dimension, normalized_gameplay_mode)
    safe_index = max(0, min(len(profiles) - 1, int(profile_index)))
    profile = profiles[safe_index]

    resolved_mode = normalize_topology_mode(profile.mode_override or base_mode)
    rules = list(
        default_edge_rules_for_mode(
            dimension,
            gravity_axis,
            mode=resolved_mode,
            wrap_gravity_axis=wrap_gravity,
        )
    )
    for axis, (neg, pos) in profile.axis_edges.items():
        if axis >= dimension:
            continue
        rules[axis] = (neg, pos)
    validated_rules = _validate_gameplay_mode_rules(
        gameplay_mode=normalized_gameplay_mode,
        dimension=dimension,
        gravity_axis=gravity_axis,
        rules=tuple(rules),
    )
    return resolved_mode, validated_rules, profile


def export_resolved_topology_profile(
    *,
    dimension: int,
    gravity_axis: int,
    topology_mode: str,
    topology_advanced: bool,
    profile_index: int,
    gameplay_mode: str | None = None,
    wrap_gravity_axis: bool | None = None,
) -> tuple[bool, str, Path | None]:
    normalized_gameplay_mode = normalize_topology_gameplay_mode(gameplay_mode)
    resolved_mode, edge_rules, profile = resolve_topology_designer_selection(
        dimension=dimension,
        gravity_axis=gravity_axis,
        topology_mode=topology_mode,
        topology_advanced=topology_advanced,
        profile_index=profile_index,
        gameplay_mode=normalized_gameplay_mode,
        wrap_gravity_axis=wrap_gravity_axis,
    )
    destination = topology_profile_export_file_default_path()
    payload: dict[str, object] = {
        "version": 2,
        "dimension": int(dimension),
        "gameplay_mode": normalized_gameplay_mode,
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
        write_json_object(destination, payload)
    except OSError as exc:
        return False, f"Failed exporting topology profile: {exc}", None
    return True, f"Exported topology profile to {destination}", destination
