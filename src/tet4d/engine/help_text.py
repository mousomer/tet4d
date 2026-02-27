from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .runtime.json_storage import read_json_value_or_raise
from .runtime.project_config import project_root_path

HELP_CONFIG_DIR = project_root_path() / "config" / "help"
HELP_CONTENT_FILE = HELP_CONFIG_DIR / "content" / "runtime_help_content.json"
HELP_LAYOUT_FILE = HELP_CONFIG_DIR / "layout" / "runtime_help_layout.json"


class HelpTextValidationError(RuntimeError):
    pass


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = read_json_value_or_raise(path)
    except OSError as exc:
        raise HelpTextValidationError(
            f"Failed reading help file {path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise HelpTextValidationError(
            f"Invalid JSON in help file {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise HelpTextValidationError(f"Help file {path} must contain a JSON object")
    return payload


def _require_object(value: object, *, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HelpTextValidationError(f"{path} must be an object")
    return value


def _require_list(value: object, *, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise HelpTextValidationError(f"{path} must be a list")
    return value


def _require_string(value: object, *, path: str, non_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise HelpTextValidationError(f"{path} must be a string")
    if non_empty and not value.strip():
        raise HelpTextValidationError(f"{path} must be non-empty")
    return value.strip() if non_empty else value


def _require_int(value: object, *, path: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise HelpTextValidationError(f"{path} must be an integer")
    if value < minimum:
        raise HelpTextValidationError(f"{path} must be >= {minimum}")
    return value


def _string_lines(raw: object, *, path: str, allow_empty: bool) -> tuple[str, ...]:
    if raw is None:
        if allow_empty:
            return tuple()
        raise HelpTextValidationError(f"{path} must be a list")
    values = _require_list(raw, path=path)
    lines = tuple(
        _require_string(item, path=f"{path}[{idx}]") for idx, item in enumerate(values)
    )
    if not allow_empty and not lines:
        raise HelpTextValidationError(f"{path} must be non-empty")
    return lines


def _rgb_triplet(value: object, *, path: str) -> tuple[int, int, int]:
    values = _require_list(value, path=path)
    if len(values) != 3:
        raise HelpTextValidationError(f"{path} must have 3 items")
    rgb = tuple(
        _require_int(v, path=f"{path}[{idx}]", minimum=0)
        for idx, v in enumerate(values)
    )
    if any(component > 255 for component in rgb):
        raise HelpTextValidationError(f"{path} values must be <= 255")
    return (rgb[0], rgb[1], rgb[2])


def _string_map(raw: object, *, path: str) -> dict[str, str]:
    obj = _require_object(raw, path=path)
    out: dict[str, str] = {}
    for key, value in obj.items():
        clean_key = _require_string(key, path=f"{path} keys", non_empty=True)
        out[clean_key] = _require_string(
            value, path=f"{path}.{clean_key}", non_empty=True
        )
    return out


def _validate_fallback_topic(raw: object) -> dict[str, Any]:
    topic = _require_object(raw, path="help_content.fallback_topic")
    sections_raw = _require_list(
        topic.get("sections"), path="help_content.fallback_topic.sections"
    )
    if not sections_raw:
        raise HelpTextValidationError(
            "help_content.fallback_topic.sections must be non-empty"
        )
    sections: list[dict[str, Any]] = []
    for idx, raw_section in enumerate(sections_raw):
        section = _require_object(
            raw_section, path=f"help_content.fallback_topic.sections[{idx}]"
        )
        lines = _string_lines(
            section.get("lines"),
            path=f"help_content.fallback_topic.sections[{idx}].lines",
            allow_empty=False,
        )
        sections.append(
            {
                "id": _require_string(
                    section.get("id"),
                    path=f"help_content.fallback_topic.sections[{idx}].id",
                    non_empty=True,
                ),
                "title": _require_string(
                    section.get("title"),
                    path=f"help_content.fallback_topic.sections[{idx}].title",
                    non_empty=True,
                ),
                "lines": lines,
            }
        )
    return {
        "id": _require_string(
            topic.get("id"), path="help_content.fallback_topic.id", non_empty=True
        ),
        "title": _require_string(
            topic.get("title"),
            path="help_content.fallback_topic.title",
            non_empty=True,
        ),
        "summary": _require_string(
            topic.get("summary"),
            path="help_content.fallback_topic.summary",
            non_empty=True,
        ),
        "sections": tuple(sections),
    }


def _validate_topic_blocks(raw: object) -> dict[str, dict[str, Any]]:
    blocks = _require_object(raw, path="help_content.topic_blocks")
    out: dict[str, dict[str, Any]] = {}
    for topic_id, raw_entry in blocks.items():
        clean_id = _require_string(
            topic_id, path="help_content.topic_blocks keys", non_empty=True
        )
        entry = _require_object(raw_entry, path=f"help_content.topic_blocks.{clean_id}")
        compact_lines = _string_lines(
            entry.get("compact_lines"),
            path=f"help_content.topic_blocks.{clean_id}.compact_lines",
            allow_empty=True,
        )
        full_lines = _string_lines(
            entry.get("full_lines"),
            path=f"help_content.topic_blocks.{clean_id}.full_lines",
            allow_empty=True,
        )
        if not compact_lines and not full_lines:
            raise HelpTextValidationError(
                f"help_content.topic_blocks.{clean_id} must define compact_lines or full_lines"
            )
        out[clean_id] = {
            "compact_lines": compact_lines,
            "full_lines": full_lines,
            "compact_topic_limit": _require_int(
                entry.get("compact_topic_limit", 0),
                path=f"help_content.topic_blocks.{clean_id}.compact_topic_limit",
                minimum=0,
            ),
            "compact_overflow_line": _require_string(
                entry.get("compact_overflow_line", ""),
                path=f"help_content.topic_blocks.{clean_id}.compact_overflow_line",
            ),
        }
    return out


def _validate_media_placement(raw: object) -> dict[str, dict[str, str]]:
    media = _require_object(raw, path="help_layout.topic_media_placement")
    if not media:
        raise HelpTextValidationError(
            "help_layout.topic_media_placement must not be empty"
        )
    out: dict[str, dict[str, str]] = {}
    for topic_id, raw_entry in media.items():
        clean_id = _require_string(
            topic_id,
            path="help_layout.topic_media_placement keys",
            non_empty=True,
        )
        entry = _require_object(
            raw_entry, path=f"help_layout.topic_media_placement.{clean_id}"
        )
        mode = _require_string(
            entry.get("mode"),
            path=f"help_layout.topic_media_placement.{clean_id}.mode",
            non_empty=True,
        )
        if mode not in {"text", "controls"}:
            raise HelpTextValidationError(
                f"help_layout.topic_media_placement.{clean_id}.mode must be 'text' or 'controls'"
            )
        out[clean_id] = {
            "mode": mode,
            "icon_placement": _require_string(
                entry.get("icon_placement"),
                path=f"help_layout.topic_media_placement.{clean_id}.icon_placement",
                non_empty=True,
            ),
            "image_placement": _require_string(
                entry.get("image_placement"),
                path=f"help_layout.topic_media_placement.{clean_id}.image_placement",
                non_empty=True,
            ),
        }
    if "default" not in out:
        raise HelpTextValidationError(
            "help_layout.topic_media_placement must define a 'default' entry"
        )
    return out


def _validate_layout_payload(payload: dict[str, Any]) -> dict[str, Any]:
    colors = _require_object(payload.get("colors"), path="help_layout.colors")
    thresholds = _require_object(
        payload.get("thresholds"), path="help_layout.thresholds"
    )
    geometry = _require_object(payload.get("geometry"), path="help_layout.geometry")
    compact_adjustments = _require_object(
        geometry.get("compact_adjustments"),
        path="help_layout.geometry.compact_adjustments",
    )
    topic_rules = _require_object(
        payload.get("topic_rules"), path="help_layout.topic_rules"
    )
    controls_helper_layout = _require_object(
        payload.get("controls_helper_layout"),
        path="help_layout.controls_helper_layout",
    )
    header = _require_object(payload.get("header"), path="help_layout.header")
    labels = _require_object(payload.get("labels"), path="help_layout.labels")
    footer_hints = _require_object(
        payload.get("footer_hints"),
        path="help_layout.footer_hints",
    )

    return {
        "version": _require_int(
            payload.get("version"), path="help_layout.version", minimum=1
        ),
        "colors": {
            "bg_top": _rgb_triplet(
                colors.get("bg_top"), path="help_layout.colors.bg_top"
            ),
            "bg_bottom": _rgb_triplet(
                colors.get("bg_bottom"), path="help_layout.colors.bg_bottom"
            ),
            "text": _rgb_triplet(colors.get("text"), path="help_layout.colors.text"),
            "muted": _rgb_triplet(colors.get("muted"), path="help_layout.colors.muted"),
            "highlight": _rgb_triplet(
                colors.get("highlight"), path="help_layout.colors.highlight"
            ),
        },
        "thresholds": {
            "compact_width_threshold": _require_int(
                thresholds.get("compact_width_threshold"),
                path="help_layout.thresholds.compact_width_threshold",
                minimum=1,
            ),
            "compact_height_threshold": _require_int(
                thresholds.get("compact_height_threshold"),
                path="help_layout.thresholds.compact_height_threshold",
                minimum=1,
            ),
        },
        "geometry": {
            "outer_pad": _require_int(
                geometry.get("outer_pad"),
                path="help_layout.geometry.outer_pad",
                minimum=0,
            ),
            "header_extra": _require_int(
                geometry.get("header_extra"),
                path="help_layout.geometry.header_extra",
                minimum=0,
            ),
            "gap": _require_int(
                geometry.get("gap"), path="help_layout.geometry.gap", minimum=0
            ),
            "footer_height": _require_int(
                geometry.get("footer_height"),
                path="help_layout.geometry.footer_height",
                minimum=0,
            ),
            "min_content_height": _require_int(
                geometry.get("min_content_height"),
                path="help_layout.geometry.min_content_height",
                minimum=1,
            ),
            "content_pad_x": _require_int(
                geometry.get("content_pad_x"),
                path="help_layout.geometry.content_pad_x",
                minimum=0,
            ),
            "content_pad_y": _require_int(
                geometry.get("content_pad_y"),
                path="help_layout.geometry.content_pad_y",
                minimum=0,
            ),
            "compact_adjustments": {
                "header_extra_min": _require_int(
                    compact_adjustments.get("header_extra_min"),
                    path="help_layout.geometry.compact_adjustments.header_extra_min",
                    minimum=0,
                ),
                "header_extra_divisor": _require_int(
                    compact_adjustments.get("header_extra_divisor"),
                    path="help_layout.geometry.compact_adjustments.header_extra_divisor",
                    minimum=1,
                ),
                "footer_height_min": _require_int(
                    compact_adjustments.get("footer_height_min"),
                    path="help_layout.geometry.compact_adjustments.footer_height_min",
                    minimum=0,
                ),
                "footer_height_reduce": _require_int(
                    compact_adjustments.get("footer_height_reduce"),
                    path="help_layout.geometry.compact_adjustments.footer_height_reduce",
                    minimum=0,
                ),
                "gap_min": _require_int(
                    compact_adjustments.get("gap_min"),
                    path="help_layout.geometry.compact_adjustments.gap_min",
                    minimum=0,
                ),
                "gap_reduce": _require_int(
                    compact_adjustments.get("gap_reduce"),
                    path="help_layout.geometry.compact_adjustments.gap_reduce",
                    minimum=0,
                ),
                "min_content_height_min": _require_int(
                    compact_adjustments.get("min_content_height_min"),
                    path="help_layout.geometry.compact_adjustments.min_content_height_min",
                    minimum=1,
                ),
                "min_content_height_divisor": _require_int(
                    compact_adjustments.get("min_content_height_divisor"),
                    path="help_layout.geometry.compact_adjustments.min_content_height_divisor",
                    minimum=1,
                ),
            },
        },
        "topic_rules": {
            "controls_topic_id": _require_string(
                topic_rules.get("controls_topic_id"),
                path="help_layout.topic_rules.controls_topic_id",
                non_empty=True,
            ),
            "key_reference_topic_id": _require_string(
                topic_rules.get("key_reference_topic_id"),
                path="help_layout.topic_rules.key_reference_topic_id",
                non_empty=True,
            ),
        },
        "controls_helper_layout": {
            "inset_x": _require_int(
                controls_helper_layout.get("inset_x"),
                path="help_layout.controls_helper_layout.inset_x",
                minimum=0,
            ),
            "bottom_pad_y": _require_int(
                controls_helper_layout.get("bottom_pad_y"),
                path="help_layout.controls_helper_layout.bottom_pad_y",
                minimum=0,
            ),
            "icon_placement": _require_string(
                controls_helper_layout.get("icon_placement"),
                path="help_layout.controls_helper_layout.icon_placement",
                non_empty=True,
            ),
            "image_placement": _require_string(
                controls_helper_layout.get("image_placement"),
                path="help_layout.controls_helper_layout.image_placement",
                non_empty=True,
            ),
        },
        "header": {
            "title": _require_string(
                header.get("title"), path="help_layout.header.title", non_empty=True
            ),
            "subtitle_compact": _require_string(
                header.get("subtitle_compact"),
                path="help_layout.header.subtitle_compact",
                non_empty=True,
            ),
            "subtitle_full": _require_string(
                header.get("subtitle_full"),
                path="help_layout.header.subtitle_full",
                non_empty=True,
            ),
        },
        "labels": {
            "topic": _require_string(
                labels.get("topic"), path="help_layout.labels.topic", non_empty=True
            ),
            "part": _require_string(
                labels.get("part"), path="help_layout.labels.part", non_empty=True
            ),
        },
        "footer_hints": {
            "compact": _require_string(
                footer_hints.get("compact"),
                path="help_layout.footer_hints.compact",
                non_empty=True,
            ),
            "full": _require_string(
                footer_hints.get("full"),
                path="help_layout.footer_hints.full",
                non_empty=True,
            ),
        },
        "topic_media_placement": _validate_media_placement(
            payload.get("topic_media_placement")
        ),
    }


@lru_cache(maxsize=1)
def help_content_registry() -> dict[str, Any]:
    payload = _read_json_object(HELP_CONTENT_FILE)
    return {
        "version": _require_int(
            payload.get("version"), path="help_content.version", minimum=1
        ),
        "topic_blocks": _validate_topic_blocks(payload.get("topic_blocks")),
        "value_templates": _string_map(
            payload.get("value_templates"), path="help_content.value_templates"
        ),
        "action_group_headings": _string_map(
            payload.get("action_group_headings"),
            path="help_content.action_group_headings",
        ),
        "fallback_topic": _validate_fallback_topic(payload.get("fallback_topic")),
    }


@lru_cache(maxsize=1)
def help_layout_registry() -> dict[str, Any]:
    return _validate_layout_payload(_read_json_object(HELP_LAYOUT_FILE))


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
