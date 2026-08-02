from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from tet4d.generated.topology_contract_v1 import (
    CONTRACT_NAME,
    CONTRACT_VERSION,
    MAXIMUM_AXIS_LENGTH,
    MAXIMUM_RANK,
    MINIMUM_AXIS_LENGTH,
    MINIMUM_RANK,
    VALID_TRANSFORM_SIGNS,
)

from .contract_validation import (
    checked_dimension_product,
    require_bounded_json_int,
    require_json_array,
    require_json_int,
    require_json_int_sequence,
    require_json_string,
)
from .glue_model import (
    AXIS_NAMES,
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
    boundary_sort_key,
)
from .glue_validate import validate_explorer_topology_profile

TOPOLOGY_CONTRACT_SCHEMA = CONTRACT_NAME
TOPOLOGY_CONTRACT_VERSION = CONTRACT_VERSION


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )


def _boundary_payload(boundary: BoundaryRef) -> dict[str, object]:
    return {"axis": AXIS_NAMES[boundary.axis], "side": boundary.side}


def canonical_topology_payload(
    profile: ExplorerTopologyProfile,
    dims: Sequence[int],
) -> dict[str, object]:
    """Return the strict v1 semantic contract for an existing Python profile.

    Disabled editor rows, input order, direction, and user-facing glue IDs do not
    change topology identity. Active seams receive deterministic contract IDs.
    """
    if len(dims) != profile.dimension:
        raise ValueError("board_dimensions length must match dimension")
    normalized_dims = require_json_int_sequence(
        dims,
        "board_dimensions",
        minimum=MINIMUM_AXIS_LENGTH,
        maximum=MAXIMUM_AXIS_LENGTH,
        require_list=False,
    )
    checked_dimension_product(normalized_dims)
    validate_explorer_topology_profile(profile, dims=normalized_dims)
    rows = [glue.canonical_geometry() for glue in profile.active_gluings()]
    rows.sort(
        key=lambda row: (
            boundary_sort_key(row[0]),
            boundary_sort_key(row[1]),
            row[2].permutation,
            row[2].signs,
        )
    )
    gluings = []
    for index, (source, target, transform) in enumerate(rows):
        gluings.append(
            {
                "id": f"seam_{index:03d}",
                "source": _boundary_payload(source),
                "target": _boundary_payload(target),
                "transform": {
                    "permutation": list(transform.permutation),
                    "signs": list(transform.signs),
                },
            }
        )
    return {
        "schema": TOPOLOGY_CONTRACT_SCHEMA,
        "schema_version": TOPOLOGY_CONTRACT_VERSION,
        "dimension": profile.dimension,
        "board_dimensions": list(normalized_dims),
        "gluings": gluings,
    }


