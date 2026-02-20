from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from .runtime_config import playbot_budget_table_for_ndim

FieldSpec = tuple[str, str, int, int]

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config" / "menu"
DEFAULTS_FILE = CONFIG_DIR / "defaults.json"
STRUCTURE_FILE = CONFIG_DIR / "structure.json"
_MODE_KEYS = ("2d", "3d", "4d")
_PARITY_ENTRY_ACTIONS = ("settings", "keybindings", "help", "bot_options", "quit")
_SETTINGS_HUB_LAYOUT_KINDS = {"header", "item"}


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

    version = payload["version"]
    if isinstance(version, bool) or not isinstance(version, int) or version <= 0:
        raise RuntimeError("defaults.version must be a positive integer")

    active_profile = payload["active_profile"]
    if not isinstance(active_profile, str) or not active_profile.strip():
        raise RuntimeError("defaults.active_profile must be a non-empty string")

    last_mode = payload["last_mode"]
    if last_mode not in _MODE_KEYS:
        raise RuntimeError("defaults.last_mode must be one of: 2d, 3d, 4d")
    return version, active_profile, last_mode


def _validate_defaults_display(payload: dict[str, Any]) -> dict[str, Any]:
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
    return display


def _validate_defaults_audio(payload: dict[str, Any]) -> dict[str, Any]:
    audio = payload["audio"]
    if not isinstance(audio, dict):
        raise RuntimeError("defaults.audio must be an object")
    for key in ("master_volume", "sfx_volume"):
        value = audio.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RuntimeError(f"defaults.audio.{key} must be a number")
    if not isinstance(audio.get("mute"), bool):
        raise RuntimeError("defaults.audio.mute must be a boolean")
    return audio


def _validate_defaults_analytics(payload: dict[str, Any]) -> dict[str, Any]:
    analytics = payload["analytics"]
    if not isinstance(analytics, dict):
        raise RuntimeError("defaults.analytics must be an object")
    if not isinstance(analytics.get("score_logging_enabled"), bool):
        raise RuntimeError("defaults.analytics.score_logging_enabled must be a boolean")
    return analytics


def _validate_defaults_settings(payload: dict[str, Any]) -> dict[str, dict[str, int]]:
    settings = payload["settings"]
    if not isinstance(settings, dict):
        raise RuntimeError("defaults.settings must be an object")
    validated_settings: dict[str, dict[str, int]] = {}
    for mode_key in _MODE_KEYS:
        if mode_key not in settings:
            raise RuntimeError(f"defaults.settings missing mode key: {mode_key}")
        validated_settings[mode_key] = _validate_mode_settings(mode_key, settings[mode_key])
    return validated_settings


def _runtime_budget_for_mode(mode_key: str) -> int:
    if mode_key == "2d":
        budget = playbot_budget_table_for_ndim(2)[1]
    elif mode_key == "3d":
        budget = playbot_budget_table_for_ndim(3)[1]
    else:
        budget = playbot_budget_table_for_ndim(4)[1]
    return int(budget)


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


def _validate_action_list(raw_actions: object, key: str) -> tuple[str, ...]:
    if not isinstance(raw_actions, list):
        raise RuntimeError(f"structure.{key} must be a list")
    actions: list[str] = []
    seen: set[str] = set()
    for idx, raw_action in enumerate(raw_actions):
        if not isinstance(raw_action, str) or not raw_action.strip():
            raise RuntimeError(f"structure.{key}[{idx}] must be a non-empty string")
        action = raw_action.strip().lower()
        if action in seen:
            raise RuntimeError(f"structure.{key} contains duplicate action: {action}")
        seen.add(action)
        actions.append(action)
    if not actions:
        raise RuntimeError(f"structure.{key} must not be empty")
    return tuple(actions)


