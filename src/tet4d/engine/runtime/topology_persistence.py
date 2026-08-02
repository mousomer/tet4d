from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, NoReturn

from tet4d.engine.topology_explorer import (
    AXIS_NAMES,
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
)
from tet4d.engine.topology_explorer.contract_validation import (
    TopologyRepresentationError,
    require_json_array,
    require_json_bool,
    require_json_int,
    require_json_int_sequence,
    require_json_object,
    require_json_string,
)
from tet4d.engine.topology_explorer.domain_validation import (
    require_bounded_integral,
)
from tet4d.engine.topology_explorer.glue_model import normalize_dimension

CURRENT_TOPOLOGY_PERSISTENCE_VERSION = 1
LEGACY_TOPOLOGY_PERSISTENCE_VERSION = 0
TOPOLOGY_PERSISTENCE_DIMENSIONS = (2, 3, 4)

_PROFILES_FIELD = "explorer_topology_profiles"
_PROFILE_FIELDS = frozenset(("dimension", "gluings"))
_PROFILE_SLOTS = frozenset(("2d", "3d", "4d"))
_SEAM_FIELDS = frozenset(("id", "enabled", "source", "target", "transform"))
_SEAM_REQUIRED = _SEAM_FIELDS - {"enabled"}
_BAD_PERM_RANK = "permutation has the wrong tangent rank"
_BAD_PERM_VALUE = "permutation is not complete"
_BAD_SIGN_RANK = "signs have the wrong tangent rank"
_BAD_SIGN_VALUE = "signs must contain only -1 or 1"
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
    source_version: int | None = None
    migrated: bool = False
    recovered: bool = False
    used_fallback: bool = False
    diagnostics: tuple[PersistenceDiagnostic, ...] = ()


BooleanPolicy = Literal["exact", "legacy_string_aliases"]
MissingEnabledPolicy = Literal["reject", "default_true_with_diagnostic"]
MissingDimensionPolicy = Literal["reject", "use_trusted_slot_with_diagnostic"]


@dataclass(frozen=True)
class PersistencePolicy:
    source_version: int
    migrated: bool
    boolean_policy: BooleanPolicy
    missing_enabled_policy: MissingEnabledPolicy
    missing_dimension_policy: MissingDimensionPolicy
    document_fields: frozenset[str]
    ignored_document_fields: tuple[str, ...] = ()
    ignored_profile_fields: tuple[str, ...] = ()
    ignored_seam_fields: tuple[str, ...] = ()


CURRENT_V1_POLICY = PersistencePolicy(
    1,
    False,
    "exact",
    "reject",
    "reject",
    frozenset(("version", _PROFILES_FIELD)),
)
LEGACY_V0_POLICY = PersistencePolicy(
    0,
    True,
    "legacy_string_aliases",
    "default_true_with_diagnostic",
    "use_trusted_slot_with_diagnostic",
    frozenset((_PROFILES_FIELD,)),
    ignored_document_fields=("metadata",),
    ignored_profile_fields=("metadata", "name"),
    ignored_seam_fields=("metadata",),
)


class _PersistenceFailure(ValueError):
    def __init__(self, code: str, path: str, message: str, value: object = None):
        super().__init__(message)
        self.code, self.path, self.value = code, path, value


def _fail(code: str, path: str, message: str, value: object = None) -> NoReturn:
    raise _PersistenceFailure(code, path, message, value)


def _freeze(value: object) -> object:
    if type(value) is dict:
        return tuple(
            (key, _freeze(item))
            for key, item in sorted(value.items(), key=lambda row: str(row[0]))
        )
    if type(value) is list:
        return tuple(_freeze(item) for item in value)
    return value


def _add(
    diagnostics: list[PersistenceDiagnostic],
    code: str,
    path: str,
    message: str,
    *,
    severity: DiagnosticSeverity = "warning",
    value: object = None,
    recovery: str | None = None,
) -> None:
    diagnostics.append(
        PersistenceDiagnostic(severity, code, path, message, _freeze(value), recovery)
    )


