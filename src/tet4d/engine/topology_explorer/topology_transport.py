from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tet4d.generated.topology_contract_v1 import (
    AXIS_NAMES,
    CONTRACT_VERSION,
    MAXIMUM_AXIS_LENGTH,
    MAXIMUM_INDEXABLE_VOLUME,
    MAXIMUM_RANK,
    MINIMUM_AXIS_LENGTH,
    MINIMUM_RANK,
    VALID_BOUNDARY_SIDES,
    VALID_MOVEMENT_DELTAS,
    VALID_TRANSFORM_SIGNS,
)


@dataclass(frozen=True)
class TopologyTransportError(ValueError):
    code: str
    path: str
    expected: str
    actual: str
    message: str

    def __str__(self) -> str:
        return self.message


def _category(value: object) -> str:
    if value is None:
        return "null"
    if type(value) is bool:
        return "boolean"
    if type(value) is int:
        return "integer"
    if type(value) is float:
        return "float"
    if type(value) is str:
        return "string"
    if type(value) is list:
        return "array"
    if type(value) is dict:
        return "object"
    return type(value).__name__


def _fail(code: str, path: str, expected: str, actual: str, message: str) -> None:
    raise TopologyTransportError(code, path, expected, actual, message)


def _object(value: object, path: str) -> dict[str, object]:
    if type(value) is not dict:
        _fail(
            "wrong_type", path, "object", _category(value), f"{path} must be an object"
        )
    assert isinstance(value, dict)
    if any(type(key) is not str for key in value):
        _fail(
            "wrong_type",
            path,
            "object with string keys",
            "non-string key",
            f"{path} keys must be strings",
        )
    return value


def _array(value: object, path: str) -> list[object]:
    if type(value) is not list:
        _fail("wrong_type", path, "array", _category(value), f"{path} must be an array")
    assert isinstance(value, list)
    return value


def _exact_fields(
    value: Mapping[str, object], fields: frozenset[str], path: str
) -> None:
    missing = sorted(fields.difference(value))
    if missing:
        field = missing[0]
        _fail(
            "missing_field",
            f"{path}.{field}",
            "present field",
            "missing",
            f"{path}.{field} is required",
        )
    unknown = sorted(set(value).difference(fields))
    if unknown:
        field = unknown[0]
        _fail(
            "unknown_required_value",
            f"{path}.{field}",
            "known field",
            "unknown field",
            f"{path}.{field} is not supported",
        )


def _integer(value: object, path: str) -> int:
    if type(value) is not int:
        _fail(
            "wrong_type",
            path,
            "integer",
            _category(value),
            f"{path} must be an integer",
        )
    assert isinstance(value, int)
    return value


def _boolean(value: object, path: str) -> bool:
    if type(value) is not bool:
        _fail(
            "wrong_type", path, "boolean", _category(value), f"{path} must be a boolean"
        )
    assert isinstance(value, bool)
    return value


def _string(value: object, path: str) -> str:
    if type(value) is not str:
        _fail(
            "wrong_type", path, "string", _category(value), f"{path} must be a string"
        )
    assert isinstance(value, str)
    return value


def _integer_array(value: object, path: str) -> list[int]:
    return [
        _integer(item, f"{path}[{index}]")
        for index, item in enumerate(_array(value, path))
    ]


def _boundary(value: object, path: str, rank: int) -> dict[str, object]:
    row = _object(value, path)
    _exact_fields(row, frozenset(("axis", "side")), path)
    axis_name = _string(row["axis"], f"{path}.axis").strip().lower()
    if axis_name not in AXIS_NAMES[:rank]:
        _fail(
            "invalid_axis",
            f"{path}.axis",
            "axis name within profile rank",
            axis_name,
            f"{path}.axis is outside the profile rank",
        )
    side = _string(row["side"], f"{path}.side").strip()
    if side not in VALID_BOUNDARY_SIDES:
        _fail(
            "invalid_side",
            f"{path}.side",
            "- or +",
            side,
            f"{path}.side must be a contract boundary side",
        )
    return {"axis": AXIS_NAMES.index(axis_name), "side": side}


