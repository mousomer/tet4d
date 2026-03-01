from __future__ import annotations

import re
import json
import logging
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

MODE_KEYS = ("2d", "3d", "4d")
MODE_KEY_SET = set(MODE_KEYS)
GRID_MODE_NAMES = ("off", "edge", "full", "helper")
BOT_MODE_NAMES = ("off", "assist", "auto", "step")
BOT_PROFILE_NAMES = ("fast", "balanced", "deep", "ultra")

OVERLAY_TRANSPARENCY_MIN = 0.0
OVERLAY_TRANSPARENCY_MAX = 0.85
OVERLAY_TRANSPARENCY_STEP = 0.05

GAME_SEED_MIN = 0
GAME_SEED_MAX = 999_999_999
GAME_SEED_STEP = 1

MIN_WINDOW_WIDTH = 640
MIN_WINDOW_HEIGHT = 480
FALLBACK_DEFAULT_WINDOWED_SIZE = (1200, 760)
FALLBACK_DEFAULT_OVERLAY_TRANSPARENCY = 0.25
FALLBACK_DEFAULT_GAME_SEED = 1337

PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuntimeSettingDefaults:
    windowed_size: tuple[int, int]
    overlay_transparency: float
    game_seed: int


def as_non_empty_string(value: object, *, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{path} must be a non-empty string")
    return value.strip()


def require_object(value: object, *, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must be an object")
    return value


def require_list(value: object, *, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise RuntimeError(f"{path} must be a list")
    return value


def require_bool(value: object, *, path: str) -> bool:
    if not isinstance(value, bool):
        raise RuntimeError(f"{path} must be a boolean")
    return value


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


def string_tuple(
    raw_values: object,
    *,
    path: str,
    normalize_lower: bool = False,
) -> tuple[str, ...]:
    values = require_list(raw_values, path=path)
    out: list[str] = []
    for idx, raw in enumerate(values):
        value = as_non_empty_string(raw, path=f"{path}[{idx}]")
        out.append(value.lower() if normalize_lower else value)
    if not out:
        raise RuntimeError(f"{path} must not be empty")
    return tuple(out)


def mode_key_for_dimension(dimension: int) -> str:
    if dimension not in (2, 3, 4):
        raise ValueError("dimension must be one of: 2, 3, 4")
    return f"{dimension}d"


def clamp_overlay_transparency(
    value: object,
    *,
    default: float = FALLBACK_DEFAULT_OVERLAY_TRANSPARENCY,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        numeric = float(default)
    else:
        numeric = float(value)
    return max(OVERLAY_TRANSPARENCY_MIN, min(OVERLAY_TRANSPARENCY_MAX, numeric))


def clamp_game_seed(
    value: object,
    *,
    default: int = FALLBACK_DEFAULT_GAME_SEED,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        numeric = int(default)
    else:
        numeric = int(value)
    return max(GAME_SEED_MIN, min(GAME_SEED_MAX, numeric))


def normalize_windowed_size(
    raw: object,
    *,
    fallback: tuple[int, int] = FALLBACK_DEFAULT_WINDOWED_SIZE,
    min_width: int = MIN_WINDOW_WIDTH,
    min_height: int = MIN_WINDOW_HEIGHT,
) -> tuple[int, int]:
    width: int
    height: int
    if (
        isinstance(raw, (list, tuple))
        and len(raw) == 2
        and all(isinstance(v, int) and not isinstance(v, bool) for v in raw)
    ):
        width, height = int(raw[0]), int(raw[1])
    else:
        width, height = fallback
    return (max(min_width, width), max(min_height, height))


def _extract_windowed_size(display: dict[str, Any]) -> tuple[int, int]:
    raw = display.get("windowed_size")
    return normalize_windowed_size(raw)


def derive_runtime_setting_defaults(
    defaults_payload: dict[str, Any],
) -> RuntimeSettingDefaults:
    display = defaults_payload.get("display")
    if not isinstance(display, dict):
        display = {}
    settings = defaults_payload.get("settings")
    seed_value: object = None
    if isinstance(settings, dict):
        mode_2d = settings.get("2d")
        if isinstance(mode_2d, dict):
            seed_value = mode_2d.get("game_seed")

    return RuntimeSettingDefaults(
        windowed_size=_extract_windowed_size(display),
        overlay_transparency=clamp_overlay_transparency(
            display.get("overlay_transparency"),
            default=FALLBACK_DEFAULT_OVERLAY_TRANSPARENCY,
        ),
        game_seed=clamp_game_seed(seed_value, default=FALLBACK_DEFAULT_GAME_SEED),
    )


def sync_runtime_bot_budget(
    settings: dict[str, dict[str, int]],
    *,
    runtime_budget_for_mode_fn: Callable[[str], int],
) -> None:
    for mode_key in MODE_KEYS:
        mode_settings = settings.get(mode_key)
        if isinstance(mode_settings, dict):
            mode_settings["bot_budget_ms"] = int(runtime_budget_for_mode_fn(mode_key))


def validate_defaults_payload(
    payload: dict[str, Any],
    *,
    runtime_budget_for_mode_fn: Callable[[str], int],
) -> dict[str, Any]:
    required = {
        "version",
        "active_profile",
        "last_mode",
        "display",
        "audio",
        "analytics",
        "settings",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise RuntimeError("defaults config missing keys: " + ", ".join(missing))

    version = require_int(payload["version"], path="defaults.version", min_value=1)
    active_profile = as_non_empty_string(
        payload["active_profile"], path="defaults.active_profile"
    )
    last_mode = as_non_empty_string(
        payload["last_mode"], path="defaults.last_mode"
    ).lower()
    if last_mode not in MODE_KEY_SET:
        raise RuntimeError("defaults.last_mode must be one of: 2d, 3d, 4d")

    display = require_object(payload["display"], path="defaults.display")
    fullscreen = require_bool(
        display.get("fullscreen"), path="defaults.display.fullscreen"
    )
    windowed_size = require_list(
        display.get("windowed_size"), path="defaults.display.windowed_size"
    )
    if len(windowed_size) != 2:
        raise RuntimeError("defaults.display.windowed_size must have length 2")
    width = require_int(
        windowed_size[0], path="defaults.display.windowed_size[0]", min_value=1
    )
    height = require_int(
        windowed_size[1], path="defaults.display.windowed_size[1]", min_value=1
    )
    overlay_transparency = require_number(
        display.get("overlay_transparency"),
        path="defaults.display.overlay_transparency",
    )
    if not (
        OVERLAY_TRANSPARENCY_MIN <= overlay_transparency <= OVERLAY_TRANSPARENCY_MAX
    ):
        raise RuntimeError(
            "defaults.display.overlay_transparency must be within [0.0, 0.85]"
        )

    audio = require_object(payload["audio"], path="defaults.audio")
    master_volume = require_number(
        audio.get("master_volume"), path="defaults.audio.master_volume"
    )
    sfx_volume = require_number(
        audio.get("sfx_volume"), path="defaults.audio.sfx_volume"
    )
    mute = require_bool(audio.get("mute"), path="defaults.audio.mute")

    analytics = require_object(payload["analytics"], path="defaults.analytics")
    score_logging_enabled = require_bool(
        analytics.get("score_logging_enabled"),
        path="defaults.analytics.score_logging_enabled",
    )

    settings_raw = require_object(payload["settings"], path="defaults.settings")
    settings: dict[str, dict[str, int]] = {}
    for mode_key in MODE_KEYS:
        mode_settings = require_object(
            settings_raw.get(mode_key), path=f"defaults.settings.{mode_key}"
        )
        cleaned: dict[str, int] = {}
        for attr, value in mode_settings.items():
            cleaned[str(attr)] = require_int(
                value,
                path=f"defaults.settings.{mode_key}.{attr}",
            )
        settings[mode_key] = cleaned

    sync_runtime_bot_budget(
        settings,
        runtime_budget_for_mode_fn=runtime_budget_for_mode_fn,
    )
    return {
        "version": version,
        "active_profile": active_profile,
        "last_mode": last_mode,
        "display": {
            "fullscreen": fullscreen,
            "windowed_size": [width, height],
            "overlay_transparency": overlay_transparency,
        },
        "audio": {
            "master_volume": master_volume,
            "sfx_volume": sfx_volume,
            "mute": mute,
        },
        "analytics": {
            "score_logging_enabled": score_logging_enabled,
        },
        "settings": settings,
    }


def read_json_value_or_raise(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_object_or_raise(path: Path) -> dict[str, Any]:
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


def _warn_config_issue(message: str) -> None:
    warnings.warn(message, RuntimeWarning)
    logger.warning(message)


def read_json_object_or_empty(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        _warn_config_issue(f"Failed reading config file {path}: {exc}")
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        _warn_config_issue(f"Invalid JSON in config file {path}: {exc}")
        return {}
    if not isinstance(payload, dict):
        _warn_config_issue(f"Config file {path} must contain a JSON object")
        return {}
    return payload


def write_json_object(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def atomic_write_json(
    path: Path,
    payload: object,
    *,
    trailing_newline: bool = True,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    if trailing_newline:
        encoded += "\n"
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(encoded, encoding="utf-8")
    temp_path.replace(path)


def atomic_write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(payload, encoding="utf-8")
    temp_path.replace(path)


def copy_text_file(src_path: Path, dst_path: Path) -> None:
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")


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
