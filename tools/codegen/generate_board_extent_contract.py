"""Generate language bindings for the professional live board-extent contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "contracts" / "board_extent_contract_v1.json"
PYTHON_OUTPUT_PATH = (
    ROOT / "src" / "tet4d" / "generated" / "board_extent_contract_v1.py"
)
CPP_OUTPUT_PATH = (
    ROOT
    / "native"
    / "tet4d_core"
    / "include"
    / "tet4d_core"
    / "generated"
    / "board_extent_contract_v1.hpp"
)
GODOT_OUTPUT_PATH = (
    ROOT
    / "godot"
    / "Tet4D.Godot"
    / "scripts"
    / "generated"
    / "board_extent_contract_v1.gd"
)
SCHEMA_OUTPUT_PATH = ROOT / "config" / "schema" / "board_extent_contract.schema.json"

ROOT_FIELDS = frozenset({"contract", "contract_version", "modes"})
MODE_FIELDS = frozenset(
    {
        "axis_maxima",
        "axis_minima",
        "axis_order",
        "canonical_default_shape",
        "id",
        "native_maximum_cells",
        "rank",
        "supported_topology_kind",
    }
)
MODE_IDS = ("live_2d", "live_3d", "live_4d")
SIGNED_64_MAX = 9_223_372_036_854_775_807


def _require_exact_fields(
    payload: Mapping[str, object], expected: frozenset[str], path: str
) -> None:
    if frozenset(payload) != expected:
        raise ValueError(f"{path} fields must be exactly {', '.join(sorted(expected))}")


def _require_mapping(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object")  # noqa: TRY004
    return value


def _require_int(value: object, path: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{path} must be an integer")
    if value < -SIGNED_64_MAX - 1 or value > SIGNED_64_MAX:
        raise ValueError(f"{path} must fit signed 64-bit representation")
    return value


def _require_string(value: object, path: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{path} must be a string")
    return value


def _require_int_list(value: object, path: str) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be an array")  # noqa: TRY004
    return tuple(
        _require_int(item, f"{path}[{index}]") for index, item in enumerate(value)
    )


def _require_string_list(value: object, path: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be an array")  # noqa: TRY004
    return tuple(
        _require_string(item, f"{path}[{index}]") for index, item in enumerate(value)
    )


def _checked_product(values: Sequence[int], path: str) -> int:
    result = 1
    for index, value in enumerate(values):
        if value < 1:
            raise ValueError(f"{path}[{index}] must be positive")
        if result > SIGNED_64_MAX // value:
            raise ValueError(f"{path} overflows signed 64-bit multiplication")
        result *= value
    return result


def _validate_mode_axis_rules(
    path: str,
    rank: int,
    axes: tuple[str, ...],
    minima: tuple[int, ...],
    maxima: tuple[int, ...],
    default: tuple[int, ...],
) -> None:
    if not all(len(values) == rank for values in (axes, minima, maxima, default)):
        raise ValueError(f"{path} axis arrays must each have rank entries")
    if axes != ("X", "Y", "Z", "W")[:rank]:
        raise ValueError(f"{path}.axis_order must use canonical axis order")
    for axis, (minimum, maximum, default_value) in enumerate(
        zip(minima, maxima, default, strict=True)
    ):
        if minimum < 1:
            raise ValueError(f"{path}.axis_minima[{axis}] must be positive")
        if minimum > maximum:
            raise ValueError(f"{path}.axis_minima[{axis}] must not exceed maximum")
        if not minimum <= default_value <= maximum:
            raise ValueError(
                f"{path}.canonical_default_shape[{axis}] is outside its range"
            )


def _normalize_mode(value: object, index: int) -> dict[str, object]:
    path = f"modes[{index}]"
    payload = _require_mapping(value, path)
    _require_exact_fields(payload, MODE_FIELDS, path)
    mode_id = _require_string(payload.get("id"), f"{path}.id")
    rank = _require_int(payload.get("rank"), f"{path}.rank")
    if rank < 2 or rank > 4:
        raise ValueError(f"{path}.rank must be in [2, 4]")
    axes = _require_string_list(payload.get("axis_order"), f"{path}.axis_order")
    minima = _require_int_list(payload.get("axis_minima"), f"{path}.axis_minima")
    maxima = _require_int_list(payload.get("axis_maxima"), f"{path}.axis_maxima")
    default = _require_int_list(
        payload.get("canonical_default_shape"), f"{path}.canonical_default_shape"
    )
    _validate_mode_axis_rules(path, rank, axes, minima, maxima, default)
    maximum_cells = _require_int(
        payload.get("native_maximum_cells"), f"{path}.native_maximum_cells"
    )
    if maximum_cells < 1:
        raise ValueError(f"{path}.native_maximum_cells must be positive")
    if _checked_product(maxima, f"{path}.axis_maxima") != maximum_cells:
        raise ValueError(
            f"{path}.native_maximum_cells must equal the axis-maximum product"
        )
    topology_kind = _require_string(
        payload.get("supported_topology_kind"), f"{path}.supported_topology_kind"
    )
    if topology_kind != "bounded":
        raise ValueError(f"{path}.supported_topology_kind must be bounded")
    return {
        "axis_maxima": list(maxima),
        "axis_minima": list(minima),
        "axis_order": list(axes),
        "canonical_default_shape": list(default),
        "id": mode_id,
        "native_maximum_cells": maximum_cells,
        "rank": rank,
        "supported_topology_kind": topology_kind,
    }


def validate_contract_source(value: object) -> dict[str, object]:
    payload = _require_mapping(value, "contract")
    _require_exact_fields(payload, ROOT_FIELDS, "contract")
    if payload.get("contract") != "tet4d.board_extent_contract":
        raise ValueError("contract must identify tet4d.board_extent_contract")
    version = _require_int(payload.get("contract_version"), "contract_version")
    if version != 1:
        raise ValueError("contract_version must be 1")
    raw_modes = payload.get("modes")
    if not isinstance(raw_modes, list):
        raise ValueError("modes must be an array")  # noqa: TRY004
    modes = [_normalize_mode(value, index) for index, value in enumerate(raw_modes)]
    if tuple(mode["id"] for mode in modes) != MODE_IDS:
        raise ValueError(
            "modes must be exactly live_2d, live_3d, live_4d in canonical order"
        )
    return {
        "contract": "tet4d.board_extent_contract",
        "contract_version": version,
        "modes": modes,
    }


def canonical_source_json(payload: Mapping[str, object]) -> str:
    return json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )


def contract_fingerprint(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_source_json(payload).encode("utf-8")).hexdigest()


def load_contract_source(path: Path = SOURCE_PATH) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to read board extent contract source: {exc}") from exc
    return validate_contract_source(raw)


def _python_modes(modes: list[object]) -> str:
    return "(\n" + "\n".join(f"    {mode!r}," for mode in modes) + "\n)"


def render_python(payload: Mapping[str, object]) -> str:
    modes = payload["modes"]
    assert isinstance(modes, list)
    return f'''# Generated by tools/codegen/generate_board_extent_contract.py. Do not edit.
from __future__ import annotations

from typing import Final

CONTRACT_NAME: Final = "{payload["contract"]}"
CONTRACT_VERSION: Final = {payload["contract_version"]}
CONTRACT_FINGERPRINT: Final = "{contract_fingerprint(payload)}"
MODE_SPECS: Final = {_python_modes(modes)}
'''


def _cpp_values(values: list[object]) -> str:
    return ", ".join(str(value) for value in values)


def _cpp_string_values(values: list[object]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _cpp_mode(mode: Mapping[str, object]) -> str:
    mode_id = str(mode["id"])
    rank = int(mode["rank"])
    axes = list(mode["axis_order"])
    minima = list(mode["axis_minima"])
    maxima = list(mode["axis_maxima"])
    default = list(mode["canonical_default_shape"])
    maximum_cells = int(mode["native_maximum_cells"])
    topology_kind = str(mode["supported_topology_kind"])
    padded_numbers = lambda values: values + [0] * (4 - len(values))
    padded_axes = lambda values: values + [""] * (4 - len(values))
    return (
        f'\t{{"{mode_id}", {rank}, {{{_cpp_string_values(padded_axes(axes))}}}, '
        f"{{{_cpp_values(padded_numbers(minima))}}}, "
        f"{{{_cpp_values(padded_numbers(maxima))}}}, "
        f'{{{_cpp_values(padded_numbers(default))}}}, {maximum_cells}, "{topology_kind}"}},'
    )


def render_cpp(payload: Mapping[str, object]) -> str:
    modes = payload["modes"]
    assert isinstance(modes, list)
    return f'''// Generated by tools/codegen/generate_board_extent_contract.py. Do not edit.
#pragma once

#include <array>
#include <cstdint>
#include <string_view>

namespace tet4d::core::generated {{

struct BoardExtentModeSpec {{
\tstd::string_view id;
\tstd::int64_t rank;
\tstd::array<std::string_view, 4> axis_order;
\tstd::array<std::int64_t, 4> axis_minima;
\tstd::array<std::int64_t, 4> axis_maxima;
\tstd::array<std::int64_t, 4> canonical_default_shape;
\tstd::int64_t native_maximum_cells;
\tstd::string_view supported_topology_kind;
}};

inline constexpr std::string_view BOARD_EXTENT_CONTRACT_NAME = "{payload["contract"]}";
inline constexpr std::int64_t BOARD_EXTENT_CONTRACT_VERSION = {payload["contract_version"]};
inline constexpr std::string_view BOARD_EXTENT_CONTRACT_FINGERPRINT = "{contract_fingerprint(payload)}";
inline constexpr std::array<BoardExtentModeSpec, {len(modes)}> BOARD_EXTENT_MODE_SPECS{{{{
{chr(10).join(_cpp_mode(mode) for mode in modes)}
}}}};

}} // namespace tet4d::core::generated
'''


def _godot_mode(mode: Mapping[str, object]) -> str:
    spec = {
        "rank": mode["rank"],
        "axis_order": mode["axis_order"],
        "axis_minima": mode["axis_minima"],
        "axis_maxima": mode["axis_maxima"],
        "canonical_default_shape": mode["canonical_default_shape"],
        "native_maximum_cells": mode["native_maximum_cells"],
        "supported_topology_kind": mode["supported_topology_kind"],
    }
    return f'\t"{mode["id"]}": {json.dumps(spec)},'


def render_godot(payload: Mapping[str, object]) -> str:
    modes = payload["modes"]
    assert isinstance(modes, list)
    return f'''# Generated by tools/codegen/generate_board_extent_contract.py. Do not edit.
extends RefCounted

class_name BoardExtentContractV1

const CONTRACT_NAME := "{payload["contract"]}"
const CONTRACT_VERSION := {payload["contract_version"]}
const CONTRACT_FINGERPRINT := "{contract_fingerprint(payload)}"
const MODE_SPECS := {{
{chr(10).join(_godot_mode(mode) for mode in modes)}
}}


static func mode_spec(mode: String) -> Dictionary:
\treturn (MODE_SPECS.get(mode, {{}}) as Dictionary).duplicate(true)


static func canonical_default_shape(mode: String) -> Array:
\treturn (mode_spec(mode).get("canonical_default_shape", []) as Array).duplicate()


static func axis_ranges(mode: String) -> Array:
\tvar spec := mode_spec(mode)
\tvar minima: Array = spec.get("axis_minima", [])
\tvar maxima: Array = spec.get("axis_maxima", [])
\tvar result: Array = []
\tfor index in range(minima.size()):
\t\tresult.append([int(minima[index]), int(maxima[index])])
\treturn result
'''


def render_schema(payload: Mapping[str, object]) -> str:
    modes = payload["modes"]
    assert isinstance(modes, list)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://tet4d.local/schema/board_extent_contract.schema.json",
        "title": "Tet4D professional live board extent contract v1",
        "type": "object",
        "additionalProperties": False,
        "required": ["contract", "contract_version", "modes"],
        "properties": {
            "contract": {"const": payload["contract"]},
            "contract_version": {"const": payload["contract_version"]},
            "modes": {
                "type": "array",
                "minItems": len(modes),
                "maxItems": len(modes),
                "items": {"$ref": "#/$defs/mode"},
            },
        },
        "$defs": {
            "mode": {
                "type": "object",
                "additionalProperties": False,
                "required": sorted(MODE_FIELDS),
                "properties": {
                    "id": {"enum": list(MODE_IDS)},
                    "rank": {"type": "integer", "minimum": 2, "maximum": 4},
                    "axis_order": {
                        "type": "array",
                        "items": {"enum": ["X", "Y", "Z", "W"]},
                    },
                    "axis_minima": {
                        "type": "array",
                        "items": {"type": "integer", "minimum": 1},
                    },
                    "axis_maxima": {
                        "type": "array",
                        "items": {"type": "integer", "minimum": 1},
                    },
                    "canonical_default_shape": {
                        "type": "array",
                        "items": {"type": "integer", "minimum": 1},
                    },
                    "native_maximum_cells": {"type": "integer", "minimum": 1},
                    "supported_topology_kind": {"const": "bounded"},
                },
            }
        },
    }
    return json.dumps(schema, ensure_ascii=False, indent=2) + "\n"


def expected_outputs(payload: Mapping[str, object]) -> dict[Path, str]:
    return {
        PYTHON_OUTPUT_PATH: render_python(payload),
        CPP_OUTPUT_PATH: render_cpp(payload),
        GODOT_OUTPUT_PATH: render_godot(payload),
        SCHEMA_OUTPUT_PATH: render_schema(payload),
    }


def check_outputs(outputs: Mapping[Path, str]) -> int:
    stale = [
        path.relative_to(ROOT)
        for path, expected in outputs.items()
        if not path.exists() or path.read_text(encoding="utf-8") != expected
    ]
    if stale:
        for path in stale:
            print(f"stale generated board extent contract binding: {path}")
        print("run: python tools/codegen/generate_board_extent_contract.py")
        return 1
    print("board extent contract generated bindings: OK")
    return 0


def write_outputs(outputs: Mapping[Path, str]) -> None:
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload = load_contract_source()
        outputs = expected_outputs(payload)
    except ValueError as exc:
        print(f"board extent contract generation failed: {exc}")
        return 1
    if args.check:
        return check_outputs(outputs)
    write_outputs(outputs)
    print(f"generated board extent contract bindings ({contract_fingerprint(payload)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
