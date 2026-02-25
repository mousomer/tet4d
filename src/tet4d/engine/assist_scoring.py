import sys as _sys

from .runtime import assist_scoring as _impl

_sys.modules[__name__] = _impl
