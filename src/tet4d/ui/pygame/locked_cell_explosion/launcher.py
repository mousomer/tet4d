from __future__ import annotations

from dataclasses import dataclass
import random
from typing import TYPE_CHECKING

import pygame

from tet4d.engine.gameplay.api import (
    piece_set_2d_label_gameplay,
    piece_set_2d_options_gameplay,
    piece_set_label_gameplay,
    piece_set_options_for_dimension_gameplay,
)
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.pieces2d import get_piece_bag_2d
from tet4d.engine.gameplay.pieces_nd import get_piece_shapes_nd
from tet4d.engine.runtime.menu_config import explorer_default_board_dims
from tet4d.engine.topology_explorer import BoundaryRef
from tet4d.engine.topology_explorer.presets import explorer_presets_for_dimension
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.ui_utils import (
    draw_panel_frame,
    draw_vertical_gradient,
    draw_wrapped_label_value_lines,
    wrap_text_lines,
    wrapped_label_value_layout,
)

from .board_view import draw_native_board_view
from .controller import LockedCellExplosionController, build_locked_cell_explosion
from .model import (
    EXPLOSION_BOUNDARY_RESPONSES,
    EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
    EXPLOSION_PARTICLE_COLLISION_MODES,
    EXPLOSION_PARTICLE_COLLISIONS_OFF,
    EXPLOSION_SPEED_NORMAL,
    EXPLOSION_SPEED_PRESETS,
    ExplosionSeedCell,
    ExplosionTopologyInput,
    StandaloneExplosionConfig,
)

if TYPE_CHECKING:
    from tet4d.engine.topology_explorer import ExplorerTopologyProfile

_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)
_DISABLED_COLOR = (136, 144, 172)
_PANEL_COLOR = (20, 24, 58)
_PANEL_ALT_COLOR = (10, 14, 34)
_PREVIEW_BG = (6, 10, 22)
_SEED_STEP = 1
_DIMENSIONS = (2, 3, 4)

_SNAPSHOT_SOURCE_INHERITED = "inherited_current_state"
_SNAPSHOT_SOURCE_SINGLE_CELL = "single_cell"
_SNAPSHOT_SOURCE_SINGLE_PIECE = "single_piece"
_SNAPSHOT_SOURCE_PIECE_CHANGE = "piece_change"
_SNAPSHOT_SOURCE_LABELS = {
    _SNAPSHOT_SOURCE_INHERITED: "Inherited Current State",
    _SNAPSHOT_SOURCE_SINGLE_CELL: "Single Cell",
    _SNAPSHOT_SOURCE_SINGLE_PIECE: "Single Piece",
    _SNAPSHOT_SOURCE_PIECE_CHANGE: "Piece Change",
}

_VIEW_MODE_BOARD_NATIVE = "board_native"
_VIEW_MODE_PROJECTION_REFERENCE = "projection_reference"
_VIEW_MODE_LABELS = {
    _VIEW_MODE_BOARD_NATIVE: "True Board View",
    _VIEW_MODE_PROJECTION_REFERENCE: "Projection Reference",
}

_ALL_ROW_KEYS = (
    "dimension",
    "view_mode",
    "topology",
    "snapshot_source",
    "piece_set",
    "piece_shape",
    "cell_x",
    "cell_y",
    "cell_z",
    "cell_w",
    "boundary_response",
    "particle_collisions",
    "trace_enabled",
    "speed_preset",
    "sound_enabled",
    "seed",
    "restart",
    "back",
)
_STATIC_ROW_VALUE_TEXT = {
    "restart": "Enter",
    "back": "Esc",
}
_AXIS_LABELS = ("X", "Y", "Z", "W")
_COLOR_CYCLE = (1, 2, 3, 4, 5, 6, 7)


@dataclass(frozen=True)
class _RowLayout:
    row_key: str
    label_lines: tuple[str, ...]
    value_lines: tuple[str, ...]
    row_height: int


@dataclass(frozen=True)
class _SurfaceLayout:
    left_rect: pygame.Rect
    right_rect: pygame.Rect
    row_viewport: pygame.Rect
    footer_rect: pygame.Rect
    preview_header_rect: pygame.Rect
    preview_scene_rect: pygame.Rect
    title_lines: tuple[str, ...]
    subtitle_lines: tuple[str, ...]
    footer_lines: tuple[str, ...]
    preview_header_lines: tuple[str, ...]


@dataclass
class StandaloneExplosionSurfaceState:
    dimension: int = 2
    view_mode: str = _VIEW_MODE_BOARD_NATIVE
    topology_preset_id: str = ""
    snapshot_source_id: str = _SNAPSHOT_SOURCE_SINGLE_PIECE
    piece_set_id: str = ""
    piece_shape_name: str = ""
    cell_origin: tuple[int, int, int, int] = (-1, -1, -1, -1)
    boundary_response: str = EXPLOSION_BOUNDARY_RESPONSE_ESCAPE
    particle_collisions: str = EXPLOSION_PARTICLE_COLLISIONS_OFF
    trace_enabled: bool = False
    speed_preset: str = EXPLOSION_SPEED_NORMAL
    sound_enabled: bool = True
    seed: int = 1337
    launch_speed_scale_override: float = 1.0
    time_scale_override: float = 1.0
    board_dims_override: tuple[int, ...] | None = None
    topology_profile_override: ExplorerTopologyProfile | None = None
    topology_label_override: str | None = None
    snapshot_label_override: str | None = None
    occupied_cells_override: tuple[ExplosionSeedCell, ...] | None = None
    locked_rows: frozenset[str] = frozenset()
    controller: LockedCellExplosionController | None = None
    selected_index: int = 0
    running: bool = True
    status: str = "Enter restarts the simulator. Esc returns to the launcher."
    status_error: bool = False
    camera_3d: object | None = None
    view_4d: object | None = None


def build_standalone_explosion_surface_state(
    *,
    dimension: int = 2,
) -> StandaloneExplosionSurfaceState:
    state = StandaloneExplosionSurfaceState(
        dimension=int(dimension) if int(dimension) in _DIMENSIONS else 2,
    )
    _ensure_view_state(state)
    _normalize_surface_state(state)
    state.controller = _build_controller(state)
    return state


