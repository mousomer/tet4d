from __future__ import annotations

import math
from typing import Any

from .model import ExplosionParticle, ExplosionRenderParticle


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


def project_particle_for_render(
    particle: ExplosionParticle,
    *,
    dimension: int,
    board_dims: tuple[int, ...],
    render_context: Any | None,
) -> ExplosionRenderParticle:
    if render_context is None or int(dimension) < 4:
        return ExplosionRenderParticle(
            particle_id=particle.particle_id,
            source_coord=particle.source_coord,
            position_nd=particle.position_nd,
            render_position=_pad_vec3(particle.position_nd),
            rotation_deg=particle.rotation_deg,
            alpha=1.0,
            color_id=particle.color_id,
        )
    axis_map = getattr(render_context, "basis_axis_map", ()) or (
        (0, 1),
        (1, 1),
        (2, 1),
        (3, 1),
    )
    mapped: list[float] = []
    for axis, sign in axis_map[:4]:
        axis_index = int(axis)
        value = (
            float(particle.position_nd[axis_index])
            if 0 <= axis_index < len(particle.position_nd)
            else 0.0
        )
        size = float(board_dims[axis_index]) if 0 <= axis_index < len(board_dims) else 1.0
        mapped.append(value if int(sign) > 0 else (size - 1.0 - value))
    while len(mapped) < 4:
        mapped.append(0.0)
    return ExplosionRenderParticle(
        particle_id=particle.particle_id,
        source_coord=particle.source_coord,
        position_nd=particle.position_nd,
        render_position=(mapped[0], mapped[1], mapped[2]),
        rotation_deg=particle.rotation_deg,
        alpha=1.0,
        color_id=particle.color_id,
        layer_weights=_layer_weights_for_value(
            mapped[3],
            layer_count=max(1, int(getattr(render_context, "layer_count", 1))),
        ),
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

