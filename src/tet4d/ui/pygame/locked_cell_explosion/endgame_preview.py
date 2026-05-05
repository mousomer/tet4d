from __future__ import annotations

from dataclasses import dataclass
import math
from typing import TYPE_CHECKING

from tet4d.engine.runtime.project_config import constants_payload
from tet4d.ui.pygame.endgame_shell_effects import (
    EscapeEventFrame,
    EndgameBoardShard,
    EndgameBoundaryImpact,
    EndgameImpactDrawState,
    EndgameShellSoundEvent,
    EndgameShardDrawState,
    build_escape_events,
    build_board_shards,
    boundary_impact_from_event,
    evaluate_escape_event,
    link_shards_to_events,
    load_shell_timeline,
    shell_sound_events_for_frame,
    transform_board_shard,
    transform_boundary_impact,
)

from .model import ExplosionSeedCell

if TYPE_CHECKING:
    from tet4d.ui.pygame.endgame_animation import SnapshotCell


@dataclass(frozen=True)
class PreviewSourceCell:
    source_coord: tuple[int, ...]
    position: tuple[float, ...]
    color_id: int
    layer_index: int | None
    source_group_id: str | None = None


@dataclass(frozen=True)
class ShellPreviewEscapingCellState:
    source_coord: tuple[int, ...]
    source_position: tuple[float, ...]
    render_position: tuple[float, ...]
    rotation_deg: tuple[float, float, float]
    alpha: float
    color_id: int
    progress: float
    layer_index: int | None


@dataclass(frozen=True)
class EndgamePreviewCache:
    source_cells: tuple[PreviewSourceCell, ...]
    survivor_cells: tuple[ExplosionSeedCell, ...]
    escaping_cells: tuple[ExplosionSeedCell, ...]
    escaping_source_cells: tuple[PreviewSourceCell, ...]
    escape_events: tuple
    impacts: tuple[EndgameBoundaryImpact, ...]
    shards: tuple[EndgameBoardShard, ...]


@dataclass(frozen=True)
class EndgamePreviewFrame:
    phase: str
    frozen_cells: tuple[PreviewSourceCell, ...]
    escape_event_frames: tuple[EscapeEventFrame, ...]
    sound_events: tuple[EndgameShellSoundEvent, ...]
    escaping_proxy_cells: tuple[ShellPreviewEscapingCellState, ...]
    impact_frames: tuple[tuple[EndgameBoundaryImpact, EndgameImpactDrawState], ...]
    shard_frames: tuple[tuple[EndgameBoundaryImpact, EndgameBoardShard, EndgameShardDrawState], ...]
    residue_frames: tuple[tuple[EndgameBoundaryImpact, float], ...]


_PHASE_HOLD = "hold"
_PHASE_RUPTURE = "rupture"
_PHASE_SHARD_DRIFT = "shard_drift"
_PHASE_RESIDUE = "residue"


def _tuning() -> dict[str, object]:
    return constants_payload()["animation"]["endgame"]


def _float_value(tuning: dict[str, object], name: str, default: float) -> float:
    return float(tuning.get(name, default))


def default_shell_preview_time_scale(tuning: dict[str, object] | None = None) -> float:
    resolved_tuning = _tuning() if tuning is None else tuning
    return max(0.0, _float_value(resolved_tuning, "shell_preview_default_time_scale", 1.0))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _lerp(a: float, b: float, t: float) -> float:
    progress = _clamp01(t)
    return float(a) + ((float(b) - float(a)) * progress)


def _lerp_vec(start: tuple[float, ...], end: tuple[float, ...], t: float) -> tuple[float, ...]:
    progress = _clamp01(t)
    return tuple(_lerp(start[idx], end[idx], progress) for idx in range(len(start)))


def _smoothstep(value: float) -> float:
    progress = _clamp01(value)
    return progress * progress * (3.0 - (2.0 * progress))