def launcher_row_keys() -> tuple[str, ...]:
    return _ALL_ROW_KEYS


def _ensure_view_state(state: StandaloneExplosionSurfaceState) -> None:
    if state.camera_3d is None:
        from tet4d.ui.pygame.front3d_render import Camera3D

        state.camera_3d = Camera3D()
    if state.view_4d is None:
        from tet4d.ui.pygame.front4d_render import LayerView3D

        state.view_4d = LayerView3D()


def _boundaries_for_dimension(dimension: int) -> tuple[BoundaryRef, ...]:
    return tuple(
        BoundaryRef(dimension=dimension, axis=axis, side=side)
        for axis in range(int(dimension))
        for side in ("-", "+")
    )


def _preset_options_for_dimension(dimension: int):
    return explorer_presets_for_dimension(int(dimension))


def _default_preset_id(dimension: int) -> str:
    return str(_preset_options_for_dimension(dimension)[0].preset_id)


def _piece_set_options_for_dimension(dimension: int) -> tuple[str, ...]:
    if int(dimension) == 2:
        return tuple(piece_set_2d_options_gameplay())
    return tuple(piece_set_options_for_dimension_gameplay(int(dimension)))


def _default_piece_set_id(dimension: int) -> str:
    options = _piece_set_options_for_dimension(int(dimension))
    return str(options[0]) if options else ""


def _piece_set_label_for_dimension(dimension: int, piece_set_id: str) -> str:
    if int(dimension) == 2:
        return piece_set_2d_label_gameplay(piece_set_id)
    return piece_set_label_gameplay(piece_set_id)


def _piece_shapes_for_state(
    state: StandaloneExplosionSurfaceState,
    *,
    board_dims: tuple[int, ...],
):
    rng = random.Random(int(state.seed))
    if int(state.dimension) == 2:
        return tuple(
            get_piece_bag_2d(
                str(state.piece_set_id),
                rng=rng,
                board_dims=(int(board_dims[0]), int(board_dims[1])),
            )
        )
    return tuple(
        get_piece_shapes_nd(
            int(state.dimension),
            piece_set_id=str(state.piece_set_id),
            rng=rng,
            board_dims=board_dims,
        )
    )


def _available_snapshot_source_ids(
    state: StandaloneExplosionSurfaceState,
) -> tuple[str, ...]:
    if state.occupied_cells_override is not None:
        return (
            _SNAPSHOT_SOURCE_INHERITED,
            _SNAPSHOT_SOURCE_SINGLE_CELL,
            _SNAPSHOT_SOURCE_SINGLE_PIECE,
            _SNAPSHOT_SOURCE_PIECE_CHANGE,
        )
    return (
        _SNAPSHOT_SOURCE_SINGLE_CELL,
        _SNAPSHOT_SOURCE_SINGLE_PIECE,
        _SNAPSHOT_SOURCE_PIECE_CHANGE,
    )


def _view_mode_options_for_state(
    state: StandaloneExplosionSurfaceState,
) -> tuple[str, ...]:
    if int(state.dimension) == 2:
        return (_VIEW_MODE_BOARD_NATIVE,)
    return (_VIEW_MODE_BOARD_NATIVE, _VIEW_MODE_PROJECTION_REFERENCE)


def _dynamic_row_keys(
    state: StandaloneExplosionSurfaceState,
) -> tuple[str, ...]:
    rows = ["dimension"]
    if int(state.dimension) >= 3:
        rows.append("view_mode")
    rows.extend(("topology", "snapshot_source"))
    if state.occupied_cells_override is None:
        snapshot_source_id = str(state.snapshot_source_id)
        if snapshot_source_id in {
            _SNAPSHOT_SOURCE_SINGLE_PIECE,
            _SNAPSHOT_SOURCE_PIECE_CHANGE,
        }:
            rows.append("piece_set")
        if snapshot_source_id == _SNAPSHOT_SOURCE_SINGLE_PIECE:
            rows.append("piece_shape")
        if snapshot_source_id == _SNAPSHOT_SOURCE_SINGLE_CELL:
            rows.extend(f"cell_{axis.lower()}" for axis in _AXIS_LABELS[: int(state.dimension)])
    rows.extend(
        (
            "boundary_response",
            "particle_collisions",
            "trace_enabled",
            "speed_preset",
            "sound_enabled",
            "seed",
            "restart",
            "back",
        )
    )
    return tuple(rows)


def _row_label_text(row_key: str) -> str:
    labels = {
        "dimension": "Dimension",
        "view_mode": "View Mode",
        "topology": "Topology Preset",
        "snapshot_source": "Initial Snapshot",
        "piece_set": "Piece Set",
        "piece_shape": "Piece Shape",
        "boundary_response": "Boundary Response",
        "particle_collisions": "Particle Collisions",
        "trace_enabled": "Trace",
        "speed_preset": "Speed Preset",
        "sound_enabled": "Sound",
        "seed": "Seed",
        "restart": "Restart Simulation",
        "back": "Back",
    }
    if row_key.startswith("cell_"):
        return f"Cell {row_key.split('_', 1)[1].upper()}"
    return labels[row_key]


def _preset_for_state(
    state: StandaloneExplosionSurfaceState,
):
    for preset in _preset_options_for_dimension(int(state.dimension)):
        if preset.preset_id == str(state.topology_preset_id):
            return preset
    return None


def _preset_metadata_for_profile(
    dimension: int,
    profile: ExplorerTopologyProfile | None,
) -> tuple[str | None, str | None]:
    if profile is None:
        return None, None
    for preset in _preset_options_for_dimension(int(dimension)):
        if preset.profile == profile:
            return str(preset.preset_id), str(preset.label)
    return None, None


def _board_dims_for_state(state: StandaloneExplosionSurfaceState) -> tuple[int, ...]:
    if state.board_dims_override is not None:
        return tuple(int(value) for value in state.board_dims_override)
    return explorer_default_board_dims(int(state.dimension))


