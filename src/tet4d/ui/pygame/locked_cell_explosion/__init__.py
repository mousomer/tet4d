from .controller import LockedCellExplosionController, build_locked_cell_explosion
from .model import (
    EXPLOSION_BOUNDARY_RESPONSES,
    EXPLOSION_BOUNDARY_RESPONSE_BOUNCE,
    EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
    EXPLOSION_DIAGNOSTICS_MODE_FULL,
    EXPLOSION_DIAGNOSTICS_MODE_OFF,
    EXPLOSION_DIAGNOSTICS_MODE_SUMMARY,
    EXPLOSION_DIAGNOSTICS_MODES,
    EXPLOSION_MASS_MODE_RANDOM,
    EXPLOSION_MASS_MODE_UNIFORM,
    EXPLOSION_MASS_MODES,
    EXPLOSION_PARTICLE_COLLISION_MODES,
    EXPLOSION_PARTICLE_COLLISIONS_OFF,
    EXPLOSION_PARTICLE_COLLISIONS_ON,
    EXPLOSION_SPEED_FAST,
    EXPLOSION_SPEED_NORMAL,
    EXPLOSION_SPEED_PRESETS,
    EXPLOSION_SPEED_SLOW,
    EXPLOSION_TRAIL_MAX_LIFETIME_MS,
    EXPLOSION_TRAIL_MAX_SAMPLES,
    EXPLOSION_TRAIL_MIN_MOVEMENT_SPACING,
    EXPLOSION_TRAIL_MIN_TIME_SPACING_MS,
    EXPLOSION_TRAIL_RETENTION_MAX_MS,
    EXPLOSION_TRAIL_RETENTION_MIN_MS,
    ExplosionParticle,
    ExplosionRenderParticle,
    ExplosionRenderTrailSegment,
    ExplosionSeedCell,
    ExplosionTrailSample,
    ExplosionTopologyInput,
    StandaloneExplosionConfig,
    normalize_boundary_response,
    normalize_particle_collisions,
    normalize_speed_preset,
    speed_scale_for_preset,
)
from .simulation import (
    build_endgame_state,
    step_endgame_state,
    velocity_norm_sq_sum_for_particles,
)

_LAZY_LAUNCHER_EXPORTS = {
    "StandaloneExplosionSurfaceState",
    "build_explorer_explosion_surface_state",
    "build_standalone_explosion_config",
    "build_standalone_explosion_surface_state",
    "launcher_row_keys",
    "restart_standalone_explosion",
    "run_standalone_explosion_launcher",
}


def __getattr__(name: str):
    if name in _LAZY_LAUNCHER_EXPORTS:
        from . import launcher

        value = getattr(launcher, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "EXPLOSION_BOUNDARY_RESPONSES",
    "EXPLOSION_BOUNDARY_RESPONSE_BOUNCE",
    "EXPLOSION_BOUNDARY_RESPONSE_ESCAPE",
    "EXPLOSION_DIAGNOSTICS_MODE_FULL",
    "EXPLOSION_DIAGNOSTICS_MODE_OFF",
    "EXPLOSION_DIAGNOSTICS_MODE_SUMMARY",
    "EXPLOSION_DIAGNOSTICS_MODES",
    "EXPLOSION_MASS_MODE_RANDOM",
    "EXPLOSION_MASS_MODE_UNIFORM",
    "EXPLOSION_MASS_MODES",
    "EXPLOSION_PARTICLE_COLLISION_MODES",
    "EXPLOSION_PARTICLE_COLLISIONS_OFF",
    "EXPLOSION_PARTICLE_COLLISIONS_ON",
    "EXPLOSION_SPEED_FAST",
    "EXPLOSION_SPEED_NORMAL",
    "EXPLOSION_SPEED_PRESETS",
    "EXPLOSION_SPEED_SLOW",
    "EXPLOSION_TRAIL_MAX_LIFETIME_MS",
    "EXPLOSION_TRAIL_MAX_SAMPLES",
    "EXPLOSION_TRAIL_MIN_MOVEMENT_SPACING",
    "EXPLOSION_TRAIL_MIN_TIME_SPACING_MS",
    "EXPLOSION_TRAIL_RETENTION_MAX_MS",
    "EXPLOSION_TRAIL_RETENTION_MIN_MS",
    "ExplosionParticle",
    "ExplosionRenderParticle",
    "ExplosionRenderTrailSegment",
    "ExplosionSeedCell",
    "ExplosionTrailSample",
    "ExplosionTopologyInput",
    "LockedCellExplosionController",
    "StandaloneExplosionSurfaceState",
    "StandaloneExplosionConfig",
    "build_explorer_explosion_surface_state",
    "build_endgame_state",
    "build_locked_cell_explosion",
    "build_standalone_explosion_config",
    "build_standalone_explosion_surface_state",
    "launcher_row_keys",
    "normalize_boundary_response",
    "normalize_particle_collisions",
    "normalize_speed_preset",
    "restart_standalone_explosion",
    "run_standalone_explosion_launcher",
    "speed_scale_for_preset",
    "step_endgame_state",
    "velocity_norm_sq_sum_for_particles",
]
