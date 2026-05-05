from __future__ import annotations

from tet4d.ui.pygame.locked_cell_explosion.model import ExplosionParticle, ExplosionSeedCell
from tet4d.ui.pygame.locked_cell_explosion.simulation import (
    build_endgame_state,
    step_endgame_state,
    total_kinetic_energy_for_particles,
)


def test_kinetic_energy_uses_mass_weighted_velocity_norm() -> None:
    particles = [
        ExplosionParticle(
            particle_id=0,
            source_coord=(0, 0),
            position_nd=(0.0, 0.0),
            velocity_nd=(3.0, 4.0),
            color_id=1,
            collision_mass=2.0,
        )
    ]

    assert total_kinetic_energy_for_particles(particles) == 25.0


def test_no_collision_free_flight_preserves_energy() -> None:
    state = build_endgame_state(
        locked_cells=(ExplosionSeedCell((1, 1, 1, 1), 2, "E"),),
        board_shape=(8, 8, 8, 8),
        dimension=4,
        preset="classic",
        seed=7777,
        settings={
            "boundary_response": "bounce",
            "collision_mode": "no_collision",
            "endgame_live_cell_fraction": 1.0,
            "sound_enabled": False,
        },
    )
    particle = state.particles[0]
    particle.position_nd = (3.0, 3.0, 3.0, 3.0)
    particle.velocity_nd = (0.4, 0.3, 0.2, 0.1)
    state.total_kinetic_energy = total_kinetic_energy_for_particles(state.particles)
    before = state.total_kinetic_energy

    step_endgame_state(state, dt_ms=120.0)

    assert state.total_kinetic_energy == before
    assert state.diagnostics_summary is not None
    assert state.diagnostics_summary.kinetic_energy == before
