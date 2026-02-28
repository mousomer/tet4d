"""pygame UI adapters (transitional wrappers during architecture refactor)."""

from tet4d.engine import api as engine_api


def run_3d() -> None:
    engine_api.run_front3d_ui()


def run_4d() -> None:
    engine_api.run_front4d_ui()


__all__ = ["run_3d", "run_4d"]
