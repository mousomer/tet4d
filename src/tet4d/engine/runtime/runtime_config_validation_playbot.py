from __future__ import annotations

from typing import Any

from .settings_schema import (
    BOT_PROFILE_NAMES,
    require_int,
    require_number,
    require_object,
    require_state_relative_path,
)


def _validate_budget(raw_budget: object) -> dict[str, dict[str, int]]:
    budget_obj = require_object(raw_budget, path="playbot.budget_ms")
    budgets: dict[str, dict[str, int]] = {}
    for dim_key in ("2d", "3d", "4d_plus"):
        raw_dim = require_object(
            budget_obj.get(dim_key), path=f"playbot.budget_ms.{dim_key}"
        )
        dim_budget: dict[str, int] = {}
        for profile_name in BOT_PROFILE_NAMES:
            dim_budget[profile_name] = require_int(
                raw_dim.get(profile_name),
                path=f"playbot.budget_ms.{dim_key}.{profile_name}",
                min_value=1,
            )
        budgets[dim_key] = dim_budget
    return budgets


def _validate_board_size_scaling(raw_scaling: object) -> dict[str, Any]:
    scaling_obj = require_object(raw_scaling, path="playbot.board_size_scaling")
    reference_cells_obj = require_object(
        scaling_obj.get("reference_cells"),
        path="playbot.board_size_scaling.reference_cells",
    )
    reference_cells = {
        "2d": require_int(
            reference_cells_obj.get("2d"),
            path="playbot.board_size_scaling.reference_cells.2d",
            min_value=1,
        ),
        "3d": require_int(
            reference_cells_obj.get("3d"),
            path="playbot.board_size_scaling.reference_cells.3d",
            min_value=1,
        ),
        "4d_plus": require_int(
            reference_cells_obj.get("4d_plus"),
            path="playbot.board_size_scaling.reference_cells.4d_plus",
            min_value=1,
        ),
    }
    min_scale = require_number(
        scaling_obj.get("min_scale"),
        path="playbot.board_size_scaling.min_scale",
        min_value=0.1,
    )
    max_scale = require_number(
        scaling_obj.get("max_scale"),
        path="playbot.board_size_scaling.max_scale",
        min_value=min_scale,
    )
    exponent = require_number(
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


def _validate_clamp(raw_clamp: object) -> dict[str, int]:
    clamp_obj = require_object(raw_clamp, path="playbot.clamp")
    return {
        "floor_divisor": require_int(
            clamp_obj.get("floor_divisor"),
            path="playbot.clamp.floor_divisor",
            min_value=1,
        ),
        "floor_min": require_int(
            clamp_obj.get("floor_min"),
            path="playbot.clamp.floor_min",
            min_value=0,
        ),
        "ceil_multiplier": require_int(
            clamp_obj.get("ceil_multiplier"),
            path="playbot.clamp.ceil_multiplier",
            min_value=1,
        ),
        "ceil_min": require_int(
            clamp_obj.get("ceil_min"),
            path="playbot.clamp.ceil_min",
            min_value=1,
        ),
    }


def _validate_lookahead(raw_lookahead: object) -> dict[str, dict[str, int]]:
    lookahead_obj = require_object(raw_lookahead, path="playbot.lookahead")
    depth_obj = require_object(
        lookahead_obj.get("depth"), path="playbot.lookahead.depth"
    )
    top_k_obj = require_object(
        lookahead_obj.get("top_k"), path="playbot.lookahead.top_k"
    )
    depth = {
        "fast": require_int(
            depth_obj.get("fast"), path="playbot.lookahead.depth.fast", min_value=1
        ),
        "balanced_2d_3d": require_int(
            depth_obj.get("balanced_2d_3d"),
            path="playbot.lookahead.depth.balanced_2d_3d",
            min_value=1,
        ),
        "deep_2d_3d": require_int(
            depth_obj.get("deep_2d_3d"),
            path="playbot.lookahead.depth.deep_2d_3d",
            min_value=1,
        ),
        "ultra_2d_3d": require_int(
            depth_obj.get("ultra_2d_3d"),
            path="playbot.lookahead.depth.ultra_2d_3d",
            min_value=1,
        ),
        "all_4d_plus": require_int(
            depth_obj.get("all_4d_plus"),
            path="playbot.lookahead.depth.all_4d_plus",
            min_value=1,
        ),
    }
    top_k = {
        "depth_lte_one": require_int(
            top_k_obj.get("depth_lte_one"),
            path="playbot.lookahead.top_k.depth_lte_one",
            min_value=1,
        ),
        "balanced_2d": require_int(
            top_k_obj.get("balanced_2d"),
            path="playbot.lookahead.top_k.balanced_2d",
            min_value=1,
        ),
        "deep_2d": require_int(
            top_k_obj.get("deep_2d"),
            path="playbot.lookahead.top_k.deep_2d",
            min_value=1,
        ),
        "ultra_2d": require_int(
            top_k_obj.get("ultra_2d"),
            path="playbot.lookahead.top_k.ultra_2d",
            min_value=1,
        ),
        "balanced_3d_plus": require_int(
            top_k_obj.get("balanced_3d_plus"),
            path="playbot.lookahead.top_k.balanced_3d_plus",
            min_value=1,
        ),
        "deep_3d_plus": require_int(
            top_k_obj.get("deep_3d_plus"),
            path="playbot.lookahead.top_k.deep_3d_plus",
            min_value=1,
        ),
        "ultra_3d_plus": require_int(
            top_k_obj.get("ultra_3d_plus"),
            path="playbot.lookahead.top_k.ultra_3d_plus",
            min_value=1,
        ),
    }
    return {"depth": depth, "top_k": top_k}


def _validate_adaptive_fallback(raw_adaptive: object) -> dict[str, Any]:
    adaptive_obj = require_object(raw_adaptive, path="playbot.adaptive_fallback")
    adaptive_enabled = adaptive_obj.get("enabled")
    if not isinstance(adaptive_enabled, bool):
        raise RuntimeError("playbot.adaptive_fallback.enabled must be a boolean")

    lookahead_min_obj = require_object(
        adaptive_obj.get("lookahead_min_budget_ms"),
        path="playbot.adaptive_fallback.lookahead_min_budget_ms",
    )
    lookahead_min_budget_ms = {
        "2d": require_int(
            lookahead_min_obj.get("2d"),
            path="playbot.adaptive_fallback.lookahead_min_budget_ms.2d",
            min_value=1,
        ),
        "3d": require_int(
            lookahead_min_obj.get("3d"),
            path="playbot.adaptive_fallback.lookahead_min_budget_ms.3d",
            min_value=1,
        ),
        "4d_plus": require_int(
            lookahead_min_obj.get("4d_plus"),
            path="playbot.adaptive_fallback.lookahead_min_budget_ms.4d_plus",
            min_value=1,
        ),
    }

    candidate_cap_obj = require_object(
        adaptive_obj.get("candidate_cap"),
        path="playbot.adaptive_fallback.candidate_cap",
    )
    candidate_cap: dict[str, dict[str, float | int]] = {}
    for dim_key in ("2d", "3d", "4d_plus"):
        dim_cap_obj = require_object(
            candidate_cap_obj.get(dim_key),
            path=f"playbot.adaptive_fallback.candidate_cap.{dim_key}",
        )
        candidate_cap[dim_key] = {
            "per_ms": require_number(
                dim_cap_obj.get("per_ms"),
                path=f"playbot.adaptive_fallback.candidate_cap.{dim_key}.per_ms",
                min_value=0.1,
            ),
            "min": require_int(
                dim_cap_obj.get("min"),
                path=f"playbot.adaptive_fallback.candidate_cap.{dim_key}.min",
                min_value=1,
            ),
            "max": require_int(
                dim_cap_obj.get("max"),
                path=f"playbot.adaptive_fallback.candidate_cap.{dim_key}.max",
                min_value=1,
            ),
        }
        if candidate_cap[dim_key]["max"] < candidate_cap[dim_key]["min"]:
            raise RuntimeError(
                f"playbot.adaptive_fallback.candidate_cap.{dim_key}.max must be >= min"
            )

    deadline_safety_ms = require_number(
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


def _validate_auto_algorithm(raw_auto: object) -> dict[str, Any]:
    auto_obj = require_object(raw_auto, path="playbot.auto_algorithm")
    greedy_bias_obj = require_object(
        auto_obj.get("greedy_bias"),
        path="playbot.auto_algorithm.greedy_bias",
    )
    greedy_bias = {
        "2d": require_number(
            greedy_bias_obj.get("2d"),
            path="playbot.auto_algorithm.greedy_bias.2d",
        ),
        "3d": require_number(
            greedy_bias_obj.get("3d"),
            path="playbot.auto_algorithm.greedy_bias.3d",
        ),
        "4d_plus": require_number(
            greedy_bias_obj.get("4d_plus"),
            path="playbot.auto_algorithm.greedy_bias.4d_plus",
        ),
    }
    return {
        "greedy_bias": greedy_bias,
        "density_weight": require_number(
            auto_obj.get("density_weight"),
            path="playbot.auto_algorithm.density_weight",
        ),
        "lines_cleared_weight": require_number(
            auto_obj.get("lines_cleared_weight"),
            path="playbot.auto_algorithm.lines_cleared_weight",
        ),
        "threshold": require_number(
            auto_obj.get("threshold"),
            path="playbot.auto_algorithm.threshold",
        ),
    }


def _validate_benchmark(raw_benchmark: object) -> dict[str, Any]:
    benchmark_obj = require_object(raw_benchmark, path="playbot.benchmark")
    thresholds_obj = require_object(
        benchmark_obj.get("p95_threshold_ms"),
        path="playbot.benchmark.p95_threshold_ms",
    )
    benchmark_thresholds = {
        "2d": require_number(
            thresholds_obj.get("2d"),
            path="playbot.benchmark.p95_threshold_ms.2d",
            min_value=1.0,
        ),
        "3d": require_number(
            thresholds_obj.get("3d"),
            path="playbot.benchmark.p95_threshold_ms.3d",
            min_value=1.0,
        ),
        "4d": require_number(
            thresholds_obj.get("4d"),
            path="playbot.benchmark.p95_threshold_ms.4d",
            min_value=1.0,
        ),
    }
    history_file = require_state_relative_path(
        benchmark_obj.get("history_file"),
        path="playbot.benchmark.history_file",
    )
    return {
        "p95_threshold_ms": benchmark_thresholds,
        "history_file": history_file,
    }


def _validate_controller(raw_controller: object) -> dict[str, int]:
    controller_obj = require_object(raw_controller, path="playbot.controller")
    return {
        "hard_drop_after_soft_drops": require_int(
            controller_obj.get("hard_drop_after_soft_drops"),
            path="playbot.controller.hard_drop_after_soft_drops",
            min_value=0,
        ),
    }


def _validate_dry_run(raw_dry_run: object) -> dict[str, int]:
    dry_run_obj = require_object(raw_dry_run, path="playbot.dry_run")
    return {
        "default_pieces": require_int(
            dry_run_obj.get("default_pieces"),
            path="playbot.dry_run.default_pieces",
            min_value=1,
        ),
        "default_seed": require_int(
            dry_run_obj.get("default_seed"),
            path="playbot.dry_run.default_seed",
        ),
    }


def validate_playbot_policy_payload(payload: dict[str, Any]) -> dict[str, Any]:
    require_int(payload.get("version"), path="playbot.version", min_value=1)
    budgets = _validate_budget(payload.get("budget_ms"))
    board_size_scaling = _validate_board_size_scaling(payload.get("board_size_scaling"))
    clamp = _validate_clamp(payload.get("clamp"))
    lookahead = _validate_lookahead(payload.get("lookahead"))
    adaptive_fallback = _validate_adaptive_fallback(payload.get("adaptive_fallback"))
    auto_algorithm = _validate_auto_algorithm(payload.get("auto_algorithm"))
    benchmark = _validate_benchmark(payload.get("benchmark"))
    controller = _validate_controller(payload.get("controller"))
    dry_run = _validate_dry_run(payload.get("dry_run"))

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
