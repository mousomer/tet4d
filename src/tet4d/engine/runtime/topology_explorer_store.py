from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path

from tet4d.engine.runtime.project_config import (
    explorer_topology_profiles_file_default_path,
)
from tet4d.engine.runtime.settings_schema import write_json_object
from tet4d.engine.runtime.topology_persistence import (
    TOPOLOGY_PERSISTENCE_DIMENSIONS,
    PersistenceDiagnostic,
    TopologyProfileLoadResult,
    empty_topology_profile,
    load_topology_profile_document,
    topology_profiles_document,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.engine.topology_explorer.glue_model import normalize_dimension

logger = logging.getLogger(__name__)


def _file_path(root_dir: Path | None = None) -> Path:
    return explorer_topology_profiles_file_default_path(root_dir=root_dir)


def _default_result(dimension: int) -> TopologyProfileLoadResult:
    return TopologyProfileLoadResult(
        profile=empty_topology_profile(dimension),
        source_version=None,
        migrated=False,
        recovered=False,
        used_fallback=False,
        diagnostics=(),
    )


def _read_document(root_dir: Path | None = None) -> tuple[object | None, str | None]:
    path = _file_path(root_dir=root_dir)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, None
    except OSError as exc:
        return None, f"Failed reading explorer topology persistence: {exc}"
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        return None, f"Invalid explorer topology persistence JSON: {exc}"


def _io_fallback(dimension: int, message: str) -> TopologyProfileLoadResult:
    return TopologyProfileLoadResult(
        profile=empty_topology_profile(dimension),
        source_version=None,
        migrated=False,
        recovered=True,
        used_fallback=True,
        diagnostics=(
            PersistenceDiagnostic(
                "error",
                "malformed_json",
                "$",
                message,
            ),
            PersistenceDiagnostic(
                "error",
                "malformed_profile_fallback",
                "$",
                "profile was replaced by the no-gluing fallback",
                recovery=f"use empty {dimension}D topology",
            ),
        ),
    )


def load_explorer_topology_profile(
    dimension: int,
    *,
    root_dir: Path | None = None,
) -> TopologyProfileLoadResult:
    normalized_dimension = normalize_dimension(dimension)
    if normalized_dimension not in TOPOLOGY_PERSISTENCE_DIMENSIONS:
        raise ValueError("dimension must be 2, 3, or 4 for explorer topology profiles")
    document, error = _read_document(root_dir=root_dir)
    if error is not None:
        return _io_fallback(normalized_dimension, error)
    if document is None:
        return _default_result(normalized_dimension)
    return load_topology_profile_document(document, normalized_dimension)


def load_explorer_topology_profiles_payload(
    root_dir: Path | None = None,
) -> dict[str, object]:
    results = tuple(
        load_explorer_topology_profile(dimension, root_dir=root_dir)
        for dimension in TOPOLOGY_PERSISTENCE_DIMENSIONS
    )
    for result in results:
        report_topology_persistence_diagnostics(result)
    profiles = tuple(result.profile for result in results)
    return topology_profiles_document(profiles)


def report_topology_persistence_diagnostics(
    result: TopologyProfileLoadResult,
) -> None:
    for diagnostic in result.diagnostics:
        message = (
            f"Topology persistence {diagnostic.code} at {diagnostic.path}: "
            f"{diagnostic.message}"
        )
        warnings.warn(message, RuntimeWarning, stacklevel=2)
        logger.warning(message)


def save_explorer_topology_profile(
    profile: ExplorerTopologyProfile,
    *,
    root_dir: Path | None = None,
) -> tuple[bool, str]:
    if profile.dimension not in TOPOLOGY_PERSISTENCE_DIMENSIONS:
        return False, "dimension must be 2, 3, or 4 for explorer topology profiles"
    results = {
        dimension: load_explorer_topology_profile(dimension, root_dir=root_dir)
        for dimension in TOPOLOGY_PERSISTENCE_DIMENSIONS
    }
    profiles = tuple(
        profile if dimension == profile.dimension else results[dimension].profile
        for dimension in TOPOLOGY_PERSISTENCE_DIMENSIONS
    )
    path = _file_path(root_dir=root_dir)
    try:
        write_json_object(path, topology_profiles_document(profiles))
    except OSError as exc:
        return False, f"Failed saving explorer topology profile: {exc}"
    recovery_count = sum(len(result.diagnostics) for result in results.values())
    suffix = (
        f"; recovered {recovery_count} stored persistence issue(s)"
        if recovery_count
        else ""
    )
    return True, f"Saved explorer topology profile for {profile.dimension}D{suffix}"


__all__ = [
    "load_explorer_topology_profile",
    "load_explorer_topology_profiles_payload",
    "report_topology_persistence_diagnostics",
    "save_explorer_topology_profile",
]
