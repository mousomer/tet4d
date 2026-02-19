from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .keybindings import (
    active_key_profile,
    load_active_profile_bindings,
    set_active_key_profile,
)
from .menu_config import default_settings_payload

STATE_DIR = Path(__file__).resolve().parent.parent / "state"
STATE_FILE = STATE_DIR / "menu_settings.json"
_BASE_DEFAULTS = default_settings_payload()
_DEFAULT_DISPLAY = _BASE_DEFAULTS.get("display", {})
_DEFAULT_WINDOWED_SIZE_RAW = (
    _DEFAULT_DISPLAY.get("windowed_size")
    if isinstance(_DEFAULT_DISPLAY, dict)
    else None
)
if (
    isinstance(_DEFAULT_WINDOWED_SIZE_RAW, list)
    and len(_DEFAULT_WINDOWED_SIZE_RAW) == 2
    and all(isinstance(v, int) and not isinstance(v, bool) for v in _DEFAULT_WINDOWED_SIZE_RAW)
):
    DEFAULT_WINDOWED_SIZE = (_DEFAULT_WINDOWED_SIZE_RAW[0], _DEFAULT_WINDOWED_SIZE_RAW[1])
else:  # pragma: no cover - guarded by config validation
    DEFAULT_WINDOWED_SIZE = (1200, 760)
_PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_MODE_KEYS = {"2d", "3d", "4d"}


def _default_settings_payload() -> dict[str, Any]:
    payload = default_settings_payload()
    payload.setdefault("display", {})
    display = payload["display"]
    if isinstance(display, dict):
        windowed_size = display.get("windowed_size")
        if (
            not isinstance(windowed_size, list)
            or len(windowed_size) != 2
            or any(isinstance(v, bool) or not isinstance(v, int) for v in windowed_size)
        ):
            display["windowed_size"] = [DEFAULT_WINDOWED_SIZE[0], DEFAULT_WINDOWED_SIZE[1]]
    payload.setdefault("analytics", {"score_logging_enabled": False})
    analytics = payload.get("analytics")
    if not isinstance(analytics, dict):
        payload["analytics"] = {"score_logging_enabled": False}
    elif not isinstance(analytics.get("score_logging_enabled"), bool):
        analytics["score_logging_enabled"] = False
    return payload


def _mode_key_for_dimension(dimension: int) -> str:
    if dimension not in (2, 3, 4):
        raise ValueError("dimension must be one of: 2, 3, 4")
    return f"{dimension}d"


def _merge_loaded_scalars(payload: dict[str, Any], loaded: dict[str, Any]) -> None:
    for key in ("version", "active_profile", "last_mode"):
        if key in loaded:
            payload[key] = loaded[key]


def _merge_loaded_section(payload: dict[str, Any], loaded: dict[str, Any], key: str) -> None:
    target = payload.get(key)
    incoming = loaded.get(key)
    if isinstance(target, dict) and isinstance(incoming, dict):
        target.update(incoming)


def _merge_loaded_mode_settings(payload: dict[str, Any], loaded: dict[str, Any]) -> None:
    loaded_settings = loaded.get("settings")
    if not isinstance(loaded_settings, dict):
        return
    merged = payload.get("settings")
    if not isinstance(merged, dict):
        return
    for mode_key, mode_settings in loaded_settings.items():
        if mode_key in merged and isinstance(mode_settings, dict):
            merged[mode_key].update(mode_settings)


def _load_payload() -> dict[str, Any]:
    payload = _default_settings_payload()
    if not STATE_FILE.exists():
        return payload
    try:
        raw = STATE_FILE.read_text(encoding="utf-8")
        loaded = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return payload
    if not isinstance(loaded, dict):
        return payload
    _merge_loaded_scalars(payload, loaded)
    _merge_loaded_section(payload, loaded, "display")
    _merge_loaded_section(payload, loaded, "audio")
    _merge_loaded_section(payload, loaded, "analytics")
    _merge_loaded_mode_settings(payload, loaded)
    _sanitize_payload(payload)
    return payload


def _save_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        temp_path = STATE_FILE.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temp_path.replace(STATE_FILE)
    except OSError as exc:
        return False, f"Failed saving menu state: {exc}"
    return True, f"Saved menu state to {STATE_FILE}"


def _sanitize_version_profile_mode(payload: dict[str, Any], default_payload: dict[str, Any]) -> None:
    version = payload.get("version")
    if isinstance(version, int) and version > 0:
        payload["version"] = version
    else:
        payload["version"] = default_payload["version"]

    raw_profile = payload.get("active_profile")
    if not isinstance(raw_profile, str) or not raw_profile.strip():
        payload["active_profile"] = default_payload["active_profile"]
    else:
        normalized_profile = raw_profile.strip().lower()
        if _PROFILE_NAME_RE.match(normalized_profile):
            payload["active_profile"] = normalized_profile
        else:
            payload["active_profile"] = default_payload["active_profile"]

    raw_mode = payload.get("last_mode")
    payload["last_mode"] = raw_mode if raw_mode in _MODE_KEYS else default_payload["last_mode"]