def _phase_start_ms(phase: str, tuning: dict[str, object]) -> float:
    hold_ms = _float_value(tuning, "shell_preview_hold_ms", 1000.0)
    rupture_ms = _float_value(tuning, "shell_preview_rupture_ms", 1100.0)
    shard_ms = _float_value(tuning, "shell_preview_shard_drift_ms", 2200.0)
    if phase == _PHASE_RUPTURE:
        return hold_ms
    if phase == _PHASE_SHARD_DRIFT:
        return hold_ms + rupture_ms
    if phase == _PHASE_RESIDUE:
        return hold_ms + rupture_ms + shard_ms
    return 0.0


def shell_preview_phase_for_elapsed(elapsed_ms: float, tuning: dict[str, object] | None = None) -> str:
    resolved_tuning = _tuning() if tuning is None else tuning
    hold_ms = _float_value(resolved_tuning, "shell_preview_hold_ms", 1000.0)
    rupture_ms = _float_value(resolved_tuning, "shell_preview_rupture_ms", 1100.0)
    shard_ms = _float_value(resolved_tuning, "shell_preview_shard_drift_ms", 2200.0)
    elapsed = max(0.0, float(elapsed_ms))
    if elapsed < hold_ms:
        return _PHASE_HOLD
    if elapsed < hold_ms + rupture_ms:
        return _PHASE_RUPTURE
    if elapsed < hold_ms + rupture_ms + shard_ms:
        return _PHASE_SHARD_DRIFT
    return _PHASE_RESIDUE


def shell_preview_timeline_progress(
    elapsed_ms: float,
    *,
    phase: str,
    tuning: dict[str, object] | None = None,
) -> float:
    resolved_tuning = _tuning() if tuning is None else tuning
    start_ms = _phase_start_ms(phase, resolved_tuning)
    if phase == _PHASE_HOLD:
        duration_ms = _float_value(resolved_tuning, "shell_preview_hold_ms", 1000.0)
    elif phase == _PHASE_RUPTURE:
        duration_ms = _float_value(resolved_tuning, "shell_preview_rupture_ms", 1100.0)
    elif phase == _PHASE_SHARD_DRIFT:
        duration_ms = _float_value(resolved_tuning, "shell_preview_shard_drift_ms", 2200.0)
    else:
        return 1.0
    return _clamp01((max(0.0, float(elapsed_ms)) - start_ms) / max(1.0, duration_ms))


def scaled_shell_preview_elapsed(state, dt_ms: float, tuning: dict[str, object] | None = None) -> float:
    resolved_tuning = _tuning() if tuning is None else tuning
    default_scale = _float_value(resolved_tuning, "shell_preview_default_time_scale", 1.0)
    scale = float(getattr(state, "shell_preview_time_scale", default_scale))
    return max(0.0, float(dt_ms)) * max(0.0, scale)


def _sorted_seed_cells(source_cells: tuple[ExplosionSeedCell, ...]) -> tuple[ExplosionSeedCell, ...]:
    return tuple(sorted(source_cells, key=lambda cell: (tuple(int(v) for v in cell.source_coord), int(cell.color_id), str(cell.source_group_id or ""))))


def _preview_source_cells(source_cells: tuple[ExplosionSeedCell, ...], dimension: int) -> tuple[PreviewSourceCell, ...]:
    return tuple(
        PreviewSourceCell(
            source_coord=tuple(int(v) for v in cell.source_coord[:dimension]),
            position=tuple(float(v) for v in cell.source_coord[:dimension]),
            color_id=int(cell.color_id),
            layer_index=int(cell.source_coord[3]) if int(dimension) == 4 and len(cell.source_coord) > 3 else None,
            source_group_id=str(cell.source_group_id) if cell.source_group_id is not None else None,
        )
        for cell in _sorted_seed_cells(source_cells)
    )


def _snapshot_cells(source_cells: tuple[PreviewSourceCell, ...]) -> tuple["SnapshotCell", ...]:
    from tet4d.ui.pygame.endgame_animation import SnapshotCell

    return tuple(
        SnapshotCell(
            source_coord=tuple(int(v) for v in cell.source_coord),
            position=tuple(float(v) for v in cell.position),
            color_id=int(cell.color_id),
            layer_index=cell.layer_index,
        )
        for cell in source_cells
    )


