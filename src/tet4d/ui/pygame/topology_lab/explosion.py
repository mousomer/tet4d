from __future__ import annotations

from tet4d.engine.runtime.menu_settings_state import mode_endgame_settings
from tet4d.ui.pygame.locked_cell_explosion import (
    ExplosionSeedCell,
    build_explorer_explosion_surface_state,
)

from .piece_sandbox import ensure_piece_sandbox, sandbox_cells
from .scene_state import TopologyLabState, current_explorer_profile, playground_dims_for_state


def clear_scene_explosion(state: TopologyLabState) -> None:
    state.pending_explosion_surface_state = None
    state.scene_explosion = None


def consume_pending_scene_explosion_launch(state: TopologyLabState):
    pending = state.pending_explosion_surface_state
    state.pending_explosion_surface_state = None
    return pending


def scene_explosion_particles(state: TopologyLabState):
    del state
    return tuple()


def start_sandbox_explosion(state: TopologyLabState) -> tuple[bool, str]:
    ensure_piece_sandbox(state)
    cells = tuple(tuple(int(value) for value in coord) for coord in sandbox_cells(state))
    if not cells:
        return False, "Sandbox explosion requires at least one visible sandbox cell"
    mode_key = f"{int(state.dimension)}d"
    (
        _preset_id,
        boundary_response,
        particle_collisions,
        relic_speed_percent,
        shatter_speed_percent,
    ) = mode_endgame_settings(mode_key)
    color_id = 1
    if state.sandbox is not None:
        color_id = 1 + (int(state.sandbox.piece_index) % 7)
    state.pending_explosion_surface_state = build_explorer_explosion_surface_state(
        dimension=int(state.dimension),
        board_dims=tuple(int(value) for value in playground_dims_for_state(state)),
        explorer_profile=current_explorer_profile(state),
        occupied_cells=tuple(
            ExplosionSeedCell(
                source_coord=coord,
                color_id=color_id,
                source_group_id="sandbox",
            )
            for coord in cells
        ),
        random_seed=sum(
            (axis + 17) * (index + 1)
            for index, coord in enumerate(cells)
            for axis in coord
        ),
        boundary_response=str(boundary_response),
        particle_collisions=str(particle_collisions),
        speed_preset="normal",
        sound_enabled=True,
        launch_speed_scale=float(shatter_speed_percent) / 100.0,
        time_scale=float(relic_speed_percent) / 100.0,
    )
    pending = state.pending_explosion_surface_state
    assert pending is not None
    pending.status = "Explorer launch inherits current sandbox cells; Enter restarts in place."
    return True, f"Sandbox explosion launched for {len(cells)} cells"


def step_scene_explosion(
    state: TopologyLabState,
    *,
    dt_ms: float,
    play_sfx,
) -> None:
    del state, dt_ms, play_sfx
