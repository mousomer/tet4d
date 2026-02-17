from __future__ import annotations

import os


# Keep pygame-based tests stable in headless runners/CI.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