def _seed_cells(snapshot_cells: tuple["SnapshotCell", ...], *, source_lookup: dict[tuple[int, ...], PreviewSourceCell]) -> tuple[ExplosionSeedCell, ...]:
    return tuple(
        ExplosionSeedCell(
            source_coord=tuple(int(v) for v in cell.source_coord),
            color_id=int(cell.color_id),
            source_group_id=source_lookup[tuple(int(v) for v in cell.source_coord)].source_group_id,
        )
        for cell in snapshot_cells
    )


def preview_source_cell_map(cache: EndgamePreviewCache) -> dict[tuple[int, ...], PreviewSourceCell]:
    return {tuple(int(v) for v in cell.source_coord): cell for cell in cache.source_cells}


def _signature(source_cells: tuple[ExplosionSeedCell, ...], board_dims: tuple[int, ...], dimension: int, seed: int, live_fraction: float) -> tuple[object, ...]:
    return (
        int(dimension),
        tuple(int(v) for v in board_dims),
        int(seed),
        round(float(live_fraction), 6),
        tuple((tuple(int(v) for v in cell.source_coord), int(cell.color_id), str(cell.source_group_id or "")) for cell in _sorted_seed_cells(source_cells)),
    )


def reset_shell_preview_state(state) -> None:
    state.shell_preview_elapsed_ms = 0.0
    state.shell_preview_signature = None
    state.shell_preview_cache = None


def advance_shell_preview_elapsed(state, dt_ms: float) -> None:
    if bool(getattr(state, "shell_preview_enabled", False)):
        tuning = _tuning()
        state.shell_preview_elapsed_ms = max(
            0.0,
            float(getattr(state, "shell_preview_elapsed_ms", 0.0)) + scaled_shell_preview_elapsed(state, dt_ms, tuning),
        )


def _build_cache(source_cells: tuple[ExplosionSeedCell, ...], board_dims: tuple[int, ...], dimension: int, seed: int, live_fraction: float) -> EndgamePreviewCache:
    from tet4d.ui.pygame.endgame_animation import split_endgame_locked_cells

    preview_cells = _preview_source_cells(source_cells, int(dimension))
    source_lookup = {tuple(int(v) for v in cell.source_coord): cell for cell in preview_cells}
    snapshot_cells = _snapshot_cells(preview_cells)
    split = split_endgame_locked_cells(locked_cells=snapshot_cells, dimension=int(dimension), seed=int(seed), live_fraction=float(live_fraction))
    escaping_source_cells = tuple(source_lookup[tuple(int(v) for v in cell.source_coord)] for cell in split.escaping_cells)
    escape_events = build_escape_events(
        escaping_cells=escaping_source_cells,
        board_dims=tuple(int(v) for v in board_dims),
        rng_seed=int(seed),
        dimension=int(dimension),
        tuning=_tuning(),
    )
    impacts = tuple(boundary_impact_from_event(event) for event in escape_events)
    shards = build_board_shards(events=escape_events, rng_seed=int(seed), dimension=int(dimension), tuning=_tuning())
    return EndgamePreviewCache(
        preview_cells,
        _seed_cells(split.persistent_live_cells, source_lookup=source_lookup),
        _seed_cells(split.escaping_cells, source_lookup=source_lookup),
        escaping_source_cells,
        link_shards_to_events(tuple(escape_events), tuple(shards)),
        impacts,
        tuple(shards),
    )


