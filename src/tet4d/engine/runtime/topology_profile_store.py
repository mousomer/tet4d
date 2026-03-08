from __future__ import annotations

from pathlib import Path
from typing import Any

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    TOPOLOGY_GAMEPLAY_MODE_OPTIONS,
    TopologyProfileState,
    default_topology_profile_state,
    normalize_topology_gameplay_mode,
    topology_profile_state_from_payload,
    topology_profile_state_payload,
)
from tet4d.engine.runtime.project_config import topology_profiles_file_default_path
from tet4d.engine.runtime.settings_schema import read_json_object_or_empty, write_json_object

_TOPOLOGY_DIMENSIONS = (3, 4)
_DEFAULT_GRAVITY_AXIS = 1


def _default_payload() -> dict[str, Any]:
    topology_profiles: dict[str, dict[str, dict[str, object]]] = {}
    for gameplay_mode in TOPOLOGY_GAMEPLAY_MODE_OPTIONS:
        per_dimension: dict[str, dict[str, object]] = {}
        for dimension in _TOPOLOGY_DIMENSIONS:
            profile = default_topology_profile_state(
                dimension=dimension,
                gravity_axis=_DEFAULT_GRAVITY_AXIS,
                gameplay_mode=gameplay_mode,
            )
            per_dimension[f"{dimension}d"] = topology_profile_state_payload(profile)
        topology_profiles[gameplay_mode] = per_dimension
    return {
        "version": 1,
        "topology_profiles": topology_profiles,
    }


def _file_path(root_dir: Path | None = None) -> Path:
    return topology_profiles_file_default_path(root_dir=root_dir)


def _load_payload(root_dir: Path | None = None) -> dict[str, Any]:
    path = _file_path(root_dir=root_dir)
    loaded = read_json_object_or_empty(path)
    payload = _default_payload()
    loaded_profiles = loaded.get("topology_profiles")
    if not isinstance(loaded_profiles, dict):
        return payload
    payload_profiles = payload["topology_profiles"]
    assert isinstance(payload_profiles, dict)
    for gameplay_mode in TOPOLOGY_GAMEPLAY_MODE_OPTIONS:
        raw_mode = loaded_profiles.get(gameplay_mode)
        if not isinstance(raw_mode, dict):
            continue
        mode_bucket = payload_profiles[gameplay_mode]
        assert isinstance(mode_bucket, dict)
        for dimension in _TOPOLOGY_DIMENSIONS:
            dim_key = f"{dimension}d"
            raw_profile = raw_mode.get(dim_key)
            profile = topology_profile_state_from_payload(
                dimension=dimension,
                gravity_axis=_DEFAULT_GRAVITY_AXIS,
                gameplay_mode=gameplay_mode,
                payload=raw_profile,
            )
            mode_bucket[dim_key] = topology_profile_state_payload(profile)
    return payload


def load_topology_profiles_payload(root_dir: Path | None = None) -> dict[str, Any]:
    return _load_payload(root_dir=root_dir)


def load_topology_profile(
    gameplay_mode: str,
    dimension: int,
    *,
    root_dir: Path | None = None,
) -> TopologyProfileState:
    normalized_mode = normalize_topology_gameplay_mode(gameplay_mode)
    if dimension not in _TOPOLOGY_DIMENSIONS:
        raise ValueError("dimension must be 3 or 4 for topology lab profiles")
    payload = _load_payload(root_dir=root_dir)
    raw_profile = (
        payload.get("topology_profiles", {})
        .get(normalized_mode, {})
        .get(f"{dimension}d")
    )
    return topology_profile_state_from_payload(
        dimension=dimension,
        gravity_axis=_DEFAULT_GRAVITY_AXIS,
        gameplay_mode=normalized_mode,
        payload=raw_profile,
    )


def save_topology_profile(
    profile: TopologyProfileState,
    *,
    root_dir: Path | None = None,
) -> tuple[bool, str]:
    normalized_mode = normalize_topology_gameplay_mode(profile.gameplay_mode)
    if profile.dimension not in _TOPOLOGY_DIMENSIONS:
        return False, "dimension must be 3 or 4 for topology lab profiles"
    payload = _load_payload(root_dir=root_dir)
    topology_profiles = payload.setdefault("topology_profiles", {})
    if not isinstance(topology_profiles, dict):
        topology_profiles = {}
        payload["topology_profiles"] = topology_profiles
    per_mode = topology_profiles.setdefault(normalized_mode, {})
    if not isinstance(per_mode, dict):
        per_mode = {}
        topology_profiles[normalized_mode] = per_mode
    per_mode[f"{profile.dimension}d"] = topology_profile_state_payload(profile)
    path = _file_path(root_dir=root_dir)
    try:
        write_json_object(path, payload)
    except OSError as exc:
        return False, f"Failed saving topology profile: {exc}"
    return True, f"Saved topology profile for {normalized_mode} {profile.dimension}D"


def topology_profile_note(gameplay_mode: str) -> str:
    normalized_mode = normalize_topology_gameplay_mode(gameplay_mode)
    if normalized_mode == GAMEPLAY_MODE_NORMAL:
        return "Y boundaries are fixed in Normal Game and cannot be wrapped."
    return "Explorer Mode allows Y-boundary wrapping and upward traversal."


__all__ = [
    "GAMEPLAY_MODE_EXPLORER",
    "GAMEPLAY_MODE_NORMAL",
    "load_topology_profile",
    "load_topology_profiles_payload",
    "save_topology_profile",
    "topology_profile_note",
]
