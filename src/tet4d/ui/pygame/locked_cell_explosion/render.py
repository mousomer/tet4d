from __future__ import annotations

import math
from typing import Any

from .model import (
    EXPLOSION_TRAIL_MAX_LIFETIME_MS,
    ExplosionParticle,
    ExplosionRenderParticle,
    ExplosionRenderTrailSegment,
    ExplosionTrailSample,
)


def _pad_vec3(value: tuple[float, ...]) -> tuple[float, float, float]:
    padded = tuple(value) + (0.0, 0.0, 0.0)
    return (float(padded[0]), float(padded[1]), float(padded[2]))


def _layer_weights_for_value(
    layer_value: float,
    *,
    layer_count: int,
) -> tuple[tuple[int, float], ...]:
    if layer_count <= 1:
        return ((0, 1.0),)
    clamped = max(0.0, min(float(layer_count - 1), float(layer_value)))
    base_index = int(math.floor(clamped))
    fraction = clamped - float(base_index)
    if fraction <= 1e-6 or base_index >= layer_count - 1:
        return ((base_index, 1.0),)
    return ((base_index, 1.0 - fraction), (base_index + 1, fraction))


def _project_position_for_render(
    position_nd: tuple[float, ...],
    *,
    dimension: int,
    board_dims: tuple[int, ...],
    render_context: Any | None,
) -> tuple[tuple[float, float, float], tuple[tuple[int, float], ...]]:
    if render_context is None or int(dimension) < 4:
        return _pad_vec3(position_nd), ()
    axis_map = getattr(render_context, "basis_axis_map", ()) or (
        (0, 1),
        (1, 1),
        (2, 1),
        (3, 1),
    )
    mapped: list[float] = []
    for axis, sign in axis_map[:4]:
        axis_index = int(axis)
        value = float(position_nd[axis_index]) if 0 <= axis_index < len(position_nd) else 0.0
        size = float(board_dims[axis_index]) if 0 <= axis_index < len(board_dims) else 1.0
        mapped.append(value if int(sign) > 0 else (size - 1.0 - value))
    while len(mapped) < 4:
        mapped.append(0.0)
    return (
        (mapped[0], mapped[1], mapped[2]),
        _layer_weights_for_value(
            mapped[3],
            layer_count=max(1, int(getattr(render_context, "layer_count", 1))),
        ),
    )


def _trail_strength_for_age(age_ms: float) -> float:
    age_ratio = max(0.0, min(1.0, float(age_ms) / EXPLOSION_TRAIL_MAX_LIFETIME_MS))
    return 1.0 - age_ratio


def _trail_style_for_sample(
    sample: ExplosionTrailSample,
    *,
    elapsed_ms: float,
) -> tuple[float, float]:
    strength = _trail_strength_for_age(float(elapsed_ms) - float(sample.elapsed_ms))
    alpha = 0.12 + (0.76 * strength)
    width = 0.22 + (0.88 * strength)
    return alpha, width


def _render_trail_segments(
    particle: ExplosionParticle,
    *,
    dimension: int,
    board_dims: tuple[int, ...],
    render_context: Any | None,
    elapsed_ms: float,
) -> tuple[ExplosionRenderTrailSegment, ...]:
    segments: list[ExplosionRenderTrailSegment] = []
    previous_sample: ExplosionTrailSample | None = None
    for sample in tuple(particle.trail_samples):
        if sample.segment_break:
            previous_sample = None
            continue
        if previous_sample is not None:
            tail_render_position, tail_layer_weights = _project_position_for_render(
                tuple(float(value) for value in previous_sample.position_nd),
                dimension=dimension,
                board_dims=board_dims,
                render_context=render_context,
            )
            head_render_position, head_layer_weights = _project_position_for_render(
                tuple(float(value) for value in sample.position_nd),
                dimension=dimension,
                board_dims=board_dims,
                render_context=render_context,
            )
            alpha, width = _trail_style_for_sample(sample, elapsed_ms=elapsed_ms)
            segments.append(
                ExplosionRenderTrailSegment(
                    tail_position_nd=tuple(float(value) for value in previous_sample.position_nd),
                    head_position_nd=tuple(float(value) for value in sample.position_nd),
                    tail_render_position=tail_render_position,
                    head_render_position=head_render_position,
                    tail_layer_weights=tail_layer_weights,
                    head_layer_weights=head_layer_weights,
                    alpha=alpha,
                    width=width,
                )
            )
        previous_sample = sample
    return tuple(segments)


def project_particle_for_render(
    particle: ExplosionParticle,
    *,
    dimension: int,
    board_dims: tuple[int, ...],
    render_context: Any | None,
) -> ExplosionRenderParticle:
    render_position, layer_weights = _project_position_for_render(
        tuple(float(value) for value in particle.position_nd),
        dimension=dimension,
        board_dims=board_dims,
        render_context=render_context,
    )
    trail_segments = _render_trail_segments(
        particle,
        dimension=dimension,
        board_dims=board_dims,
        render_context=render_context,
        elapsed_ms=float(getattr(particle, "trail_elapsed_ms", 0.0)),
    )
    if render_context is None or int(dimension) < 4:
        return ExplosionRenderParticle(
            particle_id=particle.particle_id,
            source_coord=particle.source_coord,
            position_nd=particle.position_nd,
            render_position=render_position,
            rotation_deg=particle.rotation_deg,
            alpha=1.0,
            color_id=particle.color_id,
            trail_segments=trail_segments,
        )
    return ExplosionRenderParticle(
        particle_id=particle.particle_id,
        source_coord=particle.source_coord,
        position_nd=particle.position_nd,
        render_position=render_position,
        rotation_deg=particle.rotation_deg,
        alpha=1.0,
        color_id=particle.color_id,
        layer_weights=layer_weights,
        trail_segments=trail_segments,
    )


def render_particles(
    particles: tuple[ExplosionParticle, ...] | list[ExplosionParticle],
    *,
    dimension: int,
    board_dims: tuple[int, ...],
    render_context: Any | None,
) -> tuple[ExplosionRenderParticle, ...]:
    return tuple(
        project_particle_for_render(
            particle,
            dimension=dimension,
            board_dims=board_dims,
            render_context=render_context,
        )
        for particle in particles
    )
