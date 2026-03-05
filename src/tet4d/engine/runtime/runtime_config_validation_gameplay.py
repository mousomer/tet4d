from __future__ import annotations

from typing import Any

from .settings_schema import (
    BOT_MODE_NAMES,
    GRID_MODE_NAMES,
    require_int,
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


def _validate_assist_scoring(raw_assist: object) -> dict[str, Any]:
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
        "speed": speed,
        "combined": {"min": combined_min, "max": combined_max},
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
    return {
        "version": payload["version"],
        "speed_curve": _validate_speed_curve(payload.get("speed_curve")),
        "challenge_prefill": _validate_challenge_prefill(
            payload.get("challenge_prefill")
        ),
        "assist_scoring": _validate_assist_scoring(payload.get("assist_scoring")),
        "clear_scoring": _validate_clear_scoring(payload.get("clear_scoring")),
        "grid_modes": _validate_grid_modes(payload.get("grid_modes")),
    }
