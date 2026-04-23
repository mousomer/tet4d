from __future__ import annotations

from dataclasses import dataclass, replace
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
from tet4d.engine.topology_explorer.presets import (
    explorer_preset_sections_for_dimension,
    preset_display_label,
)
from tet4d.engine.ui_logic.view_modes import (
    GridMode,
    ShadowMode,
    grid_mode_label,
    shadow_mode_label,
)
from tet4d.ui.pygame import board_presentation
from tet4d.ui.pygame.controls import (
    ControlRowLayout as _RowLayout,
    NumericRowSpec as _NumericRowSpec,
    append_numeric_text_input as _controls_append_numeric_text_input,
    build_control_row_layouts,
    close_dropdown as _close_dropdown,
    commit_numeric_text_mode as _controls_commit_numeric_text_mode,
    dropdown_menu_rect as _controls_dropdown_menu_rect,
    dropdown_option_index_at_position as _controls_dropdown_option_index_at_position,
    dropdown_option_rects as _controls_dropdown_option_rects,
    dropdown_visible_slice as _controls_dropdown_visible_slice,
    handle_numeric_text_keydown as _controls_handle_numeric_text_keydown,
    numeric_display_text as _controls_numeric_display_text,
    open_dropdown as _open_dropdown,
    row_index_at_position as _controls_row_index_at_position,
    row_rects as _controls_row_rects,
    select_dropdown_option_from_click as _controls_select_dropdown_option_from_click,
    set_slider_value_from_pointer as _controls_set_slider_value_from_pointer,
    slider_fraction_for_row as _controls_slider_fraction_for_row,
    slider_fraction_from_pointer as _controls_slider_fraction_from_pointer,
    slider_rect_for_row as _controls_slider_rect_for_row,
    start_numeric_text_mode as _controls_start_numeric_text_mode,
    step_numeric_row as _controls_step_numeric_row,
    stop_numeric_text_mode as _controls_stop_numeric_text_mode,
    update_dropdown_hover_index as _controls_update_dropdown_hover_index,
    update_dropdown_scroll as _controls_update_dropdown_scroll,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.ui_utils import (
    draw_panel_frame,
    draw_value_slider,
    draw_vertical_gradient,
    draw_wrapped_label_value_lines,
    fit_text,
    wrap_text_lines,
)

from .controller import LockedCellExplosionController, build_locked_cell_explosion
from .defaults_store import (
    ENDGAME_LIVE_CELL_FRACTION_DEFAULT,
    ExplosionDefaults,
    clamp_endgame_live_cell_fraction,
    mode_explosion_defaults,
    save_mode_explosion_defaults,
)
from .simulation import (
    assign_particle_masses,
    total_kinetic_energy_for_particles,
    velocity_norm_sq_sum_for_particles,
)
from .model import (
    EXPLOSION_BOUNDARY_RESPONSES,
    EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
    EXPLOSION_COLLISION_ELASTICITY_MAX,
    EXPLOSION_COLLISION_ELASTICITY_MIN,
    EXPLOSION_DIAGNOSTICS_MODES,
    EXPLOSION_DIAGNOSTICS_MODE_FULL,
    EXPLOSION_DIAGNOSTICS_MODE_OFF,
    EXPLOSION_MASS_MODE_UNIFORM,
    EXPLOSION_MASS_MODES,
    EXPLOSION_MASS_MAX,
    EXPLOSION_MASS_MIN,
    EXPLOSION_PARTICLE_COLLISION_MODES,
    EXPLOSION_PARTICLE_COLLISIONS_OFF,
    EXPLOSION_SPEED_NORMAL,
    EXPLOSION_SPEED_PRESETS,
    EXPLOSION_TRAIL_MAX_LIFETIME_MS,
    EXPLOSION_TRAIL_RETENTION_MAX_MS,
    EXPLOSION_TRAIL_RETENTION_MIN_MS,
    ExplosionSeedCell,
    ExplosionTopologyInput,
    StandaloneExplosionConfig,
    clamp_collision_elasticity,
    clamp_mass_value,
    clamp_trace_retention_ms,
    normalize_mass_mode,
    normalize_mass_range,
    normalize_diagnostics_mode,
    trail_sample_budget_for_lifetime_ms,
)
from .runtime_config import (
    ExplosionRuntimeLaunchInputs,
    build_runtime_explosion_config,
)

if TYPE_CHECKING:
    from tet4d.engine.topology_explorer import ExplorerTopologyProfile


def _camera_controls_module():
    from tet4d.ui.pygame.topology_lab import camera_controls

    return camera_controls

_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)
_DISABLED_COLOR = (136, 144, 172)
_PANEL_COLOR = (20, 24, 58)
_PANEL_ALT_COLOR = (10, 14, 34)
_PREVIEW_BG = (6, 10, 22)
_DROPDOWN_AFFORDANCE_WIDTH = 34
_DROPDOWN_MENU_WIDTH = 220
_DROPDOWN_OPTION_VERTICAL_PADDING = 10
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
_W_MOVEMENT_ANIMATION_FADE = "fade"
_W_MOVEMENT_ANIMATION_BOX_SIZE = "box_size"
_W_MOVEMENT_ANIMATION_LABELS = {
    _W_MOVEMENT_ANIMATION_FADE: "Fade",
    _W_MOVEMENT_ANIMATION_BOX_SIZE: "Box Size",
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
    "mass_mode",
    "base_mass",
    "random_mass_min",
    "random_mass_max",
    "collision_elasticity",
    "diagnostics_mode",
    "grid_mode",
    "shadow_mode",
    "w_movement_animation",
    "trace_enabled",
    "trace_retention",
    "speed_preset",
    "sound_enabled",
    "seed",
    "save",
    "restart",
    "back",
)
_STATIC_ROW_VALUE_TEXT = {
    "save": "Enter",
    "restart": "Enter",
    "back": "Esc",
}
_AXIS_LABELS = ("X", "Y", "Z", "W")
_COLOR_CYCLE = (1, 2, 3, 4, 5, 6, 7)


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
    mass_mode: str = EXPLOSION_MASS_MODE_UNIFORM
    base_mass: float = 1.0
    random_mass_min: float = 0.75
    random_mass_max: float = 1.25
    collision_elasticity: float = 1.0
    diagnostics_mode: str = EXPLOSION_DIAGNOSTICS_MODE_OFF
    grid_mode: GridMode = GridMode.FULL
    shadow_mode: ShadowMode = ShadowMode.OFF
    trace_enabled: bool = False
    trace_retention_ms: float = EXPLOSION_TRAIL_MAX_LIFETIME_MS
    trace_retention_input_text: str = ""
    speed_preset: str = EXPLOSION_SPEED_NORMAL
    w_movement_animation_style: str = _W_MOVEMENT_ANIMATION_FADE
    endgame_live_cell_fraction: float = ENDGAME_LIVE_CELL_FRACTION_DEFAULT
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
    open_dropdown_row_key: str | None = None
    dropdown_hover_index: int | None = None
    dropdown_scroll_offset: int = 0
    hovered_row_key: str | None = None
    numeric_text_row_key: str = ""
    numeric_text_buffer: str = ""
    numeric_text_replace_on_type: bool = False
    slider_drag_row_key: str | None = None
    running: bool = True
    status: str = "Enter restarts the simulator. Esc returns to the launcher."
    status_error: bool = False
    camera_3d: object | None = None
    view_4d: object | None = None
    mouse_orbit: object | None = None


def build_standalone_explosion_surface_state(
    *,
    dimension: int = 2,
) -> StandaloneExplosionSurfaceState:
    resolved_dimension = int(dimension) if int(dimension) in _DIMENSIONS else 2
    state = StandaloneExplosionSurfaceState(
        dimension=resolved_dimension,
    )
    _apply_persisted_explosion_defaults(state)
    _ensure_view_state(state)
    _normalize_surface_state(state)
    state.controller = _build_controller(state)
    return state


def launcher_row_keys() -> tuple[str, ...]:
    return _ALL_ROW_KEYS


def _ensure_view_state(state: StandaloneExplosionSurfaceState) -> None:
    camera_controls = _camera_controls_module()
    state.camera_3d = camera_controls.ensure_scene_camera(3, state.camera_3d)
    state.view_4d = camera_controls.ensure_scene_camera(4, state.view_4d)
    state.mouse_orbit = camera_controls.ensure_mouse_orbit_state(state.mouse_orbit)


def _boundaries_for_dimension(dimension: int) -> tuple[BoundaryRef, ...]:
    return tuple(
        BoundaryRef(dimension=dimension, axis=axis, side=side)
        for axis in range(int(dimension))
        for side in ("-", "+")
    )


