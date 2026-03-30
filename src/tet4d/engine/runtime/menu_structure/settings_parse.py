from __future__ import annotations

from typing import Any

from ..settings_schema import (
    MODE_KEYS,
    as_non_empty_string,
    require_bool,
    require_int,
    require_list,
    require_object,
    string_tuple,
)
from .parse_helpers import parse_mode_string_lists, parse_string_list

_SETTINGS_HUB_LAYOUT_KINDS = {"header", "item"}


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
    hints = parse_string_list(
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
    return parse_mode_string_lists(hints_obj, base_path="structure.setup_hints")


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
        parsed[row_key] = parse_string_list(
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
                path=f"structure.keybinding_category_docs.groups.{group_name}.label",
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
                path=f"structure.settings_category_metrics.{category_id}.field_count",
                min_value=0,
            ),
            "action_count": require_int(
                entry.get("action_count"),
                path=(f"structure.settings_category_metrics.{category_id}.action_count"),
                min_value=0,
            ),
            "mode_specific": require_bool(
                entry.get("mode_specific"),
                path=f"structure.settings_category_metrics.{category_id}.mode_specific",
            ),
            "top_level": require_bool(
                entry.get("top_level"),
                path=f"structure.settings_category_metrics.{category_id}.top_level",
            ),
        }
    return metrics


def parse_settings_sections(
    payload: dict[str, Any],
    *,
    layout_rows: tuple[dict[str, str], ...],
) -> dict[str, dict[str, Any]]:
    layout_headers = {
        row["label"] for row in layout_rows if row.get("kind") == "header"
    }
    layout_item_keys = {
        row["row_key"] for row in layout_rows if row.get("kind") == "item"
    }
    raw_sections = require_object(
        payload.get("settings_sections"),
        path="structure.settings_sections",
    )
    sections: dict[str, dict[str, Any]] = {}
    for raw_section_id, raw_section in raw_sections.items():
        section_id = as_non_empty_string(
            raw_section_id,
            path="structure.settings_sections keys",
        ).lower()
        section = require_object(
            raw_section,
            path=f"structure.settings_sections.{section_id}",
        )
        headers = parse_string_list(
            section.get("headers"),
            path=f"structure.settings_sections.{section_id}.headers",
        )
        row_keys = string_tuple(
            section.get("row_keys"),
            path=f"structure.settings_sections.{section_id}.row_keys",
            normalize_lower=True,
        )
        missing_headers = sorted(set(headers) - layout_headers)
        if missing_headers:
            raise RuntimeError(
                "structure.settings_sections."
                f"{section_id}.headers reference unknown layout headers: "
                + ", ".join(missing_headers)
            )
        missing_row_keys = sorted(set(row_keys) - layout_item_keys)
        if missing_row_keys:
            raise RuntimeError(
                "structure.settings_sections."
                f"{section_id}.row_keys reference unknown layout row keys: "
                + ", ".join(missing_row_keys)
            )
        sections[section_id] = {
            "title": as_non_empty_string(
                section.get("title"),
                path=f"structure.settings_sections.{section_id}.title",
            ),
            "subtitle": as_non_empty_string(
                section.get("subtitle"),
                path=f"structure.settings_sections.{section_id}.subtitle",
            ),
            "headers": headers,
            "row_keys": row_keys,
        }
    return sections


def parse_launcher_settings_routes(
    payload: dict[str, Any],
    *,
    settings_sections: dict[str, dict[str, Any]],
    launcher_settings_action_ids: set[str],
) -> dict[str, dict[str, str]]:
    raw_routes = require_object(
        payload.get("launcher_settings_routes"),
        path="structure.launcher_settings_routes",
    )
    routes: dict[str, dict[str, str]] = {}
    for raw_action_id, raw_route in raw_routes.items():
        action_id = as_non_empty_string(
            raw_action_id,
            path="structure.launcher_settings_routes keys",
        ).lower()
        if action_id not in launcher_settings_action_ids:
            raise RuntimeError(
                "structure.launcher_settings_routes references unknown launcher settings action: "
                f"{action_id}"
            )
        route = require_object(
            raw_route,
            path=f"structure.launcher_settings_routes.{action_id}",
        )
        section_id = as_non_empty_string(
            route.get("section_id"),
            path=f"structure.launcher_settings_routes.{action_id}.section_id",
        ).lower()
        if section_id not in settings_sections:
            raise RuntimeError(
                "structure.launcher_settings_routes."
                f"{action_id}.section_id references unknown section: {section_id}"
            )
        initial_row_key = as_non_empty_string(
            route.get("initial_row_key"),
            path=f"structure.launcher_settings_routes.{action_id}.initial_row_key",
        ).lower()
        if initial_row_key not in settings_sections[section_id]["row_keys"]:
            raise RuntimeError(
                "structure.launcher_settings_routes."
                f"{action_id}.initial_row_key must belong to section {section_id}: "
                f"{initial_row_key}"
            )
        routes[action_id] = {
            "section_id": section_id,
            "initial_row_key": initial_row_key,
        }
    return routes


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
