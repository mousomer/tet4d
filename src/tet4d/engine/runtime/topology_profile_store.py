from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    TOPOLOGY_GAMEPLAY_MODE_OPTIONS,
    TopologyProfileState,
    default_topology_profile_state,
    normalize_topology_gameplay_mode,
    topology_profile_state_payload,
    topology_profile_store_v1_state_from_payload,
)
from tet4d.engine.runtime.project_config import topology_profiles_file_default_path
from tet4d.engine.runtime.settings_schema import (
    read_file_bytes,
    write_json_object,
)
from tet4d.engine.topology_explorer.contract_validation import (
    require_json_int,
    require_json_object,
)

_TOPOLOGY_DIMENSIONS = (2, 3, 4)
_DEFAULT_GRAVITY_AXIS = 1
_TOPOLOGY_PROFILE_STORE_VERSION = 1


class TopologyProfileStoreStatus(str, Enum):
    MISSING = "missing"
    VALID = "valid"
    INVALID = "invalid"


@dataclass(frozen=True)
class TopologyProfileStoreLoadResult:
    status: TopologyProfileStoreStatus
    payload: dict[str, Any] | None
    diagnostics: tuple[str, ...] = ()
    source_digest: str | None = None


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
        "version": _TOPOLOGY_PROFILE_STORE_VERSION,
        "topology_profiles": topology_profiles,
    }


def _file_path(root_dir: Path | None = None) -> Path:
    return topology_profiles_file_default_path(root_dir=root_dir)


def load_topology_profile_store(
    root_dir: Path | None = None,
) -> TopologyProfileStoreLoadResult:
    path = _file_path(root_dir=root_dir)
    try:
        source_bytes = read_file_bytes(path)
    except FileNotFoundError:
        return TopologyProfileStoreLoadResult(
            status=TopologyProfileStoreStatus.MISSING,
            payload=_default_payload(),
        )
    except OSError as exc:
        return TopologyProfileStoreLoadResult(
            status=TopologyProfileStoreStatus.INVALID,
            payload=None,
            diagnostics=(f"Failed reading topology profile store: {exc}",),
        )
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    try:
        loaded = json.loads(source_bytes)
        payload = _load_current_topology_profile_store_v1(loaded)
    except (TypeError, ValueError) as exc:
        return TopologyProfileStoreLoadResult(
            status=TopologyProfileStoreStatus.INVALID,
            payload=None,
            diagnostics=(f"Invalid topology profile store: {exc}",),
            source_digest=source_digest,
        )
    return TopologyProfileStoreLoadResult(
        status=TopologyProfileStoreStatus.VALID,
        payload=payload,
        source_digest=source_digest,
    )


def _safe_payload(result: TopologyProfileStoreLoadResult) -> dict[str, Any]:
    return result.payload if result.payload is not None else _default_payload()


def _load_current_topology_profile_store_v1(document: object) -> dict[str, Any]:
    document = require_json_object(document, "topology profile store")
    if set(document) != {"version", "topology_profiles"}:
        raise ValueError("topology profile store fields are invalid")
    version = require_json_int(document["version"], "topology profile store.version")
    if version != _TOPOLOGY_PROFILE_STORE_VERSION:
        raise ValueError("unsupported topology profile store version")
    loaded_profiles = require_json_object(
        document["topology_profiles"], "topology profile store.topology_profiles"
    )
    if set(loaded_profiles) != set(TOPOLOGY_GAMEPLAY_MODE_OPTIONS):
        raise ValueError("topology profile store gameplay modes are invalid")
    payload = _default_payload()
    payload_profiles = payload["topology_profiles"]
    assert isinstance(payload_profiles, dict)
    expected_dimension_keys = {f"{dimension}d" for dimension in _TOPOLOGY_DIMENSIONS}
    for gameplay_mode in TOPOLOGY_GAMEPLAY_MODE_OPTIONS:
        raw_mode = require_json_object(
            loaded_profiles[gameplay_mode],
            f"topology profile store.topology_profiles.{gameplay_mode}",
        )
        if set(raw_mode) != expected_dimension_keys:
            raise ValueError("topology profile store dimension slots are invalid")
        mode_bucket = payload_profiles[gameplay_mode]
        assert isinstance(mode_bucket, dict)
        for dimension in _TOPOLOGY_DIMENSIONS:
            dim_key = f"{dimension}d"
            profile = topology_profile_store_v1_state_from_payload(
                dimension=dimension,
                gravity_axis=_DEFAULT_GRAVITY_AXIS,
                gameplay_mode=gameplay_mode,
                payload=raw_mode[dim_key],
            )
            mode_bucket[dim_key] = topology_profile_state_payload(profile)
    return payload


