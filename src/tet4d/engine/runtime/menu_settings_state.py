from __future__ import annotations

from typing import Any

from .menu_config import default_settings_payload
from .project_config import menu_settings_file_path, state_dir_path
from .settings_schema import (
    RuntimeSettingDefaults,
    clamp_animation_duration_ms,
    clamp_game_seed,
    clamp_lines_per_level,
    clamp_overlay_transparency,
    clamp_toggle_index,
    derive_runtime_setting_defaults,
    mode_key_for_dimension,
)
from .menu_settings.sections import (
    ANIMATION_DURATION_MS_MAX,
    ANIMATION_DURATION_MS_MIN,
    ANIMATION_DURATION_MS_STEP,
    GAME_SEED_MAX,
    GAME_SEED_MIN,
    GAME_SEED_STEP,
    OVERLAY_TRANSPARENCY_MAX,
    OVERLAY_TRANSPARENCY_MIN,
    OVERLAY_TRANSPARENCY_STEP,
    analytics_settings_for_payload,
    audio_settings_for_payload,
    coerce_shared_gameplay_settings,
    display_settings_for_payload,
    global_game_seed_from_payload,
    mode_shared_gameplay_settings_from_payload,
    normalize_mode_key,
)
from .menu_settings.store import (
    apply_mode_settings_to_state,
    default_settings_payload_for_runtime,
    iter_all_mode_settings,
    load_payload,
    mode_settings_view,
    normalize_active_profile_name,
    sanitize_and_save_payload,
    save_payload,
    save_payload_section,
)

STATE_DIR = state_dir_path()
STATE_FILE = menu_settings_file_path()

_BASE_DEFAULTS = default_settings_payload()
_RUNTIME_DEFAULTS: RuntimeSettingDefaults = derive_runtime_setting_defaults(
    _BASE_DEFAULTS
)
DEFAULT_WINDOWED_SIZE = _RUNTIME_DEFAULTS.windowed_size
DEFAULT_OVERLAY_TRANSPARENCY = _RUNTIME_DEFAULTS.overlay_transparency
DEFAULT_GAME_SEED = _RUNTIME_DEFAULTS.game_seed


def _default_settings_payload() -> dict[str, Any]:
    return default_settings_payload_for_runtime(_BASE_DEFAULTS, defaults=_RUNTIME_DEFAULTS)


def _load_payload() -> dict[str, Any]:
    return load_payload(
        STATE_FILE,
        base_default_payload=_BASE_DEFAULTS,
        defaults=_RUNTIME_DEFAULTS,
    )


def _save_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    return save_payload(STATE_FILE, payload)


def _sanitize_and_save_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    return sanitize_and_save_payload(
        STATE_FILE,
        payload,
        base_default_payload=_BASE_DEFAULTS,
        defaults=_RUNTIME_DEFAULTS,
    )


def _save_payload_section(
    section_name: str,
    updates: dict[str, Any],
) -> tuple[bool, str]:
    return save_payload_section(
        STATE_FILE,
        section_name,
        updates,
        base_default_payload=_BASE_DEFAULTS,
        defaults=_RUNTIME_DEFAULTS,
    )


def apply_saved_menu_settings(
    state: Any,
    dimension: int,
    include_profile: bool = True,
) -> tuple[bool, str]:
    payload = _load_payload()
    default_profile = normalize_active_profile_name(
        _default_settings_payload().get("active_profile"),
        default="small",
    )
    mode_key = mode_key_for_dimension(dimension)
    mode_settings = payload.get("settings", {}).get(mode_key, {})
    if isinstance(mode_settings, dict):
        apply_mode_settings_to_state(state, mode_settings)
    if include_profile:
        state.active_profile = normalize_active_profile_name(
            payload.get("active_profile"),
            default=default_profile,
        )
    return True, "Loaded saved menu settings"


def save_menu_settings(state: Any, dimension: int) -> tuple[bool, str]:
    payload = _load_payload()
    mode_key = mode_key_for_dimension(dimension)
    payload["last_mode"] = mode_key
    payload["active_profile"] = normalize_active_profile_name(
        getattr(state, "active_profile", payload.get("active_profile")),
        default=normalize_active_profile_name(
            _default_settings_payload().get("active_profile"),
            default="small",
        ),
    )
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

    state.active_profile = normalize_active_profile_name(
        defaults.get("active_profile"),
        default="small",
    )
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
    return display_settings_for_payload(
        _load_payload(),
        default_payload=_default_settings_payload(),
        defaults=_RUNTIME_DEFAULTS,
    )


def default_display_settings() -> dict[str, Any]:
    return display_settings_for_payload(
        _default_settings_payload(),
        default_payload=_default_settings_payload(),
        defaults=_RUNTIME_DEFAULTS,
    )


def get_overlay_transparency() -> float:
    return float(get_display_settings()["overlay_transparency"])


def get_analytics_settings() -> dict[str, Any]:
    return analytics_settings_for_payload(
        _load_payload(),
        default_payload=_default_settings_payload(),
    )


