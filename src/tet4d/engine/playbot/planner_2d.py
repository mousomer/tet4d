import sys

from tet4d.ai.playbot import planner_2d as _impl

sys.modules[__name__] = _impl
