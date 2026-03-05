from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tet4d.engine.runtime.settings_schema import (
    as_non_empty_string,
    require_int,
    require_list,
    require_object,
    sanitize_text,
)

_VALID_MODES = {"2d", "3d", "4d"}
_VALID_LOGIC = {"all", "any"}
_MAX_ID_LENGTH = 96
_MAX_TITLE_LENGTH = 160
_MAX_TEXT_LENGTH = 320
_MAX_TOKEN_LENGTH = 128


@dataclass(frozen=True)
class TutorialStepUI:
    text: str
    hint: str | None
    highlights: tuple[str, ...]
    key_prompts: tuple[str, ...]


@dataclass(frozen=True)
class TutorialStepGating:
    allow: tuple[str, ...]
    deny: tuple[str, ...]


@dataclass(frozen=True)
class TutorialStepSetup:
    camera_preset: str | None
    spawn_piece: str | None
    starter_piece_id: str | None
    board_preset: str | None
    rng_seed: int | None
    spawn_min_visible_layer: int | None
    bottom_layers_min: int | None
    bottom_layers_max: int | None
    overlay_start_percent: int | None
    overlay_target_percent: int | None


@dataclass(frozen=True)
class TutorialCompletionCondition:
    events: tuple[str, ...]
    predicates: tuple[str, ...]
    logic: str
    event_count_required: int


@dataclass(frozen=True)
class TutorialStep:
    step_id: str
    ui: TutorialStepUI
    gating: TutorialStepGating
    setup: TutorialStepSetup
    complete_when: TutorialCompletionCondition


@dataclass(frozen=True)
class TutorialLesson:
    lesson_id: str
    title: str
    mode: str
    steps: tuple[TutorialStep, ...]


@dataclass(frozen=True)
class TutorialPayload:
    schema_version: int
    lessons: tuple[TutorialLesson, ...]


def _clean_required_text(
    raw: object,
    *,
    path: str,
    max_length: int,
    normalize_lower: bool = False,
) -> str:
    text = as_non_empty_string(raw, path=path)
    text = sanitize_text(text, max_length=max_length).strip()
    if not text:
        raise RuntimeError(f"{path} must contain at least one printable character")
    return text.lower() if normalize_lower else text


def _clean_optional_text(raw: object, *, path: str, max_length: int) -> str | None:
    if raw is None:
        return None
    text = _clean_required_text(raw, path=path, max_length=max_length)
    return text or None


def _parse_token_list(
    raw: object,
    *,
    path: str,
    normalize_lower: bool = True,
) -> tuple[str, ...]:
    values = require_list(raw, path=path)
    out: list[str] = []
    for index, value in enumerate(values):
        out.append(
            _clean_required_text(
                value,
                path=f"{path}[{index}]",
                max_length=_MAX_TOKEN_LENGTH,
                normalize_lower=normalize_lower,
            )
        )
    return tuple(out)


def _parse_ui(raw: object, *, path: str) -> TutorialStepUI:
    ui_obj = require_object(raw, path=path)
    text = _clean_required_text(
        ui_obj.get("text"),
        path=f"{path}.text",
        max_length=_MAX_TEXT_LENGTH,
    )
    hint = _clean_optional_text(
        ui_obj.get("hint"),
        path=f"{path}.hint",
        max_length=_MAX_TEXT_LENGTH,
    )
    highlights = _parse_token_list(
        ui_obj.get("highlights", []),
        path=f"{path}.highlights",
        normalize_lower=True,
    )
    key_prompts = _parse_token_list(
        ui_obj.get("key_prompts", []),
        path=f"{path}.key_prompts",
        normalize_lower=True,
    )
    if len(key_prompts) != 1:
        raise RuntimeError(f"{path}.key_prompts must contain exactly one action")
    return TutorialStepUI(
        text=text,
        hint=hint,
        highlights=highlights,
        key_prompts=key_prompts,
    )


def _parse_gating(raw: object, *, path: str) -> TutorialStepGating:
    if raw is None:
        return TutorialStepGating(allow=(), deny=())
    gating_obj = require_object(raw, path=path)
    allow = _parse_token_list(
        gating_obj.get("allow", []),
        path=f"{path}.allow",
        normalize_lower=True,
    )
    deny = _parse_token_list(
        gating_obj.get("deny", []),
        path=f"{path}.deny",
        normalize_lower=True,
    )
    return TutorialStepGating(allow=allow, deny=deny)


