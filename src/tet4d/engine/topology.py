import sys as _sys

from .gameplay import topology as _impl

_sys.modules[__name__] = _impl
