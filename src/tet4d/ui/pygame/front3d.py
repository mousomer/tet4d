from __future__ import annotations


def run_3d() -> None:
    # Transitional adapter: delegates to existing pygame-heavy engine module.
    from tet4d.engine.front3d_game import run

    run()
