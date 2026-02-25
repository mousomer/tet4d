from __future__ import annotations

import json
from pathlib import Path
from typing import Any


GRID_MODE_NAMES = ("off", "edge", "full", "helper")
BOT_MODE_NAMES = ("off", "assist", "auto", "step")
BOT_PROFILE_NAMES = ("fast", "balanced", "deep", "ultra")


def require_state_relative_path(value: object, *, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{path} must be a non-empty string")
    normalized = value.strip().replace("\\", "/")
    candidate = Path(normalized)
    if candidate.is_absolute():
        raise RuntimeError(f"{path} must be a relative path under state/")
    parts = [part for part in candidate.parts if part not in ("", ".")]
    if not parts:
        raise RuntimeError(f"{path} must be a relative path under state/")
    if any(part == ".." for part in parts):
        raise RuntimeError(f"{path} must not contain '..'")
    if any(":" in part for part in parts):
        raise RuntimeError(f"{path} must not contain ':' path segments")
    clean = "/".join(parts)
    if not clean.startswith("state/"):
        raise RuntimeError(f"{path} must be under state/")
    return clean


def read_json_payload(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - runtime failure path
        raise RuntimeError(f"Failed reading config file {path}: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in config file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Config file {path} must contain a JSON object")
    return payload


def require_int(
    value: object,
    *,
    path: str,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError(f"{path} must be an integer")
    if min_value is not None and value < min_value:
        raise RuntimeError(f"{path} must be >= {min_value}")
    if max_value is not None and value > max_value:
        raise RuntimeError(f"{path} must be <= {max_value}")
    return value


def require_number(
    value: object,
    *,
    path: str,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{path} must be a number")
    num = float(value)
    if min_value is not None and num < min_value:
        raise RuntimeError(f"{path} must be >= {min_value}")
    if max_value is not None and num > max_value:
        raise RuntimeError(f"{path} must be <= {max_value}")
    return num


def require_object(value: object, *, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must be an object")
    return value
