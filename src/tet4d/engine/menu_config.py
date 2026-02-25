import sys as _sys

from .runtime import menu_config as _impl

_sys.modules[__name__] = _impl
