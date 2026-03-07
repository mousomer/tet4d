from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from typing import Any

from tet4d.engine.runtime.project_config import project_root_path
from tet4d.engine.runtime.settings_schema import (
    as_non_empty_string,
    read_json_object_or_raise,
    require_int,
    require_list,
    require_object,
    sanitize_text,
)

from .schema import (
    TutorialLesson,
    TutorialPayload,
    build_tutorial_lesson_map,
    parse_tutorial_payload,
    tutorial_payload_to_dict,
)

_LESSONS_RELATIVE_PATH = "config/tutorial/lessons.json"
_PLAN_RELATIVE_PATH = "config/tutorial/plan.json"
_VALID_PLAN_MODES = {"2d", "3d", "4d", "all"}
_MAX_PLAN_TOKEN_LENGTH = 128


def tutorial_lessons_file_path():
    return project_root_path() / _LESSONS_RELATIVE_PATH


def tutorial_plan_file_path():
    return project_root_path() / _PLAN_RELATIVE_PATH


def _plan_text(raw: object, *, path: str, max_length: int = _MAX_PLAN_TOKEN_LENGTH) -> str:
    value = as_non_empty_string(raw, path=path)
    cleaned = sanitize_text(value, max_length=max_length).strip()
    if not cleaned:
        raise RuntimeError(f"{path} must contain printable text")
    return cleaned


def _parse_plan_modes(raw: object, *, path: str) -> list[str]:
    modes_raw = require_list(raw, path=path)
    out: list[str] = []
    for index, mode_raw in enumerate(modes_raw):
        mode = _plan_text(mode_raw, path=f"{path}[{index}]", max_length=8).lower()
        if mode not in _VALID_PLAN_MODES:
            raise RuntimeError(
                f"{path}[{index}] must be one of: {sorted(_VALID_PLAN_MODES)}"
            )
        out.append(mode)
    if not out:
        raise RuntimeError(f"{path} must not be empty")
    return out


def _parse_plan_stage(raw: object, *, path: str) -> dict[str, Any]:
    stage = require_object(raw, path=path)
    stage_id = _plan_text(stage.get("stage_id"), path=f"{path}.stage_id").lower()
    order = require_int(stage.get("order"), path=f"{path}.order", min_value=1)
    title = _plan_text(stage.get("title"), path=f"{path}.title", max_length=160)
    objective = _plan_text(
        stage.get("objective"),
        path=f"{path}.objective",
        max_length=320,
    )
    applies_to = _parse_plan_modes(stage.get("applies_to"), path=f"{path}.applies_to")
    kind = _plan_text(stage.get("kind", "action"), path=f"{path}.kind", max_length=24)
    action_id_raw = stage.get("action_id")
    action_id: str | None = None
    if action_id_raw is not None:
        action_id = _plan_text(
            action_id_raw,
            path=f"{path}.action_id",
            max_length=96,
        ).lower()
    if kind.lower() == "action" and not action_id:
        raise RuntimeError(f"{path}.action_id is required for action stages")
    return {
        "stage_id": stage_id,
        "order": order,
        "title": title,
        "objective": objective,
        "applies_to": applies_to,
        "kind": kind.lower(),
        "action_id": action_id,
    }


def _parse_tutorial_plan_payload(raw: dict[str, Any]) -> dict[str, Any]:
    root = require_object(raw, path="tutorial_plan")
    schema_version = require_int(
        root.get("schema_version"),
        path="tutorial_plan.schema_version",
        min_value=1,
    )
    plan_id = _plan_text(root.get("plan_id"), path="tutorial_plan.plan_id").lower()
    title = _plan_text(root.get("title"), path="tutorial_plan.title", max_length=160)
    description = _plan_text(
        root.get("description"),
        path="tutorial_plan.description",
        max_length=512,
    )
    stages_raw = require_list(root.get("stages"), path="tutorial_plan.stages")
    if not stages_raw:
        raise RuntimeError("tutorial_plan.stages must not be empty")
    stages: list[dict[str, Any]] = []
    seen_stage_ids: set[str] = set()
    last_order = 0
    for index, stage_raw in enumerate(stages_raw):
        stage = _parse_plan_stage(
            stage_raw,
            path=f"tutorial_plan.stages[{index}]",
        )
        stage_id = str(stage["stage_id"])
        if stage_id in seen_stage_ids:
            raise RuntimeError(f"tutorial_plan.stages duplicate stage_id: {stage_id}")
        seen_stage_ids.add(stage_id)
        order = int(stage["order"])
        if order <= last_order:
            raise RuntimeError("tutorial_plan.stages must be strictly ordered by 'order'")
        last_order = order
        stages.append(stage)
    return {
        "schema_version": schema_version,
        "plan_id": plan_id,
        "title": title,
        "description": description,
        "stages": stages,
    }


@lru_cache(maxsize=1)
def load_tutorial_payload() -> TutorialPayload:
    raw = read_json_object_or_raise(tutorial_lessons_file_path())
    return parse_tutorial_payload(raw)


@lru_cache(maxsize=1)
def load_tutorial_plan_payload() -> dict[str, Any]:
    raw = read_json_object_or_raise(tutorial_plan_file_path())
    return _parse_tutorial_plan_payload(raw)


def tutorial_payload_dict() -> dict[str, Any]:
    return tutorial_payload_to_dict(load_tutorial_payload())


def tutorial_plan_payload_dict() -> dict[str, Any]:
    return deepcopy(load_tutorial_plan_payload())


def tutorial_lesson_map() -> dict[str, TutorialLesson]:
    return build_tutorial_lesson_map(load_tutorial_payload())


def tutorial_lesson_ids() -> tuple[str, ...]:
    return tuple(sorted(tutorial_lesson_map().keys()))


def tutorial_board_dims_for_mode(mode: str) -> tuple[int, ...]:
    clean_mode = _plan_text(mode, path="tutorial.mode", max_length=8).lower()
    if clean_mode not in {"2d", "3d", "4d"}:
        raise RuntimeError("tutorial.mode must be one of: 2d, 3d, 4d")
    payload = load_tutorial_payload()
    return tuple(int(value) for value in payload.board_profiles.dims_for_mode(clean_mode))


def clear_tutorial_content_cache() -> None:
    load_tutorial_payload.cache_clear()
    load_tutorial_plan_payload.cache_clear()
