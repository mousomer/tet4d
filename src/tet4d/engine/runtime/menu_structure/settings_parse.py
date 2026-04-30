from __future__ import annotations

from typing import Any

from ..menu_field_spec import FieldControlFamily, FieldSemanticType
from ..settings_schema import (
    MODE_KEYS,
    as_non_empty_string,
    require_bool,
    require_int,
    require_list,
    require_object,
)
from .parse_helpers import parse_mode_string_lists, parse_string_list

_SETTING_SEMANTIC_TYPES: set[FieldSemanticType] = {"bool", "enum", "int", "float"}
_SETUP_CONTROL_FAMILIES: set[FieldControlFamily] = {
    "selector",
    "slider",
    "stepper",
    "toggle",
}
_STORAGE_TYPES = {"bool", "float", "int", "int_index", "string_id"}


def _parse_setup_field_semantics(
    field: dict[str, Any],
    *,
    mode_key: str,
    idx: int,
) -> tuple[str, str]:
    semantic_type = as_non_empty_string(
        field.get("semantic_type"),
        path=f"structure.setup_fields.{mode_key}[{idx}].semantic_type",
    ).lower()
    if semantic_type not in _SETTING_SEMANTIC_TYPES:
        raise RuntimeError(
            "structure.setup_fields."
            f"{mode_key}[{idx}].semantic_type must be one of: "
            + ", ".join(sorted(_SETTING_SEMANTIC_TYPES))
        )
    control = as_non_empty_string(
        field.get("control"),
        path=f"structure.setup_fields.{mode_key}[{idx}].control",
    ).lower()
    if control not in _SETUP_CONTROL_FAMILIES:
        raise RuntimeError(
            "structure.setup_fields."
            f"{mode_key}[{idx}].control must be one of: "
            + ", ".join(sorted(_SETUP_CONTROL_FAMILIES))
        )
    return semantic_type, control


def _parse_enum_setup_field(
    field: dict[str, Any],
    *,
    mode_key: str,
    idx: int,
    parsed_field: dict[str, Any],
) -> dict[str, Any]:
    raw_options = field.get("options")
    raw_options_source = field.get("options_source")
    has_options = raw_options is not None
    has_options_source = raw_options_source is not None
    if parsed_field["control"] != "selector":
        raise RuntimeError(
            "structure.setup_fields."
            f"{mode_key}[{idx}] enum fields must use control='selector'"
        )
    if has_options == has_options_source:
        raise RuntimeError(
            "structure.setup_fields."
            f"{mode_key}[{idx}] enum fields must define exactly one of "
            "'options' or 'options_source'"
        )
    if "min" in field or "max" in field:
        raise RuntimeError(
            "structure.setup_fields."
            f"{mode_key}[{idx}] enum fields must not define min/max bounds"
        )
    if has_options:
        parsed_field["options"] = parse_string_list(
            raw_options,
            path=f"structure.setup_fields.{mode_key}[{idx}].options",
        )
    else:
        parsed_field["options_source"] = as_non_empty_string(
            raw_options_source,
            path=f"structure.setup_fields.{mode_key}[{idx}].options_source",
        ).lower()
    return parsed_field


def _parse_bool_setup_field(
    field: dict[str, Any],
    *,
    mode_key: str,
    idx: int,
    parsed_field: dict[str, Any],
) -> dict[str, Any]:
    if parsed_field["control"] != "toggle":
        raise RuntimeError(
            "structure.setup_fields."
            f"{mode_key}[{idx}] bool fields must use control='toggle'"
        )
    if any(key in field for key in ("min", "max", "options", "options_source")):
        raise RuntimeError(
            "structure.setup_fields."
            f"{mode_key}[{idx}] bool fields must not define numeric or enum metadata"
        )
    return parsed_field


def _parse_numeric_setup_field(
    field: dict[str, Any],
    *,
    mode_key: str,
    idx: int,
    parsed_field: dict[str, Any],
) -> dict[str, Any]:
    if parsed_field["control"] not in {"slider", "stepper"}:
        raise RuntimeError(
            "structure.setup_fields."
            f"{mode_key}[{idx}] numeric fields must use control='slider' or 'stepper'"
        )
    if "options" in field or "options_source" in field:
        raise RuntimeError(
            "structure.setup_fields."
            f"{mode_key}[{idx}] numeric fields must not define enum options"
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
    parsed_field["min"] = min_val
    parsed_field["max"] = raw_max
    return parsed_field


def _parse_setup_field(
    raw_field: object,
    *,
    mode_key: str,
    idx: int,
) -> dict[str, Any]:
    field = require_object(raw_field, path=f"structure.setup_fields.{mode_key}[{idx}]")
    parsed_field = {
        "label": as_non_empty_string(
            field.get("label"),
            path=f"structure.setup_fields.{mode_key}[{idx}].label",
        ),
        "attr": as_non_empty_string(
            field.get("attr"),
            path=f"structure.setup_fields.{mode_key}[{idx}].attr",
        ),
    }
    raw_storage_type = field.get("storage_type")
    if raw_storage_type is not None:
        storage_type = as_non_empty_string(
            raw_storage_type,
            path=f"structure.setup_fields.{mode_key}[{idx}].storage_type",
        ).lower()
        if storage_type not in _STORAGE_TYPES:
            raise RuntimeError(
                "structure.setup_fields."
                f"{mode_key}[{idx}].storage_type must be one of: "
                + ", ".join(sorted(_STORAGE_TYPES))
            )
        parsed_field["storage_type"] = storage_type
    semantic_type, control = _parse_setup_field_semantics(field, mode_key=mode_key, idx=idx)
    parsed_field["semantic_type"] = semantic_type
    parsed_field["control"] = control
    if semantic_type == "enum":
        return _parse_enum_setup_field(
            field,
            mode_key=mode_key,
            idx=idx,
            parsed_field=parsed_field,
        )
    if semantic_type == "bool":
        return _parse_bool_setup_field(
            field,
            mode_key=mode_key,
            idx=idx,
            parsed_field=parsed_field,
        )
    return _parse_numeric_setup_field(
        field,
        mode_key=mode_key,
        idx=idx,
        parsed_field=parsed_field,
    )


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
        setup_fields[mode_key] = [
            _parse_setup_field(raw_field, mode_key=mode_key, idx=idx)
            for idx, raw_field in enumerate(raw_fields)
        ]
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
