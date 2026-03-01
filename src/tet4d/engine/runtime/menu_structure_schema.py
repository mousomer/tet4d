from __future__ import annotations

from typing import Any

from ..ui_logic.menu_action_contracts import PARITY_ACTION_IDS
from .settings_schema import (
    MODE_KEYS,
    as_non_empty_string,
    require_bool,
    require_int,
    require_list,
    require_object,
    string_tuple,
)

_SETTINGS_HUB_LAYOUT_KINDS = {"header", "item"}
_MENU_ITEM_TYPES = {"action", "submenu", "route"}
_MENU_ENTRYPOINT_KEYS = ("launcher", "pause")
_DEFAULT_MENU_ENTRYPOINTS = {
    "launcher": "launcher_root",
    "pause": "pause_root",
}
_UI_COPY_SECTION_SPECS: dict[str, dict[str, tuple[str, ...]]] = {
    "launcher": {
        "string_fields": (
            "info_active_profile_template",
            "info_continue_mode_template",
            "controls_hint_template",
            "escape_hint_back",
            "escape_hint_quit",
        ),
    },
    "settings_hub": {
        "string_fields": (
            "title",
            "subtitle_categories_template",
            "reset_confirm_f8",
        ),
        "list_fields": ("hints",),
    },
    "keybindings_menu": {
        "string_fields": (
            "title",
            "subtitle_section_mode",
            "subtitle_binding_mode",
            "capture_template",
            "text_mode_confirm_hint",
        ),
        "list_fields": ("hints", "section_hints"),
    },
    "bot_options": {
        "string_fields": (
            "title",
            "subtitle",
            "saved_status",
            "reset_confirm_enter",
            "reset_confirm_f8",
            "reset_done_template",
        ),
        "list_fields": ("hints",),
    },
    "setup_menu": {
        "string_fields": (
            "title_template",
            "subtitle_template",
            "title_2d",
            "subtitle_2d",
            "bindings_hint_template",
            "compact_controls_hint",
        ),
    },
}


def parse_menu_item(raw: object, *, path: str) -> dict[str, str]:
    item = require_object(raw, path=path)
    item_type = as_non_empty_string(item.get("type"), path=f"{path}.type").lower()
    label = as_non_empty_string(item.get("label"), path=f"{path}.label")
    if item_type not in _MENU_ITEM_TYPES:
        raise RuntimeError(
            f"{path}.type must be one of: " + ", ".join(sorted(_MENU_ITEM_TYPES))
        )
    if item_type == "action":
        action_id = as_non_empty_string(
            item.get("action_id"),
            path=f"{path}.action_id",
        ).lower()
        return {"type": "action", "label": label, "action_id": action_id}
    if item_type == "submenu":
        menu_id = as_non_empty_string(
            item.get("menu_id"), path=f"{path}.menu_id"
        ).lower()
        return {"type": "submenu", "label": label, "menu_id": menu_id}
    route_id = as_non_empty_string(
        item.get("route_id"), path=f"{path}.route_id"
    ).lower()
    return {"type": "route", "label": label, "route_id": route_id}


