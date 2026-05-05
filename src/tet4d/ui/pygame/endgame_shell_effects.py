from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any

from tet4d.ui.pygame.render.board_boundary import board_boundary_coordinate

VecN = tuple[float, ...]
CellKey = tuple[tuple[int, ...], VecN, int, int]


@dataclass(frozen=True)
class EndgameBoundaryImpact:
    source_coord: tuple[int, ...]
    start_position: VecN
    impact_position: VecN
    outward_direction: VecN
    color_id: int
    axis: int
    side: int
    force: float
    birth_ms: float


@dataclass(frozen=True)
class EndgameShellTimeline:
    hold_ms: float
    rupture_ms: float
    impact_window_ms: float
    shard_drift_ms: float
    residue_start_ms: float


@dataclass(frozen=True)
class EndgameEscapeEvent:
    event_index: int
    source_coord: tuple[int, ...]
    source_position: VecN
    color_id: int
    source_layer_index: int | None
    impact_position: VecN
    impact_axis: int
    impact_side: int
    outward_direction: VecN
    force: float
    rupture_delay_ms: float
    impact_ms: float
    proxy_lifetime_ms: float
    shard_indices: tuple[int, ...]


@dataclass(frozen=True)
class EndgameBoardShard:
    source_impact_index: int
    event_index: int
    source_coord: tuple[int, ...]
    start_position: VecN
    direction: VecN
    speed: float
    spin_deg_per_s: float
    size: float
    birth_ms: float
    lifetime_ms: float
    alpha: float
    color_hint: tuple[int, int, int] | None


@dataclass(frozen=True)
class EndgameImpactDrawState:
    position: VecN
    alpha: float
    radius: float
    streak_width: float


@dataclass(frozen=True)
class EndgameShardDrawState:
    position: VecN
    alpha: float
    rotation_deg: float
    size: float


@dataclass(frozen=True)
class EscapeProxyState:
    event_index: int
    source_coord: tuple[int, ...]
    render_position: VecN
    color_id: int
    alpha: float
    scale: float
    rotation_deg: float
    progress: float
    layer_index: int | None


@dataclass(frozen=True)
class EscapeStreakState:
    event_index: int
    source_coord: tuple[int, ...]
    tail_position: VecN
    head_position: VecN
    color_id: int
    alpha: float
    width_scale: float
    layer_index: int | None


@dataclass(frozen=True)
class ImpactFlashState:
    event_index: int
    source_coord: tuple[int, ...]
    position: VecN
    color_id: int
    alpha: float
    radius_scale: float
    force: float
    layer_index: int | None


@dataclass(frozen=True)
class ResidueCrackState:
    event_index: int
    source_coord: tuple[int, ...]
    position: VecN
    direction: VecN
    alpha: float
    length_scale: float
    layer_index: int | None


@dataclass(frozen=True)
class EscapeEventFrame:
    event_index: int
    source_coord: tuple[int, ...]
    source_cell_visible: bool
    proxy: EscapeProxyState | None
    streak: EscapeStreakState | None
    impact_flash: ImpactFlashState | None
    shards: tuple[EndgameShardDrawState, ...]
    residue: tuple[ResidueCrackState, ...]


@dataclass(frozen=True)
class EndgameShellSoundEvent:
    event_key: str
    sound_id: str
    trigger_ms: float
    volume: float
    pan_hint: float | None
    pitch: float


def _value(tuning: Any, name: str, default: float) -> float:
    value = tuning.get(name, default) if isinstance(tuning, dict) else getattr(tuning, name, default)
    return float(value)


def _mix(acc: int, value: int) -> int:
    return (((int(acc) ^ int(value)) * 16_777_619) & 0xFFFFFFFF) or 1


def _score(coord: tuple[int, ...], color_id: int, layer: int, seed: int) -> int:
    value = _mix(1_469_598_103, seed)
    for axis_value in coord:
        value = _mix(value, axis_value + 431)
    return _mix(_mix(value, color_id + 977), layer + 1597)


