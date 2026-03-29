from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from tet4d.engine.core.model import Coord
from tet4d.engine.topology_explorer import (
    ExplorerTopologyProfile,
    movement_steps_for_dimension,
    validate_topology_bijection,
    validate_topology_structure,
)
from tet4d.engine.topology_explorer.transport_resolver import (
    CELLWISE_DEFORMATION,
    build_explorer_transport_resolver,
)

from .topology_playground_state import (
    EXPLORER_USABILITY_BLOCKED,
    EXPLORER_USABILITY_CELLWISE,
    PLAYABILITY_STATUS_ANALYZING,
    PLAYABILITY_STATUS_BLOCKED,
    PLAYABILITY_STATUS_PLAYABLE,
    PLAYABILITY_STATUS_WARNING,
    RIGID_PLAYABILITY_BLOCKED,
    RIGID_PLAYABILITY_PLAYABLE,
    RIGID_PLAYABILITY_UNKNOWN,
    RIGID_PLAY_MODE_AUTO,
    RIGID_PLAY_MODE_OFF,
    RIGID_PLAY_MODE_ON,
    TOPOLOGY_VALIDITY_INVALID,
    TOPOLOGY_VALIDITY_VALID,
    TopologyPlaygroundMovementSummary,
    TopologyPlaygroundPlayabilityAnalysis,
    TopologyPlaygroundState,
)


@dataclass(frozen=True)
class _RigidTransportFailure:
    step_label: str
    source_cells: tuple[Coord, Coord]
    moved_cells: tuple[Coord, Coord]
    crossing_text: str | None


def _movement_summary_from_preview(
    preview: dict[str, object] | None,
) -> TopologyPlaygroundMovementSummary:
    graph = {} if preview is None else dict(preview.get("movement_graph", {}))

    def _optional_int(key: str) -> int | None:
        value = graph.get(key)
        if value is None:
            return None
        return int(value)

    return TopologyPlaygroundMovementSummary(
        cell_count=_optional_int("cell_count"),
        directed_edge_count=_optional_int("directed_edge_count"),
        boundary_traversal_count=_optional_int("boundary_traversal_count"),
        component_count=_optional_int("component_count"),
    )


def _all_coords(dims: tuple[int, ...]) -> tuple[Coord, ...]:
    return tuple(
        tuple(int(value) for value in coord)
        for coord in product(*(range(size) for size in dims))
    )


def _adjacent_neighbor(coord: Coord, axis: int, dims: tuple[int, ...]) -> Coord | None:
    candidate = list(coord)
    candidate[axis] += 1
    if candidate[axis] >= dims[axis]:
        return None
    return tuple(candidate)


def _crossing_text_from_piece_step(cell_steps: tuple[object, ...]) -> str | None:
    for cell_step in cell_steps:
        traversal = getattr(cell_step, "traversal", None)
        if traversal is None:
            continue
        return (
            f"{traversal.glue_id} "
            f"({traversal.source_boundary.label} -> {traversal.target_boundary.label})"
        )
    return None


def _first_rigid_transport_failure(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    resolver=None,
) -> _RigidTransportFailure | None:
    coords = _all_coords(dims)
    steps = tuple(movement_steps_for_dimension(profile.dimension))
    if resolver is None:
        resolver = build_explorer_transport_resolver(profile, dims)
    for step in steps:
        for coord in coords:
            for axis in range(profile.dimension):
                neighbor = _adjacent_neighbor(coord, axis, dims)
                if neighbor is None:
                    continue
                source_cells = (coord, neighbor)
                outcome = resolver.resolve_piece_step(source_cells, step)
                if outcome.kind != CELLWISE_DEFORMATION or outcome.rigidly_coherent:
                    continue
                if outcome.moved_cells is None or len(outcome.moved_cells) != 2:
                    continue
                return _RigidTransportFailure(
                    step_label=step.label,
                    source_cells=source_cells,
                    moved_cells=(outcome.moved_cells[0], outcome.moved_cells[1]),
                    crossing_text=_crossing_text_from_piece_step(outcome.cell_steps),
                )
    return None


def _invalid_summary(reason: str) -> str:
    if "unsupported for current board dimensions" in reason:
        return "Invalid for current board dimensions."
    return "Invalid topology."


def _invalid_analysis(
    reason: str,
    *,
    preview: dict[str, object] | None,
) -> TopologyPlaygroundPlayabilityAnalysis:
    return TopologyPlaygroundPlayabilityAnalysis(
        status=PLAYABILITY_STATUS_BLOCKED,
        validity=TOPOLOGY_VALIDITY_INVALID,
        explorer_usability=EXPLORER_USABILITY_BLOCKED,
        rigid_playability=RIGID_PLAYABILITY_BLOCKED,
        summary=_invalid_summary(reason),
        validity_reason=reason,
        explorer_reason=(
            "Explorer/probe is unavailable until the current topology validates "
            "for these board dimensions."
        ),
        rigid_reason=(
            "Play launch stays restricted because runtime validation already "
            "rejects this topology."
        ),
        errors=(reason,),
        movement_summary=_movement_summary_from_preview(preview),
    )


