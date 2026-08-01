#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "contracts" / "topology_contract_v1.json"
PYTHON_OUTPUT_PATH = ROOT / "src" / "tet4d" / "generated" / "topology_contract_v1.py"
CPP_OUTPUT_PATH = (
    ROOT
    / "native"
    / "tet4d_core"
    / "include"
    / "tet4d_core"
    / "generated"
    / "topology_contract_v1.hpp"
)
SCHEMA_OUTPUT_PATH = ROOT / "config" / "schema" / "topology_contract.schema.json"

_ROOT_FIELDS = frozenset(
    {
        "axis_length",
        "axis_names",
        "boundary_sides",
        "contract",
        "contract_version",
        "maximum_indexable_volume",
        "movement_deltas",
        "rank",
        "transform_signs",
    }
)
_RANGE_FIELDS = frozenset({"minimum", "maximum"})
_SIGNED_64_MAX = 9_223_372_036_854_775_807


def _require_exact_fields(
    payload: Mapping[str, object],
    expected: frozenset[str],
    path: str,
) -> None:
    if frozenset(payload) != expected:
        raise ValueError(f"{path} fields must be exactly {', '.join(sorted(expected))}")


def _require_mapping(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object")  # noqa: TRY004 - one generator validation error type.
    return value


def _require_json_int(value: object, path: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{path} must be an integer")
    if value < -_SIGNED_64_MAX - 1 or value > _SIGNED_64_MAX:
        raise ValueError(f"{path} must fit signed 64-bit representation")
    return value


def _require_string_list(value: object, path: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be an array")  # noqa: TRY004 - one generator validation error type.
    if any(type(item) is not str for item in value):
        raise ValueError(f"{path} must contain only strings")
    result = tuple(value)
    if len(set(result)) != len(result):
        raise ValueError(f"{path} must not contain duplicates")
    return result


def _require_int_list(value: object, path: str) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be an array")  # noqa: TRY004 - one generator validation error type.
    result = tuple(
        _require_json_int(item, f"{path}[{index}]") for index, item in enumerate(value)
    )
    if len(set(result)) != len(result):
        raise ValueError(f"{path} must not contain duplicates")
    return result


def _require_range(value: object, path: str) -> tuple[int, int]:
    payload = _require_mapping(value, path)
    _require_exact_fields(payload, _RANGE_FIELDS, path)
    minimum = _require_json_int(payload.get("minimum"), f"{path}.minimum")
    maximum = _require_json_int(payload.get("maximum"), f"{path}.maximum")
    if minimum > maximum:
        raise ValueError(f"{path}.minimum must not exceed {path}.maximum")
    return minimum, maximum


def validate_contract_source(value: object) -> dict[str, object]:
    payload = _require_mapping(value, "contract")
    _require_exact_fields(payload, _ROOT_FIELDS, "contract")
    if payload.get("contract") != "tet4d.topology_contract":
        raise ValueError("contract must identify tet4d.topology_contract")
    version = _require_json_int(payload.get("contract_version"), "contract_version")
    if version != 1:
        raise ValueError("contract_version must be 1")
    rank_minimum, rank_maximum = _require_range(payload.get("rank"), "rank")
    if (rank_minimum, rank_maximum) != (2, 4):
        raise ValueError("rank must define the supported range 2 through 4")
    axis_minimum, axis_maximum = _require_range(
        payload.get("axis_length"),
        "axis_length",
    )
    if axis_minimum < 1:
        raise ValueError("axis_length.minimum must be positive")
    maximum_volume = _require_json_int(
        payload.get("maximum_indexable_volume"),
        "maximum_indexable_volume",
    )
    if maximum_volume < 1:
        raise ValueError("maximum_indexable_volume must be positive")
    signs = _require_int_list(payload.get("transform_signs"), "transform_signs")
    if signs != (-1, 1):
        raise ValueError("transform_signs must be exactly -1 and 1")
    sides = _require_string_list(payload.get("boundary_sides"), "boundary_sides")
    if sides != ("-", "+"):
        raise ValueError("boundary_sides must be exactly '-' and '+'")
    deltas = _require_int_list(payload.get("movement_deltas"), "movement_deltas")
    if deltas != (-1, 1):
        raise ValueError("movement_deltas must be exactly -1 and 1")
    axes = _require_string_list(payload.get("axis_names"), "axis_names")
    if axes != ("x", "y", "z", "w") or len(axes) != rank_maximum:
        raise ValueError("axis_names must be exactly x, y, z, w")
    return {
        "axis_length": {"maximum": axis_maximum, "minimum": axis_minimum},
        "axis_names": list(axes),
        "boundary_sides": list(sides),
        "contract": "tet4d.topology_contract",
        "contract_version": version,
        "maximum_indexable_volume": maximum_volume,
        "movement_deltas": list(deltas),
        "rank": {"maximum": rank_maximum, "minimum": rank_minimum},
        "transform_signs": list(signs),
    }


def canonical_source_json(payload: Mapping[str, object]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def contract_fingerprint(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_source_json(payload).encode("utf-8")).hexdigest()


def load_contract_source(path: Path = SOURCE_PATH) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to read topology contract source: {exc}") from exc
    return validate_contract_source(raw)


def render_python(payload: Mapping[str, object]) -> str:
    fingerprint = contract_fingerprint(payload)
    rank = payload["rank"]
    axis_length = payload["axis_length"]
    assert isinstance(rank, Mapping)
    assert isinstance(axis_length, Mapping)
    return f"""# Generated by tools/codegen/generate_topology_contract.py. Do not edit.
from __future__ import annotations

from typing import Final

CONTRACT_NAME: Final = "{payload["contract"]}"
CONTRACT_VERSION: Final = {payload["contract_version"]}
MINIMUM_RANK: Final = {rank["minimum"]}
MAXIMUM_RANK: Final = {rank["maximum"]}
MINIMUM_AXIS_LENGTH: Final = {axis_length["minimum"]}
MAXIMUM_AXIS_LENGTH: Final = {axis_length["maximum"]}
MAXIMUM_INDEXABLE_VOLUME: Final = {payload["maximum_indexable_volume"]}
AXIS_NAMES: Final = ({_cpp_string_array(payload["axis_names"])})
VALID_TRANSFORM_SIGNS: Final = {tuple(payload["transform_signs"])!r}
VALID_BOUNDARY_SIDES: Final = ({_cpp_string_array(payload["boundary_sides"])})
VALID_MOVEMENT_DELTAS: Final = {tuple(payload["movement_deltas"])!r}
CONTRACT_FINGERPRINT: Final = (
    "{fingerprint}"
)
"""


def _cpp_int_array(values: object) -> str:
    assert isinstance(values, list)
    return ", ".join(str(value) for value in values)


def _cpp_string_array(values: object) -> str:
    assert isinstance(values, list)
    return ", ".join(f'"{value}"' for value in values)


def render_cpp(payload: Mapping[str, object]) -> str:
    fingerprint = contract_fingerprint(payload)
    rank = payload["rank"]
    axis_length = payload["axis_length"]
    axes = payload["axis_names"]
    signs = payload["transform_signs"]
    sides = payload["boundary_sides"]
    deltas = payload["movement_deltas"]
    assert isinstance(rank, Mapping)
    assert isinstance(axis_length, Mapping)
    assert isinstance(axes, list)
    assert isinstance(signs, list)
    assert isinstance(sides, list)
    assert isinstance(deltas, list)
    return f"""// Generated by tools/codegen/generate_topology_contract.py. Do not edit.
#pragma once

#include <array>
#include <cstdint>
#include <string_view>

namespace tet4d::core::generated {{

inline constexpr std::string_view CONTRACT_NAME = "{payload["contract"]}";
inline constexpr std::int64_t CONTRACT_VERSION = {payload["contract_version"]};
inline constexpr std::int64_t MINIMUM_RANK = {rank["minimum"]};
inline constexpr std::int64_t MAXIMUM_RANK = {rank["maximum"]};
inline constexpr std::int64_t MINIMUM_AXIS_LENGTH = {axis_length["minimum"]};
inline constexpr std::int64_t MAXIMUM_AXIS_LENGTH = {axis_length["maximum"]};
inline constexpr std::int64_t MAXIMUM_INDEXABLE_VOLUME = {payload["maximum_indexable_volume"]}LL;
inline constexpr std::array<std::string_view, {len(axes)}> AXIS_NAMES{{{{{_cpp_string_array(axes)}}}}};
inline constexpr std::array<std::int64_t, {len(signs)}> VALID_TRANSFORM_SIGNS{{{{{_cpp_int_array(signs)}}}}};
inline constexpr std::array<std::string_view, {len(sides)}> VALID_BOUNDARY_SIDES{{{{{_cpp_string_array(sides)}}}}};
inline constexpr std::array<std::int64_t, {len(deltas)}> VALID_MOVEMENT_DELTAS{{{{{_cpp_int_array(deltas)}}}}};
inline constexpr std::string_view CONTRACT_FINGERPRINT = "{fingerprint}";

}} // namespace tet4d::core::generated
"""


def render_contract_schema(payload: Mapping[str, object]) -> str:
    rank = payload["rank"]
    axis_length = payload["axis_length"]
    axes = payload["axis_names"]
    signs = payload["transform_signs"]
    sides = payload["boundary_sides"]
    assert isinstance(rank, Mapping)
    assert isinstance(axis_length, Mapping)
    assert isinstance(axes, list)
    assert isinstance(signs, list)
    assert isinstance(sides, list)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://tet4d.local/schema/topology_contract.schema.json",
        "title": "Tet4D canonical topology contract v1",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema",
            "schema_version",
            "dimension",
            "board_dimensions",
            "gluings",
        ],
        "properties": {
            "schema": {"const": payload["contract"]},
            "schema_version": {"const": payload["contract_version"]},
            "dimension": {
                "type": "integer",
                "minimum": rank["minimum"],
                "maximum": rank["maximum"],
            },
            "board_dimensions": {
                "type": "array",
                "minItems": rank["minimum"],
                "maxItems": rank["maximum"],
                "items": {
                    "type": "integer",
                    "minimum": axis_length["minimum"],
                    "maximum": axis_length["maximum"],
                },
            },
            "gluings": {
                "type": "array",
                "items": {"$ref": "#/$defs/gluing"},
            },
        },
        "$defs": {
            "boundary": {
                "type": "object",
                "additionalProperties": False,
                "required": ["axis", "side"],
                "properties": {
                    "axis": {"enum": axes},
                    "side": {"enum": sides},
                },
            },
            "transform": {
                "type": "object",
                "additionalProperties": False,
                "required": ["permutation", "signs"],
                "properties": {
                    "permutation": {
                        "type": "array",
                        "items": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": rank["maximum"] - 2,
                        },
                    },
                    "signs": {"type": "array", "items": {"enum": signs}},
                },
            },
            "gluing": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "source", "target", "transform"],
                "properties": {
                    "id": {"type": "string", "pattern": "^seam_[0-9]{3}$"},
                    "source": {"$ref": "#/$defs/boundary"},
                    "target": {"$ref": "#/$defs/boundary"},
                    "transform": {"$ref": "#/$defs/transform"},
                },
            },
        },
    }
    return json.dumps(schema, ensure_ascii=False, indent=2) + "\n"


def expected_outputs(payload: Mapping[str, object]) -> dict[Path, str]:
    return {
        PYTHON_OUTPUT_PATH: render_python(payload),
        CPP_OUTPUT_PATH: render_cpp(payload),
        SCHEMA_OUTPUT_PATH: render_contract_schema(payload),
    }


def check_outputs(outputs: Mapping[Path, str]) -> int:
    stale = []
    for path, expected in outputs.items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            stale.append(path.relative_to(ROOT))
    if stale:
        for path in stale:
            print(f"stale generated topology contract binding: {path}")
        print("run: python tools/codegen/generate_topology_contract.py")
        return 1
    print("topology contract generated bindings: OK")
    return 0


def write_outputs(outputs: Mapping[Path, str]) -> None:
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the source and fail if checked-in bindings are stale",
    )
    args = parser.parse_args()
    try:
        payload = load_contract_source()
        outputs = expected_outputs(payload)
    except ValueError as exc:
        print(f"topology contract generation failed: {exc}")
        return 1
    if args.check:
        return check_outputs(outputs)
    write_outputs(outputs)
    print(f"generated topology contract bindings ({contract_fingerprint(payload)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
