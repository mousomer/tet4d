from __future__ import annotations

from typing import Any

from .settings_schema import (
    BOT_MODE_NAMES,
    GRID_MODE_NAMES,
    as_non_empty_string,
    require_int,
    require_list,
    require_number,
    require_object,
)


def validate_audio_sfx_payload(payload: dict[str, Any]) -> dict[str, Any]:
    require_int(payload.get("version"), path="audio.version", min_value=1)
    events_obj = require_object(payload.get("events"), path="audio.events")
    if not events_obj:
        raise RuntimeError("audio.events must not be empty")
    events: dict[str, dict[str, float | int]] = {}
    for event_name, raw_spec in events_obj.items():
        if not isinstance(event_name, str) or not event_name.strip():
            raise RuntimeError("audio.events keys must be non-empty strings")
        spec = require_object(raw_spec, path=f"audio.events.{event_name}")
        events[event_name] = {
            "frequency_hz": require_number(
                spec.get("frequency_hz"),
                path=f"audio.events.{event_name}.frequency_hz",
                min_value=1.0,
            ),
            "duration_ms": require_int(
                spec.get("duration_ms"),
                path=f"audio.events.{event_name}.duration_ms",
                min_value=1,
            ),
            "amplitude": require_number(
                spec.get("amplitude"),
                path=f"audio.events.{event_name}.amplitude",
                min_value=0.0,
                max_value=1.0,
            ),
        }
    return {"version": payload["version"], "events": events}


def _validate_speed_curve(raw_speed_curve: object) -> dict[str, dict[str, int]]:
    speed_curve = require_object(raw_speed_curve, path="gameplay.speed_curve")
    validated_speed_curve: dict[str, dict[str, int]] = {}
    for key in ("2d", "3d", "4d_plus"):
        entry = require_object(speed_curve.get(key), path=f"gameplay.speed_curve.{key}")
        validated_speed_curve[key] = {
            "base_ms": require_int(
                entry.get("base_ms"),
                path=f"gameplay.speed_curve.{key}.base_ms",
                min_value=1,
            ),
            "min_ms": require_int(
                entry.get("min_ms"),
                path=f"gameplay.speed_curve.{key}.min_ms",
                min_value=1,
            ),
        }
    return validated_speed_curve


def _validate_challenge_prefill(raw_challenge: object) -> dict[str, float]:
    challenge = require_object(raw_challenge, path="gameplay.challenge_prefill")
    return {
        "2d_fill_ratio": require_number(
            challenge.get("2d_fill_ratio"),
            path="gameplay.challenge_prefill.2d_fill_ratio",
            min_value=0.0,
            max_value=1.0,
        ),
        "nd_fill_ratio": require_number(
            challenge.get("nd_fill_ratio"),
            path="gameplay.challenge_prefill.nd_fill_ratio",
            min_value=0.0,
            max_value=1.0,
        ),
    }


def _validate_mode_factors(
    raw_factors: object,
    *,
    path: str,
    mode_names: tuple[str, ...],
) -> dict[str, float]:
    factors_obj = require_object(raw_factors, path=path)
    factors: dict[str, float] = {}
    for mode_name in mode_names:
        factors[mode_name] = require_number(
            factors_obj.get(mode_name),
            path=f"{path}.{mode_name}",
            min_value=0.0,
            max_value=1.0,
        )
    return factors


def _validate_kick_factors(
    raw_factors: object,
    *,
    level_order: tuple[str, ...],
) -> dict[str, float]:
    factors = _validate_mode_factors(
        raw_factors,
        path="gameplay.assist_scoring.kick_factors",
        mode_names=level_order,
    )
    if "off" in factors and float(factors["off"]) != 1.0:
        raise RuntimeError("gameplay.assist_scoring.kick_factors.off must be 1.0")
    previous: float | None = None
    for level_name in level_order:
        factor = float(factors[level_name])
        if previous is not None and factor > previous:
            raise RuntimeError(
                "gameplay.assist_scoring.kick_factors must not increase with kick permissiveness"
            )
        previous = factor
    return factors