def _preset_options_for_dimension(dimension: int):
    return tuple(
        preset
        for section in explorer_preset_sections_for_dimension(int(dimension))
        for preset in section.presets
    )


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
            "mass_mode",
            "base_mass",
            "random_mass_min",
            "random_mass_max",
            "collision_elasticity",
            "diagnostics_mode",
            "grid_mode",
            "shadow_mode",
            *(("w_movement_animation",) if int(state.dimension) == 4 else ()),
            "trace_enabled",
            "trace_retention",
            "endgame_live_cell_fraction",
            "speed_preset",
            "sound_enabled",
            "seed",
            "save",
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
        "mass_mode": "Mass Mode",
        "base_mass": "Base Mass",
        "random_mass_min": "Random Mass Min",
        "random_mass_max": "Random Mass Max",
        "collision_elasticity": "Collision Elasticity",
        "diagnostics_mode": "Diagnostics",
        "grid_mode": "Grid",
        "shadow_mode": "Shadow",
        "w_movement_animation": "W Movement",
        "trace_enabled": "Trace",
        "trace_retention": "Trace Retention",
        "endgame_live_cell_fraction": "Endgame Live Fraction",
        "speed_preset": "Speed Preset",
        "sound_enabled": "Sound",
        "seed": "Seed",
        "save": "Save Defaults",
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
            return (
                str(preset.preset_id),
                preset_display_label(preset, include_group=True, include_unsafe=True),
            )
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
    state.mass_mode = normalize_mass_mode(state.mass_mode)
    state.base_mass = clamp_mass_value(state.base_mass)
    state.random_mass_min, state.random_mass_max = normalize_mass_range(
        state.random_mass_min,
        state.random_mass_max,
    )
    state.collision_elasticity = clamp_collision_elasticity(state.collision_elasticity)
    state.diagnostics_mode = normalize_diagnostics_mode(state.diagnostics_mode)
    if str(state.speed_preset) not in EXPLOSION_SPEED_PRESETS:
        state.speed_preset = EXPLOSION_SPEED_PRESETS[1]
    if state.grid_mode not in _grid_mode_options():
        state.grid_mode = GridMode.EDGE
    if state.shadow_mode not in _shadow_mode_options():
        state.shadow_mode = ShadowMode.OFF
    if str(state.w_movement_animation_style) not in _w_movement_animation_options():
        state.w_movement_animation_style = _W_MOVEMENT_ANIMATION_FADE
    state.trace_retention_ms = clamp_trace_retention_ms(state.trace_retention_ms)
    state.endgame_live_cell_fraction = clamp_endgame_live_cell_fraction(
        state.endgame_live_cell_fraction
    )
    if not str(state.trace_retention_input_text).strip():
        state.trace_retention_input_text = _trace_retention_input_text(
            state.trace_retention_ms
        )


def _grid_mode_options() -> tuple[GridMode, ...]:
    return (
        GridMode.OFF,
        GridMode.EDGE,
        GridMode.FULL,
    )


def _shadow_mode_options() -> tuple[ShadowMode, ...]:
    return (
        ShadowMode.OFF,
        ShadowMode.BOTTOM_BOUNDARY,
        ShadowMode.ALL_BOUNDARIES,
    )


def _w_movement_animation_options() -> tuple[str, ...]:
    return (
        _W_MOVEMENT_ANIMATION_FADE,
        _W_MOVEMENT_ANIMATION_BOX_SIZE,
    )


def _normalize_selection_index(
    state: StandaloneExplosionSurfaceState,
) -> None:
    row_keys = _dynamic_row_keys(state)
    if int(state.selected_index) < 0 or int(state.selected_index) >= len(row_keys):
        state.selected_index = 0
    if (
        state.open_dropdown_row_key is not None
        and state.open_dropdown_row_key not in row_keys
    ):
        _close_dropdown(state)
    state.seed = max(0, int(state.seed))


def _normalize_surface_state(state: StandaloneExplosionSurfaceState) -> None:
    _ensure_view_state(state)
    _normalize_dimension_and_topology(state)
    _normalize_snapshot_and_view(state)
    _normalize_piece_selection(state, board_dims=_board_dims_for_state(state))
    _normalize_simulation_settings(state)
    _normalize_selection_index(state)


def _mode_key_for_state(state: StandaloneExplosionSurfaceState) -> str:
    return f"{int(state.dimension)}d"


def _apply_explosion_defaults(
    state: StandaloneExplosionSurfaceState,
    defaults: ExplosionDefaults,
) -> None:
    state.view_mode = str(defaults.view_mode)
    state.topology_preset_id = str(defaults.topology_preset_id)
    state.snapshot_source_id = str(defaults.snapshot_source_id)
    state.piece_set_id = str(defaults.piece_set_id)
    state.piece_shape_name = str(defaults.piece_shape_name)
    state.cell_origin = tuple(int(value) for value in defaults.cell_origin)
    state.boundary_response = str(defaults.boundary_response)
    state.particle_collisions = str(defaults.particle_collisions)
    state.mass_mode = str(defaults.mass_mode)
    state.base_mass = float(defaults.base_mass)
    state.random_mass_min = float(defaults.random_mass_min)
    state.random_mass_max = float(defaults.random_mass_max)
    state.collision_elasticity = float(defaults.collision_elasticity)
    state.diagnostics_mode = str(defaults.diagnostics_mode)
    state.grid_mode = GridMode(str(defaults.grid_mode))
    state.shadow_mode = ShadowMode(str(defaults.shadow_mode))
    state.trace_enabled = bool(defaults.trace_enabled)
    state.trace_retention_ms = float(defaults.trace_retention_ms)
    state.trace_retention_input_text = _trace_retention_input_text(
        state.trace_retention_ms
    )
    state.speed_preset = str(defaults.speed_preset)
    state.w_movement_animation_style = str(defaults.w_movement_animation_style)
    state.endgame_live_cell_fraction = float(defaults.endgame_live_cell_fraction)
    state.sound_enabled = bool(defaults.sound_enabled)
    state.seed = int(defaults.seed)


def _apply_persisted_explosion_defaults(
    state: StandaloneExplosionSurfaceState,
) -> None:
    _apply_explosion_defaults(state, mode_explosion_defaults(_mode_key_for_state(state)))


def _persistent_defaults_from_state(
    state: StandaloneExplosionSurfaceState,
) -> ExplosionDefaults:
    _normalize_surface_state(state)
    return ExplosionDefaults(
        topology_preset_id=str(state.topology_preset_id),
        snapshot_source_id=str(state.snapshot_source_id),
        piece_set_id=str(state.piece_set_id),
        piece_shape_name=str(state.piece_shape_name),
        cell_origin=tuple(int(value) for value in state.cell_origin),
        view_mode=str(state.view_mode),
        boundary_response=str(state.boundary_response),
        particle_collisions=str(state.particle_collisions),
        mass_mode=str(state.mass_mode),
        base_mass=float(state.base_mass),
        random_mass_min=float(state.random_mass_min),
        random_mass_max=float(state.random_mass_max),
        collision_elasticity=float(state.collision_elasticity),
        diagnostics_mode=str(state.diagnostics_mode),
        grid_mode=str(state.grid_mode.value),
        shadow_mode=str(state.shadow_mode.value),
        trace_enabled=bool(state.trace_enabled),
        trace_retention_ms=float(state.trace_retention_ms),
        speed_preset=str(state.speed_preset),
        w_movement_animation_style=str(state.w_movement_animation_style),
        endgame_live_cell_fraction=float(state.endgame_live_cell_fraction),
        sound_enabled=bool(state.sound_enabled),
        seed=int(state.seed),
    )


def save_standalone_explosion_defaults(
    state: StandaloneExplosionSurfaceState,
) -> tuple[bool, str]:
    return save_mode_explosion_defaults(
        _mode_key_for_state(state),
        _persistent_defaults_from_state(state),
    )


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
    return build_runtime_explosion_config(
        defaults=_persistent_defaults_from_state(state),
        launch=ExplosionRuntimeLaunchInputs(
            dimension=int(state.dimension),
            topology=topology,
            occupied_cells=occupied_cells,
            random_seed=int(state.seed),
            launch_speed_scale=float(state.launch_speed_scale_override),
            time_scale=float(state.time_scale_override),
        ),
    )