def _transform(value: object, path: str, rank: int) -> dict[str, list[int]]:
    row = _object(value, path)
    _exact_fields(row, frozenset(("permutation", "signs")), path)
    permutation = _integer_array(row["permutation"], f"{path}.permutation")
    signs = _integer_array(row["signs"], f"{path}.signs")
    tangent_rank = rank - 1
    if len(permutation) != tangent_rank:
        _fail(
            "invalid_permutation",
            f"{path}.permutation",
            "one entry per tangent axis",
            str(len(permutation)),
            f"{path}.permutation length must equal rank minus one",
        )
    if len(signs) != tangent_rank:
        _fail(
            "invalid_sign",
            f"{path}.signs",
            "one sign per tangent axis",
            str(len(signs)),
            f"{path}.signs length must equal rank minus one",
        )
    seen: set[int] = set()
    for index, item in enumerate(permutation):
        if item < 0 or item >= tangent_rank or item in seen:
            _fail(
                "invalid_permutation",
                f"{path}.permutation[{index}]",
                "unique tangent-axis index",
                str(item),
                f"{path}.permutation must be a complete permutation",
            )
        seen.add(item)
        if signs[index] not in VALID_TRANSFORM_SIGNS:
            _fail(
                "invalid_sign",
                f"{path}.signs[{index}]",
                "-1 or 1",
                str(signs[index]),
                f"{path}.signs must contain contract signs",
            )
    return {"permutation": permutation, "signs": signs}


def _boundary_extents(dimensions: list[int], axis: int) -> list[int]:
    return [value for index, value in enumerate(dimensions) if index != axis]


def _dimensions(value: object, rank: int) -> list[int]:
    dimensions = _integer_array(value, "profile.dimensions")
    if len(dimensions) != rank:
        _fail(
            "invalid_dimension_count",
            "profile.dimensions",
            "one dimension per rank axis",
            str(len(dimensions)),
            "profile.dimensions length must equal rank",
        )
    volume = 1
    for index, dimension in enumerate(dimensions):
        path = f"profile.dimensions[{index}]"
        if dimension < MINIMUM_AXIS_LENGTH or dimension > MAXIMUM_AXIS_LENGTH:
            _fail(
                "out_of_range",
                path,
                "contract axis-length range",
                str(dimension),
                f"{path} is outside the contract axis-length range",
            )
        if volume > MAXIMUM_INDEXABLE_VOLUME // dimension:
            _fail(
                "volume_overflow",
                "profile.dimensions",
                "product at most maximum indexable volume",
                "product exceeds maximum",
                "profile.dimensions product exceeds the contract maximum",
            )
        volume *= dimension
    return dimensions


def _seam(
    value: object,
    index: int,
    rank: int,
    dimensions: list[int],
    ids: set[str],
    active_boundaries: set[tuple[int, str]],
) -> dict[str, object]:
    path = f"profile.seams[{index}]"
    row = _object(value, path)
    _exact_fields(
        row,
        frozenset(("id", "source", "target", "transform", "enabled")),
        path,
    )
    seam_id = _string(row["id"], f"{path}.id").strip()
    if not seam_id or seam_id in ids:
        _fail(
            "unknown_required_value",
            f"{path}.id",
            "unique non-empty string",
            "empty" if not seam_id else seam_id,
            f"{path}.id must be unique and non-empty",
        )
    ids.add(seam_id)
    source = _boundary(row["source"], f"{path}.source", rank)
    target = _boundary(row["target"], f"{path}.target", rank)
    transform = _transform(row["transform"], f"{path}.transform", rank)
    enabled = _boolean(row["enabled"], f"{path}.enabled")
    source_key = (int(source["axis"]), str(source["side"]))
    target_key = (int(target["axis"]), str(target["side"]))
    if source_key == target_key:
        _fail(
            "invalid_side",
            f"{path}.target",
            "boundary distinct from source",
            f"{target_key[0]}{target_key[1]}",
            f"{path} cannot identify a boundary with itself",
        )
    source_extents = _boundary_extents(dimensions, source_key[0])
    target_extents = _boundary_extents(dimensions, target_key[0])
    permutation = transform["permutation"]
    for source_index, target_index in enumerate(permutation):
        if source_extents[source_index] != target_extents[target_index]:
            _fail(
                "invalid_permutation",
                f"{path}.transform.permutation[{source_index}]",
                "extent-compatible tangent mapping",
                str(target_index),
                f"{path}.transform does not preserve boundary extents",
            )
    if enabled and (source_key in active_boundaries or target_key in active_boundaries):
        _fail(
            "unknown_required_value",
            path,
            "unused active boundaries",
            "duplicate active boundary",
            f"{path} reuses an active boundary",
        )
    if enabled:
        active_boundaries.update((source_key, target_key))
    return {
        "id": seam_id,
        "source": source,
        "target": target,
        "transform": transform,
        "enabled": enabled,
    }


