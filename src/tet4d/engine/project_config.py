import sys as _sys

from .runtime import project_config as _impl

_sys.modules[__name__] = _impl
