import sys as _sys

from .gameplay import challenge_mode as _impl

_sys.modules[__name__] = _impl
