from __future__ import annotations

import json
from typing import Any

from ..api import (
    keybindings_active_key_profile as active_key_profile,
    keybindings_load_active_profile_bindings as load_active_profile_bindings,
    keybindings_set_active_key_profile as set_active_key_profile,
)
from .menu_config import default_settings_payload
from .project_config import menu_settings_file_path, state_dir_path
from .settings_sanitize import (
    analytics_settings_from_payload,
    audio_settings_from_payload,
    display_settings_from_payload,
    ensure_default_settings_payload,
    merge_loaded_payload,
    sanitize_payload,
)
from .settings_schema import (
    MODE_KEYS,
    RuntimeSettingDefaults,
    atomic_write_json,
    clamp_lines_per_level,
    clamp_game_seed,
    clamp_overlay_transparency,
    clamp_toggle_index,
    derive_runtime_setting_defaults,
    mode_key_for_dimension,
    read_json_value_or_raise,
)
from .runtime_config import kick_level_names
from . import settings_schema as _settings_schema

STATE_DIR = state_dir_path()
STATE_FILE = menu_settings_file_path()

_BASE_DEFAULTS = default_settings_payload()
_RUNTIME_DEFAULTS: RuntimeSettingDefaults = derive_runtime_setting_defaults(
    _BASE_DEFAULTS
)
DEFAULT_WINDOWED_SIZE = _RUNTIME_DEFAULTS.windowed_size
DEFAULT_OVERLAY_TRANSPARENCY = _RUNTIME_DEFAULTS.overlay_transparency
DEFAULT_GAME_SEED = _RUNTIME_DEFAULTS.game_seed
OVERLAY_TRANSPARENCY_MIN = _settings_schema.OVERLAY_TRANSPARENCY_MIN
OVERLAY_TRANSPARENCY_MAX = _settings_schema.OVERLAY_TRANSPARENCY_MAX
OVERLAY_TRANSPARENCY_STEP = _settings_schema.OVERLAY_TRANSPARENCY_STEP
GAME_SEED_MIN = _settings_schema.GAME_SEED_MIN
GAME_SEED_MAX = _settings_schema.GAME_SEED_MAX
GAME_SEED_STEP = _settings_schema.GAME_SEED_STEP

_MODE_KEYS = set(MODE_KEYS)
_KICK_LEVEL_NAMES = kick_level_names()


def _clamp_kick_level_index(value: Any, *, default: int = 0) -> int:
    max_index = max(0, len(_KICK_LEVEL_NAMES) - 1)
    if isinstance(value, bool) or not isinstance(value, int):
        numeric = int(default)
    else:
        numeric = int(value)
    return max(0, min(max_index, numeric))


_SHARED_GAMEPLAY_SPECS: tuple[
    tuple[str, Any, int],
    ...,
] = (
    ("random_mode_index", clamp_toggle_index, 0),
    ("topology_advanced", clamp_toggle_index, 0),
    ("kick_level_index", _clamp_kick_level_index, 0),
    ("auto_speedup_enabled", clamp_toggle_index, 1),
    ("lines_per_level", clamp_lines_per_level, 10),
)


def _normalize_mode_key(mode_key: str) -> str:
    normalized = str(mode_key).strip().lower()
    if normalized not in _MODE_KEYS:
        raise ValueError("mode_key must be one of: 2d, 3d, 4d")
    return normalized


def _coerce_shared_gameplay_settings(
    raw: dict[str, Any],
    *,
    defaults: dict[str, int] | None = None,
) -> dict[str, int]:
    normalized: dict[str, int] = {}
    for setting_name, clamp_fn, fallback in _SHARED_GAMEPLAY_SPECS:
        default_value = (
            defaults[setting_name] if defaults is not None else int(fallback)
        )
        normalized[setting_name] = int(
            clamp_fn(
                raw.get(setting_name),
                default=default_value,
            )
        )
    return normalized


def _settings_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    settings = payload.get("settings")
    if isinstance(settings, dict):
        return settings
    settings = {}
    payload["settings"] = settings
    return settings


def _mode_settings_mapping(
    settings: dict[str, Any],
    mode_key: str,
) -> dict[str, Any]:
    mode_settings = settings.get(mode_key)
    if isinstance(mode_settings, dict):
        return mode_settings
    mode_settings = {}
    settings[mode_key] = mode_settings
    return mode_settings


def _iter_all_mode_settings(
    payload: dict[str, Any],
) -> tuple[tuple[str, dict[str, Any]], ...]:
    settings = _settings_mapping(payload)
    mode_settings: list[tuple[str, dict[str, Any]]] = []
    for mode_key in MODE_KEYS:
        mode_settings.append((mode_key, _mode_settings_mapping(settings, mode_key)))
    return tuple(mode_settings)


