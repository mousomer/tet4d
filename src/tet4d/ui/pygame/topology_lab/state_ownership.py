from __future__ import annotations

from dataclasses import dataclass

from tet4d.engine.runtime.topology_playground_state import (
    TopologyPlaygroundState as RuntimeTopologyPlaygroundState,
)

from .scene_state import TopologyLabState, playground_dims_for_state

_UNSET = object()


def _identity_frame(dimension: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return tuple(range(dimension)), tuple(1 for _ in range(dimension))


def _normalize_coord(
    dimension: int,
    coord: tuple[int, ...] | None,
) -> tuple[int, ...] | None:
    if coord is None:
        return None
    normalized = tuple(int(value) for value in coord)
    if len(normalized) != dimension:
        return None
    return normalized


def _coord_in_bounds(
    coord: tuple[int, ...],
    dims: tuple[int, ...],
) -> bool:
    return all(
        0 <= int(value) < int(dims[index]) for index, value in enumerate(coord)
    )


def _normalize_path(
    dimension: int,
    dims: tuple[int, ...],
    path: list[tuple[int, ...]] | tuple[tuple[int, ...], ...] | None,
) -> list[tuple[int, ...]]:
    normalized: list[tuple[int, ...]] = []
    for entry in path or ():
        coord = _normalize_coord(dimension, entry)
        if coord is not None and _coord_in_bounds(coord, dims):
            normalized.append(coord)
    return normalized


def _normalize_frame(
    dimension: int,
    permutation: tuple[int, ...] | None,
    signs: tuple[int, ...] | None,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    default_permutation, default_signs = _identity_frame(dimension)
    normalized_permutation = (
        default_permutation
        if permutation is None
        else tuple(int(value) for value in permutation)
    )
    normalized_signs = (
        default_signs if signs is None else tuple(int(value) for value in signs)
    )
    if len(normalized_permutation) != dimension:
        normalized_permutation = default_permutation
    if len(normalized_signs) != dimension:
        normalized_signs = default_signs
    if tuple(sorted(normalized_permutation)) != tuple(range(dimension)):
        normalized_permutation = default_permutation
    if any(value not in (-1, 1) for value in normalized_signs):
        normalized_signs = default_signs
    return normalized_permutation, normalized_signs


def _default_focus_coord(state: TopologyLabState) -> tuple[int, ...]:
    dims = playground_dims_for_state(state)
    if state.sandbox is not None and state.sandbox.origin is not None:
        origin = _normalize_coord(state.dimension, state.sandbox.origin)
        if origin is not None and _coord_in_bounds(origin, dims):
            return origin
    return tuple(max(0, size // 2) for size in dims)


@dataclass(frozen=True)
class TopologyLabEditorOwnershipState:
    selected_boundary_index: int | None
    selected_glue_id: str | None
    hovered_boundary_index: int | None
    hovered_glue_id: str | None
    pending_source_index: int | None


@dataclass(frozen=True)
class TopologyLabInspectorOwnershipState:
    probe_coord: tuple[int, ...] | None
    probe_trace: tuple[str, ...]
    probe_path: tuple[tuple[int, ...], ...]
    probe_frame_permutation: tuple[int, ...] | None
    probe_frame_signs: tuple[int, ...] | None
    highlighted_glue_id: str | None


@dataclass(frozen=True)
class TopologyLabSandboxOwnershipState:
    piece_state: object | None
    focus_coord: tuple[int, ...] | None
    focus_trace: tuple[str, ...]
    focus_path: tuple[tuple[int, ...], ...]
    focus_frame_permutation: tuple[int, ...] | None
    focus_frame_signs: tuple[int, ...] | None


@dataclass(frozen=True)
class TopologyLabPlayOwnershipState:
    preview_requested: bool


@dataclass(frozen=True)
class TopologyLabDerivedCacheOwnershipState:
    scene_boundaries: tuple[object, ...]
    scene_preview_dims: tuple[int, ...]
    scene_active_glue_ids: dict[str, str]
    scene_basis_arrows: tuple[dict[str, object], ...]
    scene_preview: dict[str, object] | None
    scene_preview_error: str | None
    scene_preview_signature: object | None
    scene_preview_cache: object | None
    experiment_batch: dict[str, object] | None


@dataclass(frozen=True)
class TopologyLabOwnershipSnapshot:
    canonical_state: RuntimeTopologyPlaygroundState | None
    editor: TopologyLabEditorOwnershipState
    inspector: TopologyLabInspectorOwnershipState
    sandbox: TopologyLabSandboxOwnershipState
    play: TopologyLabPlayOwnershipState
    caches: TopologyLabDerivedCacheOwnershipState


def ownership_snapshot(state: TopologyLabState) -> TopologyLabOwnershipSnapshot:
    return TopologyLabOwnershipSnapshot(
        canonical_state=state.canonical_state,
        editor=TopologyLabEditorOwnershipState(
            selected_boundary_index=state.selected_boundary_index,
            selected_glue_id=state.selected_glue_id,
            hovered_boundary_index=state.hovered_boundary_index,
            hovered_glue_id=state.hovered_glue_id,
            pending_source_index=state.pending_source_index,
        ),
        inspector=TopologyLabInspectorOwnershipState(
            probe_coord=state.probe_coord,
            probe_trace=tuple(str(entry) for entry in (state.probe_trace or ())),
            probe_path=tuple(
                tuple(int(value) for value in entry)
                for entry in (state.probe_path or ())
            ),
            probe_frame_permutation=state.probe_frame_permutation,
            probe_frame_signs=state.probe_frame_signs,
            highlighted_glue_id=state.highlighted_glue_id,
        ),
        sandbox=TopologyLabSandboxOwnershipState(
            piece_state=state.sandbox,
            focus_coord=getattr(state, "sandbox_focus_coord", None),
            focus_trace=tuple(
                str(entry) for entry in getattr(state, "sandbox_focus_trace", ()) or ()
            ),
            focus_path=tuple(
                tuple(int(value) for value in entry)
                for entry in getattr(state, "sandbox_focus_path", ()) or ()
            ),
            focus_frame_permutation=getattr(
                state,
                "sandbox_focus_frame_permutation",
                None,
            ),
            focus_frame_signs=getattr(state, "sandbox_focus_frame_signs", None),
        ),
        play=TopologyLabPlayOwnershipState(
            preview_requested=bool(state.play_preview_requested),
        ),
        caches=TopologyLabDerivedCacheOwnershipState(
            scene_boundaries=tuple(state.scene_boundaries),
            scene_preview_dims=tuple(state.scene_preview_dims),
            scene_active_glue_ids=dict(state.scene_active_glue_ids),
            scene_basis_arrows=tuple(state.scene_basis_arrows),
            scene_preview=state.scene_preview,
            scene_preview_error=state.scene_preview_error,
            scene_preview_signature=state.scene_preview_signature,
            scene_preview_cache=state.scene_preview_cache,
            experiment_batch=state.experiment_batch,
        ),
    )


def current_sandbox_focus_coord(state: TopologyLabState) -> tuple[int, ...]:
    dims = playground_dims_for_state(state)
    current = _normalize_coord(
        state.dimension,
        getattr(state, "sandbox_focus_coord", None),
    )
    if current is not None and _coord_in_bounds(current, dims):
        return current
    return _default_focus_coord(state)


def current_sandbox_focus_trace(state: TopologyLabState) -> list[str]:
    return list(getattr(state, "sandbox_focus_trace", ()) or ())


def current_sandbox_focus_path(state: TopologyLabState) -> list[tuple[int, ...]]:
    dims = playground_dims_for_state(state)
    path = _normalize_path(
        state.dimension,
        dims,
        getattr(state, "sandbox_focus_path", None),
    )
    coord = current_sandbox_focus_coord(state)
    if not path or path[-1] != coord:
        return [coord]
    return path


def current_sandbox_focus_frame(
    state: TopologyLabState,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return _normalize_frame(
        state.dimension,
        getattr(state, "sandbox_focus_frame_permutation", None),
        getattr(state, "sandbox_focus_frame_signs", None),
    )


def replace_sandbox_focus_state(
    state: TopologyLabState,
    *,
    coord: tuple[int, ...] | None,
    trace: list[str] | tuple[str, ...] | None,
    path: list[tuple[int, ...]] | tuple[tuple[int, ...], ...] | None,
    frame_permutation: tuple[int, ...] | object = _UNSET,
    frame_signs: tuple[int, ...] | object = _UNSET,
) -> None:
    dims = playground_dims_for_state(state)
    normalized_coord = _normalize_coord(state.dimension, coord)
    if normalized_coord is not None and not _coord_in_bounds(normalized_coord, dims):
        normalized_coord = _default_focus_coord(state)
    current_permutation, current_signs = current_sandbox_focus_frame(state)
    normalized_permutation, normalized_signs = _normalize_frame(
        state.dimension,
        current_permutation if frame_permutation is _UNSET else frame_permutation,
        current_signs if frame_signs is _UNSET else frame_signs,
    )
    normalized_trace = [str(entry) for entry in (trace or ())]
    normalized_path = _normalize_path(state.dimension, dims, path)
    if normalized_coord is None:
        setattr(state, "sandbox_focus_coord", None)
        setattr(state, "sandbox_focus_trace", normalized_trace)
        setattr(state, "sandbox_focus_path", [])
    else:
        setattr(state, "sandbox_focus_coord", normalized_coord)
        setattr(state, "sandbox_focus_trace", normalized_trace)
        setattr(
            state,
            "sandbox_focus_path",
            normalized_path
            if normalized_path and normalized_path[-1] == normalized_coord
            else [normalized_coord],
        )
    setattr(state, "sandbox_focus_frame_permutation", normalized_permutation)
    setattr(state, "sandbox_focus_frame_signs", normalized_signs)


def select_sandbox_projection_coord(
    state: TopologyLabState,
    coord: tuple[int, ...],
) -> tuple[int, ...] | None:
    dims = playground_dims_for_state(state)
    normalized = _normalize_coord(state.dimension, coord)
    if normalized is None or not _coord_in_bounds(normalized, dims):
        return None
    identity_permutation, identity_signs = _identity_frame(state.dimension)
    replace_sandbox_focus_state(
        state,
        coord=normalized,
        trace=(),
        path=(normalized,),
        frame_permutation=identity_permutation,
        frame_signs=identity_signs,
    )
    return normalized


__all__ = [
    "TopologyLabDerivedCacheOwnershipState",
    "TopologyLabEditorOwnershipState",
    "TopologyLabInspectorOwnershipState",
    "TopologyLabOwnershipSnapshot",
    "TopologyLabPlayOwnershipState",
    "TopologyLabSandboxOwnershipState",
    "current_sandbox_focus_coord",
    "current_sandbox_focus_frame",
    "current_sandbox_focus_path",
    "current_sandbox_focus_trace",
    "ownership_snapshot",
    "replace_sandbox_focus_state",
    "select_sandbox_projection_coord",
]
