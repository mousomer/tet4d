from __future__ import annotations

import math
import random

from tet4d.ui.pygame.render.board_boundary import board_boundary_coordinate, board_boundary_limits

from .model import (
    EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
    EXPLOSION_DIAGNOSTICS_MODE_FULL,
    EXPLOSION_DIAGNOSTICS_MODE_OFF,
    EXPLOSION_MASS_MODE_RANDOM,
    EXPLOSION_PARTICLE_COLLISIONS_ON,
    EXPLOSION_TRAIL_MAX_LIFETIME_MS,
    EXPLOSION_TRAIL_MAX_SAMPLES,
    EXPLOSION_TRAIL_MIN_MOVEMENT_SPACING,
    EXPLOSION_TRAIL_MIN_TIME_SPACING_MS,
    ExplosionAudioEvent,
    ExplosionDiagnosticsEvent,
    ExplosionDiagnosticsSummary,
    ExplosionParticle,
    ExplosionParticleDiagnostics,
    ExplosionSeedCell,
    ExplosionSimulationState,
    ExplosionTrailSample,
    StandaloneExplosionConfig,
    clamp_trace_retention_ms,
    clamp_collision_elasticity,
    clamp_mass_value,
    normalize_mass_mode,
    normalize_mass_range,
    normalize_boundary_response,
    normalize_diagnostics_mode,
    normalize_particle_collisions,
    speed_scale_for_preset,
    trail_sample_budget_for_lifetime_ms,
)
from .topology import ExplosionTopologyAdapter, build_explosion_topology_adapter

_EPSILON = 1e-6
_MAX_BOUNDARY_EVENTS_PER_STEP = 12
_BOUNDARY_RESTITUTION = 1.0
_COLLISION_DAMPING = 1.0
_POST_CONTACT_TIME_EPSILON = 1e-6
_INTERIOR_POSITION_EPSILON = 1e-5
_DIAGNOSTIC_ENERGY_TOLERANCE = 1e-5
_DIAGNOSTIC_SPEED_DROP_TOLERANCE = 0.25
_DIAGNOSTIC_HEADING_DELTA_DEG = 2.0
_DIAGNOSTIC_MAX_EVENTS = 12


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


def _vec_unit(value):
    length = _vec_len(value)
    if length <= _EPSILON:
        return None
    return tuple(component / length for component in value)


def _heading_delta_deg(before, after) -> float:
    before_unit = _vec_unit(before)
    after_unit = _vec_unit(after)
    if before_unit is None or after_unit is None:
        return 0.0
    dot = max(-1.0, min(1.0, _vec_dot(before_unit, after_unit)))
    return math.degrees(math.acos(dot))


def total_kinetic_energy_for_particles(
    particles: list[ExplosionParticle] | tuple[ExplosionParticle, ...],
) -> float:
    return float(0.5 * velocity_norm_sq_sum_for_particles(particles, weighted_by_mass=True))


def _active_particles(
    particles: list[ExplosionParticle] | tuple[ExplosionParticle, ...],
) -> tuple[ExplosionParticle, ...]:
    return tuple(particle for particle in particles if particle.active)


def _speed_sq_for_particle(particle: ExplosionParticle) -> float:
    return float(
        sum(float(component) * float(component) for component in particle.velocity_nd)
    )


def velocity_norm_sq_sum_for_particles(
    particles: list[ExplosionParticle] | tuple[ExplosionParticle, ...],
    *,
    weighted_by_mass: bool = False,
) -> float:
    total = 0.0
    for particle in _active_particles(particles):
        speed_sq = _speed_sq_for_particle(particle)
        if weighted_by_mass:
            total += float(particle.collision_mass) * speed_sq
        else:
            total += speed_sq
    return float(total)


