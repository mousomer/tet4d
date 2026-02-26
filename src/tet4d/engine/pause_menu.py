import sys

from tet4d.ui.pygame import pause_menu as _impl

sys.modules[__name__] = _impl
