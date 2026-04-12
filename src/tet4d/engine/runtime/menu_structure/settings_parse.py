from __future__ import annotations

from typing import Any

from ..settings_schema import (
    MODE_KEYS,
    as_non_empty_string,
    require_bool,
    require_int,
    require_list,
    require_object,
)
from .parse_helpers import parse_mode_string_lists, parse_string_list


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