def ensure_shell_preview_cache(state, *, source_cells: tuple[ExplosionSeedCell, ...], board_dims: tuple[int, ...]) -> EndgamePreviewCache | None:
    if not bool(getattr(state, "shell_preview_enabled", False)):
        reset_shell_preview_state(state)
        return None
    signature = _signature(tuple(source_cells), board_dims, int(getattr(state, "dimension", len(board_dims))), int(getattr(state, "seed", 0)), float(getattr(state, "endgame_live_cell_fraction", 0.12)))
    if getattr(state, "shell_preview_cache", None) is None or getattr(state, "shell_preview_signature", None) != signature:
        state.shell_preview_elapsed_ms = 0.0
        state.shell_preview_signature = signature
        state.shell_preview_cache = _build_cache(tuple(source_cells), tuple(int(v) for v in board_dims), int(getattr(state, "dimension", len(board_dims))), int(getattr(state, "seed", 0)), float(getattr(state, "endgame_live_cell_fraction", 0.12)))
    return state.shell_preview_cache


def preview_survivor_cells_for_state(state, *, source_cells: tuple[ExplosionSeedCell, ...], board_dims: tuple[int, ...]) -> tuple[ExplosionSeedCell, ...]:
    cache = ensure_shell_preview_cache(state, source_cells=source_cells, board_dims=board_dims)
    return tuple(source_cells) if cache is None else cache.survivor_cells


def _rupture_impact_draw_state(
    impact: EndgameBoundaryImpact,
    *,
    rupture_progress: float,
    tuning: dict[str, object],
) -> EndgameImpactDrawState:
    eased = 0.08 + (0.92 * (0.5 - (0.5 * math.cos(math.pi * _clamp01(rupture_progress)))))
    flash_progress = _clamp01((rupture_progress - 0.72) / 0.28)
    flash_alpha = _smoothstep(flash_progress) * impact.force
    return EndgameImpactDrawState(
        position=_lerp_vec(impact.start_position, impact.impact_position, eased),
        alpha=max(0.18, 0.42 + (0.48 * eased)) * impact.force,
        radius=_float_value(tuning, "impact_flash_radius", 5.0) * flash_alpha,
        streak_width=_float_value(tuning, "impact_streak_width", 3.5) * (0.9 + (0.55 * eased)),
    )


def _rupture_proxy_progress(rupture_progress: float) -> float:
    return _smoothstep(_clamp01(float(rupture_progress) / 0.84))


def _rupture_proxy_alpha(impact: EndgameBoundaryImpact, *, rupture_progress: float) -> float:
    fade = 1.0 - _smoothstep(max(0.0, (float(rupture_progress) - 0.78) / 0.22))
    return max(0.0, min(1.0, fade * (0.8 + (0.2 * float(impact.force)))))


def _rupture_proxy_rotation_deg(
    impact: EndgameBoundaryImpact,
    *,
    progress: float,
) -> tuple[float, float, float]:
    spin = float(impact.side) * (18.0 + (54.0 * float(impact.force))) * (0.35 + progress)
    axis_scale = float(impact.axis + 1)
    return (
        spin * 0.16 * axis_scale,
        spin * 0.24 * max(1.0, len(impact.source_coord) - axis_scale + 1.0),
        spin * 0.82,
    )


def _escaping_proxy_state_for_impact(
    impact: EndgameBoundaryImpact,
    *,
    source_cell: PreviewSourceCell,
    rupture_progress: float,
) -> ShellPreviewEscapingCellState:
    progress = _rupture_proxy_progress(rupture_progress)
    return ShellPreviewEscapingCellState(
        source_coord=tuple(int(v) for v in impact.source_coord),
        source_position=tuple(float(v) for v in source_cell.position),
        render_position=_lerp_vec(impact.start_position, impact.impact_position, progress),
        rotation_deg=_rupture_proxy_rotation_deg(impact, progress=progress),
        alpha=_rupture_proxy_alpha(impact, rupture_progress=rupture_progress),
        color_id=int(impact.color_id),
        progress=progress,
        layer_index=source_cell.layer_index,
    )


