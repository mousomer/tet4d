from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tet4d.engine.topology_explorer import (
    AXIS_NAMES,
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
)
from tet4d.engine.topology_explorer.glue_model import normalize_dimension

CURRENT_TOPOLOGY_PERSISTENCE_VERSION = 1
LEGACY_TOPOLOGY_PERSISTENCE_VERSION = 0
TOPOLOGY_PERSISTENCE_DIMENSIONS = (2, 3, 4)

DiagnosticSeverity = Literal["warning", "error"]


@dataclass(frozen=True)
class PersistenceDiagnostic:
    severity: DiagnosticSeverity
    code: str
    path: str
    message: str
    original_value: object | None = None
    recovery: str | None = None


@dataclass(frozen=True)
class TopologyProfileLoadResult:
    profile: ExplorerTopologyProfile
    source_version: int | None
    migrated: bool
    recovered: bool
    used_fallback: bool
    diagnostics: tuple[PersistenceDiagnostic, ...]


class _PersistenceFailure(ValueError):
    def __init__(self, code: str, path: str, message: str, value: object = None):
        super().__init__(message)
        self.code = code
        self.path = path
        self.value = value


def _freeze_original(value: object) -> object:
    if type(value) is dict:
        return tuple(
            (key, _freeze_original(item))
            for key, item in sorted(value.items(), key=lambda row: str(row[0]))
        )
    if type(value) is list:
        return tuple(_freeze_original(item) for item in value)
    return value


def empty_topology_profile(dimension: int) -> ExplorerTopologyProfile:
    return ExplorerTopologyProfile(normalize_dimension(dimension), ())