def _validate_settings_hub_layout_row(raw_row: object, *, idx: int) -> tuple[dict[str, str], bool]:
    if not isinstance(raw_row, dict):
        raise RuntimeError(f"structure.settings_hub_layout_rows[{idx}] must be an object")
    kind = raw_row.get("kind")
    label = raw_row.get("label")
    row_key = raw_row.get("row_key", "")
    if not isinstance(kind, str) or kind not in _SETTINGS_HUB_LAYOUT_KINDS:
        raise RuntimeError(
            f"structure.settings_hub_layout_rows[{idx}].kind must be one of: "
            + ", ".join(sorted(_SETTINGS_HUB_LAYOUT_KINDS))
        )
    if not isinstance(label, str) or not label.strip():
        raise RuntimeError(f"structure.settings_hub_layout_rows[{idx}].label must be a non-empty string")
    if kind == "header":
        if row_key not in ("", None):
            raise RuntimeError(
                f"structure.settings_hub_layout_rows[{idx}].row_key must be empty for header rows"
            )
        return {"kind": "header", "label": label.strip(), "row_key": ""}, False
    if not isinstance(row_key, str) or not row_key.strip():
        raise RuntimeError(
            f"structure.settings_hub_layout_rows[{idx}].row_key must be a non-empty string for item rows"
        )
    return {"kind": "item", "label": label.strip(), "row_key": row_key.strip().lower()}, True


def _validate_settings_hub_layout_rows(payload: dict[str, Any]) -> tuple[dict[str, str], ...]:
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
        raise RuntimeError("structure.settings_hub_layout_rows must include at least one item row")
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


def _validate_setup_field(raw_field: object, *, mode_key: str, idx: int) -> dict[str, Any]:
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