def default_analytics_settings() -> dict[str, Any]:
    return analytics_settings_for_payload(
        _default_settings_payload(),
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
    return audio_settings_for_payload(
        _load_payload(),
        default_payload=_default_settings_payload(),
    )


def default_audio_settings() -> dict[str, Any]:
    return audio_settings_for_payload(
        _default_settings_payload(),
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
            "master_volume": None if master_volume is None else float(master_volume),
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
    return global_game_seed_from_payload(_load_payload(), default=DEFAULT_GAME_SEED)


def default_mode_shared_gameplay_settings(mode_key: str) -> dict[str, Any]:
    normalized_mode = normalize_mode_key(mode_key)
    defaults = _default_settings_payload()
    mode_settings = mode_settings_view(defaults.get("settings"), normalized_mode)
    return coerce_shared_gameplay_settings(mode_settings)


def mode_shared_gameplay_settings(mode_key: str) -> dict[str, Any]:
    normalized_mode = normalize_mode_key(mode_key)
    payload = _load_payload()
    defaults = default_mode_shared_gameplay_settings(normalized_mode)
    return mode_shared_gameplay_settings_from_payload(
        payload,
        mode_key=normalized_mode,
        defaults=defaults,
    )


def mode_speedup_settings(mode_key: str) -> tuple[int, int]:
    settings = mode_shared_gameplay_settings(mode_key)
    return (
        int(settings["auto_speedup_enabled"]),
        int(settings["lines_per_level"]),
    )


def mode_rotation_animation_mode(mode_key: str) -> str:
    settings = mode_shared_gameplay_settings(mode_key)
    return str(settings["rotation_animation_mode"])


def mode_animation_settings(mode_key: str) -> tuple[int, int]:
    settings = mode_shared_gameplay_settings(mode_key)
    rotation_key = (
        "rotation_animation_duration_ms_2d"
        if normalize_mode_key(mode_key) == "2d"
        else "rotation_animation_duration_ms_nd"
    )
    return (
        int(settings[rotation_key]),
        int(settings["translation_animation_duration_ms"]),
    )


def save_shared_gameplay_settings(
    random_mode_index: int,
    topology_advanced: int,
    kick_level_index: int,
    auto_speedup_enabled: int,
    lines_per_level: int,
    rotation_animation_mode: str,
    rotation_animation_duration_ms_2d: int,
    rotation_animation_duration_ms_nd: int,
    translation_animation_duration_ms: int,
) -> tuple[bool, str]:
    payload = _load_payload()
    raw_values = {
        "random_mode_index": int(random_mode_index),
        "topology_advanced": int(topology_advanced),
        "kick_level_index": int(kick_level_index),
        "auto_speedup_enabled": int(auto_speedup_enabled),
        "lines_per_level": int(lines_per_level),
        "rotation_animation_mode": str(rotation_animation_mode),
        "rotation_animation_duration_ms_2d": int(rotation_animation_duration_ms_2d),
        "rotation_animation_duration_ms_nd": int(rotation_animation_duration_ms_nd),
        "translation_animation_duration_ms": int(translation_animation_duration_ms),
    }
    for mode_key, mode_settings in iter_all_mode_settings(payload):
        defaults = default_mode_shared_gameplay_settings(mode_key)
        mode_settings.update(
            coerce_shared_gameplay_settings(raw_values, defaults=defaults)
        )
    return _sanitize_and_save_payload(payload)


def save_global_game_seed(seed: int) -> tuple[bool, str]:
    payload = _load_payload()
    clamped_seed = clamp_game_seed(seed, default=DEFAULT_GAME_SEED)
    for _mode_key, mode_settings in iter_all_mode_settings(payload):
        mode_settings["game_seed"] = clamped_seed
    return _sanitize_and_save_payload(payload)


__all__ = [
    "ANIMATION_DURATION_MS_MAX",
    "ANIMATION_DURATION_MS_MIN",
    "ANIMATION_DURATION_MS_STEP",
    "DEFAULT_GAME_SEED",
    "DEFAULT_OVERLAY_TRANSPARENCY",
    "DEFAULT_WINDOWED_SIZE",
    "GAME_SEED_MAX",
    "GAME_SEED_MIN",
    "GAME_SEED_STEP",
    "OVERLAY_TRANSPARENCY_MAX",
    "OVERLAY_TRANSPARENCY_MIN",
    "OVERLAY_TRANSPARENCY_STEP",
    "STATE_DIR",
    "STATE_FILE",
    "apply_saved_menu_settings",
    "clamp_animation_duration_ms",
    "clamp_game_seed",
    "clamp_lines_per_level",
    "clamp_overlay_transparency",
    "clamp_toggle_index",
    "default_analytics_settings",
    "default_audio_settings",
    "default_display_settings",
    "default_mode_shared_gameplay_settings",
    "get_analytics_settings",
    "get_audio_settings",
    "get_display_settings",
    "get_global_game_seed",
    "get_overlay_transparency",
    "load_app_settings_payload",
    "load_menu_settings",
    "mode_animation_settings",
    "mode_shared_gameplay_settings",
    "mode_speedup_settings",
    "reset_menu_settings_to_defaults",
    "save_analytics_settings",
    "save_app_settings_payload",
    "save_audio_settings",
    "save_display_settings",
    "save_global_game_seed",
    "save_menu_settings",
    "save_shared_gameplay_settings",
]
