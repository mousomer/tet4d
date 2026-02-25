import sys as _sys

from .gameplay import pieces_nd as _impl

_sys.modules[__name__] = _impl
