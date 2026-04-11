from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import math
import random

from tet4d.engine.runtime.project_config import constants_payload

Vec3 = tuple[float, float, float]

TERMINAL_PHASE_PLAYING = "playing"
TERMINAL_PHASE_GAME_OVER_ANIMATING = "game_over_animating"
TERMINAL_PHASE_GAME_OVER_COMPLETE = "game_over_complete"


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


@dataclass(frozen=True)
class EndgameAnimationTuning:
    enabled: bool
    total_duration_ms: float
    crack_onset_duration_ms: float
    release_duration_ms: float
    fade_duration_ms: float
    shell_fragment_speed_min: float
    shell_fragment_speed_max: float
    cell_fragment_speed_min: float
    cell_fragment_speed_max: float
    angular_velocity_deg_min: float
    angular_velocity_deg_max: float
    outward_bias_strength: float
    random_spread_strength: float
    drag_per_second: float
    gravity_per_second: float
    seed_salt: int

    @property
    def fade_start_ms(self) -> float:
        return max(
            float(self.crack_onset_duration_ms + self.release_duration_ms),
            float(self.total_duration_ms - self.fade_duration_ms),
        )


def load_endgame_animation_tuning() -> EndgameAnimationTuning:
    animation_payload = constants_payload().get("animation", {})
    payload = animation_payload.get("endgame", {})
    if not isinstance(payload, dict):
        payload = {}
    return EndgameAnimationTuning(
        enabled=_coerce_bool(payload.get("enabled"), default=True),
        total_duration_ms=_clamp_float(
            payload.get("total_duration_ms"),
            default=1800.0,
            minimum=1.0,
        ),
        crack_onset_duration_ms=_clamp_float(
            payload.get("crack_onset_duration_ms"),
            default=220.0,
            minimum=0.0,
        ),
        release_duration_ms=_clamp_float(
            payload.get("release_duration_ms"),
            default=420.0,
            minimum=0.0,
        ),
        fade_duration_ms=_clamp_float(
            payload.get("fade_duration_ms"),
            default=780.0,
            minimum=0.0,
        ),
        shell_fragment_speed_min=_clamp_float(
            payload.get("shell_fragment_speed_min"),
            default=1.4,
            minimum=0.0,
        ),
        shell_fragment_speed_max=_clamp_float(
            payload.get("shell_fragment_speed_max"),
            default=4.6,
            minimum=0.0,
        ),
        cell_fragment_speed_min=_clamp_float(
            payload.get("cell_fragment_speed_min"),
            default=2.8,
            minimum=0.0,
        ),
        cell_fragment_speed_max=_clamp_float(
            payload.get("cell_fragment_speed_max"),
            default=6.6,
            minimum=0.0,
        ),
        angular_velocity_deg_min=_clamp_float(
            payload.get("angular_velocity_deg_min"),
            default=90.0,
            minimum=0.0,
        ),
        angular_velocity_deg_max=_clamp_float(
            payload.get("angular_velocity_deg_max"),
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
        drag_per_second=_clamp_float(
            payload.get("drag_per_second"),
            default=0.82,
            minimum=0.0,
        ),
        gravity_per_second=_clamp_float(
            payload.get("gravity_per_second"),
            default=0.48,
            minimum=0.0,
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


@dataclass(frozen=True)
class CellFragment:
    source_coord: tuple[int, ...]
    base_geometry: str
    initial_position: Vec3
    velocity: Vec3
    acceleration: Vec3
    angular_velocity_deg: Vec3
    detach_start_ms: float
    fade_start_ms: float
    lifetime_ms: float
    color_id: int
    layer_index: int | None = None
    jitter_offset: Vec3 = (0.0, 0.0, 0.0)


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


@dataclass
class EndgameAnimationState:
    snapshot: EndgameSnapshot
    tuning: EndgameAnimationTuning
    cell_fragments: tuple[CellFragment, ...]
    shell_fragments: tuple[ShellFragment, ...]
    phase: str = TERMINAL_PHASE_GAME_OVER_ANIMATING
    elapsed_ms: float = 0.0

    @property
    def frozen_render_active(self) -> bool:
        return self.phase != TERMINAL_PHASE_PLAYING

    @property
    def animating(self) -> bool:
        return self.phase == TERMINAL_PHASE_GAME_OVER_ANIMATING

    def step(self, dt_ms: float) -> None:
        if self.phase != TERMINAL_PHASE_GAME_OVER_ANIMATING:
            return
        self.elapsed_ms = float(self.elapsed_ms + max(0.0, dt_ms))


def endgame_prompt_ready(animation: EndgameAnimationState | None) -> bool:
    if animation is None:
        return False
    return float(animation.elapsed_ms) >= float(animation.tuning.crack_onset_duration_ms)


def endgame_sfx_events_between(
    *,
    previous_elapsed_ms: float,
    current_elapsed_ms: float,
    tuning: EndgameAnimationTuning,
) -> tuple[str, ...]:
    if current_elapsed_ms <= previous_elapsed_ms:
        return tuple()
    crack_time_ms = float(tuning.crack_onset_duration_ms)
    release_end_ms = float(
        tuning.crack_onset_duration_ms + tuning.release_duration_ms
    )
    mid_release_ms = float((crack_time_ms + release_end_ms) * 0.5)
    events: list[str] = []
    for threshold_ms, event_name in (
        (crack_time_ms, "endgame_crack"),
        (mid_release_ms, "endgame_pop"),
        (release_end_ms, "endgame_boom"),
    ):
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
    tuning: EndgameAnimationTuning | None = None,
) -> EndgameSnapshot:
    active_tuning = (
        load_endgame_animation_tuning() if tuning is None else tuning
    )
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
    )


def _vec_add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _vec_sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vec_mul(a: Vec3, scalar: float) -> Vec3:
    return (a[0] * scalar, a[1] * scalar, a[2] * scalar)


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
        return (0.0, 0.0, randomizer.uniform(minimum, maximum) * _random_signed(randomizer))
    return (
        randomizer.uniform(minimum, maximum) * _random_signed(randomizer),
        randomizer.uniform(minimum, maximum) * _random_signed(randomizer),
        randomizer.uniform(minimum, maximum) * _random_signed(randomizer),
    )


def _cell_fragment_from_snapshot_cell(
    cell: SnapshotCell,
    *,
    randomizer: random.Random,
    snapshot: EndgameSnapshot,
    tuning: EndgameAnimationTuning,
    planar: bool,
) -> CellFragment:
    direction = _fragment_direction(
        randomizer=randomizer,
        origin=cell.position,
        board_center=snapshot.board_center,
        planar=planar,
        outward_bias_strength=tuning.outward_bias_strength,
        random_spread_strength=tuning.random_spread_strength,
    )
    speed = randomizer.uniform(
        tuning.cell_fragment_speed_min,
        tuning.cell_fragment_speed_max,
    )
    detach_start_ms = tuning.crack_onset_duration_ms + (
        tuning.release_duration_ms * randomizer.random()
    )
    jitter_scale = (tuning.crack_onset_duration_ms / 1000.0) * speed
    return CellFragment(
        source_coord=cell.source_coord,
        base_geometry="cell",
        initial_position=cell.position,
        velocity=_vec_mul(direction, speed),
        acceleration=(0.0, tuning.gravity_per_second, 0.0),
        angular_velocity_deg=_random_angular_velocity(
            randomizer,
            planar=planar,
            minimum=tuning.angular_velocity_deg_min,
            maximum=tuning.angular_velocity_deg_max,
        ),
        detach_start_ms=detach_start_ms,
        fade_start_ms=tuning.fade_start_ms,
        lifetime_ms=tuning.total_duration_ms,
        color_id=cell.color_id,
        layer_index=cell.layer_index,
        jitter_offset=_vec_mul(
            _random_unit_vec3(randomizer, planar=planar),
            jitter_scale,
        ),
    )


def _shell_segment_center(
    segment: tuple[Vec3, Vec3],
) -> Vec3:
    start, end = segment
    return (
        (start[0] + end[0]) * 0.5,
        (start[1] + end[1]) * 0.5,
        (start[2] + end[2]) * 0.5,
    )


def _shell_segment_local_points(
    segment: tuple[Vec3, Vec3],
) -> tuple[Vec3, Vec3]:
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
        acceleration=(0.0, tuning.gravity_per_second, 0.0),
        angular_velocity_deg=_random_angular_velocity(
            randomizer,
            planar=planar,
            minimum=tuning.angular_velocity_deg_min,
            maximum=tuning.angular_velocity_deg_max,
        ),
        detach_start_ms=detach_start_ms,
        fade_start_ms=tuning.fade_start_ms,
        lifetime_ms=tuning.total_duration_ms,
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
        ("box_edge", layer_index, (corners[a], corners[b]))
        for a, b in edge_pairs
    )