def _sanitize_display_section(payload: dict[str, Any], default_payload: dict[str, Any]) -> None:
    display = payload.setdefault("display", {})
    if not isinstance(display, dict):
        payload["display"] = {}
        display = payload["display"]
    default_display = default_payload.get("display", {})
    default_fullscreen = False
    default_windowed_size = [DEFAULT_WINDOWED_SIZE[0], DEFAULT_WINDOWED_SIZE[1]]
    if isinstance(default_display, dict):
        default_fullscreen = bool(default_display.get("fullscreen", False))
        raw_default_size = default_display.get("windowed_size")
        if (
            isinstance(raw_default_size, list)
            and len(raw_default_size) == 2
            and all(isinstance(v, int) and not isinstance(v, bool) for v in raw_default_size)
        ):
            default_windowed_size = raw_default_size

    fullscreen = bool(display.get("fullscreen", default_fullscreen))
    raw_size = display.get("windowed_size", default_windowed_size)
    if (
        not isinstance(raw_size, list)
        or len(raw_size) != 2
        or any(isinstance(v, bool) or not isinstance(v, int) for v in raw_size)
    ):
        raw_size = default_windowed_size
    width = max(640, raw_size[0])
    height = max(480, raw_size[1])
    display["fullscreen"] = fullscreen
    display["windowed_size"] = [width, height]


def _sanitize_audio_section(payload: dict[str, Any], default_payload: dict[str, Any]) -> None:
    audio = payload.setdefault("audio", {})
    if not isinstance(audio, dict):
        payload["audio"] = {}
        audio = payload["audio"]
    default_audio = default_payload.get("audio", {})
    default_master = 0.8
    default_sfx = 0.7
    default_mute = False
    if isinstance(default_audio, dict):
        raw_master = default_audio.get("master_volume")
        raw_sfx = default_audio.get("sfx_volume")
        if isinstance(raw_master, (int, float)) and not isinstance(raw_master, bool):
            default_master = float(raw_master)
        if isinstance(raw_sfx, (int, float)) and not isinstance(raw_sfx, bool):
            default_sfx = float(raw_sfx)
        default_mute = bool(default_audio.get("mute", False))

    master = audio.get("master_volume", default_master)
    sfx = audio.get("sfx_volume", default_sfx)
    mute = bool(audio.get("mute", default_mute))
    if not isinstance(master, (int, float)):
        master = default_master
    if not isinstance(sfx, (int, float)):
        sfx = default_sfx
    audio["master_volume"] = max(0.0, min(1.0, float(master)))
    audio["sfx_volume"] = max(0.0, min(1.0, float(sfx)))
    audio["mute"] = mute


def _sanitize_analytics_section(payload: dict[str, Any], default_payload: dict[str, Any]) -> None:
    analytics = payload.setdefault("analytics", {})
    if not isinstance(analytics, dict):
        payload["analytics"] = {}
        analytics = payload["analytics"]
    default_analytics = default_payload.get("analytics", {})
    default_logging = (
        bool(default_analytics.get("score_logging_enabled", False))
        if isinstance(default_analytics, dict)
        else False
    )
    analytics["score_logging_enabled"] = bool(
        analytics.get("score_logging_enabled", default_logging)
    )


def _sanitize_mode_settings(payload: dict[str, Any], default_payload: dict[str, Any]) -> None:
    settings = payload.get("settings")
    if not isinstance(settings, dict):
        settings = {}
    sanitized_settings: dict[str, dict[str, Any]] = {}
    default_settings = default_payload["settings"]
    for mode_key, mode_defaults in default_settings.items():
        mode_payload = settings.get(mode_key, {})
        if not isinstance(mode_payload, dict):
            mode_payload = {}
        merged_mode: dict[str, Any] = {}
        for attr_name, default_value in mode_defaults.items():
            value = mode_payload.get(attr_name, default_value)
            if isinstance(default_value, int):
                if isinstance(value, bool) or not isinstance(value, int):
                    value = default_value
            elif not isinstance(value, type(default_value)):
                value = default_value
            merged_mode[attr_name] = value
        sanitized_settings[mode_key] = merged_mode
    payload["settings"] = sanitized_settings


def _sanitize_payload(payload: dict[str, Any]) -> None:
    default_payload = _default_settings_payload()
    _sanitize_version_profile_mode(payload, default_payload)
    _sanitize_display_section(payload, default_payload)
    _sanitize_audio_section(payload, default_payload)
    _sanitize_analytics_section(payload, default_payload)
    _sanitize_mode_settings(payload, default_payload)


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
    mode_key = _mode_key_for_dimension(dimension)
    mode_settings = payload.get("settings", {}).get(mode_key, {})
    if isinstance(mode_settings, dict):
        _apply_mode_settings_to_state(state, mode_settings)
    state.active_profile = active_key_profile()
    return True, "Loaded saved menu settings"