def _record(
    diagnostics: list[PersistenceDiagnostic],
    failure: _PersistenceFailure | TopologyRepresentationError,
) -> None:
    code = failure.code if isinstance(failure, _PersistenceFailure) else "wrong_type"
    diagnostics.append(
        PersistenceDiagnostic(
            "error", code, failure.path, str(failure), _freeze(failure.value)
        )
    )


def _fields(
    payload: dict[str, object],
    path: str,
    required: frozenset[str],
    allowed: frozenset[str],
    *,
    ignored: tuple[str, ...] = (),
    diagnostics: list[PersistenceDiagnostic] | None = None,
    ignored_message: str = "",
    ignored_recovery: str = "",
) -> None:
    missing = sorted(required - payload.keys())
    if missing:
        field = missing[0]
        _fail(
            "missing_required_field", f"{path}.{field}", f"{path}.{field} is required"
        )
    unknown = sorted(payload.keys() - allowed - set(ignored))
    if unknown:
        field = unknown[0]
        _fail(
            "unknown_field",
            f"{path}.{field}",
            f"{path}.{field} is not recognized",
            payload[field],
        )
    if diagnostics is not None:
        for field in ignored:
            if field in payload:
                _add(
                    diagnostics,
                    "unknown_field_ignored",
                    f"{path}.{field}",
                    ignored_message,
                    recovery=ignored_recovery,
                )


def empty_topology_profile(dimension: int) -> ExplorerTopologyProfile:
    return ExplorerTopologyProfile(dimension, ())


def _boundary_payload(boundary: BoundaryRef) -> dict[str, object]:
    return {"axis": AXIS_NAMES[boundary.axis], "side": boundary.side}


def _transform_payload(transform: BoundaryTransform) -> dict[str, object]:
    return {"permutation": list(transform.permutation), "signs": list(transform.signs)}


