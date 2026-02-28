from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from .project_config import (
    playbot_history_file_default_path,
    playbot_history_file_default_relative,
    project_root_path,
    resolve_state_relative_path,
)
from .runtime_config_validation_playbot import validate_playbot_policy_payload
from .settings_schema import (
    BOT_MODE_NAMES,
    GRID_MODE_NAMES,
    read_json_object_or_raise,
    require_int,
    require_number,
    require_object,
)


CONFIG_DIR = project_root_path() / "config"
GAMEPLAY_TUNING_FILE = CONFIG_DIR / "gameplay" / "tuning.json"
PLAYBOT_POLICY_FILE = CONFIG_DIR / "playbot" / "policy.json"
AUDIO_SFX_FILE = CONFIG_DIR / "audio" / "sfx.json"
DEFAULT_PLAYBOT_HISTORY_FILE = playbot_history_file_default_relative()


def _read_json_payload(path: Path) -> dict[str, Any]:
    return read_json_object_or_raise(path)


def _dimension_bucket_key(ndim: int) -> str:
    if ndim <= 2:
        return "2d"
    if ndim == 3:
        return "3d"
    return "4d_plus"


def _normalized_name(value: str) -> str:
    return value.strip().lower()


def _bucket_lookup(mapping: dict[str, Any], ndim: int) -> Any:
    return mapping[_dimension_bucket_key(ndim)]


def _validate_audio_sfx_payload(payload: dict[str, Any]) -> dict[str, Any]:
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
                "gameplay.grid_modes.cycle[{idx}] must be one of: "
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


def _validate_gameplay_tuning_payload(payload: dict[str, Any]) -> dict[str, Any]:
    require_int(payload.get("version"), path="gameplay.version", min_value=1)
    return {
        "version": payload["version"],
        "speed_curve": _validate_speed_curve(payload.get("speed_curve")),
        "challenge_prefill": _validate_challenge_prefill(
            payload.get("challenge_prefill")
        ),
        "assist_scoring": _validate_assist_scoring(payload.get("assist_scoring")),
        "grid_modes": _validate_grid_modes(payload.get("grid_modes")),
    }


@lru_cache(maxsize=1)
def _gameplay_tuning() -> dict[str, Any]:
    payload = _read_json_payload(GAMEPLAY_TUNING_FILE)
    return _validate_gameplay_tuning_payload(payload)


@lru_cache(maxsize=1)
def _playbot_policy() -> dict[str, Any]:
    payload = _read_json_payload(PLAYBOT_POLICY_FILE)
    return validate_playbot_policy_payload(payload)


@lru_cache(maxsize=1)
def _audio_sfx() -> dict[str, Any]:
    payload = _read_json_payload(AUDIO_SFX_FILE)
    return _validate_audio_sfx_payload(payload)


def gameplay_tuning_payload() -> dict[str, Any]:
    return deepcopy(_gameplay_tuning())


def speed_curve_for_dimension(dimension: int) -> tuple[int, int]:
    config = _gameplay_tuning()["speed_curve"]
    key = _dimension_bucket_key(dimension)
    return config[key]["base_ms"], config[key]["min_ms"]


def challenge_prefill_ratio(dimension: int) -> float:
    challenge = _gameplay_tuning()["challenge_prefill"]
    if dimension <= 2:
        return challenge["2d_fill_ratio"]
    return challenge["nd_fill_ratio"]


def assist_bot_factor(mode_name: str) -> float:
    factors = _gameplay_tuning()["assist_scoring"]["bot_factors"]
    normalized = _normalized_name(mode_name)
    return float(factors.get(normalized, factors["off"]))


def assist_grid_factor(mode_name: str) -> float:
    factors = _gameplay_tuning()["assist_scoring"]["grid_factors"]
    normalized = _normalized_name(mode_name)
    return float(factors.get(normalized, factors["off"]))


def assist_speed_formula() -> tuple[float, float, int, int]:
    speed = _gameplay_tuning()["assist_scoring"]["speed"]
    return (
        float(speed["base"]),
        float(speed["per_level"]),
        int(speed["min_level"]),
        int(speed["max_level"]),
    )


def assist_combined_bounds() -> tuple[float, float]:
    combined = _gameplay_tuning()["assist_scoring"]["combined"]
    return float(combined["min"]), float(combined["max"])


def grid_mode_cycle_names() -> tuple[str, ...]:
    return tuple(_gameplay_tuning()["grid_modes"]["cycle"])


def grid_mode_fallback_name() -> str:
    return str(_gameplay_tuning()["grid_modes"]["fallback"])


