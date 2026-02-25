import sys as _sys

from .runtime import score_analyzer as _impl

_sys.modules[__name__] = _impl