def kinetic_energy_formula_text_for_particles(
    particles: list[ExplosionParticle] | tuple[ExplosionParticle, ...],
    *,
    max_terms: int = 4,
) -> str:
    active_particles = _active_particles(particles)
    if not active_particles:
        return "K = 0.00 = 1/2 m [0.00]"
    speed_terms = tuple(_vec_len(tuple(float(value) for value in particle.velocity_nd)) for particle in active_particles)
    masses = tuple(float(particle.collision_mass) for particle in active_particles)
    energy = total_kinetic_energy_for_particles(active_particles)
    shown_terms = max(1, int(max_terms))
    uniform_mass = all(
        abs(mass - masses[0]) <= _EPSILON
        for mass in masses[1:]
    )
    if uniform_mass:
        terms = [f"{speed_terms[index]:.2f}^2" for index in range(min(len(speed_terms), shown_terms))]
        if len(speed_terms) > shown_terms:
            terms.append("...")
        return f"K = {energy:.2f} = 1/2 {masses[0]:.2f} [{ ' + '.join(terms) }]"
    weighted_terms = [
        f"{masses[index]:.2f}*{speed_terms[index]:.2f}^2"
        for index in range(min(len(speed_terms), shown_terms))
    ]
    if len(speed_terms) > shown_terms:
        weighted_terms.append("...")
    return f"K = {energy:.2f} = 1/2 [{' + '.join(weighted_terms)}]"


def weighted_speed_sq_sum_text_for_particles(
    particles: list[ExplosionParticle] | tuple[ExplosionParticle, ...],
) -> str:
    return f"Σ(m_i||v_i||^2) = {velocity_norm_sq_sum_for_particles(particles, weighted_by_mass=True):.2f}"


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
    mass_mode: str,
    base_mass: float,
    random_mass_min: float,
    random_mass_max: float,
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
    mass = (
        randomizer.uniform(random_mass_min, random_mass_max)
        if mass_mode == EXPLOSION_MASS_MODE_RANDOM
        else base_mass
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
        collision_mass=mass,
        trail_max_lifetime_ms=clamp_trace_retention_ms(trace_retention_ms),
        trail_max_samples=trail_sample_budget_for_lifetime_ms(trace_retention_ms),
        trail_samples=[
            ExplosionTrailSample(
                position_nd=origin,
                elapsed_ms=0.0,
            )
        ],
    )


