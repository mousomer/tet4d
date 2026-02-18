from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import prod

from ..runtime_config import (
    playbot_adaptive_candidate_cap_for_ndim,
    playbot_adaptive_fallback_enabled,
    playbot_adaptive_lookahead_min_budget_ms,
    playbot_auto_algorithm_policy_for_ndim,
    playbot_benchmark_history_file,
    playbot_benchmark_p95_thresholds,
    playbot_board_size_scaling_policy_for_ndim,
    playbot_budget_table_for_ndim,
    playbot_clamp_policy,
    playbot_deadline_safety_ms,
    playbot_lookahead_depth,
    playbot_lookahead_top_k,
)


class BotMode(str, Enum):
    OFF = "off"
    ASSIST = "assist"
    AUTO = "auto"
    STEP = "step"


BOT_MODE_OPTIONS: tuple[BotMode, ...] = (
    BotMode.OFF,
    BotMode.ASSIST,
    BotMode.AUTO,
    BotMode.STEP,
)


class BotPlannerProfile(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    DEEP = "deep"
    ULTRA = "ultra"


BOT_PLANNER_PROFILE_OPTIONS: tuple[BotPlannerProfile, ...] = (
    BotPlannerProfile.FAST,
    BotPlannerProfile.BALANCED,
    BotPlannerProfile.DEEP,
    BotPlannerProfile.ULTRA,
)


class BotPlannerAlgorithm(str, Enum):
    AUTO = "auto"
    HEURISTIC = "heuristic"
    GREEDY_LAYER = "greedy_layer"


BOT_PLANNER_ALGORITHM_OPTIONS: tuple[BotPlannerAlgorithm, ...] = (
    BotPlannerAlgorithm.AUTO,
    BotPlannerAlgorithm.HEURISTIC,
    BotPlannerAlgorithm.GREEDY_LAYER,
)


def bot_mode_label(mode: BotMode) -> str:
    return mode.value.upper()


def bot_mode_from_index(index: int) -> BotMode:
    safe_index = max(0, min(len(BOT_MODE_OPTIONS) - 1, int(index)))
    return BOT_MODE_OPTIONS[safe_index]


def bot_planner_profile_label(profile: BotPlannerProfile) -> str:
    return profile.value.upper()


def bot_planner_profile_from_index(index: int) -> BotPlannerProfile:
    safe_index = max(0, min(len(BOT_PLANNER_PROFILE_OPTIONS) - 1, int(index)))
    return BOT_PLANNER_PROFILE_OPTIONS[safe_index]


def bot_planner_algorithm_label(algorithm: BotPlannerAlgorithm) -> str:
    return algorithm.value.upper()


def bot_planner_algorithm_from_index(index: int) -> BotPlannerAlgorithm:
    safe_index = max(0, min(len(BOT_PLANNER_ALGORITHM_OPTIONS) - 1, int(index)))
    return BOT_PLANNER_ALGORITHM_OPTIONS[safe_index]


def _board_size_scale(ndim: int, dims: tuple[int, ...] | None) -> float:
    if not dims:
        return 1.0
    ref_cells, min_scale, max_scale, exponent = playbot_board_size_scaling_policy_for_ndim(ndim)
    normalized_cells = max(1, prod(max(1, int(size)) for size in dims))
    ratio = normalized_cells / max(1, int(ref_cells))
    raw_scale = ratio ** max(0.01, float(exponent))
    return max(float(min_scale), min(float(max_scale), raw_scale))


def default_planning_budget_ms(
    ndim: int,
    profile: BotPlannerProfile,
    *,
    dims: tuple[int, ...] | None = None,
) -> int:
    fast, balanced, deep, ultra = playbot_budget_table_for_ndim(ndim)
    if profile == BotPlannerProfile.FAST:
        base = fast
    elif profile == BotPlannerProfile.DEEP:
        base = deep
    elif profile == BotPlannerProfile.ULTRA:
        base = ultra
    else:
        base = balanced
    scaled = int(round(base * _board_size_scale(ndim, dims)))
    return max(1, scaled)


def clamp_planning_budget_ms(
    ndim: int,
    budget_ms: int,
    *,
    dims: tuple[int, ...] | None = None,
) -> int:
    floor_divisor, floor_min, ceil_multiplier, ceil_min = playbot_clamp_policy()
    floor = max(
        floor_min,
        default_planning_budget_ms(ndim, BotPlannerProfile.FAST, dims=dims) // max(1, floor_divisor),
    )
    ceil = max(
        ceil_min,
        default_planning_budget_ms(ndim, BotPlannerProfile.ULTRA, dims=dims) * max(1, ceil_multiplier),
    )
    return max(floor, min(ceil, int(budget_ms)))


def planning_lookahead_depth(
    ndim: int,
    profile: BotPlannerProfile,
    *,
    budget_ms: int | None = None,
) -> int:
    base_depth = playbot_lookahead_depth(ndim, profile.value)
    if not playbot_adaptive_fallback_enabled() or budget_ms is None:
        return base_depth
    if int(budget_ms) < playbot_adaptive_lookahead_min_budget_ms(ndim):
        return 1
    return base_depth


def planning_lookahead_top_k(
    ndim: int,
    profile: BotPlannerProfile,
    *,
    budget_ms: int | None = None,
) -> int:
    depth = planning_lookahead_depth(ndim, profile, budget_ms=budget_ms)
    return playbot_lookahead_top_k(ndim, profile.value, depth)


def adaptive_candidate_cap(
    ndim: int,
    budget_ms: int,
    *,
    dims: tuple[int, ...] | None = None,
) -> int:
    if not playbot_adaptive_fallback_enabled():
        return 1_000_000
    per_ms, cap_min, cap_max = playbot_adaptive_candidate_cap_for_ndim(ndim)
    scale = _board_size_scale(ndim, dims)
    candidate_cap = int(round(float(budget_ms) * per_ms * scale))
    return max(int(cap_min), min(int(cap_max), candidate_cap))


def adaptive_deadline_safety_ms() -> float:
    return playbot_deadline_safety_ms()


def resolve_auto_planner_algorithm(
    *,
    ndim: int,
    dims: tuple[int, ...],
    occupied_cells: int,
    lines_cleared: int,
) -> BotPlannerAlgorithm:
    if ndim <= 2:
        return BotPlannerAlgorithm.HEURISTIC
    bias, density_weight, lines_weight, threshold = playbot_auto_algorithm_policy_for_ndim(ndim)
    total_cells = max(1, prod(max(1, int(size)) for size in dims))
    density = min(1.0, max(0.0, occupied_cells / total_cells))
    greedy_score = bias + density_weight * density + lines_weight * float(lines_cleared)
    if greedy_score >= threshold:
        return BotPlannerAlgorithm.GREEDY_LAYER
    return BotPlannerAlgorithm.HEURISTIC


def benchmark_p95_thresholds() -> dict[str, float]:
    return playbot_benchmark_p95_thresholds()


def benchmark_history_file() -> str:
    return str(playbot_benchmark_history_file())


@dataclass(frozen=True)
class PlanStats:
    candidate_count: int
    expected_clears: int
    heuristic_score: float
    planning_ms: float


@dataclass(frozen=True)
class DryRunReport:
    passed: bool
    reason: str
    pieces_dropped: int
    clears_observed: int
    game_over: bool
