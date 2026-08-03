from __future__ import annotations

import hashlib
import json
import math
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

from tet4d.engine.runtime.project_config import (
    explorer_topology_preview_cache_dir_path,
)
from tet4d.engine.runtime.settings_schema import (
    atomic_write_json,
    read_json_value_or_raise,
)
from tet4d.engine.runtime.topology_playground_state import (
    TopologyPlaygroundMovementSummary,
    TopologyPlaygroundPlayabilityAnalysis,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.engine.topology_explorer.domain_validation import (
    require_instance,
    require_integral,
    require_integral_sequence,
)
from tet4d.engine.topology_explorer.movement_graph import (
    deserialize_movement_graph_rows,
    movement_graph_rows,
    serialize_movement_graph_rows,
)

TOPOLOGY_CACHE_VERSION = 3
_CACHE_DATA_FIELDS = frozenset({"graph_rows", "playability_analysis"})
_CACHE_METADATA_FIELDS = frozenset({"cache_key", "cache_version", "dims"})
_PLAYABILITY_FIELDS = frozenset(
    {
        "status",
        "validity",
        "explorer_usability",
        "rigid_playability",
        "summary",
        "validity_reason",
        "explorer_reason",
        "rigid_reason",
        "warnings",
        "errors",
        "movement_summary",
        "recommended_next_preset",
    }
)
_PLAYABILITY_STRING_FIELDS = _PLAYABILITY_FIELDS - {
    "warnings",
    "errors",
    "movement_summary",
    "recommended_next_preset",
}
_MOVEMENT_SUMMARY_FIELDS = frozenset(
    {
        "cell_count",
        "directed_edge_count",
        "boundary_traversal_count",
        "component_count",
    }
)


def _profile_signature_payload(
    profile: ExplorerTopologyProfile,
) -> dict[str, object]:
    return {
        "dimension": profile.dimension,
        "gluings": [
            {
                "id": glue.glue_id,
                "enabled": glue.enabled,
                "source": {
                    "axis": glue.source.axis,
                    "side": glue.source.side,
                },
                "target": {
                    "axis": glue.target.axis,
                    "side": glue.target.side,
                },
                "transform": {
                    "permutation": list(glue.transform.permutation),
                    "signs": list(glue.transform.signs),
                },
            }
            for glue in profile.gluings
        ],
    }


def topology_cache_key(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
) -> str:
    validated_profile = require_instance(profile, "profile", ExplorerTopologyProfile)
    normalized_dims = require_integral_sequence(dims, "dims")
    if len(normalized_dims) != validated_profile.dimension:
        raise ValueError("dims rank must match topology profile dimension")
    if any(value <= 0 for value in normalized_dims):
        raise ValueError("dims must contain only positive integers")
    payload = {
        "cache_version": TOPOLOGY_CACHE_VERSION,
        "dims": list(normalized_dims),
        "profile": _profile_signature_payload(validated_profile),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def topology_cache_dir_path(*, root_dir: Path | None = None) -> Path:
    return explorer_topology_preview_cache_dir_path(root_dir=root_dir)


def topology_cache_file_path(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    root_dir: Path | None = None,
) -> Path:
    return (
        topology_cache_dir_path(root_dir=root_dir)
        / f"{topology_cache_key(profile, dims=dims)}.json"
    )


def _cache_entry_metadata_matches(
    payload: object,
    *,
    expected_key: str,
    expected_version: int,
    expected_dims: tuple[int, ...],
) -> bool:
    if type(payload) is not dict or not payload:
        return False
    if not _CACHE_METADATA_FIELDS.issubset(payload):
        return False
    if set(payload) - _CACHE_METADATA_FIELDS - _CACHE_DATA_FIELDS:
        return False
    if type(payload.get("cache_version")) is not int:
        return False
    if payload["cache_version"] != expected_version:
        return False
    if type(payload.get("cache_key")) is not str:
        return False
    if payload["cache_key"] != expected_key:
        return False
    stored_dims = payload.get("dims")
    if type(stored_dims) is not list:
        return False
    if any(type(value) is not int for value in stored_dims):
        return False
    return tuple(stored_dims) == expected_dims


def read_topology_cache_entry(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    cache_version: int = TOPOLOGY_CACHE_VERSION,
    root_dir: Path | None = None,
) -> dict[str, Any] | None:
    normalized_version = require_integral(cache_version, "cache_version")
    normalized_dims = require_integral_sequence(dims, "dims")
    expected_key = topology_cache_key(profile, dims=normalized_dims)
    cache_path = topology_cache_file_path(profile, dims=dims, root_dir=root_dir)
    if not cache_path.exists():
        return None
    try:
        payload = read_json_value_or_raise(cache_path)
    except (OSError, ValueError):
        return None
    if not _cache_entry_metadata_matches(
        payload,
        expected_key=expected_key,
        expected_version=normalized_version,
        expected_dims=normalized_dims,
    ):
        return None
    assert isinstance(payload, dict)
    return payload


def _validate_cache_json_value(value: object, *, path: str = "cache") -> None:
    if value is None or type(value) in {str, bool, int}:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{path} must contain only finite floats")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _validate_cache_json_value(item, path=f"{path}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError(f"{path} mapping keys must be strings")
            _validate_cache_json_value(item, path=f"{path}.{key}")
        return
    raise TypeError(f"{path} contains unsupported value {type(value).__name__}")


def write_topology_cache_entry(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    entry: dict[str, Any],
    cache_version: int = TOPOLOGY_CACHE_VERSION,
    root_dir: Path | None = None,
) -> None:
    normalized_version = require_integral(cache_version, "cache_version")
    normalized_dims = require_integral_sequence(dims, "dims")
    cache_key = topology_cache_key(profile, dims=normalized_dims)
    cache_path = topology_cache_file_path(
        profile,
        dims=normalized_dims,
        root_dir=root_dir,
    )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    unknown_fields = set(entry) - _CACHE_DATA_FIELDS - _CACHE_METADATA_FIELDS
    if unknown_fields:
        raise ValueError(
            f"unknown topology cache field(s): {', '.join(sorted(unknown_fields))}"
        )
    payload = {key: value for key, value in entry.items() if key in _CACHE_DATA_FIELDS}
    payload["cache_version"] = normalized_version
    payload["cache_key"] = cache_key
    payload["dims"] = list(normalized_dims)
    _validate_cache_json_value(payload)
    atomic_write_json(cache_path, payload)


def merge_topology_cache_entry(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    cache_version: int = TOPOLOGY_CACHE_VERSION,
    root_dir: Path | None = None,
    **updates: object,
) -> None:
    entry = (
        read_topology_cache_entry(
            profile,
            dims=dims,
            cache_version=cache_version,
            root_dir=root_dir,
        )
        or {}
    )
    entry.update(updates)
    write_topology_cache_entry(
        profile,
        dims=dims,
        entry=entry,
        cache_version=cache_version,
        root_dir=root_dir,
    )


def read_cached_graph_rows(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    cache_version: int = TOPOLOGY_CACHE_VERSION,
    root_dir: Path | None = None,
):
    entry = read_topology_cache_entry(
        profile,
        dims=dims,
        cache_version=cache_version,
        root_dir=root_dir,
    )
    if entry is None:
        return None
    cached_rows = deserialize_movement_graph_rows(
        entry.get("graph_rows"),
        dims=dims,
    )
    if cached_rows is None:
        return None
    # A structurally valid cache still cannot define topology semantics. Compare
    # it with the authoritative profile/resolver result before reuse.
    if cached_rows != movement_graph_rows(profile, dims=dims):
        return None
    return cached_rows


def write_cached_graph_rows(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    graph_rows,
    cache_version: int = TOPOLOGY_CACHE_VERSION,
    root_dir: Path | None = None,
) -> None:
    merge_topology_cache_entry(
        profile,
        dims=dims,
        cache_version=cache_version,
        root_dir=root_dir,
        graph_rows=serialize_movement_graph_rows(graph_rows, dims=dims),
    )


def _serialize_playability_analysis(
    analysis: TopologyPlaygroundPlayabilityAnalysis,
) -> dict[str, object]:
    payload = asdict(analysis)
    payload["warnings"] = list(analysis.warnings)
    payload["errors"] = list(analysis.errors)
    payload["movement_summary"] = asdict(analysis.movement_summary)
    return payload


def _playability_scalar_fields_are_valid(payload: dict[str, object]) -> bool:
    if any(type(payload[field]) is not str for field in _PLAYABILITY_STRING_FIELDS):
        return False
    if any(type(payload[field]) is not list for field in ("warnings", "errors")):
        return False
    if any(
        type(value) is not str
        for field in ("warnings", "errors")
        for value in payload[field]
    ):
        return False
    recommended = payload["recommended_next_preset"]
    return recommended is None or type(recommended) is str


def _validated_movement_summary_payload(
    payload: object,
) -> dict[str, int | None] | None:
    if type(payload) is not dict or set(payload) != _MOVEMENT_SUMMARY_FIELDS:
        return None
    if any(
        value is not None and (type(value) is not int or value < 0)
        for value in payload.values()
    ):
        return None
    return payload


def _deserialize_playability_analysis(
    payload: object,
) -> TopologyPlaygroundPlayabilityAnalysis | None:
    if type(payload) is not dict:
        return None
    if set(payload) != _PLAYABILITY_FIELDS:
        return None
    if not _playability_scalar_fields_are_valid(payload):
        return None
    movement_summary_payload = _validated_movement_summary_payload(
        payload["movement_summary"]
    )
    if movement_summary_payload is None:
        return None
    try:
        return TopologyPlaygroundPlayabilityAnalysis(
            status=payload["status"],
            validity=payload["validity"],
            explorer_usability=payload["explorer_usability"],
            rigid_playability=payload["rigid_playability"],
            summary=payload["summary"],
            validity_reason=payload["validity_reason"],
            explorer_reason=payload["explorer_reason"],
            rigid_reason=payload["rigid_reason"],
            warnings=tuple(payload["warnings"]),
            errors=tuple(payload["errors"]),
            movement_summary=TopologyPlaygroundMovementSummary(
                cell_count=movement_summary_payload.get("cell_count"),
                directed_edge_count=movement_summary_payload.get("directed_edge_count"),
                boundary_traversal_count=movement_summary_payload.get(
                    "boundary_traversal_count"
                ),
                component_count=movement_summary_payload.get("component_count"),
            ),
            recommended_next_preset=payload["recommended_next_preset"],
        )
    except ValueError:
        return None


def read_cached_playability_analysis(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    root_dir: Path | None = None,
) -> TopologyPlaygroundPlayabilityAnalysis | None:
    entry = read_topology_cache_entry(profile, dims=dims, root_dir=root_dir)
    if entry is None:
        return None
    return _deserialize_playability_analysis(entry.get("playability_analysis"))


def write_cached_playability_analysis(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    analysis: TopologyPlaygroundPlayabilityAnalysis,
    root_dir: Path | None = None,
) -> None:
    merge_topology_cache_entry(
        profile,
        dims=dims,
        root_dir=root_dir,
        playability_analysis=_serialize_playability_analysis(analysis),
    )


def topology_cache_usage(*, root_dir: Path | None = None) -> tuple[int, int]:
    cache_dir = topology_cache_dir_path(root_dir=root_dir)
    if not cache_dir.exists():
        return 0, 0
    file_count = 0
    total_bytes = 0
    for path in cache_dir.rglob("*"):
        if not path.is_file():
            continue
        file_count += 1
        total_bytes += int(path.stat().st_size)
    return file_count, total_bytes


def clear_topology_cache(*, root_dir: Path | None = None) -> tuple[int, int]:
    cache_dir = topology_cache_dir_path(root_dir=root_dir)
    file_count, total_bytes = topology_cache_usage(root_dir=root_dir)
    if cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)
    return file_count, total_bytes
