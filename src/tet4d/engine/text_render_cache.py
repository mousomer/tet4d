import sys as _sys

from ..ui.pygame import text_render_cache as _impl

_sys.modules[__name__] = _impl
