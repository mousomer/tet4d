from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS: dict[str, tuple[str, str]] = {
    "BOT_MODE_OPTIONS": ("tet4d.ai.playbot.types", "BOT_MODE_OPTIONS"),
    "BOT_PLANNER_ALGORITHM_OPTIONS": ("tet4d.ai.playbot.types", "BOT_PLANNER_ALGORITHM_OPTIONS"),
    "BOT_PLANNER_PROFILE_OPTIONS": ("tet4d.ai.playbot.types", "BOT_PLANNER_PROFILE_OPTIONS"),
    "BotMode": ("tet4d.ai.playbot.types", "BotMode"),
    "BotPlannerAlgorithm": ("tet4d.ai.playbot.types", "BotPlannerAlgorithm"),
    "BotPlannerProfile": ("tet4d.ai.playbot.types", "BotPlannerProfile"),
    "DryRunReport": ("tet4d.ai.playbot.types", "DryRunReport"),
    "PlayBotController": ("tet4d.ai.playbot.controller", "PlayBotController"),
    "bot_mode_from_index": ("tet4d.ai.playbot.types", "bot_mode_from_index"),
    "bot_mode_label": ("tet4d.ai.playbot.types", "bot_mode_label"),
    "bot_planner_algorithm_from_index": ("tet4d.ai.playbot.types", "bot_planner_algorithm_from_index"),
    "bot_planner_algorithm_label": ("tet4d.ai.playbot.types", "bot_planner_algorithm_label"),
    "bot_planner_profile_from_index": ("tet4d.ai.playbot.types", "bot_planner_profile_from_index"),
    "bot_planner_profile_label": ("tet4d.ai.playbot.types", "bot_planner_profile_label"),
    "default_planning_budget_ms": ("tet4d.ai.playbot.types", "default_planning_budget_ms"),
    "plan_best_2d_move": ("tet4d.ai.playbot.planner_2d", "plan_best_2d_move"),
    "plan_best_nd_move": ("tet4d.ai.playbot.planner_nd", "plan_best_nd_move"),
    "run_dry_run_2d": ("tet4d.ai.playbot.dry_run", "run_dry_run_2d"),
    "run_dry_run_nd": ("tet4d.ai.playbot.dry_run", "run_dry_run_nd"),
}

__all__ = [
    "BOT_MODE_OPTIONS",
    "BOT_PLANNER_ALGORITHM_OPTIONS",
    "BOT_PLANNER_PROFILE_OPTIONS",
    "BotMode",
    "BotPlannerAlgorithm",
    "BotPlannerProfile",
    "DryRunReport",
    "PlayBotController",
    "bot_mode_from_index",
    "bot_mode_label",
    "bot_planner_algorithm_from_index",
    "bot_planner_algorithm_label",
    "bot_planner_profile_from_index",
    "bot_planner_profile_label",
    "default_planning_budget_ms",
    "plan_best_2d_move",
    "plan_best_nd_move",
    "run_dry_run_2d",
    "run_dry_run_nd",
]


def __getattr__(name: str) -> Any:
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = target
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
