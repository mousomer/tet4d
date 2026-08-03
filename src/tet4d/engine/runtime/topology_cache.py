from __future__ import annotations

import hashlib
import json
import math
import shutil
from dataclasses import asdict
from itertools import product
from pathlib import Path
from typing import Any

from tet4d.engine.runtime.project_config import (
    explorer_topology_preview_cache_dir_path,
)
from tet4d.engine.runtime.settings_schema import (
    atomic_write_json,
    read_file_bytes,
    read_json_value_or_raise,
)
from tet4d.engine.runtime.topology_playground_state import (
    TopologyPlaygroundMovementSummary,
    TopologyPlaygroundPlayabilityAnalysis,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.engine.topology_explorer.contract_validation import (
    require_json_int,
    require_json_int_sequence,
    require_json_object,
    require_json_string,
)
from tet4d.engine.topology_explorer.domain_validation import (
    require_instance,
    require_integral,
    require_integral_sequence,
)
from tet4d.engine.topology_explorer.glue_model import MoveStep
from tet4d.engine.topology_explorer.glue_validate import (
    validate_explorer_topology_profile,
)
from tet4d.engine.topology_explorer.movement_graph import (
    MOVEMENT_GRAPH_ALGORITHM_VERSION,
    MovementEdge,
    deserialize_movement_graph_rows,
    movement_graph_rows,  # noqa: F401 - cold-read tests instrument the actual cache-module boundary.
    serialize_movement_graph_rows,
)
from tet4d.engine.topology_explorer.transport_resolver import (
    build_explorer_transport_resolver,
)

TOPOLOGY_CACHE_VERSION = 4
_CACHE_DATA_FIELDS = frozenset(
    {
        "graph_directed_edge_count",
        "graph_row_count",
        "graph_rows",
        "playability_analysis",
    }
)
_CACHE_METADATA_FIELDS = frozenset(
    {
        "cache_key",
        "cache_version",
        "dims",
        "graph_algorithm_version",
    }
)
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
        "graph_algorithm_version": MOVEMENT_GRAPH_ALGORITHM_VERSION,
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


def _cache_digest_file_path(cache_path: Path) -> Path:
    return cache_path.with_suffix(cache_path.suffix + ".sha256")


def _cache_entry_metadata_matches(
    payload: object,
    *,
    expected_key: str,
    expected_version: int,
    expected_dims: tuple[int, ...],
) -> bool:
    try:
        document = require_json_object(payload, "cache")
        if not document or not _CACHE_METADATA_FIELDS.issubset(document):
            return False
        if set(document) - _CACHE_METADATA_FIELDS - _CACHE_DATA_FIELDS:
            return False
        if (
            require_json_int(document["cache_version"], "cache.cache_version")
            != expected_version
        ):
            return False
        if (
            require_json_int(
                document["graph_algorithm_version"],
                "cache.graph_algorithm_version",
            )
            != MOVEMENT_GRAPH_ALGORITHM_VERSION
        ):
            return False
        if (
            require_json_string(document["cache_key"], "cache.cache_key")
            != expected_key
        ):
            return False
        stored_dims = require_json_int_sequence(document["dims"], "cache.dims")
        if stored_dims != expected_dims:
            return False
        _validate_cache_json_value(document)
        return True
    except (KeyError, TypeError, ValueError):
        return False


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
        encoded = read_file_bytes(cache_path)
        stored_digest = read_json_value_or_raise(_cache_digest_file_path(cache_path))
        if type(stored_digest) is not str:
            return None
        if hashlib.sha256(encoded).hexdigest() != stored_digest:
            return None
        payload = json.loads(encoded)
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
    payload["graph_algorithm_version"] = MOVEMENT_GRAPH_ALGORITHM_VERSION
    payload["cache_key"] = cache_key
    payload["dims"] = list(normalized_dims)
    _validate_cache_json_value(payload)
    atomic_write_json(cache_path, payload)
    atomic_write_json(
        _cache_digest_file_path(cache_path),
        hashlib.sha256(read_file_bytes(cache_path)).hexdigest(),
    )


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
    row_count = entry.get("graph_row_count")
    if type(row_count) is not int or row_count != len(cached_rows):
        return None
    directed_edge_count = entry.get("graph_directed_edge_count")
    actual_edge_count = sum(len(edges) for _, edges in cached_rows)
    if type(directed_edge_count) is not int or directed_edge_count != actual_edge_count:
        return None
    if not _cached_boundary_rows_match_profile(
        profile,
        dims=dims,
        cached_rows=cached_rows,
    ):
        return None
    return cached_rows


def _cached_boundary_rows_match_profile(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    cached_rows: tuple[tuple[tuple[int, ...], tuple[MovementEdge, ...]], ...],
) -> bool:
    validated_profile = validate_explorer_topology_profile(profile, dims=dims)
    resolver = build_explorer_transport_resolver(validated_profile, dims)
    edges_by_coord = {
        coord: {edge.step: edge for edge in edges} for coord, edges in cached_rows
    }
    for axis, size in enumerate(dims):
        for boundary_value, delta in ((0, -1), (size - 1, 1)):
            step = MoveStep(axis=axis, delta=delta)
            face_ranges = [range(value) for value in dims]
            face_ranges[axis] = (boundary_value,)
            for raw_coord in product(*face_ranges):
                coord = tuple(raw_coord)
                result = resolver.resolve_cell_step(coord, step)
                actual = edges_by_coord[coord].get(step)
                expected = (
                    None
                    if result.target is None
                    else MovementEdge(
                        step=step,
                        target=result.target,
                        traversal=result.traversal,
                    )
                )
                if actual != expected:
                    return False
    return True


def write_cached_graph_rows(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    graph_rows,
    cache_version: int = TOPOLOGY_CACHE_VERSION,
    root_dir: Path | None = None,
) -> None:
    serialized_rows = serialize_movement_graph_rows(graph_rows, dims=dims)
    merge_topology_cache_entry(
        profile,
        dims=dims,
        cache_version=cache_version,
        root_dir=root_dir,
        graph_rows=serialized_rows,
        graph_row_count=len(serialized_rows),
        graph_directed_edge_count=sum(len(row["edges"]) for row in serialized_rows),
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