def build_explorer_explosion_surface_state(
    *,
    dimension: int,
    board_dims: tuple[int, ...],
    explorer_profile: ExplorerTopologyProfile | None,
    occupied_cells: tuple[ExplosionSeedCell, ...],
    random_seed: int,
    launch_speed_scale: float = 1.0,
    time_scale: float = 1.0,
) -> StandaloneExplosionSurfaceState:
    saved_defaults = mode_explosion_defaults(f"{int(dimension)}d")
    preset_id, preset_label = _preset_metadata_for_profile(dimension, explorer_profile)
    state = StandaloneExplosionSurfaceState(dimension=int(dimension))
    _apply_explosion_defaults(state, saved_defaults)
    state.topology_preset_id = str(preset_id or saved_defaults.topology_preset_id)
    state.snapshot_source_id = _SNAPSHOT_SOURCE_INHERITED
    state.seed = int(random_seed if random_seed is not None else saved_defaults.seed)
    state.launch_speed_scale_override = float(launch_speed_scale)
    state.time_scale_override = float(time_scale)
    state.board_dims_override = tuple(int(value) for value in board_dims)
    state.topology_profile_override = explorer_profile
    state.topology_label_override = preset_label or "Custom Explorer Topology"
    state.snapshot_label_override = "Inherited Current State"
    state.occupied_cells_override = tuple(occupied_cells)
    state.locked_rows = frozenset({"dimension", "topology", "snapshot_source", "seed"})
    state.status = "Explorer launch inherits the current sandbox cells and topology."
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
    return row_key not in {
        "view_mode",
        "grid_mode",
        "shadow_mode",
        "trace_enabled",
        "trace_retention",
        "mass_mode",
        "base_mass",
        "random_mass_min",
        "random_mass_max",
        "collision_elasticity",
        "diagnostics_mode",
    }


def _trace_retention_step_ms() -> float:
    return 120.0


def _trace_retention_input_text(retention_ms: float) -> str:
    return f"{float(retention_ms) / 1000.0:.2f}"


def _numeric_spec_for_row(
    state: StandaloneExplosionSurfaceState,
    row_key: str,
) -> _NumericRowSpec | None:
    if row_key in {"base_mass", "random_mass_min", "random_mass_max"}:
        return _NumericRowSpec(
            row_key=row_key,
            minimum=float(EXPLOSION_MASS_MIN),
            maximum=float(EXPLOSION_MASS_MAX),
            step=0.05,
            decimals=2,
        )
    if row_key == "collision_elasticity":
        return _NumericRowSpec(
            row_key=row_key,
            minimum=float(EXPLOSION_COLLISION_ELASTICITY_MIN),
            maximum=float(EXPLOSION_COLLISION_ELASTICITY_MAX),
            step=0.05,
            decimals=2,
        )
    if row_key == "trace_retention":
        return _NumericRowSpec(
            row_key=row_key,
            minimum=float(EXPLOSION_TRAIL_RETENTION_MIN_MS),
            maximum=float(EXPLOSION_TRAIL_RETENTION_MAX_MS),
            step=float(_trace_retention_step_ms()),
            decimals=2,
            unit_suffix=" s",
        )
    if row_key == "endgame_live_cell_fraction":
        return _NumericRowSpec(
            row_key=row_key,
            minimum=0.0,
            maximum=1.0,
            step=0.01,
            decimals=2,
        )
    if row_key == "seed":
        return _NumericRowSpec(
            row_key=row_key,
            minimum=0.0,
            maximum=9999.0,
            step=float(_SEED_STEP),
            decimals=0,
        )
    if row_key.startswith("cell_"):
        axis_index = _AXIS_LABELS.index(row_key.split("_", 1)[1].upper())
        board_dims = _board_dims_for_state(state)
        return _NumericRowSpec(
            row_key=row_key,
            minimum=0.0,
            maximum=float(max(0, int(board_dims[axis_index]) - 1)),
            step=1.0,
            decimals=0,
        )
    return None


def _numeric_row_keys(state: StandaloneExplosionSurfaceState) -> tuple[str, ...]:
    return tuple(
        row_key
        for row_key in _dynamic_row_keys(state)
        if _numeric_spec_for_row(state, row_key) is not None
    )


def _numeric_value_for_row(
    state: StandaloneExplosionSurfaceState,
    row_key: str,
) -> float:
    if row_key == "base_mass":
        return float(state.base_mass)
    if row_key == "random_mass_min":
        return float(state.random_mass_min)
    if row_key == "random_mass_max":
        return float(state.random_mass_max)
    if row_key == "collision_elasticity":
        return float(state.collision_elasticity)
    if row_key == "trace_retention":
        return float(state.trace_retention_ms)
    if row_key == "endgame_live_cell_fraction":
        return float(state.endgame_live_cell_fraction)
    if row_key == "seed":
        return float(state.seed)
    if row_key.startswith("cell_"):
        axis_index = _AXIS_LABELS.index(row_key.split("_", 1)[1].upper())
        return float(state.cell_origin[axis_index])
    raise KeyError(row_key)


def _format_numeric_value(
    value: float,
    *,
    decimals: int,
) -> str:
    if decimals <= 0:
        return str(int(round(value)))
    return f"{value:.{decimals}f}"


def _numeric_display_text_for_row(
    state: StandaloneExplosionSurfaceState,
    row_key: str,
) -> str:
    return _controls_numeric_display_text(
        state,
        row_key=row_key,
        spec_for_row=lambda key: _numeric_spec_for_row(state, key),
        value_for_row=lambda key: _numeric_value_for_row(state, key),
        custom_formatters={"trace_retention": _trace_retention_input_text},
    )


def _set_numeric_value_for_row(
    state: StandaloneExplosionSurfaceState,
    row_key: str,
    value: float,
) -> None:
    spec = _numeric_spec_for_row(state, row_key)
    if spec is None:
        raise KeyError(row_key)
    clamped = max(spec.minimum, min(spec.maximum, float(value)))
    if row_key == "trace_retention":
        state.trace_retention_ms = clamp_trace_retention_ms(clamped)
        state.trace_retention_input_text = _trace_retention_input_text(
            state.trace_retention_ms
        )
        _apply_live_trace_retention(state)
        return
    if row_key == "endgame_live_cell_fraction":
        state.endgame_live_cell_fraction = clamp_endgame_live_cell_fraction(clamped)
        return
    if row_key == "seed":
        state.seed = int(round(clamped))
        _normalize_surface_state(state)
        _apply_live_mass_and_collision_settings(state)
        return
    if row_key == "base_mass":
        state.base_mass = clamp_mass_value(clamped)
        _apply_live_mass_and_collision_settings(state)
        return
    if row_key == "random_mass_min":
        state.random_mass_min, state.random_mass_max = normalize_mass_range(
            clamped,
            state.random_mass_max,
        )
        _apply_live_mass_and_collision_settings(state)
        return
    if row_key == "random_mass_max":
        state.random_mass_min, state.random_mass_max = normalize_mass_range(
            state.random_mass_min,
            clamped,
        )
        _apply_live_mass_and_collision_settings(state)
        return
    if row_key == "collision_elasticity":
        state.collision_elasticity = clamp_collision_elasticity(clamped)
        _apply_live_mass_and_collision_settings(state)
        return
    if row_key.startswith("cell_"):
        axis_index = _AXIS_LABELS.index(row_key.split("_", 1)[1].upper())
        updated = list(state.cell_origin)
        updated[axis_index] = int(round(clamped))
        state.cell_origin = tuple(updated)
        _normalize_surface_state(state)
        return


def _start_numeric_text_mode(
    state: StandaloneExplosionSurfaceState,
    row_key: str,
    *,
    incoming_text: str = "",
) -> bool:
    return _controls_start_numeric_text_mode(
        state,
        row_key,
        spec_for_row=lambda key: _numeric_spec_for_row(state, key),
        value_for_row=lambda key: _numeric_value_for_row(state, key),
        display_value_for_edit=lambda key, value, spec: _format_numeric_value(
            value / (1000.0 if key == "trace_retention" else 1.0),
            decimals=spec.decimals,
        ),
        incoming_text=incoming_text,
    )


def _stop_numeric_text_mode(state: StandaloneExplosionSurfaceState) -> None:
    _controls_stop_numeric_text_mode(state)


def _append_numeric_text_input(
    state: StandaloneExplosionSurfaceState,
    incoming_text: str,
) -> bool:
    return _controls_append_numeric_text_input(
        state,
        incoming_text,
        spec_for_row=lambda key: _numeric_spec_for_row(state, key),
    )