def _mode_settings_view(settings: Any, mode_key: str) -> dict[str, Any]:
    if not isinstance(settings, dict):
        return {}
    mode_settings = settings.get(mode_key)
    return mode_settings if isinstance(mode_settings, dict) else {}


def _default_settings_payload() -> dict[str, Any]:
    return ensure_default_settings_payload(
        default_settings_payload(),
        defaults=_RUNTIME_DEFAULTS,
    )


def _load_payload() -> dict[str, Any]:
    payload = _default_settings_payload()
    if not STATE_FILE.exists():
        return payload
    try:
        loaded = read_json_value_or_raise(STATE_FILE)
    except (OSError, json.JSONDecodeError):
        return payload
    if not isinstance(loaded, dict):
        return payload

    merge_loaded_payload(payload, loaded)
    sanitize_payload(
        payload,
        default_payload=_default_settings_payload(),
        defaults=_RUNTIME_DEFAULTS,
    )
    return payload


def _save_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    try:
        atomic_write_json(STATE_FILE, payload, trailing_newline=False)
    except OSError as exc:
        return False, f"Failed saving menu state: {exc}"
    return True, f"Saved menu state to {STATE_FILE}"


def _sanitize_and_save_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    sanitize_payload(
        payload,
        default_payload=_default_settings_payload(),
        defaults=_RUNTIME_DEFAULTS,
    )
    return _save_payload(payload)


def _save_payload_section(
    section_name: str,
    updates: dict[str, Any],
) -> tuple[bool, str]:
    payload = _load_payload()
    section = payload.setdefault(section_name, {})
    for key, value in updates.items():
        if value is not None:
            section[key] = value
    return _sanitize_and_save_payload(payload)


def _load_saved_profile(payload: dict[str, Any]) -> tuple[bool, str]:
    profile = payload.get("active_profile")
    if not isinstance(profile, str):
        return True, ""
    ok_profile, msg_profile = set_active_key_profile(profile)
    if not ok_profile:
        return False, msg_profile
    ok_bindings, msg_bindings = load_active_profile_bindings()
    if not ok_bindings:
        return False, msg_bindings
    return True, ""


def _apply_mode_settings_to_state(state: Any, mode_settings: dict[str, Any]) -> None:
    for attr_name, value in mode_settings.items():
        if not hasattr(state.settings, attr_name):
            continue
        current = getattr(state.settings, attr_name)
        if isinstance(current, int):
            if isinstance(value, bool) or not isinstance(value, int):
                continue
        elif not isinstance(value, type(current)):
            continue
        setattr(state.settings, attr_name, value)


def apply_saved_menu_settings(
    state: Any,
    dimension: int,
    include_profile: bool = True,
) -> tuple[bool, str]:
    payload = _load_payload()
    if include_profile:
        ok_profile, msg_profile = _load_saved_profile(payload)
        if not ok_profile:
            return False, msg_profile
    mode_key = mode_key_for_dimension(dimension)
    mode_settings = payload.get("settings", {}).get(mode_key, {})
    if isinstance(mode_settings, dict):
        _apply_mode_settings_to_state(state, mode_settings)
    state.active_profile = active_key_profile()
    return True, "Loaded saved menu settings"


def save_menu_settings(state: Any, dimension: int) -> tuple[bool, str]:
    payload = _load_payload()
    mode_key = mode_key_for_dimension(dimension)
    payload["last_mode"] = mode_key
    payload["active_profile"] = active_key_profile()
    mode_settings = payload.setdefault("settings", {}).setdefault(mode_key, {})
    for attr_name, value in vars(state.settings).items():
        mode_settings[attr_name] = value
    return _save_payload(payload)


def load_menu_settings(
    state: Any,
    dimension: int,
    include_profile: bool = True,
) -> tuple[bool, str]:
    return apply_saved_menu_settings(state, dimension, include_profile=include_profile)


def reset_menu_settings_to_defaults(state: Any, dimension: int) -> tuple[bool, str]:
    defaults = _default_settings_payload()
    mode_key = mode_key_for_dimension(dimension)
    mode_defaults = defaults["settings"][mode_key]
    for attr_name, value in mode_defaults.items():
        if hasattr(state.settings, attr_name):
            setattr(state.settings, attr_name, value)

    default_profile = defaults.get("active_profile")
    if isinstance(default_profile, str):
        ok_profile, msg_profile = set_active_key_profile(default_profile)
        if not ok_profile:
            return False, msg_profile
        ok_bindings, msg_bindings = load_active_profile_bindings()
        if not ok_bindings:
            return False, msg_bindings
    state.active_profile = active_key_profile()
    return True, f"Reset {mode_key} settings to defaults"


def load_app_settings_payload() -> dict[str, Any]:
    return _load_payload()


