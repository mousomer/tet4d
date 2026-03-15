from __future__ import annotations

from .common import TopologyLabHitTarget
from .scene_state import (
    TOOL_EDIT,
    TopologyLabState,
    current_explorer_draft,
    current_explorer_profile,
    set_active_tool,
    set_highlighted_glue_id,
    set_selected_boundary_index,
    set_selected_glue_id,
    tool_is_edit,
    tool_is_inspect,
    update_explorer_draft,
    uses_general_explorer_editor,
)


def pick_target(
    targets: list[TopologyLabHitTarget] | None,
    pos: tuple[int, int],
) -> TopologyLabHitTarget | None:
    priority = {
        "tool_mode": 0,
        "action": 1,
        "row_step": 2,
        "projection_cell": 3,
        "glue_pick": 4,
        "boundary_pick": 5,
        "projection_panel": 6,
        "row_select": 7,
    }
    matches = [target for target in (targets or []) if target.rect.collidepoint(pos)]
    if not matches:
        return None
    ordered = sorted(
        matches,
        key=lambda target: (
            priority.get(target.kind, 6),
            target.rect.width * target.rect.height,
            abs(target.rect.centerx - pos[0]) + abs(target.rect.centery - pos[1]),
        ),
    )
    return ordered[0]


_BOUNDARY_LABELS = tuple(f"{axis}{side}" for axis in "xyzw" for side in ("-", "+"))


def _select_boundary_only(state: TopologyLabState, boundary_index: int) -> None:
    set_selected_boundary_index(state, boundary_index)


def _set_draft_target(
    state: TopologyLabState, *, source_index: int, target_index: int
) -> None:
    draft = current_explorer_draft(state)
    assert draft is not None
    update_explorer_draft(
        state,
        slot_index=draft.slot_index,
        source_index=source_index,
        target_index=target_index,
        permutation_index=draft.permutation_index,
        signs=draft.signs,
    )


def _finish_create_pick(state: TopologyLabState, boundary_index: int) -> str:
    assert state.pending_source_index is not None
    _set_draft_target(
        state,
        source_index=state.pending_source_index,
        target_index=boundary_index,
    )
    set_selected_boundary_index(state, boundary_index)
    state.pending_source_index = None
    set_active_tool(state, TOOL_EDIT)
    return "Target boundary selected; editing transform"


def _glue_boundary_indexes(glue) -> tuple[int, int]:
    source_index = glue.source.axis * 2 + (1 if glue.source.side == "+" else 0)
    target_index = glue.target.axis * 2 + (1 if glue.target.side == "+" else 0)
    return source_index, target_index


def _select_existing_glue(
    state: TopologyLabState,
    *,
    boundary_index: int,
    glue_index: int,
    glue,
    source_index: int,
    target_index: int,
) -> str:
    draft = current_explorer_draft(state)
    assert draft is not None
    set_selected_boundary_index(state, boundary_index)
    set_selected_glue_id(state, glue.glue_id)
    set_highlighted_glue_id(state, glue.glue_id)
    update_explorer_draft(
        state,
        slot_index=glue_index,
        source_index=source_index,
        target_index=target_index,
        permutation_index=draft.permutation_index,
        signs=draft.signs,
    )
    return f"Editing {glue.glue_id}"


def _handle_edit_pick(state: TopologyLabState, boundary_index: int) -> str | None:
    _select_boundary_only(state, boundary_index)
    if state.pending_source_index is not None:
        return _finish_create_pick(state, boundary_index)
    profile = current_explorer_profile(state)
    if profile is None:
        return None
    for index, glue in enumerate(profile.gluings):
        source_index, target_index = _glue_boundary_indexes(glue)
        if boundary_index in {source_index, target_index}:
            return _select_existing_glue(
                state,
                boundary_index=boundary_index,
                glue_index=index,
                glue=glue,
                source_index=source_index,
                target_index=target_index,
            )
    state.pending_source_index = boundary_index
    set_selected_glue_id(state, None)
    set_highlighted_glue_id(state, None)
    return "Source boundary selected"


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
    if not uses_general_explorer_editor(state) or current_explorer_draft(state) is None:
        return None
    state.hovered_boundary_index = boundary_index
    if tool_is_edit(state.active_tool):
        return _handle_edit_pick(state, boundary_index)
    if tool_is_inspect(state.active_tool):
        _select_boundary_only(state, boundary_index)
        return f"Boundary {_BOUNDARY_LABELS[boundary_index]} selected"
    return None


def apply_boundary_edit_pick(
    state: TopologyLabState, boundary_index: int
) -> str | None:
    if not uses_general_explorer_editor(state) or current_explorer_draft(state) is None:
        return None
    if not tool_is_edit(state.active_tool):
        return "Switch to Edit to change seams"
    state.hovered_boundary_index = boundary_index
    profile = current_explorer_profile(state)
    if profile is not None:
        for index, glue in enumerate(profile.gluings):
            source_index, target_index = _glue_boundary_indexes(glue)
            if boundary_index in {source_index, target_index}:
                set_active_tool(state, TOOL_EDIT)
                return _select_existing_glue(
                    state,
                    boundary_index=boundary_index,
                    glue_index=index,
                    glue=glue,
                    source_index=source_index,
                    target_index=target_index,
                )
    state.pending_source_index = boundary_index
    set_selected_boundary_index(state, boundary_index)
    set_selected_glue_id(state, None)
    set_highlighted_glue_id(state, None)
    return "Source boundary selected"


def apply_glue_pick(state: TopologyLabState, glue_id: str) -> str | None:
    profile = current_explorer_profile(state)
    draft = current_explorer_draft(state)
    if not uses_general_explorer_editor(state) or profile is None or draft is None:
        return None
    for index, glue in enumerate(profile.gluings):
        if glue.glue_id != glue_id:
            continue
        source_index, target_index = _glue_boundary_indexes(glue)
        set_selected_glue_id(state, glue_id)
        set_highlighted_glue_id(state, glue_id)
        set_selected_boundary_index(state, source_index)
        if tool_is_edit(state.active_tool):
            update_explorer_draft(
                state,
                slot_index=index,
                source_index=source_index,
                target_index=target_index,
                permutation_index=draft.permutation_index,
                signs=draft.signs,
            )
            set_active_tool(state, TOOL_EDIT)
            return f"Editing {glue_id}"
        return f"Selected {glue_id}"
    return None


__all__ = [
    "apply_boundary_edit_pick",
    "apply_boundary_pick",
    "apply_glue_pick",
    "pick_target",
    "update_hover_target",
]