def _seams(value: object, rank: int, dimensions: list[int]) -> list[dict[str, object]]:
    ids: set[str] = set()
    active_boundaries: set[tuple[int, str]] = set()
    return [
        _seam(item, index, rank, dimensions, ids, active_boundaries)
        for index, item in enumerate(_array(value, "profile.seams"))
    ]


def validate_topology_transport_profile(payload: object) -> dict[str, object]:
    profile = _object(payload, "profile")
    _exact_fields(
        profile,
        frozenset(("contract_version", "rank", "dimensions", "seams")),
        "profile",
    )
    version = _integer(profile["contract_version"], "profile.contract_version")
    if version != CONTRACT_VERSION:
        _fail(
            "contract_version_mismatch",
            "profile.contract_version",
            str(CONTRACT_VERSION),
            str(version),
            "profile.contract_version is unsupported",
        )
    rank = _integer(profile["rank"], "profile.rank")
    if rank < MINIMUM_RANK or rank > MAXIMUM_RANK:
        _fail(
            "invalid_rank",
            "profile.rank",
            "contract rank range",
            str(rank),
            "profile.rank is outside the contract range",
        )
    dimensions = _dimensions(profile["dimensions"], rank)
    seams = _seams(profile["seams"], rank, dimensions)
    return {
        "contract_version": version,
        "rank": rank,
        "dimensions": dimensions,
        "seams": seams,
    }


def validate_topology_transport_query(
    payload: object, profile: Mapping[str, object]
) -> dict[str, object]:
    query = _object(payload, "query")
    _exact_fields(
        query,
        frozenset(("dimensions", "coordinate", "axis", "delta")),
        "query",
    )
    rank = int(profile["rank"])
    profile_dimensions = list(profile["dimensions"])
    dimensions = _integer_array(query["dimensions"], "query.dimensions")
    coordinate = _integer_array(query["coordinate"], "query.coordinate")
    if len(dimensions) != rank:
        _fail(
            "invalid_dimension_count",
            "query.dimensions",
            "one dimension per profile rank axis",
            str(len(dimensions)),
            "query.dimensions length must equal profile rank",
        )
    if dimensions != profile_dimensions:
        _fail(
            "unknown_required_value",
            "query.dimensions",
            "dimensions equal to validated profile",
            "different dimensions",
            "query.dimensions must equal profile.dimensions",
        )
    if len(coordinate) != rank:
        _fail(
            "coordinate_rank_mismatch",
            "query.coordinate",
            "one coordinate per profile rank axis",
            str(len(coordinate)),
            "query.coordinate length must equal profile rank",
        )
    for index, item in enumerate(coordinate):
        if item < 0 or item >= dimensions[index]:
            path = f"query.coordinate[{index}]"
            _fail(
                "coordinate_out_of_bounds",
                path,
                "coordinate inside board dimensions",
                str(item),
                f"{path} is outside the board",
            )
    axis = _integer(query["axis"], "query.axis")
    if axis < 0 or axis >= rank:
        _fail(
            "invalid_axis",
            "query.axis",
            "axis index within profile rank",
            str(axis),
            "query.axis is outside the profile rank",
        )
    delta = _integer(query["delta"], "query.delta")
    if delta not in VALID_MOVEMENT_DELTAS:
        _fail(
            "invalid_delta",
            "query.delta",
            "-1 or 1",
            str(delta),
            "query.delta must be a contract unit movement delta",
        )
    return {
        "dimensions": dimensions,
        "coordinate": coordinate,
        "axis": axis,
        "delta": delta,
    }


__all__ = [
    "TopologyTransportError",
    "validate_topology_transport_profile",
    "validate_topology_transport_query",
]