def assign_particle_masses(
    particles: list[ExplosionParticle] | tuple[ExplosionParticle, ...],
    *,
    random_seed: int,
    mass_mode: str,
    base_mass: float,
    random_mass_min: float,
    random_mass_max: float,
) -> None:
    resolved_mode = normalize_mass_mode(mass_mode)
    resolved_base_mass = clamp_mass_value(base_mass)
    resolved_min, resolved_max = normalize_mass_range(random_mass_min, random_mass_max)
    randomizer = random.Random(int(random_seed))
    for particle in particles:
        particle.collision_mass = (
            randomizer.uniform(resolved_min, resolved_max)
            if resolved_mode == EXPLOSION_MASS_MODE_RANDOM
            else resolved_base_mass
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


def _record_boundary_bounce(
    particle: ExplosionParticle,
    *,
    elapsed_ms: float,
    contact_position: tuple[float, ...],
) -> None:
    _record_trail_sample(
        particle,
        elapsed_ms=elapsed_ms,
        position_nd=contact_position,
        force=True,
    )


def _set_position_velocity_snapshot(
    diagnostics: dict[str, object] | None,
    *,
    position_key: str,
    velocity_key: str,
    position: tuple[float, ...],
    velocity: tuple[float, ...],
    overwrite: bool = True,
) -> None:
    if diagnostics is None:
        return
    if overwrite:
        diagnostics[position_key] = tuple(float(value) for value in position)
        diagnostics[velocity_key] = tuple(float(value) for value in velocity)
        return
    diagnostics.setdefault(position_key, tuple(float(value) for value in position))
    diagnostics.setdefault(velocity_key, tuple(float(value) for value in velocity))


def _particle_energy_for_velocity(
    particle: ExplosionParticle,
    velocity: tuple[float, ...],
) -> float:
    return 0.5 * float(particle.collision_mass) * _vec_dot(velocity, velocity)


def _diagnostics_event(
    events: list[ExplosionDiagnosticsEvent],
    *,
    step_index: int,
    particle_id: int,
    stage: str,
    message: str,
) -> None:
    events.append(
        ExplosionDiagnosticsEvent(
            step_index=int(step_index),
            particle_id=int(particle_id),
            stage=str(stage),
            message=str(message),
        )
    )


def _k_for_particle(particle: ExplosionParticle) -> float:
    return 0.5 * float(particle.collision_mass) * _speed_sq_for_particle(particle)


def _finish_without_contact(
    particle: ExplosionParticle,
    *,
    remaining: float,
    elapsed_ms: float,
    force_end_trail_sample: bool,
    boundary_response: str,
    board_dims: tuple[int, ...],
    diagnostics: dict[str, object] | None,
) -> tuple[ExplosionAudioEvent, ...]:
    _finish_particle_step(
        particle,
        remaining=remaining,
        elapsed_ms=elapsed_ms,
        force_end_trail_sample=force_end_trail_sample,
        boundary_response=boundary_response,
        board_dims=board_dims,
    )
    _set_position_velocity_snapshot(
        diagnostics,
        position_key="after_free_flight_position",
        velocity_key="after_free_flight_velocity",
        position=particle.position_nd,
        velocity=particle.velocity_nd,
        overwrite=False,
    )
    _set_position_velocity_snapshot(
        diagnostics,
        position_key="after_finalize_position",
        velocity_key="after_finalize_velocity",
        position=particle.position_nd,
        velocity=particle.velocity_nd,
    )
    return tuple()


def _handle_seam_contact(
    particle: ExplosionParticle,
    *,
    boundary,
    elapsed_ms: float,
    diagnostics: dict[str, object] | None,
) -> ExplosionAudioEvent:
    pre_seam_position = tuple(float(value) for value in particle.position_nd)
    particle.position_nd = boundary.transform_position(particle.position_nd)
    particle.velocity_nd = boundary.transform_velocity(particle.velocity_nd)
    if diagnostics is not None:
        diagnostics["contact_count"] = int(diagnostics.get("contact_count", 0)) + 1
        diagnostics["last_contact_type"] = "seam"
        diagnostics["last_contact_normal"] = None
    _set_position_velocity_snapshot(
        diagnostics,
        position_key="after_seam_position",
        velocity_key="after_seam_velocity",
        position=particle.position_nd,
        velocity=particle.velocity_nd,
    )
    _record_seam_break(
        particle,
        elapsed_ms=elapsed_ms,
        pre_seam_position=pre_seam_position,
        post_seam_position=tuple(float(value) for value in particle.position_nd),
    )
    return ExplosionAudioEvent(
        family="seam",
        strength=max(0.6, _vec_len(particle.velocity_nd)),
    )


def _handle_boundary_contact(
    particle: ExplosionParticle,
    *,
    axis: int,
    side: str,
    remaining: float,
    boundary_response: str,
    board_dims: tuple[int, ...],
    elapsed_ms: float,
    diagnostics: dict[str, object] | None,
) -> tuple[bool, ExplosionAudioEvent | None]:
    if boundary_response == EXPLOSION_BOUNDARY_RESPONSE_ESCAPE:
        particle.escaped = True
        particle.position_nd = _vec_add(
            particle.position_nd,
            _vec_mul(particle.velocity_nd, remaining),
        )
        _set_position_velocity_snapshot(
            diagnostics,
            position_key="after_boundary_position",
            velocity_key="after_boundary_velocity",
            position=particle.position_nd,
            velocity=particle.velocity_nd,
        )
        _set_position_velocity_snapshot(
            diagnostics,
            position_key="after_finalize_position",
            velocity_key="after_finalize_velocity",
            position=particle.position_nd,
            velocity=particle.velocity_nd,
        )
        return True, None
    contact_position = tuple(float(value) for value in particle.position_nd)
    velocity = list(particle.velocity_nd)
    velocity[axis] = -float(velocity[axis]) * _BOUNDARY_RESTITUTION
    particle.velocity_nd = tuple(velocity)
    _record_boundary_bounce(
        particle,
        elapsed_ms=elapsed_ms,
        contact_position=contact_position,
    )
    particle.position_nd = _move_to_interior_boundary_position(
        particle.position_nd,
        axis=axis,
        side=side,
        board_dims=board_dims,
    )
    if diagnostics is not None:
        normal = [0.0] * len(board_dims)
        normal[axis] = -1.0 if side == "+" else 1.0
        diagnostics["contact_count"] = int(diagnostics.get("contact_count", 0)) + 1
        diagnostics["last_contact_type"] = "boundary"
        diagnostics["last_contact_normal"] = tuple(normal)
    _set_position_velocity_snapshot(
        diagnostics,
        position_key="after_boundary_position",
        velocity_key="after_boundary_velocity",
        position=particle.position_nd,
        velocity=particle.velocity_nd,
    )
    return False, ExplosionAudioEvent(
        family="bounce",
        strength=max(0.4, abs(float(velocity[axis]))),
    )


def build_simulation(
    config: StandaloneExplosionConfig,
) -> tuple[ExplosionSimulationState, ExplosionTopologyAdapter]:
    boundary_response = normalize_boundary_response(config.boundary_response)
    particle_collisions = normalize_particle_collisions(config.particle_collisions)
    mass_mode = normalize_mass_mode(config.mass_mode)
    base_mass = clamp_mass_value(config.base_mass)
    random_mass_min, random_mass_max = normalize_mass_range(
        config.random_mass_min,
        config.random_mass_max,
    )
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
            mass_mode=mass_mode,
            base_mass=base_mass,
            random_mass_min=random_mass_min,
            random_mass_max=random_mass_max,
        )
        for index, cell in enumerate(config.occupied_cells)
    ]
    assign_particle_masses(
        particles,
        random_seed=int(config.random_seed),
        mass_mode=mass_mode,
        base_mass=base_mass,
        random_mass_min=random_mass_min,
        random_mass_max=random_mass_max,
    )
    return (
        ExplosionSimulationState(
            dimension=int(config.dimension),
            board_dims=tuple(int(value) for value in config.topology.board_dims),
            boundary_response=boundary_response,
            particle_collisions=particle_collisions,
            collision_elasticity=clamp_collision_elasticity(config.collision_elasticity),
            particles=particles,
            velocity_norm_sq_sum=velocity_norm_sq_sum_for_particles(particles),
            total_kinetic_energy=total_kinetic_energy_for_particles(particles),
            diagnostics_mode=normalize_diagnostics_mode(config.diagnostics_mode),
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


def _finish_particle_step(
    particle: ExplosionParticle,
    *,
    remaining: float,
    elapsed_ms: float,
    force_end_trail_sample: bool,
    boundary_response: str,
    board_dims: tuple[int, ...],
) -> None:
    particle.position_nd = _vec_add(
        particle.position_nd,
        _vec_mul(particle.velocity_nd, remaining),
    )
    if boundary_response != EXPLOSION_BOUNDARY_RESPONSE_ESCAPE:
        particle.position_nd = _clamp_position_to_board_interior(
            particle.position_nd,
            board_dims=board_dims,
        )
    if force_end_trail_sample:
        _record_trail_sample(
            particle,
            elapsed_ms=elapsed_ms,
            force=True,
        )


def _step_particle(
    particle: ExplosionParticle,
    *,
    dt_seconds: float,
    adapter: ExplosionTopologyAdapter,
    boundary_response: str,
    elapsed_ms: float,
    diagnostics: dict[str, object] | None = None,
) -> tuple[ExplosionAudioEvent, ...]:
    if not particle.active:
        return tuple()
    _set_position_velocity_snapshot(
        diagnostics,
        position_key="before_position",
        velocity_key="before_velocity",
        position=particle.position_nd,
        velocity=particle.velocity_nd,
    )
    _advance_rotation(particle, dt_seconds)
    if particle.escaped:
        particle.position_nd = _vec_add(
            particle.position_nd,
            _vec_mul(particle.velocity_nd, dt_seconds),
        )
        _set_position_velocity_snapshot(
            diagnostics,
            position_key="after_free_flight_position",
            velocity_key="after_free_flight_velocity",
            position=particle.position_nd,
            velocity=particle.velocity_nd,
        )
        _set_position_velocity_snapshot(
            diagnostics,
            position_key="after_finalize_position",
            velocity_key="after_finalize_velocity",
            position=particle.position_nd,
            velocity=particle.velocity_nd,
        )
        return tuple()
    remaining = float(dt_seconds)
    events: list[ExplosionAudioEvent] = []
    force_end_trail_sample = False
    for _ in range(_MAX_BOUNDARY_EVENTS_PER_STEP):
        hit_time, axis, side = _boundary_time(
            particle.position_nd,
            particle.velocity_nd,
            adapter.board_dims,
        )
        if axis < 0 or hit_time > remaining:
            events.extend(
                _finish_without_contact(
                    particle,
                    remaining=remaining,
                    elapsed_ms=elapsed_ms,
                    force_end_trail_sample=force_end_trail_sample,
                    boundary_response=boundary_response,
                    board_dims=adapter.board_dims,
                    diagnostics=diagnostics,
                )
            )
            return tuple(events)
        particle.position_nd = _vec_add(
            particle.position_nd,
            _vec_mul(particle.velocity_nd, hit_time),
        )
        _set_position_velocity_snapshot(
            diagnostics,
            position_key="after_free_flight_position",
            velocity_key="after_free_flight_velocity",
            position=particle.position_nd,
            velocity=particle.velocity_nd,
            overwrite=False,
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
            events.append(
                _handle_seam_contact(
                    particle,
                    boundary=boundary,
                    elapsed_ms=elapsed_ms,
                    diagnostics=diagnostics,
                )
            )
            remaining = max(0.0, remaining - min(remaining, _POST_CONTACT_TIME_EPSILON))
            continue
        done, boundary_event = _handle_boundary_contact(
            particle,
            axis=axis,
            side=side,
            remaining=remaining,
            boundary_response=boundary_response,
            board_dims=adapter.board_dims,
            elapsed_ms=elapsed_ms,
            diagnostics=diagnostics,
        )
        if done:
            return tuple(events)
        force_end_trail_sample = True
        if boundary_event is not None:
            events.append(boundary_event)
        remaining = max(0.0, remaining - min(remaining, _POST_CONTACT_TIME_EPSILON))
        if remaining <= _EPSILON:
            return tuple(events)
    events.extend(
        _finish_without_contact(
            particle,
            remaining=remaining,
            elapsed_ms=elapsed_ms,
            force_end_trail_sample=force_end_trail_sample,
            boundary_response=boundary_response,
            board_dims=adapter.board_dims,
            diagnostics=diagnostics,
        )
    )
    return tuple(events)


def _resolve_collisions(
    particles: list[ExplosionParticle],
    *,
    collision_elasticity: float,
    collided_particle_ids: set[int] | None = None,
) -> tuple[ExplosionAudioEvent, ...]:
    if len(particles) < 2:
        return tuple()
    restitution = clamp_collision_elasticity(collision_elasticity)
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
                if collided_particle_ids is not None:
                    collided_particle_ids.add(int(left.particle_id))
                    collided_particle_ids.add(int(right.particle_id))
                impulse = -((1.0 + restitution) * relative_speed) / total_mass
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


def _build_diagnostics_summary(
    state: ExplosionSimulationState,
    *,
    before_energy: float,
    before_weighted_sum: float,
    particle_stage_data: dict[int, dict[str, object]],
    before_collision_energy: float,
    after_collision_energy: float,
    collided_particle_ids: set[int],
    seam_energy_before_after: dict[int, tuple[float, float]],
    boundary_energy_before_after: dict[int, tuple[float, float]],
    finalize_energy_before_after: dict[int, tuple[float, float]],
) -> ExplosionDiagnosticsSummary:
    mode = normalize_diagnostics_mode(state.diagnostics_mode)
    if mode == EXPLOSION_DIAGNOSTICS_MODE_OFF:
        return ExplosionDiagnosticsSummary(
            diagnostics_mode=mode,
            step_index=int(state.diagnostics_step_index),
            kinetic_energy=float(state.total_kinetic_energy),
            weighted_speed_sq_sum=float(state.velocity_norm_sq_sum),
            delta_kinetic_energy=float(state.total_kinetic_energy - before_energy),
            contact_count=0,
            suspicious_count=0,
        )
    step_events: list[ExplosionDiagnosticsEvent] = []
    particle_details: list[ExplosionParticleDiagnostics] = []
    contact_count = 0
    for particle in state.particles:
        if not particle.active:
            continue
        detail, particle_events, particle_contacts = _particle_diagnostics_for_step(
            state,
            particle=particle,
            data=particle_stage_data.get(particle.particle_id, {}),
            collided_particle_ids=collided_particle_ids,
            seam_energy_before_after=seam_energy_before_after,
            boundary_energy_before_after=boundary_energy_before_after,
            finalize_energy_before_after=finalize_energy_before_after,
        )
        particle_details.append(detail)
        step_events.extend(particle_events)
        contact_count += particle_contacts
    restitution = clamp_collision_elasticity(state.collision_elasticity)
    collision_delta = after_collision_energy - before_collision_energy
    step_events.extend(
        _collision_diagnostics_events(
            state,
            restitution=restitution,
            collision_delta=collision_delta,
        )
    )
    recent_events = (state.diagnostics_recent_events + step_events)[-_DIAGNOSTIC_MAX_EVENTS:]
    state.diagnostics_recent_events = recent_events
    focus_particle_id = next(
        (detail.particle_id for detail in particle_details if detail.flagged_this_step),
        particle_details[0].particle_id if particle_details else None,
    )
    return ExplosionDiagnosticsSummary(
        diagnostics_mode=mode,
        step_index=int(state.diagnostics_step_index),
        kinetic_energy=float(state.total_kinetic_energy),
        weighted_speed_sq_sum=float(velocity_norm_sq_sum_for_particles(state.particles, weighted_by_mass=True)),
        delta_kinetic_energy=float(state.total_kinetic_energy - before_energy),
        contact_count=int(contact_count),
        suspicious_count=len(step_events),
        particle_details=tuple(particle_details) if mode == EXPLOSION_DIAGNOSTICS_MODE_FULL else tuple(particle_details[:1]),
        recent_events=tuple(recent_events),
        focus_particle_id=focus_particle_id,
    )


def _particle_diagnostics_for_step(
    state: ExplosionSimulationState,
    *,
    particle: ExplosionParticle,
    data: dict[str, object],
    collided_particle_ids: set[int],
    seam_energy_before_after: dict[int, tuple[float, float]],
    boundary_energy_before_after: dict[int, tuple[float, float]],
    finalize_energy_before_after: dict[int, tuple[float, float]],
) -> tuple[ExplosionParticleDiagnostics, list[ExplosionDiagnosticsEvent], int]:
    step_events: list[ExplosionDiagnosticsEvent] = []
    before_velocity = tuple(data.get("before_velocity", particle.velocity_nd))
    after_velocity = tuple(data.get("after_finalize_velocity", particle.velocity_nd))
    heading_delta = _heading_delta_deg(before_velocity, after_velocity)
    speed_sq = _speed_sq_for_particle(particle)
    previous_speed_sq = float(
        state.diagnostics_previous_speed_sq_by_particle.get(particle.particle_id, speed_sq)
    )
    last_contact_type = str(data.get("last_contact_type", "none"))
    if last_contact_type == "none" and particle.particle_id in collided_particle_ids:
        last_contact_type = "collision"
    last_contact_normal = data.get("last_contact_normal")
    contact_count = int(data.get("contact_count", 0))
    if particle.particle_id in collided_particle_ids:
        contact_count += 1
    before_speed_sq = _vec_dot(before_velocity, before_velocity)
    flagged = _append_particle_motion_events(
        step_events,
        state=state,
        particle=particle,
        before_speed_sq=before_speed_sq,
        previous_speed_sq=previous_speed_sq,
        speed_sq=speed_sq,
        heading_delta=heading_delta,
        last_contact_type=last_contact_type,
        contact_count=contact_count,
        seam_energy_before_after=seam_energy_before_after,
        boundary_energy_before_after=boundary_energy_before_after,
        finalize_energy_before_after=finalize_energy_before_after,
    )
    state.diagnostics_previous_speed_sq_by_particle[particle.particle_id] = float(speed_sq)
    if contact_count > 0:
        state.diagnostics_last_contact_step_by_particle[particle.particle_id] = state.diagnostics_step_index
    return (
        ExplosionParticleDiagnostics(
            particle_id=int(particle.particle_id),
            mass=float(particle.collision_mass),
            speed_sq=float(speed_sq),
            previous_speed_sq=float(previous_speed_sq),
            heading_delta_deg=float(heading_delta),
            last_contact_type=last_contact_type,
            last_contact_normal=last_contact_normal,
            flagged_this_step=flagged,
        ),
        step_events,
        contact_count,
    )


def _append_particle_motion_events(
    events: list[ExplosionDiagnosticsEvent],
    *,
    state: ExplosionSimulationState,
    particle: ExplosionParticle,
    before_speed_sq: float,
    previous_speed_sq: float,
    speed_sq: float,
    heading_delta: float,
    last_contact_type: str,
    contact_count: int,
    seam_energy_before_after: dict[int, tuple[float, float]],
    boundary_energy_before_after: dict[int, tuple[float, float]],
    finalize_energy_before_after: dict[int, tuple[float, float]],
) -> bool:
    flagged = False
    if heading_delta > _DIAGNOSTIC_HEADING_DELTA_DEG and last_contact_type == "none":
        flagged = True
        _diagnostics_event(
            events,
            step_index=state.diagnostics_step_index,
            particle_id=particle.particle_id,
            stage="finalize",
            message=f"heading change without contact at step {state.diagnostics_step_index}",
        )
    if before_speed_sq - speed_sq > _DIAGNOSTIC_SPEED_DROP_TOLERANCE and last_contact_type == "none":
        flagged = True
        _diagnostics_event(
            events,
            step_index=state.diagnostics_step_index,
            particle_id=particle.particle_id,
            stage="free_flight",
            message=f"speed drop without contact at step {state.diagnostics_step_index}",
        )
    last_contact_step = state.diagnostics_last_contact_step_by_particle.get(particle.particle_id)
    if contact_count > 0 and last_contact_step == state.diagnostics_step_index - 1:
        flagged = True
        _diagnostics_event(
            events,
            step_index=state.diagnostics_step_index,
            particle_id=particle.particle_id,
            stage="boundary",
            message=f"repeated boundary recontact / possible snagging at step {state.diagnostics_step_index}",
        )
    flagged |= _append_energy_stage_events(
        events,
        state=state,
        particle_id=particle.particle_id,
        seam_energy_before_after=seam_energy_before_after.get(particle.particle_id),
        boundary_energy_before_after=boundary_energy_before_after.get(particle.particle_id),
        finalize_energy_before_after=finalize_energy_before_after.get(particle.particle_id),
    )
    return flagged


def _append_energy_stage_events(
    events: list[ExplosionDiagnosticsEvent],
    *,
    state: ExplosionSimulationState,
    particle_id: int,
    seam_energy_before_after: tuple[float, float] | None,
    boundary_energy_before_after: tuple[float, float] | None,
    finalize_energy_before_after: tuple[float, float] | None,
) -> bool:
    flagged = False
    if seam_energy_before_after is not None and abs(seam_energy_before_after[1] - seam_energy_before_after[0]) > _DIAGNOSTIC_ENERGY_TOLERANCE:
        flagged = True
        _diagnostics_event(
            events,
            step_index=state.diagnostics_step_index,
            particle_id=particle_id,
            stage="seam_transport",
            message=f"energy change during seam transport at step {state.diagnostics_step_index}",
        )
    if (
        boundary_energy_before_after is not None
        and _BOUNDARY_RESTITUTION >= 1.0 - _EPSILON
        and abs(boundary_energy_before_after[1] - boundary_energy_before_after[0]) > _DIAGNOSTIC_ENERGY_TOLERANCE
    ):
        flagged = True
        _diagnostics_event(
            events,
            step_index=state.diagnostics_step_index,
            particle_id=particle_id,
            stage="boundary_resolution",
            message=f"energy change during elastic boundary resolution at step {state.diagnostics_step_index}",
        )
    if finalize_energy_before_after is not None and abs(finalize_energy_before_after[1] - finalize_energy_before_after[0]) > _DIAGNOSTIC_ENERGY_TOLERANCE:
        flagged = True
        _diagnostics_event(
            events,
            step_index=state.diagnostics_step_index,
            particle_id=particle_id,
            stage="finalize",
            message=f"energy change during finalize/nudge at step {state.diagnostics_step_index}",
        )
    return flagged


def _collision_diagnostics_events(
    state: ExplosionSimulationState,
    *,
    restitution: float,
    collision_delta: float,
) -> list[ExplosionDiagnosticsEvent]:
    events: list[ExplosionDiagnosticsEvent] = []
    if restitution >= 1.0 - _EPSILON:
        if abs(collision_delta) > _DIAGNOSTIC_ENERGY_TOLERANCE:
            _diagnostics_event(
                events,
                step_index=state.diagnostics_step_index,
                particle_id=-1,
                stage="collision_resolution",
                message=f"energy drift in elastic collision stage at step {state.diagnostics_step_index}",
            )
        return events
    if collision_delta > _DIAGNOSTIC_ENERGY_TOLERANCE:
        _diagnostics_event(
            events,
            step_index=state.diagnostics_step_index,
            particle_id=-1,
            stage="collision_resolution",
            message=f"energy increase in inelastic collision stage at step {state.diagnostics_step_index}",
        )
    return events


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
    state.diagnostics_step_index += 1
    before_energy = float(state.total_kinetic_energy)
    before_weighted_sum = float(
        velocity_norm_sq_sum_for_particles(state.particles, weighted_by_mass=True)
    )
    particle_stage_data: dict[int, dict[str, object]] = {}
    events: list[ExplosionAudioEvent] = []
    for particle in state.particles:
        diagnostics = particle_stage_data.setdefault(particle.particle_id, {})
        events.extend(
            _step_particle(
                particle,
                dt_seconds=dt_seconds,
                adapter=adapter,
                boundary_response=state.boundary_response,
                elapsed_ms=state.elapsed_ms,
                diagnostics=diagnostics,
            )
        )
    seam_energy_before_after: dict[int, tuple[float, float]] = {}
    boundary_energy_before_after: dict[int, tuple[float, float]] = {}
    finalize_energy_before_after: dict[int, tuple[float, float]] = {}
    for particle in state.particles:
        if not particle.active:
            continue
        data = particle_stage_data.get(particle.particle_id, {})
        before_velocity = tuple(data.get("before_velocity", particle.velocity_nd))
        after_seam_velocity = data.get("after_seam_velocity")
        after_boundary_velocity = data.get("after_boundary_velocity")
        after_finalize_velocity = tuple(data.get("after_finalize_velocity", particle.velocity_nd))
        before_k = _particle_energy_for_velocity(particle, before_velocity)
        if after_seam_velocity is not None:
            seam_velocity = tuple(after_seam_velocity)
            seam_k = _particle_energy_for_velocity(particle, seam_velocity)
            seam_energy_before_after[particle.particle_id] = (before_k, seam_k)
        if after_boundary_velocity is not None:
            boundary_before_velocity = tuple(after_seam_velocity) if after_seam_velocity is not None else before_velocity
            boundary_k_before = _particle_energy_for_velocity(particle, boundary_before_velocity)
            boundary_velocity = tuple(after_boundary_velocity)
            boundary_k_after = _particle_energy_for_velocity(particle, boundary_velocity)
            boundary_energy_before_after[particle.particle_id] = (
                boundary_k_before,
                boundary_k_after,
            )
        finalize_before_velocity = (
            tuple(after_boundary_velocity)
            if after_boundary_velocity is not None
            else tuple(after_seam_velocity)
            if after_seam_velocity is not None
            else before_velocity
        )
        finalize_k_before = _particle_energy_for_velocity(particle, finalize_before_velocity)
        finalize_k_after = _particle_energy_for_velocity(particle, after_finalize_velocity)
        finalize_energy_before_after[particle.particle_id] = (
            finalize_k_before,
            finalize_k_after,
        )
    before_collision_energy = total_kinetic_energy_for_particles(state.particles)
    collided_particle_ids: set[int] = set()
    if state.particle_collisions == EXPLOSION_PARTICLE_COLLISIONS_ON:
        events.extend(
            _resolve_collisions(
                state.particles,
                collision_elasticity=float(getattr(state, "collision_elasticity", 1.0)),
                collided_particle_ids=collided_particle_ids,
            )
        )
    after_collision_energy = total_kinetic_energy_for_particles(state.particles)
    for particle in state.particles:
        if not particle.active:
            continue
        _record_trail_sample(
            particle,
            elapsed_ms=state.elapsed_ms,
        )
    state.velocity_norm_sq_sum = velocity_norm_sq_sum_for_particles(state.particles)
    state.total_kinetic_energy = total_kinetic_energy_for_particles(state.particles)
    state.diagnostics_summary = _build_diagnostics_summary(
        state,
        before_energy=before_energy,
        before_weighted_sum=before_weighted_sum,
        particle_stage_data=particle_stage_data,
        before_collision_energy=before_collision_energy,
        after_collision_energy=after_collision_energy,
        collided_particle_ids=collided_particle_ids,
        seam_energy_before_after=seam_energy_before_after,
        boundary_energy_before_after=boundary_energy_before_after,
        finalize_energy_before_after=finalize_energy_before_after,
    )
    return tuple(events)