def _norm(vector: VecN, fallback: VecN) -> VecN:
    length = math.sqrt(sum(component * component for component in vector))
    return fallback if length <= 1e-9 else tuple(component / length for component in vector)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _lerp_vec(start: VecN, end: VecN, t: float) -> VecN:
    progress = _clamp01(t)
    return tuple(float(a) + ((float(b) - float(a)) * progress) for a, b in zip(start, end))


def _smoothstep(value: float) -> float:
    progress = _clamp01(value)
    return progress * progress * (3.0 - (2.0 * progress))


def _ease_in_cubic(value: float) -> float:
    progress = _clamp01(value)
    return progress * progress * progress


def _cell_parts(cell: Any, dimension: int) -> CellKey:
    coord = tuple(int(value) for value in getattr(cell, "source_coord"))[:dimension]
    position = tuple(float(value) for value in getattr(cell, "position", coord))[:dimension]
    layer = getattr(cell, "layer_index", None)
    return coord, position, int(getattr(cell, "color_id")), -1 if layer is None else int(layer)


def boundary_impact_cap_for_dimension(dimension: int, tuning: Any) -> int:
    return max(0, int(_value(tuning, f"boundary_impact_cap_{int(dimension)}d", 24.0)))


def board_shard_cap_for_dimension(dimension: int, tuning: Any) -> int:
    return max(0, int(_value(tuning, f"board_shard_cap_{int(dimension)}d", 32.0)))


def load_shell_timeline(tuning: Any) -> EndgameShellTimeline:
    hold_ms = _value(tuning, "shell_preview_hold_ms", _value(tuning, "shell_event_hold_ms", 1150.0))
    rupture_ms = _value(tuning, "shell_preview_rupture_ms", _value(tuning, "shell_event_rupture_ms", 1250.0))
    impact_window_ms = _value(tuning, "shell_event_impact_window_ms", 420.0)
    shard_drift_ms = _value(tuning, "shell_preview_shard_drift_ms", _value(tuning, "shell_event_shard_drift_ms", 2400.0))
    return EndgameShellTimeline(
        hold_ms=hold_ms,
        rupture_ms=rupture_ms,
        impact_window_ms=impact_window_ms,
        shard_drift_ms=shard_drift_ms,
        residue_start_ms=hold_ms + rupture_ms,
    )


def _boundary_bias(coord: tuple[int, ...], board_dims: tuple[int, ...]) -> float:
    edge_distance = min(
        (min(float(value), float(size - 1 - value)) for value, size in zip(coord, board_dims)),
        default=0.0,
    )
    return 1.0 / (1.0 + max(0.0, edge_distance))


def _select_cells(cells: tuple[CellKey, ...], board_dims: tuple[int, ...], seed: int, cap: int) -> tuple[CellKey, ...]:
    ranked = [
        (cell, float(_score(cell[0], cell[2], cell[3], seed)) - (_boundary_bias(cell[0], board_dims) * 120_000_000.0))
        for cell in sorted(cells, key=lambda item: (item[0], item[2], item[3]))
    ]
    ranked.sort(key=lambda item: (item[1], item[0][0], item[0][2], item[0][3]))
    chosen, remaining = ([ranked[0]] if ranked and cap > 0 else []), ranked[1:]
    while remaining and len(chosen) < cap:
        best = max(
            range(min(18, len(remaining))),
            key=lambda i: (
                min(sum(float(a - b) ** 2 for a, b in zip(remaining[i][0][0], item[0][0])) for item in chosen)
                * 1_000_000.0
            )
            - remaining[i][1],
        )
        chosen.append(remaining.pop(best))
    return tuple(cell for cell, _rank in chosen)


