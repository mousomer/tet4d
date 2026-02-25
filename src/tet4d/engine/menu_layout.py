import sys as _sys

from .ui_logic import menu_layout as _impl

_sys.modules[__name__] = _impl
