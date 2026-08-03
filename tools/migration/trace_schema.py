from __future__ import annotations

import hashlib
import json
import math
import re
from numbers import Integral
from pathlib import Path
from typing import Any

TRACE_VERSION = 1
SCHEMA_VERSION = 1

_MEMORY_REPR_PATTERN = re.compile(r"<[^>]+ object at 0x[0-9a-fA-F]+>")
_TIMESTAMP_KEY_FRAGMENTS = ("timestamp", "datetime", "generated_at", "created_at")
_LOCAL_USER_PATH_MARKERS = ("/" + "Users" + "/", "\\" + "Users" + "\\")


def _validate_trace_value(value: Any, *, path: str = "$") -> None:
    if value is None or type(value) in {str, bool, int}:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{path} must contain a finite float")
        return
    if type(value) in {list, tuple}:
        for index, item in enumerate(value):
            _validate_trace_value(item, path=f"{path}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError(f"{path} mapping keys must be strings")
            _validate_trace_value(item, path=f"{path}.{key}")
        return
    raise TypeError(f"{path} contains unsupported trace value {type(value).__name__}")


def canonical_json(payload: Any) -> str:
    _validate_trace_value(payload)
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def compact_canonical_json(payload: Any) -> str:
    _validate_trace_value(payload)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def stable_hash(payload: Any) -> str:
    canonical = compact_canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def write_canonical_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload), encoding="utf-8")
    return path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def coord_payload(coord: Any) -> list[int] | None:
    if coord is None:
        return None
    values: list[int] = []
    for index, value in enumerate(coord):
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise TypeError(f"coord[{index}] must be an integer")
        values.append(int(value))
    return values


def coords_payload(coords: Any) -> list[list[int]]:
    validated = [coord_payload(coord) for coord in coords]
    if any(coord is None for coord in validated):
        raise TypeError("coords must not contain null coordinates")
    return [list(coord) for coord in sorted(validated) if coord is not None]


def command_payload(command_id: str, **fields: Any) -> dict[str, Any]:
    if type(command_id) is not str or not command_id:
        raise TypeError("command_id must be a non-empty string")
    payload = {"id": command_id}
    payload.update({key: to_jsonable(value) for key, value in fields.items()})
    return payload


def frame_payload(index: int, **fields: Any) -> dict[str, Any]:
    if isinstance(index, bool) or not isinstance(index, Integral):
        raise TypeError("frame index must be an integer")
    payload = {"frame_index": int(index)}
    payload.update({key: to_jsonable(value) for key, value in fields.items()})
    payload["state_hash"] = stable_hash(payload)
    return payload


def generator_metadata(name: str) -> dict[str, Any]:
    if type(name) is not str or not name:
        raise TypeError("generator name must be a non-empty string")
    return {
        "name": name,
        "schema_version": SCHEMA_VERSION,
    }


def trace_file_name(case_id: str) -> str:
    if type(case_id) is not str:
        raise TypeError("case_id must be a string")
    safe = case_id.strip()
    if not safe:
        raise ValueError("case_id must be non-empty")
    return f"{safe}.json"


def to_jsonable(value: Any) -> Any:
    if value is None or type(value) in {str, int, bool}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("trace floats must be finite")
        return round(value, 6)
    if type(value) is tuple:
        return [to_jsonable(item) for item in value]
    if type(value) is list:
        return [to_jsonable(item) for item in value]
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise TypeError("trace mapping keys must be strings")
        return {key: to_jsonable(value[key]) for key in sorted(value)}
    raise TypeError(f"unsupported trace value: {type(value).__name__}")


def assert_trace_hygiene(payload: Any) -> None:
    _validate_trace_value(payload)

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key).lower()
                if any(fragment in key_text for fragment in _TIMESTAMP_KEY_FRAGMENTS):
                    raise AssertionError(f"timestamp-like key in trace at {path}.{key}")
                visit(item, f"{path}.{key}")
            return
        if isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, f"{path}[{index}]")
            return
        if isinstance(value, str):
            if _MEMORY_REPR_PATTERN.search(value):
                raise AssertionError(f"memory repr in trace at {path}")
            if any(marker in value for marker in _LOCAL_USER_PATH_MARKERS):
                raise AssertionError(f"absolute local path in trace at {path}")

    visit(payload, "$")