def _residue_frames(
    impacts: tuple[EndgameBoundaryImpact, ...],
    *,
    elapsed_ms: float,
    tuning: dict[str, object],
) -> tuple[tuple[EndgameBoundaryImpact, float], ...]:
    phase = shell_preview_phase_for_elapsed(elapsed_ms, tuning)
    if phase == _PHASE_HOLD:
        return ()
    if phase == _PHASE_RUPTURE:
        alpha = 0.0
    elif phase == _PHASE_SHARD_DRIFT:
        progress = shell_preview_timeline_progress(elapsed_ms, phase=_PHASE_SHARD_DRIFT, tuning=tuning)
        alpha = _float_value(tuning, "cracked_board_residue_alpha", 0.14) * _smoothstep(max(0.0, (progress - 0.18) / 0.82))
    else:
        alpha = _float_value(tuning, "cracked_board_residue_alpha", 0.14)
    return tuple((impact, alpha) for impact in impacts if alpha > 0.0)


def build_shell_preview_frame_for_state(
    state,
    *,
    source_cells: tuple[ExplosionSeedCell, ...],
    board_dims: tuple[int, ...],
    previous_elapsed_ms: float | None = None,
    sound_run_key: str = "shell_preview",
) -> EndgamePreviewFrame | None:
    cache = ensure_shell_preview_cache(state, source_cells=source_cells, board_dims=board_dims)
    if cache is None:
        return None
    elapsed_ms, tuning = float(getattr(state, "shell_preview_elapsed_ms", 0.0)), _tuning()
    phase = shell_preview_phase_for_elapsed(elapsed_ms, tuning)
    timeline = load_shell_timeline(tuning)
    escape_event_frames = tuple(
        evaluate_escape_event(
            event,
            elapsed_ms=elapsed_ms,
            timeline=timeline,
            shards=cache.shards,
            tuning=tuning,
        )
        for event in cache.escape_events
    )
    sound_events = ()
    if previous_elapsed_ms is not None:
        sound_events = shell_sound_events_for_frame(
            tuple(cache.escape_events),
            previous_elapsed_ms=float(previous_elapsed_ms),
            elapsed_ms=elapsed_ms,
            timeline=timeline,
            max_release_sounds=8,
            max_impact_sounds=10,
            run_key=str(sound_run_key),
        )
    if phase == _PHASE_HOLD:
        return EndgamePreviewFrame(
            phase=phase,
            frozen_cells=cache.source_cells,
            escape_event_frames=escape_event_frames,
            sound_events=tuple(sound_events),
            escaping_proxy_cells=(),
            impact_frames=(),
            shard_frames=(),
            residue_frames=(),
        )
    if phase == _PHASE_RUPTURE:
        rupture_progress = shell_preview_timeline_progress(elapsed_ms, phase=_PHASE_RUPTURE, tuning=tuning)
        source_map = preview_source_cell_map(cache)
        impact_frames = tuple(
            (impact, _rupture_impact_draw_state(impact, rupture_progress=rupture_progress, tuning=tuning))
            for impact in cache.impacts
        )
        return EndgamePreviewFrame(
            phase=phase,
            frozen_cells=(),
            escape_event_frames=escape_event_frames,
            sound_events=tuple(sound_events),
            escaping_proxy_cells=tuple(
                _escaping_proxy_state_for_impact(
                    impact,
                    source_cell=source_map[tuple(int(v) for v in impact.source_coord)],
                    rupture_progress=rupture_progress,
                )
                for impact in cache.impacts
            ),
            impact_frames=impact_frames,
            shard_frames=(),
            residue_frames=(),
        )
    return EndgamePreviewFrame(
        phase=phase,
        frozen_cells=(),
        escape_event_frames=escape_event_frames,
        sound_events=tuple(sound_events),
        escaping_proxy_cells=(),
        impact_frames=tuple(
            (impact, draw_state)
            for impact in cache.impacts
            if (draw_state := transform_boundary_impact(impact, elapsed_ms=elapsed_ms, tuning=tuning)) is not None
        ),
        shard_frames=tuple(
            (cache.impacts[shard.source_impact_index], shard, draw_state)
            for shard in cache.shards
            if (draw_state := transform_board_shard(shard, elapsed_ms=elapsed_ms, tuning=tuning)) is not None
        ),
        residue_frames=_residue_frames(cache.impacts, elapsed_ms=elapsed_ms, tuning=tuning),
    )
