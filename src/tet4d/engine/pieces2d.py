import sys as _sys

from .gameplay import pieces2d as _impl

_sys.modules[__name__] = _impl