def _impact_for_cell(cell: CellKey, board_dims: tuple[int, ...], seed: int) -> EndgameBoundaryImpact:
    coord, start, color_id, layer = cell
    center = tuple((float(size) - 1.0) * 0.5 for size in board_dims)
    fallback_axis = abs(_score(coord, color_id, layer, seed)) % len(board_dims)
    fallback_side = -1 if coord[fallback_axis] <= center[fallback_axis] else 1
    rng = random.Random(_score(coord, color_id, layer, seed ^ 0x45D9F3B))
    jitter = tuple(rng.uniform(-0.18, 0.18) for _ in board_dims)
    fallback = tuple(float(fallback_side if axis == fallback_axis else 0.0) for axis in range(len(board_dims)))
    direction = _norm(tuple((start[axis] - center[axis]) + jitter[axis] for axis in range(len(board_dims))), fallback)
    hits = []
    for axis, component in enumerate(direction):
        if abs(component) > 1e-9:
            side = 1 if component > 0.0 else -1
            plane = board_boundary_coordinate(dims=board_dims, axis=axis, side="+" if side > 0 else "-")
            t = (plane - start[axis]) / component
            if t >= 0.0:
                hits.append((t, axis, side))
    t, axis, side = min(hits) if hits else (0.0, fallback_axis, fallback_side)
    impact = tuple(start[idx] + direction[idx] * t for idx in range(len(board_dims)))
    impact = tuple(
        board_boundary_coordinate(dims=board_dims, axis=idx, side="+" if side > 0 else "-")
        if idx == axis
        else max(-0.5, min(float(board_dims[idx]) - 0.5, value))
        for idx, value in enumerate(impact)
    )
    return EndgameBoundaryImpact(coord, start, impact, direction, color_id, axis, side, rng.uniform(0.65, 1.0), rng.uniform(0.0, 90.0))


def build_boundary_impacts(
    *,
    escaping_cells,
    board_dims: tuple[int, ...],
    rng_seed: int,
    dimension: int,
    tuning: Any,
) -> tuple[EndgameBoundaryImpact, ...]:
    dims = tuple(int(value) for value in board_dims[: int(dimension)])
    cells = tuple(_cell_parts(cell, len(dims)) for cell in escaping_cells)
    selected = _select_cells(cells, dims, int(rng_seed), boundary_impact_cap_for_dimension(dimension, tuning))
    return tuple(_impact_for_cell(cell, dims, int(rng_seed)) for cell in selected)


def build_escape_events(
    *,
    escaping_cells,
    board_dims: tuple[int, ...],
    rng_seed: int,
    dimension: int,
    tuning: Any,
) -> tuple[EndgameEscapeEvent, ...]:
    impacts = build_boundary_impacts(
        escaping_cells=escaping_cells,
        board_dims=board_dims,
        rng_seed=rng_seed,
        dimension=dimension,
        tuning=tuning,
    )
    source_lookup = {
        parts[0]: parts
        for parts in (
            _cell_parts(cell, int(dimension))
            for cell in escaping_cells
        )
    }
    timeline = load_shell_timeline(tuning)
    delay_max_ms = _value(tuning, "shell_event_delay_max_ms", 180.0)
    impact_progress_min = _value(tuning, "shell_event_proxy_impact_progress_min", 0.78)
    impact_progress_max = _value(tuning, "shell_event_proxy_impact_progress_max", 0.92)
    progress_min = min(impact_progress_min, impact_progress_max)
    progress_max = max(impact_progress_min, impact_progress_max)
    events: list[EndgameEscapeEvent] = []
    for index, impact in enumerate(impacts):
        coord, start, _color_id, layer = source_lookup[tuple(int(v) for v in impact.source_coord)]
        rng = random.Random(_mix(_score(coord, impact.color_id, impact.axis, int(rng_seed)), index ^ 0x51ED))
        rupture_delay_ms = rng.uniform(0.0, delay_max_ms)
        impact_progress = rng.uniform(progress_min, progress_max)
        remaining_rupture_ms = max(60.0, float(timeline.rupture_ms) - rupture_delay_ms)
        proxy_lifetime_ms = max(60.0, remaining_rupture_ms * impact_progress)
        impact_ms = float(timeline.hold_ms) + rupture_delay_ms + proxy_lifetime_ms
        events.append(
            EndgameEscapeEvent(
                event_index=index,
                source_coord=tuple(int(v) for v in impact.source_coord),
                source_position=tuple(float(v) for v in start),
                color_id=int(impact.color_id),
                source_layer_index=None if layer < 0 else int(layer),
                impact_position=tuple(float(v) for v in impact.impact_position),
                impact_axis=int(impact.axis),
                impact_side=int(impact.side),
                outward_direction=tuple(float(v) for v in impact.outward_direction),
                force=float(impact.force),
                rupture_delay_ms=rupture_delay_ms,
                impact_ms=impact_ms,
                proxy_lifetime_ms=proxy_lifetime_ms,
                shard_indices=(),
            )
        )
    return tuple(events)


