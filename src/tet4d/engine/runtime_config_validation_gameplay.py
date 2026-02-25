from __future__ import annotations

from typing import Any

from .runtime_config_validation_shared import (
    BOT_MODE_NAMES,
    GRID_MODE_NAMES,
    require_int,
    require_number,
    require_object,
)


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
            speed_obj.get("base"),
            path="gameplay.assist_scoring.speed.base",
        ),
        "per_level": require_number(
            speed_obj.get("per_level"),
            path="gameplay.assist_scoring.speed.per_level",
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
    combined = {
        "min": combined_min,
        "max": combined_max,
    }

    return {
        "bot_factors": bot_factors,
        "grid_factors": grid_factors,
        "speed": speed,
        "combined": combined,
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
                f"gameplay.grid_modes.cycle[{idx}] must be one of: {', '.join(GRID_MODE_NAMES)}"
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
    return {
        "cycle": tuple(cycle),
        "fallback": fallback_mode,
    }


def validate_gameplay_tuning_payload(payload: dict[str, Any]) -> dict[str, Any]:
    require_int(payload.get("version"), path="gameplay.version", min_value=1)

    speed_curve = _validate_speed_curve(payload.get("speed_curve"))
    challenge_prefill = _validate_challenge_prefill(payload.get("challenge_prefill"))
    assist_scoring = _validate_assist_scoring(payload.get("assist_scoring"))
    grid_modes = _validate_grid_modes(payload.get("grid_modes"))

    return {
        "version": payload["version"],
        "speed_curve": speed_curve,
        "challenge_prefill": challenge_prefill,
        "assist_scoring": assist_scoring,
        "grid_modes": grid_modes,
    }
