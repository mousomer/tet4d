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
    piece_blocks: tuple[tuple[int, ...], ...] = ((0, 0),)
    piece_pos: tuple[int, ...] | None = None
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


TOPOLOGY_CASES_BY_ID = {case.case_id: case for case in TOPOLOGY_TRACE_CASES}
GAMEPLAY_CASES_BY_ID = {case.case_id: case for case in GAMEPLAY_TRACE_CASES}