def load_topology_profiles_payload(root_dir: Path | None = None) -> dict[str, Any]:
    return _safe_payload(load_topology_profile_store(root_dir=root_dir))


def load_topology_profile(
    gameplay_mode: str,
    dimension: int,
    *,
    root_dir: Path | None = None,
) -> TopologyProfileState:
    normalized_mode = normalize_topology_gameplay_mode(gameplay_mode)
    if dimension not in _TOPOLOGY_DIMENSIONS:
        raise ValueError("dimension must be 2, 3, or 4 for topology lab profiles")
    payload = _safe_payload(load_topology_profile_store(root_dir=root_dir))
    raw_profile = (
        payload.get("topology_profiles", {})
        .get(normalized_mode, {})
        .get(f"{dimension}d")
    )
    return topology_profile_store_v1_state_from_payload(
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
    try:
        validated_profile = topology_profile_store_v1_state_from_payload(
            dimension=profile.dimension,
            gravity_axis=_DEFAULT_GRAVITY_AXIS,
            gameplay_mode=profile.gameplay_mode,
            payload=topology_profile_state_payload(profile),
        )
    except (AttributeError, TypeError, ValueError) as exc:
        return False, f"Invalid topology profile: {exc}"
    normalized_mode = normalize_topology_gameplay_mode(validated_profile.gameplay_mode)
    load_result = load_topology_profile_store(root_dir=root_dir)
    if load_result.status is TopologyProfileStoreStatus.INVALID:
        diagnostic = (
            load_result.diagnostics[0] if load_result.diagnostics else "invalid"
        )
        return (
            False,
            f"Refusing to overwrite invalid topology profile store: {diagnostic}",
        )
    payload = _safe_payload(load_result)
    topology_profiles = payload["topology_profiles"]
    assert isinstance(topology_profiles, dict)
    per_mode = topology_profiles[normalized_mode]
    assert isinstance(per_mode, dict)
    per_mode[f"{validated_profile.dimension}d"] = topology_profile_state_payload(
        validated_profile
    )
    path = _file_path(root_dir=root_dir)
    if not _store_source_matches(path, load_result):
        return False, "Topology profile store changed while saving; no data was written"
    try:
        write_json_object(path, payload)
    except OSError as exc:
        return False, f"Failed saving topology profile: {exc}"
    return (
        True,
        f"Saved topology profile for {normalized_mode} {validated_profile.dimension}D",
    )


def _store_source_matches(
    path: Path,
    load_result: TopologyProfileStoreLoadResult,
) -> bool:
    if load_result.status is TopologyProfileStoreStatus.MISSING:
        return not path.exists()
    if load_result.status is not TopologyProfileStoreStatus.VALID:
        return False
    try:
        current_bytes = read_file_bytes(path)
    except OSError:
        return False
    return hashlib.sha256(current_bytes).hexdigest() == load_result.source_digest


def topology_profile_note(gameplay_mode: str) -> str:
    normalized_mode = normalize_topology_gameplay_mode(gameplay_mode)
    if normalized_mode == GAMEPLAY_MODE_NORMAL:
        return "Y boundaries are fixed in Normal Game and cannot be wrapped."
    return "Explorer Mode allows Y-boundary wrapping and upward traversal."


__all__ = [
    "GAMEPLAY_MODE_EXPLORER",
    "GAMEPLAY_MODE_NORMAL",
    "TopologyProfileStoreLoadResult",
    "TopologyProfileStoreStatus",
    "load_topology_profile",
    "load_topology_profile_store",
    "load_topology_profiles_payload",
    "save_topology_profile",
    "topology_profile_note",
]