def _parse_setup(raw: object, *, path: str) -> TutorialStepSetup:
    if raw is None:
        return TutorialStepSetup(
            camera_preset=None,
            spawn_piece=None,
            starter_piece_id=None,
            board_preset=None,
            rng_seed=None,
            spawn_min_visible_layer=None,
            bottom_layers_min=None,
            bottom_layers_max=None,
            overlay_start_percent=None,
            overlay_target_percent=None,
        )
    setup_obj = require_object(raw, path=path)
    camera_preset = _clean_optional_text(
        setup_obj.get("camera_preset"),
        path=f"{path}.camera_preset",
        max_length=_MAX_TOKEN_LENGTH,
    )
    spawn_piece = _clean_optional_text(
        setup_obj.get("spawn_piece"),
        path=f"{path}.spawn_piece",
        max_length=_MAX_TOKEN_LENGTH,
    )
    starter_piece_id = _clean_optional_text(
        setup_obj.get("starter_piece_id"),
        path=f"{path}.starter_piece_id",
        max_length=_MAX_TOKEN_LENGTH,
    )
    board_preset = _clean_optional_text(
        setup_obj.get("board_preset"),
        path=f"{path}.board_preset",
        max_length=_MAX_TOKEN_LENGTH,
    )
    rng_seed_raw = setup_obj.get("rng_seed")
    rng_seed = None
    if rng_seed_raw is not None:
        rng_seed = require_int(rng_seed_raw, path=f"{path}.rng_seed")
    spawn_min_visible_layer_raw = setup_obj.get("spawn_min_visible_layer")
    spawn_min_visible_layer = None
    if spawn_min_visible_layer_raw is not None:
        spawn_min_visible_layer = require_int(
            spawn_min_visible_layer_raw,
            path=f"{path}.spawn_min_visible_layer",
            min_value=0,
        )
    bottom_layers_min_raw = setup_obj.get("bottom_layers_min")
    bottom_layers_min = None
    if bottom_layers_min_raw is not None:
        bottom_layers_min = require_int(
            bottom_layers_min_raw,
            path=f"{path}.bottom_layers_min",
            min_value=0,
        )
    bottom_layers_max_raw = setup_obj.get("bottom_layers_max")
    bottom_layers_max = None
    if bottom_layers_max_raw is not None:
        bottom_layers_max = require_int(
            bottom_layers_max_raw,
            path=f"{path}.bottom_layers_max",
            min_value=0,
        )
    if (
        bottom_layers_min is not None
        and bottom_layers_max is not None
        and bottom_layers_max < bottom_layers_min
    ):
        raise RuntimeError(
            f"{path}.bottom_layers_max must be >= {path}.bottom_layers_min"
        )
    overlay_start_percent_raw = setup_obj.get("overlay_start_percent")
    overlay_start_percent = None
    if overlay_start_percent_raw is not None:
        overlay_start_percent = require_int(
            overlay_start_percent_raw,
            path=f"{path}.overlay_start_percent",
            min_value=0,
            max_value=100,
        )
    overlay_target_percent_raw = setup_obj.get("overlay_target_percent")
    overlay_target_percent = None
    if overlay_target_percent_raw is not None:
        overlay_target_percent = require_int(
            overlay_target_percent_raw,
            path=f"{path}.overlay_target_percent",
            min_value=0,
            max_value=100,
        )
    return TutorialStepSetup(
        camera_preset=camera_preset,
        spawn_piece=spawn_piece,
        starter_piece_id=starter_piece_id,
        board_preset=board_preset,
        rng_seed=rng_seed,
        spawn_min_visible_layer=spawn_min_visible_layer,
        bottom_layers_min=bottom_layers_min,
        bottom_layers_max=bottom_layers_max,
        overlay_start_percent=overlay_start_percent,
        overlay_target_percent=overlay_target_percent,
    )


def _parse_complete_when(raw: object, *, path: str) -> TutorialCompletionCondition:
    completion_obj = require_object(raw, path=path)
    events = _parse_token_list(
        completion_obj.get("events", []),
        path=f"{path}.events",
        normalize_lower=True,
    )
    predicates = _parse_token_list(
        completion_obj.get("predicates", []),
        path=f"{path}.predicates",
        normalize_lower=True,
    )
    logic = _clean_required_text(
        completion_obj.get("logic", "all"),
        path=f"{path}.logic",
        max_length=16,
        normalize_lower=True,
    )
    event_count_required = require_int(
        completion_obj.get("event_count_required", 1),
        path=f"{path}.event_count_required",
        min_value=1,
        max_value=9,
    )
    if logic not in _VALID_LOGIC:
        raise RuntimeError(f"{path}.logic must be one of: all, any")
    if len(events) > 9:
        raise RuntimeError(f"{path}.events must contain at most 9 actions")
    if not events and not predicates:
        raise RuntimeError(
            f"{path} must define at least one event or predicate requirement"
        )
    return TutorialCompletionCondition(
        events=events,
        predicates=predicates,
        logic=logic,
        event_count_required=event_count_required,
    )


def _parse_step(raw: object, *, path: str) -> TutorialStep:
    step_obj = require_object(raw, path=path)
    step_id = _clean_required_text(
        step_obj.get("id"),
        path=f"{path}.id",
        max_length=_MAX_ID_LENGTH,
        normalize_lower=True,
    )
    return TutorialStep(
        step_id=step_id,
        ui=_parse_ui(step_obj.get("ui"), path=f"{path}.ui"),
        gating=_parse_gating(step_obj.get("gating"), path=f"{path}.gating"),
        setup=_parse_setup(step_obj.get("setup"), path=f"{path}.setup"),
        complete_when=_parse_complete_when(
            step_obj.get("complete_when"),
            path=f"{path}.complete_when",
        ),
    )


