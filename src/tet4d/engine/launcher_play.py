from __future__ import annotations

import sys

from tet4d.ui.pygame import launcher_play as _impl

sys.modules[__name__] = _impl
