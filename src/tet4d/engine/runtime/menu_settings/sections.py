from __future__ import annotations

from typing import Any

from .. import settings_schema as _settings_schema
from ..runtime_config import kick_level_names
from ..settings_sanitize import (
    analytics_settings_from_payload,
    audio_settings_from_payload,
    display_settings_from_payload,
)
from ..settings_schema import (
    MODE_KEYS,
    clamp_animation_duration_ms,
    clamp_game_seed,
    clamp_lines_per_level,
    clamp_toggle_index,
)
from .store import mode_settings_view

_MODE_KEYS = set(MODE_KEYS)
_KICK_LEVEL_NAMES = kick_level_names()
_SHARED_GAMEPLAY_SPECS: tuple[tuple[str, Any, int], ...] = (
    ("random_mode_index", clamp_toggle_index, 0),
    ("topology_advanced", clamp_toggle_index, 0),
    ("kick_level_index", None, 0),
    ("auto_speedup_enabled", clamp_toggle_index, 1),
    ("lines_per_level", clamp_lines_per_level, 10),
    ("rotation_animation_duration_ms_2d", clamp_animation_duration_ms, 300),
    ("rotation_animation_duration_ms_nd", clamp_animation_duration_ms, 300),
    ("translation_animation_duration_ms", clamp_animation_duration_ms, 120),
)


OVERLAY_TRANSPARENCY_MIN = _settings_schema.OVERLAY_TRANSPARENCY_MIN
OVERLAY_TRANSPARENCY_MAX = _settings_schema.OVERLAY_TRANSPARENCY_MAX
OVERLAY_TRANSPARENCY_STEP = _settings_schema.OVERLAY_TRANSPARENCY_STEP
GAME_SEED_MIN = _settings_schema.GAME_SEED_MIN
GAME_SEED_MAX = _settings_schema.GAME_SEED_MAX
GAME_SEED_STEP = _settings_schema.GAME_SEED_STEP
ANIMATION_DURATION_MS_MIN = _settings_schema.ANIMATION_DURATION_MS_MIN
ANIMATION_DURATION_MS_MAX = _settings_schema.ANIMATION_DURATION_MS_MAX
ANIMATION_DURATION_MS_STEP = _settings_schema.ANIMATION_DURATION_MS_STEP


def clamp_kick_level_index(value: Any, *, default: int = 0) -> int:
    max_index = max(0, len(_KICK_LEVEL_NAMES) - 1)
    if isinstance(value, bool) or not isinstance(value, int):
        numeric = int(default)
    else:
        numeric = int(value)
    return max(0, min(max_index, numeric))


def normalize_mode_key(mode_key: str) -> str:
    normalized = str(mode_key).strip().lower()
    if normalized not in _MODE_KEYS:
        raise ValueError("mode_key must be one of: 2d, 3d, 4d")
    return normalized


def coerce_shared_gameplay_settings(
    raw: dict[str, Any],
    *,
    defaults: dict[str, int] | None = None,
) -> dict[str, int]:
    normalized: dict[str, int] = {}
    for setting_name, clamp_fn, fallback in _SHARED_GAMEPLAY_SPECS:
        default_value = defaults[setting_name] if defaults is not None else int(fallback)
        if setting_name == "kick_level_index":
            normalized[setting_name] = int(
                clamp_kick_level_index(raw.get(setting_name), default=default_value)
            )
            continue
        normalized[setting_name] = int(
            clamp_fn(
                raw.get(setting_name),
                default=default_value,
            )
        )
    return normalized


def display_settings_for_payload(
    payload: dict[str, Any],
    *,
    default_payload: dict[str, Any],
    defaults: Any,
) -> dict[str, Any]:
    return display_settings_from_payload(
        payload,
        default_payload=default_payload,
        defaults=defaults,
    )


def audio_settings_for_payload(
    payload: dict[str, Any],
    *,
    default_payload: dict[str, Any],
) -> dict[str, Any]:
    return audio_settings_from_payload(
        payload,
        default_payload=default_payload,
    )


def analytics_settings_for_payload(
    payload: dict[str, Any],
    *,
    default_payload: dict[str, Any],
) -> dict[str, Any]:
    return analytics_settings_from_payload(
        payload,
        default_payload=default_payload,
    )


def global_game_seed_from_payload(payload: dict[str, Any], *, default: int) -> int:
    raw_seed = mode_settings_view(payload.get("settings"), "2d").get("game_seed")
    return clamp_game_seed(raw_seed, default=default)


def mode_shared_gameplay_settings_from_payload(
    payload: dict[str, Any],
    *,
    mode_key: str,
    defaults: dict[str, int],
) -> dict[str, int]:
    mode_settings = mode_settings_view(payload.get("settings"), mode_key)
    return coerce_shared_gameplay_settings(mode_settings, defaults=defaults)
