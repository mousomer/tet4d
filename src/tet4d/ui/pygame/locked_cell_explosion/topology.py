from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from tet4d.engine.gameplay.topology import EDGE_BOUNDED, EDGE_INVERT, EDGE_WRAP
from tet4d.engine.topology_explorer.glue_model import BoundaryRef, MoveStep
from tet4d.engine.topology_explorer.transport_resolver import (
    ExplorerTransportResolver,
    build_explorer_transport_resolver,
)

from .model import ExplosionTopologyInput, VecN


def _vec_add(left: VecN, right: VecN) -> VecN:
    return tuple(a + b for a, b in zip(left, right))


def _linear_apply(
    value: Sequence[float],
    *,
    permutation: Sequence[int],
    signs: Sequence[int],
) -> VecN:
    mapped = [0.0] * len(permutation)
    for source_axis, target_axis in enumerate(permutation):
        mapped[int(target_axis)] = float(value[source_axis]) * float(signs[source_axis])
    return tuple(mapped)


def _boundary_step(boundary: BoundaryRef) -> MoveStep:
    return MoveStep(axis=boundary.axis, delta=-1 if boundary.side == "-" else 1)


def _entry_step(boundary: BoundaryRef) -> MoveStep:
    return MoveStep(axis=boundary.axis, delta=1 if boundary.side == "-" else -1)


def _continuous_translation_for_seam(seam) -> VecN:
    sample_source, sample_target = seam.boundary_coord_map[0]
    source_plane = [float(value) for value in sample_source]
    target_plane = [float(value) for value in sample_target]
    source_plane[seam.source_boundary.axis] += 0.5 * float(seam.exit_step.delta)
    target_plane[seam.target_boundary.axis] -= 0.5 * float(seam.entry_step.delta)
    linear_sample = _linear_apply(
        source_plane,
        permutation=seam.piece_frame_transform.permutation,
        signs=seam.piece_frame_transform.signs,
    )
    return tuple(
        target_plane[axis] - linear_sample[axis] for axis in range(len(target_plane))
    )


@dataclass(frozen=True)
class ExplosionSeam:
    glue_id: str
    source_boundary: BoundaryRef
    target_boundary: BoundaryRef
    entry_step: MoveStep
    exit_step: MoveStep
    permutation: tuple[int, ...]
    signs: tuple[int, ...]
    translation: VecN

    def transform_position(self, position: VecN) -> VecN:
        return _vec_add(
            _linear_apply(
                position,
                permutation=self.permutation,
                signs=self.signs,
            ),
            self.translation,
        )

    def transform_velocity(self, velocity: VecN) -> VecN:
        return _linear_apply(
            velocity,
            permutation=self.permutation,
            signs=self.signs,
        )


@dataclass(frozen=True)
class ExplosionTopologyAdapter:
    board_dims: tuple[int, ...]
    seams_by_boundary: dict[BoundaryRef, ExplosionSeam]

    def seam_for_boundary(self, boundary: BoundaryRef) -> ExplosionSeam | None:
        return self.seams_by_boundary.get(boundary)


def _synthetic_seam(
    *,
    dims: tuple[int, ...],
    source_boundary: BoundaryRef,
    behavior: str,
    wrapped_axes: frozenset[int],
) -> ExplosionSeam:
    target_boundary = BoundaryRef(
        dimension=source_boundary.dimension,
        axis=source_boundary.axis,
        side="+" if source_boundary.side == "-" else "-",
    )
    permutation = tuple(range(source_boundary.dimension))
    signs = [1] * source_boundary.dimension
    if behavior == EDGE_INVERT:
        for axis in wrapped_axes:
            if axis != source_boundary.axis:
                signs[axis] = -1
    translation = [0.0] * source_boundary.dimension
    axis = source_boundary.axis
    size = float(dims[axis])
    if source_boundary.side == "-":
        translation[axis] = size
    else:
        translation[axis] = -size
    if behavior == EDGE_INVERT:
        for axis in wrapped_axes:
            if axis == source_boundary.axis:
                continue
            translation[axis] = float(dims[axis] - 1)
    return ExplosionSeam(
        glue_id=f"edge_{source_boundary.label}",
        source_boundary=source_boundary,
        target_boundary=target_boundary,
        entry_step=_entry_step(target_boundary),
        exit_step=_boundary_step(source_boundary),
        permutation=permutation,
        signs=tuple(signs),
        translation=tuple(translation),
    )


def _adapter_from_edge_rules(topology: ExplosionTopologyInput) -> ExplosionTopologyAdapter:
    dims = tuple(int(value) for value in topology.board_dims)
    edge_rules = tuple(topology.topology_edge_rules or ())
    wrapped_axes = frozenset(
        axis
        for axis, (neg, pos) in enumerate(edge_rules)
        if neg != EDGE_BOUNDED or pos != EDGE_BOUNDED
    )
    seams: dict[BoundaryRef, ExplosionSeam] = {}
    for axis, axis_rules in enumerate(edge_rules):
        for side_index, behavior in enumerate(axis_rules):
            boundary = BoundaryRef(
                dimension=len(dims),
                axis=axis,
                side="-" if side_index == 0 else "+",
            )
            if behavior not in {EDGE_WRAP, EDGE_INVERT}:
                continue
            seams[boundary] = _synthetic_seam(
                dims=dims,
                source_boundary=boundary,
                behavior=behavior,
                wrapped_axes=wrapped_axes,
            )
    return ExplosionTopologyAdapter(board_dims=dims, seams_by_boundary=seams)


def _adapter_from_transport(resolver: ExplorerTransportResolver) -> ExplosionTopologyAdapter:
    seams: dict[BoundaryRef, ExplosionSeam] = {}
    for seam in resolver.directed_seams:
        seams[seam.source_boundary] = ExplosionSeam(
            glue_id=seam.glue_id,
            source_boundary=seam.source_boundary,
            target_boundary=seam.target_boundary,
            entry_step=seam.entry_step,
            exit_step=seam.exit_step,
            permutation=tuple(int(value) for value in seam.piece_frame_transform.permutation),
            signs=tuple(int(value) for value in seam.piece_frame_transform.signs),
            translation=_continuous_translation_for_seam(seam),
        )
    return ExplosionTopologyAdapter(
        board_dims=tuple(int(value) for value in resolver.dims),
        seams_by_boundary=seams,
    )


def build_explosion_topology_adapter(
    topology: ExplosionTopologyInput,
) -> ExplosionTopologyAdapter:
    if topology.explorer_transport is not None:
        return _adapter_from_transport(topology.explorer_transport)
    if topology.explorer_topology_profile is not None:
        return _adapter_from_transport(
            build_explorer_transport_resolver(
                topology.explorer_topology_profile,
                topology.board_dims,
            )
        )
    return _adapter_from_edge_rules(topology)