def save_menu_settings(state: Any, dimension: int) -> tuple[bool, str]:
    payload = _load_payload()
    mode_key = _mode_key_for_dimension(dimension)
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
    mode_key = _mode_key_for_dimension(dimension)
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

    display = payload.get("display")
    if isinstance(display, dict):
        merged["display"].update(display)

    audio = payload.get("audio")
    if isinstance(audio, dict):
        merged["audio"].update(audio)

    analytics = payload.get("analytics")
    if isinstance(analytics, dict):
        merged["analytics"].update(analytics)

    settings = payload.get("settings")
    if isinstance(settings, dict):
        for mode_key, mode_settings in settings.items():
            if mode_key in merged["settings"] and isinstance(mode_settings, dict):
                merged["settings"][mode_key].update(mode_settings)
    _sanitize_payload(merged)
    return _save_payload(merged)


def get_display_settings() -> dict[str, Any]:
    payload = _load_payload()
    display = payload.get("display", {})
    if not isinstance(display, dict):
        defaults = _default_settings_payload().get("display", {})
        default_fullscreen = bool(defaults.get("fullscreen", False)) if isinstance(defaults, dict) else False
        default_windowed_size = (
            list(defaults.get("windowed_size", [DEFAULT_WINDOWED_SIZE[0], DEFAULT_WINDOWED_SIZE[1]]))
            if isinstance(defaults, dict)
            else [DEFAULT_WINDOWED_SIZE[0], DEFAULT_WINDOWED_SIZE[1]]
        )
        return {
            "fullscreen": default_fullscreen,
            "windowed_size": default_windowed_size,
        }
    defaults = _default_settings_payload().get("display", {})
    default_fullscreen = bool(defaults.get("fullscreen", False)) if isinstance(defaults, dict) else False
    default_windowed_size = (
        list(defaults.get("windowed_size", [DEFAULT_WINDOWED_SIZE[0], DEFAULT_WINDOWED_SIZE[1]]))
        if isinstance(defaults, dict)
        else [DEFAULT_WINDOWED_SIZE[0], DEFAULT_WINDOWED_SIZE[1]]
    )
    return {
        "fullscreen": bool(display.get("fullscreen", default_fullscreen)),
        "windowed_size": list(display.get("windowed_size", default_windowed_size)),
    }


def get_analytics_settings() -> dict[str, Any]:
    payload = _load_payload()
    analytics = payload.get("analytics", {})
    if not isinstance(analytics, dict):
        defaults = _default_settings_payload().get("analytics", {})
        default_logging = (
            bool(defaults.get("score_logging_enabled", False))
            if isinstance(defaults, dict)
            else False
        )
        return {"score_logging_enabled": default_logging}
    defaults = _default_settings_payload().get("analytics", {})
    default_logging = (
        bool(defaults.get("score_logging_enabled", False))
        if isinstance(defaults, dict)
        else False
    )
    return {
        "score_logging_enabled": bool(
            analytics.get("score_logging_enabled", default_logging)
        )
    }


def save_display_settings(
    *,
    fullscreen: bool | None = None,
    windowed_size: tuple[int, int] | None = None,
) -> tuple[bool, str]:
    payload = _load_payload()
    display = payload.setdefault("display", {})
    if fullscreen is not None:
        display["fullscreen"] = bool(fullscreen)
    if windowed_size is not None:
        width = max(640, int(windowed_size[0]))
        height = max(480, int(windowed_size[1]))
        display["windowed_size"] = [width, height]
    _sanitize_payload(payload)
    return _save_payload(payload)


def get_audio_settings() -> dict[str, Any]:
    payload = _load_payload()
    audio = payload.get("audio", {})
    defaults = _default_settings_payload().get("audio", {})
    default_master = float(defaults.get("master_volume", 0.8)) if isinstance(defaults, dict) else 0.8
    default_sfx = float(defaults.get("sfx_volume", 0.7)) if isinstance(defaults, dict) else 0.7
    default_mute = bool(defaults.get("mute", False)) if isinstance(defaults, dict) else False
    if not isinstance(audio, dict):
        return {"master_volume": default_master, "sfx_volume": default_sfx, "mute": default_mute}
    return {
        "master_volume": float(audio.get("master_volume", default_master)),
        "sfx_volume": float(audio.get("sfx_volume", default_sfx)),
        "mute": bool(audio.get("mute", default_mute)),
    }


def save_audio_settings(
    *,
    master_volume: float | None = None,
    sfx_volume: float | None = None,
    mute: bool | None = None,
) -> tuple[bool, str]:
    payload = _load_payload()
    audio = payload.setdefault("audio", {})
    if master_volume is not None:
        audio["master_volume"] = float(master_volume)
    if sfx_volume is not None:
        audio["sfx_volume"] = float(sfx_volume)
    if mute is not None:
        audio["mute"] = bool(mute)
    _sanitize_payload(payload)
    return _save_payload(payload)


def save_analytics_settings(
    *,
    score_logging_enabled: bool | None = None,
) -> tuple[bool, str]:
    payload = _load_payload()
    analytics = payload.setdefault("analytics", {})
    if score_logging_enabled is not None:
        analytics["score_logging_enabled"] = bool(score_logging_enabled)
    _sanitize_payload(payload)
    return _save_payload(payload)
