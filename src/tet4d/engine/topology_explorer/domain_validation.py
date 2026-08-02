from __future__ import annotations

from collections.abc import Sequence
from numbers import Integral
from typing import TypeVar

_T = TypeVar("_T")


def require_integral(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{path} must be an integer")  # noqa: TRY004 - topology domain validation has one stable rejection type.
    return int(value)


def require_non_negative_integral(value: object, path: str) -> int:
    normalized = require_integral(value, path)
    if normalized < 0:
        raise ValueError(f"{path} must be non-negative")
    return normalized


def require_bounded_integral(
    value: object,
    path: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    normalized = require_integral(value, path)
    if normalized < minimum or normalized > maximum:
        raise ValueError(f"{path} must be between {minimum} and {maximum}")
    return normalized


def require_exact_bool(value: object, path: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{path} must be a boolean")
    return value


def require_string(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path} must be a string")  # noqa: TRY004 - topology domain validation has one stable rejection type.
    return value


def require_sequence(value: object, path: str) -> Sequence[object]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise ValueError(f"{path} must be a non-string sequence")  # noqa: TRY004 - topology domain validation has one stable rejection type.
    return value


def require_instance(value: object, path: str, item_type: type[_T]) -> _T:
    if not isinstance(value, item_type):
        raise ValueError(f"{path} must be a {item_type.__name__}")  # noqa: TRY004 - topology domain validation has one stable rejection type.
    return value


def require_integral_sequence(value: object, path: str) -> tuple[int, ...]:
    sequence = require_sequence(value, path)
    normalized = [
        require_integral(item, f"{path}[{index}]")
        for index, item in enumerate(sequence)
    ]
    return tuple(normalized)


def require_instance_sequence(
    value: object,
    path: str,
    item_type: type[_T],
) -> tuple[_T, ...]:
    sequence = require_sequence(value, path)
    normalized: list[_T] = []
    for index, item in enumerate(sequence):
        if not isinstance(item, item_type):
            raise ValueError(f"{path}[{index}] must be a {item_type.__name__}")  # noqa: TRY004 - topology domain validation has one stable rejection type.
        normalized.append(item)
    return tuple(normalized)


__all__ = [
    "require_bounded_integral",
    "require_exact_bool",
    "require_instance",
    "require_instance_sequence",
    "require_integral",
    "require_integral_sequence",
    "require_non_negative_integral",
    "require_sequence",
    "require_string",
]
