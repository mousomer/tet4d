from __future__ import annotations

import math
import random

from tet4d.ui.pygame.render.board_boundary import board_boundary_coordinate, board_boundary_limits

from .model import (
    EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
    EXPLOSION_PARTICLE_COLLISIONS_ON,
    EXPLOSION_TRAIL_MAX_LIFETIME_MS,
    EXPLOSION_TRAIL_MAX_SAMPLES,
    EXPLOSION_TRAIL_MIN_MOVEMENT_SPACING,
    EXPLOSION_TRAIL_MIN_TIME_SPACING_MS,
    ExplosionAudioEvent,
    ExplosionParticle,
    ExplosionSeedCell,
    ExplosionSimulationState,
    ExplosionTrailSample,
    StandaloneExplosionConfig,
    clamp_trace_retention_ms,
    normalize_boundary_response,
    normalize_particle_collisions,
    speed_scale_for_preset,
    trail_sample_budget_for_lifetime_ms,
)
from .topology import ExplosionTopologyAdapter, build_explosion_topology_adapter

_EPSILON = 1e-6
_MAX_BOUNDARY_EVENTS_PER_STEP = 12
_BOUNDARY_RESTITUTION = 1.0
_COLLISION_RESTITUTION = 1.0
_COLLISION_DAMPING = 1.0
_POST_CONTACT_TIME_EPSILON = 1e-6
_INTERIOR_POSITION_EPSILON = 1e-5


def _vec_add(left, right):
    return tuple(a + b for a, b in zip(left, right))


def _vec_sub(left, right):
    return tuple(a - b for a, b in zip(left, right))


def _vec_mul(value, scalar):
    return tuple(component * scalar for component in value)


def _vec_dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def _vec_len(value) -> float:
    return math.sqrt(sum(component * component for component in value))


def total_kinetic_energy_for_particles(
    particles: list[ExplosionParticle] | tuple[ExplosionParticle, ...],
) -> float:
    total = 0.0
    for particle in particles:
        if not particle.active:
            continue
        speed_sq = sum(float(component) * float(component) for component in particle.velocity_nd)
        total += 0.5 * float(particle.collision_mass) * speed_sq
    return float(total)


def _normalize(value, *, default):
    length = _vec_len(value)
    if length <= _EPSILON:
        return tuple(default)
    return tuple(component / length for component in value)


def _random_unit_vector(randomizer: random.Random, *, dimension: int) -> tuple[float, ...]:
    raw = tuple(randomizer.uniform(-1.0, 1.0) for _ in range(max(1, int(dimension))))
    default = tuple(1.0 if axis == 0 else 0.0 for axis in range(max(1, int(dimension))))
    return _normalize(raw, default=default)


def _pad_rotation(value: tuple[float, ...]) -> tuple[float, float, float]:
    padded = tuple(value) + (0.0, 0.0, 0.0)
    return (float(padded[0]), float(padded[1]), float(padded[2]))


def _initial_particle(
    *,
    particle_id: int,
    cell: ExplosionSeedCell,
    board_center: tuple[float, ...],
    randomizer: random.Random,
    launch_speed_scale: float,
    trace_retention_ms: float,
) -> ExplosionParticle:
    origin = tuple(float(value) for value in cell.source_coord)
    outward = _normalize(
        _vec_sub(origin, board_center),
        default=tuple(1.0 if axis == 1 else 0.0 for axis in range(len(origin))),
    )
    random_vec = _random_unit_vector(randomizer, dimension=len(origin))
    direction = _normalize(
        _vec_add(_vec_mul(outward, 0.7), _vec_mul(random_vec, 0.9)),
        default=outward,
    )
    speed = randomizer.uniform(2.6, 4.8) * max(0.05, float(launch_speed_scale))
    angular = _pad_rotation(
        tuple(randomizer.uniform(-220.0, 220.0) for _ in range(3))
    )
    return ExplosionParticle(
        particle_id=int(particle_id),
        source_coord=tuple(int(value) for value in cell.source_coord),
        position_nd=origin,
        velocity_nd=_vec_mul(direction, speed),
        color_id=int(cell.color_id),
        source_group_id=cell.source_group_id,
        rotation_deg=(0.0, 0.0, 0.0),
        angular_velocity_deg=angular,
        collision_radius=randomizer.uniform(0.24, 0.36),
        collision_mass=randomizer.uniform(0.9, 1.1),
        trail_max_lifetime_ms=clamp_trace_retention_ms(trace_retention_ms),
        trail_max_samples=trail_sample_budget_for_lifetime_ms(trace_retention_ms),
        trail_samples=[
            ExplosionTrailSample(
                position_nd=origin,
                elapsed_ms=0.0,
            )
        ],
    )


