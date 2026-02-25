import sys as _sys

from .runtime import runtime_config_validation as _impl

_sys.modules[__name__] = _impl
