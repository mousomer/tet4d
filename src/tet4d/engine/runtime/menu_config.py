from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..ui_logic.menu_action_contracts import PARITY_ACTION_IDS
from .json_storage import read_json_object_or_raise
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


def _read_json_payload(path: Path) -> dict[str, Any]:
    payload = read_json_object_or_raise(path)
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _as_non_empty_string(value: object, *, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{path} must be a non-empty string")
    return value.strip()


def _require_object(value: object, *, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must be an object")
    return value


def _require_list(value: object, *, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise RuntimeError(f"{path} must be a list")
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


def _string_tuple(
    raw_values: object,
    *,
    path: str,
    normalize_lower: bool = False,
) -> tuple[str, ...]:
    values = _require_list(raw_values, path=path)
    out: list[str] = []
    for idx, raw in enumerate(values):
        value = _as_non_empty_string(raw, path=f"{path}[{idx}]")
        out.append(value.lower() if normalize_lower else value)
    if not out:
        raise RuntimeError(f"{path} must not be empty")
    return tuple(out)


def _mode_key_for_dimension(dimension: int) -> str:
    if dimension not in (2, 3, 4):
        raise ValueError("dimension must be one of: 2, 3, 4")
    return f"{dimension}d"


def _runtime_budget_for_mode(mode_key: str) -> int:
    ndims = {"2d": 2, "3d": 3, "4d": 4}[mode_key]
    return int(playbot_budget_table_for_ndim(ndims)[1])


def _sync_runtime_bot_budget(settings: dict[str, dict[str, int]]) -> None:
    for mode_key in _MODE_KEYS:
        mode_settings = settings.get(mode_key)
        if isinstance(mode_settings, dict):
            mode_settings["bot_budget_ms"] = _runtime_budget_for_mode(mode_key)


def _validate_defaults_payload(payload: dict[str, Any]) -> dict[str, Any]:
    required = {
        "version",
        "active_profile",
        "last_mode",
        "display",
        "audio",
        "analytics",
        "settings",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise RuntimeError("defaults config missing keys: " + ", ".join(missing))

    version = _require_int(payload["version"], path="defaults.version", min_value=1)
    active_profile = _as_non_empty_string(
        payload["active_profile"], path="defaults.active_profile"
    )
    last_mode = _as_non_empty_string(
        payload["last_mode"], path="defaults.last_mode"
    ).lower()
    if last_mode not in _MODE_KEYS:
        raise RuntimeError("defaults.last_mode must be one of: 2d, 3d, 4d")

    display = _require_object(payload["display"], path="defaults.display")
    fullscreen = _require_bool(
        display.get("fullscreen"), path="defaults.display.fullscreen"
    )
    windowed_size = _require_list(
        display.get("windowed_size"), path="defaults.display.windowed_size"
    )
    if len(windowed_size) != 2:
        raise RuntimeError("defaults.display.windowed_size must have length 2")
    width = _require_int(
        windowed_size[0], path="defaults.display.windowed_size[0]", min_value=1
    )
    height = _require_int(
        windowed_size[1], path="defaults.display.windowed_size[1]", min_value=1
    )
    overlay_transparency = _require_number(
        display.get("overlay_transparency"),
        path="defaults.display.overlay_transparency",
    )
    if not (0.0 <= overlay_transparency <= 0.85):
        raise RuntimeError(
            "defaults.display.overlay_transparency must be within [0.0, 0.85]"
        )

    audio = _require_object(payload["audio"], path="defaults.audio")
    master_volume = _require_number(
        audio.get("master_volume"), path="defaults.audio.master_volume"
    )
    sfx_volume = _require_number(
        audio.get("sfx_volume"), path="defaults.audio.sfx_volume"
    )
    mute = _require_bool(audio.get("mute"), path="defaults.audio.mute")

    analytics = _require_object(payload["analytics"], path="defaults.analytics")
    score_logging_enabled = _require_bool(
        analytics.get("score_logging_enabled"),
        path="defaults.analytics.score_logging_enabled",
    )

    settings_raw = _require_object(payload["settings"], path="defaults.settings")
    settings: dict[str, dict[str, int]] = {}
    for mode_key in _MODE_KEYS:
        mode_settings = _require_object(
            settings_raw.get(mode_key), path=f"defaults.settings.{mode_key}"
        )
        cleaned: dict[str, int] = {}
        for attr, value in mode_settings.items():
            cleaned[str(attr)] = _require_int(
                value,
                path=f"defaults.settings.{mode_key}.{attr}",
            )
        settings[mode_key] = cleaned

    _sync_runtime_bot_budget(settings)
    return {
        "version": version,
        "active_profile": active_profile,
        "last_mode": last_mode,
        "display": {
            "fullscreen": fullscreen,
            "windowed_size": [width, height],
            "overlay_transparency": overlay_transparency,
        },
        "audio": {
            "master_volume": master_volume,
            "sfx_volume": sfx_volume,
            "mute": mute,
        },
        "analytics": {
            "score_logging_enabled": score_logging_enabled,
        },
        "settings": settings,
    }


def _parse_launcher_menu(raw: object) -> tuple[tuple[str, str], ...]:
    items = _require_list(raw, path="structure.launcher_menu")
    out: list[tuple[str, str]] = []
    for idx, raw_item in enumerate(items):
        item = _require_object(raw_item, path=f"structure.launcher_menu[{idx}]")
        action = _as_non_empty_string(
            item.get("action"), path=f"structure.launcher_menu[{idx}].action"
        ).lower()
        label = _as_non_empty_string(
            item.get("label"), path=f"structure.launcher_menu[{idx}].label"
        )
        out.append((action, label))
    if not out:
        raise RuntimeError("structure.launcher_menu must not be empty")
    return tuple(out)


def _parse_menu_item(raw: object, *, path: str) -> dict[str, str]:
    item = _require_object(raw, path=path)
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
        return {"type": "action", "label": label, "action_id": action_id}
    if item_type == "submenu":
        menu_id = _as_non_empty_string(
            item.get("menu_id"), path=f"{path}.menu_id"
        ).lower()
        return {"type": "submenu", "label": label, "menu_id": menu_id}
    route_id = _as_non_empty_string(
        item.get("route_id"), path=f"{path}.route_id"
    ).lower()
    return {"type": "route", "label": label, "route_id": route_id}


def _parse_menus(raw: object) -> dict[str, dict[str, Any]]:
    menus_obj = _require_object(raw, path="structure.menus")
    if not menus_obj:
        raise RuntimeError("structure.menus must not be empty")

    menus: dict[str, dict[str, Any]] = {}
    for raw_menu_id, raw_menu in menus_obj.items():
        menu_id = _as_non_empty_string(raw_menu_id, path="structure.menus keys").lower()
        menu = _require_object(raw_menu, path=f"structure.menus.{menu_id}")
        title = _as_non_empty_string(
            menu.get("title"), path=f"structure.menus.{menu_id}.title"
        )
        raw_items = _require_list(
            menu.get("items"), path=f"structure.menus.{menu_id}.items"
        )
        if not raw_items:
            raise RuntimeError(f"structure.menus.{menu_id}.items must not be empty")
        items = tuple(
            _parse_menu_item(raw_item, path=f"structure.menus.{menu_id}.items[{idx}]")
            for idx, raw_item in enumerate(raw_items)
        )
        menus[menu_id] = {"title": title, "items": items}

    for menu_id, menu in menus.items():
        for idx, item in enumerate(menu["items"]):
            if item["type"] != "submenu":
                continue
            target = item["menu_id"]
            if target not in menus:
                raise RuntimeError(
                    f"structure.menus.{menu_id}.items[{idx}] references unknown submenu target: {target}"
                )
    return menus


def _parse_menu_entrypoints(
    payload: dict[str, Any], *, menus: dict[str, dict[str, Any]]
) -> dict[str, str]:
    raw = payload.get("menu_entrypoints")
    entrypoints = dict(_DEFAULT_MENU_ENTRYPOINTS)
    if raw is not None:
        entry_obj = _require_object(raw, path="structure.menu_entrypoints")
        for key in _MENU_ENTRYPOINT_KEYS:
            if key in entry_obj:
                entrypoints[key] = _as_non_empty_string(
                    entry_obj[key], path=f"structure.menu_entrypoints.{key}"
                ).lower()
    for key, menu_id in entrypoints.items():
        if menu_id not in menus:
            raise RuntimeError(
                f"structure.menu_entrypoints.{key} references unknown menu id: {menu_id}"
            )
    return entrypoints


def _parse_settings_hub_layout_rows(raw: object) -> tuple[dict[str, str], ...]:
    rows = _require_list(raw, path="structure.settings_hub_layout_rows")
    if not rows:
        raise RuntimeError("structure.settings_hub_layout_rows must not be empty")

    parsed: list[dict[str, str]] = []
    item_rows = 0
    for idx, raw_row in enumerate(rows):
        row = _require_object(
            raw_row, path=f"structure.settings_hub_layout_rows[{idx}]"
        )
        kind = _as_non_empty_string(
            row.get("kind"), path=f"structure.settings_hub_layout_rows[{idx}].kind"
        )
        if kind not in _SETTINGS_HUB_LAYOUT_KINDS:
            raise RuntimeError(
                "structure.settings_hub_layout_rows kind must be one of: "
                + ", ".join(sorted(_SETTINGS_HUB_LAYOUT_KINDS))
            )
        label = _as_non_empty_string(
            row.get("label"), path=f"structure.settings_hub_layout_rows[{idx}].label"
        )
        if kind == "header":
            parsed.append({"kind": "header", "label": label, "row_key": ""})
            continue
        row_key = _as_non_empty_string(
            row.get("row_key"),
            path=f"structure.settings_hub_layout_rows[{idx}].row_key",
        ).lower()
        parsed.append({"kind": "item", "label": label, "row_key": row_key})
        item_rows += 1

    if item_rows == 0:
        raise RuntimeError(
            "structure.settings_hub_layout_rows must include at least one item row"
        )
    return tuple(parsed)


def _parse_setup_fields(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    raw_setup = _require_object(
        payload.get("setup_fields"), path="structure.setup_fields"
    )
    setup_fields: dict[str, list[dict[str, Any]]] = {}
    for mode_key in _MODE_KEYS:
        raw_fields = _require_list(
            raw_setup.get(mode_key), path=f"structure.setup_fields.{mode_key}"
        )
        if not raw_fields:
            raise RuntimeError(f"structure.setup_fields.{mode_key} must not be empty")
        fields: list[dict[str, Any]] = []
        for idx, raw_field in enumerate(raw_fields):
            field = _require_object(
                raw_field, path=f"structure.setup_fields.{mode_key}[{idx}]"
            )
            label = _as_non_empty_string(
                field.get("label"),
                path=f"structure.setup_fields.{mode_key}[{idx}].label",
            )
            attr = _as_non_empty_string(
                field.get("attr"), path=f"structure.setup_fields.{mode_key}[{idx}].attr"
            )
            min_val = _require_int(
                field.get("min"), path=f"structure.setup_fields.{mode_key}[{idx}].min"
            )
            raw_max = field.get("max")
            if isinstance(raw_max, bool) or not isinstance(raw_max, (int, str)):
                raise RuntimeError(
                    f"structure.setup_fields.{mode_key}[{idx}].max must be int or dynamic token"
                )
            fields.append(
                {
                    "label": label,
                    "attr": attr,
                    "min": min_val,
                    "max": raw_max,
                }
            )
        setup_fields[mode_key] = fields
    return setup_fields


def _parse_keybinding_category_docs(payload: dict[str, Any]) -> dict[str, Any]:
    raw_docs = payload.get("keybinding_category_docs")
    if raw_docs is None:
        return {"scope_order": ("all", "2d", "3d", "4d"), "groups": {}}

    docs = _require_object(raw_docs, path="structure.keybinding_category_docs")
    groups_raw = _require_object(
        docs.get("groups"), path="structure.keybinding_category_docs.groups"
    )
    groups: dict[str, dict[str, str]] = {}
    for raw_group_name, raw_group in groups_raw.items():
        group_name = _as_non_empty_string(
            raw_group_name,
            path="structure.keybinding_category_docs.groups keys",
        ).lower()
        group_obj = _require_object(
            raw_group,
            path=f"structure.keybinding_category_docs.groups.{group_name}",
        )
        groups[group_name] = {
            "label": _as_non_empty_string(
                group_obj.get("label"),
                path=f"structure.keybinding_category_docs.groups.{group_name}.label",
            ),
            "description": _as_non_empty_string(
                group_obj.get("description"),
                path=f"structure.keybinding_category_docs.groups.{group_name}.description",
            ),
        }
    return {
        "scope_order": _string_tuple(
            docs.get("scope_order"),
            path="structure.keybinding_category_docs.scope_order",
            normalize_lower=True,
        ),
        "groups": groups,
    }


def _parse_settings_category_docs(
    payload: dict[str, Any],
) -> tuple[dict[str, str], ...]:
    raw = payload.get("settings_category_docs")
    if raw is None:
        return tuple()
    rows = _require_list(raw, path="structure.settings_category_docs")
    docs: list[dict[str, str]] = []
    for idx, raw_doc in enumerate(rows):
        doc = _require_object(raw_doc, path=f"structure.settings_category_docs[{idx}]")
        docs.append(
            {
                "id": _as_non_empty_string(
                    doc.get("id"), path=f"structure.settings_category_docs[{idx}].id"
                ).lower(),
                "label": _as_non_empty_string(
                    doc.get("label"),
                    path=f"structure.settings_category_docs[{idx}].label",
                ),
                "description": _as_non_empty_string(
                    doc.get("description"),
                    path=f"structure.settings_category_docs[{idx}].description",
                ),
            }
        )
    return tuple(docs)


def _parse_settings_split_rules(payload: dict[str, Any]) -> dict[str, Any]:
    raw_rules = payload.get("settings_split_rules")
    if raw_rules is None:
        return {
            "max_top_level_fields": 5,
            "max_top_level_actions": 2,
            "split_when_mode_specific": True,
        }

    rules = _require_object(raw_rules, path="structure.settings_split_rules")
    return {
        "max_top_level_fields": _require_int(
            rules.get("max_top_level_fields"),
            path="structure.settings_split_rules.max_top_level_fields",
            min_value=1,
        ),
        "max_top_level_actions": _require_int(
            rules.get("max_top_level_actions"),
            path="structure.settings_split_rules.max_top_level_actions",
            min_value=1,
        ),
        "split_when_mode_specific": _require_bool(
            rules.get("split_when_mode_specific"),
            path="structure.settings_split_rules.split_when_mode_specific",
        ),
    }


def _parse_settings_category_metrics(
    payload: dict[str, Any], docs: tuple[dict[str, str], ...]
) -> dict[str, dict[str, Any]]:
    raw_metrics = payload.get("settings_category_metrics")
    if not isinstance(raw_metrics, dict):
        return {}

    doc_ids = {entry["id"] for entry in docs}
    metrics: dict[str, dict[str, Any]] = {}
    for raw_category_id, raw_entry in raw_metrics.items():
        category_id = _as_non_empty_string(
            raw_category_id, path="structure.settings_category_metrics keys"
        ).lower()
        if category_id not in doc_ids:
            raise RuntimeError(
                f"structure.settings_category_metrics.{category_id} has no matching settings_category_docs id"
            )
        entry = _require_object(
            raw_entry,
            path=f"structure.settings_category_metrics.{category_id}",
        )
        metrics[category_id] = {
            "field_count": _require_int(
                entry.get("field_count"),
                path=f"structure.settings_category_metrics.{category_id}.field_count",
                min_value=0,
            ),
            "action_count": _require_int(
                entry.get("action_count"),
                path=f"structure.settings_category_metrics.{category_id}.action_count",
                min_value=0,
            ),
            "mode_specific": _require_bool(
                entry.get("mode_specific"),
                path=f"structure.settings_category_metrics.{category_id}.mode_specific",
            ),
            "top_level": _require_bool(
                entry.get("top_level"),
                path=f"structure.settings_category_metrics.{category_id}.top_level",
            ),
        }
    return metrics


def _collect_reachable_menu_ids(
    menus: dict[str, dict[str, Any]], *, start_menu_id: str
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
    menus: dict[str, dict[str, Any]], *, menu_ids: set[str]
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


def _enforce_menu_entrypoint_parity(validated: dict[str, Any]) -> None:
    menus: dict[str, dict[str, Any]] = validated["menus"]
    entrypoints: dict[str, str] = validated["menu_entrypoints"]
    launcher_actions = _collect_actions_for_menu_ids(
        menus,
        menu_ids=_collect_reachable_menu_ids(
            menus, start_menu_id=entrypoints["launcher"]
        ),
    )
    pause_actions = _collect_actions_for_menu_ids(
        menus,
        menu_ids=_collect_reachable_menu_ids(menus, start_menu_id=entrypoints["pause"]),
    )
    required = set(PARITY_ACTION_IDS)
    launcher_missing = sorted(required - launcher_actions)
    pause_missing = sorted(required - pause_actions)
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


def _enforce_settings_split_policy(validated: dict[str, Any]) -> None:
    metrics: dict[str, dict[str, Any]] = validated["settings_category_metrics"]
    if not metrics:
        return

    rules = validated["settings_split_rules"]
    max_fields = int(rules["max_top_level_fields"])
    max_actions = int(rules["max_top_level_actions"])
    split_mode_specific = bool(rules["split_when_mode_specific"])
    docs = {entry["id"]: entry for entry in validated["settings_category_docs"]}

    required_top_labels: list[str] = []
    for category_id, entry in metrics.items():
        if not bool(entry.get("top_level")):
            continue
        if int(entry.get("field_count", 0)) > max_fields:
            raise RuntimeError(
                f"settings split policy violation: {category_id} exceeds max_top_level_fields"
            )
        if int(entry.get("action_count", 0)) > max_actions:
            raise RuntimeError(
                f"settings split policy violation: {category_id} exceeds max_top_level_actions"
            )
        if split_mode_specific and bool(entry.get("mode_specific")):
            raise RuntimeError(
                f"settings split policy violation: {category_id} is mode-specific and must not remain top-level"
            )
        required_top_labels.append(docs[category_id]["label"])

    hub_rows = set(validated["settings_hub_rows"])
    missing_rows = [label for label in required_top_labels if label not in hub_rows]
    if missing_rows:
        raise RuntimeError(
            "settings_hub_rows missing top-level categories required by split policy: "
            + ", ".join(missing_rows)
        )

    layout_headers = {
        row["label"]
        for row in validated["settings_hub_layout_rows"]
        if row["kind"] == "header"
    }
    missing_headers = [
        label for label in required_top_labels if label not in layout_headers
    ]
    if missing_headers:
        raise RuntimeError(
            "settings_hub_layout_rows missing required top-level headers: "
            + ", ".join(missing_headers)
        )


def _validate_structure_payload(payload: dict[str, Any]) -> dict[str, Any]:
    launcher_menu = _parse_launcher_menu(payload.get("launcher_menu"))
    menus = _parse_menus(payload.get("menus"))
    entrypoints = _parse_menu_entrypoints(payload, menus=menus)

    pause_rows = _string_tuple(
        payload.get("pause_menu_rows"), path="structure.pause_menu_rows"
    )
    pause_actions = _string_tuple(
        payload.get("pause_menu_actions"),
        path="structure.pause_menu_actions",
        normalize_lower=True,
    )
    if len(pause_rows) != len(pause_actions):
        raise RuntimeError(
            "pause_menu_rows and pause_menu_actions must have equal length"
        )

    settings_docs = _parse_settings_category_docs(payload)
    validated = {
        "launcher_menu": launcher_menu,
        "menus": menus,
        "menu_entrypoints": entrypoints,
        "settings_hub_rows": _string_tuple(
            payload.get("settings_hub_rows"), path="structure.settings_hub_rows"
        ),
        "settings_hub_layout_rows": _parse_settings_hub_layout_rows(
            payload.get("settings_hub_layout_rows")
        ),
        "bot_options_rows": _string_tuple(
            payload.get("bot_options_rows"), path="structure.bot_options_rows"
        ),
        "pause_menu_rows": pause_rows,
        "pause_menu_actions": pause_actions,
        "setup_fields": _parse_setup_fields(payload),
        "keybinding_category_docs": _parse_keybinding_category_docs(payload),
        "settings_category_docs": settings_docs,
        "settings_split_rules": _parse_settings_split_rules(payload),
        "settings_category_metrics": _parse_settings_category_metrics(
            payload, settings_docs
        ),
    }
    _enforce_settings_split_policy(validated)
    _enforce_menu_entrypoint_parity(validated)
    return validated


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


@lru_cache(maxsize=1)
def _defaults_payload() -> dict[str, Any]:
    return _validate_defaults_payload(_read_json_payload(DEFAULTS_FILE))


@lru_cache(maxsize=1)
def _structure_payload() -> dict[str, Any]:
    return _validate_structure_payload(_read_json_payload(STRUCTURE_FILE))


def default_settings_payload() -> dict[str, Any]:
    return deepcopy(_defaults_payload())


def menu_graph() -> dict[str, dict[str, Any]]:
    return deepcopy(_structure_payload()["menus"])


def menu_entrypoints() -> dict[str, str]:
    return deepcopy(_structure_payload()["menu_entrypoints"])


def launcher_menu_id() -> str:
    return str(_structure_payload()["menu_entrypoints"]["launcher"])


def pause_menu_id() -> str:
    return str(_structure_payload()["menu_entrypoints"]["pause"])


def menu_definition(menu_id: str) -> dict[str, Any]:
    clean_menu_id = _as_non_empty_string(menu_id, path="menu_id").lower()
    menu = _structure_payload()["menus"].get(clean_menu_id)
    if menu is None:
        raise KeyError(f"Unknown menu id: {clean_menu_id}")
    return deepcopy(menu)


def menu_items(menu_id: str) -> tuple[dict[str, str], ...]:
    return tuple(menu_definition(menu_id)["items"])


def reachable_action_ids(start_menu_id: str) -> tuple[str, ...]:
    clean_start = _as_non_empty_string(start_menu_id, path="start_menu_id").lower()
    payload = _structure_payload()
    reachable_menus = _collect_reachable_menu_ids(
        payload["menus"], start_menu_id=clean_start
    )
    actions = _collect_actions_for_menu_ids(payload["menus"], menu_ids=reachable_menus)
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
    return deepcopy(_structure_payload()["keybinding_category_docs"])


def settings_category_docs() -> tuple[dict[str, str], ...]:
    return deepcopy(_structure_payload()["settings_category_docs"])


def settings_split_rules() -> dict[str, Any]:
    return deepcopy(_structure_payload()["settings_split_rules"])


def settings_category_metrics() -> dict[str, dict[str, Any]]:
    return deepcopy(_structure_payload()["settings_category_metrics"])


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
