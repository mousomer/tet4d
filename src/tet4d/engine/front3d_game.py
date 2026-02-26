from importlib import import_module as _import_module
import sys as _sys


_impl = _import_module("tet4d.ui.pygame.front3d_game")
_sys.modules[__name__] = _impl
