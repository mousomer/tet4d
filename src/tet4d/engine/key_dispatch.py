import sys as _sys

from .ui_logic import key_dispatch as _impl

_sys.modules[__name__] = _impl