def boundary_impact_from_event(event: EndgameEscapeEvent) -> EndgameBoundaryImpact:
    return EndgameBoundaryImpact(
        source_coord=tuple(int(v) for v in event.source_coord),
        start_position=tuple(float(v) for v in event.source_position),
        impact_position=tuple(float(v) for v in event.impact_position),
        outward_direction=tuple(float(v) for v in event.outward_direction),
        color_id=int(event.color_id),
        axis=int(event.impact_axis),
        side=int(event.impact_side),
        force=float(event.force),
        birth_ms=float(event.impact_ms),
    )


def build_board_shards(
    *,
    impacts: tuple[EndgameBoundaryImpact, ...] | None = None,
    events: tuple[EndgameEscapeEvent, ...] | None = None,
    rng_seed: int,
    dimension: int,
    tuning: Any,
) -> tuple[EndgameBoardShard, ...]:
    cap, shards = board_shard_cap_for_dimension(dimension, tuning), []
    birth_spread_ms = min(
        40.0,
        max(0.0, _value(tuning, "shell_event_impact_window_ms", 420.0) * 0.1),
    )
    event_sequence = events
    if event_sequence is None:
        event_sequence = tuple(
            EndgameEscapeEvent(
                event_index=index,
                source_coord=tuple(int(v) for v in impact.source_coord),
                source_position=tuple(float(v) for v in impact.start_position),
                color_id=int(impact.color_id),
                source_layer_index=None,
                impact_position=tuple(float(v) for v in impact.impact_position),
                impact_axis=int(impact.axis),
                impact_side=int(impact.side),
                outward_direction=tuple(float(v) for v in impact.outward_direction),
                force=float(impact.force),
                rupture_delay_ms=0.0,
                impact_ms=float(impact.birth_ms),
                proxy_lifetime_ms=0.0,
                shard_indices=(),
            )
            for index, impact in enumerate(impacts or ())
        )
    for event in event_sequence:
        for shard_index in range(max(1, min(3, cap - len(shards)))):
            rng = random.Random(_mix(_score(event.source_coord, event.color_id, shard_index, rng_seed), event.event_index))
            jitter = tuple(rng.uniform(-0.45, 0.45) for _ in event.outward_direction)
            direction = _norm(tuple((value * 1.8) + jitter[idx] for idx, value in enumerate(event.outward_direction)), event.outward_direction)
            shards.append(
                EndgameBoardShard(
                    source_impact_index=int(event.event_index),
                    event_index=int(event.event_index),
                    source_coord=tuple(int(v) for v in event.source_coord),
                    start_position=tuple(float(v) for v in event.impact_position),
                    direction=direction,
                    speed=rng.uniform(_value(tuning, "board_shard_speed_min", 1.2), _value(tuning, "board_shard_speed_max", 4.0)),
                    spin_deg_per_s=rng.uniform(_value(tuning, "board_shard_spin_min_deg_per_s", -240.0), _value(tuning, "board_shard_spin_max_deg_per_s", 240.0)),
                    size=rng.uniform(0.18, 0.48) * event.force,
                    birth_ms=float(event.impact_ms) + rng.uniform(0.0, birth_spread_ms),
                    lifetime_ms=rng.uniform(_value(tuning, "board_shard_lifetime_min_ms", 1200.0), _value(tuning, "board_shard_lifetime_max_ms", 2600.0)),
                    alpha=max(0.0, min(1.0, _value(tuning, "board_shard_alpha", 0.45))),
                    color_hint=None,
                )
            )
            if len(shards) >= cap:
                return tuple(shards)
    return tuple(shards)


