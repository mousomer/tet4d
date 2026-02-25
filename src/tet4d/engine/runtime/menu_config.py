from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..ui_logic.menu_action_contracts import PARITY_ACTION_IDS
from .project_config import project_root_path
from .runtime_config import playbot_budget_table_for_ndim

FieldSpec = tuple[str, str, int, int]

CONFIG_DIR = project_root_path() / "config" / "menu"
DEFAULTS_FILE = CONFIG_DIR / "defaults.json"
STRUCTURE_FILE = CONFIG_DIR / "structure.json"
_MODE_KEYS = ("2d", "3d", "4d")
_SETTINGS_HUB_LAYOUT_KINDS = {"header", "item"}
_MENU_ITEM_TYPES = {"action", "submenu", "route"}
_MENU_ENTRYPOINT_KEYS = ("launcher", "pause")
_DEFAULT_MENU_ENTRYPOINTS = {
    "launcher": "launcher_root",
    "pause": "pause_root",
}
_LEGACY_PLAY_MENU_ID = "launcher_play"


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


def _as_non_empty_string(value: object, *, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{path} must be a non-empty string")
    return value.strip()


def _require_object(value: object, *, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must be an object")
    return value


def _require_bool(value: object, *, path: str) -> bool:
    if not isinstance(value, bool):
        raise RuntimeError(f"{path} must be a boolean")
    return value


def _require_int(value: object, *, path: str, min_value: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError(f"{path} must be an integer")
    if min_value is not None and value < min_value:
        raise RuntimeError(f"{path} must be >= {min_value}")
    return value


def _require_number(value: object, *, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{path} must be a number")
    return float(value)


def _validate_string_list(
    raw_values: object,
    *,
    path: str,
    normalize_lower: bool = False,
    unique: bool = False,
) -> tuple[str, ...]:
    if not isinstance(raw_values, list):
        raise RuntimeError(f"{path} must be a list")
    values: list[str] = []
    seen: set[str] = set()
    for idx, raw_value in enumerate(raw_values):
        value = _as_non_empty_string(raw_value, path=f"{path}[{idx}]")
        if normalize_lower:
            value = value.lower()
        if unique and value in seen:
            raise RuntimeError(f"{path} contains duplicate value: {value}")
        seen.add(value)
        values.append(value)
    if not values:
        raise RuntimeError(f"{path} must not be empty")
    return tuple(values)


def _mode_key_for_dimension(dimension: int) -> str:
    if dimension not in (2, 3, 4):
        raise ValueError("dimension must be one of: 2, 3, 4")
    return f"{dimension}d"


def _validate_mode_settings(mode_key: str, settings: object) -> dict[str, int]:
    settings_obj = _require_object(settings, path=f"defaults.settings.{mode_key}")
    validated: dict[str, int] = {}
    for attr_name, value in settings_obj.items():
        validated[attr_name] = _require_int(
            value,
            path=f"defaults.settings.{mode_key}.{attr_name}",
        )
    return validated


def _validate_defaults_meta(payload: dict[str, Any]) -> tuple[int, str, str]:
    required_top_level = (
        "version",
        "active_profile",
        "last_mode",
        "display",
        "audio",
        "analytics",
        "settings",
    )
    missing = [key for key in required_top_level if key not in payload]
    if missing:
        raise RuntimeError(f"defaults config missing keys: {', '.join(missing)}")

    version = _require_int(payload["version"], path="defaults.version", min_value=1)

    active_profile = payload["active_profile"]
    if not isinstance(active_profile, str) or not active_profile.strip():
        raise RuntimeError("defaults.active_profile must be a non-empty string")

    last_mode = payload["last_mode"]
    if last_mode not in _MODE_KEYS:
        raise RuntimeError("defaults.last_mode must be one of: 2d, 3d, 4d")
    return version, active_profile, last_mode


def _validate_defaults_display(payload: dict[str, Any]) -> dict[str, Any]:
    display = _require_object(payload["display"], path="defaults.display")
    _require_bool(display.get("fullscreen"), path="defaults.display.fullscreen")
    windowed_size = display.get("windowed_size")
    if (
        not isinstance(windowed_size, list)
        or len(windowed_size) != 2
        or any(isinstance(v, bool) or not isinstance(v, int) for v in windowed_size)
    ):
        raise RuntimeError("defaults.display.windowed_size must be [int, int]")
    return display


def _validate_defaults_audio(payload: dict[str, Any]) -> dict[str, Any]:
    audio = _require_object(payload["audio"], path="defaults.audio")
    for key in ("master_volume", "sfx_volume"):
        _require_number(audio.get(key), path=f"defaults.audio.{key}")
    _require_bool(audio.get("mute"), path="defaults.audio.mute")
    return audio


def _validate_defaults_analytics(payload: dict[str, Any]) -> dict[str, Any]:
    analytics = _require_object(payload["analytics"], path="defaults.analytics")
    _require_bool(
        analytics.get("score_logging_enabled"),
        path="defaults.analytics.score_logging_enabled",
    )
    return analytics


def _validate_defaults_settings(payload: dict[str, Any]) -> dict[str, dict[str, int]]:
    settings = _require_object(payload["settings"], path="defaults.settings")
    validated_settings: dict[str, dict[str, int]] = {}
    for mode_key in _MODE_KEYS:
        if mode_key not in settings:
            raise RuntimeError(f"defaults.settings missing mode key: {mode_key}")
        validated_settings[mode_key] = _validate_mode_settings(
            mode_key, settings[mode_key]
        )
    return validated_settings


def _runtime_budget_for_mode(mode_key: str) -> int:
    ndims = {"2d": 2, "3d": 3, "4d": 4}[mode_key]
    return int(playbot_budget_table_for_ndim(ndims)[1])


def _sync_runtime_bot_budget(settings: dict[str, dict[str, int]]) -> None:
    for mode_key in _MODE_KEYS:
        mode_settings = settings.get(mode_key)
        if not isinstance(mode_settings, dict):
            continue
        mode_settings["bot_budget_ms"] = _runtime_budget_for_mode(mode_key)


def _validate_defaults_payload(payload: dict[str, Any]) -> dict[str, Any]:
    version, active_profile, last_mode = _validate_defaults_meta(payload)
    display = _validate_defaults_display(payload)
    audio = _validate_defaults_audio(payload)
    analytics = _validate_defaults_analytics(payload)
    validated_settings = _validate_defaults_settings(payload)
    _sync_runtime_bot_budget(validated_settings)
    return {
        "version": version,
        "active_profile": active_profile,
        "last_mode": last_mode,
        "display": display,
        "audio": audio,
        "analytics": analytics,
        "settings": validated_settings,
    }


def _validate_menu_item(raw_item: object) -> tuple[str, str]:
    entry = _require_object(raw_item, path="structure.launcher_menu entries")
    action = _as_non_empty_string(
        entry.get("action"),
        path="structure.launcher_menu.action",
    )
    label = _as_non_empty_string(
        entry.get("label"),
        path="structure.launcher_menu.label",
    )
    return action, label


def _validate_row_list(raw_rows: object, key: str) -> tuple[str, ...]:
    return _validate_string_list(raw_rows, path=f"structure.{key}")


def _validate_action_list(raw_actions: object, key: str) -> tuple[str, ...]:
    return _validate_string_list(
        raw_actions,
        path=f"structure.{key}",
        normalize_lower=True,
        unique=True,
    )


def _validate_menu_graph_item(
    raw_item: object,
    *,
    menu_id: str,
    idx: int,
) -> dict[str, str]:
    path = f"structure.menus.{menu_id}.items[{idx}]"
    item = _require_object(raw_item, path=path)
    item_type = _as_non_empty_string(item.get("type"), path=f"{path}.type").lower()
    label = _as_non_empty_string(item.get("label"), path=f"{path}.label")
    if item_type not in _MENU_ITEM_TYPES:
        raise RuntimeError(
            f"{path}.type must be one of: " + ", ".join(sorted(_MENU_ITEM_TYPES))
        )
    if item_type == "action":
        action_id = _as_non_empty_string(
            item.get("action_id"), path=f"{path}.action_id"
        ).lower()
        return {
            "type": "action",
            "label": label,
            "action_id": action_id,
        }
    if item_type == "submenu":
        target_menu_id = _as_non_empty_string(
            item.get("menu_id"), path=f"{path}.menu_id"
        ).lower()
        return {
            "type": "submenu",
            "label": label,
            "menu_id": target_menu_id,
        }
    route_id = _as_non_empty_string(
        item.get("route_id"), path=f"{path}.route_id"
    ).lower()
    return {
        "type": "route",
        "label": label,
        "route_id": route_id,
    }


def _validate_menus_graph(raw_menus: object) -> dict[str, dict[str, Any]]:
    menus = _require_object(raw_menus, path="structure.menus")
    if not menus:
        raise RuntimeError("structure.menus must not be empty")

    validated: dict[str, dict[str, Any]] = {}
    for raw_menu_id, raw_menu in menus.items():
        menu_id = _as_non_empty_string(raw_menu_id, path="structure.menus keys").lower()
        menu_obj = _require_object(raw_menu, path=f"structure.menus.{menu_id}")
        title = _as_non_empty_string(
            menu_obj.get("title"), path=f"structure.menus.{menu_id}.title"
        )
        raw_items = menu_obj.get("items")
        if not isinstance(raw_items, list) or not raw_items:
            raise RuntimeError(
                f"structure.menus.{menu_id}.items must be a non-empty list"
            )
        items = tuple(
            _validate_menu_graph_item(raw_item, menu_id=menu_id, idx=idx)
            for idx, raw_item in enumerate(raw_items)
        )
        validated[menu_id] = {
            "title": title,
            "items": items,
        }

    for menu_id, menu in validated.items():
        items: tuple[dict[str, str], ...] = menu["items"]
        for idx, item in enumerate(items):
            if item["type"] != "submenu":
                continue
            target_menu_id = item["menu_id"]
            if target_menu_id not in validated:
                raise RuntimeError(
                    f"structure.menus.{menu_id}.items[{idx}] references unknown submenu target: {target_menu_id}"
                )
    return validated


def _validate_menu_entrypoints(
    payload: dict[str, Any],
    *,
    menus: dict[str, dict[str, Any]],
) -> dict[str, str]:
    raw_entrypoints = payload.get("menu_entrypoints")
    if raw_entrypoints is None:
        entrypoints = dict(_DEFAULT_MENU_ENTRYPOINTS)
    else:
        entrypoints_obj = _require_object(
            raw_entrypoints, path="structure.menu_entrypoints"
        )
        entrypoints = {}
        for key in _MENU_ENTRYPOINT_KEYS:
            default_id = _DEFAULT_MENU_ENTRYPOINTS[key]
            raw_value = entrypoints_obj.get(key, default_id)
            menu_id = _as_non_empty_string(
                raw_value,
                path=f"structure.menu_entrypoints.{key}",
            ).lower()
            entrypoints[key] = menu_id
    for key in _MENU_ENTRYPOINT_KEYS:
        menu_id = entrypoints[key]
        if menu_id not in menus:
            raise RuntimeError(
                f"structure.menu_entrypoints.{key} references unknown menu id: {menu_id}"
            )
    return entrypoints


def _legacy_menus_graph(
    launcher_menu: tuple[tuple[str, str], ...],
    pause_rows: tuple[str, ...],
    pause_actions: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    launcher_items: list[dict[str, str]] = []
    has_play_hub = False
    for action, label in launcher_menu:
        if action == "play":
            has_play_hub = True
            launcher_items.append(
                {
                    "type": "submenu",
                    "label": label,
                    "menu_id": _LEGACY_PLAY_MENU_ID,
                }
            )
            continue
        launcher_items.append(
            {
                "type": "action",
                "label": label,
                "action_id": action,
            }
        )

    menus: dict[str, dict[str, Any]] = {
        _DEFAULT_MENU_ENTRYPOINTS["launcher"]: {
            "title": "Main Menu",
            "items": tuple(launcher_items),
        },
        _DEFAULT_MENU_ENTRYPOINTS["pause"]: {
            "title": "Pause Menu",
            "items": tuple(
                {
                    "type": "action",
                    "label": label,
                    "action_id": action,
                }
                for label, action in zip(pause_rows, pause_actions)
            ),
        },
    }
    if has_play_hub:
        menus[_LEGACY_PLAY_MENU_ID] = {
            "title": "Choose Mode",
            "items": (
                {"type": "action", "label": "Play 2D", "action_id": "play_2d"},
                {"type": "action", "label": "Play 3D", "action_id": "play_3d"},
                {"type": "action", "label": "Play 4D", "action_id": "play_4d"},
            ),
        }
    return menus


def _validate_or_build_menus(
    payload: dict[str, Any],
    *,
    launcher_menu: tuple[tuple[str, str], ...],
    pause_rows: tuple[str, ...],
    pause_actions: tuple[str, ...],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    raw_menus = payload.get("menus")
    if raw_menus is None:
        if not launcher_menu:
            raise RuntimeError(
                "structure.launcher_menu must be provided when structure.menus is absent"
            )
        if not pause_rows or not pause_actions:
            raise RuntimeError(
                "structure.pause_menu_rows and structure.pause_menu_actions must be provided when structure.menus is absent"
            )
        return _legacy_menus_graph(launcher_menu, pause_rows, pause_actions), dict(
            _DEFAULT_MENU_ENTRYPOINTS
        )

    menus = _validate_menus_graph(raw_menus)
    entrypoints = _validate_menu_entrypoints(payload, menus=menus)
    return menus, entrypoints


def _validate_settings_hub_layout_row(
    raw_row: object, *, idx: int
) -> tuple[dict[str, str], bool]:
    path = f"structure.settings_hub_layout_rows[{idx}]"
    row = _require_object(raw_row, path=path)
    kind = row.get("kind")
    row_key = row.get("row_key", "")
    if not isinstance(kind, str) or kind not in _SETTINGS_HUB_LAYOUT_KINDS:
        raise RuntimeError(
            f"{path}.kind must be one of: "
            + ", ".join(sorted(_SETTINGS_HUB_LAYOUT_KINDS))
        )
    label = _as_non_empty_string(row.get("label"), path=f"{path}.label")
    if kind == "header":
        if row_key not in ("", None):
            raise RuntimeError(f"{path}.row_key must be empty for header rows")
        return {"kind": "header", "label": label, "row_key": ""}, False
    if not isinstance(row_key, str) or not row_key.strip():
        raise RuntimeError(f"{path}.row_key must be a non-empty string for item rows")
    return {"kind": "item", "label": label, "row_key": row_key.strip().lower()}, True


def _validate_settings_hub_layout_rows(
    payload: dict[str, Any],
) -> tuple[dict[str, str], ...]:
    raw_rows = payload.get("settings_hub_layout_rows")
    if not isinstance(raw_rows, list):
        raise RuntimeError("structure.settings_hub_layout_rows must be a list")
    rows: list[dict[str, str]] = []
    item_count = 0
    for idx, raw_row in enumerate(raw_rows):
        row, is_item = _validate_settings_hub_layout_row(raw_row, idx=idx)
        rows.append(row)
        item_count += int(is_item)
    if not rows:
        raise RuntimeError("structure.settings_hub_layout_rows must not be empty")
    if item_count == 0:
        raise RuntimeError(
            "structure.settings_hub_layout_rows must include at least one item row"
        )
    return tuple(rows)


def _resolve_field_max(
    raw_max: object,
    piece_set_max: int,
    topology_profile_max: int,
    mode_key: str,
    attr_name: str,
) -> int:
    if raw_max == "piece_set_max":
        return max(0, int(piece_set_max))
    if raw_max == "topology_profile_max":
        return max(0, int(topology_profile_max))
    if isinstance(raw_max, bool) or not isinstance(raw_max, int):
        raise RuntimeError(
            f"structure.setup_fields.{mode_key}.{attr_name}.max must be int or dynamic max token"
        )
    return raw_max


def _validate_setup_field(
    raw_field: object, *, mode_key: str, idx: int
) -> dict[str, Any]:
    path = f"structure.setup_fields.{mode_key}[{idx}]"
    field = _require_object(raw_field, path=path)
    label = _as_non_empty_string(field.get("label"), path=f"{path}.label")
    attr_name = _as_non_empty_string(field.get("attr"), path=f"{path}.attr")
    min_val = _require_int(field.get("min"), path=f"{path}.min")
    max_val = field.get("max")
    if isinstance(max_val, bool) or not isinstance(max_val, (int, str)):
        raise RuntimeError(f"{path}.max must be int or 'piece_set_max'")
    return {
        "label": label,
        "attr": attr_name,
        "min": min_val,
        "max": max_val,
    }


def _validate_setup_fields(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    setup_fields = payload.get("setup_fields")
    if not isinstance(setup_fields, dict):
        raise RuntimeError("structure.setup_fields must be an object")

    validated: dict[str, list[dict[str, Any]]] = {}
    for mode_key in _MODE_KEYS:
        raw_fields = setup_fields.get(mode_key)
        if not isinstance(raw_fields, list):
            raise RuntimeError(f"structure.setup_fields.{mode_key} must be a list")
        fields = [
            _validate_setup_field(raw_field, mode_key=mode_key, idx=idx)
            for idx, raw_field in enumerate(raw_fields)
        ]
        if not fields:
            raise RuntimeError(f"structure.setup_fields.{mode_key} must not be empty")
        validated[mode_key] = fields
    return validated


def _validate_scope_order(raw_docs: dict[str, Any]) -> tuple[str, ...]:
    return _validate_string_list(
        raw_docs.get("scope_order"),
        path="structure.keybinding_category_docs.scope_order",
        normalize_lower=True,
    )


def _validate_group_doc(
    group_name: str, raw_group: object
) -> tuple[str, dict[str, str]]:
    clean_name = _as_non_empty_string(
        group_name,
        path="structure.keybinding_category_docs.groups keys",
    ).lower()
    if not isinstance(raw_group, dict):
        raise RuntimeError(
            f"structure.keybinding_category_docs.groups.{group_name} must be an object"
        )
    label = _as_non_empty_string(
        raw_group.get("label"),
        path=f"structure.keybinding_category_docs.groups.{group_name}.label",
    )
    description = _as_non_empty_string(
        raw_group.get("description"),
        path=f"structure.keybinding_category_docs.groups.{group_name}.description",
    )
    return clean_name, {
        "label": label,
        "description": description,
    }


def _validate_group_docs(raw_docs: dict[str, Any]) -> dict[str, dict[str, str]]:
    raw_groups = raw_docs.get("groups")
    if not isinstance(raw_groups, dict):
        raise RuntimeError(
            "structure.keybinding_category_docs.groups must be an object"
        )
    groups: dict[str, dict[str, str]] = {}
    for group_name, raw_group in raw_groups.items():
        key, value = _validate_group_doc(group_name, raw_group)
        groups[key] = value
    return groups


def _validate_keybinding_category_docs(payload: dict[str, Any]) -> dict[str, Any]:
    raw_docs = payload.get("keybinding_category_docs")
    if raw_docs is None:
        return {
            "scope_order": ("all", "2d", "3d", "4d"),
            "groups": {},
        }
    if not isinstance(raw_docs, dict):
        raise RuntimeError("structure.keybinding_category_docs must be an object")
    return {
        "scope_order": _validate_scope_order(raw_docs),
        "groups": _validate_group_docs(raw_docs),
    }


def _validate_settings_category_docs(
    payload: dict[str, Any],
) -> tuple[dict[str, str], ...]:
    raw_docs = payload.get("settings_category_docs")
    if raw_docs is None:
        return tuple()
    if not isinstance(raw_docs, list):
        raise RuntimeError("structure.settings_category_docs must be a list")

    docs: list[dict[str, str]] = []
    for idx, raw_item in enumerate(raw_docs):
        entry = _require_object(
            raw_item, path=f"structure.settings_category_docs[{idx}]"
        )
        item_id = _as_non_empty_string(
            entry.get("id"),
            path=f"structure.settings_category_docs[{idx}].id",
        ).lower()
        label = _as_non_empty_string(
            entry.get("label"),
            path=f"structure.settings_category_docs[{idx}].label",
        )
        description = _as_non_empty_string(
            entry.get("description"),
            path=f"structure.settings_category_docs[{idx}].description",
        )
        docs.append(
            {
                "id": item_id,
                "label": label,
                "description": description,
            }
        )
    return tuple(docs)


def _validate_settings_split_rules(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("settings_split_rules")
    if raw is None:
        return {
            "max_top_level_fields": 5,
            "max_top_level_actions": 2,
            "split_when_mode_specific": True,
        }
    rules = _require_object(raw, path="structure.settings_split_rules")
    max_fields = _require_int(
        rules.get("max_top_level_fields"),
        path="structure.settings_split_rules.max_top_level_fields",
        min_value=1,
    )
    max_actions = _require_int(
        rules.get("max_top_level_actions"),
        path="structure.settings_split_rules.max_top_level_actions",
        min_value=1,
    )
    split_mode_specific = _require_bool(
        rules.get("split_when_mode_specific"),
        path="structure.settings_split_rules.split_when_mode_specific",
    )
    return {
        "max_top_level_fields": max_fields,
        "max_top_level_actions": max_actions,
        "split_when_mode_specific": split_mode_specific,
    }


def _validate_settings_category_metrics(
    payload: dict[str, Any],
    settings_docs: tuple[dict[str, str], ...],
) -> dict[str, dict[str, Any]]:
    raw = payload.get("settings_category_metrics")
    docs_by_id = {entry["id"]: entry for entry in settings_docs}
    if not isinstance(raw, dict):
        return {}

    metrics: dict[str, dict[str, Any]] = {}
    for category_id, raw_entry in raw.items():
        if not isinstance(category_id, str) or not category_id.strip():
            raise RuntimeError(
                "structure.settings_category_metrics keys must be non-empty strings"
            )
        clean_id = category_id.strip().lower()
        if clean_id not in docs_by_id:
            raise RuntimeError(
                f"structure.settings_category_metrics.{clean_id} has no matching settings_category_docs id"
            )
        entry = _require_object(
            raw_entry,
            path=f"structure.settings_category_metrics.{clean_id}",
        )
        field_count = _require_int(
            entry.get("field_count"),
            path=f"structure.settings_category_metrics.{clean_id}.field_count",
            min_value=0,
        )
        action_count = _require_int(
            entry.get("action_count"),
            path=f"structure.settings_category_metrics.{clean_id}.action_count",
            min_value=0,
        )
        mode_specific = _require_bool(
            entry.get("mode_specific"),
            path=f"structure.settings_category_metrics.{clean_id}.mode_specific",
        )
        top_level = _require_bool(
            entry.get("top_level"),
            path=f"structure.settings_category_metrics.{clean_id}.top_level",
        )
        metrics[clean_id] = {
            "field_count": field_count,
            "action_count": action_count,
            "mode_specific": mode_specific,
            "top_level": top_level,
        }
    return metrics


def _enforce_settings_split_policy(validated: dict[str, Any]) -> None:
    metrics = validated.get("settings_category_metrics", {})
    if not isinstance(metrics, dict) or not metrics:
        return
    rules = validated["settings_split_rules"]
    max_fields = int(rules["max_top_level_fields"])
    max_actions = int(rules["max_top_level_actions"])
    split_mode_specific = bool(rules["split_when_mode_specific"])

    docs = validated["settings_category_docs"]
    docs_by_id = {entry["id"]: entry for entry in docs}
    required_top_labels: list[str] = []
    for category_id, entry in metrics.items():
        if not bool(entry["top_level"]):
            continue
        field_count = int(entry["field_count"])
        action_count = int(entry["action_count"])
        mode_specific = bool(entry["mode_specific"])
        if field_count > max_fields:
            raise RuntimeError(
                f"settings split policy violation: {category_id} field_count={field_count} exceeds max_top_level_fields={max_fields}"
            )
        if action_count > max_actions:
            raise RuntimeError(
                f"settings split policy violation: {category_id} action_count={action_count} exceeds max_top_level_actions={max_actions}"
            )
        if split_mode_specific and mode_specific:
            raise RuntimeError(
                f"settings split policy violation: {category_id} is mode-specific and must not remain top-level"
            )
        required_top_labels.append(docs_by_id[category_id]["label"])

    rows = tuple(validated["settings_hub_rows"])
    row_set = set(rows)
    missing_labels = [label for label in required_top_labels if label not in row_set]
    if missing_labels:
        raise RuntimeError(
            f"settings_hub_rows missing top-level categories required by split policy: {', '.join(missing_labels)}"
        )
    layout_rows = tuple(validated["settings_hub_layout_rows"])
    layout_headers = tuple(
        row["label"] for row in layout_rows if row["kind"] == "header"
    )
    layout_header_set = set(layout_headers)
    missing_layout_headers = [
        label for label in required_top_labels if label not in layout_header_set
    ]
    if missing_layout_headers:
        raise RuntimeError(
            "settings_hub_layout_rows missing required top-level headers: "
            + ", ".join(missing_layout_headers)
        )


def _collect_reachable_menu_ids(
    menus: dict[str, dict[str, Any]],
    *,
    start_menu_id: str,
) -> set[str]:
    reachable: set[str] = set()
    queue = [start_menu_id]
    while queue:
        menu_id = queue.pop()
        if menu_id in reachable:
            continue
        menu = menus.get(menu_id)
        if menu is None:
            continue
        reachable.add(menu_id)
        for item in menu["items"]:
            if item["type"] == "submenu":
                queue.append(item["menu_id"])
    return reachable


def _collect_actions_for_menu_ids(
    menus: dict[str, dict[str, Any]],
    *,
    menu_ids: set[str],
) -> set[str]:
    actions: set[str] = set()
    for menu_id in menu_ids:
        menu = menus.get(menu_id)
        if menu is None:
            continue
        for item in menu["items"]:
            if item["type"] == "action":
                actions.add(item["action_id"])
    return actions


def _legacy_launcher_menu_from_graph(
    menus: dict[str, dict[str, Any]],
    *,
    launcher_menu_id: str,
) -> tuple[tuple[str, str], ...]:
    menu = menus.get(launcher_menu_id)
    if menu is None:
        return tuple()
    legacy: list[tuple[str, str]] = []
    for item in menu["items"]:
        item_type = item["type"]
        if item_type == "action":
            legacy.append((item["action_id"], item["label"]))
            continue
        if item_type == "submenu":
            legacy.append((item["menu_id"], item["label"]))
            continue
        legacy.append((item["route_id"], item["label"]))
    return tuple(legacy)


def _legacy_pause_views_from_graph(
    menus: dict[str, dict[str, Any]],
    *,
    pause_menu_id: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    menu = menus.get(pause_menu_id)
    if menu is None:
        return tuple(), tuple()
    rows: list[str] = []
    actions: list[str] = []
    for item in menu["items"]:
        rows.append(item["label"])
        actions.append(item["action_id"] if item["type"] == "action" else "")
    return tuple(rows), tuple(actions)


def _enforce_menu_entrypoint_parity(validated: dict[str, Any]) -> None:
    menus = validated["menus"]
    entrypoints = validated["menu_entrypoints"]
    launcher_reachable = _collect_reachable_menu_ids(
        menus,
        start_menu_id=entrypoints["launcher"],
    )
    pause_reachable = _collect_reachable_menu_ids(
        menus,
        start_menu_id=entrypoints["pause"],
    )
    launcher_actions = _collect_actions_for_menu_ids(menus, menu_ids=launcher_reachable)
    pause_actions = _collect_actions_for_menu_ids(menus, menu_ids=pause_reachable)
    required_actions = set(PARITY_ACTION_IDS)

    launcher_missing = sorted(required_actions - launcher_actions)
    pause_missing = sorted(required_actions - pause_actions)
    if launcher_missing:
        raise RuntimeError(
            "launcher entrypoint missing required parity actions: "
            + ", ".join(launcher_missing)
        )
    if pause_missing:
        raise RuntimeError(
            "pause entrypoint missing required parity actions: "
            + ", ".join(pause_missing)
        )


def _validate_structure_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw_launcher_menu = payload.get("launcher_menu")
    if raw_launcher_menu is None:
        launcher_menu_items: tuple[tuple[str, str], ...] = tuple()
    else:
        if not isinstance(raw_launcher_menu, list):
            raise RuntimeError("structure.launcher_menu must be a list")
        launcher_menu_items = tuple(
            _validate_menu_item(item) for item in raw_launcher_menu
        )
        if not launcher_menu_items:
            raise RuntimeError("structure.launcher_menu must not be empty")

    raw_pause_rows = payload.get("pause_menu_rows")
    if raw_pause_rows is None:
        pause_rows = tuple()
    else:
        pause_rows = _validate_row_list(raw_pause_rows, "pause_menu_rows")

    raw_pause_actions = payload.get("pause_menu_actions")
    if raw_pause_actions is None:
        pause_actions = tuple()
    else:
        pause_actions = _validate_action_list(raw_pause_actions, "pause_menu_actions")

    if pause_rows and pause_actions and len(pause_rows) != len(pause_actions):
        raise RuntimeError(
            "pause_menu_rows and pause_menu_actions must have equal length"
        )

    menus, entrypoints = _validate_or_build_menus(
        payload,
        launcher_menu=launcher_menu_items,
        pause_rows=pause_rows,
        pause_actions=pause_actions,
    )
    if not launcher_menu_items:
        launcher_menu_items = _legacy_launcher_menu_from_graph(
            menus,
            launcher_menu_id=entrypoints["launcher"],
        )
    if not pause_rows and not pause_actions:
        pause_rows, pause_actions = _legacy_pause_views_from_graph(
            menus,
            pause_menu_id=entrypoints["pause"],
        )
    settings_docs = _validate_settings_category_docs(payload)
    validated = {
        "launcher_menu": launcher_menu_items,
        "menus": menus,
        "menu_entrypoints": entrypoints,
        "settings_hub_rows": _validate_row_list(
            payload.get("settings_hub_rows"), "settings_hub_rows"
        ),
        "settings_hub_layout_rows": _validate_settings_hub_layout_rows(payload),
        "bot_options_rows": _validate_row_list(
            payload.get("bot_options_rows"), "bot_options_rows"
        ),
        "pause_menu_rows": pause_rows,
        "pause_menu_actions": pause_actions,
        "setup_fields": _validate_setup_fields(payload),
        "keybinding_category_docs": _validate_keybinding_category_docs(payload),
        "settings_category_docs": settings_docs,
        "settings_split_rules": _validate_settings_split_rules(payload),
        "settings_category_metrics": _validate_settings_category_metrics(
            payload, settings_docs
        ),
    }
    _enforce_settings_split_policy(validated)
    _enforce_menu_entrypoint_parity(validated)
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


def menu_graph() -> dict[str, dict[str, Any]]:
    menus = _structure_payload()["menus"]
    return deepcopy(menus)


def menu_entrypoints() -> dict[str, str]:
    entrypoints = _structure_payload()["menu_entrypoints"]
    return deepcopy(entrypoints)


def launcher_menu_id() -> str:
    return str(_structure_payload()["menu_entrypoints"]["launcher"])


def pause_menu_id() -> str:
    return str(_structure_payload()["menu_entrypoints"]["pause"])


def menu_definition(menu_id: str) -> dict[str, Any]:
    clean_menu_id = _as_non_empty_string(menu_id, path="menu_id").lower()
    menus = _structure_payload()["menus"]
    menu = menus.get(clean_menu_id)
    if menu is None:
        raise KeyError(f"Unknown menu id: {clean_menu_id}")
    return deepcopy(menu)


def menu_items(menu_id: str) -> tuple[dict[str, str], ...]:
    menu = menu_definition(menu_id)
    return tuple(menu["items"])


def reachable_action_ids(start_menu_id: str) -> tuple[str, ...]:
    clean_start = _as_non_empty_string(start_menu_id, path="start_menu_id").lower()
    payload = _structure_payload()
    menus: dict[str, dict[str, Any]] = payload["menus"]
    reachable_menus = _collect_reachable_menu_ids(menus, start_menu_id=clean_start)
    actions = _collect_actions_for_menu_ids(menus, menu_ids=reachable_menus)
    return tuple(sorted(actions))


def launcher_menu_items() -> tuple[tuple[str, str], ...]:
    return tuple(_structure_payload()["launcher_menu"])


def settings_hub_rows() -> tuple[str, ...]:
    return tuple(_structure_payload()["settings_hub_rows"])


def bot_options_rows() -> tuple[str, ...]:
    return tuple(_structure_payload()["bot_options_rows"])


def settings_hub_layout_rows() -> tuple[tuple[str, str, str], ...]:
    rows = _structure_payload()["settings_hub_layout_rows"]
    return tuple((row["kind"], row["label"], row["row_key"]) for row in rows)


def pause_menu_rows() -> tuple[str, ...]:
    return tuple(_structure_payload()["pause_menu_rows"])


def pause_menu_actions() -> tuple[str, ...]:
    return tuple(_structure_payload()["pause_menu_actions"])


def setup_fields_for_dimension(
    dimension: int,
    *,
    piece_set_max: int = 0,
    topology_profile_max: int = 0,
) -> list[FieldSpec]:
    mode_key = _mode_key_for_dimension(dimension)
    raw_fields = _structure_payload()["setup_fields"][mode_key]
    fields: list[FieldSpec] = []
    for raw_field in raw_fields:
        label = raw_field["label"]
        attr_name = raw_field["attr"]
        min_val = raw_field["min"]
        max_val = _resolve_field_max(
            raw_field["max"],
            piece_set_max,
            topology_profile_max,
            mode_key,
            attr_name,
        )
        if min_val > max_val:
            raise RuntimeError(
                f"Invalid field bounds for {mode_key}.{attr_name}: min {min_val} > max {max_val}"
            )
        fields.append((label, attr_name, min_val, max_val))
    return fields


def keybinding_category_docs() -> dict[str, Any]:
    docs = _structure_payload()["keybinding_category_docs"]
    return deepcopy(docs)


def settings_category_docs() -> tuple[dict[str, str], ...]:
    docs = _structure_payload()["settings_category_docs"]
    return deepcopy(docs)


def settings_split_rules() -> dict[str, Any]:
    rules = _structure_payload()["settings_split_rules"]
    return deepcopy(rules)


def settings_category_metrics() -> dict[str, dict[str, Any]]:
    metrics = _structure_payload()["settings_category_metrics"]
    return deepcopy(metrics)


def settings_top_level_categories() -> tuple[dict[str, str], ...]:
    payload = _structure_payload()
    docs: tuple[dict[str, str], ...] = payload["settings_category_docs"]
    metrics: dict[str, dict[str, Any]] = payload.get("settings_category_metrics", {})
    if not metrics:
        fallback_rows = set(payload["settings_hub_rows"])
        return tuple(entry for entry in docs if entry["label"] in fallback_rows)
    top_level_ids = {
        category_id
        for category_id, entry in metrics.items()
        if bool(entry.get("top_level"))
    }
    return tuple(entry for entry in docs if entry["id"] in top_level_ids)


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