def _validate_assist_scoring(
    raw_assist: object,
    *,
    kick_level_order: tuple[str, ...],
) -> dict[str, Any]:
    assist = require_object(raw_assist, path="gameplay.assist_scoring")
    bot_factors = _validate_mode_factors(
        assist.get("bot_factors"),
        path="gameplay.assist_scoring.bot_factors",
        mode_names=BOT_MODE_NAMES,
    )
    grid_factors = _validate_mode_factors(
        assist.get("grid_factors"),
        path="gameplay.assist_scoring.grid_factors",
        mode_names=GRID_MODE_NAMES,
    )
    speed_obj = require_object(
        assist.get("speed"), path="gameplay.assist_scoring.speed"
    )
    speed_min_level = require_int(
        speed_obj.get("min_level"),
        path="gameplay.assist_scoring.speed.min_level",
        min_value=1,
    )
    speed_max_level = require_int(
        speed_obj.get("max_level"),
        path="gameplay.assist_scoring.speed.max_level",
        min_value=speed_min_level,
    )
    speed = {
        "base": require_number(
            speed_obj.get("base"), path="gameplay.assist_scoring.speed.base"
        ),
        "per_level": require_number(
            speed_obj.get("per_level"), path="gameplay.assist_scoring.speed.per_level"
        ),
        "min_level": speed_min_level,
        "max_level": speed_max_level,
    }
    combined_obj = require_object(
        assist.get("combined"), path="gameplay.assist_scoring.combined"
    )
    combined_min = require_number(
        combined_obj.get("min"),
        path="gameplay.assist_scoring.combined.min",
    )
    combined_max = require_number(
        combined_obj.get("max"),
        path="gameplay.assist_scoring.combined.max",
        min_value=combined_min,
    )
    return {
        "bot_factors": bot_factors,
        "grid_factors": grid_factors,
        "kick_factors": _validate_kick_factors(
            assist.get("kick_factors"),
            level_order=kick_level_order,
        ),
        "speed": speed,
        "combined": {"min": combined_min, "max": combined_max},
    }


def _validate_rotation_kick_level_order(
    kicks: dict[str, Any],
) -> tuple[tuple[str, ...], set[str], str]:
    raw_level_order = require_list(
        kicks.get("level_order"),
        path="gameplay.rotation_kicks.level_order",
    )
    if not raw_level_order:
        raise RuntimeError("gameplay.rotation_kicks.level_order must not be empty")
    level_order: list[str] = []
    seen_levels: set[str] = set()
    for idx, raw_level in enumerate(raw_level_order):
        level_name = as_non_empty_string(
            raw_level,
            path=f"gameplay.rotation_kicks.level_order[{idx}]",
        ).lower()
        if level_name in seen_levels:
            raise RuntimeError(
                "gameplay.rotation_kicks.level_order must not contain duplicates"
            )
        seen_levels.add(level_name)
        level_order.append(level_name)
    default_level = as_non_empty_string(
        kicks.get("default_level"),
        path="gameplay.rotation_kicks.default_level",
    ).lower()
    if default_level not in seen_levels:
        raise RuntimeError(
            "gameplay.rotation_kicks.default_level must exist in level_order"
        )
    return tuple(level_order), seen_levels, default_level



def _validate_rotation_kick_level_candidates(
    raw_level_candidates: object,
    *,
    level_order: tuple[str, ...],
    seen_levels: set[str],
) -> dict[str, int]:
    level_candidates_obj = require_object(
        raw_level_candidates,
        path="gameplay.rotation_kicks.level_candidates",
    )
    if set(level_candidates_obj) != seen_levels:
        raise RuntimeError(
            "gameplay.rotation_kicks.level_candidates keys must match level_order"
        )
    level_candidates: dict[str, int] = {}
    previous = -1
    for level_name in level_order:
        count = require_int(
            level_candidates_obj.get(level_name),
            path=f"gameplay.rotation_kicks.level_candidates.{level_name}",
            min_value=0,
        )
        if count < previous:
            raise RuntimeError(
                "gameplay.rotation_kicks.level_candidates must be non-decreasing across level_order"
            )
        level_candidates[level_name] = count
        previous = count
    return level_candidates



def _validate_rotation_kick_candidate_offsets(
    raw_candidate_offsets: object,
) -> tuple[tuple[int, int], ...]:
    candidate_offset_rows = require_list(
        raw_candidate_offsets,
        path="gameplay.rotation_kicks.candidate_offsets",
    )
    if not candidate_offset_rows:
        raise RuntimeError(
            "gameplay.rotation_kicks.candidate_offsets must not be empty"
        )
    candidate_offsets: list[tuple[int, int]] = []
    seen_offsets: set[tuple[int, int]] = set()
    for idx, raw_pair in enumerate(candidate_offset_rows):
        pair = require_list(
            raw_pair,
            path=f"gameplay.rotation_kicks.candidate_offsets[{idx}]",
        )
        if len(pair) != 2:
            raise RuntimeError(
                f"gameplay.rotation_kicks.candidate_offsets[{idx}] must have length 2"
            )
        offset = (
            require_int(
                pair[0],
                path=f"gameplay.rotation_kicks.candidate_offsets[{idx}][0]",
            ),
            require_int(
                pair[1],
                path=f"gameplay.rotation_kicks.candidate_offsets[{idx}][1]",
            ),
        )
        if offset == (0, 0):
            raise RuntimeError(
                f"gameplay.rotation_kicks.candidate_offsets[{idx}] must not be [0, 0]"
            )
        if offset in seen_offsets:
            raise RuntimeError(
                f"gameplay.rotation_kicks.candidate_offsets[{idx}] duplicates an earlier offset"
            )
        seen_offsets.add(offset)
        candidate_offsets.append(offset)
    return tuple(candidate_offsets)