def save_app_settings_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    merged = _default_settings_payload()
    for key in ("version", "active_profile", "last_mode"):
        if key in payload:
            merged[key] = payload[key]

    for section in ("display", "audio", "analytics"):
        section_payload = payload.get(section)
        if isinstance(section_payload, dict):
            merged[section].update(section_payload)

    settings = payload.get("settings")
    if isinstance(settings, dict):
        for mode_key, mode_settings in settings.items():
            if mode_key in merged["settings"] and isinstance(mode_settings, dict):
                merged["settings"][mode_key].update(mode_settings)

    return _sanitize_and_save_payload(merged)


def get_display_settings() -> dict[str, Any]:
    return display_settings_from_payload(
        _load_payload(),
        default_payload=_default_settings_payload(),
        defaults=_RUNTIME_DEFAULTS,
    )


def get_analytics_settings() -> dict[str, Any]:
    return analytics_settings_from_payload(
        _load_payload(),
        default_payload=_default_settings_payload(),
    )


def save_display_settings(
    *,
    fullscreen: bool | None = None,
    windowed_size: tuple[int, int] | None = None,
    overlay_transparency: float | None = None,
) -> tuple[bool, str]:
    updates: dict[str, Any] = {}
    if fullscreen is not None:
        updates["fullscreen"] = bool(fullscreen)
    if windowed_size is not None:
        width = max(640, int(windowed_size[0]))
        height = max(480, int(windowed_size[1]))
        updates["windowed_size"] = [width, height]
    if overlay_transparency is not None:
        updates["overlay_transparency"] = clamp_overlay_transparency(
            overlay_transparency,
            default=DEFAULT_OVERLAY_TRANSPARENCY,
        )
    return _save_payload_section("display", updates)


def get_audio_settings() -> dict[str, Any]:
    return audio_settings_from_payload(
        _load_payload(),
        default_payload=_default_settings_payload(),
    )


def save_audio_settings(
    *,
    master_volume: float | None = None,
    sfx_volume: float | None = None,
    mute: bool | None = None,
) -> tuple[bool, str]:
    return _save_payload_section(
        "audio",
        {
            "master_volume": (
                None if master_volume is None else float(master_volume)
            ),
            "sfx_volume": None if sfx_volume is None else float(sfx_volume),
            "mute": None if mute is None else bool(mute),
        },
    )


def save_analytics_settings(
    *,
    score_logging_enabled: bool | None = None,
) -> tuple[bool, str]:
    return _save_payload_section(
        "analytics",
        {
            "score_logging_enabled": (
                None if score_logging_enabled is None else bool(score_logging_enabled)
            )
        },
    )


def get_global_game_seed() -> int:
    payload = _load_payload()
    raw_seed = _mode_settings_view(payload.get("settings"), "2d").get("game_seed")
    return clamp_game_seed(raw_seed, default=DEFAULT_GAME_SEED)


def default_mode_shared_gameplay_settings(mode_key: str) -> dict[str, int]:
    normalized_mode = _normalize_mode_key(mode_key)
    defaults = _default_settings_payload()
    mode_settings = _mode_settings_view(defaults.get("settings"), normalized_mode)
    return _coerce_shared_gameplay_settings(mode_settings)


def mode_shared_gameplay_settings(mode_key: str) -> dict[str, int]:
    normalized_mode = _normalize_mode_key(mode_key)
    payload = _load_payload()
    defaults = default_mode_shared_gameplay_settings(normalized_mode)
    mode_settings = _mode_settings_view(payload.get("settings"), normalized_mode)
    return _coerce_shared_gameplay_settings(mode_settings, defaults=defaults)


def mode_speedup_settings(mode_key: str) -> tuple[int, int]:
    settings = mode_shared_gameplay_settings(mode_key)
    return (
        int(settings["auto_speedup_enabled"]),
        int(settings["lines_per_level"]),
    )


def save_shared_gameplay_settings(
    *,
    random_mode_index: int,
    topology_advanced: int,
    kick_level_index: int,
    auto_speedup_enabled: int,
    lines_per_level: int,
) -> tuple[bool, str]:
    payload = _load_payload()
    raw_values = {
        "random_mode_index": int(random_mode_index),
        "topology_advanced": int(topology_advanced),
        "kick_level_index": int(kick_level_index),
        "auto_speedup_enabled": int(auto_speedup_enabled),
        "lines_per_level": int(lines_per_level),
    }
    for mode_key, mode_settings in _iter_all_mode_settings(payload):
        defaults = default_mode_shared_gameplay_settings(mode_key)
        mode_settings.update(
            _coerce_shared_gameplay_settings(raw_values, defaults=defaults)
        )
    return _sanitize_and_save_payload(payload)


def save_global_game_seed(seed: int) -> tuple[bool, str]:
    payload = _load_payload()
    clamped_seed = clamp_game_seed(seed, default=DEFAULT_GAME_SEED)
    for _mode_key, mode_settings in _iter_all_mode_settings(payload):
        mode_settings["game_seed"] = clamped_seed

    return _sanitize_and_save_payload(payload)
