from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_GRID_MODE_NAMES = ("off", "edge", "full", "helper")
_BOT_MODE_NAMES = ("off", "assist", "auto", "step")
_BOT_PROFILE_NAMES = ("fast", "balanced", "deep", "ultra")


def _require_state_relative_path(value: object, *, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{path} must be a non-empty string")
    normalized = value.strip().replace("\\", "/")
    candidate = Path(normalized)
    if candidate.is_absolute():
        raise RuntimeError(f"{path} must be a relative path under state/")
    parts = [part for part in candidate.parts if part not in ("", ".")]
    if not parts:
        raise RuntimeError(f"{path} must be a relative path under state/")
    if any(part == ".." for part in parts):
        raise RuntimeError(f"{path} must not contain '..'")
    if any(":" in part for part in parts):
        raise RuntimeError(f"{path} must not contain ':' path segments")
    clean = "/".join(parts)
    if not clean.startswith("state/"):
        raise RuntimeError(f"{path} must be under state/")
    return clean


def read_json_payload(path: Path) -> dict[str, Any]:
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


def validate_gameplay_tuning_payload(payload: dict[str, Any]) -> dict[str, Any]:
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


def _validate_playbot_budget(raw_budget: object) -> dict[str, dict[str, int]]:
    budget_obj = _require_object(raw_budget, path="playbot.budget_ms")
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
    return budgets


def _validate_playbot_board_size_scaling(raw_scaling: object) -> dict[str, Any]:
    scaling_obj = _require_object(raw_scaling, path="playbot.board_size_scaling")
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
    return {
        "reference_cells": reference_cells,
        "min_scale": min_scale,
        "max_scale": max_scale,
        "exponent": exponent,
    }


def _validate_playbot_clamp(raw_clamp: object) -> dict[str, int]:
    clamp_obj = _require_object(raw_clamp, path="playbot.clamp")
    return {
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


def _validate_playbot_lookahead(raw_lookahead: object) -> dict[str, dict[str, int]]:
    lookahead_obj = _require_object(raw_lookahead, path="playbot.lookahead")
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
    return {"depth": depth, "top_k": top_k}


def _validate_playbot_adaptive_fallback(raw_adaptive: object) -> dict[str, Any]:
    adaptive_obj = _require_object(raw_adaptive, path="playbot.adaptive_fallback")
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
    return {
        "enabled": adaptive_enabled,
        "lookahead_min_budget_ms": lookahead_min_budget_ms,
        "candidate_cap": candidate_cap,
        "deadline_safety_ms": deadline_safety_ms,
    }


def _validate_playbot_auto_algorithm(raw_auto: object) -> dict[str, Any]:
    auto_obj = _require_object(raw_auto, path="playbot.auto_algorithm")
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
    return {
        "greedy_bias": greedy_bias,
        "density_weight": _require_number(
            auto_obj.get("density_weight"),
            path="playbot.auto_algorithm.density_weight",
        ),
        "lines_cleared_weight": _require_number(
            auto_obj.get("lines_cleared_weight"),
            path="playbot.auto_algorithm.lines_cleared_weight",
        ),
        "threshold": _require_number(
            auto_obj.get("threshold"),
            path="playbot.auto_algorithm.threshold",
        ),
    }


def _validate_playbot_benchmark(raw_benchmark: object) -> dict[str, Any]:
    benchmark_obj = _require_object(raw_benchmark, path="playbot.benchmark")
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
    history_file = _require_state_relative_path(
        benchmark_obj.get("history_file"),
        path="playbot.benchmark.history_file",
    )
    return {
        "p95_threshold_ms": benchmark_thresholds,
        "history_file": history_file,
    }


def _validate_playbot_controller(raw_controller: object) -> dict[str, int]:
    controller_obj = _require_object(raw_controller, path="playbot.controller")
    return {
        "hard_drop_after_soft_drops": _require_int(
            controller_obj.get("hard_drop_after_soft_drops"),
            path="playbot.controller.hard_drop_after_soft_drops",
            min_value=0,
        ),
    }


def _validate_playbot_dry_run(raw_dry_run: object) -> dict[str, int]:
    dry_run_obj = _require_object(raw_dry_run, path="playbot.dry_run")
    return {
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


def validate_playbot_policy_payload(payload: dict[str, Any]) -> dict[str, Any]:
    _require_int(payload.get("version"), path="playbot.version", min_value=1)
    budgets = _validate_playbot_budget(payload.get("budget_ms"))
    board_size_scaling = _validate_playbot_board_size_scaling(payload.get("board_size_scaling"))
    clamp = _validate_playbot_clamp(payload.get("clamp"))
    lookahead = _validate_playbot_lookahead(payload.get("lookahead"))
    adaptive_fallback = _validate_playbot_adaptive_fallback(payload.get("adaptive_fallback"))
    auto_algorithm = _validate_playbot_auto_algorithm(payload.get("auto_algorithm"))
    benchmark = _validate_playbot_benchmark(payload.get("benchmark"))
    controller = _validate_playbot_controller(payload.get("controller"))
    dry_run = _validate_playbot_dry_run(payload.get("dry_run"))

    return {
        "version": payload["version"],
        "budget_ms": budgets,
        "board_size_scaling": board_size_scaling,
        "clamp": clamp,
        "lookahead": lookahead,
        "adaptive_fallback": adaptive_fallback,
        "auto_algorithm": auto_algorithm,
        "benchmark": benchmark,
        "controller": controller,
        "dry_run": dry_run,
    }


def validate_audio_sfx_payload(payload: dict[str, Any]) -> dict[str, Any]:
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
