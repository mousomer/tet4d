import sys as _sys

from ..ui.pygame import camera_mouse as _impl

_sys.modules[__name__] = _impl
