from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import math
import random

from tet4d.engine.runtime.endgame_presets import (
    ENDGAME_INTERACTION_COLLIDE,
    ENDGAME_INTERACTION_NONE,
    ENDGAME_PRESET_DEFAULT_ORBIT,
    ENDGAME_PRESET_IDS,
    ENDGAME_PRESET_INVERT_ALL,
    ENDGAME_PRESET_SPHERE,
    ENDGAME_PRESET_WRAP_ALL,
    normalize_endgame_interaction_mode,
    normalize_endgame_preset_id,
)
from tet4d.engine.runtime.project_config import constants_payload

Vec3 = tuple[float, float, float]

TERMINAL_PHASE_PLAYING = "playing"
TERMINAL_PHASE_ENDGAME_SHATTER = "endgame_shatter"
TERMINAL_PHASE_ENDGAME_RELIC_FIELD = "endgame_relic_field"
TERMINAL_PHASE_GAME_OVER_COMPLETE = "game_over_complete"

# Compatibility alias retained for existing callers/tests that still refer to the
# pre-split endgame phase name.
TERMINAL_PHASE_GAME_OVER_ANIMATING = TERMINAL_PHASE_ENDGAME_SHATTER

_TAU = math.tau


def _clamp_float(value: object, *, default: float, minimum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return float(default)
    return max(float(minimum), float(value))


def _clamp_int(value: object, *, default: int, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return int(default)
    return max(int(minimum), int(value))


def _coerce_bool(value: object, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return bool(default)


def _normalize_path_family_weights(
    value: object,
) -> tuple[tuple[str, int], ...]:
    default_weights = (
        ("ellipse", 4),
        ("helix", 3),
        ("lissajous", 3),
    )
    if not isinstance(value, dict):
        return default_weights
    normalized: list[tuple[str, int]] = []
    for family in ("ellipse", "helix", "lissajous"):
        raw_weight = value.get(family)
        if isinstance(raw_weight, bool) or not isinstance(raw_weight, int):
            continue
        if raw_weight <= 0:
            continue
        normalized.append((family, int(raw_weight)))
    return tuple(normalized) if normalized else default_weights


def _preset_payload_map(value: object) -> dict[str, dict[str, object]]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, dict[str, object]] = {}
    for preset_id in ENDGAME_PRESET_IDS:
        preset_payload = value.get(preset_id)
        if isinstance(preset_payload, dict):
            normalized[preset_id] = dict(preset_payload)
    return normalized


@dataclass(frozen=True)
class EndgamePresetConfig:
    preset_id: str
    field_kind: str
    drift_scale: float
    oscillation_scale: float
    extent_scale: float
    sphere_radius_scale: float
    tangential_bias: float
    radial_correction_strength: float


@dataclass(frozen=True)
class EndgameAnimationTuning:
    enabled: bool
    crack_onset_duration_ms: float
    shatter_duration_ms: float
    capture_transition_duration_ms: float
    shell_fragment_lifetime_ms: float
    shell_fade_duration_ms: float
    shell_fragment_speed_min: float
    shell_fragment_speed_max: float
    relic_burst_speed_min: float
    relic_burst_speed_max: float
    burst_angular_velocity_deg_min: float
    burst_angular_velocity_deg_max: float
    outward_bias_strength: float
    random_spread_strength: float
    burst_drag_per_second: float
    burst_gravity_per_second: float
    relic_spin_deg_min: float
    relic_spin_deg_max: float
    relic_field_speed_min: float
    relic_field_speed_max: float
    orbit_radius_min: float
    orbit_radius_max: float
    orbit_depth_amplitude_min: float
    orbit_depth_amplitude_max: float
    anchor_spread_radius: float
    path_family_weights: tuple[tuple[str, int], ...]
    default_preset_id: str
    default_interaction_mode: str
    field_extent_multiplier: float
    wrap_margin: float
    preset_registry: tuple[EndgamePresetConfig, ...]
    collision_radius_min: float
    collision_radius_max: float
    collision_restitution: float
    collision_damping: float
    collision_separation_bias: float
    collision_max_relics: int
    collision_velocity_sample_ms: float
    seed_salt: int

    @property
    def capture_start_ms(self) -> float:
        return max(
            float(self.crack_onset_duration_ms),
            float(self.shatter_duration_ms - self.capture_transition_duration_ms),
        )

    @property
    def prompt_ready_ms(self) -> float:
        return float(self.shatter_duration_ms)

    @property
    def shell_fade_start_ms(self) -> float:
        return max(
            0.0,
            float(self.shell_fragment_lifetime_ms - self.shell_fade_duration_ms),
        )

    def preset_config_for(self, preset_id: str) -> EndgamePresetConfig:
        normalized = normalize_endgame_preset_id(
            preset_id,
            default=self.default_preset_id,
        )
        for config in self.preset_registry:
            if config.preset_id == normalized:
                return config
        return self.preset_registry[0]


def load_endgame_animation_tuning() -> EndgameAnimationTuning:
    animation_payload = constants_payload().get("animation", {})
    payload = animation_payload.get("endgame", {})
    if not isinstance(payload, dict):
        payload = {}
    preset_payloads = _preset_payload_map(payload.get("presets"))

    def _preset_config(
        preset_id: str,
        *,
        field_kind: str,
        drift_scale: float,
        oscillation_scale: float,
        extent_scale: float,
        sphere_radius_scale: float = 0.0,
        tangential_bias: float = 0.0,
        radial_correction_strength: float = 0.0,
    ) -> EndgamePresetConfig:
        preset_payload = preset_payloads.get(preset_id, {})
        return EndgamePresetConfig(
            preset_id=preset_id,
            field_kind=field_kind,
            drift_scale=_clamp_float(
                preset_payload.get("drift_scale"),
                default=drift_scale,
                minimum=0.0,
            ),
            oscillation_scale=_clamp_float(
                preset_payload.get("oscillation_scale"),
                default=oscillation_scale,
                minimum=0.0,
            ),
            extent_scale=_clamp_float(
                preset_payload.get("extent_scale"),
                default=extent_scale,
                minimum=0.2,
            ),
            sphere_radius_scale=_clamp_float(
                preset_payload.get("sphere_radius_scale"),
                default=sphere_radius_scale,
                minimum=0.0,
            ),
            tangential_bias=_clamp_float(
                preset_payload.get("tangential_bias"),
                default=tangential_bias,
                minimum=0.0,
            ),
            radial_correction_strength=_clamp_float(
                preset_payload.get("radial_correction_strength"),
                default=radial_correction_strength,
                minimum=0.0,
            ),
        )

    shatter_duration_ms = _clamp_float(
        payload.get("shatter_duration_ms"),
        default=1400.0,
        minimum=1.0,
    )
    capture_transition_duration_ms = min(
        shatter_duration_ms,
        _clamp_float(
            payload.get("capture_transition_duration_ms"),
            default=620.0,
            minimum=0.0,
        ),
    )
    shell_fragment_lifetime_ms = min(
        shatter_duration_ms,
        _clamp_float(
            payload.get("shell_fragment_lifetime_ms"),
            default=1320.0,
            minimum=0.0,
        ),
    )
    return EndgameAnimationTuning(
        enabled=_coerce_bool(payload.get("enabled"), default=True),
        crack_onset_duration_ms=_clamp_float(
            payload.get("crack_onset_duration_ms"),
            default=220.0,
            minimum=0.0,
        ),
        shatter_duration_ms=shatter_duration_ms,
        capture_transition_duration_ms=capture_transition_duration_ms,
        shell_fragment_lifetime_ms=shell_fragment_lifetime_ms,
        shell_fade_duration_ms=_clamp_float(
            payload.get("shell_fade_duration_ms"),
            default=380.0,
            minimum=0.0,
        ),
        shell_fragment_speed_min=_clamp_float(
            payload.get("shell_fragment_speed_min"),
            default=1.6,
            minimum=0.0,
        ),
        shell_fragment_speed_max=_clamp_float(
            payload.get("shell_fragment_speed_max"),
            default=4.9,
            minimum=0.0,
        ),
        relic_burst_speed_min=_clamp_float(
            payload.get("relic_burst_speed_min"),
            default=3.2,
            minimum=0.0,
        ),
        relic_burst_speed_max=_clamp_float(
            payload.get("relic_burst_speed_max"),
            default=7.2,
            minimum=0.0,
        ),
        burst_angular_velocity_deg_min=_clamp_float(
            payload.get("burst_angular_velocity_deg_min"),
            default=90.0,
            minimum=0.0,
        ),
        burst_angular_velocity_deg_max=_clamp_float(
            payload.get("burst_angular_velocity_deg_max"),
            default=320.0,
            minimum=0.0,
        ),
        outward_bias_strength=_clamp_float(
            payload.get("outward_bias_strength"),
            default=1.0,
            minimum=0.0,
        ),
        random_spread_strength=_clamp_float(
            payload.get("random_spread_strength"),
            default=0.65,
            minimum=0.0,
        ),
        burst_drag_per_second=_clamp_float(
            payload.get("burst_drag_per_second"),
            default=0.84,
            minimum=0.0,
        ),
        burst_gravity_per_second=_clamp_float(
            payload.get("burst_gravity_per_second"),
            default=0.52,
            minimum=0.0,
        ),
        relic_spin_deg_min=_clamp_float(
            payload.get("relic_spin_deg_min"),
            default=12.0,
            minimum=0.0,
        ),
        relic_spin_deg_max=_clamp_float(
            payload.get("relic_spin_deg_max"),
            default=44.0,
            minimum=0.0,
        ),
        relic_field_speed_min=_clamp_float(
            payload.get("relic_field_speed_min"),
            default=0.42,
            minimum=0.0,
        ),
        relic_field_speed_max=_clamp_float(
            payload.get("relic_field_speed_max"),
            default=0.96,
            minimum=0.0,
        ),
        orbit_radius_min=_clamp_float(
            payload.get("orbit_radius_min"),
            default=0.9,
            minimum=0.0,
        ),
        orbit_radius_max=_clamp_float(
            payload.get("orbit_radius_max"),
            default=3.2,
            minimum=0.0,
        ),
        orbit_depth_amplitude_min=_clamp_float(
            payload.get("orbit_depth_amplitude_min"),
            default=0.35,
            minimum=0.0,
        ),
        orbit_depth_amplitude_max=_clamp_float(
            payload.get("orbit_depth_amplitude_max"),
            default=1.8,
            minimum=0.0,
        ),
        anchor_spread_radius=_clamp_float(
            payload.get("anchor_spread_radius"),
            default=1.7,
            minimum=0.0,
        ),
        path_family_weights=_normalize_path_family_weights(
            payload.get("path_family_weights")
        ),
        default_preset_id=normalize_endgame_preset_id(
            payload.get("default_preset_id"),
            default=ENDGAME_PRESET_DEFAULT_ORBIT,
        ),
        default_interaction_mode=normalize_endgame_interaction_mode(
            payload.get("default_interaction_mode"),
            default=ENDGAME_INTERACTION_NONE,
        ),
        field_extent_multiplier=_clamp_float(
            payload.get("field_extent_multiplier"),
            default=1.12,
            minimum=0.2,
        ),
        wrap_margin=_clamp_float(
            payload.get("wrap_margin"),
            default=0.85,
            minimum=0.0,
        ),
        preset_registry=(
            _preset_config(
                ENDGAME_PRESET_DEFAULT_ORBIT,
                field_kind="orbit",
                drift_scale=0.18,
                oscillation_scale=1.0,
                extent_scale=1.0,
            ),
            _preset_config(
                ENDGAME_PRESET_WRAP_ALL,
                field_kind="wrap",
                drift_scale=0.92,
                oscillation_scale=0.62,
                extent_scale=1.08,
            ),
            _preset_config(
                ENDGAME_PRESET_INVERT_ALL,
                field_kind="invert",
                drift_scale=0.84,
                oscillation_scale=0.56,
                extent_scale=1.02,
            ),
            _preset_config(
                ENDGAME_PRESET_SPHERE,
                field_kind="sphere",
                drift_scale=0.34,
                oscillation_scale=0.46,
                extent_scale=1.0,
                sphere_radius_scale=0.92,
                tangential_bias=1.08,
                radial_correction_strength=0.42,
            ),
        ),
        collision_radius_min=_clamp_float(
            payload.get("collision_radius_min"),
            default=0.34,
            minimum=0.05,
        ),
        collision_radius_max=_clamp_float(
            payload.get("collision_radius_max"),
            default=0.54,
            minimum=0.05,
        ),
        collision_restitution=_clamp_float(
            payload.get("collision_restitution"),
            default=0.78,
            minimum=0.0,
        ),
        collision_damping=_clamp_float(
            payload.get("collision_damping"),
            default=0.92,
            minimum=0.0,
        ),
        collision_separation_bias=_clamp_float(
            payload.get("collision_separation_bias"),
            default=1.0,
            minimum=0.0,
        ),
        collision_max_relics=_clamp_int(
            payload.get("collision_max_relics"),
            default=96,
            minimum=1,
        ),
        collision_velocity_sample_ms=_clamp_float(
            payload.get("collision_velocity_sample_ms"),
            default=18.0,
            minimum=1.0,
        ),
        seed_salt=_clamp_int(payload.get("seed_salt"), default=7919, minimum=0),
    )


@dataclass(frozen=True)
class EndgameRenderContext:
    mode_key: str
    projection_name: str = "ORTHOGRAPHIC"
    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    zoom: float = 1.0
    cam_dist: float = 0.0
    projective_strength: float = 0.0
    projective_bias: float = 0.0
    xw_deg: float = 0.0
    zw_deg: float = 0.0
    layer_axis_label: str = ""
    layer_count: int = 1


@dataclass(frozen=True)
class SnapshotCell:
    source_coord: tuple[int, ...]
    position: Vec3
    color_id: int
    layer_index: int | None = None


@dataclass(frozen=True)
class EndgameSnapshot:
    dimension: int
    board_dims: tuple[int, ...]
    render_dims: tuple[int, int, int]
    board_center: Vec3
    locked_cells: tuple[SnapshotCell, ...]
    rng_seed: int
    render_context: EndgameRenderContext
    preset_id: str = ENDGAME_PRESET_DEFAULT_ORBIT
    interaction_mode: str = ENDGAME_INTERACTION_NONE


@dataclass(frozen=True)
class ShellFragment:
    source_kind: str
    source_index: int
    base_geometry: tuple[Vec3, Vec3]
    initial_position: Vec3
    velocity: Vec3
    acceleration: Vec3
    angular_velocity_deg: Vec3
    detach_start_ms: float
    fade_start_ms: float
    lifetime_ms: float
    layer_index: int | None = None
    jitter_offset: Vec3 = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class CellRelic:
    source_coord: tuple[int, ...]
    base_geometry: str
    initial_position: Vec3
    burst_velocity: Vec3
    burst_acceleration: Vec3
    burst_angular_velocity_deg: Vec3
    detach_start_ms: float
    capture_anchor: Vec3
    path_family: str
    field_basis_u: Vec3
    field_basis_v: Vec3
    field_basis_w: Vec3
    field_phase: float
    field_phase_secondary: float
    field_speed: float
    field_precession_speed: float
    orbit_radius_a: float
    orbit_radius_b: float
    depth_amplitude: float
    relic_spin_deg: Vec3
    color_id: int
    layer_index: int | None = None
    jitter_offset: Vec3 = (0.0, 0.0, 0.0)
    preset_id: str = ENDGAME_PRESET_DEFAULT_ORBIT
    field_drift_velocity: Vec3 = (0.0, 0.0, 0.0)
    field_radius_band: float = 0.0
    collision_radius: float = 0.38
    collision_mass: float = 1.0
    spin_handedness: float = 1.0


# Compatibility alias retained for existing imports/tests.
CellFragment = CellRelic


@dataclass(frozen=True)
class EndgameShatterState:
    shell_fragments: tuple[ShellFragment, ...]


@dataclass(frozen=True)
class EndgameRelicFieldState:
    cell_relics: tuple[CellRelic, ...]
    preset_id: str = ENDGAME_PRESET_DEFAULT_ORBIT
    interaction_mode: str = ENDGAME_INTERACTION_NONE


@dataclass
class EndgameAnimationState:
    snapshot: EndgameSnapshot
    tuning: EndgameAnimationTuning
    shatter: EndgameShatterState
    relic_field: EndgameRelicFieldState
    phase: str = TERMINAL_PHASE_ENDGAME_SHATTER
    elapsed_ms: float = 0.0

    @property
    def shell_fragments(self) -> tuple[ShellFragment, ...]:
        return self.shatter.shell_fragments

    @property
    def cell_relics(self) -> tuple[CellRelic, ...]:
        return self.relic_field.cell_relics

    @property
    def cell_fragments(self) -> tuple[CellRelic, ...]:
        return self.relic_field.cell_relics

    @property
    def frozen_render_active(self) -> bool:
        return self.phase != TERMINAL_PHASE_PLAYING

    @property
    def animating(self) -> bool:
        return self.phase in (
            TERMINAL_PHASE_ENDGAME_SHATTER,
            TERMINAL_PHASE_ENDGAME_RELIC_FIELD,
        )

    @property
    def in_relic_field(self) -> bool:
        return self.phase == TERMINAL_PHASE_ENDGAME_RELIC_FIELD

    @property
    def preset_id(self) -> str:
        return self.relic_field.preset_id

    @property
    def interaction_mode(self) -> str:
        return self.relic_field.interaction_mode

    def step(self, dt_ms: float) -> None:
        if not self.animating:
            return
        self.elapsed_ms = float(self.elapsed_ms + max(0.0, dt_ms))
        if self.elapsed_ms >= float(self.tuning.shatter_duration_ms):
            self.phase = TERMINAL_PHASE_ENDGAME_RELIC_FIELD
        else:
            self.phase = TERMINAL_PHASE_ENDGAME_SHATTER


def endgame_prompt_ready(animation: EndgameAnimationState | None) -> bool:
    if animation is None:
        return False
    if animation.phase == TERMINAL_PHASE_GAME_OVER_COMPLETE:
        return True
    return float(animation.elapsed_ms) >= float(animation.tuning.prompt_ready_ms)


def endgame_sfx_events_between(
    *,
    previous_elapsed_ms: float,
    current_elapsed_ms: float,
    tuning: EndgameAnimationTuning,
) -> tuple[str, ...]:
    if current_elapsed_ms <= previous_elapsed_ms:
        return tuple()
    thresholds = (
        (float(tuning.crack_onset_duration_ms), "endgame_crack"),
        (float(tuning.capture_start_ms), "endgame_pop"),
        (float(tuning.shatter_duration_ms), "endgame_boom"),
    )
    events: list[str] = []
    for threshold_ms, event_name in thresholds:
        if previous_elapsed_ms < threshold_ms <= current_elapsed_ms:
            events.append(event_name)
    return tuple(events)


def _stable_seed_mix(accumulator: int, value: int) -> int:
    mixed = ((accumulator ^ int(value)) * 16_777_619) & 0xFFFFFFFF
    return mixed or 1


def derive_endgame_seed(
    *,
    base_seed: int,
    board_dims: tuple[int, ...],
    locked_cells: tuple[SnapshotCell, ...],
    salt: int,
) -> int:
    accumulator = _stable_seed_mix(2_166_136_261 ^ int(salt), int(base_seed))
    for dim in board_dims:
        accumulator = _stable_seed_mix(accumulator, int(dim))
    for cell in locked_cells:
        for axis in cell.source_coord:
            accumulator = _stable_seed_mix(accumulator, int(axis) + 257)
        accumulator = _stable_seed_mix(accumulator, int(cell.color_id) + 911)
        accumulator = _stable_seed_mix(
            accumulator,
            int(-1 if cell.layer_index is None else cell.layer_index) + 1237,
        )
    return accumulator


def create_snapshot(
    *,
    dimension: int,
    board_dims: tuple[int, ...],
    render_dims: tuple[int, int, int],
    locked_cells: tuple[SnapshotCell, ...],
    base_seed: int,
    render_context: EndgameRenderContext,
    preset_id: str | None = None,
    interaction_mode: str | None = None,
    tuning: EndgameAnimationTuning | None = None,
) -> EndgameSnapshot:
    active_tuning = load_endgame_animation_tuning() if tuning is None else tuning
    board_center = (
        (float(render_dims[0]) - 1.0) * 0.5,
        (float(render_dims[1]) - 1.0) * 0.5,
        (float(render_dims[2]) - 1.0) * 0.5,
    )
    return EndgameSnapshot(
        dimension=int(dimension),
        board_dims=tuple(int(value) for value in board_dims),
        render_dims=tuple(int(value) for value in render_dims),
        board_center=board_center,
        locked_cells=tuple(locked_cells),
        rng_seed=derive_endgame_seed(
            base_seed=int(base_seed),
            board_dims=tuple(int(value) for value in board_dims),
            locked_cells=tuple(locked_cells),
            salt=int(active_tuning.seed_salt),
        ),
        render_context=render_context,
        preset_id=normalize_endgame_preset_id(
            preset_id,
            default=active_tuning.default_preset_id,
        ),
        interaction_mode=normalize_endgame_interaction_mode(
            interaction_mode,
            default=active_tuning.default_interaction_mode,
        ),
    )


def _vec_add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _vec_sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vec_mul(a: Vec3, scalar: float) -> Vec3:
    return (a[0] * scalar, a[1] * scalar, a[2] * scalar)


def _vec_dot(a: Vec3, b: Vec3) -> float:
    return (a[0] * b[0]) + (a[1] * b[1]) + (a[2] * b[2])


def _vec_cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        (a[1] * b[2]) - (a[2] * b[1]),
        (a[2] * b[0]) - (a[0] * b[2]),
        (a[0] * b[1]) - (a[1] * b[0]),
    )


def _vec_lerp(a: Vec3, b: Vec3, progress: float) -> Vec3:
    return (
        a[0] + ((b[0] - a[0]) * progress),
        a[1] + ((b[1] - a[1]) * progress),
        a[2] + ((b[2] - a[2]) * progress),
    )


def _vec_len(a: Vec3) -> float:
    return math.sqrt((a[0] * a[0]) + (a[1] * a[1]) + (a[2] * a[2]))


def _normalize_or_default(a: Vec3, default: Vec3) -> Vec3:
    length = _vec_len(a)
    if length <= 1e-9:
        return default
    return (a[0] / length, a[1] / length, a[2] / length)


def _random_signed(randomizer: random.Random) -> float:
    return -1.0 if randomizer.random() < 0.5 else 1.0


def _random_unit_vec3(
    randomizer: random.Random,
    *,
    planar: bool,
) -> Vec3:
    vector = (
        randomizer.uniform(-1.0, 1.0),
        randomizer.uniform(-1.0, 1.0),
        0.0 if planar else randomizer.uniform(-1.0, 1.0),
    )
    return _normalize_or_default(vector, (1.0, 0.0, 0.0 if planar else 1.0))


def _smoothstep01(value: float) -> float:
    clamped = max(0.0, min(1.0, float(value)))
    return clamped * clamped * (3.0 - (2.0 * clamped))


def _wrap_phase_radians(value: float) -> float:
    return float(value % _TAU)


def _fragment_direction(
    *,
    randomizer: random.Random,
    origin: Vec3,
    board_center: Vec3,
    planar: bool,
    outward_bias_strength: float,
    random_spread_strength: float,
) -> Vec3:
    outward = _normalize_or_default(
        _vec_sub(origin, board_center),
        (0.0, -1.0, 0.0),
    )
    random_vec = _random_unit_vec3(randomizer, planar=planar)
    return _normalize_or_default(
        _vec_add(
            _vec_mul(outward, float(outward_bias_strength)),
            _vec_mul(random_vec, float(random_spread_strength)),
        ),
        outward,
    )


def _random_angular_velocity(
    randomizer: random.Random,
    *,
    planar: bool,
    minimum: float,
    maximum: float,
) -> Vec3:
    if planar:
        return (
            0.0,
            0.0,
            randomizer.uniform(minimum, maximum) * _random_signed(randomizer),
        )
    return (
        randomizer.uniform(minimum, maximum) * _random_signed(randomizer),
        randomizer.uniform(minimum, maximum) * _random_signed(randomizer),
        randomizer.uniform(minimum, maximum) * _random_signed(randomizer),
    )


def _scene_extent_limit(snapshot: EndgameSnapshot) -> float:
    return max(1.0, (min(snapshot.render_dims) * 0.5) + 1.25)


def _clamp_point_to_scene(
    point: Vec3,
    *,
    snapshot: EndgameSnapshot,
    planar: bool,
    margin: float,
) -> Vec3:
    dims = snapshot.render_dims
    x = min(float(dims[0]) - 0.5 + margin, max(-0.5 - margin, point[0]))
    y = min(float(dims[1]) - 0.5 + margin, max(-0.5 - margin, point[1]))
    if planar:
        z = 0.0
    else:
        z = min(float(dims[2]) - 0.5 + margin, max(-0.5 - margin, point[2]))
    return (x, y, z)


def _field_basis(
    *,
    randomizer: random.Random,
    direction: Vec3,
    planar: bool,
) -> tuple[Vec3, Vec3, Vec3]:
    if planar:
        primary = _normalize_or_default(
            (direction[0], direction[1], 0.0), (1.0, 0.0, 0.0)
        )
        secondary = (-primary[1], primary[0], 0.0)
        return (primary, secondary, (0.0, 0.0, 0.0))
    primary = _normalize_or_default(direction, (1.0, 0.0, 0.0))
    candidate = _random_unit_vec3(randomizer, planar=False)
    if abs(_vec_dot(primary, candidate)) > 0.92:
        candidate = _normalize_or_default(
            _vec_cross(primary, (0.0, 1.0, 0.0)),
            (0.0, 0.0, 1.0),
        )
    secondary = _normalize_or_default(
        _vec_cross(candidate, primary),
        (0.0, 0.0, 1.0),
    )
    tertiary = _normalize_or_default(
        _vec_cross(primary, secondary),
        (0.0, 1.0, 0.0),
    )
    return (primary, secondary, tertiary)


def _choose_path_family(
    *,
    randomizer: random.Random,
    tuning: EndgameAnimationTuning,
    planar: bool,
) -> str:
    allowed = [
        (family, weight)
        for family, weight in tuning.path_family_weights
        if weight > 0 and (not planar or family != "helix")
    ]
    if not allowed:
        allowed = [("ellipse", 1)]
    total = sum(weight for _, weight in allowed)
    roll = randomizer.uniform(0.0, float(total))
    accumulator = 0.0
    for family, weight in allowed:
        accumulator += float(weight)
        if roll <= accumulator:
            return family
    return allowed[-1][0]


def _field_anchor_for_cell(
    cell: SnapshotCell,
    *,
    randomizer: random.Random,
    snapshot: EndgameSnapshot,
    direction: Vec3,
    planar: bool,
    tuning: EndgameAnimationTuning,
) -> Vec3:
    bias_toward_source = _vec_lerp(snapshot.board_center, cell.position, 0.42)
    outward = _vec_mul(
        direction,
        randomizer.uniform(0.15, 0.55) * tuning.anchor_spread_radius,
    )
    tangent = _vec_mul(
        _random_unit_vec3(randomizer, planar=planar),
        randomizer.uniform(0.0, 0.35) * tuning.anchor_spread_radius,
    )
    return _clamp_point_to_scene(
        _vec_add(bias_toward_source, _vec_add(outward, tangent)),
        snapshot=snapshot,
        planar=planar,
        margin=1.25,
    )


def _field_offset_for_relic(
    relic: CellRelic,
    *,
    elapsed_ms: float,
    tuning: EndgameAnimationTuning,
) -> Vec3:
    field_seconds = max(0.0, float(elapsed_ms - tuning.capture_start_ms) / 1000.0)
    phase = _wrap_phase_radians(relic.field_phase + (relic.field_speed * field_seconds))
    precession = _wrap_phase_radians(
        relic.field_phase_secondary + (relic.field_precession_speed * field_seconds)
    )
    if relic.path_family == "lissajous":
        local = (
            relic.orbit_radius_a * math.sin(phase),
            relic.orbit_radius_b * math.sin((phase * 2.0) + precession),
            relic.depth_amplitude * math.cos((phase * 3.0) - (precession * 0.5)),
        )
    elif relic.path_family == "helix":
        local = (
            relic.orbit_radius_a * math.cos(phase),
            relic.orbit_radius_b * math.sin(phase),
            relic.depth_amplitude * math.sin((phase * 0.5) + precession),
        )
    else:
        local = (
            relic.orbit_radius_a * math.cos(phase),
            relic.orbit_radius_b * math.sin(phase + (0.35 * math.sin(precession))),
            relic.depth_amplitude * math.sin(precession),
        )
    return _vec_add(
        _vec_add(
            _vec_mul(relic.field_basis_u, local[0]),
            _vec_mul(relic.field_basis_v, local[1]),
        ),
        _vec_mul(relic.field_basis_w, local[2]),
    )


def _field_half_extents(
    snapshot: EndgameSnapshot,
    *,
    tuning: EndgameAnimationTuning,
    preset: EndgamePresetConfig,
) -> Vec3:
    scale = max(0.2, float(tuning.field_extent_multiplier * preset.extent_scale))
    return (
        max(
            1.0,
            ((float(snapshot.render_dims[0]) - 1.0) * 0.5 * scale) + tuning.wrap_margin,
        ),
        max(
            1.0,
            ((float(snapshot.render_dims[1]) - 1.0) * 0.5 * scale) + tuning.wrap_margin,
        ),
        0.0
        if snapshot.dimension == 2
        else max(
            1.0,
            ((float(snapshot.render_dims[2]) - 1.0) * 0.5 * scale) + tuning.wrap_margin,
        ),
    )


def _wrap_local_axis(value: float, extent: float) -> float:
    if extent <= 0.0:
        return 0.0
    span = extent * 2.0
    wrapped = ((value + extent) % span) - extent
    return float(wrapped)


def _wrap_point_in_box(point: Vec3, *, center: Vec3, extents: Vec3) -> Vec3:
    local = _vec_sub(point, center)
    return _vec_add(
        center,
        (
            _wrap_local_axis(local[0], extents[0]),
            _wrap_local_axis(local[1], extents[1]),
            0.0 if extents[2] <= 0.0 else _wrap_local_axis(local[2], extents[2]),
        ),
    )


def _reflect_local_axis(value: float, extent: float) -> tuple[float, float]:
    if extent <= 0.0:
        return 0.0, 1.0
    span = extent * 2.0
    band = math.floor((value + extent) / span)
    offset = (value + extent) - (band * span)
    if int(band) % 2 == 0:
        return float(-extent + offset), 1.0
    return float(extent - offset), -1.0


def _reflect_point_in_box(
    point: Vec3, *, center: Vec3, extents: Vec3
) -> tuple[Vec3, float]:
    local = _vec_sub(point, center)
    x, sign_x = _reflect_local_axis(local[0], extents[0])
    y, sign_y = _reflect_local_axis(local[1], extents[1])
    if extents[2] <= 0.0:
        z, sign_z = 0.0, 1.0
    else:
        z, sign_z = _reflect_local_axis(local[2], extents[2])
    return _vec_add(center, (x, y, z)), float(sign_x * sign_y * sign_z)


def _sphere_radius_limit(
    snapshot: EndgameSnapshot,
    *,
    tuning: EndgameAnimationTuning,
    preset: EndgamePresetConfig,
) -> float:
    extents = _field_half_extents(snapshot, tuning=tuning, preset=preset)
    candidates = [value for value in extents if value > 0.0]
    base = min(candidates) if candidates else 1.0
    return max(0.8, base * max(0.1, preset.sphere_radius_scale))


def _wrap_field_position(
    relic: CellRelic,
    *,
    elapsed_ms: float,
    snapshot: EndgameSnapshot,
    tuning: EndgameAnimationTuning,
    preset: EndgamePresetConfig,
) -> Vec3:
    field_seconds = max(0.0, float(elapsed_ms - tuning.capture_start_ms) / 1000.0)
    raw_position = _vec_add(
        relic.capture_anchor,
        _vec_add(
            _vec_mul(relic.field_drift_velocity, field_seconds * preset.drift_scale),
            _vec_mul(
                _field_offset_for_relic(relic, elapsed_ms=elapsed_ms, tuning=tuning),
                preset.oscillation_scale,
            ),
        ),
    )
    return _wrap_point_in_box(
        raw_position,
        center=snapshot.board_center,
        extents=_field_half_extents(snapshot, tuning=tuning, preset=preset),
    )


def _invert_field_position(
    relic: CellRelic,
    *,
    elapsed_ms: float,
    snapshot: EndgameSnapshot,
    tuning: EndgameAnimationTuning,
    preset: EndgamePresetConfig,
) -> tuple[Vec3, float]:
    field_seconds = max(0.0, float(elapsed_ms - tuning.capture_start_ms) / 1000.0)
    raw_position = _vec_add(
        relic.capture_anchor,
        _vec_add(
            _vec_mul(relic.field_drift_velocity, field_seconds * preset.drift_scale),
            _vec_mul(
                _field_offset_for_relic(relic, elapsed_ms=elapsed_ms, tuning=tuning),
                preset.oscillation_scale,
            ),
        ),
    )
    return _reflect_point_in_box(
        raw_position,
        center=snapshot.board_center,
        extents=_field_half_extents(snapshot, tuning=tuning, preset=preset),
    )


def _sphere_field_position(
    relic: CellRelic,
    *,
    elapsed_ms: float,
    snapshot: EndgameSnapshot,
    tuning: EndgameAnimationTuning,
    preset: EndgamePresetConfig,
) -> Vec3:
    field_seconds = max(0.0, float(elapsed_ms - tuning.capture_start_ms) / 1000.0)
    phase = _wrap_phase_radians(relic.field_phase + (relic.field_speed * field_seconds))
    precession = _wrap_phase_radians(
        relic.field_phase_secondary + (relic.field_precession_speed * field_seconds)
    )
    center = snapshot.board_center
    radial = _normalize_or_default(
        _vec_sub(relic.capture_anchor, center),
        (0.0, -1.0, 0.0),
    )
    tangent_u = _normalize_or_default(
        _vec_sub(
            relic.field_basis_u, _vec_mul(radial, _vec_dot(relic.field_basis_u, radial))
        ),
        (1.0, 0.0, 0.0),
    )
    tangent_v = _normalize_or_default(
        _vec_cross(radial, tangent_u), relic.field_basis_v
    )
    radius_limit = _sphere_radius_limit(snapshot, tuning=tuning, preset=preset)
    base_radius = max(
        radius_limit * 0.32,
        min(radius_limit * 0.92, relic.field_radius_band),
    )
    tangent = _vec_add(
        _vec_mul(
            tangent_u,
            relic.orbit_radius_a * preset.tangential_bias * math.cos(phase),
        ),
        _vec_mul(
            tangent_v,
            relic.orbit_radius_b
            * preset.tangential_bias
            * math.sin(phase + (0.35 * math.sin(precession))),
        ),
    )
    local = _vec_add(
        _vec_mul(
            radial,
            base_radius + (relic.depth_amplitude * 0.22 * math.sin(precession)),
        ),
        _vec_mul(tangent, preset.oscillation_scale),
    )
    distance = _vec_len(local)
    if distance <= radius_limit:
        return _vec_add(center, local)
    corrected = max(
        radius_limit * 0.24,
        radius_limit - ((distance - radius_limit) * preset.radial_correction_strength),
    )
    return _vec_add(
        center,
        _vec_mul(_normalize_or_default(local, radial), corrected),
    )


def relic_field_phase_radians(
    relic: CellRelic,
    *,
    elapsed_ms: float,
    tuning: EndgameAnimationTuning,
) -> float:
    field_seconds = max(0.0, float(elapsed_ms - tuning.capture_start_ms) / 1000.0)
    return _wrap_phase_radians(relic.field_phase + (relic.field_speed * field_seconds))


def endgame_preset_registry(
    tuning: EndgameAnimationTuning | None = None,
) -> tuple[EndgamePresetConfig, ...]:
    active_tuning = load_endgame_animation_tuning() if tuning is None else tuning
    return active_tuning.preset_registry


def resolve_endgame_preset_config(
    preset_id: str,
    *,
    tuning: EndgameAnimationTuning | None = None,
) -> EndgamePresetConfig:
    active_tuning = load_endgame_animation_tuning() if tuning is None else tuning
    return active_tuning.preset_config_for(preset_id)


def _burst_translation(
    *,
    initial_position: Vec3,
    velocity: Vec3,
    acceleration: Vec3,
    jitter_offset: Vec3,
    detach_start_ms: float,
    elapsed_ms: float,
    drag_per_second: float,
) -> Vec3:
    if elapsed_ms <= detach_start_ms:
        crack_denominator = max(1.0, float(detach_start_ms))
        crack_progress = max(0.0, min(1.0, float(elapsed_ms / crack_denominator)))
        return _vec_add(initial_position, _vec_mul(jitter_offset, crack_progress))
    travel_seconds = max(0.0, float(elapsed_ms - detach_start_ms) / 1000.0)
    drag = max(0.0, float(drag_per_second))
    linear_scale = (
        travel_seconds
        if drag <= 0.0
        else (travel_seconds / (1.0 + (drag * travel_seconds)))
    )
    accel_scale = (
        travel_seconds * travel_seconds
        if drag <= 0.0
        else (
            (travel_seconds * travel_seconds)
            / (1.0 + (drag * travel_seconds * travel_seconds))
        )
    )
    displacement = _vec_mul(velocity, linear_scale)
    acceleration_term = _vec_mul(acceleration, 0.5 * accel_scale)
    return _vec_add(initial_position, _vec_add(displacement, acceleration_term))


def _wrapped_rotation_deg(value: Vec3) -> Vec3:
    return (value[0] % 360.0, value[1] % 360.0, value[2] % 360.0)


def _burst_rotation_deg(
    *,
    angular_velocity_deg: Vec3,
    detach_start_ms: float,
    elapsed_ms: float,
) -> Vec3:
    if elapsed_ms <= detach_start_ms:
        return (0.0, 0.0, 0.0)
    travel_seconds = max(0.0, float(elapsed_ms - detach_start_ms) / 1000.0)
    return _wrapped_rotation_deg(_vec_mul(angular_velocity_deg, travel_seconds))


def _relic_capture_progress(
    *,
    elapsed_ms: float,
    tuning: EndgameAnimationTuning,
) -> float:
    if elapsed_ms <= tuning.capture_start_ms:
        return 0.0
    if tuning.capture_transition_duration_ms <= 0.0:
        return 1.0
    return _smoothstep01(
        (float(elapsed_ms) - tuning.capture_start_ms)
        / float(tuning.capture_transition_duration_ms)
    )


def _shell_alpha(
    *,
    elapsed_ms: float,
    fade_start_ms: float,
    lifetime_ms: float,
) -> float:
    if elapsed_ms >= lifetime_ms:
        return 0.0
    if elapsed_ms <= fade_start_ms:
        return 1.0
    fade_window = max(1.0, float(lifetime_ms - fade_start_ms))
    return max(0.0, 1.0 - ((float(elapsed_ms) - fade_start_ms) / fade_window))


def _cell_relic_from_snapshot_cell(
    cell: SnapshotCell,
    *,
    randomizer: random.Random,
    snapshot: EndgameSnapshot,
    tuning: EndgameAnimationTuning,
    planar: bool,
) -> CellRelic:
    direction = _fragment_direction(
        randomizer=randomizer,
        origin=cell.position,
        board_center=snapshot.board_center,
        planar=planar,
        outward_bias_strength=tuning.outward_bias_strength,
        random_spread_strength=tuning.random_spread_strength,
    )
    basis_u, basis_v, basis_w = _field_basis(
        randomizer=randomizer,
        direction=direction,
        planar=planar,
    )
    max_radius = max(
        tuning.orbit_radius_min,
        min(tuning.orbit_radius_max, _scene_extent_limit(snapshot)),
    )
    max_depth = max(
        tuning.orbit_depth_amplitude_min,
        min(
            tuning.orbit_depth_amplitude_max,
            _scene_extent_limit(snapshot) * 0.8,
        ),
    )
    field_speed = randomizer.uniform(
        tuning.relic_field_speed_min,
        tuning.relic_field_speed_max,
    )
    collision_radius_max = max(
        tuning.collision_radius_min,
        tuning.collision_radius_max,
    )
    return CellRelic(
        source_coord=cell.source_coord,
        base_geometry="cell",
        initial_position=cell.position,
        burst_velocity=_vec_mul(
            direction,
            randomizer.uniform(
                tuning.relic_burst_speed_min,
                tuning.relic_burst_speed_max,
            ),
        ),
        burst_acceleration=(0.0, tuning.burst_gravity_per_second, 0.0),
        burst_angular_velocity_deg=_random_angular_velocity(
            randomizer,
            planar=planar,
            minimum=tuning.burst_angular_velocity_deg_min,
            maximum=tuning.burst_angular_velocity_deg_max,
        ),
        detach_start_ms=tuning.crack_onset_duration_ms
        + (tuning.capture_transition_duration_ms * 0.4 * randomizer.random()),
        capture_anchor=_field_anchor_for_cell(
            cell,
            randomizer=randomizer,
            snapshot=snapshot,
            direction=direction,
            planar=planar,
            tuning=tuning,
        ),
        path_family=_choose_path_family(
            randomizer=randomizer,
            tuning=tuning,
            planar=planar,
        ),
        field_basis_u=basis_u,
        field_basis_v=basis_v,
        field_basis_w=basis_w if not planar else (0.0, 0.0, 0.0),
        field_phase=randomizer.uniform(0.0, _TAU),
        field_phase_secondary=randomizer.uniform(0.0, _TAU),
        field_speed=field_speed,
        field_precession_speed=field_speed * randomizer.uniform(0.35, 0.85),
        orbit_radius_a=randomizer.uniform(tuning.orbit_radius_min, max_radius),
        orbit_radius_b=randomizer.uniform(tuning.orbit_radius_min, max_radius),
        depth_amplitude=0.0
        if planar
        else randomizer.uniform(tuning.orbit_depth_amplitude_min, max_depth),
        relic_spin_deg=_random_angular_velocity(
            randomizer,
            planar=planar,
            minimum=tuning.relic_spin_deg_min,
            maximum=tuning.relic_spin_deg_max,
        ),
        color_id=cell.color_id,
        layer_index=cell.layer_index,
        jitter_offset=_vec_mul(
            _random_unit_vec3(randomizer, planar=planar),
            randomizer.uniform(0.12, 0.65),
        ),
        preset_id=snapshot.preset_id,
        field_drift_velocity=_vec_mul(
            _random_unit_vec3(randomizer, planar=planar),
            field_speed * randomizer.uniform(1.05, 1.85),
        ),
        field_radius_band=randomizer.uniform(
            max(tuning.orbit_radius_min, 0.8),
            max(max_radius, tuning.orbit_radius_min),
        ),
        collision_radius=randomizer.uniform(
            tuning.collision_radius_min,
            collision_radius_max,
        ),
        collision_mass=randomizer.uniform(0.85, 1.25),
        spin_handedness=_random_signed(randomizer),
    )


def _shell_segment_center(segment: tuple[Vec3, Vec3]) -> Vec3:
    start, end = segment
    return (
        (start[0] + end[0]) * 0.5,
        (start[1] + end[1]) * 0.5,
        (start[2] + end[2]) * 0.5,
    )


def _shell_segment_local_points(segment: tuple[Vec3, Vec3]) -> tuple[Vec3, Vec3]:
    center = _shell_segment_center(segment)
    start, end = segment
    return (_vec_sub(start, center), _vec_sub(end, center))


def _shell_fragment_from_segment(
    segment: tuple[Vec3, Vec3],
    *,
    layer_index: int | None,
    source_kind: str,
    source_index: int,
    randomizer: random.Random,
    snapshot: EndgameSnapshot,
    tuning: EndgameAnimationTuning,
    planar: bool,
) -> ShellFragment:
    center = _shell_segment_center(segment)
    direction = _fragment_direction(
        randomizer=randomizer,
        origin=center,
        board_center=snapshot.board_center,
        planar=planar,
        outward_bias_strength=tuning.outward_bias_strength,
        random_spread_strength=tuning.random_spread_strength,
    )
    speed = randomizer.uniform(
        tuning.shell_fragment_speed_min,
        tuning.shell_fragment_speed_max,
    )
    detach_start_ms = tuning.crack_onset_duration_ms * randomizer.random()
    jitter_scale = (tuning.crack_onset_duration_ms / 1000.0) * speed
    return ShellFragment(
        source_kind=source_kind,
        source_index=int(source_index),
        base_geometry=_shell_segment_local_points(segment),
        initial_position=center,
        velocity=_vec_mul(direction, speed),
        acceleration=(0.0, tuning.burst_gravity_per_second, 0.0),
        angular_velocity_deg=_random_angular_velocity(
            randomizer,
            planar=planar,
            minimum=tuning.burst_angular_velocity_deg_min,
            maximum=tuning.burst_angular_velocity_deg_max,
        ),
        detach_start_ms=detach_start_ms,
        fade_start_ms=tuning.shell_fade_start_ms,
        lifetime_ms=tuning.shell_fragment_lifetime_ms,
        layer_index=layer_index,
        jitter_offset=_vec_mul(
            _random_unit_vec3(randomizer, planar=planar),
            jitter_scale,
        ),
    )


def _segments_for_2d_grid(
    *,
    width: int,
    height: int,
) -> tuple[tuple[str, int | None, tuple[Vec3, Vec3]], ...]:
    segments: list[tuple[str, int | None, tuple[Vec3, Vec3]]] = []
    for x in range(width + 1):
        raw_x = float(x) - 0.5
        for y in range(height):
            segments.append(
                (
                    "gridline",
                    None,
                    (
                        (raw_x, float(y) - 0.5, 0.0),
                        (raw_x, float(y) + 0.5, 0.0),
                    ),
                )
            )
    for y in range(height + 1):
        raw_y = float(y) - 0.5
        for x in range(width):
            segments.append(
                (
                    "gridline",
                    None,
                    (
                        (float(x) - 0.5, raw_y, 0.0),
                        (float(x) + 0.5, raw_y, 0.0),
                    ),
                )
            )
    return tuple(segments)


def _box_edge_segments(
    *,
    dims: tuple[int, int, int],
    layer_index: int | None = None,
) -> tuple[tuple[str, int | None, tuple[Vec3, Vec3]], ...]:
    max_x = float(dims[0]) - 0.5
    max_y = float(dims[1]) - 0.5
    max_z = float(dims[2]) - 0.5
    min_x = -0.5
    min_y = -0.5
    min_z = -0.5
    corners = (
        (min_x, min_y, min_z),
        (max_x, min_y, min_z),
        (max_x, max_y, min_z),
        (min_x, max_y, min_z),
        (min_x, min_y, max_z),
        (max_x, min_y, max_z),
        (max_x, max_y, max_z),
        (min_x, max_y, max_z),
    )
    edge_pairs = (
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    )
    return tuple(
        ("box_edge", layer_index, (corners[a], corners[b])) for a, b in edge_pairs
    )


def build_endgame_animation_state(
    snapshot: EndgameSnapshot,
    *,
    tuning: EndgameAnimationTuning | None = None,
) -> EndgameAnimationState:
    active_tuning = load_endgame_animation_tuning() if tuning is None else tuning
    if not active_tuning.enabled:
        return EndgameAnimationState(
            snapshot=snapshot,
            tuning=active_tuning,
            shatter=EndgameShatterState(shell_fragments=tuple()),
            relic_field=EndgameRelicFieldState(
                cell_relics=tuple(),
                preset_id=snapshot.preset_id,
                interaction_mode=snapshot.interaction_mode,
            ),
            phase=TERMINAL_PHASE_GAME_OVER_COMPLETE,
            elapsed_ms=float(active_tuning.prompt_ready_ms),
        )

    randomizer = random.Random(snapshot.rng_seed)
    planar = snapshot.dimension == 2
    cell_relics = tuple(
        _cell_relic_from_snapshot_cell(
            cell,
            randomizer=randomizer,
            snapshot=snapshot,
            tuning=active_tuning,
            planar=planar,
        )
        for cell in snapshot.locked_cells
    )

    if snapshot.dimension == 2:
        shell_sources = _segments_for_2d_grid(
            width=int(snapshot.board_dims[0]),
            height=int(snapshot.board_dims[1]),
        )
    elif snapshot.dimension == 3:
        shell_sources = _box_edge_segments(dims=snapshot.render_dims)
    else:
        shell_sources = tuple(
            segment
            for layer_index in range(max(1, snapshot.render_context.layer_count))
            for segment in _box_edge_segments(
                dims=snapshot.render_dims,
                layer_index=layer_index,
            )
        )

    shell_fragments = tuple(
        _shell_fragment_from_segment(
            segment=segment,
            layer_index=layer_index,
            source_kind=source_kind,
            source_index=index,
            randomizer=randomizer,
            snapshot=snapshot,
            tuning=active_tuning,
            planar=planar,
        )
        for index, (source_kind, layer_index, segment) in enumerate(shell_sources)
    )
    return EndgameAnimationState(
        snapshot=snapshot,
        tuning=active_tuning,
        shatter=EndgameShatterState(shell_fragments=shell_fragments),
        relic_field=EndgameRelicFieldState(
            cell_relics=cell_relics,
            preset_id=snapshot.preset_id,
            interaction_mode=snapshot.interaction_mode,
        ),
    )


def ensure_endgame_animation(
    current: EndgameAnimationState | None,
    *,
    game_over: bool,
    snapshot_factory: Callable[[], EndgameSnapshot],
    tuning: EndgameAnimationTuning | None = None,
) -> EndgameAnimationState | None:
    if not game_over:
        return None
    if current is not None:
        return current
    return build_endgame_animation_state(snapshot_factory(), tuning=tuning)


def fragment_alpha(
    *, elapsed_ms: float, fade_start_ms: float, lifetime_ms: float
) -> float:
    return _shell_alpha(
        elapsed_ms=elapsed_ms,
        fade_start_ms=fade_start_ms,
        lifetime_ms=lifetime_ms,
    )


def fragment_translation(
    *,
    initial_position: Vec3,
    velocity: Vec3,
    acceleration: Vec3,
    jitter_offset: Vec3,
    detach_start_ms: float,
    elapsed_ms: float,
    drag_per_second: float,
) -> Vec3:
    return _burst_translation(
        initial_position=initial_position,
        velocity=velocity,
        acceleration=acceleration,
        jitter_offset=jitter_offset,
        detach_start_ms=detach_start_ms,
        elapsed_ms=elapsed_ms,
        drag_per_second=drag_per_second,
    )


def fragment_rotation_deg(
    *,
    angular_velocity_deg: Vec3,
    detach_start_ms: float,
    elapsed_ms: float,
) -> Vec3:
    return _burst_rotation_deg(
        angular_velocity_deg=angular_velocity_deg,
        detach_start_ms=detach_start_ms,
        elapsed_ms=elapsed_ms,
    )


def transform_for_cell_relic(
    relic: CellRelic,
    *,
    elapsed_ms: float,
    tuning: EndgameAnimationTuning,
    snapshot: EndgameSnapshot | None = None,
    preset_id: str | None = None,
    spin_handedness: float | None = None,
) -> tuple[Vec3, Vec3, float]:
    active_preset_id = normalize_endgame_preset_id(
        preset_id if preset_id is not None else relic.preset_id,
        default=tuning.default_preset_id,
    )
    active_snapshot = snapshot
    preset = tuning.preset_config_for(active_preset_id)
    burst_position = _burst_translation(
        initial_position=relic.initial_position,
        velocity=relic.burst_velocity,
        acceleration=relic.burst_acceleration,
        jitter_offset=relic.jitter_offset,
        detach_start_ms=relic.detach_start_ms,
        elapsed_ms=elapsed_ms,
        drag_per_second=tuning.burst_drag_per_second,
    )
    field_position = _vec_add(
        relic.capture_anchor,
        _field_offset_for_relic(
            relic,
            elapsed_ms=elapsed_ms,
            tuning=tuning,
        ),
    )
    effective_spin_handedness = (
        relic.spin_handedness if spin_handedness is None else float(spin_handedness)
    )
    if active_snapshot is not None:
        if preset.field_kind == "wrap":
            field_position = _wrap_field_position(
                relic,
                elapsed_ms=elapsed_ms,
                snapshot=active_snapshot,
                tuning=tuning,
                preset=preset,
            )
        elif preset.field_kind == "invert":
            field_position, invert_sign = _invert_field_position(
                relic,
                elapsed_ms=elapsed_ms,
                snapshot=active_snapshot,
                tuning=tuning,
                preset=preset,
            )
            effective_spin_handedness *= invert_sign
        elif preset.field_kind == "sphere":
            field_position = _sphere_field_position(
                relic,
                elapsed_ms=elapsed_ms,
                snapshot=active_snapshot,
                tuning=tuning,
                preset=preset,
            )
    capture_progress = _relic_capture_progress(
        elapsed_ms=elapsed_ms,
        tuning=tuning,
    )
    burst_rotation = _burst_rotation_deg(
        angular_velocity_deg=relic.burst_angular_velocity_deg,
        detach_start_ms=relic.detach_start_ms,
        elapsed_ms=elapsed_ms,
    )
    field_seconds = max(0.0, float(elapsed_ms - tuning.capture_start_ms) / 1000.0)
    field_phase = relic_field_phase_radians(
        relic,
        elapsed_ms=elapsed_ms,
        tuning=tuning,
    )
    field_rotation = _wrapped_rotation_deg(
        (
            (relic.relic_spin_deg[0] * field_seconds * effective_spin_handedness)
            + (18.0 * math.sin(field_phase + relic.field_phase_secondary)),
            (relic.relic_spin_deg[1] * field_seconds * effective_spin_handedness)
            + (14.0 * math.cos((field_phase * 0.5) + relic.field_phase_secondary)),
            (relic.relic_spin_deg[2] * field_seconds * effective_spin_handedness)
            + (24.0 * math.sin((field_phase * 0.75) - relic.field_phase_secondary)),
        )
    )
    return (
        _vec_lerp(burst_position, field_position, capture_progress),
        _wrapped_rotation_deg(
            _vec_lerp(burst_rotation, field_rotation, capture_progress)
        ),
        1.0,
    )


def _estimate_relic_velocity(
    relic: CellRelic,
    *,
    elapsed_ms: float,
    tuning: EndgameAnimationTuning,
    snapshot: EndgameSnapshot,
    preset_id: str,
) -> Vec3:
    sample_ms = float(tuning.collision_velocity_sample_ms)
    if sample_ms <= 0.0:
        return (0.0, 0.0, 0.0)
    position_now, _rotation, _alpha = transform_for_cell_relic(
        relic,
        elapsed_ms=elapsed_ms,
        tuning=tuning,
        snapshot=snapshot,
        preset_id=preset_id,
    )
    position_next, _rotation_next, _alpha_next = transform_for_cell_relic(
        relic,
        elapsed_ms=elapsed_ms + sample_ms,
        tuning=tuning,
        snapshot=snapshot,
        preset_id=preset_id,
    )
    return _vec_mul(
        _vec_sub(position_next, position_now),
        1000.0 / sample_ms,
    )


def _apply_boundary_post_collision(
    position: Vec3,
    *,
    snapshot: EndgameSnapshot,
    tuning: EndgameAnimationTuning,
    preset_id: str,
) -> tuple[Vec3, float]:
    preset = tuning.preset_config_for(preset_id)
    if preset.field_kind == "wrap":
        return (
            _wrap_point_in_box(
                position,
                center=snapshot.board_center,
                extents=_field_half_extents(snapshot, tuning=tuning, preset=preset),
            ),
            1.0,
        )
    if preset.field_kind == "invert":
        return _reflect_point_in_box(
            position,
            center=snapshot.board_center,
            extents=_field_half_extents(snapshot, tuning=tuning, preset=preset),
        )
    if preset.field_kind == "sphere":
        local = _vec_sub(position, snapshot.board_center)
        radius_limit = _sphere_radius_limit(snapshot, tuning=tuning, preset=preset)
        distance = _vec_len(local)
        if distance <= radius_limit:
            return position, 1.0
        return (
            _vec_add(
                snapshot.board_center,
                _vec_mul(_normalize_or_default(local, (0.0, -1.0, 0.0)), radius_limit),
            ),
            1.0,
        )
    return position, 1.0


def _apply_relic_collisions(
    relics: tuple[CellRelic, ...],
    *,
    transforms: list[tuple[Vec3, Vec3, float]],
    elapsed_ms: float,
    tuning: EndgameAnimationTuning,
    snapshot: EndgameSnapshot,
    preset_id: str,
) -> tuple[tuple[Vec3, Vec3, float], ...]:
    if len(relics) < 2 or elapsed_ms < float(tuning.shatter_duration_ms):
        return tuple(transforms)
    colliding_count = min(len(relics), int(tuning.collision_max_relics))
    indexed = sorted(
        range(colliding_count),
        key=lambda index: (
            tuple(relics[index].source_coord),
            int(relics[index].color_id),
        ),
    )
    positions = [position for position, _rotation, _alpha in transforms]
    rotations = [rotation for _position, rotation, _alpha in transforms]
    alphas = [alpha for _position, _rotation, alpha in transforms]
    velocities = [
        _estimate_relic_velocity(
            relics[index],
            elapsed_ms=elapsed_ms,
            tuning=tuning,
            snapshot=snapshot,
            preset_id=preset_id,
        )
        for index in range(colliding_count)
    ]
    spin_signs = [1.0 for _ in range(colliding_count)]
    for left_offset, left_index in enumerate(indexed):
        for right_index in indexed[left_offset + 1 :]:
            delta = _vec_sub(positions[right_index], positions[left_index])
            distance = _vec_len(delta)
            min_distance = float(relics[left_index].collision_radius) + float(
                relics[right_index].collision_radius
            )
            if distance >= min_distance:
                continue
            normal = _normalize_or_default(
                delta,
                (
                    1.0 if (right_index - left_index) % 2 == 0 else -1.0,
                    0.5,
                    0.0 if snapshot.dimension == 2 else 0.35,
                ),
            )
            overlap = max(
                0.0, (min_distance - distance) * tuning.collision_separation_bias
            )
            total_mass = max(
                0.001,
                float(
                    relics[left_index].collision_mass
                    + relics[right_index].collision_mass
                ),
            )
            left_share = float(relics[right_index].collision_mass) / total_mass
            right_share = float(relics[left_index].collision_mass) / total_mass
            positions[left_index] = _vec_sub(
                positions[left_index],
                _vec_mul(normal, overlap * left_share),
            )
            positions[right_index] = _vec_add(
                positions[right_index],
                _vec_mul(normal, overlap * right_share),
            )
            relative_speed = _vec_dot(
                _vec_sub(velocities[right_index], velocities[left_index]),
                normal,
            )
            if relative_speed < 0.0:
                impulse = (
                    -((1.0 + float(tuning.collision_restitution)) * relative_speed)
                    / total_mass
                )
                velocities[left_index] = _vec_sub(
                    velocities[left_index],
                    _vec_mul(
                        normal, impulse * float(relics[right_index].collision_mass)
                    ),
                )
                velocities[right_index] = _vec_add(
                    velocities[right_index],
                    _vec_mul(
                        normal, impulse * float(relics[left_index].collision_mass)
                    ),
                )
            spin_signs[left_index] *= -1.0
            spin_signs[right_index] *= -1.0
    resolved: list[tuple[Vec3, Vec3, float]] = list(transforms)
    for index in range(colliding_count):
        bounded_position, boundary_spin = _apply_boundary_post_collision(
            positions[index],
            snapshot=snapshot,
            tuning=tuning,
            preset_id=preset_id,
        )
        velocity_magnitude = _vec_len(velocities[index]) * float(
            tuning.collision_damping
        )
        resolved_rotation = _wrapped_rotation_deg(
            _vec_add(
                rotations[index],
                _vec_mul(
                    relics[index].relic_spin_deg,
                    min(
                        0.3,
                        velocity_magnitude * 0.018 * spin_signs[index] * boundary_spin,
                    ),
                ),
            )
        )
        resolved[index] = (bounded_position, resolved_rotation, alphas[index])
    return tuple(resolved)


def transform_relics_for_animation(
    animation: EndgameAnimationState,
) -> tuple[tuple[Vec3, Vec3, float], ...]:
    transforms = [
        transform_for_cell_relic(
            relic,
            elapsed_ms=float(animation.elapsed_ms),
            tuning=animation.tuning,
            snapshot=animation.snapshot,
            preset_id=animation.preset_id,
        )
        for relic in animation.cell_relics
    ]
    if animation.interaction_mode != ENDGAME_INTERACTION_COLLIDE:
        return tuple(transforms)
    return _apply_relic_collisions(
        animation.cell_relics,
        transforms=transforms,
        elapsed_ms=float(animation.elapsed_ms),
        tuning=animation.tuning,
        snapshot=animation.snapshot,
        preset_id=animation.preset_id,
    )


def transform_for_cell_fragment(
    fragment: CellRelic,
    *,
    elapsed_ms: float,
    drag_per_second: float,
) -> tuple[Vec3, Vec3, float]:
    del drag_per_second
    return transform_for_cell_relic(
        fragment,
        elapsed_ms=elapsed_ms,
        tuning=load_endgame_animation_tuning(),
    )


def transform_for_shell_fragment(
    fragment: ShellFragment,
    *,
    elapsed_ms: float,
    drag_per_second: float,
) -> tuple[Vec3, Vec3, float]:
    return (
        _burst_translation(
            initial_position=fragment.initial_position,
            velocity=fragment.velocity,
            acceleration=fragment.acceleration,
            jitter_offset=fragment.jitter_offset,
            detach_start_ms=fragment.detach_start_ms,
            elapsed_ms=elapsed_ms,
            drag_per_second=drag_per_second,
        ),
        _burst_rotation_deg(
            angular_velocity_deg=fragment.angular_velocity_deg,
            detach_start_ms=fragment.detach_start_ms,
            elapsed_ms=elapsed_ms,
        ),
        _shell_alpha(
            elapsed_ms=elapsed_ms,
            fade_start_ms=fragment.fade_start_ms,
            lifetime_ms=fragment.lifetime_ms,
        ),
    )


def rotate_point(point: Vec3, rotation_deg: Vec3) -> Vec3:
    x, y, z = point
    rx, ry, rz = (
        math.radians(rotation_deg[0]),
        math.radians(rotation_deg[1]),
        math.radians(rotation_deg[2]),
    )

    cos_x, sin_x = math.cos(rx), math.sin(rx)
    y, z = ((y * cos_x) - (z * sin_x), (y * sin_x) + (z * cos_x))

    cos_y, sin_y = math.cos(ry), math.sin(ry)
    x, z = ((x * cos_y) + (z * sin_y), (-x * sin_y) + (z * cos_y))

    cos_z, sin_z = math.cos(rz), math.sin(rz)
    x, y = ((x * cos_z) - (y * sin_z), (x * sin_z) + (y * cos_z))
    return (x, y, z)


def transform_shell_geometry(
    fragment: ShellFragment,
    *,
    elapsed_ms: float,
    drag_per_second: float,
) -> tuple[tuple[Vec3, Vec3], float]:
    position, rotation, alpha = transform_for_shell_fragment(
        fragment,
        elapsed_ms=elapsed_ms,
        drag_per_second=drag_per_second,
    )
    start_local, end_local = fragment.base_geometry
    start_point = _vec_add(position, rotate_point(start_local, rotation))
    end_point = _vec_add(position, rotate_point(end_local, rotation))
    return (start_point, end_point), alpha


__all__ = [
    "CellFragment",
    "CellRelic",
    "EndgameAnimationState",
    "EndgameAnimationTuning",
    "EndgamePresetConfig",
    "EndgameRelicFieldState",
    "EndgameRenderContext",
    "EndgameShatterState",
    "EndgameSnapshot",
    "ShellFragment",
    "SnapshotCell",
    "TERMINAL_PHASE_ENDGAME_RELIC_FIELD",
    "TERMINAL_PHASE_ENDGAME_SHATTER",
    "TERMINAL_PHASE_GAME_OVER_ANIMATING",
    "TERMINAL_PHASE_GAME_OVER_COMPLETE",
    "TERMINAL_PHASE_PLAYING",
    "build_endgame_animation_state",
    "create_snapshot",
    "derive_endgame_seed",
    "endgame_prompt_ready",
    "endgame_preset_registry",
    "endgame_sfx_events_between",
    "ensure_endgame_animation",
    "fragment_alpha",
    "fragment_rotation_deg",
    "fragment_translation",
    "load_endgame_animation_tuning",
    "relic_field_phase_radians",
    "resolve_endgame_preset_config",
    "rotate_point",
    "transform_for_cell_fragment",
    "transform_for_cell_relic",
    "transform_relics_for_animation",
    "transform_for_shell_fragment",
    "transform_shell_geometry",
]