def _parse_lesson(raw: object, *, path: str) -> TutorialLesson:
    lesson_obj = require_object(raw, path=path)
    lesson_id = _clean_required_text(
        lesson_obj.get("lesson_id"),
        path=f"{path}.lesson_id",
        max_length=_MAX_ID_LENGTH,
        normalize_lower=True,
    )
    title = _clean_required_text(
        lesson_obj.get("title"),
        path=f"{path}.title",
        max_length=_MAX_TITLE_LENGTH,
    )
    mode = _clean_required_text(
        lesson_obj.get("mode"),
        path=f"{path}.mode",
        max_length=8,
        normalize_lower=True,
    )
    if mode not in _VALID_MODES:
        raise RuntimeError(f"{path}.mode must be one of: 2d, 3d, 4d")
    steps_raw = require_list(lesson_obj.get("steps"), path=f"{path}.steps")
    if not steps_raw:
        raise RuntimeError(f"{path}.steps must not be empty")
    parsed_steps: list[TutorialStep] = []
    seen_step_ids: set[str] = set()
    for step_index, step_raw in enumerate(steps_raw):
        step = _parse_step(step_raw, path=f"{path}.steps[{step_index}]")
        if step.step_id in seen_step_ids:
            raise RuntimeError(f"{path}.steps has duplicate id: {step.step_id}")
        seen_step_ids.add(step.step_id)
        parsed_steps.append(step)
    return TutorialLesson(
        lesson_id=lesson_id,
        title=title,
        mode=mode,
        steps=tuple(parsed_steps),
    )


def parse_tutorial_payload(payload: dict[str, Any]) -> TutorialPayload:
    root = require_object(payload, path="tutorial")
    schema_version = require_int(
        root.get("schema_version"),
        path="tutorial.schema_version",
        min_value=1,
    )
    lessons_raw = require_list(root.get("lessons"), path="tutorial.lessons")
    if not lessons_raw:
        raise RuntimeError("tutorial.lessons must not be empty")
    parsed_lessons: list[TutorialLesson] = []
    seen_lesson_ids: set[str] = set()
    for lesson_index, lesson_raw in enumerate(lessons_raw):
        lesson = _parse_lesson(lesson_raw, path=f"tutorial.lessons[{lesson_index}]")
        if lesson.lesson_id in seen_lesson_ids:
            raise RuntimeError(
                "tutorial.lessons contains duplicate lesson_id: "
                + lesson.lesson_id
            )
        seen_lesson_ids.add(lesson.lesson_id)
        parsed_lessons.append(lesson)
    return TutorialPayload(schema_version=schema_version, lessons=tuple(parsed_lessons))


def build_tutorial_lesson_map(payload: TutorialPayload) -> dict[str, TutorialLesson]:
    return {lesson.lesson_id: lesson for lesson in payload.lessons}


def _setup_payload_for_step(step: TutorialStep) -> dict[str, Any]:
    setup_fields = (
        ("camera_preset", step.setup.camera_preset),
        ("spawn_piece", step.setup.spawn_piece),
        ("starter_piece_id", step.setup.starter_piece_id),
        ("board_preset", step.setup.board_preset),
        ("rng_seed", step.setup.rng_seed),
        ("spawn_min_visible_layer", step.setup.spawn_min_visible_layer),
        ("bottom_layers_min", step.setup.bottom_layers_min),
        ("bottom_layers_max", step.setup.bottom_layers_max),
        ("overlay_start_percent", step.setup.overlay_start_percent),
        ("overlay_target_percent", step.setup.overlay_target_percent),
    )
    payload: dict[str, Any] = {}
    for key, value in setup_fields:
        if value is not None:
            payload[key] = value
    return payload


def _step_payload(step: TutorialStep) -> dict[str, Any]:
    return {
        "id": step.step_id,
        "ui": {
            "text": step.ui.text,
            "hint": step.ui.hint,
            "highlights": list(step.ui.highlights),
            "key_prompts": list(step.ui.key_prompts),
        },
        "gating": {
            "allow": list(step.gating.allow),
            "deny": list(step.gating.deny),
        },
        "setup": _setup_payload_for_step(step),
        "complete_when": {
            "events": list(step.complete_when.events),
            "predicates": list(step.complete_when.predicates),
            "logic": step.complete_when.logic,
            "event_count_required": int(step.complete_when.event_count_required),
        },
    }


def tutorial_payload_to_dict(payload: TutorialPayload) -> dict[str, Any]:
    lessons: list[dict[str, Any]] = []
    for lesson in payload.lessons:
        steps = [_step_payload(step) for step in lesson.steps]
        lessons.append(
            {
                "lesson_id": lesson.lesson_id,
                "title": lesson.title,
                "mode": lesson.mode,
                "steps": steps,
            }
        )
    return {"schema_version": payload.schema_version, "lessons": lessons}
