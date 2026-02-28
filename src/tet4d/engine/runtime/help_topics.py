from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..ui_logic.keybindings_catalog import binding_action_ids
from .settings_schema import read_json_value_or_raise
from .project_config import project_root_path

HELP_CONFIG_DIR = project_root_path() / "config" / "help"
TOPICS_FILE = HELP_CONFIG_DIR / "topics.json"
ACTION_MAP_FILE = HELP_CONFIG_DIR / "action_map.json"

_ALLOWED_LANES = {"quick", "full", "reference"}
_ALLOWED_CONTEXTS = {"launcher", "pause", "gameplay", "keybindings"}
_ALLOWED_DIMENSIONS = {2, 3, 4}


class HelpTopicsValidationError(RuntimeError):
    pass


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = read_json_value_or_raise(path)
    except OSError as exc:
        raise HelpTopicsValidationError(
            f"Failed reading help config file {path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise HelpTopicsValidationError(
            f"Invalid JSON in help config file {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise HelpTopicsValidationError(
            f"Help config file {path} must contain a JSON object"
        )
    return payload


def _clean_string(value: object, *, path: str) -> str:
    if not isinstance(value, str):
        raise HelpTopicsValidationError(f"{path} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise HelpTopicsValidationError(f"{path} must be non-empty")
    return cleaned


def _clean_int(value: object, *, path: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise HelpTopicsValidationError(f"{path} must be an integer")
    if value < minimum:
        raise HelpTopicsValidationError(f"{path} must be >= {minimum}")
    return value


def _validate_topic_lines(raw_lines: object, *, path: str) -> tuple[str, ...]:
    if not isinstance(raw_lines, list) or not raw_lines:
        raise HelpTopicsValidationError(f"{path} must be a non-empty list")
    lines: list[str] = []
    for idx, raw_line in enumerate(raw_lines):
        lines.append(_clean_string(raw_line, path=f"{path}[{idx}]"))
    return tuple(lines)


def _validate_topic_sections(
    raw_sections: object, *, path: str
) -> tuple[dict[str, Any], ...]:
    if not isinstance(raw_sections, list) or not raw_sections:
        raise HelpTopicsValidationError(f"{path} must be a non-empty list")
    section_ids: set[str] = set()
    sections: list[dict[str, Any]] = []
    for idx, raw_section in enumerate(raw_sections):
        item_path = f"{path}[{idx}]"
        if not isinstance(raw_section, dict):
            raise HelpTopicsValidationError(f"{item_path} must be an object")
        section_id = _clean_string(raw_section.get("id"), path=f"{item_path}.id")
        if section_id in section_ids:
            raise HelpTopicsValidationError(
                f"{path} contains duplicate section id: {section_id}"
            )
        section_ids.add(section_id)
        sections.append(
            {
                "id": section_id,
                "title": _clean_string(
                    raw_section.get("title"), path=f"{item_path}.title"
                ),
                "lines": _validate_topic_lines(
                    raw_section.get("lines"), path=f"{item_path}.lines"
                ),
            }
        )
    return tuple(sections)


def _validate_dimensions(raw_dimensions: object, *, path: str) -> tuple[int, ...]:
    if not isinstance(raw_dimensions, list) or not raw_dimensions:
        raise HelpTopicsValidationError(f"{path} must be a non-empty list")
    cleaned: list[int] = []
    seen: set[int] = set()
    for idx, raw_dimension in enumerate(raw_dimensions):
        value = _clean_int(raw_dimension, path=f"{path}[{idx}]", minimum=2)
        if value not in _ALLOWED_DIMENSIONS:
            raise HelpTopicsValidationError(f"{path}[{idx}] must be one of: 2, 3, 4")
        if value in seen:
            raise HelpTopicsValidationError(
                f"{path} contains duplicate dimension: {value}"
            )
        seen.add(value)
        cleaned.append(value)
    return tuple(cleaned)


def _validate_contexts(raw_contexts: object, *, path: str) -> tuple[str, ...]:
    if not isinstance(raw_contexts, list) or not raw_contexts:
        raise HelpTopicsValidationError(f"{path} must be a non-empty list")
    cleaned: list[str] = []
    seen: set[str] = set()
    for idx, raw_context in enumerate(raw_contexts):
        context = _clean_string(raw_context, path=f"{path}[{idx}]").lower()
        if context not in _ALLOWED_CONTEXTS:
            allowed = ", ".join(sorted(_ALLOWED_CONTEXTS))
            raise HelpTopicsValidationError(f"{path}[{idx}] must be one of: {allowed}")
        if context in seen:
            raise HelpTopicsValidationError(
                f"{path} contains duplicate context: {context}"
            )
        seen.add(context)
        cleaned.append(context)
    return tuple(cleaned)


def _validate_topics_payload(
    payload: dict[str, Any],
) -> tuple[int, tuple[dict[str, Any], ...], tuple[str, ...]]:
    version = _clean_int(payload.get("version"), path="topics.version", minimum=1)
    raw_topics = payload.get("topics")
    if not isinstance(raw_topics, list) or not raw_topics:
        raise HelpTopicsValidationError("topics.topics must be a non-empty list")
    topics: list[dict[str, Any]] = []
    topic_ids: list[str] = []
    seen_ids: set[str] = set()
    for idx, raw_topic in enumerate(raw_topics):
        path = f"topics.topics[{idx}]"
        if not isinstance(raw_topic, dict):
            raise HelpTopicsValidationError(f"{path} must be an object")
        topic_id = _clean_string(raw_topic.get("id"), path=f"{path}.id")
        if topic_id in seen_ids:
            raise HelpTopicsValidationError(
                f"topics.topics has duplicate id: {topic_id}"
            )
        seen_ids.add(topic_id)
        lane = _clean_string(raw_topic.get("lane"), path=f"{path}.lane").lower()
        if lane not in _ALLOWED_LANES:
            allowed = ", ".join(sorted(_ALLOWED_LANES))
            raise HelpTopicsValidationError(f"{path}.lane must be one of: {allowed}")
        topics.append(
            {
                "id": topic_id,
                "title": _clean_string(raw_topic.get("title"), path=f"{path}.title"),
                "lane": lane,
                "priority": _clean_int(
                    raw_topic.get("priority"), path=f"{path}.priority", minimum=0
                ),
                "dimensions": _validate_dimensions(
                    raw_topic.get("dimensions"), path=f"{path}.dimensions"
                ),
                "contexts": _validate_contexts(
                    raw_topic.get("contexts"), path=f"{path}.contexts"
                ),
                "summary": _clean_string(
                    raw_topic.get("summary"), path=f"{path}.summary"
                ),
                "sections": _validate_topic_sections(
                    raw_topic.get("sections"), path=f"{path}.sections"
                ),
            }
        )
        topic_ids.append(topic_id)
    return version, tuple(topics), tuple(topic_ids)


def _validate_action_map_payload(
    payload: dict[str, Any],
    *,
    topic_ids: set[str],
) -> tuple[int, str, dict[str, str]]:
    version = _clean_int(payload.get("version"), path="action_map.version", minimum=1)
    default_topic = _clean_string(
        payload.get("default_topic"), path="action_map.default_topic"
    )
    if default_topic not in topic_ids:
        raise HelpTopicsValidationError(
            "action_map.default_topic must reference an existing help topic id"
        )
    raw_action_topics = payload.get("action_topics")
    if not isinstance(raw_action_topics, dict) or not raw_action_topics:
        raise HelpTopicsValidationError(
            "action_map.action_topics must be a non-empty object"
        )

    known_actions = set(binding_action_ids())
    action_topics: dict[str, str] = {}
    for raw_action, raw_topic_id in raw_action_topics.items():
        action = _clean_string(raw_action, path="action_map.action_topics keys")
        topic_id = _clean_string(
            raw_topic_id, path=f"action_map.action_topics.{action}"
        )
        if topic_id not in topic_ids:
            raise HelpTopicsValidationError(
                f"action_map.action_topics.{action} points to unknown topic id: {topic_id}"
            )
        action_topics[action] = topic_id

    unknown_actions = sorted(set(action_topics.keys()) - known_actions)
    if unknown_actions:
        raise HelpTopicsValidationError(
            "action_map.action_topics includes unknown actions: "
            + ", ".join(unknown_actions)
        )

    missing_actions = sorted(known_actions - set(action_topics.keys()))
    if missing_actions:
        raise HelpTopicsValidationError(
            "action_map.action_topics missing mappings for actions: "
            + ", ".join(missing_actions)
        )

    return version, default_topic, action_topics


@lru_cache(maxsize=1)
def help_topics_registry() -> dict[str, Any]:
    payload = _read_json_object(TOPICS_FILE)
    version, topics, topic_ids = _validate_topics_payload(payload)
    topic_index = {topic["id"]: topic for topic in topics}
    return {
        "version": version,
        "topics": topics,
        "topic_ids": topic_ids,
        "topic_index": topic_index,
    }


@lru_cache(maxsize=1)
def help_action_topic_registry() -> dict[str, Any]:
    topics = help_topics_registry()
    topic_ids = set(topics["topic_ids"])
    payload = _read_json_object(ACTION_MAP_FILE)
    version, default_topic, action_topics = _validate_action_map_payload(
        payload, topic_ids=topic_ids
    )
    return {
        "version": version,
        "default_topic": default_topic,
        "action_topics": action_topics,
    }


def help_topic_for_action(action: str) -> str:
    registry = help_action_topic_registry()
    mapping = registry["action_topics"]
    return mapping.get(action, registry["default_topic"])


def normalize_help_context(context_label: str) -> str:
    raw = context_label.strip().lower()
    if raw in _ALLOWED_CONTEXTS:
        return raw
    if "pause" in raw:
        return "pause"
    if "keybinding" in raw or "binding" in raw:
        return "keybindings"
    if "gameplay" in raw or "game" in raw:
        return "gameplay"
    return "launcher"


def help_topics_for_context(
    *, dimension: int, context_label: str
) -> tuple[dict[str, Any], ...]:
    dim = max(2, min(4, int(dimension)))
    context = normalize_help_context(context_label)
    registry = help_topics_registry()
    topics = registry["topics"]
    filtered = [
        topic
        for topic in topics
        if dim in topic["dimensions"] and context in topic["contexts"]
    ]
    if not filtered:
        filtered = [topic for topic in topics if dim in topic["dimensions"]]
    filtered.sort(key=lambda topic: (int(topic["priority"]), topic["id"]))
    return tuple(filtered)


def validate_help_topic_contract() -> tuple[bool, str]:
    try:
        help_topics_registry()
        help_action_topic_registry()
    except HelpTopicsValidationError as exc:
        return False, str(exc)
    return True, "Help topics contract validated"


def clear_help_topic_caches() -> None:
    help_topics_registry.cache_clear()
    help_action_topic_registry.cache_clear()