def build_endgame_animation_state(
    snapshot: EndgameSnapshot,
    *,
    tuning: EndgameAnimationTuning | None = None,
) -> EndgameAnimationState:
    active_tuning = (
        load_endgame_animation_tuning() if tuning is None else tuning
    )
    if not active_tuning.enabled:
        return EndgameAnimationState(
            snapshot=snapshot,
            tuning=active_tuning,
            cell_fragments=tuple(),
            shell_fragments=tuple(),
            phase=TERMINAL_PHASE_GAME_OVER_COMPLETE,
            elapsed_ms=float(active_tuning.total_duration_ms),
        )

    randomizer = random.Random(snapshot.rng_seed)
    planar = snapshot.dimension == 2
    cell_fragments = tuple(
        _cell_fragment_from_snapshot_cell(
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
        cell_fragments=cell_fragments,
        shell_fragments=shell_fragments,
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


def fragment_alpha(*, elapsed_ms: float, fade_start_ms: float, lifetime_ms: float) -> float:
    _ = elapsed_ms, fade_start_ms, lifetime_ms
    return 1.0


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
    if elapsed_ms <= detach_start_ms:
        crack_denominator = max(1.0, float(detach_start_ms))
        crack_progress = max(0.0, min(1.0, float(elapsed_ms / crack_denominator)))
        return _vec_add(initial_position, _vec_mul(jitter_offset, crack_progress))
    travel_seconds = max(0.0, float(elapsed_ms - detach_start_ms) / 1000.0)
    drag_scale = 1.0 / (1.0 + (float(drag_per_second) * travel_seconds))
    displacement = _vec_mul(velocity, travel_seconds * drag_scale)
    acceleration_term = _vec_mul(acceleration, 0.5 * travel_seconds * travel_seconds)
    return _vec_add(initial_position, _vec_add(displacement, acceleration_term))


def fragment_rotation_deg(
    *,
    angular_velocity_deg: Vec3,
    detach_start_ms: float,
    elapsed_ms: float,
) -> Vec3:
    if elapsed_ms <= detach_start_ms:
        return (0.0, 0.0, 0.0)
    travel_seconds = max(0.0, float(elapsed_ms - detach_start_ms) / 1000.0)
    return _vec_mul(angular_velocity_deg, travel_seconds)


def transform_for_cell_fragment(
    fragment: CellFragment,
    *,
    elapsed_ms: float,
    drag_per_second: float,
) -> tuple[Vec3, Vec3, float]:
    return (
        fragment_translation(
            initial_position=fragment.initial_position,
            velocity=fragment.velocity,
            acceleration=fragment.acceleration,
            jitter_offset=fragment.jitter_offset,
            detach_start_ms=fragment.detach_start_ms,
            elapsed_ms=elapsed_ms,
            drag_per_second=drag_per_second,
        ),
        fragment_rotation_deg(
            angular_velocity_deg=fragment.angular_velocity_deg,
            detach_start_ms=fragment.detach_start_ms,
            elapsed_ms=elapsed_ms,
        ),
        fragment_alpha(
            elapsed_ms=elapsed_ms,
            fade_start_ms=fragment.fade_start_ms,
            lifetime_ms=fragment.lifetime_ms,
        ),
    )


def transform_for_shell_fragment(
    fragment: ShellFragment,
    *,
    elapsed_ms: float,
    drag_per_second: float,
) -> tuple[Vec3, Vec3, float]:
    return (
        fragment_translation(
            initial_position=fragment.initial_position,
            velocity=fragment.velocity,
            acceleration=fragment.acceleration,
            jitter_offset=fragment.jitter_offset,
            detach_start_ms=fragment.detach_start_ms,
            elapsed_ms=elapsed_ms,
            drag_per_second=drag_per_second,
        ),
        fragment_rotation_deg(
            angular_velocity_deg=fragment.angular_velocity_deg,
            detach_start_ms=fragment.detach_start_ms,
            elapsed_ms=elapsed_ms,
        ),
        fragment_alpha(
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
    "EndgameAnimationState",
    "EndgameAnimationTuning",
    "EndgameRenderContext",
    "EndgameSnapshot",
    "ShellFragment",
    "SnapshotCell",
    "TERMINAL_PHASE_GAME_OVER_ANIMATING",
    "TERMINAL_PHASE_GAME_OVER_COMPLETE",
    "TERMINAL_PHASE_PLAYING",
    "build_endgame_animation_state",
    "create_snapshot",
    "derive_endgame_seed",
    "ensure_endgame_animation",
    "fragment_alpha",
    "fragment_rotation_deg",
    "fragment_translation",
    "load_endgame_animation_tuning",
    "rotate_point",
    "transform_for_cell_fragment",
    "transform_for_shell_fragment",
    "transform_shell_geometry",
]
