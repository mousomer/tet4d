"""AI playbot package.

Contains migrated playbot helpers and AI-owned implementations.
Public playbot APIs should generally be imported from ``tet4d.engine.api``.
"""

from importlib import import_module

__all__ = [
    "DryRunReport",
    "PlayBotController",
    "plan_best_2d_move",
    "run_dry_run_2d",
    "run_dry_run_nd",
]


def __getattr__(name: str):
    if name == "PlayBotController":
        mod = import_module("tet4d.ai.playbot.controller")
        return getattr(mod, name)
    if name == "plan_best_2d_move":
        mod = import_module("tet4d.ai.playbot.planner_2d")
        return getattr(mod, name)
    if name in {"run_dry_run_2d", "run_dry_run_nd"}:
        mod = import_module("tet4d.ai.playbot.dry_run")
        return getattr(mod, name)
    if name == "DryRunReport":
        mod = import_module("tet4d.ai.playbot.types")
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