def _commit_numeric_text_mode(
    state: StandaloneExplosionSurfaceState,
    *,
    allow_partial: bool = False,
) -> bool:
    return _controls_commit_numeric_text_mode(
        state,
        spec_for_row=lambda key: _numeric_spec_for_row(state, key),
        set_value_for_row=lambda key, value: _set_numeric_value_for_row(state, key, value),
        row_label_text=_row_label_text,
        value_transformers={"trace_retention": lambda value: value * 1000.0},
        allow_partial=allow_partial,
    )


def _commit_trace_retention_input(
    state: StandaloneExplosionSurfaceState,
    *,
    allow_partial: bool = False,
) -> bool:
    original_text = _trace_retention_input_text(state.trace_retention_ms)
    previous_row = state.numeric_text_row_key
    previous_buffer = state.numeric_text_buffer
    previous_replace = state.numeric_text_replace_on_type
    state.numeric_text_row_key = "trace_retention"
    state.numeric_text_buffer = str(state.trace_retention_input_text).strip()
    state.numeric_text_replace_on_type = False
    changed = _commit_numeric_text_mode(state, allow_partial=allow_partial)
    if allow_partial and not changed:
        state.numeric_text_row_key = previous_row
        state.numeric_text_buffer = previous_buffer
        state.numeric_text_replace_on_type = previous_replace
        return False
    if not changed:
        state.trace_retention_input_text = original_text
    return changed


def _slider_fraction_for_row(
    state: StandaloneExplosionSurfaceState,
    row_key: str,
) -> float | None:
    return _controls_slider_fraction_for_row(
        row_key,
        spec_for_row=lambda key: _numeric_spec_for_row(state, key),
        value_for_row=lambda key: _numeric_value_for_row(state, key),
    )


def _row_control_kind(row_key: str) -> str:
    if row_key in {"save", "restart", "back"}:
        return "action"
    if row_key in {"trace_retention", "endgame_live_cell_fraction", "seed", "base_mass", "random_mass_min", "random_mass_max", "collision_elasticity"} or row_key.startswith("cell_"):
        return "numeric"
    if row_key in {
        "dimension",
        "view_mode",
        "topology",
        "snapshot_source",
        "piece_set",
        "piece_shape",
        "boundary_response",
        "particle_collisions",
        "mass_mode",
        "diagnostics_mode",
        "grid_mode",
        "shadow_mode",
        "w_movement_animation",
        "trace_enabled",
        "speed_preset",
        "sound_enabled",
    }:
        return "dropdown"
    return "value"


def _apply_live_trace_retention(state: StandaloneExplosionSurfaceState) -> None:
    controller = state.controller
    if controller is None:
        return
    controller.config = replace(
        controller.config,
        trace_retention_ms=float(state.trace_retention_ms),
    )
    for particle in controller.simulation.particles:
        particle.trail_max_lifetime_ms = float(state.trace_retention_ms)
        particle.trail_max_samples = trail_sample_budget_for_lifetime_ms(
            state.trace_retention_ms
        )
        retained = [
            sample
            for sample in particle.trail_samples
            if float(sample.elapsed_ms)
            >= float(particle.trail_elapsed_ms) - float(particle.trail_max_lifetime_ms)
        ]
        if len(retained) > particle.trail_max_samples:
            retained = retained[-particle.trail_max_samples :]
        particle.trail_samples = retained


def _apply_live_mass_and_collision_settings(state: StandaloneExplosionSurfaceState) -> None:
    controller = state.controller
    if controller is None:
        return
    controller.config = replace(
        controller.config,
        mass_mode=str(state.mass_mode),
        base_mass=float(state.base_mass),
        random_mass_min=float(state.random_mass_min),
        random_mass_max=float(state.random_mass_max),
        collision_elasticity=float(state.collision_elasticity),
        diagnostics_mode=str(state.diagnostics_mode),
    )
    assign_particle_masses(
        controller.simulation.particles,
        random_seed=int(state.seed),
        mass_mode=str(state.mass_mode),
        base_mass=float(state.base_mass),
        random_mass_min=float(state.random_mass_min),
        random_mass_max=float(state.random_mass_max),
    )
    controller.simulation.collision_elasticity = float(state.collision_elasticity)
    controller.simulation.diagnostics_mode = str(state.diagnostics_mode)
    controller.simulation.velocity_norm_sq_sum = velocity_norm_sq_sum_for_particles(
        controller.simulation.particles
    )
    controller.simulation.total_kinetic_energy = total_kinetic_energy_for_particles(
        controller.simulation.particles
    )


def _adjust_axis_row(
    state: StandaloneExplosionSurfaceState,
    *,
    row_key: str,
    step: int,
) -> bool:
    return _step_numeric_row(state, row_key=row_key, direction=step)


def _step_numeric_row(
    state: StandaloneExplosionSurfaceState,
    *,
    row_key: str,
    direction: int,
) -> bool:
    return _controls_step_numeric_row(
        row_key,
        direction,
        spec_for_row=lambda key: _numeric_spec_for_row(state, key),
        value_for_row=lambda key: _numeric_value_for_row(state, key),
        set_value_for_row=lambda key, value: _set_numeric_value_for_row(state, key, value),
    )


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
    if row_key in {"boundary_response", "particle_collisions", "mass_mode", "grid_mode", "shadow_mode"}:
        return _adjust_option_cycle_row(state, row_key=row_key, step=step)
    if row_key == "diagnostics_mode":
        return _adjust_option_cycle_row(state, row_key=row_key, step=step)
    if row_key in {"speed_preset", "trace_retention", "trace_enabled", "sound_enabled", "w_movement_animation", "seed", "base_mass", "random_mass_min", "random_mass_max", "collision_elasticity"}:
        return _adjust_misc_simulation_row(state, row_key=row_key, step=step)
    return False


def _adjust_option_cycle_row(
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
    if row_key == "mass_mode":
        state.mass_mode = _cycle_option(
            str(state.mass_mode),
            EXPLOSION_MASS_MODES,
            step,
        )
        _normalize_surface_state(state)
        _apply_live_mass_and_collision_settings(state)
        return True
    if row_key == "diagnostics_mode":
        state.diagnostics_mode = _cycle_option(
            str(state.diagnostics_mode),
            EXPLOSION_DIAGNOSTICS_MODES,
            step,
        )
        if state.controller is not None:
            state.controller.config = replace(
                state.controller.config,
                diagnostics_mode=str(state.diagnostics_mode),
            )
            state.controller.simulation.diagnostics_mode = str(state.diagnostics_mode)
        return True
    if row_key == "grid_mode":
        state.grid_mode = GridMode(
            _cycle_option(
                str(state.grid_mode),
                tuple(str(value.value) for value in _grid_mode_options()),
                step,
            )
        )
        return True
    if row_key == "shadow_mode":
        state.shadow_mode = ShadowMode(
            _cycle_option(
                str(state.shadow_mode),
                tuple(str(value.value) for value in _shadow_mode_options()),
                step,
            )
        )
        return True
    return False


def _adjust_misc_simulation_row(
    state: StandaloneExplosionSurfaceState,
    *,
    row_key: str,
    step: int,
) -> bool:
    if row_key == "speed_preset":
        state.speed_preset = _cycle_option(
            str(state.speed_preset),
            EXPLOSION_SPEED_PRESETS,
            step,
        )
        return True
    if row_key in {"trace_retention", "endgame_live_cell_fraction", "base_mass", "random_mass_min", "random_mass_max", "collision_elasticity"}:
        return _step_numeric_row(state, row_key=row_key, direction=step)
    if row_key == "trace_enabled":
        state.trace_enabled = not bool(state.trace_enabled)
        return True
    if row_key == "sound_enabled":
        state.sound_enabled = not bool(state.sound_enabled)
        return True
    if row_key == "w_movement_animation":
        state.w_movement_animation_style = _cycle_option(
            str(state.w_movement_animation_style),
            _w_movement_animation_options(),
            step,
        )
        return True
    if row_key == "seed":
        return _step_numeric_row(state, row_key=row_key, direction=step)
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
    if _numeric_spec_for_row(state, row_key) is not None:
        if state.numeric_text_row_key == row_key:
            return _commit_numeric_text_mode(state)
        return _start_numeric_text_mode(state, row_key)
    if _row_control_kind(row_key) == "dropdown" and row_key not in state.locked_rows:
        if state.open_dropdown_row_key == row_key:
            _close_dropdown(state)
        else:
            _open_dropdown(state, row_key=row_key)
        return True
    if row_key == "restart":
        restart_standalone_explosion(state)
        play_sfx("menu_confirm")
        return True
    if row_key == "save":
        ok, message = save_standalone_explosion_defaults(state)
        state.status = message
        state.status_error = not ok
        if ok:
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
        "mass_mode": str(state.mass_mode).upper(),
        "grid_mode": (
            "NONE" if state.grid_mode == GridMode.OFF else grid_mode_label(state.grid_mode)
        ),
        "shadow_mode": shadow_mode_label(state.shadow_mode),
        "w_movement_animation": _W_MOVEMENT_ANIMATION_LABELS[
            str(state.w_movement_animation_style)
        ],
        "trace_enabled": "ON" if state.trace_enabled else "OFF",
        "trace_retention": _numeric_display_text_for_row(state, "trace_retention"),
        "endgame_live_cell_fraction": _numeric_display_text_for_row(
            state, "endgame_live_cell_fraction"
        ),
        "base_mass": _numeric_display_text_for_row(state, "base_mass"),
        "random_mass_min": _numeric_display_text_for_row(state, "random_mass_min"),
        "random_mass_max": _numeric_display_text_for_row(state, "random_mass_max"),
        "collision_elasticity": _numeric_display_text_for_row(state, "collision_elasticity"),
        "diagnostics_mode": str(state.diagnostics_mode).upper(),
        "sound_enabled": "ON" if state.sound_enabled else "OFF",
        "seed": _numeric_display_text_for_row(state, "seed"),
    }


