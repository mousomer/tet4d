from __future__ import annotations

from tet4d.engine.topology_explorer.presets import (
    full_wrap_profile_4d,
    projective_space_profile_4d,
    sphere_profile_4d,
)
from tet4d.ui.pygame.locked_cell_explosion.model import (
    ExplosionSeedCell,
    ExplosionTopologyInput,
)
from tet4d.ui.pygame.locked_cell_explosion.simulation import (
    build_endgame_state,
    step_endgame_state,
)


def _state(profile, *, position, velocity):
    topology = ExplosionTopologyInput(
        board_dims=(4, 4, 4, 4),
        explorer_topology_profile=profile,
    )
    state = build_endgame_state(
        locked_cells=(ExplosionSeedCell(tuple(int(round(v)) for v in position), 2, "T"),),
        board_shape=(4, 4, 4, 4),
        dimension=4,
        topology=topology,
        seed=5555,
        settings={
            "boundary_response": "bounce",
            "collision_mode": "no_collision",
            "endgame_live_cell_fraction": 1.0,
            "sound_enabled": False,
        },
    )
    particle = state.particles[0]
    particle.position_nd = tuple(float(v) for v in position)
    particle.velocity_nd = tuple(float(v) for v in velocity)
    return state, particle


def test_wrap_transport_preserves_velocity_axis_and_sign() -> None:
    state, particle = _state(
        full_wrap_profile_4d(),
        position=(1.0, 1.0, 1.0, 3.45),
        velocity=(0.0, 0.0, 0.0, 1.2),
    )

    step_endgame_state(state, dt_ms=100.0)

    assert state.last_step_events[0].kind == "seam"
    assert state.last_step_events[0].source_boundary == "w+"
    assert particle.velocity_nd == (0.0, 0.0, 0.0, 1.2)
    assert particle.position_nd[3] < 0.0


def test_invert_transport_flips_tangent_velocity_signs() -> None:
    state, particle = _state(
        projective_space_profile_4d(),
        position=(-0.45, 1.0, 1.0, 1.0),
        velocity=(-1.2, 0.2, 0.3, 0.4),
    )

    step_endgame_state(state, dt_ms=100.0)

    assert state.last_step_events[0].kind == "seam"
    assert state.last_step_events[0].source_boundary == "x-"
    assert particle.velocity_nd == (-1.2, -0.2, -0.3, -0.4)


def test_sphere_like_transport_maps_velocity_across_axes() -> None:
    state, particle = _state(
        sphere_profile_4d(),
        position=(1.0, 1.0, -0.45, 1.0),
        velocity=(0.2, 0.3, -1.2, 0.4),
    )

    step_endgame_state(state, dt_ms=100.0)

    assert state.last_step_events[0].kind == "seam"
    assert state.last_step_events[0].source_boundary == "z-"
    assert state.last_step_events[0].target_boundary == "w-"
    assert particle.velocity_nd != (0.2, 0.3, -1.2, 0.4)
    assert abs(particle.velocity_nd[3]) == 1.2
