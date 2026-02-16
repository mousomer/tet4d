from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .keybindings import (
    active_key_profile,
    load_active_profile_bindings,
    set_active_key_profile,
)

STATE_DIR = Path(__file__).resolve().parent.parent / "state"
STATE_FILE = STATE_DIR / "menu_settings.json"
DEFAULT_WINDOWED_SIZE = (1200, 760)


def _default_settings_payload() -> dict[str, Any]:
    return {
        "version": 1,
        "active_profile": "small",
        "last_mode": "2d",
        "display": {
            "fullscreen": False,
            "windowed_size": [DEFAULT_WINDOWED_SIZE[0], DEFAULT_WINDOWED_SIZE[1]],
        },
        "audio": {
            "master_volume": 0.8,
            "sfx_volume": 0.7,
            "mute": False,
        },
        "settings": {
            "2d": {"width": 10, "height": 20, "piece_set_index": 0, "speed_level": 1},
            "3d": {"width": 6, "height": 18, "depth": 6, "piece_set_index": 0, "speed_level": 1},
            "4d": {
                "width": 10,
                "height": 20,
                "depth": 6,
                "fourth": 4,
                "speed_level": 1,
                "piece_set_index": 0,
            },
        },
    }


def _mode_key_for_dimension(dimension: int) -> str:
    if dimension not in (2, 3, 4):
        raise ValueError("dimension must be one of: 2, 3, 4")
    return f"{dimension}d"


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
    payload.update({k: v for k, v in loaded.items() if k in payload})
    settings = loaded.get("settings")
    if isinstance(settings, dict):
        merged = payload["settings"]
        for mode_key, mode_settings in settings.items():
            if mode_key in merged and isinstance(mode_settings, dict):
                merged[mode_key].update(mode_settings)
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


def _sanitize_payload(payload: dict[str, Any]) -> None:
    display = payload.setdefault("display", {})
    if not isinstance(display, dict):
        payload["display"] = {}
        display = payload["display"]
    fullscreen = bool(display.get("fullscreen", False))
    raw_size = display.get("windowed_size", [DEFAULT_WINDOWED_SIZE[0], DEFAULT_WINDOWED_SIZE[1]])
    if (
        not isinstance(raw_size, list)
        or len(raw_size) != 2
        or any(not isinstance(v, int) for v in raw_size)
    ):
        raw_size = [DEFAULT_WINDOWED_SIZE[0], DEFAULT_WINDOWED_SIZE[1]]
    width = max(640, raw_size[0])
    height = max(480, raw_size[1])
    display["fullscreen"] = fullscreen
    display["windowed_size"] = [width, height]

    audio = payload.setdefault("audio", {})
    if not isinstance(audio, dict):
        payload["audio"] = {}
        audio = payload["audio"]
    master = audio.get("master_volume", 0.8)
    sfx = audio.get("sfx_volume", 0.7)
    mute = bool(audio.get("mute", False))
    if not isinstance(master, (int, float)):
        master = 0.8
    if not isinstance(sfx, (int, float)):
        sfx = 0.7
    audio["master_volume"] = max(0.0, min(1.0, float(master)))
    audio["sfx_volume"] = max(0.0, min(1.0, float(sfx)))
    audio["mute"] = mute


def apply_saved_menu_settings(
    state: Any,
    dimension: int,
    include_profile: bool = True,
) -> tuple[bool, str]:
    payload = _load_payload()
    if include_profile:
        profile = payload.get("active_profile")
        if isinstance(profile, str):
            ok_profile, msg_profile = set_active_key_profile(profile)
            if not ok_profile:
                return False, msg_profile
            ok_bindings, msg_bindings = load_active_profile_bindings()
            if not ok_bindings:
                return False, msg_bindings
    mode_key = _mode_key_for_dimension(dimension)
    mode_settings = payload.get("settings", {}).get(mode_key, {})
    if isinstance(mode_settings, dict):
        for attr_name, value in mode_settings.items():
            if hasattr(state.settings, attr_name):
                current = getattr(state.settings, attr_name)
                if isinstance(current, int):
                    if isinstance(value, bool) or not isinstance(value, int):
                        continue
                elif not isinstance(value, type(current)):
                    continue
                setattr(state.settings, attr_name, value)
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
    merged.update(payload)
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
        return {
            "fullscreen": False,
            "windowed_size": [DEFAULT_WINDOWED_SIZE[0], DEFAULT_WINDOWED_SIZE[1]],
        }
    return {
        "fullscreen": bool(display.get("fullscreen", False)),
        "windowed_size": list(display.get("windowed_size", [DEFAULT_WINDOWED_SIZE[0], DEFAULT_WINDOWED_SIZE[1]])),
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
    if not isinstance(audio, dict):
        return {"master_volume": 0.8, "sfx_volume": 0.7, "mute": False}
    return {
        "master_volume": float(audio.get("master_volume", 0.8)),
        "sfx_volume": float(audio.get("sfx_volume", 0.7)),
        "mute": bool(audio.get("mute", False)),
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
