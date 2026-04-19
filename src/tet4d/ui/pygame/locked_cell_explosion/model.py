from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tet4d.engine.topology_explorer.glue_model import ExplorerTopologyProfile
    from tet4d.engine.topology_explorer.transport_resolver import (
        ExplorerTransportResolver,
    )

Vec3 = tuple[float, float, float]
VecN = tuple[float, ...]

EXPLOSION_BOUNDARY_RESPONSE_ESCAPE = "escape"
EXPLOSION_BOUNDARY_RESPONSE_BOUNCE = "bounce"
EXPLOSION_BOUNDARY_RESPONSES = (
    EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
    EXPLOSION_BOUNDARY_RESPONSE_BOUNCE,
)

EXPLOSION_PARTICLE_COLLISIONS_OFF = "off"
EXPLOSION_PARTICLE_COLLISIONS_ON = "on"
EXPLOSION_PARTICLE_COLLISION_MODES = (
    EXPLOSION_PARTICLE_COLLISIONS_OFF,
    EXPLOSION_PARTICLE_COLLISIONS_ON,
)

EXPLOSION_SPEED_SLOW = "slow"
EXPLOSION_SPEED_NORMAL = "normal"
EXPLOSION_SPEED_FAST = "fast"
EXPLOSION_SPEED_PRESETS = (
    EXPLOSION_SPEED_SLOW,
    EXPLOSION_SPEED_NORMAL,
    EXPLOSION_SPEED_FAST,
)
EXPLOSION_TRAIL_MIN_TIME_SPACING_MS = 32.0
EXPLOSION_TRAIL_MIN_MOVEMENT_SPACING = 0.18
EXPLOSION_TRAIL_MAX_LIFETIME_MS = 620.0
EXPLOSION_TRAIL_MAX_SAMPLES = 18
_SPEED_SCALE_BY_PRESET = {
    EXPLOSION_SPEED_SLOW: 0.72,
    EXPLOSION_SPEED_NORMAL: 1.0,
    EXPLOSION_SPEED_FAST: 1.34,
}


def normalize_boundary_response(
    value: object,
    *,
    default: str = EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
) -> str:
    normalized = str(value).strip().lower()
    if normalized not in EXPLOSION_BOUNDARY_RESPONSES:
        return str(default)
    return normalized


def normalize_particle_collisions(
    value: object,
    *,
    default: str = EXPLOSION_PARTICLE_COLLISIONS_OFF,
) -> str:
    normalized = str(value).strip().lower()
    if normalized not in EXPLOSION_PARTICLE_COLLISION_MODES:
        return str(default)
    return normalized


def normalize_speed_preset(
    value: object,
    *,
    default: str = EXPLOSION_SPEED_NORMAL,
) -> str:
    normalized = str(value).strip().lower()
    if normalized not in EXPLOSION_SPEED_PRESETS:
        return str(default)
    return normalized


def speed_scale_for_preset(
    value: object,
    *,
    default: str = EXPLOSION_SPEED_NORMAL,
) -> float:
    preset = normalize_speed_preset(value, default=default)
    return float(_SPEED_SCALE_BY_PRESET[preset])


@dataclass(frozen=True)
class ExplosionSeedCell:
    source_coord: tuple[int, ...]
    color_id: int
    source_group_id: str | None = None


@dataclass
class ExplosionParticle:
    particle_id: int
    source_coord: tuple[int, ...]
    position_nd: VecN
    velocity_nd: VecN
    color_id: int
    source_group_id: str | None = None
    escaped: bool = False
    active: bool = True
    rotation_deg: Vec3 = (0.0, 0.0, 0.0)
    angular_velocity_deg: Vec3 = (0.0, 0.0, 0.0)
    collision_radius: float = 0.32
    collision_mass: float = 1.0
    trail_elapsed_ms: float = 0.0
    trail_samples: list["ExplosionTrailSample"] = field(default_factory=list)


@dataclass(frozen=True)
class ExplosionTrailSample:
    position_nd: VecN
    elapsed_ms: float
    segment_break: bool = False


@dataclass(frozen=True)
class ExplosionAudioEvent:
    family: str
    strength: float


@dataclass
class ExplosionAudioState:
    last_emit_ms_by_family: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ExplosionRenderParticle:
    particle_id: int
    source_coord: tuple[int, ...]
    position_nd: VecN
    render_position: Vec3
    rotation_deg: Vec3
    alpha: float
    color_id: int
    layer_weights: tuple[tuple[int, float], ...] = ()
    trail_segments: tuple["ExplosionRenderTrailSegment", ...] = ()


@dataclass(frozen=True)
class ExplosionRenderTrailSegment:
    tail_position_nd: VecN
    head_position_nd: VecN
    tail_render_position: Vec3
    head_render_position: Vec3
    tail_layer_weights: tuple[tuple[int, float], ...] = ()
    head_layer_weights: tuple[tuple[int, float], ...] = ()
    alpha: float = 1.0
    width: float = 1.0


@dataclass(frozen=True)
class ExplosionTopologyInput:
    board_dims: tuple[int, ...]
    topology_edge_rules: tuple[tuple[str, str], ...] | None = None
    explorer_topology_profile: ExplorerTopologyProfile | None = None
    explorer_transport: ExplorerTransportResolver | None = field(
        default=None,
        compare=False,
        repr=False,
    )


@dataclass(frozen=True)
class StandaloneExplosionConfig:
    dimension: int
    topology: ExplosionTopologyInput
    occupied_cells: tuple[ExplosionSeedCell, ...]
    random_seed: int
    boundary_response: str = EXPLOSION_BOUNDARY_RESPONSE_ESCAPE
    particle_collisions: str = EXPLOSION_PARTICLE_COLLISIONS_OFF
    speed_preset: str = EXPLOSION_SPEED_NORMAL
    sound_enabled: bool = True
    launch_speed_scale: float = 1.0
    time_scale: float = 1.0


@dataclass
class ExplosionSimulationState:
    dimension: int
    board_dims: tuple[int, ...]
    boundary_response: str
    particle_collisions: str
    particles: list[ExplosionParticle]
    elapsed_ms: float = 0.0
    total_kinetic_energy: float = 0.0
