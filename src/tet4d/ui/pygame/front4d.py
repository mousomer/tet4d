from __future__ import annotations


def run_4d() -> None:
    # Transitional adapter: delegates to existing pygame-heavy engine module.
    from tet4d.engine.front4d_game import run

    run()