def topology_profile_payload(profile: ExplorerTopologyProfile) -> dict[str, object]:
    return {
        "dimension": profile.dimension,
        "gluings": [
            {
                "id": glue.glue_id,
                "enabled": glue.enabled,
                "source": {
                    "axis": AXIS_NAMES[glue.source.axis],
                    "side": glue.source.side,
                },
                "target": {
                    "axis": AXIS_NAMES[glue.target.axis],
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


def topology_profiles_document(
    profiles: tuple[ExplorerTopologyProfile, ...],
) -> dict[str, object]:
    by_dimension = {profile.dimension: profile for profile in profiles}
    return {
        "version": CURRENT_TOPOLOGY_PERSISTENCE_VERSION,
        "explorer_topology_profiles": {
            f"{dimension}d": topology_profile_payload(
                by_dimension.get(dimension, empty_topology_profile(dimension))
            )
            for dimension in TOPOLOGY_PERSISTENCE_DIMENSIONS
        },
    }


def _diagnostic(failure: _PersistenceFailure) -> PersistenceDiagnostic:
    return PersistenceDiagnostic(
        severity="error",
        code=failure.code,
        path=failure.path,
        message=str(failure),
        original_value=_freeze_original(failure.value),
    )


def _require_object(value: object, path: str) -> dict[str, object]:
    if type(value) is not dict:
        raise _PersistenceFailure("wrong_type", path, f"{path} must be an object")
    return value


def _require_array(value: object, path: str) -> list[object]:
    if type(value) is not list:
        raise _PersistenceFailure("wrong_type", path, f"{path} must be an array")
    return value


def _require_int(value: object, path: str) -> int:
    if type(value) is not int:
        raise _PersistenceFailure(
            "wrong_type", path, f"{path} must be an integer", value
        )
    return value


def _require_string(value: object, path: str) -> str:
    if type(value) is not str:
        raise _PersistenceFailure("wrong_type", path, f"{path} must be a string", value)
    return value


def _require_fields(
    payload: dict[str, object],
    required: frozenset[str],
    path: str,
) -> None:
    missing = sorted(required - payload.keys())
    if missing:
        field = missing[0]
        raise _PersistenceFailure(
            "missing_required_field",
            f"{path}.{field}",
            f"{path}.{field} is required",
        )
    unknown = sorted(payload.keys() - required)
    if unknown:
        field = unknown[0]
        raise _PersistenceFailure(
            "unknown_field",
            f"{path}.{field}",
            f"{path}.{field} is not part of the current format",
            payload[field],
        )


def _axis_index(value: object, dimension: int, path: str) -> int:
    if type(value) is int:
        axis = value
    elif type(value) is str:
        label = value.strip().lower()
        if label not in AXIS_NAMES[:dimension]:
            raise _PersistenceFailure("invalid_axis", path, f"{path} is invalid", value)
        axis = AXIS_NAMES.index(label)
    else:
        raise _PersistenceFailure(
            "wrong_type", path, f"{path} must be an axis label or integer", value
        )
    if axis < 0 or axis >= dimension:
        raise _PersistenceFailure(
            "invalid_axis", path, f"{path} is outside the profile dimension", value
        )
    return axis


def _parse_boundary(value: object, dimension: int, path: str) -> BoundaryRef:
    payload = _require_object(value, path)
    _require_fields(payload, frozenset({"axis", "side"}), path)
    side = _require_string(payload["side"], f"{path}.side").strip()
    if side not in {"-", "+"}:
        raise _PersistenceFailure(
            "invalid_side", f"{path}.side", f"{path}.side must be '-' or '+'", side
        )
    return BoundaryRef(
        dimension,
        _axis_index(payload["axis"], dimension, f"{path}.axis"),
        side,
    )


def _parse_transform(value: object, dimension: int, path: str) -> BoundaryTransform:
    payload = _require_object(value, path)
    _require_fields(payload, frozenset({"permutation", "signs"}), path)
    permutation_raw = _require_array(payload["permutation"], f"{path}.permutation")
    signs_raw = _require_array(payload["signs"], f"{path}.signs")
    expected_length = dimension - 1
    if len(permutation_raw) != expected_length:
        raise _PersistenceFailure(
            "invalid_permutation",
            f"{path}.permutation",
            "permutation has the wrong tangent rank",
            permutation_raw,
        )
    if len(signs_raw) != expected_length:
        raise _PersistenceFailure(
            "invalid_sign",
            f"{path}.signs",
            "signs have the wrong tangent rank",
            signs_raw,
        )
    permutation = tuple(
        _require_int(item, f"{path}.permutation[{index}]")
        for index, item in enumerate(permutation_raw)
    )
    signs = tuple(
        _require_int(item, f"{path}.signs[{index}]")
        for index, item in enumerate(signs_raw)
    )
    if tuple(sorted(permutation)) != tuple(range(expected_length)):
        raise _PersistenceFailure(
            "invalid_permutation",
            f"{path}.permutation",
            "permutation is not complete",
            permutation_raw,
        )
    if any(sign not in {-1, 1} for sign in signs):
        raise _PersistenceFailure(
            "invalid_sign",
            f"{path}.signs",
            "signs must contain only -1 or 1",
            signs_raw,
        )
    return BoundaryTransform(permutation, signs)


def _parse_legacy_boolean(
    value: object,
    path: str,
    diagnostics: list[PersistenceDiagnostic],
) -> bool:
    if type(value) is bool:
        return value
    if type(value) is str and value.strip().lower() in {"true", "false"}:
        result = value.strip().lower() == "true"
        diagnostics.append(
            PersistenceDiagnostic(
                "warning",
                "legacy_boolean_alias",
                path,
                "legacy Boolean string migrated to a JSON Boolean",
                value,
                f"use {str(result).lower()}",
            )
        )
        return result
    raise _PersistenceFailure(
        "invalid_enabled", path, f"{path} is not an accepted legacy Boolean", value
    )


def _parse_gluing(
    value: object,
    dimension: int,
    path: str,
    *,
    legacy: bool,
    diagnostics: list[PersistenceDiagnostic],
) -> GluingDescriptor:
    payload = _require_object(value, path)
    required = {"id", "source", "target", "transform"}
    if not legacy:
        required.add("enabled")
    missing = sorted(required - payload.keys())
    if missing:
        field = missing[0]
        raise _PersistenceFailure(
            "missing_required_field", f"{path}.{field}", f"{path}.{field} is required"
        )
    allowed = required | ({"enabled", "metadata"} if legacy else set())
    unknown = sorted(payload.keys() - allowed)
    if unknown:
        field = unknown[0]
        raise _PersistenceFailure(
            "unknown_field",
            f"{path}.{field}",
            f"{path}.{field} is not recognized",
            payload[field],
        )
    if legacy and "metadata" in payload:
        diagnostics.append(
            PersistenceDiagnostic(
                "warning",
                "unknown_field_ignored",
                f"{path}.metadata",
                "obsolete non-semantic legacy metadata was ignored",
                recovery="discard metadata",
            )
        )
    if "enabled" not in payload:
        enabled = True
        diagnostics.append(
            PersistenceDiagnostic(
                "warning",
                "missing_optional_field_defaulted",
                f"{path}.enabled",
                "legacy enabled omission defaulted to true",
                recovery="use true",
            )
        )
    elif legacy:
        enabled = _parse_legacy_boolean(
            payload["enabled"], f"{path}.enabled", diagnostics
        )
    else:
        enabled_raw = payload["enabled"]
        if type(enabled_raw) is not bool:
            raise _PersistenceFailure(
                "invalid_enabled",
                f"{path}.enabled",
                f"{path}.enabled must be a JSON Boolean",
                enabled_raw,
            )
        enabled = enabled_raw
    try:
        return GluingDescriptor(
            glue_id=_require_string(payload["id"], f"{path}.id"),
            enabled=enabled,
            source=_parse_boundary(payload["source"], dimension, f"{path}.source"),
            target=_parse_boundary(payload["target"], dimension, f"{path}.target"),
            transform=_parse_transform(
                payload["transform"], dimension, f"{path}.transform"
            ),
        )
    except _PersistenceFailure:
        raise
    except ValueError as exc:
        raise _PersistenceFailure("malformed_seam", path, str(exc), value) from exc


def _boundary_key(boundary: BoundaryRef) -> tuple[int, int]:
    return boundary.axis, 0 if boundary.side == "-" else 1


def _semantic_seam_key(glue: GluingDescriptor) -> tuple[object, ...]:
    if _boundary_key(glue.source) <= _boundary_key(glue.target):
        source, target, transform = glue.source, glue.target, glue.transform
    else:
        source, target, transform = glue.target, glue.source, glue.transform.inverse()
    return (
        source.axis,
        source.side,
        target.axis,
        target.side,
        transform.permutation,
        transform.signs,
    )


def _resolve_duplicates_and_conflicts(
    rows: list[tuple[int, GluingDescriptor]],
    base_path: str,
    diagnostics: list[PersistenceDiagnostic],
) -> tuple[GluingDescriptor, ...]:
    unique: list[tuple[int, GluingDescriptor]] = []
    seen: dict[tuple[object, ...], tuple[int, GluingDescriptor]] = {}
    for index, glue in rows:
        key = (*_semantic_seam_key(glue), glue.enabled)
        if key in seen:
            diagnostics.append(
                PersistenceDiagnostic(
                    "warning",
                    "duplicate_seam_deduplicated",
                    f"{base_path}[{index}]",
                    "duplicate or reversed duplicate seam was removed",
                    recovery="keep one semantic seam",
                )
            )
            continue
        seen[key] = (index, glue)
        unique.append((index, glue))

    conflicts: set[int] = set()
    for left_pos, (left_index, left) in enumerate(unique):
        left_boundaries = {left.source, left.target}
        left_geometry = _semantic_seam_key(left)
        for right_index, right in unique[left_pos + 1 :]:
            same_geometry = left_geometry == _semantic_seam_key(right)
            shares_active_boundary = (
                left.enabled
                and right.enabled
                and bool(left_boundaries & {right.source, right.target})
            )
            enabled_conflict = same_geometry and left.enabled != right.enabled
            duplicate_id_conflict = left.glue_id == right.glue_id and not same_geometry
            if shares_active_boundary or enabled_conflict or duplicate_id_conflict:
                conflicts.update({left_index, right_index})

    resolved = []
    for index, glue in unique:
        if index in conflicts:
            diagnostics.append(
                PersistenceDiagnostic(
                    "error",
                    "conflicting_seam_discarded",
                    f"{base_path}[{index}]",
                    "conflicting seam was discarded without first/last-wins behavior",
                    recovery="discard every conflicting row",
                )
            )
        else:
            resolved.append(glue)
    return tuple(resolved)


def _parse_profile(
    value: object,
    dimension: int,
    path: str,
    *,
    legacy: bool,
    diagnostics: list[PersistenceDiagnostic],
) -> ExplorerTopologyProfile:
    payload = _require_object(value, path)
    if "gluings" not in payload:
        raise _PersistenceFailure(
            "missing_required_field", f"{path}.gluings", f"{path}.gluings is required"
        )
    allowed = {"dimension", "gluings"} | ({"metadata", "name"} if legacy else set())
    unknown = sorted(payload.keys() - allowed)
    if unknown:
        field = unknown[0]
        raise _PersistenceFailure(
            "unknown_field",
            f"{path}.{field}",
            f"{path}.{field} is not recognized",
            payload[field],
        )
    for obsolete in ("metadata", "name"):
        if legacy and obsolete in payload:
            diagnostics.append(
                PersistenceDiagnostic(
                    "warning",
                    "unknown_field_ignored",
                    f"{path}.{obsolete}",
                    "obsolete non-semantic legacy field was ignored",
                    recovery="discard field",
                )
            )
    if "dimension" not in payload:
        if not legacy:
            raise _PersistenceFailure(
                "missing_required_field",
                f"{path}.dimension",
                f"{path}.dimension is required",
            )
        diagnostics.append(
            PersistenceDiagnostic(
                "warning",
                "missing_optional_field_defaulted",
                f"{path}.dimension",
                "legacy profile dimension defaulted from the trusted storage slot",
                recovery=f"use {dimension}",
            )
        )
    else:
        stored_dimension = _require_int(payload["dimension"], f"{path}.dimension")
        if stored_dimension != dimension:
            raise _PersistenceFailure(
                "invalid_dimension",
                f"{path}.dimension",
                "stored dimension does not match its trusted profile slot",
                stored_dimension,
            )

    raw_gluings = _require_array(payload["gluings"], f"{path}.gluings")
    rows: list[tuple[int, GluingDescriptor]] = []
    for index, raw_glue in enumerate(raw_gluings):
        seam_path = f"{path}.gluings[{index}]"
        try:
            rows.append(
                (
                    index,
                    _parse_gluing(
                        raw_glue,
                        dimension,
                        seam_path,
                        legacy=legacy,
                        diagnostics=diagnostics,
                    ),
                )
            )
        except _PersistenceFailure as failure:
            diagnostics.append(_diagnostic(failure))
            diagnostics.append(
                PersistenceDiagnostic(
                    "error",
                    "malformed_seam_discarded",
                    seam_path,
                    "malformed seam was discarded",
                    recovery="leave its boundaries unglued",
                )
            )
    gluings = _resolve_duplicates_and_conflicts(rows, f"{path}.gluings", diagnostics)
    return ExplorerTopologyProfile(dimension, gluings)


def _fallback_result(
    dimension: int,
    source_version: int | None,
    diagnostics: list[PersistenceDiagnostic],
) -> TopologyProfileLoadResult:
    diagnostics.append(
        PersistenceDiagnostic(
            "error",
            "malformed_profile_fallback",
            "$",
            "profile was replaced by the no-gluing fallback",
            recovery=f"use empty {dimension}D topology",
        )
    )
    return TopologyProfileLoadResult(
        empty_topology_profile(dimension),
        source_version,
        migrated=source_version == LEGACY_TOPOLOGY_PERSISTENCE_VERSION,
        recovered=True,
        used_fallback=True,
        diagnostics=tuple(diagnostics),
    )


def _load_profile_slot(
    payload: dict[str, object],
    dimension: int,
    *,
    legacy: bool,
    diagnostics: list[PersistenceDiagnostic],
) -> ExplorerTopologyProfile:
    if "explorer_topology_profiles" not in payload:
        raise _PersistenceFailure(
            "missing_required_field",
            "$.explorer_topology_profiles",
            "profile collection is required",
        )
    profiles = _require_object(
        payload["explorer_topology_profiles"], "$.explorer_topology_profiles"
    )
    unknown_slots = sorted(profiles.keys() - {"2d", "3d", "4d"})
    if unknown_slots:
        field = unknown_slots[0]
        raise _PersistenceFailure(
            "unknown_field",
            f"$.explorer_topology_profiles.{field}",
            "profile slot is not recognized",
            profiles[field],
        )
    profile_path = f"$.explorer_topology_profiles.{dimension}d"
    if f"{dimension}d" not in profiles:
        raise _PersistenceFailure(
            "missing_required_field", profile_path, f"{profile_path} is required"
        )
    return _parse_profile(
        profiles[f"{dimension}d"],
        dimension,
        profile_path,
        legacy=legacy,
        diagnostics=diagnostics,
    )


def _load_current_topology_profile_v1(
    payload: dict[str, object],
    dimension: int,
    diagnostics: list[PersistenceDiagnostic],
) -> ExplorerTopologyProfile:
    allowed = {"version", "explorer_topology_profiles"}
    unexpected = sorted(set(payload) - allowed)
    if unexpected:
        field = unexpected[0]
        raise _PersistenceFailure(
            "unknown_field",
            f"$.{field}",
            f"$.{field} is not part of persistence version 1",
            payload[field],
        )
    return _load_profile_slot(payload, dimension, legacy=False, diagnostics=diagnostics)


def _load_legacy_topology_profile_v0(
    payload: dict[str, object],
    dimension: int,
    diagnostics: list[PersistenceDiagnostic],
) -> ExplorerTopologyProfile:
    allowed = {"explorer_topology_profiles", "metadata"}
    unexpected = sorted(set(payload) - allowed)
    if unexpected:
        field = unexpected[0]
        raise _PersistenceFailure(
            "unknown_field",
            f"$.{field}",
            f"$.{field} is not recognized legacy v0 data",
            payload[field],
        )
    if "metadata" in payload:
        diagnostics.append(
            PersistenceDiagnostic(
                "warning",
                "unknown_field_ignored",
                "$.metadata",
                "obsolete non-semantic legacy metadata was ignored",
                recovery="discard metadata",
            )
        )
    return _load_profile_slot(payload, dimension, legacy=True, diagnostics=diagnostics)


def load_topology_profile_document(
    document: object,
    dimension: int,
) -> TopologyProfileLoadResult:
    normalized_dimension = normalize_dimension(dimension)
    diagnostics: list[PersistenceDiagnostic] = []
    source_version: int | None = None
    try:
        payload = _require_object(document, "$")
        if "version" not in payload:
            source_version = LEGACY_TOPOLOGY_PERSISTENCE_VERSION
            legacy = True
            diagnostics.append(
                PersistenceDiagnostic(
                    "warning",
                    "missing_version",
                    "$.version",
                    "unversioned explorer persistence was recognized as legacy v0",
                    recovery="migrate to persistence version 1",
                )
            )
        else:
            source_version = _require_int(payload["version"], "$.version")
            if source_version != CURRENT_TOPOLOGY_PERSISTENCE_VERSION:
                raise _PersistenceFailure(
                    "unsupported_version",
                    "$.version",
                    "topology persistence version is unsupported",
                    source_version,
                )
            legacy = False

        if legacy:
            profile = _load_legacy_topology_profile_v0(
                payload, normalized_dimension, diagnostics
            )
        else:
            profile = _load_current_topology_profile_v1(
                payload, normalized_dimension, diagnostics
            )
    except _PersistenceFailure as failure:
        diagnostics.append(_diagnostic(failure))
        return _fallback_result(normalized_dimension, source_version, diagnostics)

    recovered = any(
        diagnostic.code not in {"missing_version"} or diagnostic.recovery is not None
        for diagnostic in diagnostics
    )
    return TopologyProfileLoadResult(
        profile,
        source_version,
        migrated=legacy,
        recovered=recovered,
        used_fallback=False,
        diagnostics=tuple(diagnostics),
    )


__all__ = [
    "CURRENT_TOPOLOGY_PERSISTENCE_VERSION",
    "LEGACY_TOPOLOGY_PERSISTENCE_VERSION",
    "TOPOLOGY_PERSISTENCE_DIMENSIONS",
    "PersistenceDiagnostic",
    "TopologyProfileLoadResult",
    "empty_topology_profile",
    "load_topology_profile_document",
    "topology_profile_payload",
    "topology_profiles_document",
]