def _dynamic_row_value_text(
    state: StandaloneExplosionSurfaceState,
    row_key: str,
) -> str:
    if _numeric_spec_for_row(state, row_key) is not None and row_key.startswith("cell_"):
        return _numeric_display_text_for_row(state, row_key)
    overrides = _row_value_overrides(state)
    if row_key in overrides:
        return overrides[row_key]
    return str(getattr(state, row_key, "")).upper()


def _row_value_text(state: StandaloneExplosionSurfaceState, row_key: str) -> str:
    if row_key in _STATIC_ROW_VALUE_TEXT:
        return _STATIC_ROW_VALUE_TEXT[row_key]
    return _dynamic_row_value_text(state, row_key)


def _dropdown_current_value(
    state: StandaloneExplosionSurfaceState,
    row_key: str,
) -> str | None:
    static_values = {
        "view_mode": str(state.view_mode),
        "topology": str(state.topology_preset_id),
        "snapshot_source": str(state.snapshot_source_id),
        "piece_set": str(state.piece_set_id),
        "piece_shape": str(state.piece_shape_name),
        "boundary_response": str(state.boundary_response),
        "particle_collisions": str(state.particle_collisions),
        "mass_mode": str(state.mass_mode),
        "diagnostics_mode": str(state.diagnostics_mode),
        "grid_mode": str(state.grid_mode.value),
        "shadow_mode": str(state.shadow_mode.value),
        "w_movement_animation": str(state.w_movement_animation_style),
        "trace_enabled": "on" if state.trace_enabled else "off",
        "speed_preset": str(state.speed_preset),
        "sound_enabled": "on" if state.sound_enabled else "off",
    }
    if row_key == "dimension":
        return str(int(state.dimension))
    return static_values.get(row_key)


