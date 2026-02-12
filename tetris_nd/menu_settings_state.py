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


def _default_settings_payload() -> dict[str, Any]:
    return {
        "version": 1,
        "active_profile": "small",
        "last_mode": "2d",
        "settings": {
            "2d": {"width": 10, "height": 20, "speed_level": 1},
            "3d": {"width": 6, "height": 18, "depth": 6, "speed_level": 1},
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
    return payload


def _save_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    except OSError as exc:
        return False, f"Failed saving menu state: {exc}"
    return True, f"Saved menu state to {STATE_FILE}"


def apply_saved_menu_settings(state: Any, dimension: int) -> tuple[bool, str]:
    payload = _load_payload()
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


def load_menu_settings(state: Any, dimension: int) -> tuple[bool, str]:
    return apply_saved_menu_settings(state, dimension)


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