def _valid_pending_analysis(
    *,
    preview: dict[str, object] | None,
    warnings: tuple[str, ...],
) -> TopologyPlaygroundPlayabilityAnalysis:
    return TopologyPlaygroundPlayabilityAnalysis(
        status=PLAYABILITY_STATUS_ANALYZING,
        validity=TOPOLOGY_VALIDITY_VALID,
        explorer_usability=EXPLORER_USABILITY_CELLWISE,
        rigid_playability=RIGID_PLAYABILITY_UNKNOWN,
        summary="Valid. Cellwise explorable. Rigid play analysis pending.",
        validity_reason="Current topology validates for the active board dimensions.",
        explorer_reason=(
            "Explorer/probe follows the validated single-cell traversal graph."
        ),
        rigid_reason=(
            "Rigid transport is still being analyzed for the current topology."
        ),
        warnings=warnings,
        movement_summary=_movement_summary_from_preview(preview),
    )


def derive_topology_playability_analysis(
    state: TopologyPlaygroundState,
    *,
    preview: dict[str, object] | None = None,
    preview_error: str | None = None,
    include_rigid_scan: bool = True,
) -> TopologyPlaygroundPlayabilityAnalysis:
    profile = state.explorer_profile
    dims = tuple(int(value) for value in state.axis_sizes)
    warnings = tuple(str(item) for item in (preview or {}).get("warnings", ()))
    movement_summary = _movement_summary_from_preview(preview)

    try:
        validate_topology_structure(profile)
        validate_topology_bijection(profile, dims=dims)
    except ValueError as exc:
        return _invalid_analysis(str(exc), preview=preview)

    if preview_error is not None:
        return _invalid_analysis(str(preview_error), preview=preview)

    if not include_rigid_scan:
        return _valid_pending_analysis(preview=preview, warnings=warnings)

    failure = _first_rigid_transport_failure(profile, dims=dims)
    if failure is None:
        return TopologyPlaygroundPlayabilityAnalysis(
            status=PLAYABILITY_STATUS_PLAYABLE,
            validity=TOPOLOGY_VALIDITY_VALID,
            explorer_usability=EXPLORER_USABILITY_CELLWISE,
            rigid_playability=RIGID_PLAYABILITY_PLAYABLE,
            summary="Valid. Cellwise explorable. Rigid-playable.",
            validity_reason=(
                "Current topology validates for the active board dimensions."
            ),
            explorer_reason=(
                "Explorer/probe follows the validated single-cell traversal graph."
            ),
            rigid_reason=(
                "Current rigid transport analysis did not find an adjacent-cell "
                "deformation case."
            ),
            warnings=warnings,
            movement_summary=movement_summary,
        )

    rigid_reason = (
        "Rigid transport fails when a two-cell piece partly crosses "
        f"{failure.crossing_text} during {failure.step_label}."
        if failure.crossing_text is not None
        else (
            "Rigid transport fails when adjacent cells take different mappings "
            f"during {failure.step_label}."
        )
    )
    return TopologyPlaygroundPlayabilityAnalysis(
        status=PLAYABILITY_STATUS_WARNING,
        validity=TOPOLOGY_VALIDITY_VALID,
        explorer_usability=EXPLORER_USABILITY_CELLWISE,
        rigid_playability=RIGID_PLAYABILITY_BLOCKED,
        summary="Valid. Cellwise explorable. Not rigid-playable.",
        validity_reason="Current topology validates for the active board dimensions.",
        explorer_reason=(
            "Explorer/probe remains available because it follows single-cell "
            "traversal rather than rigid-piece transport."
        ),
        rigid_reason=rigid_reason,
        warnings=warnings + (rigid_reason,),
        movement_summary=movement_summary,
    )


def topology_is_rigid_playable(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    resolver=None,
) -> bool:
    return (
        _first_rigid_transport_failure(
            profile,
            dims=dims,
            resolver=resolver,
        )
        is None
    )


def resolve_rigid_play_enabled(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    rigid_play_mode: str = RIGID_PLAY_MODE_AUTO,
    analysis: TopologyPlaygroundPlayabilityAnalysis | None = None,
    resolver=None,
) -> bool:
    mode = str(rigid_play_mode)
    if mode == RIGID_PLAY_MODE_ON:
        return True
    if mode == RIGID_PLAY_MODE_OFF:
        return False
    if mode != RIGID_PLAY_MODE_AUTO:
        raise ValueError(f"unsupported rigid play mode: {rigid_play_mode!r}")
    if analysis is not None:
        if analysis.validity == TOPOLOGY_VALIDITY_INVALID:
            return False
        if analysis.validity == TOPOLOGY_VALIDITY_VALID:
            if analysis.rigid_playability == RIGID_PLAYABILITY_PLAYABLE:
                return True
            if analysis.rigid_playability == RIGID_PLAYABILITY_BLOCKED:
                return False
    return topology_is_rigid_playable(profile, dims=dims, resolver=resolver)


def update_topology_playability_analysis(
    state: TopologyPlaygroundState,
    *,
    preview: dict[str, object] | None = None,
    preview_error: str | None = None,
    include_rigid_scan: bool = True,
) -> TopologyPlaygroundPlayabilityAnalysis:
    analysis = derive_topology_playability_analysis(
        state,
        preview=preview,
        preview_error=preview_error,
        include_rigid_scan=include_rigid_scan,
    )
    state.playability_analysis = analysis
    return analysis


__all__ = [
    "derive_topology_playability_analysis",
    "resolve_rigid_play_enabled",
    "topology_is_rigid_playable",
    "update_topology_playability_analysis",
]
