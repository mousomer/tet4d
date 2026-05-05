from __future__ import annotations

from tet4d.ui.pygame.locked_cell_explosion.model import ExplosionSeedCell
from tet4d.ui.pygame.locked_cell_explosion.simulation import (
    build_endgame_state,
    step_endgame_state,
)


def _state_sequence(seed: int) -> tuple[tuple[tuple[float, ...], tuple[float, ...]], ...]:
    state = build_endgame_state(
        locked_cells=(
            ExplosionSeedCell((0, 1, 1, 1), 2, "A"),
            ExplosionSeedCell((1, 1, 1, 2), 3, "B"),
            ExplosionSeedCell((2, 2, 1, 3), 4, "C"),
        ),
        board_shape=(4, 4, 4, 4),
        dimension=4,
        preset="wrap_all",
        seed=seed,
        settings={
            "boundary_response": "bounce",
            "collision_mode": "no_collision",
            "endgame_live_cell_fraction": 1.0,
            "sound_enabled": False,
        },
    )
    frames = []
    for _ in range(5):
        step_endgame_state(state, dt_ms=120.0)
        frames.append(
            tuple(
                (particle.position_nd, particle.velocity_nd)
                for particle in state.particles
            )
        )
    return tuple(frames)


def test_same_seed_settings_and_cells_produce_same_state_sequence() -> None:
    assert _state_sequence(2222) == _state_sequence(2222)


def test_different_seed_changes_state_sequence() -> None:
    assert _state_sequence(2222) != _state_sequence(2223)
