from __future__ import annotations

from collections.abc import Sequence

from tet4d.generated.topology_contract_v1 import MAXIMUM_INDEXABLE_VOLUME


def require_json_int(value: object, path: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{path} must be an integer")
    return value


def require_json_bool(value: object, path: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{path} must be a boolean")
    return value


def require_json_string(value: object, path: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{path} must be a string")
    return value


def require_bounded_json_int(
    value: object,
    path: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    normalized = require_json_int(value, path)
    if normalized < minimum or normalized > maximum:
        raise ValueError(f"{path} must be between {minimum} and {maximum}")
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
        valid_container = type(value) is list
    else:
        valid_container = isinstance(value, Sequence) and not isinstance(
            value, (str, bytes)
        )
    if not valid_container:
        raise ValueError(f"{path} must be an array")
    assert isinstance(value, Sequence)
    result = []
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        normalized = require_json_int(item, item_path)
        if minimum is not None and normalized < minimum:
            raise ValueError(f"{item_path} must be at least {minimum}")
        if maximum is not None and normalized > maximum:
            raise ValueError(f"{item_path} must be at most {maximum}")
        if allowed is not None and normalized not in allowed:
            choices = ", ".join(str(choice) for choice in allowed)
            raise ValueError(f"{item_path} must be one of {choices}")
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
        raise ValueError("maximum_indexable_volume must be positive")
    product = 1
    for index, raw_size in enumerate(dimensions):
        size = require_json_int(raw_size, f"{path}[{index}]")
        if size < 1:
            raise ValueError(f"{path}[{index}] must be positive")
        if size > maximum // product:
            raise ValueError(f"{path} product exceeds {maximum}")
        product *= size
    return product


__all__ = [
    "checked_dimension_product",
    "require_bounded_json_int",
    "require_json_bool",
    "require_json_int",
    "require_json_int_sequence",
    "require_json_string",
]
