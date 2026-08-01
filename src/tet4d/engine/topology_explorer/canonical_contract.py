from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .glue_model import (
    AXIS_NAMES,
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
)
from .glue_validate import validate_explorer_topology_profile

TOPOLOGY_CONTRACT_SCHEMA = "tet4d.topology_contract"
TOPOLOGY_CONTRACT_VERSION = 1


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )


def _boundary_key(boundary: BoundaryRef) -> tuple[int, int]:
    return boundary.axis, 0 if boundary.side == "-" else 1


def _boundary_payload(boundary: BoundaryRef) -> dict[str, object]:
    return {"axis": AXIS_NAMES[boundary.axis], "side": boundary.side}


def _canonical_glue(
    glue: GluingDescriptor,
) -> tuple[BoundaryRef, BoundaryRef, BoundaryTransform]:
    if _boundary_key(glue.source) <= _boundary_key(glue.target):
        return glue.source, glue.target, glue.transform
    return glue.target, glue.source, glue.transform.inverse()


def canonical_topology_payload(
    profile: ExplorerTopologyProfile,
    dims: Sequence[int],
) -> dict[str, object]:
    """Return the strict v1 semantic contract for an existing Python profile.

    Disabled editor rows, input order, direction, and user-facing glue IDs do not
    change topology identity. Active seams receive deterministic contract IDs.
    """
    normalized_dims = tuple(int(size) for size in dims)
    validate_explorer_topology_profile(profile, dims=normalized_dims)
    rows = [_canonical_glue(glue) for glue in profile.active_gluings()]
    rows.sort(
        key=lambda row: (
            _boundary_key(row[0]),
            _boundary_key(row[1]),
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


def _require_sequence(value: object, path: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be an array")  # noqa: TRY004 - one strict contract error type.
    return value


def _axis_index(value: object, dimension: int, path: str) -> int:
    if not isinstance(value, str):
        raise ValueError(f"{path} must be an axis name")  # noqa: TRY004 - one strict contract error type.
    normalized = value.strip().lower()
    if normalized not in AXIS_NAMES[:dimension]:
        raise ValueError(f"{path} is outside the contract dimension")
    return AXIS_NAMES.index(normalized)


def _boundary_from_payload(value: object, dimension: int, path: str) -> BoundaryRef:
    row = _require_mapping(value, path)
    _require_keys(row, frozenset(("axis", "side")), path)
    return BoundaryRef(
        dimension=dimension,
        axis=_axis_index(row.get("axis"), dimension, f"{path}.axis"),
        side=str(row.get("side", "")),
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
    if payload.get("schema_version") != TOPOLOGY_CONTRACT_VERSION:
        raise ValueError("unsupported topology contract schema version")
    dimension = payload.get("dimension")
    if isinstance(dimension, bool) or not isinstance(dimension, int):
        raise ValueError("dimension must be an integer")  # noqa: TRY004 - one strict contract error type.
    dims_raw = _require_sequence(payload.get("board_dimensions"), "board_dimensions")
    if len(dims_raw) != dimension:
        raise ValueError("board_dimensions length must match dimension")
    if any(
        isinstance(size, bool) or not isinstance(size, int) or size <= 0
        for size in dims_raw
    ):
        raise ValueError("board_dimensions must contain positive integers")
    dims = tuple(int(size) for size in dims_raw)
    glues_raw = _require_sequence(payload.get("gluings"), "gluings")
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
        permutation = _require_sequence(
            transform_row.get("permutation"), f"{path}.transform.permutation"
        )
        signs = _require_sequence(transform_row.get("signs"), f"{path}.transform.signs")
        if any(
            isinstance(item, bool) or not isinstance(item, int) for item in permutation
        ):
            raise ValueError(f"{path}.transform.permutation must contain integers")
        if any(isinstance(item, bool) or not isinstance(item, int) for item in signs):
            raise ValueError(f"{path}.transform.signs must contain integers")
        glue_id = row.get("id")
        if not isinstance(glue_id, str):
            raise ValueError(f"{path}.id must be a string")  # noqa: TRY004 - one strict contract error type.
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
                    permutation=tuple(int(item) for item in permutation),
                    signs=tuple(int(item) for item in signs),
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
