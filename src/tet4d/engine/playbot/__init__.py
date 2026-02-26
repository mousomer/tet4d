from importlib import import_module

from tet4d.ai.playbot.types import (
    BOT_MODE_OPTIONS,
    BOT_PLANNER_ALGORITHM_OPTIONS,
    BOT_PLANNER_PROFILE_OPTIONS,
    BotMode,
    BotPlannerAlgorithm,
    BotPlannerProfile,
    DryRunReport,
    bot_mode_label,
    bot_planner_algorithm_label,
    bot_planner_profile_label,
)


def run_dry_run_2d(*args, **kwargs):
    from tet4d.ai.playbot.dry_run import run_dry_run_2d as _run_dry_run_2d

    return _run_dry_run_2d(*args, **kwargs)


def run_dry_run_nd(*args, **kwargs):
    from tet4d.ai.playbot.dry_run import run_dry_run_nd as _run_dry_run_nd

    return _run_dry_run_nd(*args, **kwargs)


def __getattr__(name: str):
    if name == "PlayBotController":
        mod = import_module("tet4d.ai.playbot.controller")
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "BOT_MODE_OPTIONS",
    "BOT_PLANNER_ALGORITHM_OPTIONS",
    "BOT_PLANNER_PROFILE_OPTIONS",
    "BotMode",
    "BotPlannerAlgorithm",
    "BotPlannerProfile",
    "DryRunReport",
    "PlayBotController",
    "bot_mode_label",
    "bot_planner_algorithm_label",
    "bot_planner_profile_label",
    "run_dry_run_2d",
    "run_dry_run_nd",
]
