from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    full_wrap_profile_3d,
    full_wrap_profile_4d,
    projective_plane_profile_2d,
    projective_space_profile_3d,
    projective_space_profile_4d,
    sphere_profile_2d,
    sphere_profile_3d,
    sphere_profile_4d,
)


ProfileFactory = Callable[[], ExplorerTopologyProfile]


@dataclass(frozen=True)
class TopologyTraceCase:
    case_id: str
    dimension: int
    topology_id: str
    dims: tuple[int, ...]
    profile_factory: ProfileFactory
    probe_start: tuple[int, ...]
    commands: tuple[dict[str, Any], ...]
    seed: int | None = None
    include_play_policy: bool = False
    include_playability_repeat: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GameplayTraceCase:
    case_id: str
    dimension: int
    topology_id: str
    dims: tuple[int, ...]
    seed: int
    commands: tuple[dict[str, Any], ...]
    topology_profile_factory: ProfileFactory | None = None
    legacy_topology_mode: str = "bounded"
    wrap_gravity_axis: bool = False
    launch_from_playground: bool = False
    piece_set_id: str | None = None
    piece_blocks: tuple[tuple[int, ...], ...] = ((0, 0),)
    piece_pos: tuple[int, ...] | None = None
    current_piece_enabled: bool = True
    next_piece_blocks: tuple[tuple[int, ...], ...] | None = None
    initial_locked_cells: tuple[tuple[tuple[int, ...], int], ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EndgameTraceCase:
    case_id: str
    dimension: int
    topology_id: str
    dims: tuple[int, ...]
    seed: int
    locked_cells: tuple[tuple[tuple[int, ...], int, str | None], ...]
    frame_count: int = 8
    dt_ms: float = 160.0
    topology_profile_factory: ProfileFactory | None = None
    preset: str = "classic"
    collision_mode: str = "no_collision"
    speed_preset: str = "normal"
    live_fraction: float = 1.0
    boundary_response: str = "bounce"
    particle_overrides: tuple[dict[str, Any], ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)


def _plain_profile(dimension: int) -> ProfileFactory:
    return lambda: ExplorerTopologyProfile(dimension=dimension, gluings=())


def _default_probe_start(dimension: int) -> tuple[int, ...]:
    return tuple(2 for _ in range(dimension))


TOPOLOGY_TRACE_CASES: tuple[TopologyTraceCase, ...] = (
    TopologyTraceCase(
        "topology_plain_2d",
        2,
        "plain",
        (4, 4),
        _plain_profile(2),
        (2, 2),
        (
            {"id": "in_bounds_x_neg", "step": "x-"},
            {"id": "blocked_y_pos", "step": "y+"},
        ),
    ),
    TopologyTraceCase(
        "topology_plain_3d",
        3,
        "plain",
        (4, 4, 4),
        _plain_profile(3),
        (2, 2, 2),
        (
            {"id": "in_bounds_z_pos", "step": "z+"},
            {"id": "blocked_y_pos", "step": "y+"},
        ),
    ),
    TopologyTraceCase(
        "topology_plain_4d",
        4,
        "plain",
        (4, 4, 4, 4),
        _plain_profile(4),
        (2, 2, 2, 2),
        (
            {"id": "in_bounds_w_neg", "step": "w-"},
            {"id": "blocked_y_pos", "step": "y+"},
        ),
    ),
    TopologyTraceCase(
        "topology_wrap_2d",
        2,
        "wrap",
        (4, 4),
        lambda: axis_wrap_profile(dimension=2, wrapped_axes=(0,)),
        (0, 2),
        ({"id": "wrap_x_neg", "step": "x-"}, {"id": "roundtrip_x_pos", "step": "x+"}),
    ),
    TopologyTraceCase(
        "topology_wrap_3d",
        3,
        "wrap",
        (4, 4, 4),
        full_wrap_profile_3d,
        (0, 2, 3),
        ({"id": "wrap_x_neg", "step": "x-"}, {"id": "wrap_z_pos", "step": "z+"}),
    ),
    TopologyTraceCase(
        "topology_wrap_4d",
        4,
        "wrap",
        (4, 4, 4, 4),
        full_wrap_profile_4d,
        (0, 2, 3, 3),
        ({"id": "wrap_x_neg", "step": "x-"}, {"id": "wrap_w_pos", "step": "w+"}),
    ),
    TopologyTraceCase(
        "topology_invert_2d",
        2,
        "invert",
        (4, 4),
        projective_plane_profile_2d,
        (0, 1),
        ({"id": "invert_x_neg", "step": "x-"}, {"id": "roundtrip_x_pos", "step": "x+"}),
    ),
    TopologyTraceCase(
        "topology_invert_3d",
        3,
        "invert",
        (4, 4, 4),
        projective_space_profile_3d,
        (0, 1, 2),
        ({"id": "invert_x_neg", "step": "x-"}, {"id": "roundtrip_x_pos", "step": "x+"}),
    ),
    TopologyTraceCase(
        "topology_invert_4d",
        4,
        "invert",
        (4, 4, 4, 4),
        projective_space_profile_4d,
        (0, 1, 2, 3),
        ({"id": "invert_x_neg", "step": "x-"}, {"id": "roundtrip_x_pos", "step": "x+"}),
    ),
    TopologyTraceCase(
        "topology_sphere_like_2d",
        2,
        "sphere_like",
        (8, 8),
        sphere_profile_2d,
        (7, 7),
        (
            {"id": "cross_axis_y_pos", "step": "y+"},
            {"id": "roundtrip_y_neg", "step": "y-"},
        ),
    ),
    TopologyTraceCase(
        "topology_sphere_like_3d",
        3,
        "sphere_like",
        (4, 4, 4),
        sphere_profile_3d,
        (3, 3, 0),
        (
            {"id": "cross_axis_y_pos", "step": "y+"},
            {"id": "roundtrip_y_neg", "step": "y-"},
        ),
    ),
    TopologyTraceCase(
        "topology_sphere_like_4d",
        4,
        "sphere_like",
        (4, 4, 4, 4),
        sphere_profile_4d,
        (3, 3, 1, 0),
        (
            {"id": "cross_axis_y_pos", "step": "y+"},
            {"id": "roundtrip_y_neg", "step": "y-"},
        ),
    ),
    TopologyTraceCase(
        "topology_play_vs_sandbox_y_axis",
        3,
        "sphere_like",
        (4, 4, 4),
        sphere_profile_3d,
        (3, 3, 0),
        ({"id": "sandbox_probe_y_pos", "step": "y+"},),
        include_play_policy=True,
        notes=(
            "Sandbox probe may cross the Y seam; Play drop intent rejects that seam.",
        ),
    ),
    TopologyTraceCase(
        "topology_false_lock_regression_sphere_like",
        3,
        "sphere_like",
        (4, 4, 4),
        sphere_profile_3d,
        (3, 3, 0),
        ({"id": "sphere_y_seam_probe", "step": "y+"},),
        include_play_policy=True,
        notes=(
            "Captures the sphere-like Y seam as topology transport, not ordinary falling.",
        ),
    ),
    TopologyTraceCase(
        "topology_playability_diagnostics_stable",
        2,
        "sphere_like_invalid_dims",
        (5, 4),
        sphere_profile_2d,
        _default_probe_start(2),
        (),
        include_playability_repeat=True,
        notes=("Invalid sphere-like dimensions must produce repeatable diagnostics.",),
    ),
)


GAMEPLAY_TRACE_CASES: tuple[GameplayTraceCase, ...] = (
    GameplayTraceCase(
        "gameplay_plain_2d_short",
        2,
        "plain",
        (6, 6),
        2001,
        (
            {"id": "move_right", "action": "move", "delta": [1, 0]},
            {"id": "soft_drop", "action": "soft_drop"},
            {"id": "hard_drop", "action": "hard_drop"},
        ),
        piece_blocks=((0, 0), (1, 0)),
        piece_pos=(2, 3),
    ),
    GameplayTraceCase(
        "gameplay_plain_2d_rotation_short",
        2,
        "plain",
        (6, 6),
        2011,
        (
            {"id": "rotate_cw", "action": "rotate", "delta": 1},
            {"id": "soft_drop_after_rotate", "action": "soft_drop"},
        ),
        piece_blocks=((-1, 0), (0, 0), (1, 0), (0, 1)),
        piece_pos=(2, 2),
        notes=("Stage 11 plain 2D rotation parity trace.",),
    ),
    GameplayTraceCase(
        "gameplay_plain_2d_configurable",
        2,
        "plain",
        (10, 20),
        2049,
        (
            {"id": "move_right", "action": "move", "delta": [1, 0]},
            {"id": "rotate_cw", "action": "rotate", "delta": 1},
            {"id": "hard_drop", "action": "hard_drop"},
        ),
        piece_blocks=((-1, 0), (0, 0), (1, 0), (2, 0)),
        piece_pos=(4, 8),
        notes=("Stage 49 alternate-size 2D board-shape parity.",),
    ),
    GameplayTraceCase(
        "gameplay_plain_2d_hard_drop_lock",
        2,
        "plain",
        (6, 6),
        2012,
        ({"id": "hard_drop_from_above", "action": "hard_drop"},),
        piece_blocks=((0, 0),),
        piece_pos=(2, -1),
        notes=("Stage 11 plain 2D hard-drop lock parity trace.",),
    ),
    GameplayTraceCase(
        "gameplay_plain_2d_line_clear_short",
        2,
        "plain",
        (6, 6),
        2013,
        ({"id": "hard_drop_line_clear", "action": "hard_drop"},),
        piece_blocks=((0, 0),),
        piece_pos=(5, 4),
        initial_locked_cells=(
            ((0, 5), 2),
            ((1, 5), 2),
            ((2, 5), 2),
            ((3, 5), 2),
            ((4, 5), 2),
            ((0, 4), 9),
        ),
        notes=("Stage 11 plain 2D single-line clear parity trace.",),
    ),
    GameplayTraceCase(
        "gameplay_plain_3d_short",
        3,
        "plain",
        (5, 5, 5),
        2002,
        (
            {"id": "move_z", "action": "move_axis", "axis": 2, "delta": 1},
            {"id": "soft_drop", "action": "soft_drop"},
            {"id": "hard_drop", "action": "hard_drop"},
        ),
        piece_blocks=((0, 0, 0), (1, 0, 0)),
        piece_pos=(2, 2, 2),
    ),
    GameplayTraceCase(
        "gameplay_plain_4d_short",
        4,
        "plain",
        (5, 5, 4, 4),
        2003,
        (
            {"id": "move_w", "action": "move_axis", "axis": 3, "delta": 1},
            {"id": "soft_drop", "action": "soft_drop"},
            {"id": "hard_drop", "action": "hard_drop"},
        ),
        piece_blocks=((0, 0, 0, 0), (1, 0, 0, 0)),
        piece_pos=(2, 2, 1, 1),
    ),
    GameplayTraceCase(
        "gameplay_plain_3d_configurable",
        3,
        "plain",
        (8, 16, 8),
        2050,
        (
            {"id": "move_z", "action": "move_axis", "axis": 2, "delta": 1},
            {
                "id": "rotate_xz_cw",
                "action": "rotate",
                "axis_a": 0,
                "axis_b": 2,
                "delta": 1,
            },
            {"id": "hard_drop", "action": "hard_drop"},
        ),
        piece_set_id="native_3d",
        piece_blocks=((0, 0, 0), (1, 0, 0)),
        piece_pos=(3, 8, 3),
        notes=("Stage 49 alternate-size 3D board-shape parity.",),
    ),
    GameplayTraceCase(
        "gameplay_plain_4d_configurable_w8",
        4,
        "plain",
        (8, 16, 5, 8),
        2051,
        (
            {"id": "move_w", "action": "move_axis", "axis": 3, "delta": 1},
            {
                "id": "rotate_xw_cw",
                "action": "rotate",
                "axis_a": 0,
                "axis_b": 3,
                "delta": 1,
            },
            {"id": "hard_drop", "action": "hard_drop"},
        ),
        piece_set_id="standard_4d_5",
        piece_blocks=((0, 0, 0, 0), (1, 0, 0, 0)),
        piece_pos=(3, 8, 2, 3),
        notes=("Stage 49 alternate-size W=8 board-shape parity.",),
    ),
    GameplayTraceCase(
        "gameplay_plain_3d_rotation_short",
        3,
        "plain",
        (5, 5, 5),
        2021,
        (
            {
                "id": "rotate_xz_cw",
                "action": "rotate",
                "axis_a": 0,
                "axis_b": 2,
                "delta": 1,
            },
        ),
        piece_blocks=((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
        piece_pos=(2, 2, 2),
        notes=("Stage 17 plain 3D rotation oracle trace.",),
    ),
    GameplayTraceCase(
        "gameplay_plain_4d_rotation_short",
        4,
        "plain",
        (5, 5, 5, 5),
        2022,
        (
            {
                "id": "rotate_xw_cw",
                "action": "rotate",
                "axis_a": 0,
                "axis_b": 3,
                "delta": 1,
            },
        ),
        piece_blocks=(
            (0, 0, 0, 0),
            (1, 0, 0, 0),
            (0, 1, 0, 0),
            (0, 0, 1, 0),
        ),
        piece_pos=(2, 2, 2, 2),
        notes=("Stage 17 plain 4D rotation oracle trace.",),
    ),
    GameplayTraceCase(
        "gameplay_plain_3d_plane_clear_short",
        3,
        "plain",
        (2, 3, 2),
        2023,
        ({"id": "lock_plane_clear", "action": "lock_current_piece"},),
        piece_blocks=((0, 0, 0),),
        piece_pos=(0, 2, 0),
        initial_locked_cells=(
            ((1, 2, 0), 1),
            ((0, 2, 1), 1),
            ((1, 2, 1), 1),
            ((1, 1, 1), 2),
        ),
        notes=("Stage 17 plain 3D single-plane clear oracle trace.",),
    ),
    GameplayTraceCase(
        "gameplay_plain_4d_plane_clear_short",
        4,
        "plain",
        (2, 3, 1, 2),
        2024,
        ({"id": "lock_hyperplane_clear", "action": "lock_current_piece"},),
        piece_set_id="embedded_2d",
        piece_blocks=((0, 0, 0, 0),),
        piece_pos=(0, 2, 0, 0),
        initial_locked_cells=(
            ((1, 2, 0, 0), 1),
            ((0, 2, 0, 1), 1),
            ((1, 2, 0, 1), 1),
            ((1, 1, 0, 1), 2),
        ),
        notes=("Stage 17 plain 4D single-hyperplane clear oracle trace.",),
    ),
    GameplayTraceCase(
        "gameplay_plain_3d_spawn_blocked_game_over",
        3,
        "plain",
        (5, 5, 5),
        2025,
        ({"id": "spawn_blocked", "action": "spawn_new_piece"},),
        piece_blocks=((0, 0, 0),),
        current_piece_enabled=False,
        next_piece_blocks=((0, 0, 0), (0, 2, 0)),
        initial_locked_cells=(((2, 0, 2), 9),),
        notes=("Stage 17 plain 3D spawn-blocked game-over oracle trace.",),
    ),
    GameplayTraceCase(
        "gameplay_plain_4d_spawn_blocked_game_over",
        4,
        "plain",
        (5, 5, 5, 5),
        2026,
        ({"id": "spawn_blocked", "action": "spawn_new_piece"},),
        piece_set_id="embedded_2d",
        piece_blocks=((0, 0, 0, 0),),
        current_piece_enabled=False,
        next_piece_blocks=((0, 0, 0, 0), (0, 2, 0, 0)),
        initial_locked_cells=(((2, 0, 2, 2), 9),),
        notes=("Stage 17 plain 4D spawn-blocked game-over oracle trace.",),
    ),
    GameplayTraceCase(
        "gameplay_wrap_2d_short",
        2,
        "wrap",
        (6, 6),
        2004,
        (
            {"id": "wrap_left", "action": "move", "delta": [-1, 0]},
            {"id": "soft_drop", "action": "soft_drop"},
            {"id": "hard_drop", "action": "hard_drop"},
        ),
        legacy_topology_mode="wrap_all",
        piece_blocks=((0, 0),),
        piece_pos=(0, 3),
    ),
    GameplayTraceCase(
        "gameplay_wrap_3d_short",
        3,
        "wrap",
        (5, 5, 5),
        2005,
        (
            {"id": "wrap_x_neg", "action": "move_axis", "axis": 0, "delta": -1},
            {"id": "soft_drop", "action": "soft_drop"},
            {"id": "hard_drop", "action": "hard_drop"},
        ),
        legacy_topology_mode="wrap_all",
        piece_blocks=((0, 0, 0),),
        piece_pos=(0, 2, 2),
    ),
    GameplayTraceCase(
        "gameplay_wrap_4d_short",
        4,
        "wrap",
        (5, 5, 4, 4),
        2006,
        (
            {"id": "wrap_w_pos", "action": "move_axis", "axis": 3, "delta": 1},
            {"id": "soft_drop", "action": "soft_drop"},
            {"id": "hard_drop", "action": "hard_drop"},
        ),
        legacy_topology_mode="wrap_all",
        piece_blocks=((0, 0, 0, 0),),
        piece_pos=(2, 2, 1, 3),
    ),
    GameplayTraceCase(
        "gameplay_invert_short",
        3,
        "invert",
        (5, 5, 5),
        2007,
        (
            {"id": "invert_x_neg", "action": "move_axis", "axis": 0, "delta": -1},
            {"id": "soft_drop", "action": "soft_drop"},
            {"id": "hard_drop", "action": "hard_drop"},
        ),
        legacy_topology_mode="invert_all",
        piece_blocks=((0, 0, 0),),
        piece_pos=(0, 2, 1),
    ),
    GameplayTraceCase(
        "gameplay_sphere_like_short",
        3,
        "sphere_like",
        (4, 4, 4),
        2008,
        (
            {"id": "translate_y_seam", "action": "move_axis", "axis": 1, "delta": 1},
            {"id": "gravity_locks", "action": "gravity_step"},
        ),
        topology_profile_factory=sphere_profile_3d,
        launch_from_playground=True,
        piece_blocks=((0, 0, 0),),
        piece_pos=(3, 3, 0),
    ),
    GameplayTraceCase(
        "gameplay_y_axis_drop_policy",
        3,
        "sphere_like",
        (4, 4, 4),
        2009,
        (
            {
                "id": "translation_crosses_y_seam",
                "action": "move_axis",
                "axis": 1,
                "delta": 1,
            },
            {"id": "soft_drop_rejected", "action": "soft_drop"},
            {"id": "gravity_locks", "action": "gravity_step"},
        ),
        topology_profile_factory=sphere_profile_3d,
        launch_from_playground=True,
        piece_blocks=((0, 0, 0),),
        piece_pos=(3, 3, 0),
        notes=("Y-axis topology seam traversal is not ordinary Play drop.",),
    ),
    GameplayTraceCase(
        "gameplay_launch_topology_parity",
        4,
        "sphere_like",
        (4, 4, 4, 4),
        2010,
        (
            {
                "id": "launched_transport_y_seam",
                "action": "move_axis",
                "axis": 1,
                "delta": 1,
            },
            {"id": "gravity_policy", "action": "gravity_step"},
        ),
        topology_profile_factory=sphere_profile_4d,
        launch_from_playground=True,
        piece_blocks=((0, 0, 0, 0),),
        piece_pos=(3, 3, 1, 0),
        notes=(
            "Config is built by Play This Topology launch path before gameplay runs.",
        ),
    ),
)


ENDGAME_TRACE_CASES: tuple[EndgameTraceCase, ...] = (
    EndgameTraceCase(
        "endgame_2d_classic",
        2,
        "classic",
        (4, 4),
        3101,
        (
            ((0, 1), 2, "L"),
            ((1, 1), 3, "L"),
            ((2, 2), 4, "T"),
            ((3, 2), 5, "T"),
        ),
        particle_overrides=(
            {"particle_id": 0, "position": [0.0, 1.0], "velocity": [-1.4, 0.2]},
        ),
    ),
    EndgameTraceCase(
        "endgame_3d_classic",
        3,
        "classic",
        (4, 4, 4),
        3102,
        (
            ((0, 1, 1), 2, "I3"),
            ((1, 1, 1), 3, "I3"),
            ((2, 2, 2), 4, "L3"),
            ((3, 2, 2), 5, "L3"),
        ),
        particle_overrides=(
            {
                "particle_id": 0,
                "position": [0.0, 1.0, 1.0],
                "velocity": [-1.2, 0.1, 0.3],
            },
        ),
    ),
    EndgameTraceCase(
        "endgame_4d_classic",
        4,
        "classic",
        (4, 4, 4, 4),
        3103,
        (
            ((0, 1, 1, 1), 2, "I4"),
            ((1, 1, 1, 1), 3, "I4"),
            ((2, 2, 2, 2), 4, "L4"),
            ((3, 2, 2, 3), 5, "L4"),
        ),
        particle_overrides=(
            {
                "particle_id": 0,
                "position": [1.0, 1.0, 1.0, 1.0],
                "velocity": [0.0, 0.0, 0.0, 1.1],
            },
        ),
    ),
    EndgameTraceCase(
        "endgame_4d_wrap_all",
        4,
        "wrap_all",
        (4, 4, 4, 4),
        3104,
        (
            ((1, 1, 1, 3), 2, "W"),
            ((2, 1, 1, 3), 3, "W"),
            ((1, 2, 2, 0), 4, "W"),
        ),
        topology_profile_factory=full_wrap_profile_4d,
        preset="wrap_all",
        particle_overrides=(
            {
                "particle_id": 0,
                "position": [1.0, 1.0, 1.0, 3.45],
                "velocity": [0.0, 0.0, 0.0, 1.2],
            },
        ),
        notes=("W-axis seam transport is represented in the moving particle path.",),
    ),
    EndgameTraceCase(
        "endgame_4d_invert_all",
        4,
        "invert_all",
        (4, 4, 4, 4),
        3105,
        (
            ((0, 1, 1, 1), 2, "P"),
            ((0, 2, 1, 2), 3, "P"),
            ((1, 2, 2, 3), 4, "P"),
        ),
        topology_profile_factory=projective_space_profile_4d,
        preset="invert_all",
        particle_overrides=(
            {
                "particle_id": 0,
                "position": [-0.45, 1.0, 1.0, 1.0],
                "velocity": [-1.2, 0.2, 0.3, 0.4],
            },
        ),
    ),
    EndgameTraceCase(
        "endgame_4d_sphere_like",
        4,
        "sphere_like",
        (4, 4, 4, 4),
        3106,
        (
            ((1, 1, 0, 1), 2, "S"),
            ((1, 1, 1, 1), 3, "S"),
            ((2, 2, 2, 2), 4, "S"),
        ),
        topology_profile_factory=sphere_profile_4d,
        preset="sphere_like",
        particle_overrides=(
            {
                "particle_id": 0,
                "position": [1.0, 1.0, -0.45, 1.0],
                "velocity": [0.2, 0.3, -1.2, 0.4],
            },
        ),
        notes=("Sphere-like cross-axis transport maps position and velocity.",),
    ),
    EndgameTraceCase(
        "endgame_4d_no_collision",
        4,
        "classic",
        (4, 4, 4, 4),
        3107,
        (
            ((1, 1, 1, 1), 2, "N"),
            ((2, 1, 1, 1), 3, "N"),
        ),
        collision_mode="no_collision",
        particle_overrides=(
            {
                "particle_id": 0,
                "position": [1.2, 1.0, 1.0, 1.0],
                "velocity": [0.9, 0.0, 0.0, 0.0],
            },
            {
                "particle_id": 1,
                "position": [1.6, 1.0, 1.0, 1.0],
                "velocity": [-0.9, 0.0, 0.0, 0.0],
            },
        ),
    ),
    EndgameTraceCase(
        "endgame_4d_elastic_if_stable",
        4,
        "classic",
        (4, 4, 4, 4),
        3108,
        (
            ((1, 1, 1, 1), 2, "E"),
            ((2, 1, 1, 1), 3, "E"),
        ),
        collision_mode="elastic",
        particle_overrides=(
            {
                "particle_id": 0,
                "position": [1.2, 1.0, 1.0, 1.0],
                "velocity": [0.9, 0.0, 0.0, 0.0],
            },
            {
                "particle_id": 1,
                "position": [1.6, 1.0, 1.0, 1.0],
                "velocity": [-0.9, 0.0, 0.0, 0.0],
            },
        ),
        notes=(
            "Elastic collision trace is kept deterministic; exact conservation remains diagnostic-covered.",
        ),
    ),
)


TOPOLOGY_CASES_BY_ID = {case.case_id: case for case in TOPOLOGY_TRACE_CASES}
GAMEPLAY_CASES_BY_ID = {case.case_id: case for case in GAMEPLAY_TRACE_CASES}
ENDGAME_CASES_BY_ID = {case.case_id: case for case in ENDGAME_TRACE_CASES}
