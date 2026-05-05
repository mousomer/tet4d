from __future__ import annotations

from tet4d.ui.pygame.locked_cell_explosion.model import ExplosionSeedCell
from tet4d.ui.pygame.locked_cell_explosion.simulation import (
    _boundary_time,
    build_endgame_state,
    step_endgame_state,
)
from tet4d.ui.pygame.render.board_boundary import board_boundary_coordinate


def test_boundary_planes_use_cell_extent_coordinates() -> None:
    for dims in ((4, 5), (4, 5, 6), (4, 5, 6, 7)):
        for axis, size in enumerate(dims):
            assert board_boundary_coordinate(dims=dims, axis=axis, side="-") == -0.5
            assert board_boundary_coordinate(dims=dims, axis=axis, side="+") == size - 0.5


def test_min_and_max_boundary_contact_times_use_canonical_planes() -> None:
    dims = (4, 4, 4, 4)

    min_hit = _boundary_time((-0.25, 1.0, 1.0, 1.0), (-1.0, 0.0, 0.0, 0.0), dims)
    max_hit = _boundary_time((1.0, 1.0, 1.0, 3.25), (0.0, 0.0, 0.0, 1.0), dims)

    assert min_hit == (0.25, 0, "-")
    assert max_hit == (0.25, 3, "+")


def test_4d_w_coordinate_is_simulated_not_render_only() -> None:
    state = build_endgame_state(
        locked_cells=(ExplosionSeedCell((1, 1, 1, 1), 2, "W"),),
        board_shape=(4, 4, 4, 4),
        dimension=4,
        preset="classic",
        seed=4444,
        settings={"endgame_live_cell_fraction": 1.0, "sound_enabled": False},
    )
    particle = state.particles[0]
    particle.position_nd = (1.0, 1.0, 1.0, 1.0)
    particle.velocity_nd = (0.0, 0.0, 0.0, 1.0)

    step_endgame_state(state, dt_ms=100.0)

    assert particle.position_nd[3] > 1.0
    assert len(particle.position_nd) == 4
    assert len(particle.velocity_nd) == 4