def link_shards_to_events(
    events: tuple[EndgameEscapeEvent, ...],
    shards: tuple[EndgameBoardShard, ...],
) -> tuple[EndgameEscapeEvent, ...]:
    shard_indices_by_event: dict[int, list[int]] = {}
    for index, shard in enumerate(shards):
        shard_indices_by_event.setdefault(int(shard.event_index), []).append(index)
    return tuple(
        EndgameEscapeEvent(
            event_index=event.event_index,
            source_coord=event.source_coord,
            source_position=event.source_position,
            color_id=event.color_id,
            source_layer_index=event.source_layer_index,
            impact_position=event.impact_position,
            impact_axis=event.impact_axis,
            impact_side=event.impact_side,
            outward_direction=event.outward_direction,
            force=event.force,
            rupture_delay_ms=event.rupture_delay_ms,
            impact_ms=event.impact_ms,
            proxy_lifetime_ms=event.proxy_lifetime_ms,
            shard_indices=tuple(shard_indices_by_event.get(int(event.event_index), ())),
        )
        for event in events
    )


def transform_boundary_impact(impact: EndgameBoundaryImpact, *, elapsed_ms: float, tuning: Any) -> EndgameImpactDrawState | None:
    age = float(elapsed_ms) - impact.birth_ms
    flash_ms = _value(tuning, "impact_flash_duration_ms", 260.0)
    lifetime = max(flash_ms, _value(tuning, "impact_streak_lifetime_ms", 650.0))
    if age < 0.0 or age > lifetime:
        return None
    return EndgameImpactDrawState(
        impact.impact_position,
        max(0.0, 1.0 - age / max(1.0, lifetime)) * impact.force,
        _value(tuning, "impact_flash_radius", 5.0) * (0.45 + min(1.0, age / max(1.0, flash_ms))),
        _value(tuning, "impact_streak_width", 3.5),
    )


def transform_board_shard(shard: EndgameBoardShard, *, elapsed_ms: float, tuning: Any) -> EndgameShardDrawState | None:
    age = float(elapsed_ms) - shard.birth_ms
    if age < 0.0 or age > shard.lifetime_ms:
        return None
    seconds = age / 1000.0
    fade = max(0.0, 1.0 - age / max(1.0, shard.lifetime_ms))
    alpha = min(shard.alpha, _value(tuning, "board_shard_alpha", shard.alpha)) * fade
    position = tuple(shard.start_position[idx] + shard.direction[idx] * shard.speed * seconds for idx in range(len(shard.start_position)))
    return EndgameShardDrawState(position, alpha, shard.spin_deg_per_s * seconds, shard.size)


def _tangent_direction(event: EndgameEscapeEvent) -> VecN:
    direction = tuple(float(v) for v in event.outward_direction)
    if len(direction) == 2:
        return _norm((-direction[1], direction[0]), (0.0, 1.0))
    axis_a = int(event.impact_axis) % len(direction)
    axis_b = (axis_a + 1) % len(direction)
    tangent = [0.0 for _ in direction]
    tangent[axis_a] = -direction[axis_b]
    tangent[axis_b] = direction[axis_a]
    return _norm(tuple(tangent), tuple(1.0 if idx == axis_b else 0.0 for idx in range(len(direction))))


