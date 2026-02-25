import sys as _sys

from .gameplay import game_nd as _impl

_sys.modules[__name__] = _impl