def _trim_trail_samples(
    particle: ExplosionParticle,
    *,
    elapsed_ms: float,
) -> None:
    max_lifetime_ms = max(
        EXPLOSION_TRAIL_MIN_TIME_SPACING_MS,
        float(getattr(particle, "trail_max_lifetime_ms", EXPLOSION_TRAIL_MAX_LIFETIME_MS)),
    )
    max_samples = max(
        1,
        int(getattr(particle, "trail_max_samples", EXPLOSION_TRAIL_MAX_SAMPLES)),
    )
    cutoff = float(elapsed_ms) - max_lifetime_ms
    samples = [
        sample
        for sample in particle.trail_samples
        if float(sample.elapsed_ms) >= cutoff
    ]
    if not samples:
        samples = [
            ExplosionTrailSample(
                position_nd=tuple(float(value) for value in particle.position_nd),
                elapsed_ms=float(elapsed_ms),
            )
        ]
    if len(samples) > max_samples:
        samples = samples[-max_samples:]
    particle.trail_samples = samples
    particle.trail_elapsed_ms = float(elapsed_ms)


def _record_trail_sample(
    particle: ExplosionParticle,
    *,
    elapsed_ms: float,
    position_nd: tuple[float, ...] | None = None,
    segment_break: bool = False,
    force: bool = False,
) -> None:
    sample_position = tuple(
        float(value)
        for value in (
            particle.position_nd if position_nd is None else tuple(position_nd)
        )
    )
    particle.trail_elapsed_ms = float(elapsed_ms)
    if not force and particle.trail_samples:
        last_sample = next(
            (
                sample
                for sample in reversed(particle.trail_samples)
                if not sample.segment_break
            ),
            None,
        )
        if last_sample is not None:
            elapsed_delta = float(elapsed_ms) - float(last_sample.elapsed_ms)
            distance_delta = _vec_len(
                _vec_sub(sample_position, tuple(last_sample.position_nd))
            )
            if (
                elapsed_delta < EXPLOSION_TRAIL_MIN_TIME_SPACING_MS
                or distance_delta < EXPLOSION_TRAIL_MIN_MOVEMENT_SPACING
            ):
                _trim_trail_samples(particle, elapsed_ms=elapsed_ms)
                return
    particle.trail_samples.append(
        ExplosionTrailSample(
            position_nd=sample_position,
            elapsed_ms=float(elapsed_ms),
            segment_break=bool(segment_break),
        )
    )
    _trim_trail_samples(particle, elapsed_ms=elapsed_ms)


def _record_seam_break(
    particle: ExplosionParticle,
    *,
    elapsed_ms: float,
    pre_seam_position: tuple[float, ...],
    post_seam_position: tuple[float, ...],
) -> None:
    _record_trail_sample(
        particle,
        elapsed_ms=elapsed_ms,
        position_nd=pre_seam_position,
        force=True,
    )
    _record_trail_sample(
        particle,
        elapsed_ms=elapsed_ms,
        position_nd=post_seam_position,
        segment_break=True,
        force=True,
    )
    _record_trail_sample(
        particle,
        elapsed_ms=elapsed_ms,
        position_nd=post_seam_position,
        force=True,
    )


def build_simulation(
    config: StandaloneExplosionConfig,
) -> tuple[ExplosionSimulationState, ExplosionTopologyAdapter]:
    boundary_response = normalize_boundary_response(config.boundary_response)
    particle_collisions = normalize_particle_collisions(config.particle_collisions)
    topology = build_explosion_topology_adapter(config.topology)
    randomizer = random.Random(int(config.random_seed))
    preset_scale = speed_scale_for_preset(config.speed_preset)
    launch_speed_scale = float(config.launch_speed_scale) * preset_scale
    board_center = tuple((float(size) - 1.0) * 0.5 for size in config.topology.board_dims)
    particles = [
        _initial_particle(
            particle_id=index,
            cell=cell,
            board_center=board_center,
            randomizer=randomizer,
            launch_speed_scale=launch_speed_scale,
            trace_retention_ms=float(config.trace_retention_ms),
        )
        for index, cell in enumerate(config.occupied_cells)
    ]
    return (
        ExplosionSimulationState(
            dimension=int(config.dimension),
            board_dims=tuple(int(value) for value in config.topology.board_dims),
            boundary_response=boundary_response,
            particle_collisions=particle_collisions,
            particles=particles,
            total_kinetic_energy=total_kinetic_energy_for_particles(particles),
        ),
        topology,
    )