def evaluate_escape_event(
    event: EndgameEscapeEvent,
    *,
    elapsed_ms: float,
    timeline: EndgameShellTimeline,
    shards: tuple[EndgameBoardShard, ...],
    tuning: Any,
) -> EscapeEventFrame:
    release_ms = float(timeline.hold_ms) + float(event.rupture_delay_ms)
    impact_ms = float(event.impact_ms)
    proxy_end_ms = impact_ms
    source_cell_visible = float(elapsed_ms) < release_ms
    proxy: EscapeProxyState | None = None
    streak: EscapeStreakState | None = None
    if release_ms <= float(elapsed_ms) < proxy_end_ms:
        rupture_t = _clamp01((float(elapsed_ms) - release_ms) / max(1.0, float(event.proxy_lifetime_ms)))
        distance_t = _ease_in_cubic(rupture_t)
        wobble_t = math.sin(math.pi * rupture_t)
        tangent_scale = _value(tuning, "shell_event_proxy_tangent_jitter", 0.22) * float(event.force)
        tangent = _tangent_direction(event)
        position = tuple(
            value + (tangent[idx] * tangent_scale * wobble_t)
            for idx, value in enumerate(_lerp_vec(event.source_position, event.impact_position, distance_t))
        )
        alpha = 1.0 if rupture_t <= 0.7 else 1.0 - (((rupture_t - 0.7) / 0.25) * 0.65)
        scale_peak = _value(tuning, "shell_event_proxy_scale_peak", 1.18)
        scale = 1.0 + ((scale_peak - 1.0) * math.sin(math.pi * rupture_t))
        rotation = float(event.impact_side) * _value(tuning, "shell_event_proxy_rotation_deg", 28.0) * wobble_t
        proxy = EscapeProxyState(
            event_index=int(event.event_index),
            source_coord=tuple(int(v) for v in event.source_coord),
            render_position=position,
            color_id=int(event.color_id),
            alpha=max(0.0, min(1.0, alpha)),
            scale=scale,
            rotation_deg=rotation,
            progress=rupture_t,
            layer_index=event.source_layer_index,
        )
        streak_tail_progress = max(0.0, rupture_t - 0.18)
        tail_base = _lerp_vec(event.source_position, event.impact_position, _ease_in_cubic(streak_tail_progress))
        streak = EscapeStreakState(
            event_index=int(event.event_index),
            source_coord=tuple(int(v) for v in event.source_coord),
            tail_position=tail_base,
            head_position=position,
            color_id=int(event.color_id),
            alpha=0.22 + (0.66 * max(0.0, float(proxy.alpha))),
            width_scale=0.8 + (0.7 * rupture_t),
            layer_index=event.source_layer_index,
        )
    flash_lead_ms = min(80.0, float(timeline.impact_window_ms) * 0.5)
    flash_start_ms = impact_ms - flash_lead_ms
    flash_end_ms = impact_ms + float(timeline.impact_window_ms)
    impact_flash: ImpactFlashState | None = None
    if flash_start_ms <= float(elapsed_ms) <= flash_end_ms:
        if float(elapsed_ms) <= impact_ms:
            progress = _clamp01((float(elapsed_ms) - flash_start_ms) / max(1.0, flash_lead_ms))
            alpha = 0.2 + (0.8 * progress)
        else:
            progress = _clamp01((float(elapsed_ms) - impact_ms) / max(1.0, float(timeline.impact_window_ms)))
            alpha = 1.0 - progress
        impact_flash = ImpactFlashState(
            event_index=int(event.event_index),
            source_coord=tuple(int(v) for v in event.source_coord),
            position=tuple(float(v) for v in event.impact_position),
            color_id=int(event.color_id),
            alpha=max(0.0, min(1.0, alpha * float(event.force))),
            radius_scale=0.65 + (0.75 * _smoothstep(alpha)),
            force=float(event.force),
            layer_index=event.source_layer_index,
        )
    shard_draw_states = tuple(
        draw_state
        for shard in shards
        if int(shard.event_index) == int(event.event_index)
        if (draw_state := transform_board_shard(shard, elapsed_ms=float(elapsed_ms), tuning=tuning)) is not None
    )
    residue_alpha = 0.0
    if float(elapsed_ms) >= impact_ms:
        residue_alpha = _value(tuning, "shell_event_residue_alpha", _value(tuning, "cracked_board_residue_alpha", 0.14))
        residue_alpha *= _smoothstep((float(elapsed_ms) - impact_ms) / max(1.0, float(timeline.impact_window_ms)))
    residue = ()
    if residue_alpha > 0.0:
        residue = (
            ResidueCrackState(
                event_index=int(event.event_index),
                source_coord=tuple(int(v) for v in event.source_coord),
                position=tuple(float(v) for v in event.impact_position),
                direction=tuple(float(v) for v in event.outward_direction),
                alpha=residue_alpha,
                length_scale=0.8 + (0.55 * float(event.force)),
                layer_index=event.source_layer_index,
            ),
        )
    return EscapeEventFrame(
        event_index=int(event.event_index),
        source_coord=tuple(int(v) for v in event.source_coord),
        source_cell_visible=source_cell_visible,
        proxy=proxy,
        streak=streak,
        impact_flash=impact_flash,
        shards=shard_draw_states,
        residue=residue,
    )