def topology_contract_identity(payload: Mapping[str, object]) -> str:
    canonical = canonicalize_topology_contract(payload)
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _require_mapping(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object")  # noqa: TRY004 - one strict contract error type.
    return value


def _require_keys(
    value: Mapping[str, object], expected: frozenset[str], path: str
) -> None:
    if frozenset(value) != expected:
        raise ValueError(f"{path} fields must be exactly {', '.join(sorted(expected))}")


def _axis_index(value: object, dimension: int, path: str) -> int:
    normalized = require_json_string(value, path).strip().lower()
    if normalized not in AXIS_NAMES[:dimension]:
        raise ValueError(f"{path} is outside the contract dimension")
    return AXIS_NAMES.index(normalized)


def _boundary_from_payload(value: object, dimension: int, path: str) -> BoundaryRef:
    row = _require_mapping(value, path)
    _require_keys(row, frozenset(("axis", "side")), path)
    return BoundaryRef(
        dimension=dimension,
        axis=_axis_index(row.get("axis"), dimension, f"{path}.axis"),
        side=require_json_string(row.get("side"), f"{path}.side"),
    )


def topology_contract_profile(
    payload: Mapping[str, object],
) -> tuple[ExplorerTopologyProfile, tuple[int, ...]]:
    _require_keys(
        payload,
        frozenset(
            ("schema", "schema_version", "dimension", "board_dimensions", "gluings")
        ),
        "contract",
    )
    if payload.get("schema") != TOPOLOGY_CONTRACT_SCHEMA:
        raise ValueError("unsupported topology contract schema")
    version = require_json_int(payload.get("schema_version"), "schema_version")
    if version != TOPOLOGY_CONTRACT_VERSION:
        raise ValueError("unsupported topology contract schema version")
    dimension = require_bounded_json_int(
        payload.get("dimension"),
        "dimension",
        minimum=MINIMUM_RANK,
        maximum=MAXIMUM_RANK,
    )
    dims_raw = require_json_array(payload.get("board_dimensions"), "board_dimensions")
    if len(dims_raw) != dimension:
        raise ValueError("board_dimensions length must match dimension")
    dims = require_json_int_sequence(
        dims_raw,
        "board_dimensions",
        minimum=MINIMUM_AXIS_LENGTH,
        maximum=MAXIMUM_AXIS_LENGTH,
    )
    checked_dimension_product(dims)
    glues_raw = require_json_array(payload.get("gluings"), "gluings")
    gluings: list[GluingDescriptor] = []
    for index, value in enumerate(glues_raw):
        path = f"gluings[{index}]"
        row = _require_mapping(value, path)
        _require_keys(row, frozenset(("id", "source", "target", "transform")), path)
        transform_row = _require_mapping(row.get("transform"), f"{path}.transform")
        _require_keys(
            transform_row,
            frozenset(("permutation", "signs")),
            f"{path}.transform",
        )
        permutation = require_json_array(
            transform_row.get("permutation"), f"{path}.transform.permutation"
        )
        signs = require_json_array(
            transform_row.get("signs"), f"{path}.transform.signs"
        )
        normalized_permutation = require_json_int_sequence(
            permutation,
            f"{path}.transform.permutation",
            minimum=0,
            maximum=dimension - 2,
        )
        normalized_signs = require_json_int_sequence(
            signs,
            f"{path}.transform.signs",
            allowed=VALID_TRANSFORM_SIGNS,
        )
        glue_id = require_json_string(row.get("id"), f"{path}.id")
        gluings.append(
            GluingDescriptor(
                glue_id=glue_id,
                source=_boundary_from_payload(
                    row.get("source"), dimension, f"{path}.source"
                ),
                target=_boundary_from_payload(
                    row.get("target"), dimension, f"{path}.target"
                ),
                transform=BoundaryTransform(
                    permutation=normalized_permutation,
                    signs=normalized_signs,
                ),
            )
        )
    profile = ExplorerTopologyProfile(dimension=dimension, gluings=tuple(gluings))
    validate_explorer_topology_profile(profile, dims=dims)
    return profile, dims


def canonicalize_topology_contract(payload: Mapping[str, object]) -> dict[str, object]:
    profile, dims = topology_contract_profile(payload)
    return canonical_topology_payload(profile, dims)


@dataclass(frozen=True)
class CanonicalTopologyContract:
    profile: ExplorerTopologyProfile
    dims: tuple[int, ...]

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> CanonicalTopologyContract:
        profile, dims = topology_contract_profile(payload)
        canonical = canonical_topology_payload(profile, dims)
        canonical_profile, canonical_dims = topology_contract_profile(canonical)
        return cls(canonical_profile, canonical_dims)

    @property
    def payload(self) -> dict[str, object]:
        return canonical_topology_payload(self.profile, self.dims)

    @property
    def identity(self) -> str:
        return hashlib.sha256(_canonical_json(self.payload).encode("utf-8")).hexdigest()


__all__ = [
    "TOPOLOGY_CONTRACT_SCHEMA",
    "TOPOLOGY_CONTRACT_VERSION",
    "CanonicalTopologyContract",
    "canonical_topology_payload",
    "canonicalize_topology_contract",
    "topology_contract_identity",
    "topology_contract_profile",
]