def _validate_rotation_kicks(raw_rotation_kicks: object) -> dict[str, Any]:
    kicks = require_object(raw_rotation_kicks, path="gameplay.rotation_kicks")
    level_order, seen_levels, default_level = _validate_rotation_kick_level_order(kicks)
    level_candidates = _validate_rotation_kick_level_candidates(
        kicks.get("level_candidates"),
        level_order=level_order,
        seen_levels=seen_levels,
    )
    candidate_offsets = _validate_rotation_kick_candidate_offsets(
        kicks.get("candidate_offsets")
    )
    if max(level_candidates.values()) > len(candidate_offsets):
        raise RuntimeError(
            "gameplay.rotation_kicks.level_candidates exceeds available candidate_offsets"
        )
    return {
        "default_level": default_level,
        "level_order": level_order,
        "level_candidates": level_candidates,
        "candidate_offsets": candidate_offsets,
    }


def _validate_grid_modes(raw_grid_modes: object) -> dict[str, Any]:
    grid_modes = require_object(raw_grid_modes, path="gameplay.grid_modes")
    raw_cycle = grid_modes.get("cycle")
    if not isinstance(raw_cycle, list) or not raw_cycle:
        raise RuntimeError("gameplay.grid_modes.cycle must be a non-empty list")
    cycle: list[str] = []
    for idx, mode_name in enumerate(raw_cycle):
        if not isinstance(mode_name, str):
            raise RuntimeError(f"gameplay.grid_modes.cycle[{idx}] must be a string")
        normalized = mode_name.strip().lower()
        if normalized not in GRID_MODE_NAMES:
            raise RuntimeError(
                f"gameplay.grid_modes.cycle[{idx}] must be one of: "
                + ", ".join(GRID_MODE_NAMES)
            )
        cycle.append(normalized)
    fallback = grid_modes.get("fallback")
    if not isinstance(fallback, str):
        raise RuntimeError("gameplay.grid_modes.fallback must be a string")
    fallback_mode = fallback.strip().lower()
    if fallback_mode not in cycle:
        raise RuntimeError(
            "gameplay.grid_modes.fallback must be present in gameplay.grid_modes.cycle"
        )
    return {"cycle": tuple(cycle), "fallback": fallback_mode}


def _validate_clear_scoring(raw_clear_scoring: object) -> dict[str, Any]:
    clear_scoring = require_object(
        raw_clear_scoring,
        path="gameplay.clear_scoring",
    )
    multi_layer_bonus = require_object(
        clear_scoring.get("multi_layer_bonus"),
        path="gameplay.clear_scoring.multi_layer_bonus",
    )
    tier_two = require_int(
        multi_layer_bonus.get("2"),
        path="gameplay.clear_scoring.multi_layer_bonus.2",
        min_value=0,
    )
    tier_three = require_int(
        multi_layer_bonus.get("3"),
        path="gameplay.clear_scoring.multi_layer_bonus.3",
        min_value=0,
    )
    tier_four = require_int(
        multi_layer_bonus.get("4"),
        path="gameplay.clear_scoring.multi_layer_bonus.4",
        min_value=0,
    )
    tier_five_plus = require_int(
        multi_layer_bonus.get("5_plus"),
        path="gameplay.clear_scoring.multi_layer_bonus.5_plus",
        min_value=0,
    )
    board_clear_bonus = require_int(
        clear_scoring.get("board_clear_bonus"),
        path="gameplay.clear_scoring.board_clear_bonus",
        min_value=0,
    )
    layer_size_weighting = require_object(
        clear_scoring.get("layer_size_weighting"),
        path="gameplay.clear_scoring.layer_size_weighting",
    )
    layer_size_weighting_enabled = require_int(
        layer_size_weighting.get("enabled"),
        path="gameplay.clear_scoring.layer_size_weighting.enabled",
        min_value=0,
        max_value=1,
    )
    layer_size_weighting_reference_plane_cells = require_int(
        layer_size_weighting.get("reference_plane_cells"),
        path="gameplay.clear_scoring.layer_size_weighting.reference_plane_cells",
        min_value=1,
    )
    return {
        "multi_layer_bonus": {
            "2": tier_two,
            "3": tier_three,
            "4": tier_four,
            "5_plus": tier_five_plus,
        },
        "board_clear_bonus": board_clear_bonus,
        "layer_size_weighting": {
            "enabled": layer_size_weighting_enabled,
            "reference_plane_cells": layer_size_weighting_reference_plane_cells,
        },
    }


def validate_gameplay_tuning_payload(payload: dict[str, Any]) -> dict[str, Any]:
    require_int(payload.get("version"), path="gameplay.version", min_value=1)
    rotation_kicks = _validate_rotation_kicks(payload.get("rotation_kicks"))
    return {
        "version": payload["version"],
        "speed_curve": _validate_speed_curve(payload.get("speed_curve")),
        "challenge_prefill": _validate_challenge_prefill(
            payload.get("challenge_prefill")
        ),
        "assist_scoring": _validate_assist_scoring(
            payload.get("assist_scoring"),
            kick_level_order=rotation_kicks["level_order"],
        ),
        "rotation_kicks": rotation_kicks,
        "clear_scoring": _validate_clear_scoring(payload.get("clear_scoring")),
        "grid_modes": _validate_grid_modes(payload.get("grid_modes")),
    }
