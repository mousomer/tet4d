from __future__ import annotations

from dataclasses import dataclass

from tet4d.engine.runtime.menu_settings_state import mode_endgame_settings
from tet4d.ui.pygame.locked_cell_explosion import (
    ExplosionSeedCell,
    build_explorer_explosion_surface_state,
)

from .piece_sandbox import ensure_piece_sandbox, sandbox_cells
from .scene_state import TopologyLabState, current_explorer_profile, playground_dims_for_state


@dataclass(frozen=True)
class ExplorerExplosionLaunchRequest:
    dimension: int
    board_dims: tuple[int, ...]
    explorer_profile: object | None
    occupied_cells: tuple[ExplosionSeedCell, ...]
    random_seed: int
    launch_speed_scale: float
    time_scale: float


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


def build_sandbox_explosion_launch_request(
    state: TopologyLabState,
) -> ExplorerExplosionLaunchRequest | None:
    ensure_piece_sandbox(state)
    cells = tuple(tuple(int(value) for value in coord) for coord in sandbox_cells(state))
    if not cells:
        return None
    mode_key = f"{int(state.dimension)}d"
    (
        _preset_id,
        _boundary_response,
        _particle_collisions,
        relic_speed_percent,
        shatter_speed_percent,
    ) = mode_endgame_settings(mode_key)
    color_id = 1
    if state.sandbox is not None:
        color_id = 1 + (int(state.sandbox.piece_index) % 7)
    return ExplorerExplosionLaunchRequest(
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
        launch_speed_scale=float(shatter_speed_percent) / 100.0,
        time_scale=float(relic_speed_percent) / 100.0,
    )


def start_sandbox_explosion(state: TopologyLabState) -> tuple[bool, str]:
    request = build_sandbox_explosion_launch_request(state)
    if request is None:
        return False, "Sandbox explosion requires at least one visible sandbox cell"
    state.pending_explosion_surface_state = build_explorer_explosion_surface_state(
        dimension=int(request.dimension),
        board_dims=tuple(int(value) for value in request.board_dims),
        explorer_profile=request.explorer_profile,
        occupied_cells=tuple(request.occupied_cells),
        random_seed=int(request.random_seed),
        launch_speed_scale=float(request.launch_speed_scale),
        time_scale=float(request.time_scale),
    )
    pending = state.pending_explosion_surface_state
    assert pending is not None
    pending.status = "Explorer launch inherits current sandbox cells; Enter restarts in place."
    return True, f"Sandbox explosion launched for {len(request.occupied_cells)} cells"


def step_scene_explosion(
    state: TopologyLabState,
    *,
    dt_ms: float,
    play_sfx,
) -> None:
    del state, dt_ms, play_sfx