def parse_menus(raw: object) -> dict[str, dict[str, Any]]:
    menus_obj = require_object(raw, path="structure.menus")
    if not menus_obj:
        raise RuntimeError("structure.menus must not be empty")

    menus: dict[str, dict[str, Any]] = {}
    for raw_menu_id, raw_menu in menus_obj.items():
        menu_id = as_non_empty_string(raw_menu_id, path="structure.menus keys").lower()
        menu = require_object(raw_menu, path=f"structure.menus.{menu_id}")
        title = as_non_empty_string(
            menu.get("title"),
            path=f"structure.menus.{menu_id}.title",
        )
        raw_items = require_list(
            menu.get("items"),
            path=f"structure.menus.{menu_id}.items",
        )
        if not raw_items:
            raise RuntimeError(f"structure.menus.{menu_id}.items must not be empty")
        items = tuple(
            parse_menu_item(
                raw_item,
                path=f"structure.menus.{menu_id}.items[{idx}]",
            )
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


def parse_menu_entrypoints(
    payload: dict[str, Any],
    *,
    menus: dict[str, dict[str, Any]],
) -> dict[str, str]:
    raw = payload.get("menu_entrypoints")
    entrypoints = dict(_DEFAULT_MENU_ENTRYPOINTS)
    if raw is not None:
        entry_obj = require_object(raw, path="structure.menu_entrypoints")
        for key in _MENU_ENTRYPOINT_KEYS:
            if key in entry_obj:
                entrypoints[key] = as_non_empty_string(
                    entry_obj[key],
                    path=f"structure.menu_entrypoints.{key}",
                ).lower()
    for key, menu_id in entrypoints.items():
        if menu_id not in menus:
            raise RuntimeError(
                f"structure.menu_entrypoints.{key} references unknown menu id: {menu_id}"
            )
    return entrypoints


def parse_launcher_subtitles(payload: dict[str, Any]) -> dict[str, str]:
    raw = require_object(
        payload.get("launcher_subtitles"), path="structure.launcher_subtitles"
    )
    return _parse_copy_fields(
        raw,
        base_path="structure.launcher_subtitles",
        string_fields=("launcher_root", "launcher_play", "default"),
    )


def parse_launcher_route_actions(payload: dict[str, Any]) -> dict[str, str]:
    raw = require_object(
        payload.get("launcher_route_actions"),
        path="structure.launcher_route_actions",
    )
    route_actions: dict[str, str] = {}
    for raw_route_id, raw_action_id in raw.items():
        route_id = as_non_empty_string(
            raw_route_id,
            path="structure.launcher_route_actions keys",
        ).lower()
        action_id = as_non_empty_string(
            raw_action_id,
            path=f"structure.launcher_route_actions.{route_id}",
        ).lower()
        route_actions[route_id] = action_id
    if not route_actions:
        raise RuntimeError("structure.launcher_route_actions must not be empty")
    return route_actions


def parse_branding(payload: dict[str, Any]) -> dict[str, str]:
    raw = require_object(payload.get("branding"), path="structure.branding")
    return _parse_copy_fields(
        raw,
        base_path="structure.branding",
        string_fields=("game_title", "signature_author", "signature_message"),
    )


def _parse_string_list(raw: object, *, path: str) -> tuple[str, ...]:
    values = require_list(raw, path=path)
    if not values:
        raise RuntimeError(f"{path} must not be empty")
    return tuple(
        as_non_empty_string(value, path=f"{path}[{idx}]")
        for idx, value in enumerate(values)
    )


def _parse_mode_string_lists(
    raw_obj: dict[str, Any],
    *,
    base_path: str,
) -> dict[str, tuple[str, ...]]:
    parsed: dict[str, tuple[str, ...]] = {}
    for mode_key in MODE_KEYS:
        parsed[mode_key] = _parse_string_list(
            raw_obj.get(mode_key),
            path=f"{base_path}.{mode_key}",
        )
    return parsed


def _parse_copy_fields(
    raw: dict[str, Any],
    *,
    base_path: str,
    string_fields: tuple[str, ...],
    list_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for field in string_fields:
        parsed[field] = as_non_empty_string(
            raw.get(field),
            path=f"{base_path}.{field}",
        )
    for field in list_fields:
        parsed[field] = _parse_string_list(
            raw.get(field),
            path=f"{base_path}.{field}",
        )
    return parsed


def _parse_ui_copy_section(
    raw_ui_copy: dict[str, Any],
    *,
    section: str,
    string_fields: tuple[str, ...],
    list_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    section_path = f"structure.ui_copy.{section}"
    raw_section = require_object(raw_ui_copy.get(section), path=section_path)
    return _parse_copy_fields(
        raw_section,
        base_path=section_path,
        string_fields=string_fields,
        list_fields=list_fields,
    )


def parse_ui_copy(payload: dict[str, Any]) -> dict[str, Any]:
    raw = require_object(payload.get("ui_copy"), path="structure.ui_copy")
    parsed: dict[str, Any] = {}
    for section, spec in _UI_COPY_SECTION_SPECS.items():
        parsed[section] = _parse_ui_copy_section(
            raw,
            section=section,
            string_fields=spec["string_fields"],
            list_fields=spec.get("list_fields", ()),
        )
    return parsed


def parse_settings_hub_layout_rows(raw: object) -> tuple[dict[str, str], ...]:
    rows = require_list(raw, path="structure.settings_hub_layout_rows")
    if not rows:
        raise RuntimeError("structure.settings_hub_layout_rows must not be empty")

    parsed: list[dict[str, str]] = []
    item_rows = 0
    for idx, raw_row in enumerate(rows):
        row = require_object(raw_row, path=f"structure.settings_hub_layout_rows[{idx}]")
        kind = as_non_empty_string(
            row.get("kind"),
            path=f"structure.settings_hub_layout_rows[{idx}].kind",
        )
        if kind not in _SETTINGS_HUB_LAYOUT_KINDS:
            raise RuntimeError(
                "structure.settings_hub_layout_rows kind must be one of: "
                + ", ".join(sorted(_SETTINGS_HUB_LAYOUT_KINDS))
            )
        label = as_non_empty_string(
            row.get("label"),
            path=f"structure.settings_hub_layout_rows[{idx}].label",
        )
        if kind == "header":
            parsed.append({"kind": "header", "label": label, "row_key": ""})
            continue
        row_key = as_non_empty_string(
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


def parse_pause_copy(payload: dict[str, Any]) -> dict[str, Any]:
    raw = require_object(payload.get("pause_copy"), path="structure.pause_copy")
    subtitle_template = as_non_empty_string(
        raw.get("subtitle_template"),
        path="structure.pause_copy.subtitle_template",
    )
    hints = _parse_string_list(
        raw.get("hints"),
        path="structure.pause_copy.hints",
    )
    return {
        "subtitle_template": subtitle_template,
        "hints": hints,
    }


def parse_setup_fields(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    raw_setup = require_object(
        payload.get("setup_fields"), path="structure.setup_fields"
    )
    setup_fields: dict[str, list[dict[str, Any]]] = {}
    for mode_key in MODE_KEYS:
        raw_fields = require_list(
            raw_setup.get(mode_key),
            path=f"structure.setup_fields.{mode_key}",
        )
        if not raw_fields:
            raise RuntimeError(f"structure.setup_fields.{mode_key} must not be empty")
        fields: list[dict[str, Any]] = []
        for idx, raw_field in enumerate(raw_fields):
            field = require_object(
                raw_field, path=f"structure.setup_fields.{mode_key}[{idx}]"
            )
            label = as_non_empty_string(
                field.get("label"),
                path=f"structure.setup_fields.{mode_key}[{idx}].label",
            )
            attr = as_non_empty_string(
                field.get("attr"),
                path=f"structure.setup_fields.{mode_key}[{idx}].attr",
            )
            min_val = require_int(
                field.get("min"),
                path=f"structure.setup_fields.{mode_key}[{idx}].min",
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


def parse_setup_hints(payload: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    hints_obj = require_object(payload.get("setup_hints"), path="structure.setup_hints")
    return _parse_mode_string_lists(hints_obj, base_path="structure.setup_hints")


def parse_settings_option_labels(payload: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    labels_obj = require_object(
        payload.get("settings_option_labels"),
        path="structure.settings_option_labels",
    )
    parsed: dict[str, tuple[str, ...]] = {}
    for raw_key, raw_labels in labels_obj.items():
        row_key = as_non_empty_string(
            raw_key,
            path="structure.settings_option_labels keys",
        ).lower()
        values = require_list(
            raw_labels,
            path=f"structure.settings_option_labels.{row_key}",
        )
        parsed[row_key] = _parse_string_list(
            values,
            path=f"structure.settings_option_labels.{row_key}",
        )
    random_mode_labels = parsed.get("game_random_mode")
    if random_mode_labels is None:
        raise RuntimeError(
            "structure.settings_option_labels must include game_random_mode labels"
        )
    if len(random_mode_labels) < 2:
        raise RuntimeError(
            "structure.settings_option_labels.game_random_mode must define at least two labels"
        )
    return parsed


def parse_keybinding_category_docs(payload: dict[str, Any]) -> dict[str, Any]:
    raw_docs = payload.get("keybinding_category_docs")
    if raw_docs is None:
        return {"scope_order": ("all", "2d", "3d", "4d"), "groups": {}}

    docs = require_object(raw_docs, path="structure.keybinding_category_docs")
    groups_raw = require_object(
        docs.get("groups"),
        path="structure.keybinding_category_docs.groups",
    )
    groups: dict[str, dict[str, str]] = {}
    for raw_group_name, raw_group in groups_raw.items():
        group_name = as_non_empty_string(
            raw_group_name,
            path="structure.keybinding_category_docs.groups keys",
        ).lower()
        group_obj = require_object(
            raw_group,
            path=f"structure.keybinding_category_docs.groups.{group_name}",
        )
        groups[group_name] = {
            "label": as_non_empty_string(
                group_obj.get("label"),
                path=(f"structure.keybinding_category_docs.groups.{group_name}.label"),
            ),
            "description": as_non_empty_string(
                group_obj.get("description"),
                path=(
                    "structure.keybinding_category_docs.groups."
                    f"{group_name}.description"
                ),
            ),
        }

    return {
        "scope_order": string_tuple(
            docs.get("scope_order"),
            path="structure.keybinding_category_docs.scope_order",
            normalize_lower=True,
        ),
        "groups": groups,
    }


def parse_settings_category_docs(
    payload: dict[str, Any],
) -> tuple[dict[str, str], ...]:
    raw = payload.get("settings_category_docs")
    if raw is None:
        return tuple()
    rows = require_list(raw, path="structure.settings_category_docs")
    docs: list[dict[str, str]] = []
    for idx, raw_doc in enumerate(rows):
        doc = require_object(raw_doc, path=f"structure.settings_category_docs[{idx}]")
        docs.append(
            {
                "id": as_non_empty_string(
                    doc.get("id"),
                    path=f"structure.settings_category_docs[{idx}].id",
                ).lower(),
                "label": as_non_empty_string(
                    doc.get("label"),
                    path=f"structure.settings_category_docs[{idx}].label",
                ),
                "description": as_non_empty_string(
                    doc.get("description"),
                    path=f"structure.settings_category_docs[{idx}].description",
                ),
            }
        )
    return tuple(docs)


def parse_settings_split_rules(payload: dict[str, Any]) -> dict[str, Any]:
    raw_rules = payload.get("settings_split_rules")
    if raw_rules is None:
        return {
            "max_top_level_fields": 5,
            "max_top_level_actions": 2,
            "split_when_mode_specific": True,
        }

    rules = require_object(raw_rules, path="structure.settings_split_rules")
    return {
        "max_top_level_fields": require_int(
            rules.get("max_top_level_fields"),
            path="structure.settings_split_rules.max_top_level_fields",
            min_value=1,
        ),
        "max_top_level_actions": require_int(
            rules.get("max_top_level_actions"),
            path="structure.settings_split_rules.max_top_level_actions",
            min_value=1,
        ),
        "split_when_mode_specific": require_bool(
            rules.get("split_when_mode_specific"),
            path="structure.settings_split_rules.split_when_mode_specific",
        ),
    }


def parse_settings_category_metrics(
    payload: dict[str, Any],
    docs: tuple[dict[str, str], ...],
) -> dict[str, dict[str, Any]]:
    raw_metrics = payload.get("settings_category_metrics")
    if not isinstance(raw_metrics, dict):
        return {}

    doc_ids = {entry["id"] for entry in docs}
    metrics: dict[str, dict[str, Any]] = {}
    for raw_category_id, raw_entry in raw_metrics.items():
        category_id = as_non_empty_string(
            raw_category_id,
            path="structure.settings_category_metrics keys",
        ).lower()
        if category_id not in doc_ids:
            raise RuntimeError(
                "structure.settings_category_metrics."
                f"{category_id} has no matching settings_category_docs id"
            )
        entry = require_object(
            raw_entry,
            path=f"structure.settings_category_metrics.{category_id}",
        )
        metrics[category_id] = {
            "field_count": require_int(
                entry.get("field_count"),
                path=(f"structure.settings_category_metrics.{category_id}.field_count"),
                min_value=0,
            ),
            "action_count": require_int(
                entry.get("action_count"),
                path=(
                    f"structure.settings_category_metrics.{category_id}.action_count"
                ),
                min_value=0,
            ),
            "mode_specific": require_bool(
                entry.get("mode_specific"),
                path=(
                    f"structure.settings_category_metrics.{category_id}.mode_specific"
                ),
            ),
            "top_level": require_bool(
                entry.get("top_level"),
                path=(f"structure.settings_category_metrics.{category_id}.top_level"),
            ),
        }
    return metrics


def collect_reachable_menu_ids(
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


def collect_actions_for_menu_ids(
    menus: dict[str, dict[str, Any]],
    *,
    menu_ids: set[str],
) -> set[str]:
    return _collect_item_values_for_menu_ids(
        menus,
        menu_ids=menu_ids,
        item_type="action",
        item_field="action_id",
    )


def collect_route_ids_for_menu_ids(
    menus: dict[str, dict[str, Any]],
    *,
    menu_ids: set[str],
) -> set[str]:
    return _collect_item_values_for_menu_ids(
        menus,
        menu_ids=menu_ids,
        item_type="route",
        item_field="route_id",
    )


def _collect_item_values_for_menu_ids(
    menus: dict[str, dict[str, Any]],
    *,
    menu_ids: set[str],
    item_type: str,
    item_field: str,
) -> set[str]:
    values: set[str] = set()
    for menu_id in menu_ids:
        menu = menus.get(menu_id)
        if menu is None:
            continue
        for item in menu["items"]:
            if item["type"] == item_type:
                values.add(item[item_field])
    return values


def enforce_menu_entrypoint_parity(validated: dict[str, Any]) -> None:
    menus: dict[str, dict[str, Any]] = validated["menus"]
    entrypoints: dict[str, str] = validated["menu_entrypoints"]
    launcher_actions = collect_actions_for_menu_ids(
        menus,
        menu_ids=collect_reachable_menu_ids(
            menus,
            start_menu_id=entrypoints["launcher"],
        ),
    )
    pause_actions = collect_actions_for_menu_ids(
        menus,
        menu_ids=collect_reachable_menu_ids(
            menus,
            start_menu_id=entrypoints["pause"],
        ),
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


def enforce_settings_split_policy(validated: dict[str, Any]) -> None:
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
                "settings split policy violation: "
                f"{category_id} exceeds max_top_level_fields"
            )
        if int(entry.get("action_count", 0)) > max_actions:
            raise RuntimeError(
                "settings split policy violation: "
                f"{category_id} exceeds max_top_level_actions"
            )
        if split_mode_specific and bool(entry.get("mode_specific")):
            raise RuntimeError(
                "settings split policy violation: "
                f"{category_id} is mode-specific and must not remain top-level"
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


def validate_structure_payload(payload: dict[str, Any]) -> dict[str, Any]:
    menus = parse_menus(payload.get("menus"))
    entrypoints = parse_menu_entrypoints(payload, menus=menus)
    launcher_subtitles = parse_launcher_subtitles(payload)
    launcher_route_actions = parse_launcher_route_actions(payload)
    branding = parse_branding(payload)
    ui_copy = parse_ui_copy(payload)

    launcher_reachable_menus = collect_reachable_menu_ids(
        menus,
        start_menu_id=entrypoints["launcher"],
    )
    launcher_actions = collect_actions_for_menu_ids(
        menus,
        menu_ids=launcher_reachable_menus,
    )
    launcher_route_ids = collect_route_ids_for_menu_ids(
        menus,
        menu_ids=launcher_reachable_menus,
    )
    unknown_route_mappings = sorted(set(launcher_route_actions) - launcher_route_ids)
    if unknown_route_mappings:
        raise RuntimeError(
            "structure.launcher_route_actions maps unknown route ids: "
            + ", ".join(unknown_route_mappings)
        )
    missing_route_mappings = sorted(launcher_route_ids - set(launcher_route_actions))
    if missing_route_mappings:
        raise RuntimeError(
            "structure.launcher_route_actions missing route mappings for: "
            + ", ".join(missing_route_mappings)
        )
    invalid_route_actions = sorted(
        {
            action_id
            for action_id in launcher_route_actions.values()
            if action_id not in launcher_actions
        }
    )
    if invalid_route_actions:
        raise RuntimeError(
            "structure.launcher_route_actions references unknown launcher actions: "
            + ", ".join(invalid_route_actions)
        )

    pause_rows = string_tuple(
        payload.get("pause_menu_rows"), path="structure.pause_menu_rows"
    )
    pause_actions = string_tuple(
        payload.get("pause_menu_actions"),
        path="structure.pause_menu_actions",
        normalize_lower=True,
    )
    if len(pause_rows) != len(pause_actions):
        raise RuntimeError(
            "pause_menu_rows and pause_menu_actions must have equal length"
        )

    settings_docs = parse_settings_category_docs(payload)
    validated = {
        "menus": menus,
        "menu_entrypoints": entrypoints,
        "launcher_subtitles": launcher_subtitles,
        "launcher_route_actions": launcher_route_actions,
        "branding": branding,
        "ui_copy": ui_copy,
        "settings_hub_rows": string_tuple(
            payload.get("settings_hub_rows"),
            path="structure.settings_hub_rows",
        ),
        "settings_hub_layout_rows": parse_settings_hub_layout_rows(
            payload.get("settings_hub_layout_rows")
        ),
        "bot_options_rows": string_tuple(
            payload.get("bot_options_rows"),
            path="structure.bot_options_rows",
        ),
        "pause_menu_rows": pause_rows,
        "pause_menu_actions": pause_actions,
        "pause_copy": parse_pause_copy(payload),
        "setup_fields": parse_setup_fields(payload),
        "setup_hints": parse_setup_hints(payload),
        "settings_option_labels": parse_settings_option_labels(payload),
        "keybinding_category_docs": parse_keybinding_category_docs(payload),
        "settings_category_docs": settings_docs,
        "settings_split_rules": parse_settings_split_rules(payload),
        "settings_category_metrics": parse_settings_category_metrics(
            payload,
            settings_docs,
        ),
    }
    enforce_settings_split_policy(validated)
    enforce_menu_entrypoint_parity(validated)
    return validated


def resolve_field_max(
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
            "structure.setup_fields."
            f"{mode_key}.{attr_name}.max must be int or dynamic max token"
        )
    return raw_max
