from __future__ import annotations

from dataclasses import replace

from tet4d.engine.runtime.project_config import explorer_topology_preview_dims
from tet4d.engine.runtime.topology_explorer_preview import (
    recommended_explorer_probe_coord,
)
from tet4d.engine.runtime.topology_playground_state import (
    TopologyPlaygroundProbeState as RuntimeTopologyPlaygroundProbeState,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile

from .scene_state import (
    TopologyPlaygroundState,
    _identity_probe_frame,
    _normalize_probe_frame_value,
    uses_general_explorer_editor,
)
from .scene_state_canonical import (
    _replace_canonical_state,
    _runtime_state_for_write,
    canonical_playground_state,
    current_explorer_profile,
    sync_canonical_playground_state,
)

_UNSET = object()


def _normalize_probe_coord_value(
    dimension: int,
    coord: tuple[int, ...] | None,
) -> tuple[int, ...] | None:
    if coord is None:
        return None
    normalized = tuple(int(value) for value in coord)
    if len(normalized) != dimension:
        return None
    return normalized


def _normalize_probe_trace_value(
    trace: list[str] | tuple[str, ...] | None,
) -> tuple[str, ...]:
    return tuple(str(entry) for entry in (trace or ()))


def _normalize_probe_path_value(
    dimension: int,
    path: list[tuple[int, ...]] | tuple[tuple[int, ...], ...] | None,
) -> tuple[tuple[int, ...], ...]:
    normalized: list[tuple[int, ...]] = []
    for entry in path or ():
        coord = tuple(int(value) for value in entry)
        if len(coord) == dimension:
            normalized.append(coord)
    return tuple(normalized)


def _runtime_probe_state_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundProbeState:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        coord = runtime_state.probe_state.coord
        path = runtime_state.probe_state.path
        trace = runtime_state.probe_state.trace
        highlighted_gluing = runtime_state.probe_state.highlighted_gluing
    else:
        coord = None
        path = ()
        trace = ()
        highlighted_gluing = (
            None if state.highlighted_glue_id is None else str(state.highlighted_glue_id)
        )
    frame_permutation, frame_signs = current_probe_frame(state)
    return RuntimeTopologyPlaygroundProbeState(
        coord=coord,
        path=path,
        trace=trace,
        show_trace=probe_trace_visible(state),
        show_neighbors=probe_neighbors_visible(state),
        highlighted_gluing=highlighted_gluing,
        frame_permutation=frame_permutation,
        frame_signs=frame_signs,
    )


def current_highlighted_glue_id(state: TopologyPlaygroundState) -> str | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return runtime_state.probe_state.highlighted_gluing
    return state.highlighted_glue_id


def current_probe_coord(state: TopologyPlaygroundState) -> tuple[int, ...] | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return runtime_state.probe_state.coord
    return None


def current_probe_trace(state: TopologyPlaygroundState) -> list[str]:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return list(runtime_state.probe_state.trace)
    return []


def probe_trace_visible(state: TopologyPlaygroundState) -> bool:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return bool(runtime_state.probe_state.show_trace)
    return bool(state.probe_show_trace)


def probe_neighbors_visible(state: TopologyPlaygroundState) -> bool:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return bool(runtime_state.probe_state.show_neighbors)
    return bool(state.probe_show_neighbors)


def current_probe_path(state: TopologyPlaygroundState) -> list[tuple[int, ...]]:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return list(runtime_state.probe_state.path)
    return []


def current_probe_frame(
    state: TopologyPlaygroundState,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return _normalize_probe_frame_value(
            state.dimension,
            runtime_state.probe_state.frame_permutation,
            runtime_state.probe_state.frame_signs,
        )
    return _normalize_probe_frame_value(
        state.dimension,
        state.probe_frame_permutation,
        state.probe_frame_signs,
    )


def replace_probe_state(
    state: TopologyPlaygroundState,
    *,
    coord: tuple[int, ...] | None,
    trace: list[str] | tuple[str, ...] | None,
    path: list[tuple[int, ...]] | tuple[tuple[int, ...], ...] | None,
    highlighted_glue_id: str | None,
    frame_permutation: tuple[int, ...] | object = _UNSET,
    frame_signs: tuple[int, ...] | object = _UNSET,
) -> None:
    normalized_coord = _normalize_probe_coord_value(state.dimension, coord)
    normalized_trace = _normalize_probe_trace_value(trace)
    normalized_path = _normalize_probe_path_value(state.dimension, path)
    normalized_highlight = (
        None if highlighted_glue_id is None else str(highlighted_glue_id)
    )
    current_permutation, current_signs = current_probe_frame(state)
    normalized_permutation, normalized_signs = _normalize_probe_frame_value(
        state.dimension,
        current_permutation if frame_permutation is _UNSET else frame_permutation,
        current_signs if frame_signs is _UNSET else frame_signs,
    )
    runtime_state = _runtime_state_for_write(state, sync_if_missing=True)
    if runtime_state is not None:
        _replace_canonical_state(
            state,
            probe_state=RuntimeTopologyPlaygroundProbeState(
                coord=normalized_coord,
                path=normalized_path,
                trace=normalized_trace,
                show_trace=probe_trace_visible(state),
                show_neighbors=probe_neighbors_visible(state),
                highlighted_gluing=normalized_highlight,
                frame_permutation=normalized_permutation,
                frame_signs=normalized_signs,
            ),
        )
        return
    state.probe_show_trace = probe_trace_visible(state)
    state.probe_show_neighbors = probe_neighbors_visible(state)
    state.probe_frame_permutation = normalized_permutation
    state.probe_frame_signs = normalized_signs
    state.highlighted_glue_id = normalized_highlight


def set_probe_trace_visible(
    state: TopologyPlaygroundState,
    enabled: bool,
) -> None:
    normalized_enabled = bool(enabled)
    runtime_state = _runtime_state_for_write(state)
    if runtime_state is not None:
        _replace_canonical_state(
            state,
            probe_state=replace(
                runtime_state.probe_state,
                show_trace=normalized_enabled,
            ),
        )
        return
    state.probe_show_trace = normalized_enabled
    if uses_general_explorer_editor(state):
        sync_canonical_playground_state(state)


def set_probe_neighbors_visible(
    state: TopologyPlaygroundState,
    enabled: bool,
) -> None:
    normalized_enabled = bool(enabled)
    runtime_state = _runtime_state_for_write(state)
    if runtime_state is not None:
        _replace_canonical_state(
            state,
            probe_state=replace(
                runtime_state.probe_state,
                show_neighbors=normalized_enabled,
            ),
        )
        return
    state.probe_show_neighbors = normalized_enabled
    if uses_general_explorer_editor(state):
        sync_canonical_playground_state(state)


def set_highlighted_glue_id(
    state: TopologyPlaygroundState,
    glue_id: str | None,
) -> None:
    replace_probe_state(
        state,
        coord=current_probe_coord(state),
        trace=current_probe_trace(state),
        path=current_probe_path(state),
        highlighted_glue_id=glue_id,
    )


def playground_dims_for_state(state: TopologyPlaygroundState) -> tuple[int, ...]:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        dims = runtime_state.axis_sizes
    else:
        dims = (
            state.play_settings.board_dims
            if state.play_settings is not None
            else explorer_topology_preview_dims(state.dimension)
        )
    normalized = tuple(int(value) for value in dims[: state.dimension])
    if len(normalized) != state.dimension or any(value <= 0 for value in normalized):
        return explorer_topology_preview_dims(state.dimension)
    return normalized


def select_projection_coord(
    state: TopologyPlaygroundState,
    coord: tuple[int, ...],
) -> tuple[int, ...] | None:
    normalized = _normalize_probe_coord_value(state.dimension, coord)
    if normalized is None:
        return None
    dims = playground_dims_for_state(state)
    if any(value < 0 or value >= dims[index] for index, value in enumerate(normalized)):
        return None
    identity_permutation, identity_signs = _identity_probe_frame(state.dimension)
    replace_probe_state(
        state,
        coord=normalized,
        trace=(),
        path=(normalized,),
        highlighted_glue_id=current_highlighted_glue_id(state),
        frame_permutation=identity_permutation,
        frame_signs=identity_signs,
    )
    return normalized


def _normalize_probe_support_state(state: TopologyPlaygroundState) -> None:
    state.probe_show_trace = bool(state.probe_show_trace)
    state.probe_show_neighbors = bool(state.probe_show_neighbors)
    state.probe_frame_permutation, state.probe_frame_signs = (
        _normalize_probe_frame_value(
            state.dimension,
            state.probe_frame_permutation,
            state.probe_frame_signs,
        )
    )


def _set_probe_unavailable(
    state: TopologyPlaygroundState,
    *,
    message: str,
) -> None:
    replace_probe_state(
        state,
        coord=None,
        trace=[f"Probe unavailable: {message}"],
        path=[],
        highlighted_glue_id=None,
        frame_permutation=tuple(range(state.dimension)),
        frame_signs=tuple(1 for _ in range(state.dimension)),
    )


def _set_recommended_probe_coord(
    state: TopologyPlaygroundState,
    *,
    profile: ExplorerTopologyProfile,
    dims: tuple[int, ...],
) -> None:
    try:
        probe_coord = recommended_explorer_probe_coord(profile, dims=dims)
    except ValueError as exc:
        _set_probe_unavailable(state, message=str(exc))
        return
    replace_probe_state(
        state,
        coord=probe_coord,
        trace=[],
        path=[probe_coord],
        highlighted_glue_id=None,
        frame_permutation=tuple(range(state.dimension)),
        frame_signs=tuple(1 for _ in range(state.dimension)),
    )


def ensure_probe_state(state: TopologyPlaygroundState) -> None:
    profile = current_explorer_profile(state)
    probe_coord = current_probe_coord(state)
    probe_path = current_probe_path(state)
    needs_default = (
        probe_coord is None or len(probe_coord) != state.dimension or not probe_path
    )
    dims = playground_dims_for_state(state)
    _normalize_probe_support_state(state)
    if profile is None:
        return
    if state.scene_preview_error is not None:
        _set_probe_unavailable(state, message=state.scene_preview_error)
        return
    probe_coord = current_probe_coord(state)
    probe_out_of_bounds = probe_coord is not None and any(
        value < 0 or value >= dims[index] for index, value in enumerate(probe_coord)
    )
    if probe_coord is None or needs_default or probe_out_of_bounds:
        _set_recommended_probe_coord(state, profile=profile, dims=dims)


def reset_probe_state(state: TopologyPlaygroundState) -> None:
    dims = playground_dims_for_state(state)
    probe_coord = tuple(max(0, size // 2) for size in dims)
    frame_permutation, frame_signs = _identity_probe_frame(state.dimension)
    replace_probe_state(
        state,
        coord=probe_coord,
        trace=[],
        path=[probe_coord],
        highlighted_glue_id=None,
        frame_permutation=frame_permutation,
        frame_signs=frame_signs,
    )