def playbot_budget_table_for_ndim(ndim: int) -> tuple[int, int, int, int]:
    bucket = _bucket_lookup(_playbot_policy()["budget_ms"], ndim)
    return bucket["fast"], bucket["balanced"], bucket["deep"], bucket["ultra"]


def playbot_board_size_scaling_policy_for_ndim(
    ndim: int,
) -> tuple[int, float, float, float]:
    scaling = _playbot_policy()["board_size_scaling"]
    return (
        int(_bucket_lookup(scaling["reference_cells"], ndim)),
        float(scaling["min_scale"]),
        float(scaling["max_scale"]),
        float(scaling["exponent"]),
    )


def playbot_clamp_policy() -> tuple[int, int, int, int]:
    clamp = _playbot_policy()["clamp"]
    return (
        clamp["floor_divisor"],
        clamp["floor_min"],
        clamp["ceil_multiplier"],
        clamp["ceil_min"],
    )


def playbot_lookahead_depth(ndim: int, profile_name: str) -> int:
    depth = _playbot_policy()["lookahead"]["depth"]
    normalized = _normalized_name(profile_name)
    if normalized == "fast":
        return depth["fast"]
    if ndim >= 4:
        return depth["all_4d_plus"]
    if normalized == "ultra":
        return depth["ultra_2d_3d"]
    if normalized == "deep":
        return depth["deep_2d_3d"]
    return depth["balanced_2d_3d"]


def playbot_lookahead_top_k(ndim: int, profile_name: str, depth_value: int) -> int:
    top_k = _playbot_policy()["lookahead"]["top_k"]
    if depth_value <= 1:
        return top_k["depth_lte_one"]
    normalized = _normalized_name(profile_name)
    if ndim <= 2:
        if normalized == "ultra":
            return top_k["ultra_2d"]
        if normalized == "deep":
            return top_k["deep_2d"]
        return top_k["balanced_2d"]
    if normalized == "ultra":
        return top_k["ultra_3d_plus"]
    if normalized == "deep":
        return top_k["deep_3d_plus"]
    return top_k["balanced_3d_plus"]


def playbot_adaptive_fallback_enabled() -> bool:
    return bool(_playbot_policy()["adaptive_fallback"]["enabled"])


def playbot_adaptive_lookahead_min_budget_ms(ndim: int) -> int:
    lookup = _playbot_policy()["adaptive_fallback"]["lookahead_min_budget_ms"]
    return int(_bucket_lookup(lookup, ndim))


def playbot_adaptive_candidate_cap_for_ndim(ndim: int) -> tuple[float, int, int]:
    cap_obj = _bucket_lookup(
        _playbot_policy()["adaptive_fallback"]["candidate_cap"], ndim
    )
    return float(cap_obj["per_ms"]), int(cap_obj["min"]), int(cap_obj["max"])


def playbot_deadline_safety_ms() -> float:
    return float(_playbot_policy()["adaptive_fallback"]["deadline_safety_ms"])


def playbot_auto_algorithm_policy_for_ndim(
    ndim: int,
) -> tuple[float, float, float, float]:
    auto_obj = _playbot_policy()["auto_algorithm"]
    key = _dimension_bucket_key(ndim)
    return (
        float(auto_obj["greedy_bias"][key]),
        float(auto_obj["density_weight"]),
        float(auto_obj["lines_cleared_weight"]),
        float(auto_obj["threshold"]),
    )


def playbot_benchmark_p95_thresholds() -> dict[str, float]:
    thresholds = _playbot_policy()["benchmark"]["p95_threshold_ms"]
    return {
        "2d": float(thresholds["2d"]),
        "3d": float(thresholds["3d"]),
        "4d": float(thresholds["4d"]),
    }


def playbot_benchmark_history_file() -> Path:
    raw = _playbot_policy()["benchmark"]["history_file"]
    default_path = playbot_history_file_default_path()
    text = str(raw).strip()
    if not text:
        return default_path
    return resolve_state_relative_path(
        text,
        default_relative=DEFAULT_PLAYBOT_HISTORY_FILE,
    )


def playbot_default_hard_drop_after_soft_drops() -> int:
    return int(_playbot_policy()["controller"]["hard_drop_after_soft_drops"])


def playbot_dry_run_defaults() -> tuple[int, int]:
    dry_run = _playbot_policy()["dry_run"]
    return int(dry_run["default_pieces"]), int(dry_run["default_seed"])


def audio_event_specs() -> dict[str, tuple[float, int, float]]:
    events = _audio_sfx()["events"]
    specs: dict[str, tuple[float, int, float]] = {}
    for event_name, spec in events.items():
        specs[event_name] = (
            float(spec["frequency_hz"]),
            int(spec["duration_ms"]),
            float(spec["amplitude"]),
        )
    return specs
