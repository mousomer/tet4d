from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .runtime.help_topics_storage import load_json_file
from .runtime.project_config import project_root_path

HELP_TEXT_FILE = project_root_path() / "docs" / "help" / "runtime_help_text.json"


class HelpTextValidationError(RuntimeError):
    pass


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = load_json_file(path)
    except OSError as exc:
        raise HelpTextValidationError(f"Failed reading help text file {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise HelpTextValidationError(f"Invalid JSON in help text file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise HelpTextValidationError(f"Help text file {path} must contain a JSON object")
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
    return tuple(_clean_string(item, path=f"{path}[{idx}]") for idx, item in enumerate(raw_lines))


def _validate_fallback_topic(raw: object) -> dict[str, Any]:
    path = "help_text.fallback_topic"
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
                "id": _clean_non_empty_string(raw_section.get("id"), path=f"{section_path}.id"),
                "title": _clean_non_empty_string(
                    raw_section.get("title"), path=f"{section_path}.title"
                ),
                "lines": lines,
            }
        )
    return {
        "id": _clean_non_empty_string(raw.get("id"), path=f"{path}.id"),
        "title": _clean_non_empty_string(raw.get("title"), path=f"{path}.title"),
        "summary": _clean_non_empty_string(raw.get("summary"), path=f"{path}.summary"),
        "sections": tuple(sections),
    }


def _validate_topic_blocks(raw_blocks: object) -> dict[str, dict[str, Any]]:
    if not isinstance(raw_blocks, dict):
        raise HelpTextValidationError("help_text.topic_blocks must be an object")
    validated: dict[str, dict[str, Any]] = {}
    for topic_id, raw_entry in raw_blocks.items():
        entry_path = f"help_text.topic_blocks.{topic_id}"
        topic_key = _clean_non_empty_string(topic_id, path="help_text.topic_blocks keys")
        if not isinstance(raw_entry, dict):
            raise HelpTextValidationError(f"{entry_path} must be an object")
        compact_lines = _validate_lines(raw_entry.get("compact_lines"), path=f"{entry_path}.compact_lines")
        full_lines = _validate_lines(raw_entry.get("full_lines"), path=f"{entry_path}.full_lines")
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


@lru_cache(maxsize=1)
def help_text_registry() -> dict[str, Any]:
    payload = _read_json_object(HELP_TEXT_FILE)
    version = _clean_int(payload.get("version"), path="help_text.version", minimum=1)
    topic_blocks = _validate_topic_blocks(payload.get("topic_blocks"))
    value_templates = _validate_string_map(
        payload.get("value_templates"), path="help_text.value_templates"
    )
    action_group_headings = _validate_string_map(
        payload.get("action_group_headings"), path="help_text.action_group_headings"
    )
    fallback_topic = _validate_fallback_topic(payload.get("fallback_topic"))
    return {
        "version": version,
        "topic_blocks": topic_blocks,
        "value_templates": value_templates,
        "action_group_headings": action_group_headings,
        "fallback_topic": fallback_topic,
    }


def help_topic_block_lines(topic_id: str, *, compact: bool) -> tuple[str, ...]:
    blocks = help_text_registry()["topic_blocks"]
    raw_id = str(topic_id).strip()
    if not raw_id or raw_id not in blocks:
        return tuple()
    entry = blocks[raw_id]
    lines = entry["compact_lines"] if compact else entry["full_lines"]
    if lines:
        return lines
    return entry["full_lines"] if compact else entry["compact_lines"]


def help_topic_compact_limit(topic_id: str) -> int:
    blocks = help_text_registry()["topic_blocks"]
    raw_id = str(topic_id).strip()
    if not raw_id or raw_id not in blocks:
        return 0
    return int(blocks[raw_id]["compact_topic_limit"])


def help_topic_compact_overflow_line(topic_id: str) -> str:
    blocks = help_text_registry()["topic_blocks"]
    raw_id = str(topic_id).strip()
    if not raw_id or raw_id not in blocks:
        return ""
    return str(blocks[raw_id]["compact_overflow_line"])


def help_value_template(name: str, *, default: str = "") -> str:
    templates = help_text_registry()["value_templates"]
    key = str(name).strip()
    if not key:
        return default
    return str(templates.get(key, default))


def help_action_group_heading(group: str) -> str:
    headings = help_text_registry()["action_group_headings"]
    key = str(group).strip()
    if not key:
        return ""
    return str(headings.get(key, ""))


def help_fallback_topic() -> dict[str, Any]:
    topic = help_text_registry()["fallback_topic"]
    sections = tuple(
        {"id": section["id"], "title": section["title"], "lines": tuple(section["lines"])}
        for section in topic["sections"]
    )
    return {
        "id": topic["id"],
        "title": topic["title"],
        "summary": topic["summary"],
        "sections": sections,
    }


def clear_help_text_cache() -> None:
    help_text_registry.cache_clear()