def _boundary_time(position, velocity, board_dims):
    best_time = math.inf
    best_axis = -1
    best_side = ""
    for axis in range(len(board_dims)):
        component = float(velocity[axis])
        if abs(component) <= _EPSILON:
            continue
        limit = board_boundary_coordinate(
            dims=board_dims,
            axis=axis,
            side="-" if component < 0.0 else "+",
        )
        delta = limit - float(position[axis])
        candidate = delta / component
        if candidate < -_EPSILON or candidate >= best_time - _EPSILON:
            continue
        best_time = max(0.0, float(candidate))
        best_axis = axis
        best_side = "-" if component < 0.0 else "+"
    return best_time, best_axis, best_side


def _advance_rotation(particle: ExplosionParticle, dt_seconds: float) -> None:
    particle.rotation_deg = tuple(
        (float(current) + (float(speed) * dt_seconds)) % 360.0
        for current, speed in zip(
            particle.rotation_deg,
            particle.angular_velocity_deg,
        )
    )


def _boundary_limit_for(axis: int, side: str, board_dims: tuple[int, ...]) -> float:
    return board_boundary_coordinate(dims=board_dims, axis=axis, side=side)


def _move_to_interior_boundary_position(
    position: tuple[float, ...],
    *,
    axis: int,
    side: str,
    board_dims: tuple[int, ...],
) -> tuple[float, ...]:
    adjusted = list(float(value) for value in position)
    limit = _boundary_limit_for(axis, side, board_dims)
    adjusted[axis] = (
        limit + _INTERIOR_POSITION_EPSILON
        if side == "-"
        else limit - _INTERIOR_POSITION_EPSILON
    )
    return tuple(adjusted)


def _clamp_position_to_board_interior(
    position: tuple[float, ...],
    *,
    board_dims: tuple[int, ...],
) -> tuple[float, ...]:
    clamped: list[float] = []
    for axis, (low, high) in enumerate(board_boundary_limits(board_dims)):
        low += _INTERIOR_POSITION_EPSILON
        high -= _INTERIOR_POSITION_EPSILON
        clamped.append(min(max(float(position[axis]), low), high))
    return tuple(clamped)


def _step_particle(
    particle: ExplosionParticle,
    *,
    dt_seconds: float,
    adapter: ExplosionTopologyAdapter,
    boundary_response: str,
    elapsed_ms: float,
) -> tuple[ExplosionAudioEvent, ...]:
    if not particle.active:
        return tuple()
    _advance_rotation(particle, dt_seconds)
    if particle.escaped:
        particle.position_nd = _vec_add(
            particle.position_nd,
            _vec_mul(particle.velocity_nd, dt_seconds),
        )
        return tuple()
    remaining = float(dt_seconds)
    events: list[ExplosionAudioEvent] = []
    for _ in range(_MAX_BOUNDARY_EVENTS_PER_STEP):
        hit_time, axis, side = _boundary_time(
            particle.position_nd,
            particle.velocity_nd,
            adapter.board_dims,
        )
        if axis < 0 or hit_time > remaining:
            particle.position_nd = _vec_add(
                particle.position_nd,
                _vec_mul(particle.velocity_nd, remaining),
            )
            return tuple(events)
        particle.position_nd = _vec_add(
            particle.position_nd,
            _vec_mul(particle.velocity_nd, hit_time),
        )
        remaining = max(0.0, remaining - hit_time)
        boundary = adapter.seam_for_boundary(
            __import__("tet4d.engine.topology_explorer.glue_model", fromlist=["BoundaryRef"]).BoundaryRef(
                dimension=len(adapter.board_dims),
                axis=axis,
                side=side,
            )
        )
        if boundary is not None:
            pre_seam_position = tuple(float(value) for value in particle.position_nd)
            particle.position_nd = boundary.transform_position(particle.position_nd)
            particle.velocity_nd = boundary.transform_velocity(particle.velocity_nd)
            _record_seam_break(
                particle,
                elapsed_ms=elapsed_ms,
                pre_seam_position=pre_seam_position,
                post_seam_position=tuple(
                    float(value) for value in particle.position_nd
                ),
            )
            events.append(
                ExplosionAudioEvent(
                    family="seam",
                    strength=max(0.6, _vec_len(particle.velocity_nd)),
                )
            )
            remaining = max(0.0, remaining - min(remaining, _POST_CONTACT_TIME_EPSILON))
            continue
        if boundary_response == EXPLOSION_BOUNDARY_RESPONSE_ESCAPE:
            particle.escaped = True
            particle.position_nd = _vec_add(
                particle.position_nd,
                _vec_mul(particle.velocity_nd, remaining),
            )
            return tuple(events)
        velocity = list(particle.velocity_nd)
        velocity[axis] = -float(velocity[axis]) * _BOUNDARY_RESTITUTION
        particle.velocity_nd = tuple(velocity)
        particle.position_nd = _move_to_interior_boundary_position(
            particle.position_nd,
            axis=axis,
            side=side,
            board_dims=adapter.board_dims,
        )
        events.append(
            ExplosionAudioEvent(
                family="bounce",
                strength=max(0.4, abs(float(velocity[axis]))),
            )
        )
        remaining = max(0.0, remaining - min(remaining, _POST_CONTACT_TIME_EPSILON))
        if remaining <= _EPSILON:
            return tuple(events)
    particle.position_nd = _vec_add(
        particle.position_nd,
        _vec_mul(particle.velocity_nd, remaining),
    )
    if boundary_response != EXPLOSION_BOUNDARY_RESPONSE_ESCAPE:
        particle.position_nd = _clamp_position_to_board_interior(
            particle.position_nd,
            board_dims=adapter.board_dims,
        )
    return tuple(events)


