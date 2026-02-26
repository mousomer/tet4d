from __future__ import annotations

import sys

from tet4d.ui.pygame import loop_runner_nd as _impl

sys.modules[__name__] = _impl
