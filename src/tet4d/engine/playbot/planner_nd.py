from importlib import import_module
import sys

_impl = import_module("tet4d.ai.playbot.planner_nd")
sys.modules[__name__] = _impl
