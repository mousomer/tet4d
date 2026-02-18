from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
GAMEPLAY_TUNING_FILE = CONFIG_DIR / "gameplay" / "tuning.json"
PLAYBOT_POLICY_FILE = CONFIG_DIR / "playbot" / "policy.json"
AUDIO_SFX_FILE = CONFIG_DIR / "audio" / "sfx.json"

_GRID_MODE_NAMES = ("off", "edge", "full", "helper")
_BOT_MODE_NAMES = ("off", "assist", "auto", "step")
_BOT_PROFILE_NAMES = ("fast", "balanced", "deep", "ultra")


def _dimension_bucket_key(ndim: int) -> str:
    if ndim <= 2:
        return "2d"
    if ndim == 3:
        return "3d"
    return "4d_plus"


def _read_json_payload(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - runtime failure path
        raise RuntimeError(f"Failed reading config file {path}: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in config file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Config file {path} must contain a JSON object")
    return payload


def _require_int(
    value: object,
    *,
    path: str,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError(f"{path} must be an integer")
    if min_value is not None and value < min_value:
        raise RuntimeError(f"{path} must be >= {min_value}")
    if max_value is not None and value > max_value:
        raise RuntimeError(f"{path} must be <= {max_value}")
    return value


def _require_number(
    value: object,
    *,
    path: str,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{path} must be a number")
    num = float(value)
    if min_value is not None and num < min_value:
        raise RuntimeError(f"{path} must be >= {min_value}")
    if max_value is not None and num > max_value:
        raise RuntimeError(f"{path} must be <= {max_value}")
    return num


def _require_object(value: object, *, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must be an object")
    return value


def _validate_gameplay_tuning_payload(payload: dict[str, Any]) -> dict[str, Any]:
    _require_int(payload.get("version"), path="gameplay.version", min_value=1)

    speed_curve = _require_object(payload.get("speed_curve"), path="gameplay.speed_curve")
    validated_speed_curve: dict[str, dict[str, int]] = {}
    for key in ("2d", "3d", "4d_plus"):
        entry = _require_object(speed_curve.get(key), path=f"gameplay.speed_curve.{key}")
        validated_speed_curve[key] = {
            "base_ms": _require_int(
                entry.get("base_ms"),
                path=f"gameplay.speed_curve.{key}.base_ms",
                min_value=1,
            ),
            "min_ms": _require_int(
                entry.get("min_ms"),
                path=f"gameplay.speed_curve.{key}.min_ms",
                min_value=1,
            ),
        }

    challenge = _require_object(payload.get("challenge_prefill"), path="gameplay.challenge_prefill")
    challenge_2d = _require_number(
        challenge.get("2d_fill_ratio"),
        path="gameplay.challenge_prefill.2d_fill_ratio",
        min_value=0.0,
        max_value=1.0,
    )
    challenge_nd = _require_number(
        challenge.get("nd_fill_ratio"),
        path="gameplay.challenge_prefill.nd_fill_ratio",
        min_value=0.0,
        max_value=1.0,
    )

    assist = _require_object(payload.get("assist_scoring"), path="gameplay.assist_scoring")

    bot_factors_obj = _require_object(assist.get("bot_factors"), path="gameplay.assist_scoring.bot_factors")
    bot_factors: dict[str, float] = {}
    for mode_name in _BOT_MODE_NAMES:
        bot_factors[mode_name] = _require_number(
            bot_factors_obj.get(mode_name),
            path=f"gameplay.assist_scoring.bot_factors.{mode_name}",
            min_value=0.0,
            max_value=1.0,
        )

    grid_factors_obj = _require_object(assist.get("grid_factors"), path="gameplay.assist_scoring.grid_factors")
    grid_factors: dict[str, float] = {}
    for mode_name in _GRID_MODE_NAMES:
        grid_factors[mode_name] = _require_number(
            grid_factors_obj.get(mode_name),
            path=f"gameplay.assist_scoring.grid_factors.{mode_name}",
            min_value=0.0,
            max_value=1.0,
        )

    speed_obj = _require_object(assist.get("speed"), path="gameplay.assist_scoring.speed")
    speed_base = _require_number(
        speed_obj.get("base"),
        path="gameplay.assist_scoring.speed.base",
    )
    speed_step = _require_number(
        speed_obj.get("per_level"),
        path="gameplay.assist_scoring.speed.per_level",
    )
    speed_min_level = _require_int(
        speed_obj.get("min_level"),
        path="gameplay.assist_scoring.speed.min_level",
        min_value=1,
    )
    speed_max_level = _require_int(
        speed_obj.get("max_level"),
        path="gameplay.assist_scoring.speed.max_level",
        min_value=speed_min_level,
    )

    combined_obj = _require_object(assist.get("combined"), path="gameplay.assist_scoring.combined")
    combined_min = _require_number(
        combined_obj.get("min"),
        path="gameplay.assist_scoring.combined.min",
    )
    combined_max = _require_number(
        combined_obj.get("max"),
        path="gameplay.assist_scoring.combined.max",
        min_value=combined_min,
    )

    grid_modes = _require_object(payload.get("grid_modes"), path="gameplay.grid_modes")
    raw_cycle = grid_modes.get("cycle")
    if not isinstance(raw_cycle, list) or not raw_cycle:
        raise RuntimeError("gameplay.grid_modes.cycle must be a non-empty list")
    cycle: list[str] = []
    for idx, mode_name in enumerate(raw_cycle):
        if not isinstance(mode_name, str):
            raise RuntimeError(f"gameplay.grid_modes.cycle[{idx}] must be a string")
        normalized = mode_name.strip().lower()
        if normalized not in _GRID_MODE_NAMES:
            raise RuntimeError(
                f"gameplay.grid_modes.cycle[{idx}] must be one of: {', '.join(_GRID_MODE_NAMES)}"
            )
        cycle.append(normalized)
    fallback = grid_modes.get("fallback")
    if not isinstance(fallback, str):
        raise RuntimeError("gameplay.grid_modes.fallback must be a string")
    fallback_mode = fallback.strip().lower()
    if fallback_mode not in cycle:
        raise RuntimeError("gameplay.grid_modes.fallback must be present in gameplay.grid_modes.cycle")

    return {
        "version": payload["version"],
        "speed_curve": validated_speed_curve,
        "challenge_prefill": {
            "2d_fill_ratio": challenge_2d,
            "nd_fill_ratio": challenge_nd,
        },
        "assist_scoring": {
            "bot_factors": bot_factors,
            "grid_factors": grid_factors,
            "speed": {
                "base": speed_base,
                "per_level": speed_step,
                "min_level": speed_min_level,
                "max_level": speed_max_level,
            },
            "combined": {
                "min": combined_min,
                "max": combined_max,
            },
        },
        "grid_modes": {
            "cycle": tuple(cycle),
            "fallback": fallback_mode,
        },
    }


def _validate_playbot_policy_payload(payload: dict[str, Any]) -> dict[str, Any]:
    _require_int(payload.get("version"), path="playbot.version", min_value=1)

    budget_obj = _require_object(payload.get("budget_ms"), path="playbot.budget_ms")
    budgets: dict[str, dict[str, int]] = {}
    for dim_key in ("2d", "3d", "4d_plus"):
        raw_dim = _require_object(budget_obj.get(dim_key), path=f"playbot.budget_ms.{dim_key}")
        dim_budget: dict[str, int] = {}
        for profile_name in _BOT_PROFILE_NAMES:
            dim_budget[profile_name] = _require_int(
                raw_dim.get(profile_name),
                path=f"playbot.budget_ms.{dim_key}.{profile_name}",
                min_value=1,
            )
        budgets[dim_key] = dim_budget

    scaling_obj = _require_object(payload.get("board_size_scaling"), path="playbot.board_size_scaling")
    reference_cells_obj = _require_object(
        scaling_obj.get("reference_cells"),
        path="playbot.board_size_scaling.reference_cells",
    )
    reference_cells = {
        "2d": _require_int(
            reference_cells_obj.get("2d"),
            path="playbot.board_size_scaling.reference_cells.2d",
            min_value=1,
        ),
        "3d": _require_int(
            reference_cells_obj.get("3d"),
            path="playbot.board_size_scaling.reference_cells.3d",
            min_value=1,
        ),
        "4d_plus": _require_int(
            reference_cells_obj.get("4d_plus"),
            path="playbot.board_size_scaling.reference_cells.4d_plus",
            min_value=1,
        ),
    }
    min_scale = _require_number(
        scaling_obj.get("min_scale"),
        path="playbot.board_size_scaling.min_scale",
        min_value=0.1,
    )
    max_scale = _require_number(
        scaling_obj.get("max_scale"),
        path="playbot.board_size_scaling.max_scale",
        min_value=min_scale,
    )
    exponent = _require_number(
        scaling_obj.get("exponent"),
        path="playbot.board_size_scaling.exponent",
        min_value=0.1,
        max_value=2.0,
    )

    clamp_obj = _require_object(payload.get("clamp"), path="playbot.clamp")
    clamp = {
        "floor_divisor": _require_int(
            clamp_obj.get("floor_divisor"),
            path="playbot.clamp.floor_divisor",
            min_value=1,
        ),
        "floor_min": _require_int(
            clamp_obj.get("floor_min"),
            path="playbot.clamp.floor_min",
            min_value=0,
        ),
        "ceil_multiplier": _require_int(
            clamp_obj.get("ceil_multiplier"),
            path="playbot.clamp.ceil_multiplier",
            min_value=1,
        ),
        "ceil_min": _require_int(
            clamp_obj.get("ceil_min"),
            path="playbot.clamp.ceil_min",
            min_value=1,
        ),
    }

    lookahead_obj = _require_object(payload.get("lookahead"), path="playbot.lookahead")
    depth_obj = _require_object(lookahead_obj.get("depth"), path="playbot.lookahead.depth")
    top_k_obj = _require_object(lookahead_obj.get("top_k"), path="playbot.lookahead.top_k")
    depth = {
        "fast": _require_int(depth_obj.get("fast"), path="playbot.lookahead.depth.fast", min_value=1),
        "balanced_2d_3d": _require_int(
            depth_obj.get("balanced_2d_3d"),
            path="playbot.lookahead.depth.balanced_2d_3d",
            min_value=1,
        ),
        "deep_2d_3d": _require_int(
            depth_obj.get("deep_2d_3d"),
            path="playbot.lookahead.depth.deep_2d_3d",
            min_value=1,
        ),
        "ultra_2d_3d": _require_int(
            depth_obj.get("ultra_2d_3d"),
            path="playbot.lookahead.depth.ultra_2d_3d",
            min_value=1,
        ),
        "all_4d_plus": _require_int(
            depth_obj.get("all_4d_plus"),
            path="playbot.lookahead.depth.all_4d_plus",
            min_value=1,
        ),
    }
    top_k = {
        "depth_lte_one": _require_int(
            top_k_obj.get("depth_lte_one"),
            path="playbot.lookahead.top_k.depth_lte_one",
            min_value=1,
        ),
        "balanced_2d": _require_int(
            top_k_obj.get("balanced_2d"),
            path="playbot.lookahead.top_k.balanced_2d",
            min_value=1,
        ),
        "deep_2d": _require_int(
            top_k_obj.get("deep_2d"),
            path="playbot.lookahead.top_k.deep_2d",
            min_value=1,
        ),
        "ultra_2d": _require_int(
            top_k_obj.get("ultra_2d"),
            path="playbot.lookahead.top_k.ultra_2d",
            min_value=1,
        ),
        "balanced_3d_plus": _require_int(
            top_k_obj.get("balanced_3d_plus"),
            path="playbot.lookahead.top_k.balanced_3d_plus",
            min_value=1,
        ),
        "deep_3d_plus": _require_int(
            top_k_obj.get("deep_3d_plus"),
            path="playbot.lookahead.top_k.deep_3d_plus",
            min_value=1,
        ),
        "ultra_3d_plus": _require_int(
            top_k_obj.get("ultra_3d_plus"),
            path="playbot.lookahead.top_k.ultra_3d_plus",
            min_value=1,
        ),
    }

    adaptive_obj = _require_object(payload.get("adaptive_fallback"), path="playbot.adaptive_fallback")
    adaptive_enabled = adaptive_obj.get("enabled")
    if not isinstance(adaptive_enabled, bool):
        raise RuntimeError("playbot.adaptive_fallback.enabled must be a boolean")

    lookahead_min_obj = _require_object(
        adaptive_obj.get("lookahead_min_budget_ms"),
        path="playbot.adaptive_fallback.lookahead_min_budget_ms",
    )
    lookahead_min_budget_ms = {
        "2d": _require_int(
            lookahead_min_obj.get("2d"),
            path="playbot.adaptive_fallback.lookahead_min_budget_ms.2d",
            min_value=1,
        ),
        "3d": _require_int(
            lookahead_min_obj.get("3d"),
            path="playbot.adaptive_fallback.lookahead_min_budget_ms.3d",
            min_value=1,
        ),
        "4d_plus": _require_int(
            lookahead_min_obj.get("4d_plus"),
            path="playbot.adaptive_fallback.lookahead_min_budget_ms.4d_plus",
            min_value=1,
        ),
    }

    candidate_cap_obj = _require_object(
        adaptive_obj.get("candidate_cap"),
        path="playbot.adaptive_fallback.candidate_cap",
    )
    candidate_cap: dict[str, dict[str, float | int]] = {}
    for dim_key in ("2d", "3d", "4d_plus"):
        dim_cap_obj = _require_object(
            candidate_cap_obj.get(dim_key),
            path=f"playbot.adaptive_fallback.candidate_cap.{dim_key}",
        )
        candidate_cap[dim_key] = {
            "per_ms": _require_number(
                dim_cap_obj.get("per_ms"),
                path=f"playbot.adaptive_fallback.candidate_cap.{dim_key}.per_ms",
                min_value=0.1,
            ),
            "min": _require_int(
                dim_cap_obj.get("min"),
                path=f"playbot.adaptive_fallback.candidate_cap.{dim_key}.min",
                min_value=1,
            ),
            "max": _require_int(
                dim_cap_obj.get("max"),
                path=f"playbot.adaptive_fallback.candidate_cap.{dim_key}.max",
                min_value=1,
            ),
        }
        if candidate_cap[dim_key]["max"] < candidate_cap[dim_key]["min"]:
            raise RuntimeError(
                f"playbot.adaptive_fallback.candidate_cap.{dim_key}.max must be >= min"
            )

    deadline_safety_ms = _require_number(
        adaptive_obj.get("deadline_safety_ms"),
        path="playbot.adaptive_fallback.deadline_safety_ms",
        min_value=0.0,
    )

    auto_obj = _require_object(payload.get("auto_algorithm"), path="playbot.auto_algorithm")
    greedy_bias_obj = _require_object(
        auto_obj.get("greedy_bias"),
        path="playbot.auto_algorithm.greedy_bias",
    )
    greedy_bias = {
        "2d": _require_number(
            greedy_bias_obj.get("2d"),
            path="playbot.auto_algorithm.greedy_bias.2d",
        ),
        "3d": _require_number(
            greedy_bias_obj.get("3d"),
            path="playbot.auto_algorithm.greedy_bias.3d",
        ),
        "4d_plus": _require_number(
            greedy_bias_obj.get("4d_plus"),
            path="playbot.auto_algorithm.greedy_bias.4d_plus",
        ),
    }
    density_weight = _require_number(
        auto_obj.get("density_weight"),
        path="playbot.auto_algorithm.density_weight",
    )
    lines_cleared_weight = _require_number(
        auto_obj.get("lines_cleared_weight"),
        path="playbot.auto_algorithm.lines_cleared_weight",
    )
    threshold = _require_number(
        auto_obj.get("threshold"),
        path="playbot.auto_algorithm.threshold",
    )

    benchmark_obj = _require_object(payload.get("benchmark"), path="playbot.benchmark")
    thresholds_obj = _require_object(
        benchmark_obj.get("p95_threshold_ms"),
        path="playbot.benchmark.p95_threshold_ms",
    )
    benchmark_thresholds = {
        "2d": _require_number(
            thresholds_obj.get("2d"),
            path="playbot.benchmark.p95_threshold_ms.2d",
            min_value=1.0,
        ),
        "3d": _require_number(
            thresholds_obj.get("3d"),
            path="playbot.benchmark.p95_threshold_ms.3d",
            min_value=1.0,
        ),
        "4d": _require_number(
            thresholds_obj.get("4d"),
            path="playbot.benchmark.p95_threshold_ms.4d",
            min_value=1.0,
        ),
    }
    history_file = benchmark_obj.get("history_file")
    if not isinstance(history_file, str) or not history_file.strip():
        raise RuntimeError("playbot.benchmark.history_file must be a non-empty string")

    controller_obj = _require_object(payload.get("controller"), path="playbot.controller")
    controller = {
        "hard_drop_after_soft_drops": _require_int(
            controller_obj.get("hard_drop_after_soft_drops"),
            path="playbot.controller.hard_drop_after_soft_drops",
            min_value=0,
        ),
    }

    dry_run_obj = _require_object(payload.get("dry_run"), path="playbot.dry_run")
    dry_run = {
        "default_pieces": _require_int(
            dry_run_obj.get("default_pieces"),
            path="playbot.dry_run.default_pieces",
            min_value=1,
        ),
        "default_seed": _require_int(
            dry_run_obj.get("default_seed"),
            path="playbot.dry_run.default_seed",
        ),
    }

    return {
        "version": payload["version"],
        "budget_ms": budgets,
        "board_size_scaling": {
            "reference_cells": reference_cells,
            "min_scale": min_scale,
            "max_scale": max_scale,
            "exponent": exponent,
        },
        "clamp": clamp,
        "lookahead": {
            "depth": depth,
            "top_k": top_k,
        },
        "adaptive_fallback": {
            "enabled": adaptive_enabled,
            "lookahead_min_budget_ms": lookahead_min_budget_ms,
            "candidate_cap": candidate_cap,
            "deadline_safety_ms": deadline_safety_ms,
        },
        "auto_algorithm": {
            "greedy_bias": greedy_bias,
            "density_weight": density_weight,
            "lines_cleared_weight": lines_cleared_weight,
            "threshold": threshold,
        },
        "benchmark": {
            "p95_threshold_ms": benchmark_thresholds,
            "history_file": history_file.strip(),
        },
        "controller": controller,
        "dry_run": dry_run,
    }


def _validate_audio_sfx_payload(payload: dict[str, Any]) -> dict[str, Any]:
    _require_int(payload.get("version"), path="audio.version", min_value=1)

    events_obj = _require_object(payload.get("events"), path="audio.events")
    if not events_obj:
        raise RuntimeError("audio.events must not be empty")

    events: dict[str, dict[str, float | int]] = {}
    for event_name, raw_spec in events_obj.items():
        if not isinstance(event_name, str) or not event_name.strip():
            raise RuntimeError("audio.events keys must be non-empty strings")
        spec = _require_object(raw_spec, path=f"audio.events.{event_name}")
        events[event_name] = {
            "frequency_hz": _require_number(
                spec.get("frequency_hz"),
                path=f"audio.events.{event_name}.frequency_hz",
                min_value=1.0,
            ),
            "duration_ms": _require_int(
                spec.get("duration_ms"),
                path=f"audio.events.{event_name}.duration_ms",
                min_value=1,
            ),
            "amplitude": _require_number(
                spec.get("amplitude"),
                path=f"audio.events.{event_name}.amplitude",
                min_value=0.0,
                max_value=1.0,
            ),
        }
    return {
        "version": payload["version"],
        "events": events,
    }


@lru_cache(maxsize=1)
def _gameplay_tuning() -> dict[str, Any]:
    payload = _read_json_payload(GAMEPLAY_TUNING_FILE)
    return _validate_gameplay_tuning_payload(payload)


@lru_cache(maxsize=1)
def _playbot_policy() -> dict[str, Any]:
    payload = _read_json_payload(PLAYBOT_POLICY_FILE)
    return _validate_playbot_policy_payload(payload)


@lru_cache(maxsize=1)
def _audio_sfx() -> dict[str, Any]:
    payload = _read_json_payload(AUDIO_SFX_FILE)
    return _validate_audio_sfx_payload(payload)


def gameplay_tuning_payload() -> dict[str, Any]:
    return deepcopy(_gameplay_tuning())


def playbot_policy_payload() -> dict[str, Any]:
    return deepcopy(_playbot_policy())


def audio_sfx_payload() -> dict[str, Any]:
    return deepcopy(_audio_sfx())


def speed_curve_for_dimension(dimension: int) -> tuple[int, int]:
    config = _gameplay_tuning()["speed_curve"]
    if dimension <= 2:
        key = "2d"
    elif dimension == 3:
        key = "3d"
    else:
        key = "4d_plus"
    return config[key]["base_ms"], config[key]["min_ms"]


def challenge_prefill_ratio(dimension: int) -> float:
    challenge = _gameplay_tuning()["challenge_prefill"]
    if dimension <= 2:
        return challenge["2d_fill_ratio"]
    return challenge["nd_fill_ratio"]


def assist_bot_factor(mode_name: str) -> float:
    factors = _gameplay_tuning()["assist_scoring"]["bot_factors"]
    normalized = mode_name.strip().lower()
    return float(factors.get(normalized, factors["off"]))


def assist_grid_factor(mode_name: str) -> float:
    factors = _gameplay_tuning()["assist_scoring"]["grid_factors"]
    normalized = mode_name.strip().lower()
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
    config = _playbot_policy()["budget_ms"]
    bucket = config[_dimension_bucket_key(ndim)]
    return bucket["fast"], bucket["balanced"], bucket["deep"], bucket["ultra"]


def playbot_board_size_scaling_policy_for_ndim(ndim: int) -> tuple[int, float, float, float]:
    scaling = _playbot_policy()["board_size_scaling"]
    key = _dimension_bucket_key(ndim)
    return (
        int(scaling["reference_cells"][key]),
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
    normalized = profile_name.strip().lower()
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
    normalized = profile_name.strip().lower()
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
    return int(lookup[_dimension_bucket_key(ndim)])


def playbot_adaptive_candidate_cap_for_ndim(ndim: int) -> tuple[float, int, int]:
    cap_obj = _playbot_policy()["adaptive_fallback"]["candidate_cap"][_dimension_bucket_key(ndim)]
    return float(cap_obj["per_ms"]), int(cap_obj["min"]), int(cap_obj["max"])


def playbot_deadline_safety_ms() -> float:
    return float(_playbot_policy()["adaptive_fallback"]["deadline_safety_ms"])


def playbot_auto_algorithm_policy_for_ndim(ndim: int) -> tuple[float, float, float, float]:
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
    raw = str(_playbot_policy()["benchmark"]["history_file"])
    path = Path(raw)
    if path.is_absolute():
        return path
    return CONFIG_DIR.parent / path


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
