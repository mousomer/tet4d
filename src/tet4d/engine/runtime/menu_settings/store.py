from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from ..settings_sanitize import (
    ensure_default_settings_payload,
    merge_loaded_payload,
    sanitize_payload,
)
from ..settings_schema import MODE_KEYS, PROFILE_NAME_RE, atomic_write_json, read_json_value_or_raise


_MODE_KEYS = set(MODE_KEYS)


def normalize_active_profile_name(raw: Any, *, default: str) -> str:
    if isinstance(raw, str):
        value = raw.strip().lower()
        if PROFILE_NAME_RE.match(value):
            return value
    return default


def settings_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    settings = payload.get("settings")
    if isinstance(settings, dict):
        return settings
    settings = {}
    payload["settings"] = settings
    return settings


def mode_settings_mapping(
    settings: dict[str, Any],
    mode_key: str,
) -> dict[str, Any]:
    mode_settings = settings.get(mode_key)
    if isinstance(mode_settings, dict):
        return mode_settings
    mode_settings = {}
    settings[mode_key] = mode_settings
    return mode_settings


def iter_all_mode_settings(
    payload: dict[str, Any],
) -> tuple[tuple[str, dict[str, Any]], ...]:
    settings = settings_mapping(payload)
    mode_settings: list[tuple[str, dict[str, Any]]] = []
    for mode_key in MODE_KEYS:
        mode_settings.append((mode_key, mode_settings_mapping(settings, mode_key)))
    return tuple(mode_settings)


def mode_settings_view(settings: Any, mode_key: str) -> dict[str, Any]:
    if not isinstance(settings, dict):
        return {}
    mode_settings = settings.get(mode_key)
    return mode_settings if isinstance(mode_settings, dict) else {}


def default_settings_payload_for_runtime(
    base_default_payload: dict[str, Any],
    *,
    defaults: Any,
) -> dict[str, Any]:
    payload = deepcopy(base_default_payload)
    return ensure_default_settings_payload(
        payload,
        defaults=defaults,
    )


def load_payload(
    state_file,
    *,
    base_default_payload: dict[str, Any],
    defaults: Any,
) -> dict[str, Any]:
    payload = default_settings_payload_for_runtime(base_default_payload, defaults=defaults)
    if not state_file.exists():
        return payload
    try:
        loaded = read_json_value_or_raise(state_file)
    except (OSError, json.JSONDecodeError):
        return payload
    if not isinstance(loaded, dict):
        return payload

    merge_loaded_payload(payload, loaded)
    sanitize_payload(
        payload,
        default_payload=default_settings_payload_for_runtime(
            base_default_payload,
            defaults=defaults,
        ),
        defaults=defaults,
    )
    return payload


def save_payload(state_file, payload: dict[str, Any]) -> tuple[bool, str]:
    try:
        atomic_write_json(state_file, payload, trailing_newline=False)
    except OSError as exc:
        return False, f"Failed saving menu state: {exc}"
    return True, f"Saved menu state to {state_file}"


def sanitize_and_save_payload(
    state_file,
    payload: dict[str, Any],
    *,
    base_default_payload: dict[str, Any],
    defaults: Any,
) -> tuple[bool, str]:
    sanitize_payload(
        payload,
        default_payload=default_settings_payload_for_runtime(
            base_default_payload,
            defaults=defaults,
        ),
        defaults=defaults,
    )
    return save_payload(state_file, payload)


def save_payload_section(
    state_file,
    section_name: str,
    updates: dict[str, Any],
    *,
    base_default_payload: dict[str, Any],
    defaults: Any,
) -> tuple[bool, str]:
    payload = load_payload(
        state_file,
        base_default_payload=base_default_payload,
        defaults=defaults,
    )
    section = payload.setdefault(section_name, {})
    for key, value in updates.items():
        if value is not None:
            section[key] = value
    return sanitize_and_save_payload(
        state_file,
        payload,
        base_default_payload=base_default_payload,
        defaults=defaults,
    )


def apply_mode_settings_to_state(state: Any, mode_settings: dict[str, Any]) -> None:
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