def _as_non_empty_string(value: object, *, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{path} must be a non-empty string")
    return value.strip()


def _validate_scope_order(raw_docs: dict[str, Any]) -> tuple[str, ...]:
    raw_scope_order = raw_docs.get("scope_order")
    if not isinstance(raw_scope_order, list) or not raw_scope_order:
        raise RuntimeError("structure.keybinding_category_docs.scope_order must be a non-empty list")
    scope_order = [
        _as_non_empty_string(scope, path=f"structure.keybinding_category_docs.scope_order[{idx}]").lower()
        for idx, scope in enumerate(raw_scope_order)
    ]
    return tuple(scope_order)


def _validate_group_doc(group_name: str, raw_group: object) -> tuple[str, dict[str, str]]:
    clean_name = _as_non_empty_string(
        group_name,
        path="structure.keybinding_category_docs.groups keys",
    ).lower()
    if not isinstance(raw_group, dict):
        raise RuntimeError(f"structure.keybinding_category_docs.groups.{group_name} must be an object")
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
        raise RuntimeError("structure.keybinding_category_docs.groups must be an object")
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


def _validate_settings_category_docs(payload: dict[str, Any]) -> tuple[dict[str, str], ...]:
    raw_docs = payload.get("settings_category_docs")
    if raw_docs is None:
        return tuple()
    if not isinstance(raw_docs, list):
        raise RuntimeError("structure.settings_category_docs must be a list")

    docs: list[dict[str, str]] = []
    for idx, raw_item in enumerate(raw_docs):
        if not isinstance(raw_item, dict):
            raise RuntimeError(f"structure.settings_category_docs[{idx}] must be an object")
        item_id = raw_item.get("id")
        label = raw_item.get("label")
        description = raw_item.get("description")
        if not isinstance(item_id, str) or not item_id.strip():
            raise RuntimeError(f"structure.settings_category_docs[{idx}].id must be a non-empty string")
        if not isinstance(label, str) or not label.strip():
            raise RuntimeError(f"structure.settings_category_docs[{idx}].label must be a non-empty string")
        if not isinstance(description, str) or not description.strip():
            raise RuntimeError(
                f"structure.settings_category_docs[{idx}].description must be a non-empty string"
            )
        docs.append(
            {
                "id": item_id.strip().lower(),
                "label": label.strip(),
                "description": description.strip(),
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
    if not isinstance(raw, dict):
        raise RuntimeError("structure.settings_split_rules must be an object")
    max_fields = raw.get("max_top_level_fields")
    max_actions = raw.get("max_top_level_actions")
    split_mode_specific = raw.get("split_when_mode_specific")
    if isinstance(max_fields, bool) or not isinstance(max_fields, int) or max_fields < 1:
        raise RuntimeError("structure.settings_split_rules.max_top_level_fields must be int >= 1")
    if isinstance(max_actions, bool) or not isinstance(max_actions, int) or max_actions < 1:
        raise RuntimeError("structure.settings_split_rules.max_top_level_actions must be int >= 1")
    if not isinstance(split_mode_specific, bool):
        raise RuntimeError("structure.settings_split_rules.split_when_mode_specific must be boolean")
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
            raise RuntimeError("structure.settings_category_metrics keys must be non-empty strings")
        clean_id = category_id.strip().lower()
        if clean_id not in docs_by_id:
            raise RuntimeError(
                f"structure.settings_category_metrics.{clean_id} has no matching settings_category_docs id"
            )
        if not isinstance(raw_entry, dict):
            raise RuntimeError(f"structure.settings_category_metrics.{clean_id} must be an object")

        field_count = raw_entry.get("field_count")
        action_count = raw_entry.get("action_count")
        mode_specific = raw_entry.get("mode_specific")
        top_level = raw_entry.get("top_level")
        if isinstance(field_count, bool) or not isinstance(field_count, int) or field_count < 0:
            raise RuntimeError(
                f"structure.settings_category_metrics.{clean_id}.field_count must be int >= 0"
            )
        if isinstance(action_count, bool) or not isinstance(action_count, int) or action_count < 0:
            raise RuntimeError(
                f"structure.settings_category_metrics.{clean_id}.action_count must be int >= 0"
            )
        if not isinstance(mode_specific, bool):
            raise RuntimeError(
                f"structure.settings_category_metrics.{clean_id}.mode_specific must be boolean"
            )
        if not isinstance(top_level, bool):
            raise RuntimeError(
                f"structure.settings_category_metrics.{clean_id}.top_level must be boolean"
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
    layout_headers = tuple(row["label"] for row in layout_rows if row["kind"] == "header")
    layout_header_set = set(layout_headers)
    missing_layout_headers = [label for label in required_top_labels if label not in layout_header_set]
    if missing_layout_headers:
        raise RuntimeError(
            "settings_hub_layout_rows missing required top-level headers: "
            + ", ".join(missing_layout_headers)
        )


def _enforce_menu_entrypoint_parity(validated: dict[str, Any]) -> None:
    launcher_actions = {action for action, _label in validated["launcher_menu"]}
    pause_actions = set(validated["pause_menu_actions"])
    required_actions = set(_PARITY_ENTRY_ACTIONS)

    launcher_missing = sorted(required_actions - launcher_actions)
    pause_missing = sorted(required_actions - pause_actions)
    if launcher_missing:
        raise RuntimeError(
            "launcher_menu missing required parity actions: " + ", ".join(launcher_missing)
        )
    if pause_missing:
        raise RuntimeError(
            "pause_menu_actions missing required parity actions: " + ", ".join(pause_missing)
        )


def _validate_structure_payload(payload: dict[str, Any]) -> dict[str, Any]:
    launcher_menu = payload.get("launcher_menu")
    if not isinstance(launcher_menu, list):
        raise RuntimeError("structure.launcher_menu must be a list")
    menu_items = tuple(_validate_menu_item(item) for item in launcher_menu)
    if not menu_items:
        raise RuntimeError("structure.launcher_menu must not be empty")
    settings_docs = _validate_settings_category_docs(payload)
    validated = {
        "launcher_menu": menu_items,
        "settings_hub_rows": _validate_row_list(payload.get("settings_hub_rows"), "settings_hub_rows"),
        "settings_hub_layout_rows": _validate_settings_hub_layout_rows(payload),
        "bot_options_rows": _validate_row_list(payload.get("bot_options_rows"), "bot_options_rows"),
        "pause_menu_rows": _validate_row_list(payload.get("pause_menu_rows"), "pause_menu_rows"),
        "pause_menu_actions": _validate_action_list(payload.get("pause_menu_actions"), "pause_menu_actions"),
        "setup_fields": _validate_setup_fields(payload),
        "keybinding_category_docs": _validate_keybinding_category_docs(payload),
        "settings_category_docs": settings_docs,
        "settings_split_rules": _validate_settings_split_rules(payload),
        "settings_category_metrics": _validate_settings_category_metrics(payload, settings_docs),
    }
    if len(validated["pause_menu_rows"]) != len(validated["pause_menu_actions"]):
        raise RuntimeError("pause_menu_rows and pause_menu_actions must have equal length")
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
