"""pygame UI adapters (transitional wrappers during architecture refactor)."""

from .front3d import run_3d
from .front4d import run_4d

__all__ = ["run_3d", "run_4d"]