def _resolve_collisions(particles: list[ExplosionParticle]) -> tuple[ExplosionAudioEvent, ...]:
    if len(particles) < 2:
        return tuple()
    events: list[ExplosionAudioEvent] = []
    ordered = sorted(particles, key=lambda particle: particle.particle_id)
    for left_index, left in enumerate(ordered):
        for right in ordered[left_index + 1 :]:
            delta = _vec_sub(right.position_nd, left.position_nd)
            distance = _vec_len(delta)
            minimum = float(left.collision_radius) + float(right.collision_radius)
            if distance >= minimum:
                continue
            normal = _normalize(
                delta,
                default=tuple(
                    1.0 if axis == (right.particle_id + left.particle_id) % len(left.position_nd) else 0.0
                    for axis in range(len(left.position_nd))
                ),
            )
            overlap = max(0.0, minimum - distance)
            total_mass = max(0.001, float(left.collision_mass) + float(right.collision_mass))
            left_share = float(right.collision_mass) / total_mass
            right_share = float(left.collision_mass) / total_mass
            left.position_nd = _vec_sub(left.position_nd, _vec_mul(normal, overlap * left_share))
            right.position_nd = _vec_add(right.position_nd, _vec_mul(normal, overlap * right_share))
            relative_speed = _vec_dot(_vec_sub(right.velocity_nd, left.velocity_nd), normal)
            if relative_speed < 0.0:
                impulse = -((1.0 + _COLLISION_RESTITUTION) * relative_speed) / total_mass
                left.velocity_nd = _vec_mul(
                    _vec_sub(
                        left.velocity_nd,
                        _vec_mul(normal, impulse * float(right.collision_mass)),
                    ),
                    _COLLISION_DAMPING,
                )
                right.velocity_nd = _vec_mul(
                    _vec_add(
                        right.velocity_nd,
                        _vec_mul(normal, impulse * float(left.collision_mass)),
                    ),
                    _COLLISION_DAMPING,
                )
                events.append(
                    ExplosionAudioEvent(
                        family="collision",
                        strength=max(0.35, abs(relative_speed)),
                    )
                )
    return tuple(events)


def step_simulation(
    state: ExplosionSimulationState,
    *,
    adapter: ExplosionTopologyAdapter,
    dt_ms: float,
    time_scale: float,
) -> tuple[ExplosionAudioEvent, ...]:
    dt_seconds = max(0.0, float(dt_ms)) * max(0.05, float(time_scale)) / 1000.0
    state.elapsed_ms += max(0.0, float(dt_ms))
    if dt_seconds <= 0.0:
        return tuple()
    events: list[ExplosionAudioEvent] = []
    for particle in state.particles:
        events.extend(
            _step_particle(
                particle,
                dt_seconds=dt_seconds,
                adapter=adapter,
                boundary_response=state.boundary_response,
                elapsed_ms=state.elapsed_ms,
            )
        )
    if state.particle_collisions == EXPLOSION_PARTICLE_COLLISIONS_ON:
        events.extend(_resolve_collisions(state.particles))
    for particle in state.particles:
        if not particle.active:
            continue
        _record_trail_sample(
            particle,
            elapsed_ms=state.elapsed_ms,
        )
    state.total_kinetic_energy = total_kinetic_energy_for_particles(state.particles)
    return tuple(events)
