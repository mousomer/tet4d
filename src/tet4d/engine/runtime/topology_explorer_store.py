from __future__ import annotations

from pathlib import Path
from typing import Any

from tet4d.engine.runtime.project_config import (
    explorer_topology_profiles_file_default_path,
)
from tet4d.engine.runtime.settings_schema import (
    read_json_object_or_empty,
    write_json_object,
)
from tet4d.engine.topology_explorer import (
    AXIS_NAMES,
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
)

_TOPOLOGY_DIMENSIONS = (3, 4)
_AXIS_TO_INDEX = {axis_name: index for index, axis_name in enumerate(AXIS_NAMES)}


def _empty_profile(dimension: int) -> ExplorerTopologyProfile:
    return ExplorerTopologyProfile(dimension=int(dimension), gluings=())


def _boundary_payload(boundary: BoundaryRef) -> dict[str, object]:
    return {
        "axis": AXIS_NAMES[boundary.axis],
        "side": boundary.side,
    }


def _transform_payload(transform: BoundaryTransform) -> dict[str, object]:
    return {
        "permutation": list(transform.permutation),
        "signs": list(transform.signs),
    }


def _glue_payload(glue: GluingDescriptor) -> dict[str, object]:
    return {
        "id": glue.glue_id,
        "enabled": glue.enabled,
        "source": _boundary_payload(glue.source),
        "target": _boundary_payload(glue.target),
        "transform": _transform_payload(glue.transform),
    }


def _profile_payload(profile: ExplorerTopologyProfile) -> dict[str, object]:
    return {
        "dimension": profile.dimension,
        "gluings": [_glue_payload(glue) for glue in profile.gluings],
    }


def _axis_index(raw: object) -> int:
    if isinstance(raw, bool):
        raise ValueError("axis must be a string or integer index")
    if isinstance(raw, int):
        return int(raw)
    if isinstance(raw, str):
        axis = raw.strip().lower()
        if axis in _AXIS_TO_INDEX:
            return _AXIS_TO_INDEX[axis]
    raise ValueError("axis must be a valid axis label")


def _boundary_from_payload(payload: object, *, dimension: int) -> BoundaryRef:
    if not isinstance(payload, dict):
        raise ValueError("boundary payload must be an object")
    return BoundaryRef(
        dimension=dimension,
        axis=_axis_index(payload.get("axis")),
        side=str(payload.get("side", "")),
    )


def _transform_from_payload(payload: object, *, dimension: int) -> BoundaryTransform:
    if not isinstance(payload, dict):
        raise ValueError("transform payload must be an object")
    permutation_raw = payload.get("permutation")
    signs_raw = payload.get("signs")
    if not isinstance(permutation_raw, list) or not isinstance(signs_raw, list):
        raise ValueError("transform payload requires permutation and signs lists")
    if len(permutation_raw) != dimension - 1 or len(signs_raw) != dimension - 1:
        raise ValueError("transform tangent rank must match dimension - 1")
    return BoundaryTransform(
        permutation=tuple(int(value) for value in permutation_raw),
        signs=tuple(int(value) for value in signs_raw),
    )


def _glue_from_payload(payload: object, *, dimension: int) -> GluingDescriptor:
    if not isinstance(payload, dict):
        raise ValueError("gluing payload must be an object")
    return GluingDescriptor(
        glue_id=str(payload.get("id", "")),
        enabled=bool(payload.get("enabled", True)),
        source=_boundary_from_payload(payload.get("source"), dimension=dimension),
        target=_boundary_from_payload(payload.get("target"), dimension=dimension),
        transform=_transform_from_payload(
            payload.get("transform"), dimension=dimension
        ),
    )


def _profile_from_payload(dimension: int, payload: object) -> ExplorerTopologyProfile:
    default_profile = _empty_profile(dimension)
    if not isinstance(payload, dict):
        return default_profile
    raw_gluings = payload.get("gluings")
    if not isinstance(raw_gluings, list):
        return default_profile
    try:
        gluings = tuple(
            _glue_from_payload(raw_glue, dimension=dimension)
            for raw_glue in raw_gluings
        )
        return ExplorerTopologyProfile(dimension=dimension, gluings=gluings)
    except ValueError:
        return default_profile


def _default_payload() -> dict[str, Any]:
    return {
        "version": 1,
        "explorer_topology_profiles": {
            f"{dimension}d": _profile_payload(_empty_profile(dimension))
            for dimension in _TOPOLOGY_DIMENSIONS
        },
    }


def _file_path(root_dir: Path | None = None) -> Path:
    return explorer_topology_profiles_file_default_path(root_dir=root_dir)


def _load_payload(root_dir: Path | None = None) -> dict[str, Any]:
    payload = _default_payload()
    loaded = read_json_object_or_empty(_file_path(root_dir=root_dir))
    loaded_profiles = loaded.get("explorer_topology_profiles")
    if not isinstance(loaded_profiles, dict):
        return payload
    payload_profiles = payload["explorer_topology_profiles"]
    assert isinstance(payload_profiles, dict)
    for dimension in _TOPOLOGY_DIMENSIONS:
        dim_key = f"{dimension}d"
        payload_profiles[dim_key] = _profile_payload(
            _profile_from_payload(dimension, loaded_profiles.get(dim_key))
        )
    return payload


def load_explorer_topology_profiles_payload(
    root_dir: Path | None = None,
) -> dict[str, Any]:
    return _load_payload(root_dir=root_dir)


def load_explorer_topology_profile(
    dimension: int,
    *,
    root_dir: Path | None = None,
) -> ExplorerTopologyProfile:
    normalized_dimension = int(dimension)
    if normalized_dimension not in _TOPOLOGY_DIMENSIONS:
        raise ValueError("dimension must be 3 or 4 for explorer topology profiles")
    payload = _load_payload(root_dir=root_dir)
    raw = payload.get("explorer_topology_profiles", {}).get(f"{normalized_dimension}d")
    return _profile_from_payload(normalized_dimension, raw)


def save_explorer_topology_profile(
    profile: ExplorerTopologyProfile,
    *,
    root_dir: Path | None = None,
) -> tuple[bool, str]:
    if profile.dimension not in _TOPOLOGY_DIMENSIONS:
        return False, "dimension must be 3 or 4 for explorer topology profiles"
    payload = _load_payload(root_dir=root_dir)
    profiles = payload.setdefault("explorer_topology_profiles", {})
    if not isinstance(profiles, dict):
        profiles = {}
        payload["explorer_topology_profiles"] = profiles
    profiles[f"{profile.dimension}d"] = _profile_payload(profile)
    path = _file_path(root_dir=root_dir)
    try:
        write_json_object(path, payload)
    except OSError as exc:
        return False, f"Failed saving explorer topology profile: {exc}"
    return True, f"Saved explorer topology profile for {profile.dimension}D"


__all__ = [
    "load_explorer_topology_profile",
    "load_explorer_topology_profiles_payload",
    "save_explorer_topology_profile",
]
