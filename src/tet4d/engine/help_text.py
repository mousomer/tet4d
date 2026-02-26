from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .runtime.help_topics_storage import load_json_file
from .runtime.project_config import project_root_path

HELP_CONFIG_DIR = project_root_path() / "config" / "help"
HELP_CONTENT_FILE = HELP_CONFIG_DIR / "content" / "runtime_help_content.json"
HELP_LAYOUT_FILE = HELP_CONFIG_DIR / "layout" / "runtime_help_layout.json"


class HelpTextValidationError(RuntimeError):
    pass


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = load_json_file(path)
    except OSError as exc:
        raise HelpTextValidationError(f"Failed reading help file {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise HelpTextValidationError(f"Invalid JSON in help file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise HelpTextValidationError(f"Help file {path} must contain a JSON object")
    return payload


def _clean_string(value: object, *, path: str) -> str:
    if not isinstance(value, str):
        raise HelpTextValidationError(f"{path} must be a string")
    return value


def _clean_non_empty_string(value: object, *, path: str) -> str:
    text = _clean_string(value, path=path).strip()
    if not text:
        raise HelpTextValidationError(f"{path} must be non-empty")
    return text


def _clean_int(value: object, *, path: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise HelpTextValidationError(f"{path} must be an integer")
    if value < minimum:
        raise HelpTextValidationError(f"{path} must be >= {minimum}")
    return value


def _validate_lines(raw_lines: object, *, path: str) -> tuple[str, ...]:
    if raw_lines is None:
        return tuple()
    if not isinstance(raw_lines, list):
        raise HelpTextValidationError(f"{path} must be a list")
    return tuple(
        _clean_string(item, path=f"{path}[{idx}]") for idx, item in enumerate(raw_lines)
    )


def _validate_fallback_topic(raw: object) -> dict[str, Any]:
    path = "help_content.fallback_topic"
    if not isinstance(raw, dict):
        raise HelpTextValidationError(f"{path} must be an object")
    sections_raw = raw.get("sections")
    if not isinstance(sections_raw, list) or not sections_raw:
        raise HelpTextValidationError(f"{path}.sections must be a non-empty list")
    sections: list[dict[str, Any]] = []
    for idx, raw_section in enumerate(sections_raw):
        section_path = f"{path}.sections[{idx}]"
        if not isinstance(raw_section, dict):
            raise HelpTextValidationError(f"{section_path} must be an object")
        lines = _validate_lines(raw_section.get("lines"), path=f"{section_path}.lines")
        if not lines:
            raise HelpTextValidationError(f"{section_path}.lines must be non-empty")
        sections.append(
            {
                "id": _clean_non_empty_string(
                    raw_section.get("id"), path=f"{section_path}.id"
                ),
                "title": _clean_non_empty_string(
                    raw_section.get("title"), path=f"{section_path}.title"
                ),
                "lines": lines,
            }
        )
    return {
        "id": _clean_non_empty_string(raw.get("id"), path=f"{path}.id"),
        "title": _clean_non_empty_string(raw.get("title"), path=f"{path}.title"),
        "summary": _clean_non_empty_string(
            raw.get("summary"), path=f"{path}.summary"
        ),
        "sections": tuple(sections),
    }


def _validate_topic_blocks(raw_blocks: object) -> dict[str, dict[str, Any]]:
    if not isinstance(raw_blocks, dict):
        raise HelpTextValidationError("help_content.topic_blocks must be an object")
    validated: dict[str, dict[str, Any]] = {}
    for topic_id, raw_entry in raw_blocks.items():
        entry_path = f"help_content.topic_blocks.{topic_id}"
        topic_key = _clean_non_empty_string(topic_id, path="help_content.topic_blocks keys")
        if not isinstance(raw_entry, dict):
            raise HelpTextValidationError(f"{entry_path} must be an object")
        compact_lines = _validate_lines(
            raw_entry.get("compact_lines"),
            path=f"{entry_path}.compact_lines",
        )
        full_lines = _validate_lines(
            raw_entry.get("full_lines"), path=f"{entry_path}.full_lines"
        )
        if not compact_lines and not full_lines:
            raise HelpTextValidationError(
                f"{entry_path} must define at least one of compact_lines/full_lines"
            )
        validated[topic_key] = {
            "compact_lines": compact_lines,
            "full_lines": full_lines,
            "compact_topic_limit": _clean_int(
                raw_entry.get("compact_topic_limit", 0),
                path=f"{entry_path}.compact_topic_limit",
                minimum=0,
            ),
            "compact_overflow_line": _clean_string(
                raw_entry.get("compact_overflow_line", ""),
                path=f"{entry_path}.compact_overflow_line",
            ),
        }
    return validated


def _validate_string_map(raw_map: object, *, path: str) -> dict[str, str]:
    if not isinstance(raw_map, dict):
        raise HelpTextValidationError(f"{path} must be an object")
    out: dict[str, str] = {}
    for raw_key, raw_value in raw_map.items():
        key = _clean_non_empty_string(raw_key, path=f"{path} keys")
        out[key] = _clean_non_empty_string(raw_value, path=f"{path}.{key}")
    return out


def _validate_rgb_triplet(value: object, *, path: str) -> tuple[int, int, int]:
    if not isinstance(value, list) or len(value) != 3:
        raise HelpTextValidationError(f"{path} must be a list of 3 integers")
    cleaned: list[int] = []
    for idx, raw in enumerate(value):
        color = _clean_int(raw, path=f"{path}[{idx}]", minimum=0)
        if color > 255:
            raise HelpTextValidationError(f"{path}[{idx}] must be <= 255")
        cleaned.append(color)
    return (cleaned[0], cleaned[1], cleaned[2])


def _validate_layout_media_entry(raw: object, *, path: str) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise HelpTextValidationError(f"{path} must be an object")
    mode = _clean_non_empty_string(raw.get("mode"), path=f"{path}.mode")
    if mode not in {"text", "controls"}:
        raise HelpTextValidationError(f"{path}.mode must be 'text' or 'controls'")
    return {
        "mode": mode,
        "icon_placement": _clean_non_empty_string(
            raw.get("icon_placement"), path=f"{path}.icon_placement"
        ),
        "image_placement": _clean_non_empty_string(
            raw.get("image_placement"), path=f"{path}.image_placement"
        ),
    }


def _validate_layout_colors(colors_raw: object) -> dict[str, tuple[int, int, int]]:
    if not isinstance(colors_raw, dict):
        raise HelpTextValidationError("help_layout.colors must be an object")
    return {
        "bg_top": _validate_rgb_triplet(colors_raw.get("bg_top"), path="help_layout.colors.bg_top"),
        "bg_bottom": _validate_rgb_triplet(
            colors_raw.get("bg_bottom"), path="help_layout.colors.bg_bottom"
        ),
        "text": _validate_rgb_triplet(colors_raw.get("text"), path="help_layout.colors.text"),
        "muted": _validate_rgb_triplet(colors_raw.get("muted"), path="help_layout.colors.muted"),
        "highlight": _validate_rgb_triplet(
            colors_raw.get("highlight"), path="help_layout.colors.highlight"
        ),
    }


def _validate_layout_thresholds(thresholds_raw: object) -> dict[str, int]:
    if not isinstance(thresholds_raw, dict):
        raise HelpTextValidationError("help_layout.thresholds must be an object")
    return {
        "compact_width_threshold": _clean_int(
            thresholds_raw.get("compact_width_threshold"),
            path="help_layout.thresholds.compact_width_threshold",
            minimum=1,
        ),
        "compact_height_threshold": _clean_int(
            thresholds_raw.get("compact_height_threshold"),
            path="help_layout.thresholds.compact_height_threshold",
            minimum=1,
        ),
    }


def _validate_compact_adjustments(raw: object) -> dict[str, int]:
    if not isinstance(raw, dict):
        raise HelpTextValidationError(
            "help_layout.geometry.compact_adjustments must be an object"
        )
    return {
        "header_extra_min": _clean_int(
            raw.get("header_extra_min"),
            path="help_layout.geometry.compact_adjustments.header_extra_min",
            minimum=0,
        ),
        "header_extra_divisor": _clean_int(
            raw.get("header_extra_divisor"),
            path="help_layout.geometry.compact_adjustments.header_extra_divisor",
            minimum=1,
        ),
        "footer_height_min": _clean_int(
            raw.get("footer_height_min"),
            path="help_layout.geometry.compact_adjustments.footer_height_min",
            minimum=0,
        ),
        "footer_height_reduce": _clean_int(
            raw.get("footer_height_reduce"),
            path="help_layout.geometry.compact_adjustments.footer_height_reduce",
            minimum=0,
        ),
        "gap_min": _clean_int(
            raw.get("gap_min"),
            path="help_layout.geometry.compact_adjustments.gap_min",
            minimum=0,
        ),
        "gap_reduce": _clean_int(
            raw.get("gap_reduce"),
            path="help_layout.geometry.compact_adjustments.gap_reduce",
            minimum=0,
        ),
        "min_content_height_min": _clean_int(
            raw.get("min_content_height_min"),
            path="help_layout.geometry.compact_adjustments.min_content_height_min",
            minimum=1,
        ),
        "min_content_height_divisor": _clean_int(
            raw.get("min_content_height_divisor"),
            path="help_layout.geometry.compact_adjustments.min_content_height_divisor",
            minimum=1,
        ),
    }


def _validate_layout_geometry(geometry_raw: object) -> dict[str, Any]:
    if not isinstance(geometry_raw, dict):
        raise HelpTextValidationError("help_layout.geometry must be an object")
    return {
        "outer_pad": _clean_int(
            geometry_raw.get("outer_pad"),
            path="help_layout.geometry.outer_pad",
            minimum=0,
        ),
        "header_extra": _clean_int(
            geometry_raw.get("header_extra"),
            path="help_layout.geometry.header_extra",
            minimum=0,
        ),
        "gap": _clean_int(
            geometry_raw.get("gap"), path="help_layout.geometry.gap", minimum=0
        ),
        "footer_height": _clean_int(
            geometry_raw.get("footer_height"),
            path="help_layout.geometry.footer_height",
            minimum=0,
        ),
        "min_content_height": _clean_int(
            geometry_raw.get("min_content_height"),
            path="help_layout.geometry.min_content_height",
            minimum=1,
        ),
        "content_pad_x": _clean_int(
            geometry_raw.get("content_pad_x"),
            path="help_layout.geometry.content_pad_x",
            minimum=0,
        ),
        "content_pad_y": _clean_int(
            geometry_raw.get("content_pad_y"),
            path="help_layout.geometry.content_pad_y",
            minimum=0,
        ),
        "compact_adjustments": _validate_compact_adjustments(
            geometry_raw.get("compact_adjustments")
        ),
    }


def _validate_layout_topic_rules(topic_rules_raw: object) -> dict[str, str]:
    if not isinstance(topic_rules_raw, dict):
        raise HelpTextValidationError("help_layout.topic_rules must be an object")
    return {
        "controls_topic_id": _clean_non_empty_string(
            topic_rules_raw.get("controls_topic_id"),
            path="help_layout.topic_rules.controls_topic_id",
        ),
        "key_reference_topic_id": _clean_non_empty_string(
            topic_rules_raw.get("key_reference_topic_id"),
            path="help_layout.topic_rules.key_reference_topic_id",
        ),
    }


def _validate_controls_helper_layout(controls_helper_raw: object) -> dict[str, Any]:
    if not isinstance(controls_helper_raw, dict):
        raise HelpTextValidationError(
            "help_layout.controls_helper_layout must be an object"
        )
    return {
        "inset_x": _clean_int(
            controls_helper_raw.get("inset_x"),
            path="help_layout.controls_helper_layout.inset_x",
            minimum=0,
        ),
        "bottom_pad_y": _clean_int(
            controls_helper_raw.get("bottom_pad_y"),
            path="help_layout.controls_helper_layout.bottom_pad_y",
            minimum=0,
        ),
        "icon_placement": _clean_non_empty_string(
            controls_helper_raw.get("icon_placement"),
            path="help_layout.controls_helper_layout.icon_placement",
        ),
        "image_placement": _clean_non_empty_string(
            controls_helper_raw.get("image_placement"),
            path="help_layout.controls_helper_layout.image_placement",
        ),
    }


def _validate_layout_header(header_raw: object) -> dict[str, str]:
    if not isinstance(header_raw, dict):
        raise HelpTextValidationError("help_layout.header must be an object")
    return {
        "title": _clean_non_empty_string(
            header_raw.get("title"), path="help_layout.header.title"
        ),
        "subtitle_compact": _clean_non_empty_string(
            header_raw.get("subtitle_compact"),
            path="help_layout.header.subtitle_compact",
        ),
        "subtitle_full": _clean_non_empty_string(
            header_raw.get("subtitle_full"), path="help_layout.header.subtitle_full"
        ),
    }


def _validate_layout_labels(labels_raw: object) -> dict[str, str]:
    if not isinstance(labels_raw, dict):
        raise HelpTextValidationError("help_layout.labels must be an object")
    return {
        "topic": _clean_non_empty_string(
            labels_raw.get("topic"), path="help_layout.labels.topic"
        ),
        "part": _clean_non_empty_string(
            labels_raw.get("part"), path="help_layout.labels.part"
        ),
    }


def _validate_footer_hints(footer_hints_raw: object) -> dict[str, str]:
    if not isinstance(footer_hints_raw, dict):
        raise HelpTextValidationError("help_layout.footer_hints must be an object")
    return {
        "compact": _clean_non_empty_string(
            footer_hints_raw.get("compact"), path="help_layout.footer_hints.compact"
        ),
        "full": _clean_non_empty_string(
            footer_hints_raw.get("full"), path="help_layout.footer_hints.full"
        ),
    }


def _validate_topic_media_placement(media_raw: object) -> dict[str, dict[str, str]]:
    if not isinstance(media_raw, dict) or not media_raw:
        raise HelpTextValidationError(
            "help_layout.topic_media_placement must be a non-empty object"
        )
    topic_media_placement: dict[str, dict[str, str]] = {}
    for topic_id, raw_entry in media_raw.items():
        key = _clean_non_empty_string(
            topic_id, path="help_layout.topic_media_placement keys"
        )
        topic_media_placement[key] = _validate_layout_media_entry(
            raw_entry,
            path=f"help_layout.topic_media_placement.{key}",
        )
    if "default" not in topic_media_placement:
        raise HelpTextValidationError(
            "help_layout.topic_media_placement must define a 'default' entry"
        )
    return topic_media_placement


def _validate_layout_payload(payload: dict[str, Any]) -> dict[str, Any]:
    version = _clean_int(payload.get("version"), path="help_layout.version", minimum=1)
    return {
        "version": version,
        "colors": _validate_layout_colors(payload.get("colors")),
        "thresholds": _validate_layout_thresholds(payload.get("thresholds")),
        "geometry": _validate_layout_geometry(payload.get("geometry")),
        "topic_rules": _validate_layout_topic_rules(payload.get("topic_rules")),
        "controls_helper_layout": _validate_controls_helper_layout(
            payload.get("controls_helper_layout")
        ),
        "header": _validate_layout_header(payload.get("header")),
        "labels": _validate_layout_labels(payload.get("labels")),
        "footer_hints": _validate_footer_hints(payload.get("footer_hints")),
        "topic_media_placement": _validate_topic_media_placement(
            payload.get("topic_media_placement")
        ),
    }


@lru_cache(maxsize=1)
def help_content_registry() -> dict[str, Any]:
    payload = _read_json_object(HELP_CONTENT_FILE)
    version = _clean_int(payload.get("version"), path="help_content.version", minimum=1)
    topic_blocks = _validate_topic_blocks(payload.get("topic_blocks"))
    value_templates = _validate_string_map(
        payload.get("value_templates"), path="help_content.value_templates"
    )
    action_group_headings = _validate_string_map(
        payload.get("action_group_headings"),
        path="help_content.action_group_headings",
    )
    fallback_topic = _validate_fallback_topic(payload.get("fallback_topic"))
    return {
        "version": version,
        "topic_blocks": topic_blocks,
        "value_templates": value_templates,
        "action_group_headings": action_group_headings,
        "fallback_topic": fallback_topic,
    }


@lru_cache(maxsize=1)
def help_layout_registry() -> dict[str, Any]:
    payload = _read_json_object(HELP_LAYOUT_FILE)
    return _validate_layout_payload(payload)


def help_topic_block_lines(topic_id: str, *, compact: bool) -> tuple[str, ...]:
    blocks = help_content_registry()["topic_blocks"]
    raw_id = str(topic_id).strip()
    if not raw_id or raw_id not in blocks:
        return tuple()
    entry = blocks[raw_id]
    lines = entry["compact_lines"] if compact else entry["full_lines"]
    if lines:
        return lines
    return entry["full_lines"] if compact else entry["compact_lines"]


def help_topic_compact_limit(topic_id: str) -> int:
    blocks = help_content_registry()["topic_blocks"]
    raw_id = str(topic_id).strip()
    if not raw_id or raw_id not in blocks:
        return 0
    return int(blocks[raw_id]["compact_topic_limit"])


def help_topic_compact_overflow_line(topic_id: str) -> str:
    blocks = help_content_registry()["topic_blocks"]
    raw_id = str(topic_id).strip()
    if not raw_id or raw_id not in blocks:
        return ""
    return str(blocks[raw_id]["compact_overflow_line"])


def help_value_template(name: str, *, default: str = "") -> str:
    templates = help_content_registry()["value_templates"]
    key = str(name).strip()
    if not key:
        return default
    return str(templates.get(key, default))


def help_action_group_heading(group: str) -> str:
    headings = help_content_registry()["action_group_headings"]
    key = str(group).strip()
    if not key:
        return ""
    return str(headings.get(key, ""))


def help_fallback_topic() -> dict[str, Any]:
    topic = help_content_registry()["fallback_topic"]
    sections = tuple(
        {
            "id": section["id"],
            "title": section["title"],
            "lines": tuple(section["lines"]),
        }
        for section in topic["sections"]
    )
    return {
        "id": topic["id"],
        "title": topic["title"],
        "summary": topic["summary"],
        "sections": sections,
    }


def help_layout_payload() -> dict[str, Any]:
    layout = help_layout_registry()
    return {
        "version": layout["version"],
        "colors": dict(layout["colors"]),
        "thresholds": dict(layout["thresholds"]),
        "geometry": {
            **layout["geometry"],
            "compact_adjustments": dict(layout["geometry"]["compact_adjustments"]),
        },
        "topic_rules": dict(layout["topic_rules"]),
        "controls_helper_layout": dict(layout["controls_helper_layout"]),
        "header": dict(layout["header"]),
        "labels": dict(layout["labels"]),
        "footer_hints": dict(layout["footer_hints"]),
        "topic_media_placement": {
            key: dict(value) for key, value in layout["topic_media_placement"].items()
        },
    }


def help_topic_media_rule(topic_id: str) -> dict[str, str]:
    placement = help_layout_registry()["topic_media_placement"]
    key = str(topic_id).strip()
    if key and key in placement:
        return dict(placement[key])
    return dict(placement["default"])


def validate_help_text_contract() -> tuple[bool, str]:
    try:
        help_content_registry()
        help_layout_registry()
    except HelpTextValidationError as exc:
        return False, str(exc)
    return True, "Help text/layout contract validated"


def clear_help_text_cache() -> None:
    help_content_registry.cache_clear()
    help_layout_registry.cache_clear()
