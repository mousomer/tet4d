from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable
import math
import random

from tet4d.engine.runtime.endgame_presets import (
    ENDGAME_BOUNDARY_RESPONSE_ESCAPE,
    ENDGAME_PARTICLE_COLLISIONS_OFF,
    ENDGAME_PRESET_DEFAULT_ORBIT,
    ENDGAME_PRESET_IDS,
    ENDGAME_PRESET_INVERT_ALL,
    ENDGAME_PRESET_SPHERE,
    ENDGAME_PRESET_WRAP_ALL,
    normalize_endgame_boundary_response,
    normalize_endgame_particle_collisions,
    normalize_endgame_preset_id,
)
from tet4d.engine.runtime.project_config import constants_payload
from tet4d.ui.pygame.locked_cell_explosion import (
    ExplosionSeedCell,
    ExplosionTopologyInput,
    StandaloneExplosionConfig,
    build_locked_cell_explosion,
)
from tet4d.ui.pygame.locked_cell_explosion.defaults_store import (
    ENDGAME_LIVE_CELL_FRACTION_DEFAULT,
    clamp_endgame_live_cell_fraction,
)

Vec3 = tuple[float, float, float]
VecN = tuple[float, ...]

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
    shell_artifact_birth_spread_ms: float
    shell_artifact_lifetime_min_ms: float
    shell_artifact_lifetime_max_ms: float
    grid_break_birth_lead_ms: float
    grid_break_lifetime_ms: float
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
    default_boundary_response: str
    default_particle_collisions: str
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
        shell_artifact_birth_spread_ms=_clamp_float(
            payload.get("shell_artifact_birth_spread_ms"),
            default=180.0,
            minimum=0.0,
        ),
        shell_artifact_lifetime_min_ms=_clamp_float(
            payload.get("shell_artifact_lifetime_min_ms"),
            default=520.0,
            minimum=1.0,
        ),
        shell_artifact_lifetime_max_ms=_clamp_float(
            payload.get("shell_artifact_lifetime_max_ms"),
            default=860.0,
            minimum=1.0,
        ),
        grid_break_birth_lead_ms=_clamp_float(
            payload.get("grid_break_birth_lead_ms"),
            default=90.0,
            minimum=0.0,
        ),
        grid_break_lifetime_ms=_clamp_float(
            payload.get("grid_break_lifetime_ms"),
            default=560.0,
            minimum=1.0,
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
        default_boundary_response=normalize_endgame_boundary_response(
            payload.get("default_boundary_response"),
            default=ENDGAME_BOUNDARY_RESPONSE_ESCAPE,
        ),
        default_particle_collisions=normalize_endgame_particle_collisions(
            payload.get("default_particle_collisions"),
            default=ENDGAME_PARTICLE_COLLISIONS_OFF,
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
    basis_axis_map: tuple[tuple[int, int], ...] = ()
    layer_axis: int = 3
    layer_sign: int = 1
    w_movement_animation_style: str = "fade"


@dataclass(frozen=True)
class SnapshotCell:
    source_coord: tuple[int, ...]
    position: VecN
    color_id: int
    layer_index: int | None = None


@dataclass(frozen=True)
class EndgameSnapshot:
    dimension: int
    board_dims: tuple[int, ...]
    render_dims: tuple[int, int, int]
    board_center: VecN
    render_center: Vec3
    locked_cells: tuple[SnapshotCell, ...]
    persistent_live_cells: tuple[SnapshotCell, ...]
    escaping_cells: tuple[SnapshotCell, ...]
    rng_seed: int
    render_context: EndgameRenderContext
    preset_id: str = ENDGAME_PRESET_DEFAULT_ORBIT
    boundary_response: str = ENDGAME_BOUNDARY_RESPONSE_ESCAPE
    particle_collisions: str = ENDGAME_PARTICLE_COLLISIONS_OFF
    mass_mode: str = "uniform"
    base_mass: float = 1.0
    random_mass_min: float = 0.75
    random_mass_max: float = 1.25
    collision_elasticity: float = 1.0
    diagnostics_mode: str = "off"
    trace_retention_ms: float = 2640.0
    speed_preset: str = "normal"
    grid_mode: str = "full"
    shadow_mode: str = "off"
    trace_enabled: bool = False
    w_movement_animation_style: str = "fade"
    endgame_live_cell_fraction: float = ENDGAME_LIVE_CELL_FRACTION_DEFAULT
    relic_speed_scale: float = 1.0
    shatter_speed_scale: float = 1.0
    topology: ExplosionTopologyInput = field(
        default_factory=lambda: ExplosionTopologyInput(board_dims=(1, 1)),
        compare=False,
    )
    sound_enabled: bool = True


@dataclass(frozen=True)
class EndgameCellSplit:
    persistent_live_cells: tuple[SnapshotCell, ...]
    escaping_cells: tuple[SnapshotCell, ...]


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
class EndgameShellArtifact:
    source_coord: tuple[int, ...]
    start_position: VecN
    direction: VecN
    speed: float
    color_id: int
    birth_ms: float
    lifetime_ms: float
    kind: str


@dataclass(frozen=True)
class EndgameGridBreakMark:
    source_coord: tuple[int, ...]
    center_position: VecN
    direction: VecN
    color_id: int
    birth_ms: float
    lifetime_ms: float
    length: float
    kind: str


@dataclass(frozen=True)
class EndgameShatterState:
    shell_fragments: tuple[ShellFragment, ...]


@dataclass
class EndgameAnimationState:
    snapshot: EndgameSnapshot
    tuning: EndgameAnimationTuning
    shatter: EndgameShatterState
    phase: str = TERMINAL_PHASE_ENDGAME_SHATTER
    elapsed_ms: float = 0.0
    explosion_controller: object | None = None
    escaping_artifacts: tuple[EndgameShellArtifact, ...] = ()
    grid_break_marks: tuple[EndgameGridBreakMark, ...] = ()
    _pending_audio_events: tuple[str, ...] = ()

    @property
    def shell_fragments(self) -> tuple[ShellFragment, ...]:
        return self.shatter.shell_fragments

    @property
    def frozen_render_active(self) -> bool:
        return self.phase != TERMINAL_PHASE_PLAYING

    @property
    def animating(self) -> bool:
        return self.phase in (
            TERMINAL_PHASE_ENDGAME_SHATTER,
            TERMINAL_PHASE_ENDGAME_RELIC_FIELD,
        )

    def step(self, dt_ms: float) -> None:
        if not self.animating:
            return
        if self.explosion_controller is not None:
            self._pending_audio_events = tuple(
                self.explosion_controller.step(float(dt_ms))
            )
        self.elapsed_ms = float(self.elapsed_ms + max(0.0, dt_ms))
        if self.elapsed_ms >= float(self.tuning.shatter_duration_ms):
            self.phase = TERMINAL_PHASE_ENDGAME_RELIC_FIELD
        else:
            self.phase = TERMINAL_PHASE_ENDGAME_SHATTER

    def consume_audio_events(self) -> tuple[str, ...]:
        events = tuple(self._pending_audio_events)
        self._pending_audio_events = ()
        return events


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


_ENDGAME_SHELL_ARTIFACT_CAPS = {
    2: 32,
    3: 40,
    4: 48,
}

_ENDGAME_GRID_BREAK_CAPS = {
    2: 12,
    3: 16,
    4: 20,
}

_ENDGAME_SHELL_ARTIFACT_KINDS = ("streak", "shard", "spark")
_ENDGAME_GRID_BREAK_KINDS = ("tear", "stress", "spark")


def endgame_live_cell_count(
    *,
    dimension: int,
    available_locked_cells: int,
    live_fraction: float,
) -> int:
    available = max(0, int(available_locked_cells))
    if available <= 0:
        return 0
    target_count = round(
        clamp_endgame_live_cell_fraction(live_fraction) * float(available)
    )
    return min(available, max(1, int(target_count)))


def _canonical_endgame_locked_cells(
    locked_cells: tuple[SnapshotCell, ...],
) -> tuple[SnapshotCell, ...]:
    return tuple(
        sorted(
            locked_cells,
            key=lambda cell: (
                tuple(int(axis) for axis in cell.source_coord),
                int(cell.color_id),
                -1 if cell.layer_index is None else int(cell.layer_index),
            ),
        )
    )


def _cell_selection_score(
    cell: SnapshotCell,
    *,
    seed: int,
) -> int:
    accumulator = _stable_seed_mix(1_469_598_103, int(seed))
    for axis in cell.source_coord:
        accumulator = _stable_seed_mix(accumulator, int(axis) + 431)
    accumulator = _stable_seed_mix(accumulator, int(cell.color_id) + 977)
    accumulator = _stable_seed_mix(
        accumulator,
        int(-1 if cell.layer_index is None else cell.layer_index) + 1597,
    )
    return accumulator


def _cell_artifact_score(
    cell: SnapshotCell,
    *,
    seed: int,
) -> int:
    return _stable_seed_mix(
        _cell_selection_score(cell, seed=seed ^ 0x5F3759DF),
        int(cell.color_id) + 2_021,
    )


def select_endgame_live_locked_cells(
    *,
    locked_cells: tuple[SnapshotCell, ...],
    dimension: int,
    seed: int,
    live_fraction: float,
) -> tuple[SnapshotCell, ...]:
    canonical_cells = _canonical_endgame_locked_cells(locked_cells)
    target_count = endgame_live_cell_count(
        dimension=dimension,
        available_locked_cells=len(canonical_cells),
        live_fraction=live_fraction,
    )
    if target_count >= len(canonical_cells):
        return canonical_cells
    ranked_cells = [
        (cell, _cell_selection_score(cell, seed=seed))
        for cell in canonical_cells
    ]
    ranked_cells.sort(key=lambda item: (item[1], item[0].source_coord, item[0].color_id))
    selected: list[tuple[SnapshotCell, int]] = [ranked_cells[0]]
    remaining = ranked_cells[1:]
    candidate_window = 16
    while remaining and len(selected) < target_count:
        best_index = 0
        best_score = -1.0
        window_limit = min(candidate_window, len(remaining))
        for index in range(window_limit):
            candidate, stable_score = remaining[index]
            min_distance_sq = min(
                sum(
                    float(candidate.source_coord[axis] - chosen.source_coord[axis]) ** 2
                    for axis in range(len(candidate.source_coord))
                )
                for chosen, _chosen_score in selected
            )
            composite_score = (min_distance_sq * 1_000_000.0) - float(stable_score)
            if composite_score > best_score:
                best_index = index
                best_score = composite_score
        selected.append(remaining.pop(best_index))
    return tuple(cell for cell, _score in selected)


def split_endgame_locked_cells(
    *,
    locked_cells: tuple[SnapshotCell, ...],
    dimension: int,
    seed: int,
    live_fraction: float,
) -> EndgameCellSplit:
    canonical_cells = _canonical_endgame_locked_cells(locked_cells)
    persistent_live_cells = select_endgame_live_locked_cells(
        locked_cells=canonical_cells,
        dimension=dimension,
        seed=seed,
        live_fraction=live_fraction,
    )
    persistent_lookup = set(persistent_live_cells)
    escaping_cells = tuple(
        cell for cell in canonical_cells if cell not in persistent_lookup
    )
    return EndgameCellSplit(
        persistent_live_cells=persistent_live_cells,
        escaping_cells=escaping_cells,
    )


def _select_shell_artifact_cells(
    *,
    escaping_cells: tuple[SnapshotCell, ...],
    dimension: int,
    seed: int,
) -> tuple[SnapshotCell, ...]:
    canonical_cells = _canonical_endgame_locked_cells(escaping_cells)
    target_count = min(
        len(canonical_cells),
        _ENDGAME_SHELL_ARTIFACT_CAPS.get(int(dimension), 32),
    )
    if target_count <= 0:
        return ()
    ranked_cells = [
        (cell, _cell_artifact_score(cell, seed=seed))
        for cell in canonical_cells
    ]
    ranked_cells.sort(key=lambda item: (item[1], item[0].source_coord, item[0].color_id))
    selected: list[tuple[SnapshotCell, int]] = [ranked_cells[0]]
    remaining = ranked_cells[1:]
    while remaining and len(selected) < target_count:
        best_index = 0
        best_score = -1.0
        for index, (candidate, stable_score) in enumerate(remaining[:18]):
            min_distance_sq = min(
                sum(
                    float(candidate.source_coord[axis] - chosen.source_coord[axis]) ** 2
                    for axis in range(len(candidate.source_coord))
                )
                for chosen, _chosen_score in selected
            )
            composite_score = (min_distance_sq * 1_000_000.0) - float(stable_score)
            if composite_score > best_score:
                best_index = index
                best_score = composite_score
        selected.append(remaining.pop(best_index))
    return tuple(cell for cell, _score in selected)


def build_endgame_shell_artifacts(
    snapshot: EndgameSnapshot,
    *,
    tuning: EndgameAnimationTuning,
) -> tuple[EndgameShellArtifact, ...]:
    selected_cells = _select_shell_artifact_cells(
        escaping_cells=snapshot.escaping_cells,
        dimension=snapshot.dimension,
        seed=snapshot.rng_seed,
    )
    artifacts: list[EndgameShellArtifact] = []
    for cell in selected_cells:
        score = _cell_artifact_score(cell, seed=snapshot.rng_seed)
        randomizer = random.Random(score)
        direction = _fragment_direction(
            randomizer=randomizer,
            origin=cell.position,
            board_center=snapshot.board_center,
            dimension=len(cell.position),
            outward_bias_strength=0.9,
            random_spread_strength=0.38,
            planar=snapshot.dimension == 2,
        )
        kind = _ENDGAME_SHELL_ARTIFACT_KINDS[
            score % len(_ENDGAME_SHELL_ARTIFACT_KINDS)
        ]
        birth_ms = float(
            tuning.capture_start_ms
            + randomizer.uniform(0.0, tuning.shell_artifact_birth_spread_ms)
        )
        lifetime_min = min(
            float(tuning.shell_artifact_lifetime_min_ms),
            float(tuning.shell_artifact_lifetime_max_ms),
        )
        lifetime_max = max(
            float(tuning.shell_artifact_lifetime_min_ms),
            float(tuning.shell_artifact_lifetime_max_ms),
        )
        lifetime_ms = min(
            randomizer.uniform(lifetime_min, lifetime_max),
            max(180.0, float(tuning.shatter_duration_ms - birth_ms - 40.0)),
        )
        artifacts.append(
            EndgameShellArtifact(
                source_coord=tuple(int(axis) for axis in cell.source_coord),
                start_position=tuple(float(value) for value in cell.position),
                direction=direction,
                speed=randomizer.uniform(2.2, 5.4),
                color_id=int(cell.color_id),
                birth_ms=birth_ms,
                lifetime_ms=float(lifetime_ms),
                kind=kind,
            )
        )
    return tuple(artifacts)


def _grid_break_direction_for_artifact(artifact: EndgameShellArtifact) -> VecN:
    direction = tuple(float(value) for value in artifact.direction)
    if len(direction) < 2:
        return (1.0,)
    candidate = (-direction[1], direction[0], *direction[2:])
    if _vec_len(candidate) <= 1e-6:
        candidate = (1.0, 0.0, *tuple(0.0 for _ in direction[2:]))
    return _normalize_or_default(candidate, _unit_axis(len(direction), 0))


def build_endgame_grid_break_marks(
    artifacts: tuple[EndgameShellArtifact, ...],
    *,
    dimension: int,
    tuning: EndgameAnimationTuning,
) -> tuple[EndgameGridBreakMark, ...]:
    cap = _ENDGAME_GRID_BREAK_CAPS.get(int(dimension), 12)
    if cap <= 0:
        return ()
    ranked_artifacts = sorted(
        artifacts,
        key=lambda artifact: (
            0 if artifact.kind in ("streak", "shard") else 1,
            -float(artifact.speed),
            artifact.source_coord,
            artifact.color_id,
        ),
    )[:cap]
    marks: list[EndgameGridBreakMark] = []
    for index, artifact in enumerate(ranked_artifacts):
        randomizer = random.Random(
            _stable_seed_mix(
                _cell_artifact_score(
                    SnapshotCell(
                        source_coord=artifact.source_coord,
                        position=artifact.start_position,
                        color_id=artifact.color_id,
                    ),
                    seed=int(artifact.speed * 10_000.0),
                ),
                index + 4_091,
            )
        )
        marks.append(
            EndgameGridBreakMark(
                source_coord=artifact.source_coord,
                center_position=_vec_add(
                    artifact.start_position,
                    _vec_mul(artifact.direction, randomizer.uniform(0.08, 0.24)),
                ),
                direction=_grid_break_direction_for_artifact(artifact),
                color_id=int(artifact.color_id),
                birth_ms=max(0.0, float(artifact.birth_ms - tuning.grid_break_birth_lead_ms)),
                lifetime_ms=min(float(artifact.lifetime_ms), float(tuning.grid_break_lifetime_ms)),
                length=randomizer.uniform(0.35, 0.72),
                kind=_ENDGAME_GRID_BREAK_KINDS[index % len(_ENDGAME_GRID_BREAK_KINDS)],
            )
        )
    return tuple(marks)


def create_snapshot(
    *,
    dimension: int,
    board_dims: tuple[int, ...],
    render_dims: tuple[int, int, int],
    locked_cells: tuple[SnapshotCell, ...],
    base_seed: int,
    render_context: EndgameRenderContext,
    preset_id: str | None = None,
    boundary_response: str | None = None,
    particle_collisions: str | None = None,
    mass_mode: str = "uniform",
    base_mass: float = 1.0,
    random_mass_min: float = 0.75,
    random_mass_max: float = 1.25,
    collision_elasticity: float = 1.0,
    diagnostics_mode: str = "off",
    trace_retention_ms: float = 2640.0,
    speed_preset: str = "normal",
    grid_mode: str = "full",
    shadow_mode: str = "off",
    trace_enabled: bool = False,
    w_movement_animation_style: str = "fade",
    endgame_live_cell_fraction: float = ENDGAME_LIVE_CELL_FRACTION_DEFAULT,
    relic_speed_scale: float = 1.0,
    shatter_speed_scale: float = 1.0,
    topology_edge_rules: tuple[tuple[str, str], ...] | None = None,
    explorer_topology_profile=None,
    explorer_transport=None,
    sound_enabled: bool = True,
    tuning: EndgameAnimationTuning | None = None,
) -> EndgameSnapshot:
    active_tuning = load_endgame_animation_tuning() if tuning is None else tuning
    position_dimension = 4 if int(dimension) >= 4 else 3
    board_center = tuple(
        ((float(board_dims[idx]) - 1.0) * 0.5) if idx < len(board_dims) else 0.0
        for idx in range(position_dimension)
    )
    render_center = (
        (float(render_dims[0]) - 1.0) * 0.5,
        (float(render_dims[1]) - 1.0) * 0.5,
        (float(render_dims[2]) - 1.0) * 0.5,
    )
    canonical_locked_cells = _canonical_endgame_locked_cells(tuple(locked_cells))
    cell_split = split_endgame_locked_cells(
        locked_cells=canonical_locked_cells,
        dimension=int(dimension),
        seed=int(base_seed),
        live_fraction=float(endgame_live_cell_fraction),
    )
    render_context = replace(
        render_context,
        w_movement_animation_style=str(w_movement_animation_style),
    )
    return EndgameSnapshot(
        dimension=int(dimension),
        board_dims=tuple(int(value) for value in board_dims),
        render_dims=tuple(int(value) for value in render_dims),
        board_center=board_center,
        render_center=render_center,
        locked_cells=canonical_locked_cells,
        persistent_live_cells=cell_split.persistent_live_cells,
        escaping_cells=cell_split.escaping_cells,
        rng_seed=derive_endgame_seed(
            base_seed=int(base_seed),
            board_dims=tuple(int(value) for value in board_dims),
            locked_cells=canonical_locked_cells,
            salt=int(active_tuning.seed_salt),
        ),
        render_context=render_context,
        preset_id=normalize_endgame_preset_id(
            preset_id,
            default=active_tuning.default_preset_id,
        ),
        boundary_response=normalize_endgame_boundary_response(
            boundary_response,
            default=active_tuning.default_boundary_response,
        ),
        particle_collisions=normalize_endgame_particle_collisions(
            particle_collisions,
            default=active_tuning.default_particle_collisions,
        ),
        mass_mode=str(mass_mode),
        base_mass=float(base_mass),
        random_mass_min=float(random_mass_min),
        random_mass_max=float(random_mass_max),
        collision_elasticity=float(collision_elasticity),
        diagnostics_mode=str(diagnostics_mode),
        trace_retention_ms=float(trace_retention_ms),
        speed_preset=str(speed_preset),
        grid_mode=str(grid_mode),
        shadow_mode=str(shadow_mode),
        trace_enabled=bool(trace_enabled),
        w_movement_animation_style=str(w_movement_animation_style),
        endgame_live_cell_fraction=clamp_endgame_live_cell_fraction(
            endgame_live_cell_fraction
        ),
        relic_speed_scale=max(0.05, float(relic_speed_scale)),
        shatter_speed_scale=max(0.05, float(shatter_speed_scale)),
        topology=ExplosionTopologyInput(
            board_dims=tuple(int(value) for value in board_dims),
            topology_edge_rules=(
                None
                if topology_edge_rules is None
                else tuple(
                    (str(axis_rules[0]), str(axis_rules[1]))
                    for axis_rules in topology_edge_rules
                )
            ),
            explorer_topology_profile=explorer_topology_profile,
            explorer_transport=explorer_transport,
        ),
        sound_enabled=bool(sound_enabled),
    )


def _vec_add(a: VecN, b: VecN) -> VecN:
    return tuple(left + right for left, right in zip(a, b))


def _vec_sub(a: VecN, b: VecN) -> VecN:
    return tuple(left - right for left, right in zip(a, b))


def _vec_mul(a: VecN, scalar: float) -> VecN:
    return tuple(component * scalar for component in a)


def _vec_dot(a: VecN, b: VecN) -> float:
    return sum(left * right for left, right in zip(a, b))


def _vec_lerp(a: VecN, b: VecN, progress: float) -> VecN:
    return tuple(
        left + ((right - left) * progress) for left, right in zip(a, b)
    )


def _vec_len(a: VecN) -> float:
    return math.sqrt(sum(component * component for component in a))


def _normalize_or_default(a: VecN, default: VecN) -> VecN:
    length = _vec_len(a)
    if length <= 1e-9:
        return default
    return tuple(component / length for component in a)


def _pad_vec3(value: VecN) -> Vec3:
    padded = tuple(value) + (0.0, 0.0, 0.0)
    return (float(padded[0]), float(padded[1]), float(padded[2]))


def _zero_vec(dimension: int) -> VecN:
    return tuple(0.0 for _ in range(max(0, int(dimension))))


def _unit_axis(dimension: int, axis_index: int, *, sign: float = 1.0) -> VecN:
    return tuple(
        float(sign if idx == axis_index else 0.0) for idx in range(max(0, dimension))
    )


def _random_signed(randomizer: random.Random) -> float:
    return -1.0 if randomizer.random() < 0.5 else 1.0


def _random_unit_vector(
    randomizer: random.Random,
    *,
    dimension: int,
    planar: bool = False,
) -> VecN:
    values = [
        randomizer.uniform(-1.0, 1.0) for _ in range(max(0, int(dimension)))
    ]
    if planar and len(values) >= 3:
        for idx in range(2, len(values)):
            values[idx] = 0.0
    vector = tuple(values)
    default = _unit_axis(max(1, int(dimension)), 0)
    if planar and len(default) >= 3:
        default = tuple(default[idx] if idx < 2 else 0.0 for idx in range(len(default)))
    return _normalize_or_default(vector, default)


def _fragment_direction(
    *,
    randomizer: random.Random,
    origin: VecN,
    board_center: VecN,
    dimension: int,
    outward_bias_strength: float,
    random_spread_strength: float,
    planar: bool = False,
) -> VecN:
    default_axis = 1 if dimension > 1 else 0
    outward = _normalize_or_default(
        _vec_sub(origin, board_center),
        _unit_axis(dimension, default_axis, sign=-1.0),
    )
    random_vec = _random_unit_vector(
        randomizer,
        dimension=dimension,
        planar=planar,
    )
    return _normalize_or_default(
        _vec_add(
            _vec_mul(outward, float(outward_bias_strength)),
            _vec_mul(random_vec, float(random_spread_strength)),
        ),
        outward,
    )


def _smoothstep01(value: float) -> float:
    clamped = max(0.0, min(1.0, float(value)))
    return clamped * clamped * (3.0 - (2.0 * clamped))


def _wrap_phase_radians(value: float) -> float:
    return float(value % _TAU)


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


def _field_basis_vectors(
    *,
    randomizer: random.Random,
    direction: VecN,
) -> tuple[VecN, ...]:
    dimension = len(direction)
    if dimension <= 0:
        return tuple()
    basis: list[VecN] = []
    candidates: list[VecN] = [
        _normalize_or_default(direction, _unit_axis(dimension, 0)),
    ]
    candidates.extend(
        _random_unit_vector(randomizer, dimension=dimension)
        for _ in range(dimension * 2)
    )
    candidates.extend(_unit_axis(dimension, axis_index) for axis_index in range(dimension))
    for candidate in candidates:
        orthogonal = candidate
        for existing in basis:
            orthogonal = _vec_sub(
                orthogonal,
                _vec_mul(existing, _vec_dot(orthogonal, existing)),
            )
        if _vec_len(orthogonal) <= 1e-6:
            continue
        basis.append(
            _normalize_or_default(
                orthogonal,
                _unit_axis(dimension, len(basis) % dimension),
            )
        )
        if len(basis) >= dimension:
            break
    while len(basis) < dimension:
        basis.append(_unit_axis(dimension, len(basis)))
    return tuple(basis)


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
    direction: VecN,
    tuning: EndgameAnimationTuning,
) -> VecN:
    dimension = len(cell.position)
    bias_toward_source = _vec_lerp(snapshot.board_center, cell.position, 0.42)
    outward = _vec_mul(
        direction,
        randomizer.uniform(0.15, 0.55) * tuning.anchor_spread_radius,
    )
    tangent = _vec_mul(
        _random_unit_vector(randomizer, dimension=dimension),
        randomizer.uniform(0.0, 0.35) * tuning.anchor_spread_radius,
    )
    extents = _field_half_extents(
        snapshot,
        tuning=tuning,
        preset=resolve_endgame_preset_config(snapshot.preset_id, tuning=tuning),
        dimension=dimension,
    )
    return _wrap_point_in_box(
        _vec_add(bias_toward_source, _vec_add(outward, tangent)),
        center=snapshot.board_center,
        extents=extents,
    )


def _field_seconds(
    *,
    elapsed_ms: float,
    tuning: EndgameAnimationTuning,
    speed_scale: float,
) -> float:
    return max(
        0.0,
        float(elapsed_ms - tuning.capture_start_ms) / 1000.0,
    ) * max(0.05, float(speed_scale))


def _field_half_extents(
    snapshot: EndgameSnapshot,
    *,
    tuning: EndgameAnimationTuning,
    preset: EndgamePresetConfig,
    dimension: int | None = None,
) -> VecN:
    target_dimension = (
        len(snapshot.board_center) if dimension is None else max(1, int(dimension))
    )
    scale = max(0.2, float(tuning.field_extent_multiplier * preset.extent_scale))
    extents: list[float] = []
    for axis_index in range(target_dimension):
        if axis_index >= len(snapshot.board_dims):
            extents.append(0.0)
            continue
        extents.append(
            max(
                1.0,
                ((float(snapshot.board_dims[axis_index]) - 1.0) * 0.5 * scale)
                + tuning.wrap_margin,
            )
        )
    return tuple(extents)


def _wrap_local_axis(value: float, extent: float) -> float:
    if extent <= 0.0:
        return 0.0
    span = extent * 2.0
    wrapped = ((value + extent) % span) - extent
    return float(wrapped)


def _wrap_point_in_box(point: VecN, *, center: VecN, extents: VecN) -> VecN:
    local = _vec_sub(point, center)
    return _vec_add(
        center,
        tuple(
            0.0 if extent <= 0.0 else _wrap_local_axis(local[idx], extent)
            for idx, extent in enumerate(extents)
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
    point: VecN, *, center: VecN, extents: VecN
) -> tuple[VecN, float]:
    local = _vec_sub(point, center)
    reflected: list[float] = []
    sign = 1.0
    for axis_index, extent in enumerate(extents):
        value, axis_sign = _reflect_local_axis(local[axis_index], extent)
        reflected.append(value)
        sign *= axis_sign
    return _vec_add(center, tuple(reflected)), float(sign)


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
    initial_position: VecN,
    velocity: VecN,
    acceleration: VecN,
    jitter_offset: VecN,
    detach_start_ms: float,
    elapsed_ms: float,
    drag_per_second: float,
    speed_scale: float = 1.0,
) -> VecN:
    if elapsed_ms <= detach_start_ms:
        crack_denominator = max(1.0, float(detach_start_ms))
        crack_progress = max(0.0, min(1.0, float(elapsed_ms / crack_denominator)))
        return _vec_add(initial_position, _vec_mul(jitter_offset, crack_progress))
    travel_seconds = (
        max(0.0, float(elapsed_ms - detach_start_ms) / 1000.0)
        * max(0.05, float(speed_scale))
    )
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
    speed_scale: float = 1.0,
) -> Vec3:
    if elapsed_ms <= detach_start_ms:
        return (0.0, 0.0, 0.0)
    travel_seconds = (
        max(0.0, float(elapsed_ms - detach_start_ms) / 1000.0)
        * max(0.05, float(speed_scale))
    )
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
        board_center=snapshot.render_center,
        dimension=3,
        outward_bias_strength=tuning.outward_bias_strength,
        random_spread_strength=tuning.random_spread_strength,
        planar=planar,
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
            _pad_vec3(_random_unit_vector(randomizer, dimension=3, planar=planar)),
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
            phase=TERMINAL_PHASE_GAME_OVER_COMPLETE,
            elapsed_ms=float(active_tuning.prompt_ready_ms),
        )
    randomizer = random.Random(snapshot.rng_seed)
    planar = snapshot.dimension == 2

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
    escaping_artifacts = build_endgame_shell_artifacts(
        snapshot,
        tuning=active_tuning,
    )
    grid_break_marks = build_endgame_grid_break_marks(
        escaping_artifacts,
        dimension=snapshot.dimension,
        tuning=active_tuning,
    )
    explosion_controller = build_locked_cell_explosion(
        StandaloneExplosionConfig(
            dimension=int(snapshot.dimension),
            topology=snapshot.topology,
            occupied_cells=tuple(
                ExplosionSeedCell(
                    source_coord=tuple(int(value) for value in cell.source_coord),
                    color_id=int(cell.color_id),
                )
                for cell in snapshot.persistent_live_cells
            ),
            random_seed=int(snapshot.rng_seed),
            boundary_response=str(snapshot.boundary_response),
            particle_collisions=str(snapshot.particle_collisions),
            mass_mode=str(snapshot.mass_mode),
            base_mass=float(snapshot.base_mass),
            random_mass_min=float(snapshot.random_mass_min),
            random_mass_max=float(snapshot.random_mass_max),
            collision_elasticity=float(snapshot.collision_elasticity),
            diagnostics_mode=str(snapshot.diagnostics_mode),
            speed_preset=str(snapshot.speed_preset),
            sound_enabled=bool(snapshot.sound_enabled),
            launch_speed_scale=float(snapshot.shatter_speed_scale),
            time_scale=float(snapshot.relic_speed_scale),
            trace_retention_ms=float(snapshot.trace_retention_ms),
        )
    )
    return EndgameAnimationState(
        snapshot=snapshot,
        tuning=active_tuning,
        shatter=EndgameShatterState(shell_fragments=shell_fragments),
        explosion_controller=explosion_controller,
        escaping_artifacts=escaping_artifacts,
        grid_break_marks=grid_break_marks,
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


def transform_shell_artifact(
    artifact: EndgameShellArtifact,
    *,
    elapsed_ms: float,
) -> tuple[VecN, VecN, float]:
    if elapsed_ms < artifact.birth_ms:
        return artifact.start_position, artifact.start_position, 0.0
    age_ms = float(elapsed_ms - artifact.birth_ms)
    if age_ms >= artifact.lifetime_ms:
        return artifact.start_position, artifact.start_position, 0.0
    age_seconds = age_ms / 1000.0
    head = _vec_add(
        artifact.start_position,
        _vec_mul(artifact.direction, artifact.speed * age_seconds),
    )
    length_scale = {"streak": 0.5, "shard": 0.32, "spark": 0.18}.get(
        artifact.kind,
        0.28,
    )
    tail = _vec_sub(head, _vec_mul(artifact.direction, length_scale))
    fade_start = artifact.lifetime_ms * 0.45
    alpha = 1.0 if age_ms <= fade_start else 1.0 - (
        (age_ms - fade_start) / max(1.0, artifact.lifetime_ms - fade_start)
    )
    return tail, head, max(0.0, min(1.0, alpha))


def transform_grid_break_mark(
    mark: EndgameGridBreakMark,
    *,
    elapsed_ms: float,
) -> tuple[VecN, VecN, float]:
    if elapsed_ms < mark.birth_ms:
        return mark.center_position, mark.center_position, 0.0
    age_ms = float(elapsed_ms - mark.birth_ms)
    if age_ms >= mark.lifetime_ms:
        return mark.center_position, mark.center_position, 0.0
    progress = max(0.0, min(1.0, age_ms / max(1.0, mark.lifetime_ms)))
    length = float(mark.length) * (0.35 + (0.65 * _smoothstep01(progress)))
    half_vector = _vec_mul(mark.direction, length * 0.5)
    alpha = 1.0 - _smoothstep01(max(0.0, (progress - 0.45) / 0.55))
    return (
        _vec_sub(mark.center_position, half_vector),
        _vec_add(mark.center_position, half_vector),
        max(0.0, min(1.0, alpha)),
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
    "EndgameAnimationState",
    "EndgameAnimationTuning",
    "EndgameCellSplit",
    "EndgameGridBreakMark",
    "EndgamePresetConfig",
    "EndgameRenderContext",
    "EndgameShatterState",
    "EndgameShellArtifact",
    "EndgameSnapshot",
    "ShellFragment",
    "SnapshotCell",
    "TERMINAL_PHASE_ENDGAME_RELIC_FIELD",
    "TERMINAL_PHASE_ENDGAME_SHATTER",
    "TERMINAL_PHASE_GAME_OVER_ANIMATING",
    "TERMINAL_PHASE_GAME_OVER_COMPLETE",
    "TERMINAL_PHASE_PLAYING",
    "build_endgame_animation_state",
    "build_endgame_grid_break_marks",
    "build_endgame_shell_artifacts",
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
    "resolve_endgame_preset_config",
    "rotate_point",
    "split_endgame_locked_cells",
    "transform_for_shell_fragment",
    "transform_grid_break_mark",
    "transform_shell_artifact",
    "transform_shell_geometry",
]