def shell_sound_events_for_frame(
    events: tuple[EndgameEscapeEvent, ...],
    *,
    previous_elapsed_ms: float,
    elapsed_ms: float,
    timeline: EndgameShellTimeline,
    max_release_sounds: int,
    max_impact_sounds: int,
    run_key: str = "shell",
) -> tuple[EndgameShellSoundEvent, ...]:
    previous = float(previous_elapsed_ms)
    current = float(elapsed_ms)
    if current < previous:
        previous, current = current, previous

    def crossed(trigger_ms: float) -> bool:
        return previous < float(trigger_ms) <= current

    events_out: list[EndgameShellSoundEvent] = []
    if crossed(0.0):
        events_out.append(
            EndgameShellSoundEvent(
                event_key=f"{run_key}:global:charge",
                sound_id="endgame_charge_rumble",
                trigger_ms=0.0,
                volume=0.34,
                pan_hint=None,
                pitch=0.94,
            )
        )
    if crossed(float(timeline.hold_ms)):
        events_out.append(
            EndgameShellSoundEvent(
                event_key=f"{run_key}:global:rupture",
                sound_id="endgame_rupture_thump",
                trigger_ms=float(timeline.hold_ms),
                volume=0.76,
                pan_hint=None,
                pitch=1.0,
            )
        )
    release_events = sorted(
        (
            event
            for event in events
            if crossed(float(timeline.hold_ms) + float(event.rupture_delay_ms))
        ),
        key=lambda event: (float(event.rupture_delay_ms), int(event.event_index)),
    )[: max(0, int(max_release_sounds))]
    for event in release_events:
        events_out.append(
            EndgameShellSoundEvent(
                event_key=f"{run_key}:release:{int(event.event_index)}",
                sound_id="endgame_cell_release",
                trigger_ms=float(timeline.hold_ms) + float(event.rupture_delay_ms),
                volume=0.28 + (0.32 * float(event.force)),
                pan_hint=max(-1.0, min(1.0, float(event.outward_direction[0]) if event.outward_direction else 0.0)),
                pitch=0.96 + (0.12 * float(event.force)),
            )
        )
    impact_events = sorted(
        (
            event
            for event in events
            if crossed(float(event.impact_ms))
        ),
        key=lambda event: (float(event.impact_ms), int(event.event_index)),
    )
    if impact_events:
        cluster_trigger_ms = min(float(event.impact_ms) for event in impact_events)
        events_out.append(
            EndgameShellSoundEvent(
                event_key=f"{run_key}:global:glass_shatter",
                sound_id="endgame_glass_shatter",
                trigger_ms=cluster_trigger_ms,
                volume=0.72,
                pan_hint=None,
                pitch=1.0,
            )
        )
    for event in impact_events[: max(0, int(max_impact_sounds))]:
        events_out.append(
            EndgameShellSoundEvent(
                event_key=f"{run_key}:impact:{int(event.event_index)}",
                sound_id="endgame_boundary_crack",
                trigger_ms=float(event.impact_ms),
                volume=0.34 + (0.42 * float(event.force)),
                pan_hint=max(-1.0, min(1.0, float(event.outward_direction[0]) if event.outward_direction else 0.0)),
                pitch=0.92 + (0.16 * float(event.force)),
            )
        )
    return tuple(events_out)
