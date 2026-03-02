from __future__ import annotations

from functools import lru_cache
from typing import Any

from tet4d.engine.runtime.project_config import project_root_path
from tet4d.engine.runtime.settings_schema import read_json_object_or_raise

from .schema import (
    TutorialLesson,
    TutorialPayload,
    build_tutorial_lesson_map,
    parse_tutorial_payload,
    tutorial_payload_to_dict,
)

_LESSONS_RELATIVE_PATH = "config/tutorial/lessons.json"


def tutorial_lessons_file_path():
    return project_root_path() / _LESSONS_RELATIVE_PATH


@lru_cache(maxsize=1)
def load_tutorial_payload() -> TutorialPayload:
    raw = read_json_object_or_raise(tutorial_lessons_file_path())
    return parse_tutorial_payload(raw)


def tutorial_payload_dict() -> dict[str, Any]:
    return tutorial_payload_to_dict(load_tutorial_payload())


def tutorial_lesson_map() -> dict[str, TutorialLesson]:
    return build_tutorial_lesson_map(load_tutorial_payload())


def tutorial_lesson_ids() -> tuple[str, ...]:
    return tuple(sorted(tutorial_lesson_map().keys()))


def clear_tutorial_content_cache() -> None:
    load_tutorial_payload.cache_clear()