def topology_profile_payload(profile: ExplorerTopologyProfile) -> dict[str, object]:
    return {
        "dimension": profile.dimension,
        "gluings": [
            {
                "id": glue.glue_id,
                "enabled": glue.enabled,
                "source": _boundary_payload(glue.source),
                "target": _boundary_payload(glue.target),
                "transform": _transform_payload(glue.transform),
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
        _PROFILES_FIELD: {
            f"{dimension}d": topology_profile_payload(
                by_dimension.get(dimension, empty_topology_profile(dimension))
            )
            for dimension in TOPOLOGY_PERSISTENCE_DIMENSIONS
        },
    }


def _axis(value: object, dimension: int, path: str) -> int:
    if type(value) is str:
        label = value.strip().lower()
        if label not in AXIS_NAMES[:dimension]:
            _fail("invalid_axis", path, f"{path} is invalid", value)
        axis = AXIS_NAMES.index(label)
    else:
        axis = require_json_int(value, path)
    try:
        return require_bounded_integral(axis, path, minimum=0, maximum=dimension - 1)
    except ValueError:
        _fail("invalid_axis", path, f"{path} is outside the profile dimension", value)


def _boundary(value: object, dimension: int, path: str) -> BoundaryRef:
    payload = require_json_object(value, path)
    fields = frozenset(("axis", "side"))
    _fields(payload, path, fields, fields)
    side_path = f"{path}.side"
    side = require_json_string(payload["side"], side_path).strip()
    try:
        return BoundaryRef(
            dimension, _axis(payload["axis"], dimension, f"{path}.axis"), side
        )
    except ValueError:
        _fail("invalid_side", side_path, f"{side_path} must be '-' or '+'", side)


def _transform(value: object, dimension: int, path: str) -> BoundaryTransform:
    payload = require_json_object(value, path)
    fields = frozenset(("permutation", "signs"))
    _fields(payload, path, fields, fields)
    permutation_path, signs_path = f"{path}.permutation", f"{path}.signs"
    permutation_raw, signs_raw = payload["permutation"], payload["signs"]
    permutation = require_json_int_sequence(permutation_raw, permutation_path)
    signs = require_json_int_sequence(signs_raw, signs_path)
    tangent_rank = dimension - 1
    if len(permutation) != tangent_rank:
        _fail("invalid_permutation", permutation_path, _BAD_PERM_RANK, permutation_raw)
    if len(signs) != tangent_rank:
        _fail("invalid_sign", signs_path, _BAD_SIGN_RANK, signs_raw)
    try:
        return BoundaryTransform(permutation, signs)
    except ValueError as exc:
        if "permutation" in str(exc):
            _fail(
                "invalid_permutation",
                permutation_path,
                _BAD_PERM_VALUE,
                permutation_raw,
            )
        _fail("invalid_sign", signs_path, _BAD_SIGN_VALUE, signs_raw)


def _boolean(
    value: object,
    path: str,
    policy: BooleanPolicy,
    diagnostics: list[PersistenceDiagnostic],
) -> bool:
    try:
        return require_json_bool(value, path)
    except TopologyRepresentationError:
        pass
    if policy == "legacy_string_aliases" and type(value) is str:
        normalized = value.strip().lower()
        if normalized in {"true", "false"}:
            result = normalized == "true"
            _add(
                diagnostics,
                "legacy_boolean_alias",
                path,
                "legacy Boolean string migrated to a JSON Boolean",
                value=value,
                recovery=f"use {str(result).lower()}",
            )
            return result
    message = (
        f"{path} must be a JSON Boolean"
        if policy == "exact"
        else f"{path} is not an accepted legacy Boolean"
    )
    _fail("invalid_enabled", path, message, value)


def _seam(
    value: object,
    dimension: int,
    path: str,
    policy: PersistencePolicy,
    diagnostics: list[PersistenceDiagnostic],
) -> GluingDescriptor:
    payload = require_json_object(value, path)
    required = (
        _SEAM_FIELDS if policy.missing_enabled_policy == "reject" else _SEAM_REQUIRED
    )
    _fields(
        payload,
        path,
        required,
        _SEAM_FIELDS,
        ignored=policy.ignored_seam_fields,
        diagnostics=diagnostics,
        ignored_message="obsolete non-semantic legacy metadata was ignored",
        ignored_recovery="discard metadata",
    )
    enabled_path = f"{path}.enabled"
    if "enabled" in payload:
        enabled = _boolean(
            payload["enabled"], enabled_path, policy.boolean_policy, diagnostics
        )
    else:
        enabled = True
        _add(
            diagnostics,
            "missing_optional_field_defaulted",
            enabled_path,
            "legacy enabled omission defaulted to true",
            recovery="use true",
        )
    try:
        return GluingDescriptor(
            require_json_string(payload["id"], f"{path}.id"),
            _boundary(payload["source"], dimension, f"{path}.source"),
            _boundary(payload["target"], dimension, f"{path}.target"),
            _transform(payload["transform"], dimension, f"{path}.transform"),
            enabled,
        )
    except (_PersistenceFailure, TopologyRepresentationError):
        raise
    except ValueError as exc:
        raise _PersistenceFailure("malformed_seam", path, str(exc), value) from exc


def _seam_key(glue: GluingDescriptor) -> tuple[object, ...]:
    return glue.geometry_key()


def _resolve_seams(
    rows: list[tuple[int, GluingDescriptor]],
    path: str,
    diagnostics: list[PersistenceDiagnostic],
) -> tuple[GluingDescriptor, ...]:
    unique: list[tuple[int, GluingDescriptor]] = []
    seen: set[tuple[object, ...]] = set()
    for index, glue in rows:
        key = (*_seam_key(glue), glue.enabled)
        if key in seen:
            _add(
                diagnostics,
                "duplicate_seam_deduplicated",
                f"{path}[{index}]",
                "duplicate or reversed duplicate seam was removed",
                recovery="keep one semantic seam",
            )
        else:
            seen.add(key)
            unique.append((index, glue))

    conflicts: set[int] = set()
    for position, (left_index, left) in enumerate(unique):
        left_key = _seam_key(left)
        for right_index, right in unique[position + 1 :]:
            right_key = _seam_key(right)
            if (
                left.enabled
                and right.enabled
                and bool({left.source, left.target} & {right.source, right.target})
                or left_key == right_key
                and left.enabled != right.enabled
                or left.glue_id == right.glue_id
                and left_key != right_key
            ):
                conflicts.update((left_index, right_index))

    resolved = []
    for index, glue in unique:
        if index not in conflicts:
            resolved.append(glue)
            continue
        _add(
            diagnostics,
            "conflicting_seam_discarded",
            f"{path}[{index}]",
            "conflicting seam was discarded without first/last-wins behavior",
            severity="error",
            recovery="discard every conflicting row",
        )
    return tuple(resolved)


def _profile(
    value: object,
    dimension: int,
    path: str,
    policy: PersistencePolicy,
    diagnostics: list[PersistenceDiagnostic],
) -> ExplorerTopologyProfile:
    payload = require_json_object(value, path)
    _fields(
        payload,
        path,
        frozenset(("gluings",)),
        _PROFILE_FIELDS,
        ignored=policy.ignored_profile_fields,
        diagnostics=diagnostics,
        ignored_message="obsolete non-semantic legacy field was ignored",
        ignored_recovery="discard field",
    )
    dimension_path = f"{path}.dimension"
    if "dimension" in payload:
        stored_dimension = require_json_int(payload["dimension"], dimension_path)
        if stored_dimension != dimension:
            _fail(
                "invalid_dimension",
                dimension_path,
                "stored dimension does not match its trusted profile slot",
                stored_dimension,
            )
    elif policy.missing_dimension_policy == "reject":
        _fail("missing_required_field", dimension_path, f"{dimension_path} is required")
    else:
        _add(
            diagnostics,
            "missing_optional_field_defaulted",
            dimension_path,
            "legacy profile dimension defaulted from the trusted storage slot",
            recovery=f"use {dimension}",
        )

    seams_path = f"{path}.gluings"
    rows = []
    for index, raw_seam in enumerate(
        require_json_array(payload["gluings"], seams_path)
    ):
        item_path = f"{seams_path}[{index}]"
        try:
            rows.append(
                (index, _seam(raw_seam, dimension, item_path, policy, diagnostics))
            )
        except (_PersistenceFailure, TopologyRepresentationError) as failure:
            _record(diagnostics, failure)
            _add(
                diagnostics,
                "malformed_seam_discarded",
                item_path,
                "malformed seam was discarded",
                severity="error",
                recovery="leave its boundaries unglued",
            )
    return ExplorerTopologyProfile(
        dimension, _resolve_seams(rows, seams_path, diagnostics)
    )


def _fallback(
    dimension: int,
    source_version: int | None,
    migrated: bool,
    diagnostics: list[PersistenceDiagnostic],
) -> TopologyProfileLoadResult:
    _add(
        diagnostics,
        "malformed_profile_fallback",
        "$",
        "profile was replaced by the no-gluing fallback",
        severity="error",
        recovery=f"use empty {dimension}D topology",
    )
    return TopologyProfileLoadResult(
        empty_topology_profile(dimension),
        source_version,
        migrated,
        True,
        True,
        tuple(diagnostics),
    )


def fallback_topology_profile(
    dimension: int, diagnostic: PersistenceDiagnostic
) -> TopologyProfileLoadResult:
    normalized = normalize_dimension(dimension)
    return _fallback(normalized, None, False, [diagnostic])


def _load_profile_document(
    document: dict[str, object],
    *,
    trusted_dimension: int,
    policy: PersistencePolicy,
    initial_diagnostics: tuple[PersistenceDiagnostic, ...] = (),
) -> TopologyProfileLoadResult:
    diagnostics = list(initial_diagnostics)
    try:
        _fields(
            document,
            "$",
            frozenset((_PROFILES_FIELD,)),
            policy.document_fields,
            ignored=policy.ignored_document_fields,
            diagnostics=diagnostics,
            ignored_message="obsolete non-semantic legacy metadata was ignored",
            ignored_recovery="discard metadata",
        )
        profiles_path = f"$.{_PROFILES_FIELD}"
        profiles = require_json_object(document[_PROFILES_FIELD], profiles_path)
        _fields(profiles, profiles_path, frozenset(), _PROFILE_SLOTS)
        slot = f"{trusted_dimension}d"
        profile_path = f"{profiles_path}.{slot}"
        if slot not in profiles:
            _fail("missing_required_field", profile_path, f"{profile_path} is required")
        profile = _profile(
            profiles[slot], trusted_dimension, profile_path, policy, diagnostics
        )
    except (_PersistenceFailure, TopologyRepresentationError) as failure:
        _record(diagnostics, failure)
        return _fallback(
            trusted_dimension, policy.source_version, policy.migrated, diagnostics
        )
    return TopologyProfileLoadResult(
        profile,
        policy.source_version,
        policy.migrated,
        bool(diagnostics),
        False,
        tuple(diagnostics),
    )


def _load_current_topology_profile_v1(
    document: dict[str, object], *, trusted_dimension: int
) -> TopologyProfileLoadResult:
    return _load_profile_document(
        document, trusted_dimension=trusted_dimension, policy=CURRENT_V1_POLICY
    )


def _load_legacy_topology_profile_v0(
    document: dict[str, object],
    *,
    trusted_dimension: int,
    initial_diagnostics: tuple[PersistenceDiagnostic, ...],
) -> TopologyProfileLoadResult:
    return _load_profile_document(
        document,
        trusted_dimension=trusted_dimension,
        policy=LEGACY_V0_POLICY,
        initial_diagnostics=initial_diagnostics,
    )


def load_topology_profile_document(
    document: object, dimension: int
) -> TopologyProfileLoadResult:
    trusted_dimension = normalize_dimension(dimension)
    source_version: int | None = None
    try:
        payload = require_json_object(document, "$")
        if "version" not in payload:
            diagnostics: list[PersistenceDiagnostic] = []
            _add(
                diagnostics,
                "missing_version",
                "$.version",
                "unversioned explorer persistence was recognized as legacy v0",
                recovery="migrate to persistence version 1",
            )
            return _load_legacy_topology_profile_v0(
                payload,
                trusted_dimension=trusted_dimension,
                initial_diagnostics=tuple(diagnostics),
            )
        source_version = require_json_int(payload["version"], "$.version")
        if source_version != CURRENT_TOPOLOGY_PERSISTENCE_VERSION:
            _fail(
                "unsupported_version",
                "$.version",
                "topology persistence version is unsupported",
                source_version,
            )
        return _load_current_topology_profile_v1(
            payload, trusted_dimension=trusted_dimension
        )
    except (_PersistenceFailure, TopologyRepresentationError) as failure:
        diagnostics = []
        _record(diagnostics, failure)
        return _fallback(trusted_dimension, source_version, False, diagnostics)


__all__ = [
    "CURRENT_TOPOLOGY_PERSISTENCE_VERSION",
    "CURRENT_V1_POLICY",
    "LEGACY_TOPOLOGY_PERSISTENCE_VERSION",
    "LEGACY_V0_POLICY",
    "TOPOLOGY_PERSISTENCE_DIMENSIONS",
    "PersistenceDiagnostic",
    "TopologyProfileLoadResult",
    "empty_topology_profile",
    "fallback_topology_profile",
    "load_topology_profile_document",
    "topology_profile_payload",
    "topology_profiles_document",
]