def _topology_value_text(state: StandaloneExplosionSurfaceState) -> str:
    if state.topology_label_override:
        return str(state.topology_label_override)
    preset = _preset_for_state(state)
    if preset is not None:
        return preset_display_label(preset, include_group=True, include_unsafe=True)
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
    board_presentation.draw_native_board_view(
        screen,
        rect=area,
        fonts=fonts,
        controller=controller,
        dimension=int(state.dimension),
        board_dims=_board_dims_for_state(state),
        camera_3d=state.camera_3d,
        view_4d=state.view_4d,
        show_trace=bool(state.trace_enabled),
        grid_mode=state.grid_mode,
        shadow_mode=state.shadow_mode,
        w_movement_animation_style=state.w_movement_animation_style,
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
            explorer_ui_enabled=False,
            **base_kwargs,
        )
        return
    _draw_scene_3d(
        screen,
        fonts,
        profile=profile,
        explosion_trace_enabled=bool(state.trace_enabled),
        explorer_ui_enabled=False,
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
        return
    if row_key == "w_movement_animation":
        state.status = (
            "4D W movement set to "
            f"{_W_MOVEMENT_ANIMATION_LABELS[str(state.w_movement_animation_style)]}"
        )
        state.status_error = False
        return
    if row_key == "trace_retention":
        state.status = (
            f"Trace retention set to {float(state.trace_retention_ms) / 1000.0:.2f}s"
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
    diagnostics_summary = (
        None if state.controller is None else state.controller.diagnostics_summary
    )
    diagnostics_mode = normalize_diagnostics_mode(state.diagnostics_mode)
    formula_text = (
        "K = 0.00 = 1/2 m [0.00]"
        if state.controller is None
        else str(state.controller.kinetic_energy_formula_text())
    )
    lines = [
        str(state.status),
        formula_text,
    ]
    if diagnostics_mode != EXPLOSION_DIAGNOSTICS_MODE_OFF:
        lines.append(
            "Σ(m_i||v_i||^2) = 0.00"
            if diagnostics_summary is None
            else f"Σ(m_i||v_i||^2) = {float(diagnostics_summary.weighted_speed_sq_sum):.2f}"
        )
        lines.append(
            "ΔK this step = 0.0000 | Contacts = 0 | Suspicious = 0"
            if diagnostics_summary is None
            else (
                f"ΔK this step = {float(diagnostics_summary.delta_kinetic_energy):+.4f} | "
                f"Contacts = {int(diagnostics_summary.contact_count)} | "
                f"Suspicious = {int(diagnostics_summary.suspicious_count)}"
            )
        )
    if diagnostics_mode == EXPLOSION_DIAGNOSTICS_MODE_FULL and diagnostics_summary is not None:
        focus = next(
            (
                detail
                for detail in diagnostics_summary.particle_details
                if detail.particle_id == diagnostics_summary.focus_particle_id
            ),
            diagnostics_summary.particle_details[0]
            if diagnostics_summary.particle_details
            else None,
        )
        if focus is not None:
            current_speed = max(0.0, float(focus.speed_sq)) ** 0.5
            previous_speed = max(0.0, float(focus.previous_speed_sq)) ** 0.5
            normal_text = (
                "none"
                if focus.last_contact_normal is None
                else ", ".join(f"{float(value):+.2f}" for value in focus.last_contact_normal)
            )
            lines.extend(
                (
                    f"Particle {int(focus.particle_id)} | m={float(focus.mass):.2f} | "
                    f"||v||={current_speed:.2f} | prev={previous_speed:.2f}",
                    f"Heading Δ={float(focus.heading_delta_deg):.1f} deg | "
                    f"Last contact={focus.last_contact_type} | normal={normal_text} | "
                    f"flagged={'yes' if focus.flagged_this_step else 'no'}",
                )
            )
        if diagnostics_summary.recent_events:
            lines.append("Suspicious events:")
            lines.extend(
                f"step {int(event.step_index)} p{int(event.particle_id)}: {event.message}"
                for event in diagnostics_summary.recent_events[-4:]
            )
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


def _draw_dropdown_affordance(
    screen: pygame.Surface,
    *,
    rect: pygame.Rect,
    selected: bool,
    disabled: bool,
) -> None:
    border = _DISABLED_COLOR if disabled else (_HIGHLIGHT_COLOR if selected else _MUTED_COLOR)
    fill = _PANEL_COLOR if disabled else _PANEL_ALT_COLOR
    pygame.draw.rect(screen, fill, rect, border_radius=8)
    pygame.draw.rect(screen, border, rect, 1, border_radius=8)
    cx = rect.centerx
    cy = rect.centery + 1
    pygame.draw.polygon(
        screen,
        border,
        ((cx - 5, cy - 2), (cx + 5, cy - 2), (cx, cy + 4)),
    )


def _build_row_layouts(
    state: StandaloneExplosionSurfaceState,
    fonts,
    *,
    panel_width: int,
) -> tuple[_RowLayout, ...]:
    return build_control_row_layouts(
        _dynamic_row_keys(state),
        font=fonts.menu_font,
        panel_width=panel_width,
        dropdown_affordance_width=_DROPDOWN_AFFORDANCE_WIDTH,
        label_for_row=_row_label_text,
        value_for_row=lambda row_key: _row_value_text(state, row_key),
        control_kind_for_row=_row_control_kind,
        slider_fraction_for_row=lambda row_key: _slider_fraction_for_row(state, row_key),
    )


def _row_rects(
    *,
    layout: _SurfaceLayout,
    row_layouts: tuple[_RowLayout, ...],
    selected_index: int,
) -> tuple[pygame.Rect, ...]:
    scroll_offset = _scroll_offset_for_selection(
        row_layouts=row_layouts,
        selected_index=selected_index,
        viewport_height=layout.row_viewport.height,
    )
    return _controls_row_rects(
        viewport=layout.row_viewport,
        row_layouts=row_layouts,
        scroll_offset=scroll_offset,
    )


def _slider_rect_for_row(row_rect: pygame.Rect, row_layout: _RowLayout) -> pygame.Rect | None:
    return _controls_slider_rect_for_row(row_rect, row_layout)


def _dropdown_values_for_row(
    state: StandaloneExplosionSurfaceState,
    row_key: str,
) -> tuple[tuple[str, str], ...]:
    static_options = {
        "boundary_response": tuple(
            (value, value.upper()) for value in EXPLOSION_BOUNDARY_RESPONSES
        ),
        "particle_collisions": tuple(
            (value, value.upper()) for value in EXPLOSION_PARTICLE_COLLISION_MODES
        ),
        "mass_mode": tuple(
            (value, value.upper()) for value in EXPLOSION_MASS_MODES
        ),
        "diagnostics_mode": tuple(
            (value, value.upper()) for value in EXPLOSION_DIAGNOSTICS_MODES
        ),
        "grid_mode": tuple(
            (
                str(value.value),
                "NONE" if value == GridMode.OFF else grid_mode_label(value),
            )
            for value in _grid_mode_options()
        ),
        "shadow_mode": tuple(
            (str(value.value), shadow_mode_label(value))
            for value in _shadow_mode_options()
        ),
        "w_movement_animation": tuple(
            (value, _W_MOVEMENT_ANIMATION_LABELS[value])
            for value in _w_movement_animation_options()
        ),
        "trace_enabled": (("off", "OFF"), ("on", "ON")),
        "speed_preset": tuple((value, value.upper()) for value in EXPLOSION_SPEED_PRESETS),
        "sound_enabled": (("off", "OFF"), ("on", "ON")),
    }
    if row_key == "dimension":
        return tuple((value, f"{value}D") for value in ("2", "3", "4"))
    if row_key == "view_mode":
        return tuple((value, _VIEW_MODE_LABELS[value]) for value in _view_mode_options_for_state(state))
    if row_key == "topology":
        return tuple(
            (
                str(preset.preset_id),
                preset_display_label(preset, include_group=True, include_unsafe=True),
            )
            for preset in _preset_options_for_dimension(int(state.dimension))
        )
    if row_key == "snapshot_source":
        return tuple(
            (value, _SNAPSHOT_SOURCE_LABELS[value])
            for value in _available_snapshot_source_ids(state)
        )
    if row_key == "piece_set":
        return tuple(
            (value, _piece_set_label_for_dimension(int(state.dimension), value))
            for value in _piece_set_options_for_dimension(int(state.dimension))
        )
    if row_key == "piece_shape":
        shapes = _piece_shapes_for_state(state, board_dims=_board_dims_for_state(state))
        return tuple((str(shape.name), str(shape.name)) for shape in shapes)
    return static_options.get(row_key, ())


def _apply_dropdown_value(
    state: StandaloneExplosionSurfaceState,
    *,
    row_key: str,
    raw_value: str,
) -> bool:
    simple_setters = {
        "view_mode": ("view_mode", str(raw_value)),
        "topology": ("topology_preset_id", str(raw_value)),
        "piece_shape": ("piece_shape_name", str(raw_value)),
        "boundary_response": ("boundary_response", str(raw_value)),
        "particle_collisions": ("particle_collisions", str(raw_value)),
        "mass_mode": ("mass_mode", str(raw_value)),
        "diagnostics_mode": ("diagnostics_mode", str(raw_value)),
        "speed_preset": ("speed_preset", str(raw_value)),
        "w_movement_animation": ("w_movement_animation_style", str(raw_value)),
        "trace_enabled": ("trace_enabled", str(raw_value) == "on"),
        "sound_enabled": ("sound_enabled", str(raw_value) == "on"),
    }
    if row_key == "dimension":
        state.dimension = int(raw_value)
        _normalize_surface_state(state)
        return True
    if row_key == "snapshot_source":
        state.snapshot_source_id = str(raw_value)
        _normalize_surface_state(state)
        return True
    if row_key == "piece_set":
        state.piece_set_id = str(raw_value)
        _normalize_surface_state(state)
        return True
    if row_key == "grid_mode":
        state.grid_mode = GridMode(str(raw_value))
        return True
    if row_key == "shadow_mode":
        state.shadow_mode = ShadowMode(str(raw_value))
        return True
    if row_key in simple_setters:
        attribute, value = simple_setters[row_key]
        setattr(state, attribute, value)
        if row_key in {"mass_mode", "diagnostics_mode"}:
            _normalize_surface_state(state)
            if state.controller is not None:
                state.controller.config = replace(
                    state.controller.config,
                    diagnostics_mode=str(state.diagnostics_mode),
                )
                state.controller.simulation.diagnostics_mode = str(state.diagnostics_mode)
            if row_key == "mass_mode":
                _apply_live_mass_and_collision_settings(state)
        return True
    return False


def _dropdown_menu_rect(
    row_rect: pygame.Rect,
    *,
    option_count: int,
    viewport: pygame.Rect,
    font: pygame.font.Font,
) -> pygame.Rect:
    return _controls_dropdown_menu_rect(
        row_rect,
        option_count=option_count,
        viewport=viewport,
        font=font,
        menu_width=_DROPDOWN_MENU_WIDTH,
        option_vertical_padding=_DROPDOWN_OPTION_VERTICAL_PADDING,
    )


def _dropdown_visible_slice(
    state: StandaloneExplosionSurfaceState,
    *,
    option_count: int,
    menu_rect: pygame.Rect,
    font: pygame.font.Font,
) -> tuple[int, int]:
    return _controls_dropdown_visible_slice(
        state,
        option_count=option_count,
        menu_rect=menu_rect,
        font=font,
        option_vertical_padding=_DROPDOWN_OPTION_VERTICAL_PADDING,
    )


def _dropdown_option_rects(
    state: StandaloneExplosionSurfaceState,
    *,
    menu_rect: pygame.Rect,
    option_count: int,
    font: pygame.font.Font,
) -> tuple[tuple[int, pygame.Rect], ...]:
    return _controls_dropdown_option_rects(
        state,
        menu_rect=menu_rect,
        option_count=option_count,
        font=font,
        option_vertical_padding=_DROPDOWN_OPTION_VERTICAL_PADDING,
    )


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


def _draw_rows(
    screen: pygame.Surface,
    *,
    fonts,
    state: StandaloneExplosionSurfaceState,
    layout: _SurfaceLayout,
    row_layouts: tuple[_RowLayout, ...],
    row_rects: tuple[pygame.Rect, ...],
) -> None:
    previous_clip = screen.get_clip()
    screen.set_clip(layout.row_viewport)
    for index, (row_layout, row_rect) in enumerate(zip(row_layouts, row_rects)):
        selected = index == int(state.selected_index)
        locked = row_layout.row_key in state.locked_rows
        hovered = state.hovered_row_key == row_layout.row_key
        pygame.draw.rect(
            screen,
            _PANEL_ALT_COLOR if (selected or hovered) else _PANEL_COLOR,
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
            value_right=row_rect.right - row_layout.value_right_padding,
            top_y=row_rect.y + 6 + (row_layout.slider_layout.text_top_padding if row_layout.slider_layout is not None else 0),
            label_color=_DISABLED_COLOR if locked else _TEXT_COLOR,
            value_color=_DISABLED_COLOR if locked else (_HIGHLIGHT_COLOR if selected else _MUTED_COLOR),
            line_gap=3,
        )
        if row_layout.slider_layout is not None and row_layout.slider_fraction is not None:
            slider_rect = _slider_rect_for_row(row_rect, row_layout)
            assert slider_rect is not None
            draw_value_slider(
                screen,
                rect=slider_rect,
                fraction=row_layout.slider_fraction,
            )
        elif row_layout.control_kind == "dropdown":
            _draw_dropdown_affordance(
                screen,
                rect=pygame.Rect(
                    row_rect.right - 10 - _DROPDOWN_AFFORDANCE_WIDTH,
                    row_rect.y + 10,
                    _DROPDOWN_AFFORDANCE_WIDTH,
                    20,
                ),
                selected=selected,
                disabled=locked,
            )
    screen.set_clip(previous_clip)


def _draw_open_dropdown_menu(
    screen: pygame.Surface,
    *,
    fonts,
    state: StandaloneExplosionSurfaceState,
    layout: _SurfaceLayout,
    row_layouts: tuple[_RowLayout, ...],
    row_rects: tuple[pygame.Rect, ...],
) -> None:
    if state.open_dropdown_row_key is None:
        return
    open_index = next(
        (
            idx
            for idx, row_layout in enumerate(row_layouts)
            if row_layout.row_key == state.open_dropdown_row_key
        ),
        None,
    )
    if open_index is None:
        return
    options = _dropdown_values_for_row(
        state,
        state.open_dropdown_row_key,
    )
    if not options:
        return
    menu_rect = _dropdown_menu_rect(
        row_rects[open_index],
        option_count=len(options),
        viewport=layout.row_viewport,
        font=fonts.menu_font,
    )
    pygame.draw.rect(screen, _PANEL_COLOR, menu_rect, border_radius=10)
    pygame.draw.rect(screen, _HIGHLIGHT_COLOR, menu_rect, 1, border_radius=10)
    current_value = _dropdown_current_value(
        state,
        state.open_dropdown_row_key,
    )
    option_rects = _dropdown_option_rects(
        state,
        menu_rect=menu_rect,
        option_count=len(options),
        font=fonts.menu_font,
    )
    for option_index, option_rect in option_rects:
        option_value, option_label = options[option_index]
        if option_value == current_value:
            pygame.draw.rect(screen, _PANEL_ALT_COLOR, option_rect, border_radius=6)
        elif state.dropdown_hover_index == option_index:
            pygame.draw.rect(screen, _BG_TOP, option_rect, border_radius=6)
        text = fit_text(fonts.menu_font, option_label, option_rect.width - 12)
        option_surf = fonts.menu_font.render(
            text,
            True,
            (
                _HIGHLIGHT_COLOR
                if option_value == current_value or state.dropdown_hover_index == option_index
                else _TEXT_COLOR
            ),
        )
        screen.blit(option_surf, (option_rect.x + 6, option_rect.y + 4))


def _draw_surface(
    screen: pygame.Surface,
    fonts,
    state: StandaloneExplosionSurfaceState,
) -> None:
    _normalize_surface_state(state)
    layout = _surface_layout(screen_size=screen.get_size(), fonts=fonts, state=state)
    row_layouts = _build_row_layouts(state, fonts, panel_width=layout.left_rect.width)
    row_rects = _row_rects(
        layout=layout,
        row_layouts=row_layouts,
        selected_index=int(state.selected_index),
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
    pygame.draw.rect(screen, _PANEL_ALT_COLOR, layout.row_viewport, border_radius=12)
    _draw_rows(
        screen,
        fonts=fonts,
        state=state,
        layout=layout,
        row_layouts=row_layouts,
        row_rects=row_rects,
    )
    _draw_open_dropdown_menu(
        screen,
        fonts=fonts,
        state=state,
        layout=layout,
        row_layouts=row_layouts,
        row_rects=row_rects,
    )
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
        _camera_controls_module().step_scene_camera(_scene_camera_for_state(state), dt_ms)
        if not _process_launcher_events(state, screen=screen, fonts=fonts):
            return False, "Explosion simulator closed"
        if state.controller is not None:
            for event_name in state.controller.step(dt_ms):
                play_sfx(event_name)
        _draw_surface(screen, fonts, state)
        pygame.display.flip()
    return True, "Explosion simulator closed"


def _move_selected_row(state: StandaloneExplosionSurfaceState, step: int) -> None:
    previous_row = _dynamic_row_keys(state)[int(state.selected_index)]
    if state.numeric_text_row_key and previous_row == state.numeric_text_row_key:
        _commit_numeric_text_mode(state, allow_partial=False)
    _close_dropdown(state)
    row_keys = _dynamic_row_keys(state)
    state.selected_index = (int(state.selected_index) + int(step)) % len(row_keys)
    play_sfx("menu_move")


def _restart_from_key(state: StandaloneExplosionSurfaceState, key: int) -> None:
    if key in (pygame.K_LEFT, pygame.K_RIGHT):
        if state.numeric_text_row_key:
            _stop_numeric_text_mode(state)
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
    row_key = _dynamic_row_keys(state)[int(state.selected_index)]
    if _handle_numeric_text_keydown(state, key, row_key=row_key):
        return
    if _handle_escape_key(state, key):
        return
    if _handle_vertical_navigation_key(state, key):
        return
    if key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_r):
        _restart_from_key(state, key)
        return
    if _camera_controls_module().handle_scene_camera_key(
        int(state.dimension),
        key,
        _scene_camera_for_state(state),
    ):
        play_sfx("menu_move")
        return
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
        if not _activate_selected_row(state):
            _restart_from_key(state, pygame.K_r)


def _handle_escape_key(
    state: StandaloneExplosionSurfaceState,
    key: int,
) -> bool:
    if key != pygame.K_ESCAPE:
        return False
    if state.numeric_text_row_key:
        _stop_numeric_text_mode(state)
        state.status = "Numeric entry canceled."
        state.status_error = False
        return True
    if state.open_dropdown_row_key is not None:
        _close_dropdown(state)
        return True
    state.running = False
    return True


def _handle_vertical_navigation_key(
    state: StandaloneExplosionSurfaceState,
    key: int,
) -> bool:
    if key == pygame.K_UP:
        _move_selected_row(state, -1)
        return True
    if key == pygame.K_DOWN:
        _move_selected_row(state, 1)
        return True
    return False


def _handle_numeric_text_keydown(
    state: StandaloneExplosionSurfaceState,
    key: int,
    *,
    row_key: str,
) -> bool:
    return _controls_handle_numeric_text_keydown(
        state,
        key,
        row_key=row_key,
        spec_for_row=lambda key: _numeric_spec_for_row(state, key),
        start_numeric_mode=lambda key: _start_numeric_text_mode(state, key),
        append_input=lambda text: _append_numeric_text_input(state, text),
        commit_mode=lambda: _commit_numeric_text_mode(state, allow_partial=False),
    )


def _scene_camera_for_state(state: StandaloneExplosionSurfaceState):
    if int(state.dimension) == 3:
        return state.camera_3d
    if int(state.dimension) == 4:
        return state.view_4d
    return None


def _should_route_camera_input(state: StandaloneExplosionSurfaceState) -> bool:
    return (
        int(state.dimension) in (3, 4)
        and str(state.view_mode) == _VIEW_MODE_BOARD_NATIVE
    )


def _row_index_at_position(
    state: StandaloneExplosionSurfaceState,
    *,
    layout: _SurfaceLayout,
    fonts,
    position: tuple[int, int],
) -> int | None:
    row_layouts, row_rects = _interactive_row_geometry(
        state,
        layout=layout,
        fonts=fonts,
    )
    return _controls_row_index_at_position(row_rects, position=position)


def _interactive_row_geometry(
    state: StandaloneExplosionSurfaceState,
    *,
    layout: _SurfaceLayout,
    fonts,
) -> tuple[tuple[_RowLayout, ...], tuple[pygame.Rect, ...]]:
    row_layouts = _build_row_layouts(state, fonts, panel_width=layout.left_rect.width)
    row_rects = _row_rects(
        layout=layout,
        row_layouts=row_layouts,
        selected_index=int(state.selected_index),
    )
    return row_layouts, row_rects


def _open_dropdown_selection_from_click(
    state: StandaloneExplosionSurfaceState,
    *,
    layout: _SurfaceLayout,
    fonts,
    position: tuple[int, int],
) -> bool:
    row_layouts, row_rects = _interactive_row_geometry(
        state,
        layout=layout,
        fonts=fonts,
    )
    row_key, changed = _controls_select_dropdown_option_from_click(
        state,
        position=position,
        row_layouts=row_layouts,
        row_rects=row_rects,
        layout_viewport=layout.row_viewport,
        font=fonts.menu_font,
        options_for_row=lambda key: _dropdown_values_for_row(state, key),
        apply_value=lambda key, raw_value: _apply_dropdown_value(
            state,
            row_key=key,
            raw_value=raw_value,
        ),
        menu_width=_DROPDOWN_MENU_WIDTH,
        option_vertical_padding=_DROPDOWN_OPTION_VERTICAL_PADDING,
    )
    if changed and row_key is not None:
        if _requires_restart_for_row(row_key):
            restart_standalone_explosion(state)
        else:
            _apply_nonrestart_row_status(state, row_key=row_key)
        play_sfx("menu_confirm")
        return True
    return False


def _update_hover_state(
    state: StandaloneExplosionSurfaceState,
    event,
    *,
    layout: _SurfaceLayout,
    fonts,
) -> bool:
    if event.type != pygame.MOUSEMOTION:
        return False
    position = getattr(event, "pos", (0, 0))
    state.hovered_row_key = None
    row_layouts, row_rects = _interactive_row_geometry(
        state,
        layout=layout,
        fonts=fonts,
    )
    for row_layout, row_rect in zip(row_layouts, row_rects):
        if row_rect.collidepoint(position):
            state.hovered_row_key = row_layout.row_key
            break
    _controls_update_dropdown_hover_index(
        state,
        row_layouts=row_layouts,
        row_rects=row_rects,
        layout_viewport=layout.row_viewport,
        font=fonts.menu_font,
        position=position,
        options_for_row=lambda key: _dropdown_values_for_row(state, key),
        menu_width=_DROPDOWN_MENU_WIDTH,
        option_vertical_padding=_DROPDOWN_OPTION_VERTICAL_PADDING,
    )
    return False


def _dropdown_option_index_at_position(
    state: StandaloneExplosionSurfaceState,
    *,
    layout: _SurfaceLayout,
    fonts,
    position: tuple[int, int],
) -> int | None:
    row_layouts, row_rects = _interactive_row_geometry(
        state,
        layout=layout,
        fonts=fonts,
    )
    return _controls_dropdown_option_index_at_position(
        state,
        row_layouts=row_layouts,
        row_rects=row_rects,
        layout_viewport=layout.row_viewport,
        font=fonts.menu_font,
        position=position,
        options_for_row=lambda key: _dropdown_values_for_row(state, key),
        menu_width=_DROPDOWN_MENU_WIDTH,
        option_vertical_padding=_DROPDOWN_OPTION_VERTICAL_PADDING,
    )


def _handle_dropdown_scroll(
    state: StandaloneExplosionSurfaceState,
    event,
    *,
    layout: _SurfaceLayout,
    fonts,
) -> bool:
    row_layouts, row_rects = _interactive_row_geometry(
        state,
        layout=layout,
        fonts=fonts,
    )
    return _controls_update_dropdown_scroll(
        state,
        event,
        row_layouts=row_layouts,
        row_rects=row_rects,
        layout_viewport=layout.row_viewport,
        font=fonts.menu_font,
        options_for_row=lambda key: _dropdown_values_for_row(state, key),
        menu_width=_DROPDOWN_MENU_WIDTH,
        option_vertical_padding=_DROPDOWN_OPTION_VERTICAL_PADDING,
    )


def _handle_slider_pointer_event(
    state: StandaloneExplosionSurfaceState,
    event,
    *,
    layout: _SurfaceLayout,
    fonts,
) -> bool:
    row_layouts, row_rects = _interactive_row_geometry(
        state,
        layout=layout,
        fonts=fonts,
    )
    if _release_slider_drag(state, event):
        state.slider_drag_row_key = None
        return False
    if event.type not in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION}:
        return False
    position = getattr(event, "pos", (0, 0))
    candidate_row_key = _candidate_slider_row_key(
        state,
        event,
        position=position,
        row_layouts=row_layouts,
        row_rects=row_rects,
    )
    if candidate_row_key is None:
        return False
    row_index = _row_index_for_key(row_layouts, candidate_row_key)
    if row_index is None:
        return False
    slider_rect = _slider_rect_for_row(row_rects[row_index], row_layouts[row_index])
    if slider_rect is None:
        return False
    if not _controls_set_slider_value_from_pointer(
        candidate_row_key,
        pointer_x=position[0],
        slider_rect=slider_rect,
        spec_for_row=lambda key: _numeric_spec_for_row(state, key),
        set_value_for_row=lambda key, value: _set_numeric_value_for_row(state, key, value),
    ):
        return False
    state.selected_index = row_index
    _close_dropdown(state)
    return True


def _release_slider_drag(state: StandaloneExplosionSurfaceState, event) -> bool:
    return event.type == pygame.MOUSEBUTTONUP and getattr(event, "button", None) == 1


def _candidate_slider_row_key(
    state: StandaloneExplosionSurfaceState,
    event,
    *,
    position: tuple[int, int],
    row_layouts: tuple[_RowLayout, ...],
    row_rects: tuple[pygame.Rect, ...],
) -> str | None:
    if event.type != pygame.MOUSEBUTTONDOWN:
        return state.slider_drag_row_key
    for row_layout, row_rect in zip(row_layouts, row_rects):
        slider_rect = _slider_rect_for_row(row_rect, row_layout)
        if slider_rect is not None and slider_rect.collidepoint(position):
            state.slider_drag_row_key = row_layout.row_key
            return row_layout.row_key
    return None


def _row_index_for_key(
    row_layouts: tuple[_RowLayout, ...],
    row_key: str,
) -> int | None:
    return next(
        (
            idx
            for idx, row_layout in enumerate(row_layouts)
            if row_layout.row_key == row_key
        ),
        None,
    )


def _slider_fraction_from_pointer(slider_rect: pygame.Rect, pointer_x: int) -> float:
    return _controls_slider_fraction_from_pointer(slider_rect, pointer_x)


def _process_launcher_events(
    state: StandaloneExplosionSurfaceState,
    *,
    screen: pygame.Surface,
    fonts,
) -> bool:
    layout = _surface_layout(screen_size=screen.get_size(), fonts=fonts, state=state)
    for event in pygame.event.get():
        if _is_quit_event(event):
            return False
        if _handle_pointer_routed_event(state, event, layout=layout, fonts=fonts):
            continue
        if _handle_text_input_event(state, event):
            continue
        if event.type == pygame.KEYDOWN:
            _handle_launcher_keydown(state, event.key)
    return True


def _is_quit_event(event) -> bool:
    return event.type == pygame.QUIT


def _handle_pointer_routed_event(
    state: StandaloneExplosionSurfaceState,
    event,
    *,
    layout: _SurfaceLayout,
    fonts,
) -> bool:
    _update_hover_state(state, event, layout=layout, fonts=fonts)
    return any(
        handler(state, event, layout=layout, fonts=fonts)
        for handler in (_handle_dropdown_scroll, _handle_slider_pointer_event, _handle_left_click)
    ) or _route_camera_mouse_event(state, event, layout=layout)


def _handle_text_input_event(
    state: StandaloneExplosionSurfaceState,
    event,
) -> bool:
    if event.type != pygame.TEXTINPUT:
        return False
    row_key = _dynamic_row_keys(state)[int(state.selected_index)]
    if not (state.numeric_text_row_key or _numeric_spec_for_row(state, row_key) is not None):
        return False
    if not state.numeric_text_row_key:
        _start_numeric_text_mode(state, row_key)
    _append_numeric_text_input(state, event.text)
    return True


def _route_camera_mouse_event(
    state: StandaloneExplosionSurfaceState,
    event,
    *,
    layout: _SurfaceLayout,
) -> bool:
    if not (
        _should_route_camera_input(state)
        and event.type
        in {
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEMOTION,
            pygame.MOUSEWHEEL,
        }
    ):
        return False
    position = getattr(event, "pos", (0, 0))
    if event.type != pygame.MOUSEWHEEL and not layout.preview_scene_rect.collidepoint(position):
        return False
    return _camera_controls_module().handle_scene_camera_mouse_event(
        int(state.dimension),
        event,
        _scene_camera_for_state(state),
        state.mouse_orbit,
    )


def _handle_left_click(
    state: StandaloneExplosionSurfaceState,
    event,
    *,
    layout: _SurfaceLayout,
    fonts,
) -> bool:
    if not (event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1):
        return False
    position = event.pos if hasattr(event, "pos") else pygame.mouse.get_pos()
    if _open_dropdown_selection_from_click(
        state,
        layout=layout,
        fonts=fonts,
        position=position,
    ):
        return True
    row_index = _row_index_at_position(
        state,
        layout=layout,
        fonts=fonts,
        position=position,
    )
    if row_index is None:
        _close_dropdown(state)
        return False
    previous_row = _dynamic_row_keys(state)[int(state.selected_index)]
    if state.numeric_text_row_key and previous_row == state.numeric_text_row_key and row_index != int(state.selected_index):
        _commit_numeric_text_mode(state, allow_partial=False)
    state.selected_index = int(row_index)
    row_key = _dynamic_row_keys(state)[int(state.selected_index)]
    if _row_control_kind(row_key) == "dropdown" and row_key not in state.locked_rows:
        _open_dropdown(state, row_key=row_key)
    else:
        _close_dropdown(state)
    if _numeric_spec_for_row(state, row_key) is not None and state.hovered_row_key == row_key:
        _start_numeric_text_mode(state, row_key)
    if row_key in {"save", "restart", "back"}:
        _activate_selected_row(state)
    play_sfx("menu_move")
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