def _clamped_cell_origin(
    state: StandaloneExplosionSurfaceState,
    *,
    board_dims: tuple[int, ...],
) -> tuple[int, int, int, int]:
    center = tuple(int(size // 2) for size in board_dims)
    resolved: list[int] = []
    for axis in range(4):
        if axis < len(board_dims):
            raw = int(state.cell_origin[axis])
            if raw < 0:
                resolved.append(int(center[axis]))
            else:
                resolved.append(max(0, min(int(board_dims[axis]) - 1, raw)))
        else:
            resolved.append(0)
    return tuple(resolved)


def _exploration_spawn_origin(
    blocks: tuple[tuple[int, ...], ...] | list[tuple[int, ...]],
    board_dims: tuple[int, ...],
) -> tuple[int, ...]:
    origin: list[int] = []
    for axis, size in enumerate(board_dims):
        axis_values = [int(block[axis]) for block in blocks]
        min_axis = min(axis_values)
        max_axis = max(axis_values)
        span = max_axis - min_axis + 1
        start = (int(size) - span) // 2
        origin.append(start - min_axis)
    return tuple(origin)


def _normalize_dimension_and_topology(
    state: StandaloneExplosionSurfaceState,
) -> None:
    if int(state.dimension) not in _DIMENSIONS:
        state.dimension = 2
    preset_options = _preset_options_for_dimension(int(state.dimension))
    preset_ids = {str(option.preset_id) for option in preset_options}
    if (
        state.topology_profile_override is None
        and str(state.topology_preset_id) not in preset_ids
    ):
        state.topology_preset_id = _default_preset_id(int(state.dimension))


def _normalize_snapshot_and_view(
    state: StandaloneExplosionSurfaceState,
) -> None:
    if str(state.snapshot_source_id) not in _available_snapshot_source_ids(state):
        state.snapshot_source_id = _available_snapshot_source_ids(state)[0]
    if str(state.view_mode) not in _view_mode_options_for_state(state):
        state.view_mode = _view_mode_options_for_state(state)[0]


def _normalize_piece_selection(
    state: StandaloneExplosionSurfaceState,
    *,
    board_dims: tuple[int, ...],
) -> None:
    piece_set_options = _piece_set_options_for_dimension(int(state.dimension))
    if str(state.piece_set_id) not in piece_set_options:
        state.piece_set_id = _default_piece_set_id(int(state.dimension))
    shapes = _piece_shapes_for_state(state, board_dims=board_dims)
    piece_names = {str(shape.name) for shape in shapes}
    if not piece_names:
        state.piece_shape_name = ""
    elif str(state.piece_shape_name) not in piece_names:
        state.piece_shape_name = str(shapes[0].name)
    state.cell_origin = _clamped_cell_origin(state, board_dims=board_dims)


def _normalize_simulation_settings(
    state: StandaloneExplosionSurfaceState,
) -> None:
    if str(state.boundary_response) not in EXPLOSION_BOUNDARY_RESPONSES:
        state.boundary_response = EXPLOSION_BOUNDARY_RESPONSES[0]
    if str(state.particle_collisions) not in EXPLOSION_PARTICLE_COLLISION_MODES:
        state.particle_collisions = EXPLOSION_PARTICLE_COLLISION_MODES[0]
    if str(state.speed_preset) not in EXPLOSION_SPEED_PRESETS:
        state.speed_preset = EXPLOSION_SPEED_PRESETS[1]


def _normalize_selection_index(
    state: StandaloneExplosionSurfaceState,
) -> None:
    row_keys = _dynamic_row_keys(state)
    if int(state.selected_index) < 0 or int(state.selected_index) >= len(row_keys):
        state.selected_index = 0
    state.seed = max(0, int(state.seed))


def _normalize_surface_state(state: StandaloneExplosionSurfaceState) -> None:
    _ensure_view_state(state)
    _normalize_dimension_and_topology(state)
    _normalize_snapshot_and_view(state)
    _normalize_piece_selection(state, board_dims=_board_dims_for_state(state))
    _normalize_simulation_settings(state)
    _normalize_selection_index(state)


def _topology_input_for_state(
    state: StandaloneExplosionSurfaceState,
) -> ExplosionTopologyInput:
    preset = _preset_for_state(state)
    return ExplosionTopologyInput(
        board_dims=_board_dims_for_state(state),
        explorer_topology_profile=(
            state.topology_profile_override
            if state.topology_profile_override is not None
            else (preset.profile if preset is not None else None)
        ),
    )


def _single_cell_source_cells(
    state: StandaloneExplosionSurfaceState,
    *,
    board_dims: tuple[int, ...],
) -> tuple[ExplosionSeedCell, ...]:
    origin = _clamped_cell_origin(state, board_dims=board_dims)
    coord = tuple(int(origin[axis]) for axis in range(int(state.dimension)))
    return (
        ExplosionSeedCell(
            source_coord=coord,
            color_id=1,
            source_group_id="single_cell",
        ),
    )


def _selected_piece_shape(
    state: StandaloneExplosionSurfaceState,
    *,
    board_dims: tuple[int, ...],
):
    shapes = _piece_shapes_for_state(state, board_dims=board_dims)
    for shape in shapes:
        if str(shape.name) == str(state.piece_shape_name):
            return shape
    return shapes[0]


def _single_piece_source_cells(
    state: StandaloneExplosionSurfaceState,
    *,
    board_dims: tuple[int, ...],
) -> tuple[ExplosionSeedCell, ...]:
    shape = _selected_piece_shape(state, board_dims=board_dims)
    blocks = tuple(tuple(int(value) for value in block) for block in shape.blocks)
    origin = _exploration_spawn_origin(blocks, board_dims)
    return tuple(
        ExplosionSeedCell(
            source_coord=tuple(
                int(origin[axis]) + int(block[axis]) for axis in range(int(state.dimension))
            ),
            color_id=_COLOR_CYCLE[(int(shape.color_id) - 1 + index) % len(_COLOR_CYCLE)],
            source_group_id=str(shape.name),
        )
        for index, block in enumerate(blocks)
    )


def _piece_change_shapes_for_state(
    state: StandaloneExplosionSurfaceState,
    *,
    board_dims: tuple[int, ...],
):
    seed = int(state.seed)
    if int(state.dimension) == 2:
        runtime = GameState(
            config=GameConfig(
                width=int(board_dims[0]),
                height=int(board_dims[1]),
                piece_set=str(state.piece_set_id),
                exploration_mode=True,
                rng_seed=seed,
            ),
            board=None,
            rng=random.Random(seed),
        )
    else:
        runtime = GameStateND(
            config=GameConfigND(
                dims=board_dims,
                gravity_axis=1,
                piece_set_id=str(state.piece_set_id),
                exploration_mode=True,
                rng_seed=seed,
            ),
            board=None,
            rng=random.Random(seed),
        )
    current_shape = runtime.current_piece.shape if runtime.current_piece is not None else None
    if current_shape is None:
        shapes = _piece_shapes_for_state(state, board_dims=board_dims)
        return shapes[0], shapes[min(1, len(shapes) - 1)]
    next_shape = runtime.next_bag[-1] if runtime.next_bag else current_shape
    return current_shape, next_shape


def _piece_change_source_cells(
    state: StandaloneExplosionSurfaceState,
    *,
    board_dims: tuple[int, ...],
) -> tuple[ExplosionSeedCell, ...]:
    current_shape, next_shape = _piece_change_shapes_for_state(state, board_dims=board_dims)
    cell_map: dict[tuple[int, ...], ExplosionSeedCell] = {}
    for shape, group_id in (
        (current_shape, f"{current_shape.name}:current"),
        (next_shape, f"{next_shape.name}:next"),
    ):
        blocks = tuple(tuple(int(value) for value in block) for block in shape.blocks)
        origin = _exploration_spawn_origin(blocks, board_dims)
        for index, block in enumerate(blocks):
            coord = tuple(
                int(origin[axis]) + int(block[axis]) for axis in range(int(state.dimension))
            )
            cell_map[coord] = ExplosionSeedCell(
                source_coord=coord,
                color_id=_COLOR_CYCLE[(int(shape.color_id) - 1 + index) % len(_COLOR_CYCLE)],
                source_group_id=group_id,
            )
    return tuple(cell_map[coord] for coord in sorted(cell_map))


def _source_cells_for_state(
    state: StandaloneExplosionSurfaceState,
    *,
    board_dims: tuple[int, ...],
) -> tuple[ExplosionSeedCell, ...]:
    if state.occupied_cells_override is not None and str(state.snapshot_source_id) == _SNAPSHOT_SOURCE_INHERITED:
        return tuple(state.occupied_cells_override)
    snapshot_source_id = str(state.snapshot_source_id)
    if snapshot_source_id == _SNAPSHOT_SOURCE_SINGLE_CELL:
        return _single_cell_source_cells(state, board_dims=board_dims)
    if snapshot_source_id == _SNAPSHOT_SOURCE_PIECE_CHANGE:
        return _piece_change_source_cells(state, board_dims=board_dims)
    return _single_piece_source_cells(state, board_dims=board_dims)


def build_standalone_explosion_config(
    state: StandaloneExplosionSurfaceState,
) -> StandaloneExplosionConfig:
    _normalize_surface_state(state)
    topology = _topology_input_for_state(state)
    occupied_cells = _source_cells_for_state(state, board_dims=topology.board_dims)
    return StandaloneExplosionConfig(
        dimension=int(state.dimension),
        topology=topology,
        occupied_cells=occupied_cells,
        random_seed=int(state.seed),
        boundary_response=str(state.boundary_response),
        particle_collisions=str(state.particle_collisions),
        speed_preset=str(state.speed_preset),
        sound_enabled=bool(state.sound_enabled),
        launch_speed_scale=float(state.launch_speed_scale_override),
        time_scale=float(state.time_scale_override),
    )


def build_explorer_explosion_surface_state(
    *,
    dimension: int,
    board_dims: tuple[int, ...],
    explorer_profile: ExplorerTopologyProfile | None,
    occupied_cells: tuple[ExplosionSeedCell, ...],
    random_seed: int,
    boundary_response: str = EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
    particle_collisions: str = EXPLOSION_PARTICLE_COLLISIONS_OFF,
    speed_preset: str = EXPLOSION_SPEED_NORMAL,
    sound_enabled: bool = True,
    launch_speed_scale: float = 1.0,
    time_scale: float = 1.0,
) -> StandaloneExplosionSurfaceState:
    preset_id, preset_label = _preset_metadata_for_profile(dimension, explorer_profile)
    state = StandaloneExplosionSurfaceState(
        dimension=int(dimension),
        topology_preset_id=str(preset_id or ""),
        snapshot_source_id=_SNAPSHOT_SOURCE_INHERITED,
        boundary_response=str(boundary_response),
        particle_collisions=str(particle_collisions),
        speed_preset=str(speed_preset),
        sound_enabled=bool(sound_enabled),
        seed=int(random_seed),
        launch_speed_scale_override=float(launch_speed_scale),
        time_scale_override=float(time_scale),
        board_dims_override=tuple(int(value) for value in board_dims),
        topology_profile_override=explorer_profile,
        topology_label_override=preset_label or "Custom Explorer Topology",
        snapshot_label_override="Inherited Current State",
        occupied_cells_override=tuple(occupied_cells),
        locked_rows=frozenset({"dimension", "topology", "snapshot_source", "seed"}),
        status="Explorer launch inherits the current sandbox cells and topology.",
    )
    _ensure_view_state(state)
    _normalize_surface_state(state)
    state.controller = _build_controller(state)
    return state


def _build_controller(
    state: StandaloneExplosionSurfaceState,
) -> LockedCellExplosionController:
    return build_locked_cell_explosion(build_standalone_explosion_config(state))


def _post_restart_status(state: StandaloneExplosionSurfaceState) -> str:
    base = (
        f"{int(state.dimension)}D explosion restarted: "
        f"{_topology_value_text(state)}, "
        f"{_snapshot_value_text(state)}"
    )
    if (
        state.occupied_cells_override is None
        and str(state.snapshot_source_id) == _SNAPSHOT_SOURCE_PIECE_CHANGE
    ):
        base += f" ({_piece_change_summary_text(state)})"
    return base


def restart_standalone_explosion(
    state: StandaloneExplosionSurfaceState,
) -> LockedCellExplosionController:
    state.controller = _build_controller(state)
    state.status = _post_restart_status(state)
    state.status_error = False
    return state.controller


def _cycle_option(current: str, values: tuple[str, ...], step: int) -> str:
    index = values.index(current) if current in values else 0
    return values[(index + step) % len(values)]


def _requires_restart_for_row(row_key: str) -> bool:
    return row_key not in {"view_mode", "trace_enabled"}


def _adjust_axis_row(
    state: StandaloneExplosionSurfaceState,
    *,
    row_key: str,
    step: int,
) -> bool:
    axis_index = _AXIS_LABELS.index(row_key.split("_", 1)[1].upper())
    updated = list(state.cell_origin)
    updated[axis_index] = int(updated[axis_index]) + int(step)
    state.cell_origin = tuple(updated)
    _normalize_surface_state(state)
    return True


def _adjust_selection_row(
    state: StandaloneExplosionSurfaceState,
    *,
    row_key: str,
    step: int,
) -> bool:
    if row_key == "dimension":
        state.dimension = int(_cycle_option(str(state.dimension), ("2", "3", "4"), step))
        _normalize_surface_state(state)
        return True
    if row_key == "view_mode":
        state.view_mode = _cycle_option(
            str(state.view_mode),
            _view_mode_options_for_state(state),
            step,
        )
        return True
    if row_key == "topology":
        preset_ids = tuple(
            str(preset.preset_id)
            for preset in _preset_options_for_dimension(int(state.dimension))
        )
        state.topology_preset_id = _cycle_option(
            str(state.topology_preset_id),
            preset_ids,
            step,
        )
        return True
    if row_key == "snapshot_source":
        state.snapshot_source_id = _cycle_option(
            str(state.snapshot_source_id),
            _available_snapshot_source_ids(state),
            step,
        )
        _normalize_surface_state(state)
        return True
    if row_key == "piece_set":
        state.piece_set_id = _cycle_option(
            str(state.piece_set_id),
            _piece_set_options_for_dimension(int(state.dimension)),
            step,
        )
        _normalize_surface_state(state)
        return True
    if row_key == "piece_shape":
        shapes = _piece_shapes_for_state(state, board_dims=_board_dims_for_state(state))
        state.piece_shape_name = _cycle_option(
            str(state.piece_shape_name),
            tuple(str(shape.name) for shape in shapes),
            step,
        )
        return True
    if row_key.startswith("cell_"):
        return _adjust_axis_row(state, row_key=row_key, step=step)
    return False


def _adjust_simulation_row(
    state: StandaloneExplosionSurfaceState,
    *,
    row_key: str,
    step: int,
) -> bool:
    if row_key == "boundary_response":
        state.boundary_response = _cycle_option(
            str(state.boundary_response),
            EXPLOSION_BOUNDARY_RESPONSES,
            step,
        )
        return True
    if row_key == "particle_collisions":
        state.particle_collisions = _cycle_option(
            str(state.particle_collisions),
            EXPLOSION_PARTICLE_COLLISION_MODES,
            step,
        )
        return True
    if row_key == "speed_preset":
        state.speed_preset = _cycle_option(
            str(state.speed_preset),
            EXPLOSION_SPEED_PRESETS,
            step,
        )
        return True
    if row_key == "trace_enabled":
        state.trace_enabled = not bool(state.trace_enabled)
        return True
    if row_key == "sound_enabled":
        state.sound_enabled = not bool(state.sound_enabled)
        return True
    if row_key == "seed":
        state.seed = max(0, int(state.seed) + (step * _SEED_STEP))
        _normalize_surface_state(state)
        return True
    return False


def _adjust_selected_row(
    state: StandaloneExplosionSurfaceState,
    *,
    step: int,
) -> bool:
    row_keys = _dynamic_row_keys(state)
    row_key = row_keys[int(state.selected_index)]
    if row_key in state.locked_rows:
        return False
    return _adjust_selection_row(state, row_key=row_key, step=step) or _adjust_simulation_row(
        state,
        row_key=row_key,
        step=step,
    )


def _activate_selected_row(state: StandaloneExplosionSurfaceState) -> bool:
    row_key = _dynamic_row_keys(state)[int(state.selected_index)]
    if row_key == "restart":
        restart_standalone_explosion(state)
        play_sfx("menu_confirm")
        return True
    if row_key == "back":
        state.running = False
        play_sfx("menu_confirm")
        return True
    return False


def _row_value_overrides(
    state: StandaloneExplosionSurfaceState,
) -> dict[str, str]:
    return {
        "dimension": f"{int(state.dimension)}D",
        "view_mode": _VIEW_MODE_LABELS[str(state.view_mode)],
        "topology": _topology_value_text(state),
        "snapshot_source": _snapshot_value_text(state),
        "piece_set": _piece_set_label_for_dimension(
            int(state.dimension),
            str(state.piece_set_id),
        ),
        "piece_shape": str(state.piece_shape_name),
        "trace_enabled": "ON" if state.trace_enabled else "OFF",
        "sound_enabled": "ON" if state.sound_enabled else "OFF",
        "seed": str(int(state.seed)),
    }


def _dynamic_row_value_text(
    state: StandaloneExplosionSurfaceState,
    row_key: str,
) -> str:
    if row_key.startswith("cell_"):
        axis_index = _AXIS_LABELS.index(row_key.split("_", 1)[1].upper())
        return str(int(state.cell_origin[axis_index]))
    overrides = _row_value_overrides(state)
    if row_key in overrides:
        return overrides[row_key]
    return str(getattr(state, row_key, "")).upper()


def _row_value_text(state: StandaloneExplosionSurfaceState, row_key: str) -> str:
    if row_key in _STATIC_ROW_VALUE_TEXT:
        return _STATIC_ROW_VALUE_TEXT[row_key]
    return _dynamic_row_value_text(state, row_key)


def _topology_value_text(state: StandaloneExplosionSurfaceState) -> str:
    if state.topology_label_override:
        return str(state.topology_label_override)
    preset = _preset_for_state(state)
    if preset is not None:
        return str(preset.label)
    return "Custom"


def _snapshot_value_text(state: StandaloneExplosionSurfaceState) -> str:
    if state.snapshot_label_override and str(state.snapshot_source_id) == _SNAPSHOT_SOURCE_INHERITED:
        return str(state.snapshot_label_override)
    return _SNAPSHOT_SOURCE_LABELS[str(state.snapshot_source_id)]


def _piece_change_summary_text(state: StandaloneExplosionSurfaceState) -> str:
    current_shape, next_shape = _piece_change_shapes_for_state(
        state,
        board_dims=_board_dims_for_state(state),
    )
    return f"{current_shape.name} -> {next_shape.name}"


def _scene_focus_boundaries(
    state: StandaloneExplosionSurfaceState,
):
    boundaries = _boundaries_for_dimension(int(state.dimension))
    profile = _topology_input_for_state(state).explorer_topology_profile
    if profile is not None and profile.gluings:
        return boundaries, profile.gluings[0].source, profile.gluings[0].target
    return boundaries, boundaries[0], boundaries[min(1, len(boundaries) - 1)]


def _scene_active_glue_ids(
    state: StandaloneExplosionSurfaceState,
) -> dict[str, str]:
    active = {
        boundary.label: "free" for boundary in _boundaries_for_dimension(int(state.dimension))
    }
    profile = _topology_input_for_state(state).explorer_topology_profile
    if profile is None:
        return active
    for glue in profile.gluings:
        active[glue.source.label] = glue.glue_id
        active[glue.target.label] = glue.glue_id
    return active


def _draw_scene_2d(screen, fonts, **kwargs) -> None:
    from tet4d.ui.pygame.topology_lab.scene2d import draw_scene as draw_scene_2d

    draw_scene_2d(screen, fonts, **kwargs)


def _draw_scene_3d(screen, fonts, **kwargs) -> None:
    from tet4d.ui.pygame.topology_lab.scene3d import draw_scene as draw_scene_3d

    draw_scene_3d(screen, fonts, **kwargs)


def _draw_scene_4d(screen, fonts, **kwargs) -> None:
    from tet4d.ui.pygame.topology_lab.scene4d import draw_scene as draw_scene_4d

    draw_scene_4d(screen, fonts, **kwargs)


def _draw_native_board_preview(
    screen: pygame.Surface,
    *,
    fonts,
    area: pygame.Rect,
    controller: LockedCellExplosionController | None,
    state: StandaloneExplosionSurfaceState,
) -> None:
    draw_native_board_view(
        screen,
        rect=area,
        fonts=fonts,
        controller=controller,
        dimension=int(state.dimension),
        board_dims=_board_dims_for_state(state),
        camera_3d=state.camera_3d,
        view_4d=state.view_4d,
        show_trace=bool(state.trace_enabled),
    )


def _draw_projection_reference_scene(
    screen: pygame.Surface,
    *,
    fonts,
    area: pygame.Rect,
    controller: LockedCellExplosionController | None,
    state: StandaloneExplosionSurfaceState,
) -> None:
    boundaries, source_boundary, target_boundary = _scene_focus_boundaries(state)
    base_kwargs = dict(
        area=area,
        boundaries=boundaries,
        source_boundary=source_boundary,
        target_boundary=target_boundary,
        active_glue_ids=_scene_active_glue_ids(state),
        basis_arrows=(),
        preview_dims=_board_dims_for_state(state),
        explosion_particles=tuple(() if controller is None else controller.particles),
    )
    profile = _topology_input_for_state(state).explorer_topology_profile
    if int(state.dimension) == 2:
        _draw_scene_2d(
            screen,
            fonts,
            panel_title="Projection Reference",
            explosion_trace_enabled=bool(state.trace_enabled),
            **base_kwargs,
        )
        return
    if int(state.dimension) == 4:
        _draw_scene_4d(
            screen,
            fonts,
            profile=profile,
            explosion_trace_enabled=bool(state.trace_enabled),
            **base_kwargs,
        )
        return
    _draw_scene_3d(
        screen,
        fonts,
        profile=profile,
        explosion_trace_enabled=bool(state.trace_enabled),
        **base_kwargs,
    )


def _draw_simulation_scene(
    screen: pygame.Surface,
    *,
    fonts,
    area: pygame.Rect,
    controller: LockedCellExplosionController | None,
    state: StandaloneExplosionSurfaceState,
) -> None:
    if (
        int(state.dimension) >= 3
        and str(state.view_mode) == _VIEW_MODE_PROJECTION_REFERENCE
    ):
        _draw_projection_reference_scene(
            screen,
            fonts=fonts,
            area=area,
            controller=controller,
            state=state,
        )
        return
    _draw_native_board_preview(
        screen,
        fonts=fonts,
        area=area,
        controller=controller,
        state=state,
    )


def _apply_nonrestart_row_status(
    state: StandaloneExplosionSurfaceState,
    *,
    row_key: str,
) -> None:
    if row_key == "view_mode":
        state.status = f"View mode switched to {_VIEW_MODE_LABELS[str(state.view_mode)]}"
        state.status_error = False
        return
    if row_key == "trace_enabled":
        state.status = (
            "Trace overlay enabled"
            if state.trace_enabled
            else "Trace overlay disabled"
        )
        state.status_error = False


def _subtitle_text(state: StandaloneExplosionSurfaceState) -> str:
    if state.occupied_cells_override is not None:
        return "Explorer execution inherits sandbox cells and the resolved topology preset semantics."
    return "Standalone launcher uses preset-backed topology and engine-native board rendering."


def _preview_header_text(state: StandaloneExplosionSurfaceState) -> str:
    mode_label = _VIEW_MODE_LABELS[str(state.view_mode)]
    if int(state.dimension) == 2:
        mode_label = "Board View"
    return f"{mode_label}: {_topology_value_text(state)}"


def _footer_lines(state: StandaloneExplosionSurfaceState, *, fonts, max_width: int) -> tuple[str, ...]:
    config = build_standalone_explosion_config(state)
    cells = len(config.occupied_cells)
    energy = 0.0 if state.controller is None else float(state.controller.total_kinetic_energy)
    lines = [
        str(state.status),
        f"Board dims: {_board_dims_for_state(state)}  Cells: {cells}  Kinetic energy: {energy:.2f}",
    ]
    if (
        state.occupied_cells_override is None
        and str(state.snapshot_source_id) == _SNAPSHOT_SOURCE_PIECE_CHANGE
    ):
        lines.append(f"Piece change: {_piece_change_summary_text(state)}")
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(wrap_text_lines(fonts.hint_font, line, max_width))
    return tuple(wrapped)


def _header_lines(font, text: str, width: int) -> tuple[str, ...]:
    wrapped = wrap_text_lines(font, text, width)
    return wrapped if wrapped else ("",)


def _build_row_layouts(
    state: StandaloneExplosionSurfaceState,
    fonts,
    *,
    panel_width: int,
) -> tuple[_RowLayout, ...]:
    layouts: list[_RowLayout] = []
    for row_key in _dynamic_row_keys(state):
        label_lines, value_lines, row_height = wrapped_label_value_layout(
            fonts.menu_font,
            label=_row_label_text(row_key),
            value=_row_value_text(state, row_key),
            total_width=max(120, panel_width - 36),
            value_width_fraction=0.42,
            min_label_width=92,
            horizontal_padding=30,
            column_gap=12,
        )
        layouts.append(
            _RowLayout(
                row_key=row_key,
                label_lines=label_lines,
                value_lines=value_lines,
                row_height=row_height,
            )
        )
    return tuple(layouts)


def _surface_layout(
    *,
    screen_size: tuple[int, int],
    fonts,
    state: StandaloneExplosionSurfaceState,
) -> _SurfaceLayout:
    width, height = screen_size
    left_rect = pygame.Rect(24, 24, max(340, width // 3), height - 48)
    right_rect = pygame.Rect(
        left_rect.right + 20,
        24,
        width - left_rect.width - 68,
        height - 48,
    )
    title_lines = _header_lines(
        fonts.title_font,
        "Locked-Cell Explosion Simulator",
        left_rect.width - 36,
    )
    subtitle_lines = _header_lines(
        fonts.hint_font,
        _subtitle_text(state),
        left_rect.width - 36,
    )
    footer_lines = _footer_lines(
        state,
        fonts=fonts,
        max_width=left_rect.width - 36,
    )
    preview_header_lines = _header_lines(
        fonts.hint_font,
        _preview_header_text(state),
        right_rect.width - 36,
    )
    title_block_height = (
        len(title_lines) * (fonts.title_font.get_height() + 4)
        + len(subtitle_lines) * (fonts.hint_font.get_height() + 4)
        + 18
    )
    footer_height = len(footer_lines) * (fonts.hint_font.get_height() + 4) + 12
    row_top = left_rect.y + 18 + title_block_height
    row_viewport = pygame.Rect(
        left_rect.x + 12,
        row_top,
        left_rect.width - 24,
        max(80, left_rect.bottom - footer_height - row_top - 12),
    )
    footer_rect = pygame.Rect(
        left_rect.x + 18,
        row_viewport.bottom + 8,
        left_rect.width - 36,
        max(24, left_rect.bottom - row_viewport.bottom - 18),
    )
    preview_header_height = len(preview_header_lines) * (fonts.hint_font.get_height() + 4) + 10
    preview_header_rect = pygame.Rect(
        right_rect.x + 18,
        right_rect.y + 16,
        right_rect.width - 36,
        preview_header_height,
    )
    preview_scene_rect = pygame.Rect(
        right_rect.x + 12,
        preview_header_rect.bottom + 4,
        right_rect.width - 24,
        max(80, right_rect.bottom - preview_header_rect.bottom - 16),
    )
    return _SurfaceLayout(
        left_rect=left_rect,
        right_rect=right_rect,
        row_viewport=row_viewport,
        footer_rect=footer_rect,
        preview_header_rect=preview_header_rect,
        preview_scene_rect=preview_scene_rect,
        title_lines=title_lines,
        subtitle_lines=subtitle_lines,
        footer_lines=footer_lines,
        preview_header_lines=preview_header_lines,
    )


def _scroll_offset_for_selection(
    *,
    row_layouts: tuple[_RowLayout, ...],
    selected_index: int,
    viewport_height: int,
) -> int:
    if not row_layouts:
        return 0
    row_gap = 6
    content_height = 0
    selected_top = 0
    selected_height = row_layouts[selected_index].row_height
    for index, layout in enumerate(row_layouts):
        if index == selected_index:
            selected_top = content_height
            selected_height = layout.row_height
        content_height += layout.row_height + row_gap
    content_height = max(0, content_height - row_gap)
    max_scroll = max(0, content_height - viewport_height)
    if selected_top + selected_height <= viewport_height:
        return 0
    return max(
        0,
        min(
            max_scroll,
            selected_top + selected_height - viewport_height,
        ),
    )


def _draw_preview(
    screen: pygame.Surface,
    *,
    fonts,
    controller: LockedCellExplosionController | None,
    state: StandaloneExplosionSurfaceState,
    layout: _SurfaceLayout,
) -> None:
    pygame.draw.rect(screen, _PREVIEW_BG, layout.right_rect, border_radius=16)
    draw_panel_frame(
        screen,
        rect=layout.right_rect,
        border_radius=16,
        border_color=_PANEL_COLOR,
        fill_color=_PANEL_ALT_COLOR,
    )
    header_y = layout.preview_header_rect.y
    for line in layout.preview_header_lines:
        surf = fonts.hint_font.render(line, True, _MUTED_COLOR)
        screen.blit(surf, (layout.preview_header_rect.x, header_y))
        header_y += fonts.hint_font.get_height() + 4
    _draw_simulation_scene(
        screen,
        fonts=fonts,
        area=layout.preview_scene_rect,
        controller=controller,
        state=state,
    )


def _draw_surface(
    screen: pygame.Surface,
    fonts,
    state: StandaloneExplosionSurfaceState,
) -> None:
    _normalize_surface_state(state)
    layout = _surface_layout(screen_size=screen.get_size(), fonts=fonts, state=state)
    row_layouts = _build_row_layouts(state, fonts, panel_width=layout.left_rect.width)
    scroll_offset = _scroll_offset_for_selection(
        row_layouts=row_layouts,
        selected_index=int(state.selected_index),
        viewport_height=layout.row_viewport.height,
    )
    draw_vertical_gradient(screen, _BG_TOP, _BG_BOTTOM)
    pygame.draw.rect(screen, _PANEL_COLOR, layout.left_rect, border_radius=16)
    draw_panel_frame(
        screen,
        rect=layout.left_rect,
        border_radius=16,
        fill_color=_PANEL_ALT_COLOR,
        border_color=_PANEL_COLOR,
    )
    title_y = layout.left_rect.y + 16
    for line in layout.title_lines:
        surf = fonts.title_font.render(line, True, _TEXT_COLOR)
        screen.blit(surf, (layout.left_rect.x + 18, title_y))
        title_y += fonts.title_font.get_height() + 4
    for line in layout.subtitle_lines:
        surf = fonts.hint_font.render(line, True, _MUTED_COLOR)
        screen.blit(surf, (layout.left_rect.x + 18, title_y))
        title_y += fonts.hint_font.get_height() + 4
    pygame.draw.rect(screen, _PANEL_COLOR, layout.row_viewport, border_radius=12)
    row_gap = 6
    pygame.draw.rect(screen, _PANEL_ALT_COLOR, layout.row_viewport, border_radius=12)
    previous_clip = screen.get_clip()
    screen.set_clip(layout.row_viewport)
    row_y = layout.row_viewport.y - scroll_offset
    for index, row_layout in enumerate(row_layouts):
        row_rect = pygame.Rect(
            layout.row_viewport.x + 2,
            row_y,
            layout.row_viewport.width - 4,
            row_layout.row_height,
        )
        selected = index == int(state.selected_index)
        locked = row_layout.row_key in state.locked_rows
        pygame.draw.rect(
            screen,
            _PANEL_ALT_COLOR if selected else _PANEL_COLOR,
            row_rect,
            border_radius=10,
        )
        if selected:
            pygame.draw.rect(screen, _HIGHLIGHT_COLOR, row_rect, 2, border_radius=10)
        draw_wrapped_label_value_lines(
            screen,
            font=fonts.menu_font,
            label_lines=row_layout.label_lines,
            value_lines=row_layout.value_lines,
            label_x=row_rect.x + 12,
            value_right=row_rect.right - 12,
            top_y=row_rect.y + 6,
            label_color=_DISABLED_COLOR if locked else _TEXT_COLOR,
            value_color=_DISABLED_COLOR if locked else (_HIGHLIGHT_COLOR if selected else _MUTED_COLOR),
            line_gap=3,
        )
        row_y += row_layout.row_height + row_gap
    screen.set_clip(previous_clip)
    status_color = (255, 140, 140) if state.status_error else _MUTED_COLOR
    footer_y = layout.footer_rect.y
    for line in layout.footer_lines:
        surf = fonts.hint_font.render(line, True, status_color)
        screen.blit(surf, (layout.footer_rect.x, footer_y))
        footer_y += fonts.hint_font.get_height() + 4
    _draw_preview(
        screen,
        fonts=fonts,
        controller=state.controller,
        state=state,
        layout=layout,
    )


def run_standalone_explosion_launcher(
    screen: pygame.Surface,
    fonts,
    *,
    initial_state: StandaloneExplosionSurfaceState | None = None,
) -> tuple[bool, str]:
    state = initial_state or build_standalone_explosion_surface_state()
    _normalize_surface_state(state)
    if state.controller is None:
        state.controller = _build_controller(state)
    clock = pygame.time.Clock()
    while state.running:
        dt_ms = float(clock.tick(60))
        if not _process_launcher_events(state):
            return False, "Explosion simulator closed"
        if state.controller is not None:
            for event_name in state.controller.step(dt_ms):
                play_sfx(event_name)
        _draw_surface(screen, fonts, state)
        pygame.display.flip()
    return True, "Explosion simulator closed"


def _move_selected_row(state: StandaloneExplosionSurfaceState, step: int) -> None:
    row_keys = _dynamic_row_keys(state)
    state.selected_index = (int(state.selected_index) + int(step)) % len(row_keys)
    play_sfx("menu_move")


def _restart_from_key(state: StandaloneExplosionSurfaceState, key: int) -> None:
    if key in (pygame.K_LEFT, pygame.K_RIGHT):
        row_key = _dynamic_row_keys(state)[int(state.selected_index)]
        changed = _adjust_selected_row(
            state,
            step=-1 if key == pygame.K_LEFT else 1,
        )
        if changed:
            if _requires_restart_for_row(row_key):
                restart_standalone_explosion(state)
            else:
                _apply_nonrestart_row_status(state, row_key=row_key)
            play_sfx("menu_move")
        return
    restart_standalone_explosion(state)
    play_sfx("menu_confirm")


def _handle_launcher_keydown(
    state: StandaloneExplosionSurfaceState,
    key: int,
) -> None:
    if key == pygame.K_ESCAPE:
        state.running = False
        return
    if key == pygame.K_UP:
        _move_selected_row(state, -1)
        return
    if key == pygame.K_DOWN:
        _move_selected_row(state, 1)
        return
    if key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_r):
        _restart_from_key(state, key)
        return
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
        if not _activate_selected_row(state):
            _restart_from_key(state, pygame.K_r)


def _process_launcher_events(state: StandaloneExplosionSurfaceState) -> bool:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            _handle_launcher_keydown(state, event.key)
    return True


def run_standalone_explosion_launcher_action(
    state,
    session,
    fonts,
    *,
    persist_session_status,
) -> bool:
    mode = state.last_mode if state.last_mode in {"2d", "3d", "4d"} else "2d"
    ok, msg = run_standalone_explosion_launcher(
        session.screen,
        fonts,
        initial_state=build_standalone_explosion_surface_state(
            dimension=int(mode[0]),
        ),
    )
    persist_session_status(state, session)
    state.status = msg
    state.status_error = not ok
    return not session.running


__all__ = [
    "StandaloneExplosionSurfaceState",
    "build_explorer_explosion_surface_state",
    "build_standalone_explosion_config",
    "build_standalone_explosion_surface_state",
    "launcher_row_keys",
    "restart_standalone_explosion",
    "run_standalone_explosion_launcher_action",
    "run_standalone_explosion_launcher",
]
