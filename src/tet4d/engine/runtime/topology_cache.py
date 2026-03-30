from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from tet4d.engine.runtime.project_config import (
    explorer_topology_preview_cache_dir_path,
)
from tet4d.engine.runtime.settings_schema import (
    atomic_write_json,
    read_json_object_or_empty,
)
from tet4d.engine.runtime.topology_playground_state import (
    TopologyPlaygroundMovementSummary,
    TopologyPlaygroundPlayabilityAnalysis,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.engine.topology_explorer.movement_graph import (
    deserialize_movement_graph_rows,
    serialize_movement_graph_rows,
)

TOPOLOGY_CACHE_VERSION = 2


def _profile_signature_payload(
    profile: ExplorerTopologyProfile,
) -> dict[str, object]:
    return {
        "dimension": int(profile.dimension),
        "gluings": [
            {
                "id": glue.glue_id,
                "enabled": bool(glue.enabled),
                "source": {
                    "axis": int(glue.source.axis),
                    "side": str(glue.source.side),
                },
                "target": {
                    "axis": int(glue.target.axis),
                    "side": str(glue.target.side),
                },
                "transform": {
                    "permutation": [int(value) for value in glue.transform.permutation],
                    "signs": [int(value) for value in glue.transform.signs],
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
    payload = {
        "cache_version": TOPOLOGY_CACHE_VERSION,
        "dims": [int(value) for value in dims],
        "profile": _profile_signature_payload(profile),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def topology_cache_dir_path(*, root_dir: Path | None = None) -> Path:
    return explorer_topology_preview_cache_dir_path(root_dir=root_dir)


def topology_cache_file_path(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    root_dir: Path | None = None,
) -> Path:
    return topology_cache_dir_path(root_dir=root_dir) / f"{topology_cache_key(profile, dims=dims)}.json"


def read_topology_cache_entry(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    cache_version: int = TOPOLOGY_CACHE_VERSION,
    root_dir: Path | None = None,
) -> dict[str, Any] | None:
    payload = read_json_object_or_empty(
        topology_cache_file_path(profile, dims=dims, root_dir=root_dir)
    )
    if not isinstance(payload, dict) or not payload:
        return None
    if int(payload.get("cache_version", -1)) != int(cache_version):
        return None
    return payload


def write_topology_cache_entry(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    entry: dict[str, Any],
    cache_version: int = TOPOLOGY_CACHE_VERSION,
    root_dir: Path | None = None,
) -> None:
    cache_path = topology_cache_file_path(profile, dims=dims, root_dir=root_dir)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(entry)
    payload["cache_version"] = int(cache_version)
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
    return deserialize_movement_graph_rows(
        entry.get("graph_rows"),
        dimension=profile.dimension,
    )


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
        graph_rows=serialize_movement_graph_rows(graph_rows),
    )


def _serialize_playability_analysis(
    analysis: TopologyPlaygroundPlayabilityAnalysis,
) -> dict[str, object]:
    payload = asdict(analysis)
    payload["warnings"] = list(analysis.warnings)
    payload["errors"] = list(analysis.errors)
    payload["movement_summary"] = asdict(analysis.movement_summary)
    return payload


def _deserialize_playability_analysis(
    payload: object,
) -> TopologyPlaygroundPlayabilityAnalysis | None:
    if not isinstance(payload, dict):
        return None
    movement_summary_payload = payload.get("movement_summary", {})
    if not isinstance(movement_summary_payload, dict):
        return None
    try:
        return TopologyPlaygroundPlayabilityAnalysis(
            status=str(payload.get("status", "")),
            validity=str(payload.get("validity", "")),
            explorer_usability=str(payload.get("explorer_usability", "")),
            rigid_playability=str(payload.get("rigid_playability", "")),
            summary=str(payload.get("summary", "")),
            validity_reason=str(payload.get("validity_reason", "")),
            explorer_reason=str(payload.get("explorer_reason", "")),
            rigid_reason=str(payload.get("rigid_reason", "")),
            warnings=tuple(str(value) for value in payload.get("warnings", ())),
            errors=tuple(str(value) for value in payload.get("errors", ())),
            movement_summary=TopologyPlaygroundMovementSummary(
                cell_count=movement_summary_payload.get("cell_count"),
                directed_edge_count=movement_summary_payload.get(
                    "directed_edge_count"
                ),
                boundary_traversal_count=movement_summary_payload.get(
                    "boundary_traversal_count"
                ),
                component_count=movement_summary_payload.get("component_count"),
            ),
            recommended_next_preset=(
                None
                if payload.get("recommended_next_preset") is None
                else str(payload.get("recommended_next_preset"))
            ),
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
