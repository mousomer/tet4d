import sys as _sys

from .gameplay import speed_curve as _impl

_sys.modules[__name__] = _impl
