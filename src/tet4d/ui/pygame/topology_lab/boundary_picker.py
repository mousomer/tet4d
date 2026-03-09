from __future__ import annotations

from .common import TopologyLabHitTarget
from .scene_state import (
    TOOL_CREATE,
    TOOL_EDIT,
    TOOL_INSPECT,
    TOOL_NAVIGATE,
    TOOL_PLAY,
    TOOL_PROBE,
    TOOL_SANDBOX,
    TopologyLabState,
    set_active_tool,
    uses_general_explorer_editor,
)


def pick_target(
    targets: list[TopologyLabHitTarget] | None,
    pos: tuple[int, int],
) -> TopologyLabHitTarget | None:
    for target in reversed(targets or []):
        if target.rect.collidepoint(pos):
            return target
    return None


_BOUNDARY_LABELS = tuple(f"{axis}{side}" for axis in "xyzw" for side in ("-", "+"))


def _select_boundary_only(state: TopologyLabState, boundary_index: int) -> None:
    state.selected_boundary_index = boundary_index


def _set_draft_target(
    state: TopologyLabState, *, source_index: int, target_index: int
) -> None:
    assert state.explorer_draft is not None
    state.explorer_draft = state.explorer_draft.__class__(
        slot_index=state.explorer_draft.slot_index,
        source_index=source_index,
        target_index=target_index,
        permutation_index=state.explorer_draft.permutation_index,
        signs=state.explorer_draft.signs,
    )


def _finish_create_pick(state: TopologyLabState, boundary_index: int) -> str:
    assert state.pending_source_index is not None
    _set_draft_target(
        state,
        source_index=state.pending_source_index,
        target_index=boundary_index,
    )
    state.selected_boundary_index = boundary_index
    state.pending_source_index = None
    set_active_tool(state, TOOL_EDIT)
    return "Target boundary selected; editing transform"


def _handle_create_pick(state: TopologyLabState, boundary_index: int) -> str:
    if state.pending_source_index is None:
        state.pending_source_index = boundary_index
        state.selected_boundary_index = boundary_index
        return "Source boundary selected"
    return _finish_create_pick(state, boundary_index)


def _glue_boundary_indexes(glue) -> tuple[int, int]:
    source_index = glue.source.axis * 2 + (1 if glue.source.side == "+" else 0)
    target_index = glue.target.axis * 2 + (1 if glue.target.side == "+" else 0)
    return source_index, target_index


def _select_existing_glue(
    state: TopologyLabState,
    *,
    glue_index: int,
    glue,
    source_index: int,
    target_index: int,
) -> str:
    assert state.explorer_draft is not None
    state.selected_glue_id = glue.glue_id
    state.highlighted_glue_id = glue.glue_id
    state.explorer_draft = state.explorer_draft.__class__(
        slot_index=glue_index,
        source_index=source_index,
        target_index=target_index,
        permutation_index=state.explorer_draft.permutation_index,
        signs=state.explorer_draft.signs,
    )
    return f"Editing {glue.glue_id}"


def _handle_edit_pick(state: TopologyLabState, boundary_index: int) -> str | None:
    _select_boundary_only(state, boundary_index)
    if state.explorer_profile is None:
        return None
    for index, glue in enumerate(state.explorer_profile.gluings):
        source_index, target_index = _glue_boundary_indexes(glue)
        if boundary_index in {source_index, target_index}:
            return _select_existing_glue(
                state,
                glue_index=index,
                glue=glue,
                source_index=source_index,
                target_index=target_index,
            )
    return "No active gluing on selected boundary"


def update_hover_target(
    state: TopologyLabState, target: TopologyLabHitTarget | None
) -> None:
    state.hovered_boundary_index = None
    state.hovered_glue_id = None
    if target is None:
        return
    if target.kind == "boundary_pick":
        state.hovered_boundary_index = int(target.value)
    elif target.kind == "glue_pick":
        state.hovered_glue_id = str(target.value)


def apply_boundary_pick(state: TopologyLabState, boundary_index: int) -> str | None:
    if not uses_general_explorer_editor(state) or state.explorer_draft is None:
        return None
    state.hovered_boundary_index = boundary_index
    if state.active_tool == TOOL_NAVIGATE:
        return None
    if state.active_tool == TOOL_INSPECT:
        _select_boundary_only(state, boundary_index)
        return f"Boundary {_BOUNDARY_LABELS[boundary_index]} selected"
    if state.active_tool == TOOL_CREATE:
        return _handle_create_pick(state, boundary_index)
    if state.active_tool == TOOL_EDIT:
        return _handle_edit_pick(state, boundary_index)
    if state.active_tool in {TOOL_PROBE, TOOL_SANDBOX, TOOL_PLAY}:
        _select_boundary_only(state, boundary_index)
    return None


def apply_boundary_edit_pick(state: TopologyLabState, boundary_index: int) -> str | None:
    if not uses_general_explorer_editor(state) or state.explorer_draft is None:
        return None
    state.hovered_boundary_index = boundary_index
    if state.explorer_profile is not None:
        for index, glue in enumerate(state.explorer_profile.gluings):
            source_index, target_index = _glue_boundary_indexes(glue)
            if boundary_index in {source_index, target_index}:
                set_active_tool(state, TOOL_EDIT)
                return _select_existing_glue(
                    state,
                    glue_index=index,
                    glue=glue,
                    source_index=source_index,
                    target_index=target_index,
                )
    set_active_tool(state, TOOL_CREATE)
    return _handle_create_pick(state, boundary_index)


def apply_glue_pick(state: TopologyLabState, glue_id: str) -> str | None:
    if not uses_general_explorer_editor(state) or state.explorer_profile is None or state.explorer_draft is None:
        return None
    for index, glue in enumerate(state.explorer_profile.gluings):
        if glue.glue_id != glue_id:
            continue
        source_index, target_index = _glue_boundary_indexes(glue)
        state.selected_glue_id = glue_id
        state.highlighted_glue_id = glue_id
        state.selected_boundary_index = source_index
        state.explorer_draft = state.explorer_draft.__class__(
            slot_index=index,
            source_index=source_index,
            target_index=target_index,
            permutation_index=state.explorer_draft.permutation_index,
            signs=state.explorer_draft.signs,
        )
        set_active_tool(state, TOOL_EDIT)
        return f"Editing {glue_id}"
    return None


__all__ = [
    "apply_boundary_edit_pick",
    "apply_boundary_pick",
    "apply_glue_pick",
    "pick_target",
    "update_hover_target",
]

