from __future__ import annotations

from collections.abc import Sequence
from typing import NoReturn, cast

from tet4d.generated.topology_contract_v1 import MAXIMUM_INDEXABLE_VOLUME


class TopologyRepresentationError(ValueError):
    def __init__(self, path: str, message: str, value: object = None):
        super().__init__(message)
        self.path, self.value = path, value


def _reject(path: str, message: str, value: object = None) -> NoReturn:
    raise TopologyRepresentationError(path, message, value)


def _require_type(
    value: object,
    path: str,
    expected: type,
    label: str,
) -> object:
    if type(value) is not expected:
        _reject(
            path, f"{path} must be {label}", None if expected in {dict, list} else value
        )
    return value


def require_json_object(value: object, path: str) -> dict[str, object]:
    return cast(dict, _require_type(value, path, dict, "an object"))


def require_json_array(value: object, path: str) -> list[object]:
    return cast(list, _require_type(value, path, list, "an array"))


def require_json_int(value: object, path: str) -> int:
    return cast(int, _require_type(value, path, int, "an integer"))


def require_json_bool(value: object, path: str) -> bool:
    return cast(bool, _require_type(value, path, bool, "a boolean"))


def require_json_string(value: object, path: str) -> str:
    return cast(str, _require_type(value, path, str, "a string"))


def require_bounded_json_int(
    value: object, path: str, *, minimum: int, maximum: int
) -> int:
    normalized = require_json_int(value, path)
    if normalized < minimum or normalized > maximum:
        _reject(path, f"{path} must be between {minimum} and {maximum}", normalized)
    return normalized


def require_json_int_sequence(
    value: object,
    path: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
    allowed: tuple[int, ...] | None = None,
    require_list: bool = True,
) -> tuple[int, ...]:
    if require_list:
        sequence = require_json_array(value, path)
    else:
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            _reject(path, f"{path} must be an array", value)
        sequence = value
    result = []
    for index, item in enumerate(sequence):
        item_path = f"{path}[{index}]"
        normalized = require_json_int(item, item_path)
        if minimum is not None and normalized < minimum:
            _reject(item_path, f"{item_path} must be at least {minimum}", normalized)
        if maximum is not None and normalized > maximum:
            _reject(item_path, f"{item_path} must be at most {maximum}", normalized)
        if allowed is not None and normalized not in allowed:
            choices = ", ".join(str(choice) for choice in allowed)
            _reject(item_path, f"{item_path} must be one of {choices}", normalized)
        result.append(normalized)
    return tuple(result)


def checked_dimension_product(
    dimensions: Sequence[int],
    path: str = "board_dimensions",
    *,
    maximum: int = MAXIMUM_INDEXABLE_VOLUME,
) -> int:
    maximum = require_json_int(maximum, "maximum_indexable_volume")
    if maximum < 1:
        _reject(
            "maximum_indexable_volume",
            "maximum_indexable_volume must be positive",
            maximum,
        )
    product = 1
    for index, raw_size in enumerate(dimensions):
        size = require_json_int(raw_size, f"{path}[{index}]")
        if size < 1:
            _reject(f"{path}[{index}]", f"{path}[{index}] must be positive", size)
        if size > maximum // product:
            _reject(path, f"{path} product exceeds {maximum}", dimensions)
        product *= size
    return product


__all__ = [
    "TopologyRepresentationError",
    "checked_dimension_product",
    "require_bounded_json_int",
    "require_json_array",
    "require_json_bool",
    "require_json_int",
    "require_json_int_sequence",
    "require_json_object",
    "require_json_string",
]
