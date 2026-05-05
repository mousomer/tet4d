from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


TRACE_VERSION = 1
SCHEMA_VERSION = 1

_MEMORY_REPR_PATTERN = re.compile(r"<[^>]+ object at 0x[0-9a-fA-F]+>")
_TIMESTAMP_KEY_FRAGMENTS = ("timestamp", "datetime", "generated_at", "created_at")
_LOCAL_USER_PATH_MARKERS = ("/" + "Users" + "/", "\\" + "Users" + "\\")


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def compact_canonical_json(payload: Any) -> str:
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
    return [int(value) for value in coord]


def coords_payload(coords: Any) -> list[list[int]]:
    return [
        coord_payload(coord)
        for coord in sorted(tuple(int(v) for v in c) for c in coords)
    ]


def command_payload(command_id: str, **fields: Any) -> dict[str, Any]:
    payload = {"id": str(command_id)}
    payload.update({key: to_jsonable(value) for key, value in fields.items()})
    return payload


def frame_payload(index: int, **fields: Any) -> dict[str, Any]:
    payload = {"frame_index": int(index)}
    payload.update({key: to_jsonable(value) for key, value in fields.items()})
    payload["state_hash"] = stable_hash(payload)
    return payload


def generator_metadata(name: str) -> dict[str, Any]:
    return {
        "name": str(name),
        "schema_version": SCHEMA_VERSION,
    }


def trace_file_name(case_id: str) -> str:
    safe = str(case_id).strip()
    if not safe:
        raise ValueError("case_id must be non-empty")
    return f"{safe}.json"


def to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, Path):
        return value.name
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): to_jsonable(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if hasattr(value, "__dict__"):
        return {
            str(key): to_jsonable(item)
            for key, item in sorted(vars(value).items())
            if not str(key).startswith("_")
        }
    return str(value)


def assert_trace_hygiene(payload: Any) -> None:
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
