from __future__ import annotations

from dataclasses import dataclass

from .defaults_store import ExplosionDefaults
from .model import ExplosionSeedCell, ExplosionTopologyInput, StandaloneExplosionConfig


@dataclass(frozen=True)
class ExplosionRuntimeLaunchInputs:
    dimension: int
    topology: ExplosionTopologyInput
    occupied_cells: tuple[ExplosionSeedCell, ...]
    random_seed: int
    launch_speed_scale: float = 1.0
    time_scale: float = 1.0


def build_runtime_explosion_config(
    *,
    defaults: ExplosionDefaults,
    launch: ExplosionRuntimeLaunchInputs,
) -> StandaloneExplosionConfig:
    return StandaloneExplosionConfig(
        dimension=int(launch.dimension),
        topology=launch.topology,
        occupied_cells=tuple(launch.occupied_cells),
        random_seed=int(launch.random_seed),
        boundary_response=str(defaults.boundary_response),
        particle_collisions=str(defaults.particle_collisions),
        speed_preset=str(defaults.speed_preset),
        mass_mode=str(defaults.mass_mode),
        base_mass=float(defaults.base_mass),
        random_mass_min=float(defaults.random_mass_min),
        random_mass_max=float(defaults.random_mass_max),
        collision_elasticity=float(defaults.collision_elasticity),
        diagnostics_mode=str(defaults.diagnostics_mode),
        sound_enabled=bool(defaults.sound_enabled),
        launch_speed_scale=float(launch.launch_speed_scale),
        time_scale=float(launch.time_scale),
        trace_retention_ms=float(defaults.trace_retention_ms),
    )


__all__ = [
    "ExplosionRuntimeLaunchInputs",
    "build_runtime_explosion_config",
]
