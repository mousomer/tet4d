from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any


FieldSpec = tuple[str, str, int, int]

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config" / "menu"
DEFAULTS_FILE = CONFIG_DIR / "defaults.json"
STRUCTURE_FILE = CONFIG_DIR / "structure.json"
_MODE_KEYS = ("2d", "3d", "4d")


def _read_json_payload(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - exercised by runtime failures
        raise RuntimeError(f"Failed reading config file {path}: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in config file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Config file {path} must contain a JSON object")
    return payload


def _mode_key_for_dimension(dimension: int) -> str:
    if dimension not in (2, 3, 4):
        raise ValueError("dimension must be one of: 2, 3, 4")
    return f"{dimension}d"


def _validate_mode_settings(mode_key: str, settings: object) -> dict[str, int]:
    if not isinstance(settings, dict):
        raise RuntimeError(f"defaults.settings.{mode_key} must be an object")
    validated: dict[str, int] = {}
    for attr_name, value in settings.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise RuntimeError(
                f"defaults.settings.{mode_key}.{attr_name} must be an integer"
            )
        validated[attr_name] = value
    return validated


def _validate_defaults_payload(payload: dict[str, Any]) -> dict[str, Any]:
    required_top_level = ("version", "active_profile", "last_mode", "display", "audio", "settings")
    missing = [key for key in required_top_level if key not in payload]
    if missing:
        raise RuntimeError(f"defaults config missing keys: {', '.join(missing)}")

    version = payload["version"]
    if isinstance(version, bool) or not isinstance(version, int) or version <= 0:
        raise RuntimeError("defaults.version must be a positive integer")

    active_profile = payload["active_profile"]
    if not isinstance(active_profile, str) or not active_profile.strip():
        raise RuntimeError("defaults.active_profile must be a non-empty string")

    last_mode = payload["last_mode"]
    if last_mode not in _MODE_KEYS:
        raise RuntimeError("defaults.last_mode must be one of: 2d, 3d, 4d")

    display = payload["display"]
    if not isinstance(display, dict):
        raise RuntimeError("defaults.display must be an object")
    if not isinstance(display.get("fullscreen"), bool):
        raise RuntimeError("defaults.display.fullscreen must be a boolean")
    windowed_size = display.get("windowed_size")
    if (
        not isinstance(windowed_size, list)
        or len(windowed_size) != 2
        or any(isinstance(v, bool) or not isinstance(v, int) for v in windowed_size)
    ):
        raise RuntimeError("defaults.display.windowed_size must be [int, int]")

    audio = payload["audio"]
    if not isinstance(audio, dict):
        raise RuntimeError("defaults.audio must be an object")
    for key in ("master_volume", "sfx_volume"):
        value = audio.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RuntimeError(f"defaults.audio.{key} must be a number")
    if not isinstance(audio.get("mute"), bool):
        raise RuntimeError("defaults.audio.mute must be a boolean")

    settings = payload["settings"]
    if not isinstance(settings, dict):
        raise RuntimeError("defaults.settings must be an object")
    validated_settings: dict[str, dict[str, int]] = {}
    for mode_key in _MODE_KEYS:
        if mode_key not in settings:
            raise RuntimeError(f"defaults.settings missing mode key: {mode_key}")
        validated_settings[mode_key] = _validate_mode_settings(mode_key, settings[mode_key])

    return {
        "version": version,
        "active_profile": active_profile,
        "last_mode": last_mode,
        "display": display,
        "audio": audio,
        "settings": validated_settings,
    }


def _validate_menu_item(raw_item: object) -> tuple[str, str]:
    if not isinstance(raw_item, dict):
        raise RuntimeError("structure.launcher_menu entries must be objects")
    action = raw_item.get("action")
    label = raw_item.get("label")
    if not isinstance(action, str) or not action:
        raise RuntimeError("structure.launcher_menu.action must be a non-empty string")
    if not isinstance(label, str) or not label:
        raise RuntimeError("structure.launcher_menu.label must be a non-empty string")
    return action, label


def _validate_row_list(raw_rows: object, key: str) -> tuple[str, ...]:
    if not isinstance(raw_rows, list):
        raise RuntimeError(f"structure.{key} must be a list")
    rows: list[str] = []
    for idx, row in enumerate(raw_rows):
        if not isinstance(row, str) or not row:
            raise RuntimeError(f"structure.{key}[{idx}] must be a non-empty string")
        rows.append(row)
    if not rows:
        raise RuntimeError(f"structure.{key} must not be empty")
    return tuple(rows)


def _resolve_field_max(raw_max: object, piece_set_max: int, mode_key: str, attr_name: str) -> int:
    if raw_max == "piece_set_max":
        return max(0, int(piece_set_max))
    if isinstance(raw_max, bool) or not isinstance(raw_max, int):
        raise RuntimeError(f"structure.setup_fields.{mode_key}.{attr_name}.max must be int or 'piece_set_max'")
    return raw_max


def _validate_setup_fields(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    setup_fields = payload.get("setup_fields")
    if not isinstance(setup_fields, dict):
        raise RuntimeError("structure.setup_fields must be an object")

    validated: dict[str, list[dict[str, Any]]] = {}
    for mode_key in _MODE_KEYS:
        raw_fields = setup_fields.get(mode_key)
        if not isinstance(raw_fields, list):
            raise RuntimeError(f"structure.setup_fields.{mode_key} must be a list")
        fields: list[dict[str, Any]] = []
        for idx, raw_field in enumerate(raw_fields):
            if not isinstance(raw_field, dict):
                raise RuntimeError(f"structure.setup_fields.{mode_key}[{idx}] must be an object")
            label = raw_field.get("label")
            attr_name = raw_field.get("attr")
            min_val = raw_field.get("min")
            max_val = raw_field.get("max")
            if not isinstance(label, str) or not label:
                raise RuntimeError(
                    f"structure.setup_fields.{mode_key}[{idx}].label must be a non-empty string"
                )
            if not isinstance(attr_name, str) or not attr_name:
                raise RuntimeError(
                    f"structure.setup_fields.{mode_key}[{idx}].attr must be a non-empty string"
                )
            if isinstance(min_val, bool) or not isinstance(min_val, int):
                raise RuntimeError(f"structure.setup_fields.{mode_key}[{idx}].min must be int")
            if isinstance(max_val, bool) or not isinstance(max_val, (int, str)):
                raise RuntimeError(
                    f"structure.setup_fields.{mode_key}[{idx}].max must be int or 'piece_set_max'"
                )
            fields.append(
                {
                    "label": label,
                    "attr": attr_name,
                    "min": min_val,
                    "max": max_val,
                }
            )
        if not fields:
            raise RuntimeError(f"structure.setup_fields.{mode_key} must not be empty")
        validated[mode_key] = fields
    return validated


def _validate_structure_payload(payload: dict[str, Any]) -> dict[str, Any]:
    launcher_menu = payload.get("launcher_menu")
    if not isinstance(launcher_menu, list):
        raise RuntimeError("structure.launcher_menu must be a list")
    menu_items = tuple(_validate_menu_item(item) for item in launcher_menu)
    if not menu_items:
        raise RuntimeError("structure.launcher_menu must not be empty")
    validated = {
        "launcher_menu": menu_items,
        "settings_hub_rows": _validate_row_list(payload.get("settings_hub_rows"), "settings_hub_rows"),
        "bot_options_rows": _validate_row_list(payload.get("bot_options_rows"), "bot_options_rows"),
        "setup_fields": _validate_setup_fields(payload),
    }
    return validated


@lru_cache(maxsize=1)
def _defaults_payload() -> dict[str, Any]:
    payload = _read_json_payload(DEFAULTS_FILE)
    return _validate_defaults_payload(payload)


@lru_cache(maxsize=1)
def _structure_payload() -> dict[str, Any]:
    payload = _read_json_payload(STRUCTURE_FILE)
    return _validate_structure_payload(payload)


def default_settings_payload() -> dict[str, Any]:
    return deepcopy(_defaults_payload())


def launcher_menu_items() -> tuple[tuple[str, str], ...]:
    return tuple(_structure_payload()["launcher_menu"])


def settings_hub_rows() -> tuple[str, ...]:
    return tuple(_structure_payload()["settings_hub_rows"])


def bot_options_rows() -> tuple[str, ...]:
    return tuple(_structure_payload()["bot_options_rows"])


def setup_fields_for_dimension(dimension: int, *, piece_set_max: int = 0) -> list[FieldSpec]:
    mode_key = _mode_key_for_dimension(dimension)
    raw_fields = _structure_payload()["setup_fields"][mode_key]
    fields: list[FieldSpec] = []
    for raw_field in raw_fields:
        label = raw_field["label"]
        attr_name = raw_field["attr"]
        min_val = raw_field["min"]
        max_val = _resolve_field_max(raw_field["max"], piece_set_max, mode_key, attr_name)
        if min_val > max_val:
            raise RuntimeError(
                f"Invalid field bounds for {mode_key}.{attr_name}: min {min_val} > max {max_val}"
            )
        fields.append((label, attr_name, min_val, max_val))
    return fields


@lru_cache(maxsize=1)
def _bot_defaults_by_mode() -> dict[str, dict[str, int]]:
    defaults = _defaults_payload()
    settings = defaults["settings"]
    bot_defaults: dict[str, dict[str, int]] = {}
    for mode_key in _MODE_KEYS:
        mode_settings = settings[mode_key]
        bot_values = {
            attr_name: value
            for attr_name, value in mode_settings.items()
            if attr_name.startswith("bot_")
        }
        if not bot_values:
            raise RuntimeError(f"defaults.settings.{mode_key} must contain bot_* keys")
        bot_defaults[mode_key] = bot_values
    return bot_defaults


def bot_defaults_by_mode() -> dict[str, dict[str, int]]:
    return deepcopy(_bot_defaults_by_mode())

