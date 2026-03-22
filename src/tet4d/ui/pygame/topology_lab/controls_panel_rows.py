from __future__ import annotations

from dataclasses import dataclass

from tet4d.engine.gameplay.topology_designer import GAMEPLAY_MODE_NORMAL

from .scene_state import (
    PANE_CONTROLS,
    TopologyLabState,
    WORKSPACE_EDITOR,
    WORKSPACE_SANDBOX,
    active_workspace_name,
    uses_general_explorer_editor,
)


@dataclass(frozen=True)
class _RowSpec:
    key: str
    label: str
    axis: int | None = None
    side: int | None = None
    disabled: bool = False


_EXPLORER_BOARD_ROW_AXES = {
    "board_x": 0,
    "board_y": 1,
    "board_z": 2,
    "board_w": 3,
}

_STATUS_ROW_KEYS = frozenset(
    {
        "playability_summary",
        "playability_validity",
        "playability_explorer",
        "playability_rigid",
        "playability_reason",
        "analysis_boundary",
        "analysis_glue",
        "analysis_transform",
    }
)
_LEGACY_AXIS_LABELS = {"x": "X", "y": "Y", "z": "Z", "w": "W"}


def _workspace_context_rows(state: TopologyLabState) -> tuple[_RowSpec, ...]:
    workspace_name = active_workspace_name(state)
    if workspace_name == WORKSPACE_EDITOR:
        return (
            _RowSpec("editor_tool", "Tool"),
            _RowSpec("editor_trace", "Trace"),
            _RowSpec("editor_probe_neighbors", "Probe Neighbors"),
        )
    if workspace_name == WORKSPACE_SANDBOX:
        return (_RowSpec("sandbox_neighbor_search", "Neighbors"),)
    return ()


def _board_dimension_rows(state: TopologyLabState) -> tuple[_RowSpec, ...]:
    rows = [
        _RowSpec("dimension", "Dimension"),
        _RowSpec("board_x", "Board X"),
        _RowSpec("board_y", "Board Y"),
    ]
    if state.dimension >= 3:
        rows.append(_RowSpec("board_z", "Board Z"))
    if state.dimension >= 4:
        rows.append(_RowSpec("board_w", "Board W"))
    return tuple(rows)


def _explorer_rows(state: TopologyLabState) -> tuple[_RowSpec, ...]:
    rows = [_RowSpec("gameplay_mode", "Path")]
    rows.extend(_workspace_context_rows(state))
    rows.extend(_board_dimension_rows(state))
    rows.extend(
        (
            _RowSpec("piece_set", "Piece Set"),
            _RowSpec("speed_level", "Speed"),
            _RowSpec("rigid_play_mode", "Play Transport"),
            _RowSpec("explorer_preset", "Explorer Preset"),
            _RowSpec("playability_summary", "Topology Status"),
            _RowSpec("playability_validity", "Validity"),
            _RowSpec("playability_explorer", "Explorer"),
            _RowSpec("playability_rigid", "Rigid Play"),
            _RowSpec("playability_reason", "Why"),
            _RowSpec("analysis_boundary", "Selected Boundary"),
            _RowSpec("analysis_glue", "Selected Seam"),
            _RowSpec("analysis_transform", "Draft Transform"),
            _RowSpec("save_profile", "Save Profile"),
            _RowSpec("export", "Export Explorer Preview"),
            _RowSpec("experiments", "Build Experiment Pack"),
            _RowSpec("back", "Back"),
        )
    )
    return tuple(rows)


def _legacy_rows(state: TopologyLabState) -> tuple[_RowSpec, ...]:
    rows = [
        _RowSpec("gameplay_mode", "Workspace Path"),
        _RowSpec("dimension", "Dimension"),
        _RowSpec("preset", "Legacy Preset"),
        _RowSpec("topology_mode", "Legacy Topology"),
    ]
    for axis_name in tuple("xyzw"[: state.dimension]):
        axis = "xyzw".index(axis_name)
        disabled = axis_name == "y" and state.gameplay_mode == GAMEPLAY_MODE_NORMAL
        rows.append(
            _RowSpec(
                f"{axis_name}_neg",
                f"{_LEGACY_AXIS_LABELS[axis_name]}-",
                axis=axis,
                side=0,
                disabled=disabled,
            )
        )
        rows.append(
            _RowSpec(
                f"{axis_name}_pos",
                f"{_LEGACY_AXIS_LABELS[axis_name]}+",
                axis=axis,
                side=1,
                disabled=disabled,
            )
        )
    rows.extend(
        (
            _RowSpec("save_profile", "Save Legacy Profile"),
            _RowSpec("export", "Export Legacy Resolved Profile"),
            _RowSpec("back", "Back"),
        )
    )
    return tuple(rows)


def _rows_for_state(state: TopologyLabState) -> tuple[_RowSpec, ...]:
    if uses_general_explorer_editor(state):
        if state.active_pane != PANE_CONTROLS:
            return _workspace_context_rows(state)
        return _explorer_rows(state)
    return _legacy_rows(state)


def _selectable_row_indexes(state: TopologyLabState) -> tuple[int, ...]:
    return tuple(
        idx
        for idx, row in enumerate(_rows_for_state(state))
        if not _row_is_status_display(row)
    )


def _row_supports_step_adjustment(row: _RowSpec) -> bool:
    return (
        (not row.disabled)
        and (not _row_is_status_display(row))
        and row.key
        not in {
            "analysis_boundary",
            "analysis_glue",
            "analysis_transform",
            "apply_glue",
            "remove_glue",
            "save_profile",
            "export",
            "experiments",
            "back",
        }
    )


def _row_is_status_display(row: _RowSpec) -> bool:
    return row.key in _STATUS_ROW_KEYS
